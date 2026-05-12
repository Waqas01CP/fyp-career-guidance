"""student_profiles table — full student record."""
import uuid
from sqlalchemy import (
    Column, String, Integer, SmallInteger, Boolean, Float,
    DateTime, Text, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (UniqueConstraint("user_id"),)

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Onboarding state machine
    onboarding_stage    = Column(String, nullable=False, default="not_started")
    # Values: 'not_started' | 'riasec_complete' | 'grades_complete' | 'assessment_complete' | 'complete'

    education_level     = Column(String)   # matric|inter_part1|inter_part2|completed_inter|o_level|a_level
    student_mode        = Column(String)   # 'inter' | 'matric_planning'
    grade_system        = Column(String)   # 'percentage' | 'olevel_alevel'
    stream              = Column(String)   # NULL for O/A Level until ProfilerNode confirms
    board               = Column(String)   # Karachi Board | Federal Board | AKU | Cambridge | Other

    # Assessment scores
    riasec_scores       = Column(JSONB, nullable=False, default=dict)   # {R,I,A,S,E,C} values 10-50
    subject_marks       = Column(JSONB, nullable=False, default=dict)   # {subject: pct} 0-100
    capability_scores   = Column(JSONB, nullable=False, default=dict)   # {subject: float} 0-100

    # Profiler fields — required
    budget_per_semester = Column(Integer)
    transport_willing   = Column(Boolean)
    home_zone           = Column(SmallInteger)  # 1-5 Karachi zone

    # Profiler fields — optional
    stated_preferences  = Column(JSONB, nullable=False, default=list)
    family_constraints  = Column(Text)
    career_goal         = Column(Text)
    student_notes       = Column(Text)

    # Tier-aware assessment scores (Phase 0b migration)
    # All key names defined in SCHEMA_CONTRACT.md
    aptitude_scores        = Column(JSONB, nullable=False, default=dict)
    # Keys: numerical, spatial, verbal, logical + belief sub-scores
    # Written by POST /api/v1/profile/aptitude

    caas_scores            = Column(JSONB, nullable=False, default=dict)
    # Keys: concern, control, curiosity, confidence, cooperation (CAAS-5-SF)
    # Written by POST /api/v1/profile/caas

    vna_scores             = Column(JSONB, nullable=False, default=dict)
    # Keys: social_status, independence, achievement
    # Written by POST /api/v1/profile/vna

    family_context         = Column(JSONB, nullable=False, default=dict)
    # Keys: family_career_field, family_career_expectation, social_pressure_field
    # Written by POST /api/v1/profile/preferences (Step 4 screen)

    prestige_preference    = Column(Float, nullable=False, default=5.0)
    # Derived by ProfilerNode. Read by ScoringNode for 3D match formula.

    misc_assessment_scores = Column(JSONB, nullable=False, default=dict)
    # Keys: conscientiousness, neuroticism, information_gap, external_conflict
    # Written by POST /api/v1/profile/misc-assessment

    # kcis_scores deferred to Phase 1C migration — do not add here

    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(),
                                 onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")
