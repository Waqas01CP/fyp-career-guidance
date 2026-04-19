"""
test_supervisor_node.py — Unit tests for SupervisorNode.

No API calls — all tests mock the LLM.

Run:
    pytest backend/tests/test_supervisor_node.py -v
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import HumanMessage


# ── Fixture factory ───────────────────────────────────────────────────────────

def _make_state(messages=None, last_intent=""):
    return {
        "messages": messages if messages is not None else [HumanMessage(content="test")],
        "last_intent": last_intent,
        "student_profile": {"riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42}},
        "active_constraints": {"budget_per_semester": 50000},
        "profiling_complete": True,
        "student_mode": "inter",
        "education_level": "inter_part2",
        "current_roadmap": [{"degree_id": "neduet_bs_cs", "total_score": 0.82}],
        "previous_roadmap": None,
        "thought_trace": ["NED BS CS — stream confirmed"],
        "mismatch_notice": None,
        "conflict_detected": False,
    }


def _mock_llm_response(text: str):
    """Build a mock LLM response object with the given text."""
    mock_response = MagicMock()
    mock_response.content = text
    return mock_response


# ── Test 1: valid intent returned as-is ──────────────────────────────────────

def test_valid_intent_returned():
    """LLM returns a valid intent string — must be written to state unchanged."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm_response("market_query")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state()
        result = supervisor_node(state)
    assert result["last_intent"] == "market_query"


# ── Test 2: whitespace stripped ───────────────────────────────────────────────

def test_intent_whitespace_stripped():
    """LLM response with leading/trailing whitespace and newline is normalised."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm_response("  fee_query  \n")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state()
        result = supervisor_node(state)
    assert result["last_intent"] == "fee_query"


# ── Test 3: invalid intent falls back to follow_up ───────────────────────────

def test_invalid_intent_falls_back():
    """LLM returns an unrecognised string — must fall back to follow_up."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm_response("unknown_intent")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state()
        result = supervisor_node(state)
    assert result["last_intent"] == "follow_up"


# ── Test 4: LLM failure falls back to follow_up ──────────────────────────────

def test_llm_failure_falls_back():
    """LLM call raises an exception — must fall back to follow_up without crashing."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.side_effect = Exception("network error")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state()
        result = supervisor_node(state)
    assert result["last_intent"] == "follow_up"


# ── Test 5: empty messages handled ───────────────────────────────────────────

def test_empty_messages_handled():
    """Empty messages list — must default to get_recommendation without crashing."""
    from app.agents.nodes.supervisor import supervisor_node
    state = _make_state(messages=[])
    result = supervisor_node(state)
    assert result["last_intent"] == "get_recommendation"


# ── Test 6: only last_intent modified ────────────────────────────────────────

def test_only_last_intent_modified():
    """After supervisor_node runs, every state field except last_intent is unchanged."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm_response("fee_query")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state()
        original = {k: v for k, v in state.items() if k != "last_intent"}
        result = supervisor_node(state)

    # last_intent changed
    assert result["last_intent"] == "fee_query"
    # every other field unchanged
    for key, original_value in original.items():
        assert result[key] == original_value, f"Field '{key}' was unexpectedly modified"


# ── Test 7: Roman Urdu input classified correctly ────────────────────────────

def test_roman_urdu_classified():
    """Roman Urdu market question must produce market_query (LLM handles non-English input)."""
    with patch("app.agents.nodes.supervisor.llm") as mock_llm:
        mock_llm.invoke.return_value = _mock_llm_response("market_query")
        from app.agents.nodes.supervisor import supervisor_node
        state = _make_state(messages=[HumanMessage(content="yaar mujhe CS ka scope batao Pakistan mein")])
        result = supervisor_node(state)
    assert result["last_intent"] == "market_query"
