"""
chat.py — SSE streaming chat endpoint.
POST /api/v1/chat/stream
Rate limited: 10 requests/minute per IP via slowapi.
"""
import json
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.core.limiter import limiter
from app.core.config import settings
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.api.v1.dependencies import get_current_user
router = APIRouter(tags=["chat"])


def _sse(event: str, data: dict) -> str:
    """Format a single SSE event as a string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat/stream")
@limiter.limit(settings.CHAT_RATE_LIMIT)
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    """
    SSE streaming endpoint. Runs the LangGraph agent pipeline.
    Emits: status events (pipeline progress), chunk events (text), rich_ui events (cards).
    Terminal event: {"state": "done"}.

    Sprint 1: returns a hardcoded mock stream so frontend can build against it immediately.
    Sprint 3: replace mock_stream with real_stream (call build_graph and stream nodes).
    """
    user_id = str(current_user.id)

    async def mock_stream():
        """
        SPRINT 1 MOCK — hardcoded SSE stream for frontend development.
        Replace this with real LangGraph invocation in Sprint 3.
        """
        yield _sse("status", {"state": "profiling"})
        yield _sse("chunk", {"text": "Hello! I'm analysing your profile. "})
        yield _sse("chunk", {"text": "This is a mock response from Sprint 1. "})
        yield _sse("chunk", {"text": "The full recommendation pipeline will be live in Sprint 3."})
        yield _sse("status", {"state": "done"})

    return StreamingResponse(mock_stream(), media_type="text/event-stream")
