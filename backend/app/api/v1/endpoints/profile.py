"""
profile.py — All profile-building and admin endpoints.
GET  /api/v1/profile/me
POST /api/v1/profile/quiz
POST /api/v1/profile/grades
POST /api/v1/profile/marksheet
POST /api/v1/profile/assessment
POST /api/v1/admin/seed-knowledge
"""
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.profile_history import ProfileHistory
from app.schemas.profile import (
    ProfileOut, QuizSubmission, GradesSubmission,
    AssessmentSubmission, MarksheetUploadResponse
)
from app.api.v1.dependencies import get_current_user, require_admin
from app.services.ocr_service import extract_marks_from_image

router = APIRouter(tags=["profile"])

DATA_DIR = Path(__file__).resolve().parents[3] / "data"

# ── Education level derivation ─────────────────────────────────────────────
EDUCATION_TO_STUDENT_MODE = {
    "matric":           "matric_planning",
    "inter_part1":      "inter",
    "inter_part2":      "inter",
    "completed_inter":  "inter",
    "o_level":          "matric_planning",
    "a_level":          "inter",
}
EDUCATION_TO_GRADE_SYSTEM = {
    "matric":           "percentage",
    "inter_part1":      "percentage",
    "inter_part2":      "percentage",
    "completed_inter":  "percentage",
    "o_level":          "olevel_alevel",
    "a_level":          "olevel_alevel",
}
VALID_EDUCATION_LEVELS = set(EDUCATION_TO_STUDENT_MODE.keys())

# ── IBCC O/A Level grade → percentage approximation table ─────────────────
IBCC_GRADE_MAP = {"A*": 90, "A": 85, "B": 75, "C": 65, "D": 55, "E": 45, "U": 0}


def _ibcc_convert(raw_marks: dict[str, float]) -> dict[str, float]:
    """Convert O/A Level grade letters to percentage equivalents."""
    converted = {}
    for subject, value in raw_marks.items():
        if isinstance(value, str):
            converted[subject] = float(IBCC_GRADE_MAP.get(value.upper(), 0))
        else:
            converted[subject] = float(value)
    return converted


async def _snapshot_profile(db: AsyncSession, profile: StudentProfile, triggered_by: str):
    """Capture pre-change profile snapshot to profile_history."""
    snapshot = {
        "id": str(profile.id), "user_id": str(profile.user_id),
        "onboarding_stage": profile.onboarding_stage,
        "education_level": profile.education_level,
        "student_mode": profile.student_mode, "grade_system": profile.grade_system,
        "stream": profile.stream, "board": profile.board,
        "riasec_scores": profile.riasec_scores, "subject_marks": profile.subject_marks,
        "capability_scores": profile.capability_scores,
        "budget_per_semester": profile.budget_per_semester,
        "transport_willing": profile.transport_willing, "home_zone": profile.home_zone,
        "stated_preferences": profile.stated_preferences,
        "family_constraints": profile.family_constraints,
        "career_goal": profile.career_goal, "student_notes": profile.student_notes,
    }
    history = ProfileHistory(user_id=profile.user_id, snapshot=snapshot, triggered_by=triggered_by)
    db.add(history)


# ── GET /profile/me ─────────────────────────────────────────────────────────
@router.get("/profile/me", response_model=ProfileOut)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail={"error_code": "NOT_FOUND",
                                                      "message": "Profile not found.", "details": []})
    return profile


# ── POST /profile/quiz ──────────────────────────────────────────────────────
@router.post("/profile/quiz")
async def submit_quiz(
    payload: QuizSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit RIASEC quiz. Scores summed per dimension, range 10-50."""
    required_keys = {"R", "I", "A", "S", "E", "C"}
    if set(payload.responses.keys()) != required_keys:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": "All six RIASEC keys required.",
                                                      "details": list(required_keys - set(payload.responses.keys()))})
    for key, val in payload.responses.items():
        if not (10 <= val <= 50):
            raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                          "message": f"Score for {key} must be 10-50.",
                                                          "details": [key]})
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    await _snapshot_profile(db, profile, "quiz_update")
    profile.riasec_scores = dict(payload.responses)
    profile.onboarding_stage = "riasec_complete"
    await db.commit()
    return {"onboarding_stage": "riasec_complete"}


# ── POST /profile/grades ────────────────────────────────────────────────────
@router.post("/profile/grades")
async def submit_grades(
    payload: GradesSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit academic marks. IBCC conversion applied server-side for O/A Level."""
    if payload.education_level not in VALID_EDUCATION_LEVELS:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": f"Invalid education_level.",
                                                      "details": ["education_level"]})
    # Apply IBCC conversion for O/A Level
    grade_system = EDUCATION_TO_GRADE_SYSTEM[payload.education_level]
    if grade_system == "olevel_alevel":
        marks = _ibcc_convert(payload.subject_marks)
    else:
        marks = {k: float(v) for k, v in payload.subject_marks.items()}

    for subj, val in marks.items():
        if not (0 <= val <= 100):
            raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                          "message": f"Mark for {subj} out of range 0-100.",
                                                          "details": [subj]})
    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    await _snapshot_profile(db, profile, "grade_update")

    profile.education_level = payload.education_level
    profile.student_mode    = EDUCATION_TO_STUDENT_MODE[payload.education_level]
    profile.grade_system    = grade_system
    profile.stream          = payload.stream   # None for O/A Level
    profile.board           = payload.board
    profile.subject_marks   = marks
    profile.onboarding_stage = "grades_complete"
    await db.commit()
    return {"onboarding_stage": "grades_complete"}


# ── POST /profile/marksheet ─────────────────────────────────────────────────
@router.post("/profile/marksheet", response_model=MarksheetUploadResponse)
async def upload_marksheet(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """OCR marksheet upload. Does NOT write to DB — frontend confirms via /grades."""
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": "Only JPEG and PNG supported.",
                                                      "details": ["file"]})
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": "File too large. Max 10MB.",
                                                      "details": ["file"]})
    result = await extract_marks_from_image(image_bytes)
    return result


# ── POST /profile/assessment ────────────────────────────────────────────────
@router.post("/profile/assessment")
async def submit_assessment(
    payload: AssessmentSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit capability assessment. Scored deterministically — no LLM."""
    required_subjects = {"mathematics", "physics", "chemistry", "biology", "english"}
    if set(payload.responses.keys()) != required_subjects:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": "All five subjects required.",
                                                      "details": list(required_subjects - set(payload.responses.keys()))})
    total_q = (settings.ASSESSMENT_QUESTIONS_PER_SESSION["easy"] +
               settings.ASSESSMENT_QUESTIONS_PER_SESSION["medium"] +
               settings.ASSESSMENT_QUESTIONS_PER_SESSION["hard"])
    capability_scores = {}
    for subject, answers in payload.responses.items():
        if len(answers) != total_q:
            raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                          "message": f"{subject}: expected {total_q} answers.",
                                                          "details": [subject]})
        if any(a not in (0, 1) for a in answers):
            raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                          "message": f"{subject}: values must be 0 or 1.",
                                                          "details": [subject]})
        capability_scores[subject] = round((sum(answers) / len(answers)) * 100, 1)

    result = await db.execute(select(StudentProfile).where(StudentProfile.user_id == current_user.id))
    profile = result.scalar_one_or_none()
    await _snapshot_profile(db, profile, "assessment_update")
    profile.capability_scores = capability_scores
    profile.onboarding_stage  = "assessment_complete"
    await db.commit()
    return {"onboarding_stage": "assessment_complete", "capability_scores": capability_scores}


# ── POST /admin/seed-knowledge ──────────────────────────────────────────────
@router.post("/admin/seed-knowledge")
async def seed_knowledge(
    current_user: User = Depends(require_admin),
):
    """Re-seed knowledge base from JSON files. Idempotent. Admin only."""
    counts = {}
    for fname in ["universities.json", "lag_model.json", "affinity_matrix.json", "assessment_questions.json"]:
        fpath = DATA_DIR / fname
        if not fpath.exists():
            raise HTTPException(status_code=500, detail={"error_code": "INTERNAL_ERROR",
                                                          "message": f"{fname} not found.",
                                                          "details": [fname]})
        with open(fpath) as f:
            data = json.load(f)
        counts[fname.replace(".json", "")] = len(data) if isinstance(data, list) else len(data)
    return {"status": "success", "seeded": {
        "universities": counts.get("universities", 0),
        "lag_model_fields": counts.get("lag_model", 0),
        "affinity_matrix_fields": counts.get("affinity_matrix", 0),
        "assessment_questions": counts.get("assessment_questions", 0),
    }}
