"""chat_sessions table — LangGraph AgentState checkpointed here."""
import uuid
from sqlalchemy import Column, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_state   = Column(JSONB, nullable=False, default=dict)  # AsyncPostgresSaver writes this
    session_summary = Column(Text)                                  # NULL Sprint 1-3, populated Sprint 4
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user     = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
