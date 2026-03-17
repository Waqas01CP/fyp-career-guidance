"""
test_filter_node.py — FilterNode test cases using 5 student personas.
Written by Khuzzaim. Test harness written by Waqas.
Run: pytest tests/test_filter_node.py -v
"""
import pytest
from app.agents.state import AgentState
from app.agents.nodes.filter_node import filter_node

# ── 5 Student Personas ─────────────────────────────────────────────────────
# At least one triggers the mismatch notice.
# At least one hits a conditionally_eligible stream.

PERSONA_ALI = {
    "name": "Ali",
    "riasec_scores": {"R": 28, "I": 45, "A": 20, "S": 22, "E": 32, "C": 38},
    "subject_marks": {"mathematics": 87, "physics": 78, "chemistry": 72, "english": 80, "biology": 65},
    "stream": "Pre-Engineering",
    "education_level": "inter_part2",
    "student_mode": "inter",
    "capability_scores": {"mathematics": 75, "physics": 62, "chemistry": 70, "biology": 80, "english": 67},
    "budget": 60000,
    "home_zone": 2,
}

PERSONA_FATIMA = {
    "name": "Fatima",
    "riasec_scores": {"R": 15, "I": 35, "A": 22, "S": 46, "E": 28, "C": 30},
    "subject_marks": {"mathematics": 72, "physics": 68, "chemistry": 74, "english": 85, "biology": 78},
    "stream": "Pre-Medical",
    "education_level": "inter_part2",
    "student_mode": "inter",
    "capability_scores": {"mathematics": 58, "physics": 55, "chemistry": 66, "biology": 72, "english": 80},
    "budget": 80000,
    "home_zone": 3,
    # Should hit conditionally_eligible for CS (Pre-Medical requires bridge course)
}

PERSONA_AHMED = {
    "name": "Ahmed",
    "riasec_scores": {"R": 22, "I": 30, "A": 18, "S": 25, "E": 45, "C": 42},
    "subject_marks": {"mathematics": 65, "physics": 60, "chemistry": 58, "english": 72, "biology": 55},
    "stream": "Commerce",
    "education_level": "inter_part2",
    "student_mode": "inter",
    "capability_scores": {"mathematics": 50, "physics": 48, "chemistry": 52, "biology": 45, "english": 65},
    "budget": 45000,
    "home_zone": 4,
    # Should trigger mismatch notice (E+C profile but low marks for top programs)
}

PERSONA_SARA = {
    "name": "Sara",
    "riasec_scores": {"R": 32, "I": 38, "A": 40, "S": 30, "E": 22, "C": 20},
    "subject_marks": {"mathematics": 0, "physics": 0, "chemistry": 0, "english": 0, "biology": 0},
    "stream": "Pre-Engineering",
    "education_level": "matric",
    "student_mode": "matric_planning",
    "capability_scores": {},
    "budget": 70000,
    "home_zone": 1,
    # Matric planning mode — no marks yet
}

PERSONA_OMAR = {
    "name": "Omar",
    "riasec_scores": {"R": 18, "I": 28, "A": 50, "S": 35, "E": 30, "C": 15},
    "subject_marks": {"mathematics": 55, "physics": 50, "chemistry": 48, "english": 82, "biology": 60},
    "stream": "ICS",
    "education_level": "inter_part2",
    "student_mode": "inter",
    "capability_scores": {"mathematics": 42, "physics": 40, "chemistry": 45, "biology": 55, "english": 78},
    "budget": 35000,
    "home_zone": 5,
    # Low budget — many universities will be over_budget soft flag
}


def _make_state(persona: dict) -> AgentState:
    return AgentState(
        messages=[],
        student_profile={
            "riasec_scores": persona["riasec_scores"],
            "subject_marks": persona["subject_marks"],
            "capability_scores": persona["capability_scores"],
            "stream": persona["stream"],
            "education_level": persona["education_level"],
        },
        active_constraints={
            "budget_per_semester": persona["budget"],
            "transport_willing": True,
            "home_zone": persona["home_zone"],
        },
        profiling_complete=True,
        last_intent="get_recommendation",
        student_mode=persona["student_mode"],
        education_level=persona["education_level"],
        current_roadmap=[],
        previous_roadmap=None,
        thought_trace=[],
        mismatch_notice=None,
        conflict_detected=False,
    )


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.skip(reason="Sprint 1 stub — implement in Sprint 3 when universities.json is populated")
def test_ali_gets_results():
    state = _make_state(PERSONA_ALI)
    result = filter_node(state)
    assert len(result["current_roadmap"]) >= 5, "Ali should see at least 5 degree options"


@pytest.mark.skip(reason="Sprint 1 stub — implement in Sprint 3")
def test_fatima_hits_conditional_stream():
    """Pre-Medical student applying to CS should hit likely_eligible (bridge course required)."""
    state = _make_state(PERSONA_FATIMA)
    result = filter_node(state)
    cs_degrees = [d for d in result["current_roadmap"] if "computer" in d.get("degree_name", "").lower()]
    conditional = [d for d in cs_degrees if d.get("eligibility_tier") == "likely"]
    assert len(conditional) > 0, "Fatima (Pre-Medical) should see CS as conditionally eligible"


@pytest.mark.skip(reason="Sprint 1 stub — implement in Sprint 3")
def test_minimum_display_rule():
    """Even with low marks, at least 5 results must be shown."""
    state = _make_state(PERSONA_OMAR)
    result = filter_node(state)
    assert len(result["current_roadmap"]) >= 5, "Minimum 5 results always shown"


@pytest.mark.skip(reason="Sprint 1 stub — implement in Sprint 3")
def test_matric_planning_mode():
    """Matric student gets planning framing — no merit cutoff filtering."""
    state = _make_state(PERSONA_SARA)
    result = filter_node(state)
    # In matric_planning mode, planning_mode soft flag should be on all entries
    for entry in result["current_roadmap"]:
        flags = [f["type"] for f in entry.get("soft_flags", [])]
        assert "planning_mode" in flags, "All entries should have planning_mode flag for Sara"


def test_filter_node_stub_runs():
    """Sprint 1: filter_node runs without crashing even with no data."""
    state = _make_state(PERSONA_ALI)
    result = filter_node(state)
    assert "current_roadmap" in result
    assert "thought_trace" in result
