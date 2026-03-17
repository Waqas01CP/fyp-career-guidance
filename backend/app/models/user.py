"""users table — authentication only."""
import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, nullable=False, default="student")  # 'student' | 'admin'
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile         = relationship("StudentProfile", back_populates="user", uselist=False)
    sessions        = relationship("ChatSession", back_populates="user")
    history         = relationship("ProfileHistory", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
