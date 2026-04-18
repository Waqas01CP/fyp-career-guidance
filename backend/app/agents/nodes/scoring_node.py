"""
scoring_node.py — RIASEC match scoring + FutureValue + capability blend. Pure Python. No LLM.
Reads affinity_matrix.json and lag_model.json.
Computes total_score = (weight_match * match_score_normalised) + (weight_future * future_score/10).
Applies capability blend when abs(capability - reported_grade) >= CAPABILITY_BLEND_THRESHOLD.
Detects aptitude-preference mismatch and sets mismatch_notice.
"""
import json
import logging
from pathlib import Path

from app.agents.nodes.filter_node import calculate_aggregate
from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_affinity_matrix() -> dict:
    path = DATA_DIR / "affinity_matrix.json"
    with open(path) as f:
        data = json.load(f)
    return {entry["field_id"]: entry for entry in data}


def _load_lag_model() -> dict:
    path = DATA_DIR / "lag_model.json"
    with open(path) as f:
        data = json.load(f)
    return {entry["field_id"]: entry for entry in data}


def build_mismatch_notice(
    preferred: dict,
    top_match: dict,
    gap: float,
    future_value: float,
) -> str:
    pref_name = preferred["degree_name"]
    top_name = top_match["degree_name"]
    pref_score = preferred["total_score"] * 100
    top_score = top_match["total_score"] * 100
    return (
        f"Your {pref_name} score ({pref_score:.0f}) is {gap:.0f} points below "
        f"your top match {top_name} ({top_score:.0f}). Market outlook for "
        f"{pref_name} is below average (FutureValue {future_value:.1f}/10)."
    )


def scoring_node(state: AgentState) -> AgentState:
    """
    Pure Python scoring node. Zero LLM calls.

    For each degree in current_roadmap:
      1. Per-subject capability blend (applied BEFORE calculate_aggregate)
      2. RIASEC dot product normalised to 0-1
      3. FutureValue lookup from lag_model
      4. total_score computation
      5. thought_trace append

    After loop: sort descending by total_score, then mismatch detection.
    """
    affinity_matrix = _load_affinity_matrix()
    lag_model = _load_lag_model()

    student_profile = state["student_profile"]
    riasec_scores = student_profile.get("riasec_scores") or {}
    subject_marks = student_profile.get("subject_marks") or {}
    capability_scores = student_profile.get("capability_scores") or {}
    student_mode = state.get("student_mode") or "inter"

    # RIASEC student vector — always R I A S E C order
    student_vector = [riasec_scores.get(dim, 0) for dim in ("R", "I", "A", "S", "E", "C")]
    theoretical_max = sum(s * 10 for s in student_vector)

    weights = settings.SCORING_WEIGHTS[student_mode]
    current_roadmap = state.get("current_roadmap") or []

    for degree in current_roadmap:
        field_id: str = degree["field_id"]
        degree_name: str = degree["degree_name"]
        university_name: str = degree["university_name"]
        degree_label = f"{degree_name} ({university_name})"

        # ── Capability blend — per-subject, BEFORE calculate_aggregate() ──
        effective_marks: dict = {}
        for subject, reported_grade in subject_marks.items():
            capability = capability_scores.get(subject)
            if capability is None:
                effective_marks[subject] = reported_grade
                continue
            gap = capability - reported_grade
            if abs(gap) >= settings.CAPABILITY_BLEND_THRESHOLD:
                raw_effective = (
                    (reported_grade * (1 - settings.CAPABILITY_BLEND_WEIGHT))
                    + (capability * settings.CAPABILITY_BLEND_WEIGHT)
                )
                effective_marks[subject] = max(
                    reported_grade - settings.CAPABILITY_BLEND_MAX_SHIFT,
                    min(reported_grade + settings.CAPABILITY_BLEND_MAX_SHIFT, raw_effective),
                )
                state["thought_trace"].append(
                    f"{degree_label} — {subject}: capability {capability:.1f}% vs "
                    f"reported {reported_grade:.1f}% (gap {gap:+.0f}pts). "
                    f"Effective: {effective_marks[subject]:.1f}%"
                )
            else:
                effective_marks[subject] = reported_grade

        capability_adjustment_applied = any(
            effective_marks.get(s) != subject_marks[s] for s in subject_marks
        )

        # ── RIASEC dot product and FutureValue ────────────────────────────
        if field_id not in affinity_matrix or field_id not in lag_model:
            logger.warning(
                "%s — field_id %s not found in affinity_matrix/lag_model. "
                "Scoring with defaults.",
                degree_label,
                field_id,
            )
            state["thought_trace"].append(
                f"{degree_label} — field_id {field_id} not found in "
                "affinity_matrix/lag_model. Scoring with defaults."
            )
            match_score_normalised = 0.5
            future_score = 5.0
        else:
            riasec_affinity = affinity_matrix[field_id]["riasec_affinity"]
            degree_vector = [
                riasec_affinity.get(dim, 1) for dim in ("R", "I", "A", "S", "E", "C")
            ]
            raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
            match_score_normalised = raw_match / theoretical_max if theoretical_max > 0 else 0.0
            future_score = float(lag_model[field_id]["computed"]["future_value"])

        # ── Total score ───────────────────────────────────────────────────
        total_score = (
            (weights["match"] * match_score_normalised)
            + (weights["future"] * future_score / 10)
        )

        # ── Write scoring fields to roadmap entry ────────────────────────
        degree["total_score"] = total_score
        degree["match_score_normalised"] = match_score_normalised
        degree["future_score"] = future_score
        degree["capability_adjustment_applied"] = capability_adjustment_applied
        degree["effective_grade_used"] = effective_marks

        blend_note = " | capability blend: applied" if capability_adjustment_applied else ""
        state["thought_trace"].append(
            f"{degree_label} — RIASEC match: {match_score_normalised:.2f} | "
            f"FutureValue: {future_score} | total_score: {total_score:.2f}{blend_note}"
        )

    # ── Sort descending by total_score ────────────────────────────────────
    state["current_roadmap"] = sorted(
        current_roadmap, key=lambda x: x["total_score"], reverse=True
    )

    # ── Mismatch detection ────────────────────────────────────────────────
    state["mismatch_notice"] = None
    stated_prefs = (state.get("active_constraints") or {}).get("stated_preferences", [])

    if stated_prefs and len(state["current_roadmap"]) > 0:
        top_match_score = state["current_roadmap"][0]["total_score"]

        for pref in stated_prefs:
            pref_entries = [
                d for d in state["current_roadmap"]
                if pref.lower() in d["degree_name"].lower()
            ]
            if not pref_entries:
                continue

            pref_entry = pref_entries[0]
            pref_score = pref_entry["total_score"]
            pref_field_id = pref_entry["field_id"]
            score_gap = (top_match_score - pref_score) * 100

            if pref_field_id in lag_model:
                pref_future_value = float(lag_model[pref_field_id]["computed"]["future_value"])
            else:
                pref_future_value = 5.0

            if (
                score_gap >= settings.MISMATCH_SCORE_GAP_THRESHOLD
                and pref_future_value < settings.MISMATCH_FUTURE_VALUE_CEILING
            ):
                state["mismatch_notice"] = build_mismatch_notice(
                    preferred=pref_entry,
                    top_match=state["current_roadmap"][0],
                    gap=score_gap,
                    future_value=pref_future_value,
                )
                break

    return state
