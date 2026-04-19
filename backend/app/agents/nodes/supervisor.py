"""
supervisor.py — Intent classifier node.
Reads the latest user message. Classifies intent. Writes last_intent to state.
Does NOT answer the user. Does NOT modify any other state field.
LLM: ChatGoogleGenerativeAI (gemini-3.1-flash-lite-preview in dev, claude-haiku-4-5 in production).
"""
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

# Single module-level LLM instance — never hardcode model or key
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
)

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

VALID_INTENTS = {
    "get_recommendation",
    "profile_update",
    "fee_query",
    "market_query",
    "follow_up",
    "clarification",
    "out_of_scope",
}


def supervisor_node(state: AgentState) -> AgentState:
    """
    Reads the latest user message, classifies intent via LLM,
    writes last_intent to state. Only last_intent is modified.
    """
    # Guard: empty messages list
    if not state.get("messages"):
        logger.warning("SupervisorNode: no messages in state — defaulting to get_recommendation")
        state["last_intent"] = "get_recommendation"
        return state

    last_msg = state["messages"][-1]
    user_input = last_msg.content if hasattr(last_msg, "content") else str(last_msg)

    formatted_prompt = SUPERVISOR_SYSTEM_PROMPT.format(user_input=user_input)

    try:
        # Gemini 3.x requires at least one non-system message — pass instructions as
        # SystemMessage and user_input as HumanMessage to satisfy the API constraint
        response = llm.invoke([
            SystemMessage(content=formatted_prompt),
            HumanMessage(content=user_input),
        ])
        content = response.content
        # Gemini 3.x returns content as a list of parts; flatten to string
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in content
            )
        raw_response = content.strip().lower()
    except Exception as e:
        logger.error("SupervisorNode: LLM call failed: %s", e)
        state["last_intent"] = "follow_up"
        return state

    if raw_response in VALID_INTENTS:
        state["last_intent"] = raw_response
    else:
        logger.warning(
            "SupervisorNode: unexpected intent value %r — falling back to follow_up",
            raw_response,
        )
        state["last_intent"] = "follow_up"

    return state
