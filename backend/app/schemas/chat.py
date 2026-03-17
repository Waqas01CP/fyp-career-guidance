"""Chat schemas — request/response shapes for the SSE streaming endpoint."""
from uuid import UUID
from pydantic import BaseModel


class ChatRequest(BaseModel):
    session_id: UUID
    user_input: str
    context_overrides: dict = {}
    # Optional explicit constraint overrides e.g. {"budget": 80000}.
    # Merged into active_constraints before the graph runs.


class SSEEvent(BaseModel):
    event: str   # 'status' | 'chunk' | 'rich_ui'
    data: dict
