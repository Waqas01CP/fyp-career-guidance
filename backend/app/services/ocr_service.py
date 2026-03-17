"""
ocr_service.py — Gemini Vision marksheet extraction.
Called by POST /profile/marksheet in profile.py.
Does NOT write to the database — returns extracted marks + confidence to the endpoint.
Frontend must confirm via POST /profile/grades before anything is stored.
"""
from app.schemas.profile import MarksheetUploadResponse


async def extract_marks_from_image(image_bytes: bytes) -> MarksheetUploadResponse:
    """
    Send marksheet image to Gemini Vision and extract subject marks.

    Sprint 1: returns a mock response.
    Sprint 2: replace with real Gemini Vision API call.

    Prompt to use (Sprint 2):
        Extract all subject names and their marks/percentages from this academic marksheet.
        Return ONLY valid JSON in this exact format:
        {"mathematics": 85, "physics": 72, "chemistry": 68, "english": 79, "biology": 65}
        Use lowercase subject names. Values are integer percentages 0-100.
        If you cannot read a subject clearly, omit it.
    """
    # ── SPRINT 1 MOCK ──────────────────────────────────────────────────────
    # Replace this block with real Gemini Vision call in Sprint 2
    mock_extracted = {
        "mathematics": 0,
        "physics": 0,
        "chemistry": 0,
        "english": 0,
        "biology": 0,
    }
    mock_confidence = 0.0
    return MarksheetUploadResponse(
        status="failed",
        extracted_marks=mock_extracted,
        confidence_score=mock_confidence,
        requires_manual_verification=True,  # always True when confidence < 0.80
    )
    # ── END MOCK ───────────────────────────────────────────────────────────
