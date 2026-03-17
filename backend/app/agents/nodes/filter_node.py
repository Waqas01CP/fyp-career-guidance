"""
filter_node.py — Eligibility filtering. Pure Python. No LLM.
Reads universities.json. Applies 5 constraint checks.
Produces three output lists: confirmed_eligible, likely_eligible, stretch.
Generates thought_trace entries for every decision.
Minimum display rule: always show >= FILTER_MINIMUM_RESULTS_SHOWN degrees.
"""
import json
from pathlib import Path
from app.agents.state import AgentState
from app.core.config import settings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _load_universities() -> list:
    path = DATA_DIR / "universities.json"
    with open(path) as f:
        return json.load(f)


def filter_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — returns empty lists until universities.json is populated.
    Sprint 3: implement full 5-check constraint filtering.

    Full implementation (Sprint 3):
    For each university → for each degree:
      1. Stream eligibility: fully_eligible_streams → confirmed | conditionally_eligible_streams → likely
      2. Mandatory subjects check
      3. Aggregate >= min_percentage_hssc
      4. Fee <= budget_per_semester
      5. Marks within 5% below cutoff_min → stretch
    Hard exclusions: stream not in either eligible list AND no waiver.
    Minimum rule: always return >= FILTER_MINIMUM_RESULTS_SHOWN by RIASEC match even if low marks.
    """
    state["thought_trace"] = []

    try:
        universities = _load_universities()
    except FileNotFoundError:
        # Data not yet populated — Sprint 1 expected
        state["current_roadmap"] = []
        state["thought_trace"].append("universities.json not found — Sprint 1 stub")
        return state

    # TODO Sprint 3: full filtering logic
    state["current_roadmap"] = []
    state["thought_trace"].append("filter_node: stub — implement in Sprint 3")
    return state
