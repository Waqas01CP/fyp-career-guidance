"""
profiler.py — Conversational profiling node (LLM).
Extracts: budget_per_semester, transport_willing, home_zone (required).
Optionally: stated_preferences, family_constraints, career_goal, student_notes.
Sets profiling_complete = True when all required fields are collected.
For O/A Level students: stream confirmation is an additional required step.
LLM: ChatGoogleGenerativeAI (langchain_google_genai wrapper).
"""
import json
import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

# Single module-level LLM instance — never hardcode model or key
# temperature=0: deterministic JSON output — Gemini drops JSON format at high temperature
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0,
)

# PII patterns — scrubbed from user input before every LLM call
_PII_PATTERNS = [
    (re.compile(r"03\d{2}[-\s]?\d{7}"), "[PHONE]"),
    (re.compile(r"\d{5}[-\s]\d{7}[-\s]\d"), "[CNIC]"),
]

_KARACHI_ZONES = (
    "Karachi zones (map area names to home_zone int 1-5):\n"
    "1=North (North Karachi, Gulberg, New Karachi, Surjani)\n"
    "2=Central (Gulshan-e-Iqbal, Johar, Nazimabad, North Nazimabad)\n"
    "3=South (Defence, Clifton, Saddar, PECHS, Bahadurabad)\n"
    "4=East (Malir, Landhi, Korangi, Shah Faisal)\n"
    "5=West (SITE, Orangi, Baldia, Lyari)\n"
)

_OLEVEL_STREAM_HINT = (
    "O/A Level stream inference (present to student and ask to confirm):\n"
    "- Physics+Chemistry+Maths → Pre-Engineering\n"
    "- Physics+Chemistry+Biology → Pre-Medical\n"
    "- Maths+Computer Science+Physics/Chemistry → ICS\n"
    "- Business Studies+Accounting+Economics → Commerce\n"
    "- Unusual combination: present 2 closest options, ask student to choose\n"
)

_JSON_SCHEMA = """\
CRITICAL: Your ENTIRE response must be valid JSON. Start with { and end with }.
No text before or after. No markdown. No explanation outside the JSON.
{
  "reply_to_student": "your conversational reply here",
  "extracted_fields": {
    "budget_per_semester": null,
    "transport_willing": null,
    "home_zone": null,
    "stated_preferences": null,
    "family_constraints": null,
    "career_goal": null,
    "student_notes": null
  },
  "profiling_complete": false,
  "confirmed_stream": null
}"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _scrub_pii(text: str) -> str:
    for pattern, replacement in _PII_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def check_profiling_complete(
    active_constraints: dict,
    grade_system: str,
    stream_confirmed: bool,
) -> bool:
    """True only when all required fields are present (and stream confirmed for O/A Level)."""
    base_complete = all(
        active_constraints.get(field) is not None
        for field in settings.PROFILER_REQUIRED_FIELDS
    )
    if grade_system == "olevel_alevel":
        return base_complete and stream_confirmed
    return base_complete


def _parse_llm_response(raw: str) -> dict:
    """Parse LLM JSON response. On failure returns fallback with raw text as reply."""
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("ProfilerNode: malformed JSON from LLM — using raw as reply. Preview: %s", raw[:200])
        return {
            "reply_to_student": raw,
            "extracted_fields": {},
            "profiling_complete": False,
            "confirmed_stream": None,
        }


def _build_system_prompt(state: AgentState) -> str:
    """Build lean, directive system prompt with student context injected."""
    profile = state.get("student_profile", {})
    constraints = state.get("active_constraints", {})

    missing_required = [
        f for f in settings.PROFILER_REQUIRED_FIELDS
        if constraints.get(f) is None
    ]
    missing_optional = [
        f for f in settings.PROFILER_OPTIONAL_FIELDS
        if constraints.get(f) is None
    ]

    grade_system = profile.get("grade_system", "")

    # Compact marks: omit zero-value subjects (not taken)
    marks = profile.get("subject_marks", {})
    marks_str = " | ".join(f"{k}:{v}%" for k, v in marks.items() if v != 0) or "none"

    # Compact RIASEC (internal reference — never shown verbatim to student)
    riasec = profile.get("riasec_scores", {})
    riasec_str = " ".join(f"{k}:{v}" for k, v in riasec.items()) or "none"

    olevel_hint = _OLEVEL_STREAM_HINT if grade_system == "olevel_alevel" else ""

    prompt = (
        "You are the profiling assistant for an academic career guidance system "
        "for Pakistani students. Your job: collect missing information through "
        "natural, friendly conversation.\n\n"
        "Student context:\n"
        f"- Education: {profile.get('education_level', '?')} | "
        f"Grade system: {grade_system} | "
        f"Stream: {profile.get('stream') or 'Not set'}\n"
        f"- Marks: {marks_str}\n"
        f"- RIASEC profile: {riasec_str}\n"
        f"- Collected so far: {json.dumps(constraints, ensure_ascii=False)}\n"
        f"- Missing required fields: {missing_required}\n"
        f"- Missing optional fields: {missing_optional}\n"
        f"- Current intent: {state.get('last_intent', '')}\n\n"
        f"{_KARACHI_ZONES}\n"
        f"{olevel_hint}"
        "Rules:\n"
        "- Ask ONE missing required field at a time, conversationally — not like a form\n"
        "- Confirm each collected field in one sentence before asking the next\n"
        "- If intent=profile_update: acknowledge what changed, confirm update, "
        "then check if more fields still needed\n"
        "- Respond in the same language the student uses (English, Urdu, or Roman Urdu)\n"
        "- Never mention RIASEC scores or capability scores directly to the student\n"
        "- For olevel_alevel students: stream confirmation is REQUIRED before "
        "setting profiling_complete=true — present inferred stream and ask to confirm\n"
        "- home_zone must be an integer 1-5 (use zone table above to map area names)\n"
        "- budget_per_semester must be an integer in PKR (handle '50k', 'fifty thousand', "
        "'around 50,000' — all mean 50000)\n"
        "- transport_willing is true if student can travel anywhere in Karachi, "
        "false if they need to stay near their area\n\n"
    )
    return prompt + _JSON_SCHEMA


# ── Main node function ─────────────────────────────────────────────────────────

def profiler_node(state: AgentState) -> AgentState:
    """
    LLM-based conversational profiling node.
    Extracts budget, transport_willing, home_zone (required) plus optional fields.
    Sets profiling_complete = True when all required fields are collected.
    """
    # Ensure active_constraints exists
    if "active_constraints" not in state or state["active_constraints"] is None:
        state["active_constraints"] = {}

    # Build system prompt with current student context
    system_prompt = _build_system_prompt(state)

    # Build message list: system + conversation history (PII-scrubbed on last human message)
    history = list(state.get("messages", []))
    messages_for_llm = [SystemMessage(content=system_prompt)]
    for i, msg in enumerate(history):
        if i == len(history) - 1 and isinstance(msg, HumanMessage):
            messages_for_llm.append(HumanMessage(content=_scrub_pii(msg.content)))
        else:
            messages_for_llm.append(msg)

    # LLM call — failure returns a clean fallback state, never crashes the node
    try:
        response = llm.invoke(messages_for_llm)
        raw_response = response.content.strip()
    except Exception as e:
        logger.error("ProfilerNode: LLM call failed: %s", e)
        state["messages"] = list(state.get("messages", [])) + [
            AIMessage(content=(
                "I'm having trouble processing your request right now. "
                "Could you try again in a moment?"
            ))
        ]
        return state

    # Parse structured response
    parsed = _parse_llm_response(raw_response)

    # Merge extracted_fields — null values never overwrite existing non-null values
    extracted = parsed.get("extracted_fields", {})
    current_constraints = dict(state["active_constraints"])
    for field, value in extracted.items():
        if value is not None:
            current_constraints[field] = value
    state["active_constraints"] = current_constraints

    # Handle O/A Level stream confirmation
    confirmed_stream = parsed.get("confirmed_stream")
    grade_system = state["student_profile"].get("grade_system", "")
    if confirmed_stream and grade_system == "olevel_alevel":
        state["student_profile"]["stream"] = confirmed_stream

    # Check profiling complete — Python code is authoritative, not the LLM flag
    stream_confirmed = state["student_profile"].get("stream") is not None
    state["profiling_complete"] = check_profiling_complete(
        active_constraints=state["active_constraints"],
        grade_system=grade_system,
        stream_confirmed=stream_confirmed,
    )

    # Append the LLM's reply to the conversation
    reply = parsed.get("reply_to_student", "")
    state["messages"] = list(state.get("messages", [])) + [AIMessage(content=reply)]

    return state
