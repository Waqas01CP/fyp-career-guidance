"""messages table — per-message log with agent thought trace."""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Message(Base):
    __tablename__ = "messages"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id          = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role                = Column(String, nullable=False)   # 'user' | 'assistant'
    content             = Column(Text, nullable=False)
    agent_thought_trace = Column(JSONB, nullable=False, default=list)
    # Populated only on assistant messages from full pipeline runs (get_recommendation intent).
    # Empty list for all other messages.
    timestamp           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")
