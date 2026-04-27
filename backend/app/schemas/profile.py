"""Profile schemas — request/response shapes for all profile endpoints."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class QuizSubmission(BaseModel):
    responses: dict[str, int]
    # Keys: R, I, A, S, E, C
    # Values: integers 10-50 (frontend sums 10 Likert responses per dimension)


class GradesSubmission(BaseModel):
    education_level: str
    # One of: matric | inter_part1 | inter_part2 | completed_inter | o_level | a_level
    stream: str | None = None
    # Required for Pakistani board students. None for O/A Level.
    subject_marks: dict[str, float | str]
    # Percentages for Pakistani board (e.g. 85.0) or O/A Level grade letters (e.g. "A*", "A", "B").
    # IBCC conversion applied server-side when education_level is o_level or a_level.
    board: str | None = None
    # Karachi Board | Federal Board | AKU | Cambridge | Other. None for O/A Level.


class AssessmentSubmission(BaseModel):
    responses: dict[str, list[int]]
    # {"mathematics": [1, 0, 1, ...], ...}
    # Per-subject list of 0/1 correct flags matching question order (12 per subject)


class MarksheetUploadResponse(BaseModel):
    status: str                          # "success" | "partial" | "failed"
    extracted_marks: dict[str, float]    # {"mathematics": 80.0, ...}
    confidence_score: float              # 0.0 - 1.0
    requires_manual_verification: bool
    # Always True when confidence_score < 0.80 — no exceptions


class PreferencesSubmission(BaseModel):
    budget_per_semester: Optional[int] = None      # PKR per semester
    transport_willing: Optional[bool] = None
    home_zone: Optional[int] = None                # Karachi zone 1-5
    career_goal: Optional[str] = None
    stated_preferences: Optional[List[str]] = None


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    onboarding_stage: str
    education_level: str | None
    student_mode: str | None
    grade_system: str | None
    stream: str | None
    board: str | None
    riasec_scores: dict        # {R,I,A,S,E,C} integers 10-50, empty {} if not yet taken
    subject_marks: dict        # {subject: pct}, empty {} if not yet entered
    capability_scores: dict    # {subject: float}, empty {} if not yet taken
    budget_per_semester: int | None
    transport_willing: bool | None
    home_zone: int | None
    stated_preferences: list
    family_constraints: str | None
    career_goal: str | None
    student_notes: str | None
    updated_at: datetime
    session_id: Optional[UUID] = None
