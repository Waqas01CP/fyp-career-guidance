"""
explanation_node.py — LLM response generation. The only node the student directly experiences.
Reads: current_roadmap (top 5), student_profile, active_constraints, mismatch_notice,
       thought_trace (trimmed to top-5-relevant), previous_roadmap (for diff), student_mode.
Generates up to 4 response parts:
  Part 0: What Changed diff (if previous_roadmap exists and >= ROADMAP_SIGNIFICANT_CHANGE_COUNT changes)
  Part 1: Mismatch notice (if mismatch_notice is not None)
  Part 2: Top 5 recommendations with evidence (always)
  Part 3: Improvement advice (only for improvement_needed merit tier entries)
Language: detected from last 2-3 student messages — responds in same language (English or Roman Urdu).
LLM: Gemini 2.0 Flash (Sprint 2), Claude Sonnet 4.6 (Sprint 3+).
"""
from langchain_core.messages import AIMessage
from app.agents.state import AgentState


def explanation_node(state: AgentState) -> AgentState:
    """
    Sprint 1 STUB — returns a placeholder text message.
    Sprint 3: implement full 4-part LLM response with prompt structure.
    """
    # TODO Sprint 3: build full prompt from student data + roadmap + mismatch + trace
    # TODO Sprint 3: call Gemini/Claude, stream response chunks via SSE
    stub_response = (
        "I have analysed your profile. The recommendation pipeline is not yet fully "
        "connected — this stub will be replaced in Sprint 3 with real AI-generated "
        "recommendations based on your RIASEC profile, marks, budget, and market data."
    )
    state["messages"].append(AIMessage(content=stub_response))
    state["thought_trace"].append("explanation_node: stub — implement in Sprint 3")
    return state
