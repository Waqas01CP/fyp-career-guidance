"""
supervisor.py — Intent classifier node.
Reads the latest user message. Classifies intent. Writes last_intent to state.
Does NOT answer the user. Does NOT modify any other state field.
LLM call: Gemini 2.0 Flash.
"""
from app.agents.state import AgentState

SUPERVISOR_SYSTEM_PROMPT = """
You are an intent classifier for an academic career guidance system.
Classify the student's message into exactly one of these intents:
get_recommendation, profile_update, fee_query, market_query,
follow_up, clarification, out_of_scope

Rules:
- If the student mentions changing budget, marks, or preferences: profile_update
- If the student asks about a specific university's fees or costs: fee_query
- If the student asks about careers, jobs, or future scope: market_query
- If the student references their existing recommendations: follow_up or clarification
- If unclear between follow_up and clarification: use follow_up
- Never return anything except one of the seven intent strings above

Student message: {user_input}
Respond with only the intent string. No explanation.
"""


def supervisor_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — returns 'get_recommendation' for all inputs.
    Sprint 3: replace with real Gemini LLM call using SUPERVISOR_SYSTEM_PROMPT.
    """
    # TODO Sprint 3: call Gemini with SUPERVISOR_SYSTEM_PROMPT
    state["last_intent"] = "get_recommendation"
    return state
