"""
chat.py — SSE streaming chat endpoint.
POST /api/v1/chat/stream
Rate limited: 10 requests/minute per IP via slowapi.
"""
import asyncio
import json
import logging
import uuid as uuid_mod
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.dependencies import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.limiter import limiter
from app.models.profile import StudentProfile
from app.models.recommendation import Recommendation
from app.models.user import User
from app.schemas.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

# ── lag_model loaded once at module level (same pattern as scoring_node.py) ──
_DATA_DIR = Path(__file__).resolve().parents[3] / "data"
_LAG_MODEL: list[dict] = json.loads(
    (_DATA_DIR / "lag_model.json").read_text(encoding="utf-8")
)
_LAG_MODEL_MAP: dict[str, dict] = {e["field_id"]: e for e in _LAG_MODEL}

_EDUCATION_LABELS = {
    "matric": "Matric",
    "inter_part1": "Inter Part 1",
    "inter_part2": "Inter Part 2",
    "completed_inter": "Completed Inter",
    "o_level": "O Level",
    "a_level": "A Level",
}

# Node names registered in core_graph.py → SSE status state values
NODE_STATUS_MAP = {
    "profiler":         "profiling",
    "filter_node":      "filtering_degrees",
    "scoring_node":     "scoring_degrees",
    "explanation_node": "generating_explanation",
}


def _sse(event: str, data: dict) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _build_university_card(degree: dict, rank: int, final_state: dict) -> dict:
    """Build a 20-field university_card payload from a roadmap entry + lag_model."""
    field_id = degree.get("field_id", "")
    lag_entry = _LAG_MODEL_MAP.get(field_id, {})
    employment = lag_entry.get("employment_data", {})
    return {
        "rank":                       rank,
        "degree_id":                  degree.get("degree_id"),
        "degree_name":                degree.get("degree_name"),
        "university_id":              degree.get("university_id"),
        "university_name":            degree.get("university_name"),
        "field_id":                   field_id,
        "total_score":                degree.get("total_score"),
        "match_score_normalised":     degree.get("match_score_normalised"),
        "future_score":               degree.get("future_score"),
        "merit_tier":                 degree.get("merit_tier"),
        "eligibility_tier":           degree.get("eligibility_tier"),
        "eligibility_note":           degree.get("eligibility_note"),
        "fee_per_semester":           degree.get("fee_per_semester"),
        "aggregate_used":             degree.get("aggregate_used"),
        "soft_flags":                 degree.get("soft_flags", []),
        "lifecycle_status":           lag_entry.get("lifecycle_status"),
        "risk_factor":                lag_entry.get("risk_factor"),
        "rozee_live_count":           employment.get("rozee_live_count"),
        "rozee_last_updated":         employment.get("rozee_last_updated"),
        "policy_pending_verification": False,
    }


def _build_roadmap_timeline(
    top_degree: dict,
    student_profile: dict,
    active_constraints: dict,
) -> dict:
    """Build a 4-step roadmap_timeline payload for the top-ranked degree."""
    field_id = top_degree.get("field_id", "")
    lag_entry = _LAG_MODEL_MAP.get(field_id, {})
    career_paths = lag_entry.get("career_paths", {})
    pak_now = lag_entry.get("pakistan_now", {})
    pak_future = lag_entry.get("pakistan_future", {})
    employment = lag_entry.get("employment_data", {})

    # Step 0 — current status
    edu_label = _EDUCATION_LABELS.get(
        student_profile.get("education_level", ""), "Current Year"
    )
    stream = student_profile.get("stream") or ""
    aggregate = top_degree.get("aggregate_used")
    step0_parts = [edu_label]
    if stream:
        step0_parts.append(stream)
    if aggregate is not None:
        step0_parts.append(f"{aggregate:.1f}% aggregate")

    # Step 2 — industry entry title from career_paths
    entry_title = career_paths.get("entry_level_title") or "Industry professional role"

    # Step 3 — 2030 outlook: growth + job count
    job_count = pak_now.get("job_postings_monthly") or employment.get("rozee_live_count")
    growth_pct = pak_future.get("projected_4yr_growth")
    future_val = top_degree.get("future_score", 0)
    if growth_pct is not None:
        growth_str = f"{growth_pct * 100:.0f}% demand growth projected"
    else:
        growth_str = f"Strong growth outlook (score: {future_val:.1f}/10)"
    if job_count:
        step3_detail = f"{growth_str}. {job_count:,} active roles on Rozee today."
    else:
        step3_detail = growth_str + "."

    return {
        "steps": [
            {
                "label":  "Current Status",
                "detail": ", ".join(step0_parts),
                "status": "complete",
            },
            {
                "label":  "Recommended Degree",
                "detail": f"{top_degree.get('degree_name')} — {top_degree.get('university_name')}",
                "status": "next",
            },
            {
                "label":  "Industry Entry",
                "detail": entry_title,
                "status": "future",
            },
            {
                "label":  "2030 Outlook",
                "detail": step3_detail,
                "status": "future",
            },
        ],
        "field_id":  field_id,
        "degree_id": top_degree.get("degree_id"),
    }


async def _write_recommendation(
    db: AsyncSession,
    user_id,
    current_roadmap: list,
    previous_roadmap: list,
    last_intent: str,
) -> None:
    """Write a new recommendations row after a successful pipeline run."""
    trigger = (
        "initial"        if not previous_roadmap
        else "profile_update" if last_intent == "profile_update"
        else "manual_rerun"
    )
    rec = Recommendation(
        id=uuid_mod.uuid4(),
        user_id=user_id,
        roadmap_snapshot=[
            {
                "degree_id":   d.get("degree_id"),
                "total_score": d.get("total_score"),
                "merit_tier":  d.get("merit_tier"),
                "soft_flags":  d.get("soft_flags", []),
            }
            for d in current_roadmap
        ],
        trigger=trigger,
    )
    db.add(rec)
    await db.commit()


@router.post("/chat/stream")
@limiter.limit(settings.CHAT_RATE_LIMIT)
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    SSE streaming endpoint. Runs the LangGraph agent pipeline.
    Emits: status events (pipeline progress), chunk events (text), rich_ui events (cards).
    Terminal event: {"state": "done"}.
    """
    # ── Pre-graph setup ───────────────────────────────────────────────────────

    # Step 2: load student_profile
    result = await db.execute(
        select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail={"error_code": "NOT_FOUND", "message": "Student profile not found."},
        )

    # Step 3: LangGraph thread config — thread_id = session_id
    config = {"configurable": {"thread_id": str(payload.session_id)}}

    # Step 4: load previous_roadmap from most recent recommendations row
    rec_result = await db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(desc(Recommendation.run_timestamp))
        .limit(1)
    )
    latest_rec = rec_result.scalar_one_or_none()
    previous_roadmap: list = latest_rec.roadmap_snapshot if latest_rec else []

    # Build student_profile dict for AgentState
    student_profile_dict = {
        "education_level":    profile.education_level,
        "student_mode":       profile.student_mode,
        "grade_system":       profile.grade_system,
        "stream":             profile.stream,
        "riasec_scores":      profile.riasec_scores or {},
        "subject_marks":      profile.subject_marks or {},
        "capability_scores":  profile.capability_scores or {},
        "budget_per_semester": profile.budget_per_semester,
        "transport_willing":  profile.transport_willing,
        "home_zone":          profile.home_zone,
        "stated_preferences": profile.stated_preferences or [],
        "family_constraints": profile.family_constraints,
        "career_goal":        profile.career_goal,
        "student_notes":      profile.student_notes,
    }

    # Steps 6+7: initial_state — merge new message + cleared run-specific fields
    initial_state: dict = {
        "messages":         [HumanMessage(content=payload.user_input)],
        "student_profile":  student_profile_dict,
        "student_mode":     profile.student_mode or "inter",
        "education_level":  profile.education_level or "",
        "conflict_detected": False,
        "previous_roadmap": previous_roadmap,
        "current_roadmap":  [],
        "thought_trace":    [],
        "mismatch_notice":  None,
    }
    # Step 5: context_overrides merged into active_constraints if present
    if payload.context_overrides:
        existing = (initial_state.get("active_constraints") or {})
        initial_state["active_constraints"] = {**existing, **payload.context_overrides}

    # ── Streaming generator ───────────────────────────────────────────────────

    async def real_stream():
        keepalive_queue: asyncio.Queue = asyncio.Queue()
        stop_keepalive = asyncio.Event()

        async def _keepalive_sender():
            while not stop_keepalive.is_set():
                try:
                    await asyncio.wait_for(
                        stop_keepalive.wait(),
                        timeout=settings.STREAM_KEEPALIVE_INTERVAL,
                    )
                except asyncio.TimeoutError:
                    await keepalive_queue.put(": keepalive\n\n")

        keepalive_task = asyncio.create_task(_keepalive_sender())

        try:
            # Status events — one per node start (SupervisorNode and AnswerNode omitted)
            async for event in request.app.state.graph.astream_events(
                initial_state, config=config, version="v2"
            ):
                # Drain keepalives accumulated while graph was blocked on LLM
                while not keepalive_queue.empty():
                    yield await keepalive_queue.get()

                kind = event["event"]
                name = event.get("name", "")
                if kind == "on_chain_start" and name in NODE_STATUS_MAP:
                    yield _sse("status", {"state": NODE_STATUS_MAP[name]})

            # Drain any remaining keepalives after the graph loop completes
            while not keepalive_queue.empty():
                yield await keepalive_queue.get()

            # Get complete final state after all nodes have run
            checkpoint = await request.app.state.graph.aget_state(config)
            final_state: dict = checkpoint.values if checkpoint else {}

            # Chunk stream — last AIMessage content, word by word
            messages = final_state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                content = getattr(last_msg, "content", "")
                # Gemini returns content as a list of parts in some responses
                if isinstance(content, list):
                    content = " ".join(
                        p.get("text", "") if isinstance(p, dict) else str(p)
                        for p in content
                    )
                if content:
                    words = content.split(" ")
                    for i, word in enumerate(words):
                        chunk = word if i == len(words) - 1 else word + " "
                        yield _sse("chunk", {"text": chunk})

            # Rich_ui events — only for get_recommendation pipeline runs
            current_roadmap = final_state.get("current_roadmap", [])
            last_intent = final_state.get("last_intent", "")

            should_emit_cards = (
                current_roadmap and
                last_intent in ("get_recommendation", "follow_up")
            )
            if should_emit_cards:
                for i, degree in enumerate(current_roadmap[:5]):
                    card = _build_university_card(degree, i + 1, final_state)
                    yield _sse("rich_ui", {"type": "university_card", "payload": card})

                if last_intent == "get_recommendation":
                    timeline = _build_roadmap_timeline(
                        current_roadmap[0],
                        final_state.get("student_profile", {}),
                        final_state.get("active_constraints", {}),
                    )
                    yield _sse("rich_ui", {"type": "roadmap_timeline", "payload": timeline})
                    # Write recommendations row to DB — only on first recommendation run
                    await _write_recommendation(
                        db, current_user.id, current_roadmap, previous_roadmap, last_intent
                    )

        except Exception as e:
            logger.error("chat_stream error: %s", e, exc_info=True)
        finally:
            stop_keepalive.set()
            keepalive_task.cancel()
            # Do NOT await — unsafe during CancelledError propagation
            # Task is garbage-collected after cancellation, no leak
            yield _sse("status", {"state": "done"})

    return StreamingResponse(real_stream(), media_type="text/event-stream")
