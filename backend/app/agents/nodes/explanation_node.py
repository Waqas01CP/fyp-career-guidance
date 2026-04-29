"""
explanation_node.py — Production LLM response generation.
The only node the student directly experiences.
Reads: current_roadmap (top 5), student_profile, active_constraints, mismatch_notice,
       thought_trace (trimmed to top-5-relevant via degree_name/university_name match),
       previous_roadmap (for diff), student_mode.
Generates up to 4 response parts:
  Part 0: What Changed diff (if previous_roadmap not None and >= ROADMAP_SIGNIFICANT_CHANGE_COUNT changes)
  Part 1: Mismatch notice (if mismatch_notice is not None)
  Part 2: Top 5 recommendations with evidence (always)
  Part 3: Improvement advice (only for improvement_needed merit tier entries)
Language: LLM-native detection — last 2-3 student messages injected into prompt verbatim.
LLM: ChatGoogleGenerativeAI (dev) — swap to Claude Sonnet 4.6 via LLM_MODEL_NAME in config for Sprint 3+.
State writes: ONLY state["messages"] appended — all other fields are read-only.
"""
import json
import logging
import re
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Module-level LLM instance — model/key/temperature always from settings, never hardcoded
llm = ChatGoogleGenerativeAI(
    model=settings.LLM_MODEL_NAME,
    google_api_key=settings.GEMINI_API_KEY,
    temperature=settings.LLM_TEMPERATURE,
)

LLM_FAILURE_FALLBACK = (
    "I'm having trouble generating your recommendations right now. "
    "Please try again in a moment."
)

# Soft flag type → plain-language description (never expose technical names to the LLM output)
FLAG_DESCRIPTIONS: dict = {
    "over_budget": "Fee exceeds your stated budget",
    "commute_distance": "Moderate to difficult commute from your area",
    "stretch_merit": "Aggregate is slightly below the typical cutoff",
    "improvement_needed": "Significant improvement needed to reach cutoff",
    "entry_test_proxy_used": "Merit estimate uses assessment as entry test proxy",
    "entry_test_harder_than_assessed": "Entry test is harder than the capability assessment",
    "bridge_course_required": "Bridge course may be required",
    "planning_mode": "Planning mode — no merit assessment yet",
}

_PHONE_RE = re.compile(r"03\d{2}[-\s]?\d{7}")
_CNIC_RE = re.compile(r"\d{5}[-\s]\d{7}[-\s]\d")


# ── Data loading ──────────────────────────────────────────────────────────────

def _load_lag_model() -> dict:
    """Load lag_model.json and index by field_id. Called once per node invocation."""
    path = DATA_DIR / "lag_model.json"
    with open(path) as f:
        data = json.load(f)
    return {entry["field_id"]: entry for entry in data}


# ── Utilities ─────────────────────────────────────────────────────────────────

def _flatten_content(content) -> str:
    """Flatten Gemini 3.x list-of-parts content to plain string."""
    if isinstance(content, list):
        return "".join(
            p.get("text", "") if isinstance(p, dict) else str(p) for p in content
        )
    return content


def _scrub_pii(text: str) -> str:
    """Remove Pakistani phone numbers and CNICs before any LLM call."""
    text = _PHONE_RE.sub("[PHONE]", text)
    text = _CNIC_RE.sub("[CNIC]", text)
    return text


# ── Entry test advice ─────────────────────────────────────────────────────────

def _build_entry_test_advice(entry_test: dict, capability_scores: dict) -> str:
    """
    Return subject-level entry test weakness string for prompt context.
    Returns empty string if entry test not required or no capability gaps found.
    Threshold: capability score < 65% in a subject with weight > 0.
    """
    if not entry_test.get("required"):
        return ""
    lines = []
    for weight_key, subject in settings.ENTRY_TEST_SUBJECT_MAP.items():
        weight = entry_test.get(weight_key, 0.0)
        if weight > 0:
            score = capability_scores.get(subject)
            if score is not None and score < 65:
                lines.append(
                    f"{subject.replace('_', ' ').title()}: "
                    f"{weight * 100:.0f}% weight — capability {score:.0f}% (strengthen)"
                )
    if not lines:
        return ""
    return "Entry test gaps: " + " | ".join(lines)


# ── Degree context builder ────────────────────────────────────────────────────

def _build_degree_context(
    degree: dict,
    rank: int,
    lag_model: dict,
    capability_scores: dict,
) -> str:
    """
    Build compact context string for one ranked degree entry (Section 2 of prompt).
    Includes scores, tiers, fee, soft flags (via FLAG_DESCRIPTIONS), market data,
    entry test advice, and aggregate_used.
    """
    field_id = degree.get("field_id", "")
    lag_entry = lag_model.get(field_id, {})
    pak_now = lag_entry.get("pakistan_now", {})
    job_count = pak_now.get("job_postings_monthly")
    yoy = pak_now.get("yoy_growth_rate")
    career_paths = lag_entry.get("career_paths", {})

    total_score = degree.get("total_score", 0.0)
    merit_tier = degree.get("merit_tier") or "unknown"
    match_score = degree.get("match_score_normalised", 0.0)
    future_score = degree.get("future_score", 0.0)
    fee = degree.get("fee_per_semester", 0)
    aggregate_used = degree.get("aggregate_used")

    # Soft flags — converted to plain language via FLAG_DESCRIPTIONS
    soft_flags = degree.get("soft_flags", [])
    flag_texts = [
        FLAG_DESCRIPTIONS[f["type"]]
        for f in soft_flags
        if f.get("type") in FLAG_DESCRIPTIONS
    ]
    flags_str = " | ".join(flag_texts) if flag_texts else "none"

    # Market data — never pass None/null to LLM
    if job_count is not None and yoy is not None:
        market_str = (
            f"{job_count:,} active jobs/month on Rozee.pk | "
            f"trending {yoy * 100:.0f}% YoY"
        )
    elif job_count is not None:
        market_str = f"{job_count:,} active jobs/month on Rozee.pk"
    elif yoy is not None:
        market_str = f"Trending {yoy * 100:.0f}% YoY"
    elif career_paths:
        title = career_paths.get("entry_level_title", "")
        sectors = career_paths.get("common_sectors", [])
        sector_str = ", ".join(str(s) for s in sectors[:2]) if sectors else ""
        if title:
            market_str = f"Career: {title}" + (f" ({sector_str})" if sector_str else "")
        else:
            market_str = "Career data pending"
    else:
        market_str = "Career data pending"

    # Entry test advice from roadmap entry (not universities.json)
    entry_test = degree.get("entry_test", {})
    entry_advice = _build_entry_test_advice(entry_test, capability_scores)

    lines = [
        f"Rank {rank}: {degree.get('degree_name', '')} — {degree.get('university_name', '')}",
        f"  Score: {total_score:.2f} | Merit: {merit_tier} | RIASEC: {match_score:.2f} | FutureValue: {future_score:.1f}/10",
        f"  Fee: Rs. {fee:,}/semester",
        f"  Flags: {flags_str}",
        f"  Market: {market_str}",
    ]
    if entry_advice:
        lines.append(f"  {entry_advice}")
    if aggregate_used is not None:
        lines.append(f"  Aggregate: {aggregate_used:.1f}%")

    return "\n".join(lines)


# ── System prompt builder ─────────────────────────────────────────────────────

def _build_system_prompt(
    state: AgentState,
    top5: list,
    lag_model: dict,
    recent_text: str,
    prompt_trace: list,
    significant_change: bool,
    entered: set,
    dropped: set,
) -> str:
    """
    Assemble the complete system prompt for the ExplanationNode LLM call.
    All conditional logic (Part 0, Part 1, Part 3) is resolved here before the call.
    """
    profile = state.get("student_profile") or {}
    constraints = state.get("active_constraints") or {}
    student_mode = state.get("student_mode", "inter")
    mismatch_notice = state.get("mismatch_notice")

    # ── Section 1: Student profile ────────────────────────────────────────
    riasec = profile.get("riasec_scores") or {}
    dominant = sorted(riasec.items(), key=lambda x: x[1], reverse=True)[:2]
    dominant_str = ", ".join(f"{k}:{v}" for k, v in dominant) if dominant else "not available"

    subject_marks = profile.get("subject_marks") or {}
    marks_str = (
        " | ".join(f"{k.title()} {v}%" for k, v in subject_marks.items())
        if subject_marks else "not available"
    )

    capability_scores = profile.get("capability_scores") or {}
    cap_str = (
        " | ".join(f"{k.title()} {v:.0f}%" for k, v in capability_scores.items())
        if capability_scores else "not available"
    )

    education_level = profile.get("education_level", "")
    stream = profile.get("stream", "")
    budget = constraints.get("budget_per_semester")
    home_zone = constraints.get("home_zone")
    career_goal = constraints.get("career_goal")
    stated_prefs = constraints.get("stated_preferences") or []

    profile_lines = [
        "STUDENT PROFILE:",
        f"Marks: {marks_str}",
        f"RIASEC dominant: {dominant_str}",
        f"Capability: {cap_str}",
        f"Mode: {student_mode} | Level: {education_level}"
        + (f" | Stream: {stream}" if stream else ""),
    ]
    if budget and home_zone:
        profile_lines.append(f"Budget: Rs. {budget:,}/semester | Zone: {home_zone}")
    if career_goal:
        profile_lines.append(f"Career goal: {career_goal}")
    if stated_prefs:
        prefs_str = (
            ", ".join(stated_prefs)
            if isinstance(stated_prefs, list)
            else str(stated_prefs)
        )
        profile_lines.append(f"Stated preference: {prefs_str}")
    profile_section = "\n".join(profile_lines)

    # ── Section 2: Top-5 degree contexts ─────────────────────────────────
    has_improvement_needed = False
    degree_contexts = []
    for i, deg in enumerate(top5):
        ctx = _build_degree_context(deg, i + 1, lag_model, capability_scores)
        degree_contexts.append(ctx)
        if deg.get("merit_tier") == "improvement_needed":
            has_improvement_needed = True
    degrees_section = "\n\n".join(degree_contexts)

    # ── Section 3: Mismatch notice ────────────────────────────────────────
    mismatch_section = (
        f"MISMATCH NOTICE:\n{mismatch_notice}" if mismatch_notice else ""
    )

    # ── Reasoning trace (trimmed to top-5-relevant) ───────────────────────
    trace_section = (
        "REASONING TRACE:\n" + "\n".join(prompt_trace)
    ) if prompt_trace else ""

    # ── Section 4: Instructions ───────────────────────────────────────────

    # Part 0 — What Changed (only when significant_change)
    part0_instr = ""
    if significant_change and (entered or dropped):
        entered_names = ", ".join(entered) if entered else "none"
        dropped_names = ", ".join(dropped) if dropped else "none"
        part0_instr = (
            f"Part 0 — What Changed: Open by briefly noting changes since last run: "
            f"newly in top-5: {entered_names} | dropped from top-5: {dropped_names}. "
            "One sentence max.\n"
        )

    # Part 1 — Mismatch (only when mismatch_notice is set)
    part1_instr = ""
    if mismatch_notice:
        part1_instr = (
            "Part 1 — Mismatch: Explain the mismatch notice transparently — "
            "an honest observation, not a rejection. Use the data provided.\n"
        )

    # Core instructions (mode-dependent)
    if student_mode == "matric_planning":
        core_instr = (
            "INSTRUCTIONS — You are an academic career advisor for Pakistani students.\n"
            "Write a PLANNING response (student has not started Inter yet).\n"
            "Rules:\n"
            "- Address student directly, second person\n"
            "- Frame as 'degrees you could reach' — future-oriented, not current eligibility\n"
            "- Explain what stream and marks the student needs to reach each degree\n"
            "- Do NOT discuss current admission likelihood or merit cutoffs\n"
            "- Surface flags in plain language — never use technical flag names\n"
            "- If job numbers present: cite them (e.g. '1,240 active jobs/month on Rozee.pk')\n"
            "- Never say 'based on my analysis' or 'as an AI'\n"
            "- Do not invent data not shown above\n"
            "- End with one open question inviting follow-up\n"
            "- Conversational length — help, don't overwhelm"
        )
    else:
        core_instr = (
            "INSTRUCTIONS — You are an academic career advisor for Pakistani students.\n"
            "Write a RECOMMENDATION response.\n"
            "Rules:\n"
            "- Address student directly, second person\n"
            "- Explain WHY each degree suits them using specific numbers "
            "(RIASEC match, marks, capability scores)\n"
            "- Surface flags in plain language — never use technical flag names\n"
            "- For improvement_needed entries: give subject-specific advice "
            "using their marks and capability scores\n"
            "- If job numbers present: cite them (e.g. '1,240 active jobs/month on Rozee.pk')\n"
            "- Never say 'based on my analysis' or 'as an AI'\n"
            "- Do not invent data not shown above\n"
            "- End with one open question inviting follow-up\n"
            "- Conversational length — help, don't overwhelm"
        )

    # Part 3 — Improvement path (only when at least one improvement_needed entry)
    part3_instr = ""
    if has_improvement_needed:
        part3_instr = (
            "\nPart 3 — Improvement path: For any degree with merit tier "
            "'improvement_needed', give concrete subject-level advice — "
            "name the exact subject, cite the gap, be specific."
        )

    # Language rule — determined solely by the current (most recent) student message.
    # Label kept as "Student's recent messages" to avoid breaking existing tests.
    lang_rule = (
        "LANGUAGE RULE: Respond in the SAME language as the "
        "student's current message shown below. This overrides "
        "any previous language choices.\n"
        "If the current message is in English — respond in English.\n"
        "If the current message is in Roman Urdu (Urdu written "
        "in English letters like 'mujhe', 'kaunsa', 'chahiye') "
        "— respond in natural conversational Roman Urdu.\n"
        "If the current message is in Urdu script — respond in "
        "Urdu script.\n"
        "Do not use the language of previous messages. Only the "
        "current message determines the response language.\n"
        f"Student's recent messages: {recent_text}\n"
    )

    # ── Assemble ──────────────────────────────────────────────────────────
    parts = [
        lang_rule,
        "",
        profile_section,
        "",
        "TOP 5 DEGREES:",
        degrees_section,
    ]
    if mismatch_section:
        parts += ["", mismatch_section]
    if trace_section:
        parts += ["", trace_section]
    parts += ["", part0_instr + part1_instr + core_instr + part3_instr]

    return "\n".join(parts).strip()


# ── Node entry point ──────────────────────────────────────────────────────────

def explanation_node(state: AgentState) -> AgentState:
    """
    Production ExplanationNode. Generates up to 4-part LLM recommendation response.
    Only state["messages"] is modified — all other AgentState fields are read-only.
    """
    lag_model = _load_lag_model()

    messages = state.get("messages") or []

    # Language detection: use ONLY the most recent student message.
    # One message = one language decision — no memory of prior language choices.
    human_msgs = [m for m in messages if isinstance(m, HumanMessage)]
    current_msg_text = _scrub_pii(human_msgs[-1].content) if human_msgs else ""

    # Thought trace trimming — match on degree_name and university_name
    # FilterNode traces: "{university_name} {degree_name}" format
    # ScoringNode traces: "{degree_name} ({university_abbrev})" format
    # Neither contains degree_id — degree_id matching always produces empty trace
    current_roadmap = state.get("current_roadmap") or []
    top5_names = [d["degree_name"] for d in current_roadmap[:5]]
    top5_unis = [d["university_name"] for d in current_roadmap[:5]]
    prompt_trace = [
        t for t in state.get("thought_trace", [])
        if any(name in t for name in top5_names)
        or any(uni in t for uni in top5_unis)
    ]

    # Rerun diff for Part 0
    previous_roadmap = state.get("previous_roadmap") or []
    top5 = current_roadmap[:5]

    if previous_roadmap:
        prev_top5 = {d["degree_id"] for d in previous_roadmap[:5]}
        curr_top5 = {d["degree_id"] for d in top5}
        entered = curr_top5 - prev_top5
        dropped = prev_top5 - curr_top5
        significant_change = (
            (len(entered) + len(dropped)) >= settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT
        )
    else:
        significant_change = False
        entered = set()
        dropped = set()

    # Extract last user message as LLM trigger — PII scrubbed
    user_trigger = ""
    if messages:
        last = messages[-1]
        content = last.content if hasattr(last, "content") else str(last)
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in content
            )
        user_trigger = _scrub_pii(str(content))

    system_prompt = _build_system_prompt(
        state=state,
        top5=top5,
        lag_model=lag_model,
        recent_text=current_msg_text,
        prompt_trace=prompt_trace,
        significant_change=significant_change,
        entered=entered,
        dropped=dropped,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_trigger or "Please generate my degree recommendations."),
        ])
        content = _flatten_content(response.content)
        state["messages"].append(AIMessage(content=content.strip()))
    except Exception as e:
        logger.error("ExplanationNode: LLM call failed: %s", e)
        state["messages"].append(AIMessage(content=LLM_FAILURE_FALLBACK))

    return state
