"""
test_answer_node.py — Unit tests for AnswerNode and the fetch_fees field name fix.
All LLM calls and tool calls are mocked — no API consumption.
"""
import json
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.nodes.answer_node import answer_node
from app.agents.tools.fetch_fees import fetch_fees


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _base_state(intent: str, roadmap=None, messages=None) -> dict:
    """Minimal valid AgentState for AnswerNode tests."""
    return {
        "messages": messages or [HumanMessage(content="test question")],
        "student_profile": {
            "riasec_scores": {"R": 30, "I": 40, "A": 20, "S": 25, "E": 35, "C": 45},
            "subject_marks": {"mathematics": 80, "physics": 75, "chemistry": 70},
            "capability_scores": {"mathematics": 78, "physics": 60},
            "stream": "Pre-Engineering",
            "education_level": "inter_part2",
            "grade_system": "percentage",
        },
        "active_constraints": {
            "budget_per_semester": 60000,
            "transport_willing": True,
            "home_zone": 2,
        },
        "profiling_complete": True,
        "last_intent": intent,
        "student_mode": "inter",
        "education_level": "inter_part2",
        "current_roadmap": roadmap or [],
        "previous_roadmap": None,
        "thought_trace": [],
        "mismatch_notice": None,
        "conflict_detected": False,
    }


FAKE_FEE_DATA = {
    "university_id": "neduet",
    "university_name": "NED University of Engineering & Technology",
    "degrees": [
        {"degree_name": "BS Computer Science", "fee_per_semester": 59045},
        {"degree_name": "BS Electrical Engineering", "fee_per_semester": 59045},
    ],
}

FAKE_MARKET_DATA = {
    "field_id": "computer_science",
    "field_name": "Computer Science / Software Engineering",
    "lag_category": "FAST",
    "pakistan_now": {
        "job_postings_monthly": 12000,
        "yoy_growth_rate": 0.23,
    },
    "computed": {
        "future_value": 8.4,
    },
}

FAKE_ROADMAP = [
    {
        "degree_id": "neduet_bs_cs",
        "university_name": "NED University",
        "degree_name": "BS Computer Science",
        "total_score": 0.84,
        "merit_tier": "likely",
        "soft_flags": [],
    },
    {
        "degree_id": "neduet_bs_ee",
        "university_name": "NED University",
        "degree_name": "BS Electrical Engineering",
        "total_score": 0.72,
        "merit_tier": "likely",
        "soft_flags": [],
    },
]


# ── Tests ─────────────────────────────────────────────────────────────────────

@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.llm")
def test_fee_query_calls_fetch_fees(mock_llm, mock_fetch_fees):
    """fee_query: extraction returns 'neduet', fetch_fees returns data, AIMessage appended."""
    # Extraction call returns "neduet", answer call returns a response
    extraction_response = MagicMock()
    extraction_response.content = "neduet"
    answer_response = MagicMock()
    answer_response.content = "NED charges Rs. 59,045 per semester."
    mock_llm.invoke.side_effect = [extraction_response, answer_response]
    mock_fetch_fees.return_value = FAKE_FEE_DATA

    state = _base_state("fee_query")
    result = answer_node(state)

    assert mock_fetch_fees.called
    assert mock_fetch_fees.call_args[0][0] == "neduet"
    assert result["messages"]
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert len(last_msg.content) > 0


@patch("app.agents.nodes.answer_node.lag_calc")
@patch("app.agents.nodes.answer_node.llm")
def test_market_query_calls_lag_calc(mock_llm, mock_lag_calc):
    """market_query: extraction returns 'computer_science', lag_calc returns data, AIMessage appended."""
    extraction_response = MagicMock()
    extraction_response.content = "computer_science"
    answer_response = MagicMock()
    answer_response.content = "CS has a FutureValue of 8.4/10, indicating strong career prospects."
    mock_llm.invoke.side_effect = [extraction_response, answer_response]
    mock_lag_calc.return_value = FAKE_MARKET_DATA

    state = _base_state("market_query", messages=[HumanMessage(content="CS ka scope kya hai?")])
    result = answer_node(state)

    assert mock_lag_calc.called
    assert mock_lag_calc.call_args[0][0] == "computer_science"
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert len(last_msg.content) > 0


@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.lag_calc")
@patch("app.agents.nodes.answer_node.llm")
def test_follow_up_uses_roadmap(mock_llm, mock_lag_calc, mock_fetch_fees):
    """follow_up: AIMessage appended, no tool calls made."""
    answer_response = MagicMock()
    answer_response.content = "BS CS ranked higher because of better RIASEC match."
    mock_llm.invoke.return_value = answer_response

    state = _base_state(
        "follow_up",
        roadmap=FAKE_ROADMAP,
        messages=[HumanMessage(content="Why did BS CS rank higher than BS EE?")],
    )
    result = answer_node(state)

    assert not mock_fetch_fees.called
    assert not mock_lag_calc.called
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert len(last_msg.content) > 0


@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.lag_calc")
@patch("app.agents.nodes.answer_node.llm")
def test_out_of_scope_polite_decline(mock_llm, mock_lag_calc, mock_fetch_fees):
    """out_of_scope: AIMessage appended, no tool calls."""
    answer_response = MagicMock()
    answer_response.content = "I can only help with university and career guidance."
    mock_llm.invoke.return_value = answer_response

    state = _base_state(
        "out_of_scope",
        messages=[HumanMessage(content="Can you help me with my physics homework?")],
    )
    result = answer_node(state)

    assert not mock_fetch_fees.called
    assert not mock_lag_calc.called
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert len(last_msg.content) > 0


@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.llm")
def test_empty_tool_result_handled(mock_llm, mock_fetch_fees):
    """fee_query with empty fetch_fees result: fallback AIMessage, no answer LLM call."""
    extraction_response = MagicMock()
    extraction_response.content = "unknown_uni"
    mock_llm.invoke.return_value = extraction_response
    mock_fetch_fees.return_value = {}

    state = _base_state(
        "fee_query",
        messages=[HumanMessage(content="How much does Unknown University charge?")],
    )
    result = answer_node(state)

    # fetch_fees was called, but the answer LLM was NOT called a second time
    assert mock_fetch_fees.called
    # Only one LLM call (extraction), not two (extraction + answer)
    assert mock_llm.invoke.call_count == 1
    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    # Fallback message content
    assert "couldn't find" in last_msg.content.lower()


@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.llm")
def test_llm_failure_handled(mock_llm, mock_fetch_fees):
    """fee_query: extraction succeeds, answer LLM raises Exception, fallback AIMessage, no crash."""
    extraction_response = MagicMock()
    extraction_response.content = "neduet"
    mock_fetch_fees.return_value = FAKE_FEE_DATA
    # First call (extraction) succeeds, second call (answer) raises
    mock_llm.invoke.side_effect = [extraction_response, Exception("API error")]

    state = _base_state("fee_query")
    result = answer_node(state)

    last_msg = result["messages"][-1]
    assert isinstance(last_msg, AIMessage)
    assert "trouble" in last_msg.content.lower() or "try again" in last_msg.content.lower()


@patch("app.agents.nodes.answer_node.fetch_fees")
@patch("app.agents.nodes.answer_node.lag_calc")
@patch("app.agents.nodes.answer_node.llm")
def test_only_messages_modified(mock_llm, mock_lag_calc, mock_fetch_fees):
    """After answer_node runs, no state fields other than messages are changed."""
    answer_response = MagicMock()
    answer_response.content = "BS CS ranked higher."
    mock_llm.invoke.return_value = answer_response

    state = _base_state(
        "follow_up",
        roadmap=FAKE_ROADMAP,
        messages=[HumanMessage(content="Why did CS rank higher?")],
    )
    original_constraints = dict(state["active_constraints"])
    original_roadmap = list(state["current_roadmap"])
    original_intent = state["last_intent"]
    original_profiling = state["profiling_complete"]

    answer_node(state)

    assert state["active_constraints"] == original_constraints
    assert state["current_roadmap"] == original_roadmap
    assert state["last_intent"] == original_intent
    assert state["profiling_complete"] == original_profiling


def test_fetch_fees_field_names():
    """
    Integration test: fetch_fees('neduet') against real universities.json.
    Verifies 'name' key is used at both university and degree level.
    """
    result = fetch_fees("neduet")
    # Should return non-empty dict (NED data is in universities.json)
    assert result, "fetch_fees('neduet') returned empty dict — university not found"
    # University-level name field
    assert "university_name" in result, "Result missing 'university_name' key"
    assert result["university_name"] != "", "university_name should not be empty"
    assert result["university_name"] == "NED University of Engineering & Technology"
    # Degrees list
    assert "degrees" in result
    assert len(result["degrees"]) > 0
    # Each degree entry must have 'degree_name' (mapped from JSON 'name') and 'fee_per_semester'
    for degree in result["degrees"]:
        assert "degree_name" in degree, f"Degree entry missing 'degree_name': {degree}"
        assert degree["degree_name"] is not None, "degree_name should not be None"
        assert "fee_per_semester" in degree, f"Degree entry missing 'fee_per_semester': {degree}"
