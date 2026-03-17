"""recommendations table — roadmap snapshot per pipeline run."""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    run_timestamp    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    roadmap_snapshot = Column(JSONB, nullable=False, default=list)
    # Array of 15-field entries per ranked degree. Written by core_graph.py post-ExplanationNode.
    trigger          = Column(String, nullable=False, default="initial")
    # 'initial' | 'profile_update' | 'manual_rerun'

    user = relationship("User", back_populates="recommendations")
