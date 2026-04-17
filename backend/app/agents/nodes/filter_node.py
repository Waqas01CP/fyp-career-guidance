"""
filter_node.py — Eligibility filtering. Pure Python. No LLM calls.
Reads universities.json once at node entry. Applies 5 constraint checks per degree.
Produces a single flat list in state["current_roadmap"].
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

    Applies five constraint checks per degree (stream eligibility, mandatory subjects,
    merit tier, budget, zone). Writes results to state["current_roadmap"] and appends
    decision strings to state["thought_trace"].

    Minimum display rule: always >= FILTER_MINIMUM_RESULTS_SHOWN entries. Hard-excluded
    degrees are promoted in JSON iteration order if needed (affinity_matrix not read here).
    """
    stream = state["student_profile"].get("stream") or ""
    subject_marks = state["student_profile"].get("subject_marks") or {}
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
            hard_exclude = False

            degree_id: str = degree["degree_id"]
            degree_name: str = degree["name"]
            degree_label = f"{university_name} {degree_name}"
            elig = degree["eligibility"]
            mandatory_subjects: list[str] = elig["mandatory_subjects"]

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
                })
                continue

            # ── Check 3: Merit tier (skipped in matric_planning mode) ─────
            if student_mode != "matric_planning":
                aggregate = calculate_aggregate(subject_marks, degree["aggregate_formula"])
                cutoff_min: float = degree["cutoff_range"]["min"]
                cutoff_max: float = degree["cutoff_range"]["max"]

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
                "aggregate_formula": degree["aggregate_formula"],
                "university_id": university_id,
                "university_name": university_name,
                "degree_name": degree_name,
                "eligibility_tier": eligibility_tier,
                "merit_tier": merit_tier,
                "final_tier": final_tier,
                "eligibility_note": eligibility_note,
                "aggregate_used": round(aggregate, 2) if aggregate is not None else None,
                "fee_per_semester": fee,
                "soft_flags": soft_flags,
                "hard_excluded": False,
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
                "aggregate_formula": exc["aggregate_formula"],
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
                "fee_per_semester": exc["fee_per_semester"],
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
                "hard_excluded": False,
            })
            trace_entries.append(
                f"{exc['university_name']} {exc['degree_name']} — "
                "PROMOTED to meet minimum display rule (5-degree floor)"
            )

    state["current_roadmap"] = results
    state["thought_trace"] = (state.get("thought_trace") or []) + trace_entries
    return state
