"""profile_history table — immutable audit trail of profile changes."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class ProfileHistory(Base):
    __tablename__ = "profile_history"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    snapshot     = Column(JSONB, nullable=False)
    # Full copy of student_profiles row BEFORE the change (pre-change state).
    triggered_by = Column(String, nullable=False)
    # 'quiz_update' | 'grade_update' | 'assessment_update' | 'chat_update'
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="history")
