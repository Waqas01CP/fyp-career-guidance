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
You are an intent classifier for an academic career guidance
chatbot for Pakistani students. Classify the student's message
into exactly one of these intents:
get_recommendation, profile_update, fee_query, market_query,
follow_up, clarification, out_of_scope

CLASSIFICATION RULES (apply in order):

1. get_recommendation — student wants degree/university suggestions:
   Examples: "what degree should I do", "recommend me something",
   "which university is good for me", "suggest a career path"

2. profile_update — student is providing personal information OR
   answering a question the AI just asked:
   Examples: "200000 rs", "around 50k per month", "I live in Gulshan",
   "yes I can travel", "no I prefer nearby", "I want to be an engineer",
   "Pre-Engineering", "Karachi Board", ANY standalone number or amount,
   ANY yes/no answer, ANY location or area name, ANY subject or stream name.
   IMPORTANT: If the message looks like an answer to a previous question
   (a number, amount, location, subject name, yes/no) — always classify
   as profile_update, never out_of_scope.

3. fee_query — student asks about costs:
   Examples: "how much does NED cost", "what are FAST fees",
   "is it affordable", "fee structure"

4. market_query — student asks about careers/jobs:
   Examples: "what jobs can I get", "is CS field good in Pakistan",
   "salary in software", "future scope of electrical engineering"

5. follow_up — student references or asks about their recommendations:
   Examples: "tell me more about NED", "which one should I choose",
   "show me my options", "what about the first university you mentioned",
   "can you explain the roadmap", "which is cheapest of these"

6. clarification — student asking for explanation of something said:
   Examples: "what do you mean by merit tier", "explain RIASEC",
   "I don't understand"

7. out_of_scope — ONLY use this if the message is completely
   unrelated to education, career guidance, universities, or
   the student's own information. Examples: "write me a poem",
   "what is the weather", "tell me a joke".
   NEVER use out_of_scope for numbers, amounts, locations,
   subject names, or anything that could be an answer to a
   career guidance question.

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
