"""
scoring_node.py — RIASEC match scoring + FutureValue + capability blend. Pure Python. No LLM.
Reads affinity_matrix.json and lag_model.json.
Computes total_score = (weight_match * match_score_normalised) + (weight_future * future_score/10).
Applies capability blend when abs(capability - reported_grade) >= CAPABILITY_BLEND_THRESHOLD.
Detects aptitude-preference mismatch and sets mismatch_notice.
"""
import json
from pathlib import Path
from app.agents.state import AgentState
from app.core.config import settings

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


def scoring_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — passes current_roadmap through unchanged.
    Sprint 3: implement full RIASEC dot product + FutureValue + capability blend.

    Full implementation (Sprint 3):
    student_vector = [R, I, A, S, E, C] from riasec_scores (values 10-50)
    For each degree in current_roadmap:
      raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
      theoretical_max = sum(s * 10 for s in student_vector)
      match_score_normalised = raw_match / theoretical_max
      future_score = lag_model[field_id]["computed"]["future_value"]  # 0-10
      weights = SCORING_WEIGHTS[student_mode]
      total_score = (weights["match"] * match_score_normalised) + (weights["future"] * future_score / 10)
    Apply capability blend if gap >= CAPABILITY_BLEND_THRESHOLD.
    Detect mismatch: if stated_preference score is MISMATCH_SCORE_GAP_THRESHOLD below top match
                     AND preferred degree FutureValue < MISMATCH_FUTURE_VALUE_CEILING.
    """
    # TODO Sprint 3: full scoring implementation
    state["mismatch_notice"] = None
    state["thought_trace"].append("scoring_node: stub — implement in Sprint 3")
    return state
