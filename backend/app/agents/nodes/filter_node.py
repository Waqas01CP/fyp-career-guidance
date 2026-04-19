"""
filter_node.py — Eligibility filtering. Pure Python. No LLM calls.
Reads universities.json once at node entry. Applies 6 constraint checks per degree.
Produces a single flat list in state["current_roadmap"].

v1.9 changes:
- Check 0: HEC/council legal floor (hard exclusion, never enters hard_excluded_raw)
- Check 3: uses calculate_estimated_merit() — assessment proxy for entry test
- Check 3b: entry test difficulty warning when proxy was used
- shift field added to all roadmap entries
- aggregate_formula added to roadmap entries (required by ScoringNode)
"""

import json
import logging
from pathlib import Path

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

_TIER_PRIORITY = {"confirmed": 0, "likely": 1, "stretch": 2, "improvement_needed": 3}


def calculate_aggregate(subject_marks: dict, aggregate_formula: dict) -> float:
    """
    Compute weighted average of subject marks using subject_weights from aggregate_formula.

    Subjects with mark == 0 are excluded (treated as not taken — e.g. biology=0 for a
    Pre-Engineering student who never sat the subject). Including them with 'other' weight
    would unfairly drag the aggregate down.

    subject_weights keys are lowercase ("mathematics", "physics").
    Falls back to the "other" weight for subjects not explicitly listed.
    """
    subject_weights = aggregate_formula.get("subject_weights", {})
    other_weight = float(subject_weights.get("other", 1.0))

    total_weighted = 0.0
    total_weight = 0.0

    for subject, mark in subject_marks.items():
        if mark == 0:
            continue
        w = float(subject_weights.get(subject, other_weight))
        total_weighted += mark * w
        total_weight += w

    if total_weight == 0.0:
        return 0.0
    return total_weighted / total_weight


def calculate_estimated_merit(
    subject_marks: dict,
    capability_scores: dict,
    aggregate_formula: dict,
    entry_test: dict,
) -> tuple[float, bool]:
    """
    Compute estimated merit for FilterNode Check 3.

    When entry_test_weight == 0.0: returns (inter_component, False) — pure inter merit.
    When entry_test_weight > 0: builds a proxy from capability_scores matched against
    entry_test subject weights. Returns (estimated_merit, True).

    proxy_score is 0-100, matching entry test scale. Default for missing capability
    scores: settings.CAPABILITY_PROXY_DEFAULT (50.0 — neutral).
    """
    inter_component = calculate_aggregate(subject_marks, aggregate_formula)
    entry_test_weight = float(aggregate_formula.get("entry_test_weight", 0.0))
    inter_weight = float(aggregate_formula.get("inter_weight", 1.0))

    if entry_test_weight == 0.0:
        return (inter_component, False)

    proxy_score = 0.0
    for weight_key, subject in settings.ENTRY_TEST_SUBJECT_MAP.items():
        w = float(entry_test.get(weight_key, 0.0))
        score = float(capability_scores.get(subject, settings.CAPABILITY_PROXY_DEFAULT))
        proxy_score += score * w

    estimated_merit = (inter_component * inter_weight) + (proxy_score * entry_test_weight)
    return (estimated_merit, True)


def _commute_description(zone_diff: int) -> str:
    if zone_diff <= 1:
        return "easy commute"
    if zone_diff == 2:
        return "moderate commute"
    return "difficult commute"


def _estimate_travel(zone_diff: int) -> str:
    if zone_diff <= 1:
        return "20–30"
    if zone_diff == 2:
        return "40–60"
    return "60–90"


def _weakest_required_subject(subject_marks: dict, mandatory_subjects: list) -> str:
    """Return the mandatory subject (lowercase) with the lowest non-zero mark."""
    if not mandatory_subjects:
        return "your weakest subject"
    candidates = {}
    for subj in mandatory_subjects:
        mark = subject_marks.get(subj.lower(), 0)
        candidates[subj] = mark
    if not candidates:
        return "your weakest subject"
    return min(candidates, key=lambda s: candidates[s])


def _build_improvement_needed_flag(
    aggregate: float,
    cutoff_min: float,
    subject_marks: dict,
    mandatory_subjects: list,
    university_name: str,
    degree_name: str,
) -> dict:
    gap = round(cutoff_min - aggregate, 1)
    weakest = _weakest_required_subject(subject_marks, mandatory_subjects)
    return {
        "type": "improvement_needed",
        "gap_percentage": gap,
        "message": (
            f"Your aggregate is {gap}% below {university_name} {degree_name} "
            f"minimum cutoff of {cutoff_min}%"
        ),
        "subject_advice": f"Focus on strengthening {weakest}",
        "actionable": f"Focus on {weakest} to close this gap",
    }


def filter_node(state: AgentState) -> AgentState:
    """
    Pure Python eligibility filter. Zero LLM calls.

    Applies six constraint checks per degree:
      Check 0 — HEC/council legal floor (hard exclusion, never in hard_excluded_raw)
      Check 1 — Stream eligibility
      Check 2 — Mandatory subjects
      Check 3 — Merit tier via calculate_estimated_merit()
      Check 3b — Entry test difficulty warning (when proxy used)
      Check 4 — Budget (soft flag only)
      Check 5 — Zone distance (soft flag only)

    HEC-excluded degrees (Check 0) are legally disqualified and cannot be promoted
    by the minimum display rule. Only Check 1/2 hard exclusions enter hard_excluded_raw.
    """
    stream = state["student_profile"].get("stream") or ""
    subject_marks = state["student_profile"].get("subject_marks") or {}
    capability_scores = state["student_profile"].get("capability_scores") or {}
    budget = state["active_constraints"].get("budget_per_semester")
    home_zone = state["active_constraints"].get("home_zone") or 1
    student_mode = state.get("student_mode") or "inter"

    trace_entries: list[str] = []

    try:
        with open(DATA_DIR / "universities.json", encoding="utf-8") as fh:
            universities = json.load(fh)
    except FileNotFoundError:
        logger.error("universities.json not found at %s", DATA_DIR)
        state["current_roadmap"] = []
        state["thought_trace"] = (state.get("thought_trace") or []) + [
            "filter_node: universities.json not found"
        ]
        return state

    results: list[dict] = []
    hard_excluded_raw: list[dict] = []

    for university in universities:
        university_id: str = university["university_id"]
        university_name: str = university["name"]

        for degree in university["degrees"]:
            soft_flags: list[dict] = []
            eligibility_tier: str | None = None
            eligibility_note: str | None = None
            merit_tier: str | None = None
            aggregate: float | None = None
            trace_merit = ""
            trace_fee = ""
            hec_excluded = False
            hard_exclude = False

            degree_id: str = degree["degree_id"]
            degree_name: str = degree["name"]
            degree_label = f"{university_name} {degree_name}"
            elig = degree["eligibility"]
            mandatory_subjects: list[str] = elig["mandatory_subjects"]

            # ── Check 0: HEC/council legal floor ─────────────────────────
            # Unadjusted inter: simple mean of non-zero subject marks.
            # HEC specifies "unadjusted marks" — subject weights do not apply here.
            non_zero = [v for v in subject_marks.values() if v > 0]
            unadjusted_inter = sum(non_zero) / len(non_zero) if non_zero else 0.0
            min_required = float(elig["min_percentage_hssc"])

            if unadjusted_inter < min_required:
                degree_name_lower = degree_name.lower()
                if any(t in degree_name_lower for t in ["be ", "bsc engg", "mbbs", "bds", "pharm-d", "dvm"]):
                    council = "PEC/PMDC/PCP — legally enforced minimum"
                elif any(t in degree_name_lower for t in ["bs computer", "bs software", "bs cs", "bs ai", "bs cyber", "b.arch", "b arch"]):
                    council = "NCEAC/PCATP — legally enforced minimum"
                else:
                    council = "HEC — legally enforced minimum"
                trace_entries.append(
                    f"{degree_label} — unadjusted inter {unadjusted_inter:.1f}% < "
                    f"required {min_required:.1f}% ({council}): HARD EXCLUDED"
                )
                hec_excluded = True

            if hec_excluded:
                # Legally disqualified — never enters hard_excluded_raw,
                # never promoted by minimum display rule.
                continue

            # ── Check 1: Stream eligibility ───────────────────────────────
            if stream in elig["fully_eligible_streams"]:
                eligibility_tier = "confirmed"

            elif stream in elig["conditionally_eligible_streams"]:
                eligibility_tier = "likely"
                # Direct access per Point 4 — data integrity enforced by validation Rule 5
                eligibility_note = elig["eligibility_notes"][stream]

            else:
                if elig.get("policy_pending_verification"):
                    eligibility_tier = "likely"
                    eligibility_note = (
                        "Policy pending verification — contact admissions office "
                        "for eligibility details"
                    )
                    soft_flags.append({
                        "type": "policy_unconfirmed",
                        "message": (
                            f"{degree_label} eligibility for stream '{stream}' "
                            "is pending verification"
                        ),
                        "actionable": (
                            "Contact the admissions office to confirm eligibility "
                            "before applying"
                        ),
                    })
                else:
                    eligible_list = (
                        elig["fully_eligible_streams"]
                        + elig["conditionally_eligible_streams"]
                    )
                    trace_entries.append(
                        f"{degree_label} — stream {stream} not in "
                        f"{eligible_list}: BLOCKED → excluded"
                    )
                    hard_exclude = True

            if hard_exclude:
                hard_excluded_raw.append({
                    "degree_id": degree_id,
                    "field_id": degree["field_id"],
                    "aggregate_formula": degree["aggregate_formula"],
                    "university_id": university_id,
                    "university_name": university_name,
                    "degree_name": degree_name,
                    "fee_per_semester": degree["fee_per_semester"],
                    "shift": degree.get("shift", "full_day"),
                })
                continue

            # ── Check 2: Mandatory subjects ───────────────────────────────
            subject_marks_lower = {k.lower(): v for k, v in subject_marks.items()}

            for subject in mandatory_subjects:
                if subject.lower() not in subject_marks_lower:
                    waiver = elig["subject_waivers"].get(subject)
                    if waiver and stream in waiver.get("waivable_for_streams", []):
                        if eligibility_tier == "confirmed":
                            eligibility_tier = "likely"
                        bridge_note = (
                            f"Missing {subject} — "
                            f"{waiver.get('condition', 'bridge course required')}"
                        )
                        eligibility_note = (
                            (eligibility_note + " | " + bridge_note)
                            if eligibility_note
                            else bridge_note
                        )
                        soft_flags.append({
                            "type": "bridge_course_required",
                            "message": bridge_note,
                            "actionable": "Bridge course required before enrollment",
                        })
                    else:
                        trace_entries.append(
                            f"{degree_label} — {subject} required, not in profile, "
                            "no subject waiver → excluded"
                        )
                        hard_exclude = True
                        break

            if hard_exclude:
                hard_excluded_raw.append({
                    "degree_id": degree_id,
                    "field_id": degree["field_id"],
                    "aggregate_formula": degree["aggregate_formula"],
                    "university_id": university_id,
                    "university_name": university_name,
                    "degree_name": degree_name,
                    "fee_per_semester": degree["fee_per_semester"],
                    "shift": degree.get("shift", "full_day"),
                })
                continue

            # ── Check 3: Merit tier (skipped in matric_planning mode) ─────
            if student_mode != "matric_planning":
                estimated_merit, proxy_used = calculate_estimated_merit(
                    subject_marks,
                    capability_scores,
                    degree["aggregate_formula"],
                    degree["entry_test"],
                )
                aggregate = estimated_merit
                cutoff_min: float = degree["cutoff_range"]["min"]
                cutoff_max: float = degree["cutoff_range"]["max"]

                if proxy_used:
                    soft_flags.append({
                        "type": "entry_test_proxy_used",
                        "message": (
                            "Merit estimate uses your assessment scores as a proxy "
                            "for the entry test. Final merit depends on your actual "
                            "entry test performance."
                        ),
                        "actionable": (
                            "Treat this as a guidance estimate — your real entry "
                            "test score determines final admission."
                        ),
                    })

                if aggregate >= cutoff_max:
                    merit_tier = "confirmed"
                elif aggregate >= cutoff_min:
                    merit_tier = "likely"
                elif aggregate >= (cutoff_min - settings.MERIT_STRETCH_THRESHOLD):
                    merit_tier = "stretch"
                    soft_flags.append({
                        "type": "stretch_merit",
                        "message": (
                            f"Your aggregate is "
                            f"{round(cutoff_min - aggregate, 1)}% below "
                            f"{degree_label} minimum cutoff"
                        ),
                        "actionable": (
                            "Possible in a competitive year; entry test "
                            "performance is critical"
                        ),
                    })
                else:
                    merit_tier = "improvement_needed"
                    soft_flags.append(
                        _build_improvement_needed_flag(
                            aggregate,
                            cutoff_min,
                            subject_marks,
                            mandatory_subjects,
                            university_name,
                            degree_name,
                        )
                    )

                trace_merit = (
                    f"aggregate {aggregate:.1f}% vs range "
                    f"[{cutoff_min}%–{cutoff_max}%]: {merit_tier.upper()}"
                )

                # ── Check 3b: Entry test difficulty warning ────────────────
                if proxy_used:
                    difficulty_tier = university.get("entry_test_difficulty_tier", "standard")
                    if difficulty_tier == "hard":
                        soft_flags.append({
                            "type": "entry_test_harder_than_assessed",
                            "message": (
                                f"{university_name}'s entry test is harder than our "
                                "capability assessment. Your estimate may be optimistic."
                            ),
                            "actionable": (
                                "Invest in focused entry test prep — past papers "
                                "and dedicated study."
                            ),
                        })
                    elif difficulty_tier == "extreme":
                        soft_flags.append({
                            "type": "entry_test_harder_than_assessed",
                            "message": (
                                f"{university_name}'s entry test is significantly harder "
                                "than our capability assessment. This estimate has high "
                                "uncertainty."
                            ),
                            "actionable": (
                                "Treat this as aspirational. Dedicated preparation over "
                                "months is required. Consider this a stretch target."
                            ),
                        })

            else:
                soft_flags.append({
                    "type": "planning_mode",
                    "message": "Merit eligibility cannot be assessed without Inter marks",
                    "actionable": (
                        "Take Pre-Engineering in Inter and aim for 80%+ "
                        "to reach this program"
                    ),
                })
                merit_tier = None
                proxy_used = False
                trace_merit = "MATRIC_PLANNING (merit skipped)"

            # ── Check 4: Budget (soft flag only — never exclude) ──────────
            fee: int = degree["fee_per_semester"]
            if budget is not None and fee > budget:
                overage = fee - budget
                soft_flags.append({
                    "type": "over_budget",
                    "message": (
                        f"Fee is Rs. {fee:,}/semester — "
                        f"Rs. {overage:,} above your stated budget"
                    ),
                    "actionable": (
                        f"Increasing budget to Rs. {fee:,} makes this reachable"
                    ),
                })
                trace_fee = (
                    f"fee {fee // 1000}k > budget {budget // 1000}k: "
                    "SOFT FLAG (over_budget)"
                )
            else:
                trace_fee = (
                    f"fee {fee // 1000}k <= budget "
                    f"{(budget or 0) // 1000}k: PASS"
                )

            # ── Check 5: Transport / zone distance (soft flag only) ───────
            uni_zone: int = degree["location"]["zone"]
            zone_diff = abs(home_zone - uni_zone)
            if zone_diff >= 2:
                soft_flags.append({
                    "type": "commute_distance",
                    "message": (
                        f"{university_name} is in Zone {uni_zone} — "
                        f"{_commute_description(zone_diff)} from your area"
                    ),
                    "actionable": (
                        f"Travel time approximately "
                        f"{_estimate_travel(zone_diff)} minutes"
                    ),
                })

            # ── Final tier (most conservative of eligibility and merit) ───
            if merit_tier is None:
                final_tier = eligibility_tier
            else:
                final_tier = max(
                    eligibility_tier,
                    merit_tier,
                    key=lambda t: _TIER_PRIORITY[t],
                )

            # ── Thought trace ─────────────────────────────────────────────
            trace_entries.append(
                f"{degree_label} — stream {stream}: {eligibility_tier.upper()} | "
                f"{trace_merit} | {trace_fee} → {final_tier}"
            )

            results.append({
                "degree_id": degree_id,
                "field_id": degree["field_id"],
                "university_id": university_id,
                "university_name": university_name,
                "degree_name": degree_name,
                "eligibility_tier": eligibility_tier,
                "merit_tier": merit_tier,
                "final_tier": final_tier,
                "eligibility_note": eligibility_note,
                "aggregate_used": round(aggregate, 2) if aggregate is not None else None,
                "aggregate_formula": degree["aggregate_formula"],
                "entry_test": degree.get("entry_test", {}),
                "fee_per_semester": fee,
                "shift": degree.get("shift", "full_day"),
                "soft_flags": soft_flags,
            })

    # ── Minimum display rule ──────────────────────────────────────────────
    min_show: int = settings.FILTER_MINIMUM_RESULTS_SHOWN
    if len(results) < min_show:
        needed = min_show - len(results)
        for exc in hard_excluded_raw[:needed]:
            exc_agg = (
                round(calculate_aggregate(subject_marks, exc["aggregate_formula"]), 2)
                if student_mode != "matric_planning"
                else None
            )
            results.append({
                "degree_id": exc["degree_id"],
                "field_id": exc["field_id"],
                "university_id": exc["university_id"],
                "university_name": exc["university_name"],
                "degree_name": exc["degree_name"],
                "eligibility_tier": "likely",
                "merit_tier": "improvement_needed",
                "final_tier": "improvement_needed",
                "eligibility_note": (
                    "Shown to meet minimum display requirement — "
                    "contact university for eligibility details"
                ),
                "aggregate_used": exc_agg,
                "aggregate_formula": exc["aggregate_formula"],
                "entry_test": exc.get("entry_test", {}),
                "fee_per_semester": exc["fee_per_semester"],
                "shift": exc.get("shift", "full_day"),
                "soft_flags": [
                    {
                        "type": "planning_mode",
                        "message": (
                            "This degree is shown to meet the minimum "
                            "display requirement"
                        ),
                        "actionable": (
                            "Contact the admissions office to confirm "
                            "eligibility for your stream"
                        ),
                    }
                ],
            })
            trace_entries.append(
                f"{exc['university_name']} {exc['degree_name']} — "
                "PROMOTED to meet minimum display rule (5-degree floor)"
            )

    state["current_roadmap"] = results
    state["thought_trace"] = (state.get("thought_trace") or []) + trace_entries
    return state
