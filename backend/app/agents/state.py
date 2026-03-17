"""
state.py — AgentState TypedDict.
The shared memory that flows through every LangGraph node.
12 fields. All nodes read from and write to this dict.
NEVER import FastAPI here — agents/ is isolated from the web layer.
"""
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    # ── Conversation ──────────────────────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages]
    # Full conversation history. add_messages reducer appends — never overwrites.
    # AsyncPostgresSaver checkpoints this to chat_sessions.session_state after every node.

    # ── Student data ──────────────────────────────────────────────────────
    student_profile: dict
    # Loaded from DB at session start using JWT sub (user_uuid).
    # Contains: riasec_scores, subject_marks, capability_scores,
    #           stream, education_level, grade_system.
    # Never accepted from request body.

    active_constraints: dict
    # Extracted by ProfilerNode during conversation.
    # Contains: budget_per_semester, transport_willing, home_zone,
    #           stated_preferences, family_constraints, career_goal, student_notes.
    # May be overridden per-session via context_overrides in ChatRequest.

    # ── Graph control ─────────────────────────────────────────────────────
    profiling_complete: bool
    # True when all PROFILER_REQUIRED_FIELDS (budget, transport_willing, home_zone) are non-null.
    # For O/A Level students: stream confirmation also required before True.
    # SupervisorNode routing edge checks this before allowing get_recommendation to FilterNode.

    last_intent: str
    # Written by SupervisorNode on every turn.
    # Values: get_recommendation | profile_update | fee_query |
    #         market_query | follow_up | clarification | out_of_scope

    student_mode: str
    # "inter" | "matric_planning"
    # Set at session start from student_profile.education_level.

    education_level: str
    # Set at session start from student_profile.education_level.

    # ── Roadmap data ──────────────────────────────────────────────────────
    current_roadmap: list
    # Sorted list of scored degrees (dicts). Written by ScoringNode.
    # Each entry has 15 fields matching recommendations.roadmap_snapshot schema.

    previous_roadmap: list | None
    # Loaded at session start from most recent recommendations row.
    # None if no prior pipeline run exists.
    # Used by ExplanationNode to detect "What Changed" between runs.

    thought_trace: list
    # Reasoning steps appended by FilterNode and ScoringNode.
    # Trimmed to top-5-relevant before ExplanationNode prompt (Option B quality strategy).

    mismatch_notice: str | None
    # Set by ScoringNode when stated preference scores 20+ points below top match
    # AND preferred degree FutureValue < 6.
    # Passed to ExplanationNode prompt as Part 1 of the response structure.
    # Reset to None at the start of each new pipeline run.

    conflict_detected: bool
    # Always False in v1. Placeholder for MVP-3 (Parent Mediation) — permanently deferred.
