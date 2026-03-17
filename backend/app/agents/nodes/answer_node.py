"""
answer_node.py — Handles all post-recommendation queries. LLM + tools.
Intents handled: fee_query, market_query, follow_up, clarification, out_of_scope.
Tools: fetch_fees() for fee_query, lag_calc() for market_query.
For follow_up and clarification: reads current_roadmap directly, no tool call needed.
No status SSE event emitted for follow_up/clarification (no tool call = no wait state).
"""
from langchain_core.messages import AIMessage
from app.agents.state import AgentState
from app.agents.tools.fetch_fees import fetch_fees
from app.agents.tools.lag_calc import lag_calc


def answer_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — returns a placeholder response.
    Sprint 3: implement tool dispatch + LLM answer generation.

    Full implementation (Sprint 3):
    intent = state["last_intent"]
    if intent == "fee_query":
        entity = extract_university(state)  # LLM extracts from message
        data = fetch_fees(entity)
    elif intent == "market_query":
        field = extract_field(state)
        data = lag_calc(field)
    else:  # follow_up, clarification, out_of_scope
        data = state["current_roadmap"]
    response = llm.invoke(build_answer_prompt(intent, data, state))
    """
    stub_response = "AnswerNode stub — implement in Sprint 3."
    state["messages"].append(AIMessage(content=stub_response))
    return state
