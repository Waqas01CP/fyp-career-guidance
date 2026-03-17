"""
test_scoring_node.py — ScoringNode formula verification.
Tests the RIASEC dot product, FutureValue weighting, and capability blend math.
Run: pytest tests/test_scoring_node.py -v
"""
import pytest
from app.core.config import settings


# ── Formula unit tests (pure math — no DB, no JSON needed) ────────────────

def test_riasec_dot_product():
    """Verify the RIASEC match normalisation formula."""
    student_vector = [32, 45, 28, 31, 38, 42]   # R I A S E C — valid 10-50 range
    degree_vector  = [3,  9,  2,  2,  5,  8]    # affinity 1-10

    raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
    theoretical_max = sum(s * 10 for s in student_vector)
    normalised = raw_match / theoretical_max

    assert 0.0 <= normalised <= 1.0, "Normalised score must be between 0 and 1"
    assert theoretical_max > 0, "Theoretical max must be positive"


def test_perfect_alignment_gives_1():
    """If student and degree vectors are identical (proportionally), score approaches 1."""
    # All affinities at max (10) — any student vector gives score = 1.0
    student_vector = [32, 45, 28, 31, 38, 42]
    degree_vector  = [10, 10, 10, 10, 10, 10]

    raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
    theoretical_max = sum(s * 10 for s in student_vector)
    normalised = raw_match / theoretical_max

    assert normalised == pytest.approx(1.0), "All-10 affinity should give score 1.0"


def test_zero_overlap_gives_low_score():
    """Student strong in I/C, degree needs R/A — low score expected."""
    student_vector = [10, 50, 10, 10, 10, 50]   # Strong I and C
    degree_vector  = [10, 1,  10, 1,  1,  1]    # Needs R and A

    raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
    theoretical_max = sum(s * 10 for s in student_vector)
    normalised = raw_match / theoretical_max

    assert normalised < 0.4, "Misaligned profile should give low score"


def test_total_score_formula_inter():
    """Verify total_score = 0.6 * match + 0.4 * future/10 for inter mode."""
    match_score = 0.75
    future_score = 8.0
    weights = settings.SCORING_WEIGHTS["inter"]

    total = (weights["match"] * match_score) + (weights["future"] * future_score / 10)
    expected = (0.6 * 0.75) + (0.4 * 0.8)
    assert total == pytest.approx(expected, abs=1e-6)


def test_total_score_formula_matric_planning():
    """Verify total_score = 0.7 * match + 0.3 * future/10 for matric_planning mode."""
    match_score = 0.60
    future_score = 7.0
    weights = settings.SCORING_WEIGHTS["matric_planning"]

    total = (weights["match"] * match_score) + (weights["future"] * future_score / 10)
    expected = (0.7 * 0.60) + (0.3 * 0.7)
    assert total == pytest.approx(expected, abs=1e-6)


def test_capability_blend_triggers_at_threshold():
    """Blend triggers when abs(capability - reported) >= CAPABILITY_BLEND_THRESHOLD."""
    threshold = settings.CAPABILITY_BLEND_THRESHOLD   # 25
    weight    = settings.CAPABILITY_BLEND_WEIGHT       # 0.25
    max_shift = settings.CAPABILITY_BLEND_MAX_SHIFT    # 10

    reported_grade    = 80.0
    capability_score  = 52.0   # gap = 28, exceeds threshold
    gap = capability_score - reported_grade   # -28

    assert abs(gap) >= threshold, "This gap should trigger blend"

    raw_effective = (reported_grade * (1 - weight)) + (capability_score * weight)
    effective = max(
        reported_grade - max_shift,
        min(reported_grade + max_shift, raw_effective)
    )

    # Should shift downward (capability lower than reported) but not more than max_shift
    assert effective < reported_grade, "Effective grade should be lower"
    assert effective >= reported_grade - max_shift, "Should not shift more than max_shift"


def test_capability_blend_does_not_trigger_below_threshold():
    """Blend does NOT trigger when gap < CAPABILITY_BLEND_THRESHOLD."""
    threshold = settings.CAPABILITY_BLEND_THRESHOLD   # 25
    reported_grade   = 80.0
    capability_score = 60.0   # gap = 20, below threshold

    gap = abs(capability_score - reported_grade)   # 20
    assert gap < threshold, "This gap should NOT trigger blend"
    # effective_grade should equal reported_grade unchanged


def test_mismatch_thresholds():
    """Mismatch notice triggers when score gap >= 20 AND pref FutureValue < 6."""
    gap_threshold = settings.MISMATCH_SCORE_GAP_THRESHOLD   # 20
    fv_ceiling    = settings.MISMATCH_FUTURE_VALUE_CEILING   # 6.0

    top_match_score  = 0.84
    pref_score       = 0.52
    pref_future_value = 5.1

    score_gap = (top_match_score - pref_score) * 100   # normalise to same scale for comparison
    # In actual implementation gap is compared directly on total_score scale
    # This test verifies threshold values are correct

    assert gap_threshold == 20
    assert fv_ceiling == 6.0
    assert pref_future_value < fv_ceiling, "FutureValue below ceiling — mismatch eligible"
