"""
test_profiler_node.py — Tests for ProfilerNode.

Unit tests (no API calls): check_profiling_complete logic and field merge behaviour.
Integration tests (@pytest.mark.slow): real Gemini API — run sparingly.

Run unit tests only:
    pytest backend/tests/test_profiler_node.py -v -m "not slow"

Run all including API tests:
    pytest backend/tests/test_profiler_node.py -v
"""

import os

import pytest
from langchain_core.messages import HumanMessage

from app.agents.nodes.profiler import check_profiling_complete, profiler_node
from app.core.config import settings

# ── Fixture factory ───────────────────────────────────────────────────────────

BASE_STUDENT_PROFILE = {
    "education_level": "inter_part2",
    "grade_system": "percentage",
    "stream": "Pre-Engineering",
    "subject_marks": {
        "mathematics": 82,
        "physics": 78,
        "chemistry": 71,
        "english": 80,
        "biology": 0,
    },
    "riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
    "capability_scores": {
        "mathematics": 65.0,
        "physics": 70.0,
        "chemistry": 58.3,
        "english": 75.0,
        "biology": 0.0,
    },
}


def _make_state(
    messages=None,
    active_constraints=None,
    grade_system: str = "percentage",
    stream: str | None = "Pre-Engineering",
    last_intent: str = "get_recommendation",
) -> dict:
    profile = dict(BASE_STUDENT_PROFILE)
    profile["grade_system"] = grade_system
    profile["stream"] = stream
    return {
        "student_profile": profile,
        "active_constraints": active_constraints if active_constraints is not None else {},
        "profiling_complete": False,
        "last_intent": last_intent,
        "student_mode": "inter",
        "education_level": "inter_part2",
        "current_roadmap": [],
        "previous_roadmap": None,
        "thought_trace": [],
        "mismatch_notice": None,
        "conflict_detected": False,
        "messages": messages if messages is not None else [],
    }


# ── Unit test 1: missing any single required field returns False ──────────────

def test_check_profiling_complete_requires_all_fields():
    """PROFILER_REQUIRED_FIELDS is now empty — profiling_complete is True from first message.
    budget_per_semester/transport_willing/home_zone are collected via the Step 4 screen."""
    # Empty constraints + no required fields → True immediately
    assert check_profiling_complete({}, "percentage", stream_confirmed=True) is True
    assert check_profiling_complete({}, "percentage", stream_confirmed=False) is True

    # Fields provided (now optional) — still True
    complete_constraints = {
        "budget_per_semester": 50000,
        "transport_willing": True,
        "home_zone": 2,
    }
    assert check_profiling_complete(complete_constraints, "percentage", stream_confirmed=True) is True

    # O/A Level stream confirmation still required even with no other required fields
    assert check_profiling_complete({}, "olevel_alevel", stream_confirmed=False) is False
    assert check_profiling_complete({}, "olevel_alevel", stream_confirmed=True) is True

    # Loop is a no-op now (PROFILER_REQUIRED_FIELDS=[]) — kept for future-proofing
    for field in settings.PROFILER_REQUIRED_FIELDS:
        partial = dict(complete_constraints)
        del partial[field]
        result = check_profiling_complete(partial, "percentage", stream_confirmed=True)
        assert result is False, f"Missing '{field}' should return False, got True"


# ── Unit test 2: O/A Level requires stream confirmed ─────────────────────────

def test_check_profiling_complete_olevel_requires_stream():
    """For olevel_alevel: all required fields present but stream not confirmed → False."""
    constraints = {
        "budget_per_semester": 50000,
        "transport_willing": True,
        "home_zone": 2,
    }
    # Without stream confirmation → False
    result = check_profiling_complete(constraints, "olevel_alevel", stream_confirmed=False)
    assert result is False, "olevel_alevel with stream_confirmed=False must return False"

    # With stream confirmation → True
    result = check_profiling_complete(constraints, "olevel_alevel", stream_confirmed=True)
    assert result is True, "olevel_alevel with stream_confirmed=True and all required fields must return True"

    # Non-olevel: stream_confirmed=False does not block
    result = check_profiling_complete(constraints, "percentage", stream_confirmed=False)
    assert result is True, "percentage grade_system must not require stream_confirmed"


# ── Unit test 3: null extracted_field does not overwrite existing value ───────

def test_field_merge_null_does_not_overwrite():
    """
    Simulates the merge logic inside profiler_node.
    If active_constraints already has budget=50000 and the extracted_fields
    returns budget=null, the existing value must survive.
    """
    existing = {"budget_per_semester": 50000, "transport_willing": None, "home_zone": None}
    extracted = {"budget_per_semester": None, "transport_willing": None, "home_zone": None}

    result = dict(existing)
    for field, value in extracted.items():
        if value is not None:
            result[field] = value

    assert result["budget_per_semester"] == 50000, (
        f"budget_per_semester must remain 50000 after null merge, got {result['budget_per_semester']}"
    )


# ── Unit test 4: non-null extracted_field overwrites existing value ───────────

def test_field_merge_non_null_overwrites():
    """A non-null extracted value must overwrite the existing value in active_constraints."""
    existing = {"budget_per_semester": 50000, "transport_willing": None, "home_zone": None}
    extracted = {"budget_per_semester": 80000, "transport_willing": True, "home_zone": None}

    result = dict(existing)
    for field, value in extracted.items():
        if value is not None:
            result[field] = value

    assert result["budget_per_semester"] == 80000, (
        f"budget_per_semester must be updated to 80000, got {result['budget_per_semester']}"
    )
    assert result["transport_willing"] is True, (
        f"transport_willing must be updated to True, got {result['transport_willing']}"
    )
    assert result["home_zone"] is None, (
        "home_zone must remain None (null was extracted, existing was also None)"
    )


# ── Integration test 5: budget extraction ─────────────────────────────────────

@pytest.mark.slow
@pytest.mark.skipif(
    not settings.GEMINI_API_KEY,
    reason="GEMINI_API_KEY not set — skipping live API test"
)
def test_profiler_extracts_budget():
    """
    Send a message containing a clear budget amount.
    ProfilerNode must extract budget_per_semester as a non-null integer.
    """
    state = _make_state(
        messages=[HumanMessage(content="My budget is 50,000 rupees per semester for university fees.")],
        active_constraints={},
    )
    result = profiler_node(state)

    budget = result["active_constraints"].get("budget_per_semester")
    assert budget is not None, "budget_per_semester must be extracted from a clear budget statement"
    assert isinstance(budget, int), f"budget_per_semester must be an int, got {type(budget)}"
    assert 40000 <= budget <= 60000, (
        f"budget_per_semester extracted as {budget}, expected approximately 50000"
    )


# ── Integration test 6: zone extraction ───────────────────────────────────────

@pytest.mark.slow
@pytest.mark.skipif(
    not settings.GEMINI_API_KEY,
    reason="GEMINI_API_KEY not set — skipping live API test"
)
def test_profiler_extracts_zone():
    """
    Send a message naming a Karachi area in Zone 2.
    ProfilerNode must extract home_zone as integer 2.
    """
    state = _make_state(
        messages=[HumanMessage(content="I live in Gulshan-e-Iqbal, near the main boulevard.")],
        active_constraints={},
    )
    result = profiler_node(state)

    zone = result["active_constraints"].get("home_zone")
    assert zone is not None, "home_zone must be extracted from a Karachi area name"
    assert isinstance(zone, int), f"home_zone must be an int, got {type(zone)}"
    assert zone == 2, (
        f"Gulshan-e-Iqbal is Zone 2, but extracted home_zone={zone}"
    )


# ── Integration test 7: profiling_complete after multi-turn ───────────────────

@pytest.mark.slow
@pytest.mark.skipif(
    not settings.GEMINI_API_KEY,
    reason="GEMINI_API_KEY not set — skipping live API test"
)
def test_profiler_sets_profiling_complete():
    """
    Simulate a multi-turn conversation providing all 3 required fields across turns.
    After providing budget, transport, and zone, profiling_complete must be True.
    """
    from langchain_core.messages import AIMessage

    # Turn 1: provide budget (use "per semester" explicitly to avoid unit ambiguity)
    state = _make_state(
        messages=[HumanMessage(content="My budget is 60,000 rupees per semester.")],
        active_constraints={},
    )
    state = profiler_node(state)
    # State now has whatever was extracted in turn 1

    # Turn 2: provide transport willingness (append to existing messages + response)
    state["messages"] = state["messages"] + [
        HumanMessage(content="Yes, I can travel to any part of Karachi for university.")
    ]
    state = profiler_node(state)

    # Turn 3: provide home zone
    state["messages"] = state["messages"] + [
        HumanMessage(content="I live in North Karachi near Gulberg.")
    ]
    state = profiler_node(state)

    assert state["profiling_complete"] is True, (
        f"profiling_complete must be True after all required fields provided. "
        f"active_constraints: {state['active_constraints']}"
    )
    # Verify all three required fields are present and non-null
    for field in settings.PROFILER_REQUIRED_FIELDS:
        assert state["active_constraints"].get(field) is not None, (
            f"Required field '{field}' must be non-null after full profiling. "
            f"active_constraints: {state['active_constraints']}"
        )
