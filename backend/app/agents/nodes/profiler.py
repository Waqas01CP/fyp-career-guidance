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
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
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


def _interpret_riasec(riasec: dict) -> str:
    """Convert RIASEC scores to a counsellor-readable summary.
    Never exposed directly to the student."""
    if not riasec:
        return "not yet assessed"
    sorted_dims = sorted(riasec.items(), key=lambda x: x[1], reverse=True)
    top2 = sorted_dims[:2]
    dim_names = {
        "R": "hands-on/technical",
        "I": "analytical/investigative",
        "A": "creative/artistic",
        "S": "people-oriented/social",
        "E": "leadership/entrepreneurial",
        "C": "organised/systematic",
    }
    descriptions = [dim_names.get(d, d) for d, _ in top2]
    return f"primarily {' and '.join(descriptions)}"


def _build_system_prompt(state: AgentState) -> str:
    """Build enhanced counsellor system prompt with student context injected."""
    profile = state.get("student_profile", {})
    constraints = state.get("active_constraints", {})

    missing_optional = [
        f for f in settings.PROFILER_OPTIONAL_FIELDS
        if constraints.get(f) is None
    ]

    grade_system = profile.get("grade_system", "")

    # Compact marks: omit zero-value subjects (not taken)
    marks = profile.get("subject_marks", {})
    marks_str = " | ".join(f"{k}:{v}%" for k, v in marks.items() if v != 0) or "none"

    riasec = profile.get("riasec_scores", {})
    olevel_hint = _OLEVEL_STREAM_HINT if grade_system == "olevel_alevel" else ""

    # Conversation stage detection
    messages = state.get("messages", [])
    human_messages = [m for m in messages if isinstance(m, HumanMessage)]
    conversation_turn = len(human_messages)

    # Language detection: use ONLY the most recent student message.
    # One message = one language decision — no memory of prior language choices.
    current_msg_text = human_messages[-1].content \
        if human_messages else "no messages yet"

    # RIASEC interpretation (never expose raw scores)
    riasec_summary = _interpret_riasec(riasec)

    # Capability summary (flag weak and strong subjects)
    capability = profile.get("capability_scores", {})
    weak_subjects = [s for s, v in capability.items()
                     if isinstance(v, (int, float)) and v < 65]
    strong_subjects = [s for s, v in capability.items()
                       if isinstance(v, (int, float)) and v >= 75]

    role_block = (
        "You are an expert academic career counsellor for Pakistani "
        "secondary school students seeking university admission in Karachi. "
        "You have access to the student's complete academic profile — "
        "their interest assessment (RIASEC), subject marks, capability "
        "scores, and preferences collected so far. "
        "Your job is to have a natural counselling conversation that: "
        "(1) fills important gaps in the student's profile through "
        "targeted questions, "
        "(2) helps the student articulate their interests and goals, "
        "and (3) provides brief, personalised guidance in the process.\n\n"
    )

    profile_block = (
        "STUDENT PROFILE (use to personalise — never quote numbers directly):\n"
        f"- Education: {profile.get('education_level', '?')} | "
        f"Stream: {profile.get('stream') or 'Not confirmed'}\n"
        f"- Marks: {marks_str}\n"
        f"- Strongest capability subjects: {strong_subjects or 'none yet'}\n"
        f"- Subjects needing attention: {weak_subjects or 'none'}\n"
        f"- Interest profile summary: {riasec_summary}\n"
        f"- Budget: {constraints.get('budget_per_semester', 'not set')} PKR/semester\n"
        f"- Location zone: {constraints.get('home_zone', 'not set')} "
        f"(1=Central, 2=East, 3=West, 4=North, 5=South Karachi)\n"
        f"- Transport willing: {constraints.get('transport_willing', 'not set')}\n"
        f"- Career goal: {constraints.get('career_goal', 'not stated')}\n"
        f"- Stated preferences: {constraints.get('stated_preferences', [])}\n"
        f"- Conversation turn: {conversation_turn}\n"
        f"- Missing optional info: {missing_optional}\n\n"
    )

    strategy_block = (
        "COUNSELLING STRATEGY:\n\n"

        "EARLY CONVERSATION (turns 1-3): Ask general intake questions "
        "that any student needs answered:\n"
        "  - What subject areas genuinely interest you (beyond what "
        "    grades show)?\n"
        "  - Do you have a rough idea of a career direction, even vague?\n"
        "  - Are there fields you already know you want to avoid?\n"
        "Ask ONE of these per turn if not already known. Frame as "
        "natural counsellor conversation, not a form.\n\n"

        "MID CONVERSATION (turns 4-8): Ask profile-driven questions "
        "based on what you know about THIS student:\n"
        "  - If weak subjects exist: ask how the student feels about "
        "    them — is it a challenge they want to overcome or avoid?\n"
        "  - If RIASEC shows high I (analytical): probe research/problem-"
        "    solving interest to distinguish CS vs Engineering vs Sciences\n"
        "  - If RIASEC shows high E (entrepreneurial): ask about startup "
        "    vs corporate preference\n"
        "  - If RIASEC shows high S (social): explore whether they want "
        "    direct people work (medicine, teaching) or indirect (business)\n"
        "  - If career_goal is vague: ask what a typical day in their "
        "    dream job would look like\n\n"

        "LATE CONVERSATION (turn 9+): Generate the single most useful "
        "question for THIS student given everything collected. "
        "Consider:\n"
        "  - What would most change your recommendations if you knew it?\n"
        "  - What gap in the profile has the most impact on degree fit?\n"
        "  - What has the student NOT said that a counsellor would "
        "    naturally want to know?\n\n"

        "EXTRACTION RULES (apply throughout):\n"
        "  - Extract budget from natural mentions: '50k', 'around fifty "
        "    thousand', 'can afford 40,000' → update budget_per_semester\n"
        "  - Extract transport preference: 'I can go anywhere', 'need to "
        "    stay in Gulshan', 'far is fine' → update transport_willing\n"
        "  - Extract career goals: 'want to work in AI', 'see myself in "
        "    banking', 'want to go abroad' → update career_goal and "
        "    stated_preferences\n"
        "  - Detect stream confirmations for O/A Level students\n"
        "  - Detect family constraints: 'parents want me near home', "
        "    'family prefers girls colleges' → update family_constraints\n\n"

        "RESPONSE RULES:\n"
        "  - Maximum 3-4 sentences of counselling, then ONE question\n"
        "  - Never ask more than one question per response\n"
        "  - Never mention RIASEC scores, capability scores, or "
        "    any numerical data from the profile\n"
        "  - LANGUAGE RULE: Respond in the SAME language as the "
        "    student's current message shown below. This overrides "
        "    any previous language choices. If the current message "
        "    is in English — respond in English. If Roman Urdu "
        "    (Urdu written in English letters like 'mujhe', "
        "    'kaunsa', 'chahiye') — respond in natural Roman Urdu. "
        "    If Urdu script — respond in Urdu script. Only the "
        "    current message determines the language.\n"
        f"  - Student's current message: {current_msg_text}\n"
        "  - If student asks for recommendations directly: briefly "
        "    acknowledge, say you're building their profile, ask the "
        "    most important missing question\n"
        "  - Validate and affirm student responses before asking next "
        "    question — make them feel heard\n\n"
    )

    return (role_block + profile_block + strategy_block
            + _KARACHI_ZONES + "\n" + olevel_hint + _JSON_SCHEMA)


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

    # Build message list: system + conversation history (PII-scrubbed on ALL HumanMessages)
    history = list(state.get("messages", []))
    messages_for_llm = [SystemMessage(content=system_prompt)]
    for msg in history:
        if isinstance(msg, HumanMessage):
            messages_for_llm.append(HumanMessage(content=_scrub_pii(msg.content)))
        else:
            messages_for_llm.append(msg)

    # LLM call — failure returns a clean fallback state, never crashes the node
    try:
        response = llm.invoke(messages_for_llm)
        content = response.content
        # Gemini 3.x returns content as a list of parts; flatten to string
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in content
            )
        raw_response = content.strip()
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

    # Normalise stated_preferences to list — LLM may return a string instead of list
    prefs = state["active_constraints"].get("stated_preferences")
    if isinstance(prefs, str):
        state["active_constraints"]["stated_preferences"] = [prefs]

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
