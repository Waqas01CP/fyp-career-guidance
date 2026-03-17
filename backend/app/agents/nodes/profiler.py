"""
profiler.py — Conversational profiling node.
Extracts: budget_per_semester, transport_willing, home_zone (required).
Optionally: stated_preferences, family_constraints, career_goal, student_notes.
Sets profiling_complete = True when all required fields are collected.
For O/A Level students: stream confirmation is an additional required step.
LLM call: Gemini 2.0 Flash.
"""
from app.agents.state import AgentState
from app.core.config import settings


def profiler_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — marks profiling complete with defaults for testing.
    Sprint 2: replace with real Gemini conversational extraction.
    """
    # TODO Sprint 2: call Gemini with profiler prompt to extract constraints
    # For now: set mock constraints so downstream nodes can be tested
    if not state.get("active_constraints"):
        state["active_constraints"] = {
            "budget_per_semester": 60000,
            "transport_willing": True,
            "home_zone": 2,
            "stated_preferences": [],
            "family_constraints": None,
            "career_goal": None,
            "student_notes": None,
        }

    # Check if all required fields are present
    required = settings.PROFILER_REQUIRED_FIELDS
    profile_complete = all(
        state["active_constraints"].get(field) is not None
        for field in required
    )
    state["profiling_complete"] = profile_complete
    return state
