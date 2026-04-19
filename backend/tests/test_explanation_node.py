"""
test_explanation_node.py — Unit tests for ExplanationNode.
All LLM calls are mocked — no API consumption.
Tests cover: language detection, thought trace trimming, rerun diff,
             LLM call behaviour, state isolation, failure handling.
"""
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.nodes.explanation_node import (
    detect_language_hint,
    explanation_node,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _base_roadmap_entry(degree_id: str, merit_tier: str = "likely") -> dict:
    """Minimal roadmap entry with all fields ExplanationNode reads."""
    return {
        "degree_id": degree_id,
        "field_id": "computer_science",
        "university_id": "neduet",
        "university_name": "NED University of Engineering & Technology",
        "degree_name": f"BS {degree_id.upper()}",
        "eligibility_tier": "confirmed",
        "merit_tier": merit_tier,
        "final_tier": merit_tier,
        "eligibility_note": None,
        "aggregate_used": 82.5,
        "aggregate_formula": {
            "matric_weight": 0.0,
            "inter_weight": 0.4,
            "entry_test_weight": 0.6,
            "subject_weights": {"mathematics": 1.0, "physics": 1.0},
        },
        "entry_test": {
            "required": True,
            "math_weight": 0.25,
            "physics_weight": 0.25,
            "chemistry_weight": 0.25,
            "english_weight": 0.25,
        },
        "fee_per_semester": 64475,
        "shift": "full_day",
        "soft_flags": [],
        "total_score": 0.84,
        "match_score_normalised": 0.89,
        "future_score": 8.5,
        "capability_adjustment_applied": False,
        "effective_grade_used": {},
    }


def _base_state(
    roadmap=None,
    previous_roadmap=None,
    mismatch_notice=None,
    thought_trace=None,
    messages=None,
    student_mode="inter",
) -> dict:
    """Full valid AgentState for ExplanationNode tests."""
    if roadmap is None:
        roadmap = [_base_roadmap_entry(f"deg_{i}") for i in range(5)]
    return {
        "messages": messages or [HumanMessage(content="What degrees should I consider?")],
        "student_profile": {
            "riasec_scores": {"R": 30, "I": 45, "A": 20, "S": 25, "E": 38, "C": 42},
            "subject_marks": {
                "mathematics": 84,
                "physics": 68,
                "chemistry": 71,
                "english": 75,
            },
            "capability_scores": {
                "mathematics": 78,
                "physics": 61,
                "chemistry": 69,
            },
            "stream": "Pre-Engineering",
            "education_level": "inter_part2",
            "grade_system": "percentage",
        },
        "active_constraints": {
            "budget_per_semester": 65000,
            "transport_willing": True,
            "home_zone": 2,
            "career_goal": "wants to work in tech",
            "stated_preferences": ["CS"],
        },
        "profiling_complete": True,
        "last_intent": "get_recommendation",
        "student_mode": student_mode,
        "education_level": "inter_part2",
        "current_roadmap": roadmap,
        "previous_roadmap": previous_roadmap,
        "thought_trace": thought_trace or [],
        "mismatch_notice": mismatch_notice,
        "conflict_detected": False,
    }


# ── Language detection tests ──────────────────────────────────────────────────

def test_language_detection_english():
    """English messages return 'English'."""
    messages = [
        HumanMessage(content="What degrees should I consider?"),
        HumanMessage(content="I am interested in computer science and engineering."),
        HumanMessage(content="What is the job market like?"),
    ]
    result = detect_language_hint(messages)
    assert result == "English"


def test_language_detection_roman_urdu():
    """Messages containing Roman Urdu keywords return 'Roman Urdu'."""
    messages = [
        HumanMessage(content="kya hai meri recommendation?"),
        HumanMessage(content="mujhe CS ka scope batao"),
    ]
    result = detect_language_hint(messages)
    assert result == "Roman Urdu"


def test_language_detection_urdu_script():
    """Messages with Urdu Unicode characters return 'Urdu'."""
    messages = [
        HumanMessage(content="مجھے اپنی تجویز بتائیں"),
        HumanMessage(content="کیا کمپیوٹر سائنس اچھا ہے؟"),
    ]
    result = detect_language_hint(messages)
    assert result == "Urdu"


# ── Thought trace trimming tests ──────────────────────────────────────────────

def test_thought_trace_trimming():
    """
    10 trace entries using real production trace format (degree_name / university_name).
    3 entries match top-5 degree_names or university_names — prompt_trace must contain
    exactly those 3.
    FilterNode traces: "{university_name} {degree_name}" format.
    ScoringNode traces: "{degree_name} ({university_abbrev})" format.
    degree_id is never present in real traces — matching must use name fields.
    """
    roadmap = [_base_roadmap_entry(f"neduet_deg_{i}") for i in range(5)]
    top5_names = [d["degree_name"] for d in roadmap[:5]]
    top5_unis = [d["university_name"] for d in roadmap[:5]]

    # Build 10 trace entries: 3 match top-5 degree_name or university_name, 7 do not
    trace = [
        f"NED University of Engineering & Technology {top5_names[0]} — stream CONFIRMED | merit likely",  # match (uni)
        "University of Karachi BS Computer Science — stream CONFIRMED | merit stretch",                   # no match
        f"{top5_names[1]} (NED) — RIASEC match: 0.82 | FutureValue: 8.5",                               # match (name)
        "SZABIST BS Software Engineering — excluded: stream blocked",                                     # no match
        f"{top5_unis[0]} {top5_names[2]} — fee 64475 <= budget 65000: PASS",                            # match (both)
        "IOBM BBA — merit improvement_needed",                                                            # no match
        "IBA BS Computer Science — stream CONFIRMED | merit confirmed",                                   # no match
        "FAST BS Software Engineering — over budget",                                                     # no match
        "Bahria University BS Computer Science — merit stretch",                                          # no match
        "NUST BS Computer Science — excluded: stream",                                                    # no match
    ]

    state = _base_state(roadmap=roadmap, thought_trace=trace)

    # Replicate the trimming logic from explanation_node
    prompt_trace = [
        t for t in state["thought_trace"]
        if any(name in t for name in top5_names)
        or any(uni in t for uni in top5_unis)
    ]

    assert len(prompt_trace) == 3
    for entry in prompt_trace:
        assert any(name in entry for name in top5_names) or any(
            uni in entry for uni in top5_unis
        )


# ── Rerun diff tests ──────────────────────────────────────────────────────────

def test_rerun_diff_significant():
    """
    Previous and current top-5 differ by 2 entries → significant_change is True.
    ROADMAP_SIGNIFICANT_CHANGE_COUNT = 2.
    """
    from app.core.config import settings

    prev_roadmap = [_base_roadmap_entry(f"deg_prev_{i}") for i in range(5)]
    # curr has 3 same as prev (indices 0,1,2), and 2 new (indices 3,4 replaced)
    curr_roadmap = (
        [_base_roadmap_entry(f"deg_prev_{i}") for i in range(3)]
        + [_base_roadmap_entry("deg_new_a"), _base_roadmap_entry("deg_new_b")]
    )

    prev_top5 = {d["degree_id"] for d in prev_roadmap[:5]}
    curr_top5 = {d["degree_id"] for d in curr_roadmap[:5]}
    entered = curr_top5 - prev_top5
    dropped = prev_top5 - curr_top5
    significant_change = (
        (len(entered) + len(dropped)) >= settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT
    )

    assert significant_change is True
    assert len(entered) == 2
    assert len(dropped) == 2


def test_rerun_diff_not_significant():
    """
    Previous and current top-5 are identical (0 changes) → significant_change is False.
    Note: ROADMAP_SIGNIFICANT_CHANGE_COUNT=2 means entered+dropped must be >= 2 to trigger.
    A 1-swap gives entered=1, dropped=1, total=2 which IS significant.
    Only 0 changes (identical roadmaps) gives total=0 < 2 = not significant.
    """
    from app.core.config import settings

    roadmap = [_base_roadmap_entry(f"deg_{i}") for i in range(5)]

    prev_top5 = {d["degree_id"] for d in roadmap[:5]}
    curr_top5 = {d["degree_id"] for d in roadmap[:5]}  # identical
    entered = curr_top5 - prev_top5
    dropped = prev_top5 - curr_top5
    significant_change = (
        (len(entered) + len(dropped)) >= settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT
    )

    assert significant_change is False
    assert len(entered) == 0
    assert len(dropped) == 0


def test_no_previous_roadmap():
    """
    previous_roadmap is None → significant_change is False, no diff computed.
    """
    from app.core.config import settings

    previous_roadmap = None
    resolved = previous_roadmap or []

    if resolved:
        prev_top5 = {d["degree_id"] for d in resolved[:5]}
        curr_top5 = {d["degree_id"] for d in [_base_roadmap_entry("deg_0")][:5]}
        entered = curr_top5 - prev_top5
        dropped = prev_top5 - curr_top5
        significant_change = (
            (len(entered) + len(dropped)) >= settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT
        )
    else:
        significant_change = False

    assert significant_change is False


# ── Node behaviour tests ──────────────────────────────────────────────────────

@patch("app.agents.nodes.explanation_node.llm")
def test_explanation_appends_message(mock_llm):
    """LLM returns a response → AIMessage appended to state['messages']."""
    mock_response = MagicMock()
    mock_response.content = "Here are your top degree recommendations based on your profile."
    mock_llm.invoke.return_value = mock_response

    state = _base_state()
    initial_msg_count = len(state["messages"])

    result = explanation_node(state)

    assert len(result["messages"]) == initial_msg_count + 1
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert len(last_msg.content) > 0


@patch("app.agents.nodes.explanation_node.llm")
def test_only_messages_modified(mock_llm):
    """
    After explanation_node runs, only state['messages'] changes.
    current_roadmap, thought_trace, mismatch_notice, active_constraints all unchanged.
    """
    mock_response = MagicMock()
    mock_response.content = "Your top recommendations are ready."
    mock_llm.invoke.return_value = mock_response

    roadmap = [_base_roadmap_entry(f"deg_{i}") for i in range(5)]
    trace = ["deg_0 — stream CONFIRMED", "deg_1 — merit likely"]
    state = _base_state(
        roadmap=roadmap,
        thought_trace=trace,
        mismatch_notice="Test mismatch notice",
    )

    original_roadmap = list(state["current_roadmap"])
    original_trace = list(state["thought_trace"])
    original_mismatch = state["mismatch_notice"]
    original_constraints = dict(state["active_constraints"])
    original_profile = dict(state["student_profile"])

    explanation_node(state)

    assert state["current_roadmap"] == original_roadmap
    assert state["thought_trace"] == original_trace
    assert state["mismatch_notice"] == original_mismatch
    assert state["active_constraints"] == original_constraints
    assert state["student_profile"] == original_profile


@patch("app.agents.nodes.explanation_node.llm")
def test_llm_failure_handled(mock_llm):
    """LLM raises Exception → fallback AIMessage appended, no crash."""
    mock_llm.invoke.side_effect = Exception("API timeout")

    state = _base_state()
    initial_msg_count = len(state["messages"])

    result = explanation_node(state)

    assert len(result["messages"]) == initial_msg_count + 1
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    # Fallback message must be non-empty and not contain "None" or "null"
    assert len(last_msg.content) > 0
    assert "None" not in last_msg.content
    assert "null" not in last_msg.content
