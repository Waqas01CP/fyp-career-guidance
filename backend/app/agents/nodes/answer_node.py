"""
answer_node.py — Handles all post-recommendation queries. LLM + tools.
Intents handled: fee_query, market_query, follow_up, clarification, out_of_scope.
Tools: fetch_fees() for fee_query, lag_calc() for market_query.
For follow_up and clarification: reads current_roadmap directly, no tool call.
For out_of_scope: polite decline, no data passed.
"""
import json
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.agents.tools.fetch_fees import fetch_fees
from app.agents.tools.lag_calc import lag_calc
from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level LLM instance — same pattern as supervisor.py
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
)

# ── Extraction prompts ────────────────────────────────────────────────────────

FEE_EXTRACTION_SYSTEM_PROMPT = """Extract the university ID from the student's message.
Return only the university ID string — nothing else.

Nickname mappings (case-insensitive):
NED, NEDUET, NED University, ned university → neduet
FAST, NUCES, FAST-NUCES, Fast Nuces, fast university → fast
NUST → nust
KU, UOK, Karachi University, University of Karachi → ku
SZABIST, ZABIST → szabist
IBA, IBA Karachi → iba
AKU, Aga Khan, Aga Khan University, Aga Khan Karachi → aku

Examples:
"How much does NED charge per semester?" → neduet
"What is FAST-NUCES fee?" → fast
"Tell me about Karachi University fees" → ku

If no university is mentioned, return an empty string."""

MARKET_EXTRACTION_SYSTEM_PROMPT = """Extract the degree field ID from the student's message.
Return only the field ID string — nothing else.

Field mappings:
CS, computer science, computing → computer_science
SE, software, software engineering → software_engineering
EE, electrical, electrical engineering → electrical_engineering
AI, artificial intelligence → artificial_intelligence
civil, civil engineering → civil_engineering
mechanical, mech → mechanical_engineering
data science, data → data_science
cybersecurity, cyber, security → cybersecurity
medicine, medical, MBBS → medicine
business, BBA, management → business_administration
law, LLB → law

Examples:
"What is the job market for software engineering?" → software_engineering
"CS ka scope kya hai?" → computer_science
"mech engineering mein future kya hai?" → mechanical_engineering

If no field is mentioned, return an empty string."""

# ── Answer prompts ────────────────────────────────────────────────────────────

FEE_ANSWER_SYSTEM_PROMPT = """You are a helpful academic advisor for Pakistani students.
Answer the student's question about university fees using only the data below.
{fee_data_section}
Rules:
- Answer in 2-4 sentences. Include exact fee figures.
- If student budget is present, compare it to the fees.
- Do not invent information not in the data.
- Never say 'based on my analysis' or 'as an AI'."""

MARKET_ANSWER_SYSTEM_PROMPT = """You are a helpful academic advisor for Pakistani students.
Answer the student's question about career market prospects using only the data below.
{market_data_section}
Rules:
- Answer in 3-5 sentences.
- Cite the FutureValue score (0-10 scale) and explain what it means for career prospects.
- Mention the field's trajectory.
- Do not invent numbers not in the data.
- Never say 'based on my analysis' or 'as an AI'."""

FOLLOWUP_ANSWER_SYSTEM_PROMPT = """You are a helpful academic advisor for Pakistani students.
Answer the student's question using only information from their degree roadmap below.
{roadmap_section}
Rules:
- Answer in 2-4 sentences.
- Do not re-rank degrees. Do not invent information not in the roadmap.
- For application deadlines: frame as 'Based on the previous cycle, [University] typically
  opens applications in [month]. Check [website] for current cycle dates.'
- For improvement questions: use the student's subject_marks and
  capability_scores from the student profile above to give specific
  subject-level advice. Name the exact subject that needs improvement
  and the approximate gap to close.
- Never say 'based on my analysis' or 'as an AI'."""

OUT_OF_SCOPE_SYSTEM_PROMPT = """You are a helpful academic advisor for Pakistani students.
Politely decline in one sentence. Tell the student you can only help with university
and career guidance. Suggest they ask about their degree recommendations, fees,
or career prospects.
Never say 'based on my analysis' or 'as an AI'."""

LLM_FAILURE_FALLBACK = "I'm having trouble right now. Could you try again in a moment?"


def _flatten_content(content) -> str:
    """Flatten Gemini 3.x list-of-parts content to plain string."""
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return content


def _get_user_input(state: AgentState) -> str:
    """Extract the latest user message text from state."""
    if not state.get("messages"):
        return ""
    last = state["messages"][-1]
    return last.content if hasattr(last, "content") else str(last)


def _extract_entity(user_input: str, system_prompt: str) -> str:
    """
    Short LLM call to extract a university_id or field_id from the student message.
    Returns empty string on failure.
    """
    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ])
        content = _flatten_content(response.content)
        return content.strip().lower()
    except Exception as e:
        logger.error("AnswerNode: entity extraction LLM call failed: %s", e)
        return ""


def answer_node(state: AgentState) -> AgentState:
    """
    Handles fee_query, market_query, follow_up, clarification, out_of_scope.
    Only appends to state["messages"] — no other state field is modified.
    """
    intent = state["last_intent"]
    user_input = _get_user_input(state)

    # Build language rule from last 3 student messages — appended to every system prompt at call time
    messages = state.get("messages", [])
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    recent_human = human_msgs[-3:] if len(human_msgs) >= 3 else human_msgs
    recent_text = " | ".join(m.content for m in recent_human)
    language_rule = (
        "\n\nLANGUAGE RULE: Detect the language of the "
        "student's recent messages and respond entirely "
        "in that language. If messages contain Roman Urdu "
        "(Urdu written in English letters), respond in "
        "Roman Urdu. If Urdu script, respond in Urdu script. "
        "If English, respond in English. Do not mix languages "
        "unless the student mixes them.\n"
        f"Student's recent messages: {recent_text}\n"
    )

    # ── fee_query ─────────────────────────────────────────────────────────────
    if intent == "fee_query":
        university_id = _extract_entity(user_input, FEE_EXTRACTION_SYSTEM_PROMPT)
        if not university_id:
            state["messages"].append(AIMessage(
                content="I couldn't identify which university you're asking about. "
                        "Try asking about NED, FAST, or another university in the system."
            ))
            return state

        fee_data = fetch_fees(university_id)
        if not fee_data:
            state["messages"].append(AIMessage(
                content="I couldn't find fee information for that university. "
                        "Try asking about NED, FAST, or another university in the system."
            ))
            return state

        # Format fee data for prompt
        degree_lines = "\n".join(
            f"  - {d['degree_name']}: Rs. {d['fee_per_semester']:,}/semester"
            if d.get("fee_per_semester") and d.get("degree_name")
            else f"  - {d.get('degree_name', 'Unknown')}: fee not listed"
            for d in fee_data.get("degrees", [])
        )
        fee_section = (
            f"University: {fee_data['university_name']}\n"
            f"Degrees and fees:\n{degree_lines}"
        )
        budget = state.get("active_constraints", {}).get("budget_per_semester")
        if budget:
            fee_section += f"\nStudent's stated budget: Rs. {budget:,}/semester"

        system_prompt = FEE_ANSWER_SYSTEM_PROMPT.format(fee_data_section=fee_section) + language_rule
        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ])
            content = _flatten_content(response.content)
            state["messages"].append(AIMessage(content=content.strip()))
        except Exception as e:
            logger.error("AnswerNode: fee answer LLM call failed: %s", e)
            state["messages"].append(AIMessage(content=LLM_FAILURE_FALLBACK))
        return state

    # ── market_query ──────────────────────────────────────────────────────────
    elif intent == "market_query":
        field_id = _extract_entity(user_input, MARKET_EXTRACTION_SYSTEM_PROMPT)
        if not field_id:
            state["messages"].append(AIMessage(
                content="I couldn't identify which field you're asking about. "
                        "Try asking about computer science, electrical engineering, "
                        "or another field."
            ))
            return state

        market_data = lag_calc(field_id)
        if not market_data:
            state["messages"].append(AIMessage(
                content="I couldn't find market data for that field right now. "
                        "Try asking about computer science, electrical engineering, "
                        "or another field."
            ))
            return state

        # Format market data for prompt
        future_value = market_data.get("computed", {}).get("future_value", "N/A")
        lag_category = market_data.get("lag_category", "N/A")
        field_name = market_data.get("field_name", field_id)
        pak_now = market_data.get("pakistan_now", {})
        job_count = pak_now.get("job_postings_monthly")
        yoy = pak_now.get("yoy_growth_rate")
        career_paths = market_data.get("career_paths")

        market_section = (
            f"Field: {field_name}\n"
            f"FutureValue: {future_value}/10\n"
            f"Market trajectory category: {lag_category}"
        )
        if job_count:
            market_section += f"\nActive job postings/month in Pakistan: {job_count:,}"
        if yoy is not None:
            market_section += f"\nYear-over-year growth: {yoy * 100:.0f}%"
        if career_paths:
            market_section += f"\nCareer paths: {', '.join(career_paths)}"

        system_prompt = MARKET_ANSWER_SYSTEM_PROMPT.format(market_data_section=market_section) + language_rule
        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ])
            content = _flatten_content(response.content)
            state["messages"].append(AIMessage(content=content.strip()))
        except Exception as e:
            logger.error("AnswerNode: market answer LLM call failed: %s", e)
            state["messages"].append(AIMessage(content=LLM_FAILURE_FALLBACK))
        return state

    # ── out_of_scope ──────────────────────────────────────────────────────────
    elif intent == "out_of_scope":
        try:
            response = llm.invoke([
                SystemMessage(content=OUT_OF_SCOPE_SYSTEM_PROMPT + language_rule),
                HumanMessage(content=user_input),
            ])
            content = _flatten_content(response.content)
            state["messages"].append(AIMessage(content=content.strip()))
        except Exception as e:
            logger.error("AnswerNode: out_of_scope LLM call failed: %s", e)
            state["messages"].append(AIMessage(
                content="I can only help with university and career guidance. "
                        "Feel free to ask about your degree recommendations, fees, "
                        "or career prospects."
            ))
        return state

    # ── follow_up / clarification ─────────────────────────────────────────────
    else:
        # Slim roadmap — only fields needed for follow-up questions
        current_roadmap = state.get("current_roadmap") or []
        slim_roadmap = [
            {
                "rank": i + 1,
                "degree_name": d["degree_name"],
                "university_name": d["university_name"],
                "total_score": round(d.get("total_score", 0), 3),
                "merit_tier": d.get("merit_tier"),
                "fee_per_semester": d.get("fee_per_semester"),
                "soft_flag_types": [f["type"] for f in d.get("soft_flags", [])],
                "match_score_normalised": round(d.get("match_score_normalised", 0), 3),
                "future_score": d.get("future_score"),
                "eligibility_note": d.get("eligibility_note"),
                "aggregate_used": d.get("aggregate_used"),
            }
            for i, d in enumerate(current_roadmap)
        ]

        # Student summary — needed for improvement and eligibility questions
        student_profile = state.get("student_profile") or {}
        active_constraints = state.get("active_constraints") or {}
        student_summary = {
            "subject_marks": student_profile.get("subject_marks", {}),
            "capability_scores": student_profile.get("capability_scores", {}),
            "stream": student_profile.get("stream"),
            "budget_per_semester": active_constraints.get("budget_per_semester"),
            "stated_preferences": active_constraints.get("stated_preferences"),
            "career_goal": active_constraints.get("career_goal"),
        }

        roadmap_section = (
            "Student profile:\n"
            + json.dumps(student_summary, indent=2)
            + "\n\nDegree roadmap:\n"
            + json.dumps(slim_roadmap, indent=2)
        )
        if not current_roadmap:
            roadmap_section = "No recommendations available yet."
        system_prompt = FOLLOWUP_ANSWER_SYSTEM_PROMPT.format(roadmap_section=roadmap_section) + language_rule
        try:
            response = llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ])
            content = _flatten_content(response.content)
            state["messages"].append(AIMessage(content=content.strip()))
        except Exception as e:
            logger.error("AnswerNode: follow_up answer LLM call failed: %s", e)
            state["messages"].append(AIMessage(content=LLM_FAILURE_FALLBACK))
        return state
