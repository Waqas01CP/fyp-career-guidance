"""
test_scoring_node.py — ScoringNode formula verification.
Tests the RIASEC dot product, FutureValue weighting, and capability blend math.
Run: pytest tests/test_scoring_node.py -v
"""
import json
import pytest
from pathlib import Path

import app.agents.nodes.scoring_node as scoring_node_module
from app.agents.nodes.scoring_node import scoring_node, build_mismatch_notice
from app.core.config import settings


# ── Fixture data — all 32 NED field_ids ────────────────────────────────────────
# Values are realistic estimates based on Pakistan market outlook and Holland (1997).
# These replace the empty lag_model.json / affinity_matrix.json during tests only.
# Real files are NOT modified. See logs session for full fixture documentation.

_FIELD_IDS = [
    "architecture", "artificial_intelligence", "automotive_engineering",
    "biomedical_engineering", "business_bba", "chemical_engineering",
    "chemistry_biochemistry", "civil_engineering", "computer_science",
    "construction_engineering", "cybersecurity", "data_science", "digital_media",
    "economics", "electrical_engineering", "electronics_engineering",
    "english_linguistics", "finance_accounting", "food_engineering",
    "industrial_manufacturing_engineering", "materials_engineering",
    "mechanical_engineering", "metallurgical_engineering", "petroleum_engineering",
    "physics", "polymer_petrochemical_engineering", "social_work",
    "software_engineering", "telecommunications_engineering",
    "textile_engineering", "textile_sciences", "urban_infrastructure_engineering",
]

# Per-field RIASEC affinities (1-10 scale, Holland 1997). Never 0.
_RIASEC_AFFINITIES = {
    "architecture":                         {"R": 6, "I": 5, "A": 9, "S": 3, "E": 4, "C": 6},
    "artificial_intelligence":              {"R": 3, "I": 9, "A": 5, "S": 2, "E": 3, "C": 7},
    "automotive_engineering":               {"R": 9, "I": 6, "A": 2, "S": 2, "E": 3, "C": 5},
    "biomedical_engineering":               {"R": 6, "I": 8, "A": 3, "S": 5, "E": 3, "C": 5},
    "business_bba":                         {"R": 2, "I": 5, "A": 3, "S": 5, "E": 9, "C": 7},
    "chemical_engineering":                 {"R": 7, "I": 8, "A": 2, "S": 2, "E": 3, "C": 6},
    "chemistry_biochemistry":               {"R": 4, "I": 9, "A": 3, "S": 3, "E": 2, "C": 7},
    "civil_engineering":                    {"R": 9, "I": 6, "A": 2, "S": 3, "E": 3, "C": 7},
    "computer_science":                     {"R": 4, "I": 9, "A": 3, "S": 2, "E": 3, "C": 8},
    "construction_engineering":             {"R": 8, "I": 5, "A": 2, "S": 3, "E": 4, "C": 7},
    "cybersecurity":                        {"R": 5, "I": 9, "A": 2, "S": 4, "E": 5, "C": 8},
    "data_science":                         {"R": 2, "I": 9, "A": 3, "S": 2, "E": 3, "C": 8},
    "digital_media":                        {"R": 3, "I": 5, "A": 9, "S": 4, "E": 6, "C": 3},
    "economics":                            {"R": 2, "I": 8, "A": 3, "S": 4, "E": 6, "C": 7},
    "electrical_engineering":               {"R": 8, "I": 8, "A": 2, "S": 2, "E": 3, "C": 6},
    "electronics_engineering":              {"R": 8, "I": 7, "A": 2, "S": 2, "E": 3, "C": 6},
    "english_linguistics":                  {"R": 1, "I": 6, "A": 8, "S": 6, "E": 4, "C": 4},
    "finance_accounting":                   {"R": 2, "I": 7, "A": 2, "S": 3, "E": 6, "C": 9},
    "food_engineering":                     {"R": 6, "I": 6, "A": 3, "S": 4, "E": 3, "C": 6},
    "industrial_manufacturing_engineering": {"R": 8, "I": 5, "A": 2, "S": 2, "E": 4, "C": 7},
    "materials_engineering":                {"R": 7, "I": 7, "A": 2, "S": 2, "E": 2, "C": 6},
    "mechanical_engineering":               {"R": 9, "I": 7, "A": 2, "S": 2, "E": 3, "C": 5},
    "metallurgical_engineering":            {"R": 7, "I": 7, "A": 1, "S": 2, "E": 2, "C": 6},
    "petroleum_engineering":                {"R": 7, "I": 7, "A": 2, "S": 2, "E": 4, "C": 5},
    "physics":                              {"R": 3, "I": 9, "A": 4, "S": 2, "E": 2, "C": 7},
    "polymer_petrochemical_engineering":    {"R": 6, "I": 7, "A": 2, "S": 2, "E": 3, "C": 6},
    "social_work":                          {"R": 2, "I": 4, "A": 4, "S": 10, "E": 5, "C": 3},
    "software_engineering":                 {"R": 4, "I": 8, "A": 4, "S": 2, "E": 3, "C": 7},
    "telecommunications_engineering":       {"R": 7, "I": 8, "A": 2, "S": 2, "E": 3, "C": 6},
    "textile_engineering":                  {"R": 6, "I": 5, "A": 4, "S": 2, "E": 3, "C": 6},
    "textile_sciences":                     {"R": 5, "I": 4, "A": 6, "S": 3, "E": 3, "C": 6},
    "urban_infrastructure_engineering":     {"R": 7, "I": 5, "A": 3, "S": 4, "E": 4, "C": 7},
}

# Realistic future_value estimates (0-10) based on Pakistan market outlook.
# Guidance values from task prompt used as anchors.
_FUTURE_VALUES = {
    "architecture":                         4.5,
    "artificial_intelligence":              9.2,
    "automotive_engineering":               4.0,
    "biomedical_engineering":               6.5,
    "business_bba":                         5.5,
    "chemical_engineering":                 5.5,
    "chemistry_biochemistry":               4.0,
    "civil_engineering":                    4.5,
    "computer_science":                     8.5,
    "construction_engineering":             3.8,
    "cybersecurity":                        8.0,
    "data_science":                         7.8,
    "digital_media":                        6.5,
    "economics":                            5.0,
    "electrical_engineering":               7.0,
    "electronics_engineering":              6.0,
    "english_linguistics":                  3.5,
    "finance_accounting":                   5.5,
    "food_engineering":                     5.0,
    "industrial_manufacturing_engineering": 4.0,
    "materials_engineering":                4.0,
    "mechanical_engineering":               5.0,
    "metallurgical_engineering":            3.5,
    "petroleum_engineering":                5.0,
    "physics":                              3.5,
    "polymer_petrochemical_engineering":    4.5,
    "social_work":                          3.0,
    "software_engineering":                 8.3,
    "telecommunications_engineering":       7.0,
    "textile_engineering":                  3.0,
    "textile_sciences":                     3.2,
    "urban_infrastructure_engineering":     4.0,
}

_LAG_CATEGORIES = {
    "architecture":                         "SLOW",
    "artificial_intelligence":              "LEAPFROG",
    "automotive_engineering":               "SLOW",
    "biomedical_engineering":               "MEDIUM",
    "business_bba":                         "LOCAL",
    "chemical_engineering":                 "MEDIUM",
    "chemistry_biochemistry":               "LOCAL",
    "civil_engineering":                    "LOCAL",
    "computer_science":                     "LEAPFROG",
    "construction_engineering":             "LOCAL",
    "cybersecurity":                        "FAST",
    "data_science":                         "FAST",
    "digital_media":                        "FAST",
    "economics":                            "LOCAL",
    "electrical_engineering":               "MEDIUM",
    "electronics_engineering":              "MEDIUM",
    "english_linguistics":                  "LOCAL",
    "finance_accounting":                   "LOCAL",
    "food_engineering":                     "MEDIUM",
    "industrial_manufacturing_engineering": "SLOW",
    "materials_engineering":                "SLOW",
    "mechanical_engineering":               "SLOW",
    "metallurgical_engineering":            "SLOW",
    "petroleum_engineering":                "SLOW",
    "physics":                              "LOCAL",
    "polymer_petrochemical_engineering":    "SLOW",
    "social_work":                          "LOCAL",
    "software_engineering":                 "LEAPFROG",
    "telecommunications_engineering":       "FAST",
    "textile_engineering":                  "LOCAL",
    "textile_sciences":                     "LOCAL",
    "urban_infrastructure_engineering":     "LOCAL",
}


def _build_lag_model_fixture() -> list:
    """Build a structurally valid lag_model.json array matching Point 4 schema."""
    entries = []
    for field_id in _FIELD_IDS:
        entries.append({
            "field_id": field_id,
            "field_name": field_id.replace("_", " ").title(),
            "associated_degrees": [f"neduet_{field_id}"],
            "lag_category": _LAG_CATEGORIES[field_id],
            "lifecycle_status": "Stable",
            "risk_factor": "Medium",
            "risk_reasoning": "Test fixture placeholder",
            "outsourcing_applicable": _LAG_CATEGORIES[field_id] != "LOCAL",
            "infrastructure_constrained": False,
            "constraint_note": "",
            "pakistan_now": {
                "job_postings_monthly": 500,
                "yoy_growth_rate": 0.15,
                "sources": ["rozee.pk"],
            },
            "world_now": {
                "us_yoy_growth_rate": 0.12,
                "uk_yoy_growth_rate": 0.10,
                "uae_yoy_growth_rate": 0.15,
                "sources": ["BLS 2024"],
            },
            "world_future": {
                "us_bls_4yr_projected_growth": 0.10,
                "bls_soc_code": "00-0000",
                "projection_basis": "test fixture",
            },
            "pakistan_future": {
                "projected_4yr_growth": 0.20,
                "derivation": "test fixture",
            },
            "lag_parameters": {
                "lag_years": 2.0,
                "arrival_confidence": "medium",
                "cultural_barrier": False,
                "societal_barrier": False,
                "notes": "test fixture",
            },
            "computed": {
                "future_value": _FUTURE_VALUES[field_id],
                "last_computed": "2026-04",
            },
            "employment_data": {
                "rozee_live_count": 500,
                "rozee_last_updated": "2026-04-01",
                "hec_employment_rate": None,
                "qualitative_pathway": None,
                "data_source_used": "rozee_live",
                "data_status": "sufficient",
            },
            "career_paths": {
                "entry_level_title": "Graduate",
                "typical_first_role_salary_pkr": "50,000 – 80,000/month",
                "common_sectors": ["Industry", "Research"],
            },
        })
    return entries


def _build_affinity_matrix_fixture() -> list:
    """Build a structurally valid affinity_matrix.json array matching Point 4 schema."""
    entries = []
    for field_id in _FIELD_IDS:
        entries.append({
            "field_id": field_id,
            "riasec_affinity": _RIASEC_AFFINITIES[field_id],
            "riasec_description": f"{field_id} RIASEC profile — test fixture",
            "social_acceptability_tier": "moderate",
            "prestige_note": "Test fixture entry",
        })
    return entries


@pytest.fixture
def fixture_data_dir(tmp_path, monkeypatch):
    """Write fixture lag_model.json and affinity_matrix.json to a temp dir.
    Monkeypatches scoring_node.DATA_DIR to point to the temp directory.
    Real data files in backend/app/data/ are NOT modified.
    """
    lag = _build_lag_model_fixture()
    affinity = _build_affinity_matrix_fixture()
    (tmp_path / "lag_model.json").write_text(json.dumps(lag), encoding="utf-8")
    (tmp_path / "affinity_matrix.json").write_text(json.dumps(affinity), encoding="utf-8")
    monkeypatch.setattr(scoring_node_module, "DATA_DIR", tmp_path)
    return tmp_path


# ── Test helpers ───────────────────────────────────────────────────────────────

def _make_roadmap_entry(
    field_id: str,
    degree_id: str,
    degree_name: str,
    university_name: str = "NED University",
) -> dict:
    """Build a minimal FilterNode-style roadmap entry for testing."""
    return {
        "degree_id": degree_id,
        "field_id": field_id,
        "university_id": "neduet",
        "university_name": university_name,
        "degree_name": degree_name,
        "eligibility_tier": "confirmed",
        "merit_tier": "likely",
        "final_tier": "likely",
        "eligibility_note": None,
        "aggregate_used": 77.5,
        "aggregate_formula": {
            "matric_weight": 0.10,
            "inter_weight": 0.50,
            "entry_test_weight": 0.40,
            "subject_weights": {"mathematics": 2.0, "physics": 1.5, "other": 1.0},
        },
        "fee_per_semester": 27500,
        "shift": "full_day",
        "soft_flags": [],
    }


def _base_state(
    riasec=None,
    subject_marks=None,
    capability_scores=None,
    roadmap=None,
    stated_preferences=None,
    student_mode="inter",
) -> dict:
    """Build a minimal valid AgentState for scoring tests."""
    return {
        "messages": [],
        "student_profile": {
            "riasec_scores": riasec or {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
            "subject_marks": subject_marks or {
                "mathematics": 80,
                "physics": 75,
                "chemistry": 70,
                "english": 85,
            },
            "capability_scores": capability_scores or {
                "mathematics": 62,
                "physics": 70,
                "chemistry": 65,
                "english": 72,
            },
            "education_level": "inter_part2",
            "student_mode": student_mode,
        },
        "active_constraints": {
            "budget_per_semester": 60000,
            "transport_willing": True,
            "home_zone": 2,
            "stated_preferences": stated_preferences if stated_preferences is not None else [],
        },
        "profiling_complete": True,
        "last_intent": "get_recommendation",
        "student_mode": student_mode,
        "education_level": "inter_part2",
        "current_roadmap": roadmap if roadmap is not None else [
            _make_roadmap_entry("computer_science", "neduet_bs_cs", "BS Computer Science"),
            _make_roadmap_entry("electrical_engineering", "neduet_bs_ee", "BS Electrical Engineering"),
            _make_roadmap_entry("civil_engineering", "neduet_bs_civil", "BS Civil Engineering"),
        ],
        "previous_roadmap": None,
        "thought_trace": [],
        "mismatch_notice": None,
        "conflict_detected": False,
    }


# ── Integration tests (require fixture_data_dir) ──────────────────────────────

def test_scoring_adds_total_score(fixture_data_dir):
    """Every entry in current_roadmap has total_score as float 0-1 after scoring."""
    state = _base_state()
    result = scoring_node(state)
    for entry in result["current_roadmap"]:
        assert "total_score" in entry, f"{entry['degree_name']} missing total_score"
        assert isinstance(entry["total_score"], float)
        assert 0.0 <= entry["total_score"] <= 1.0


def test_scoring_sorted_descending(fixture_data_dir):
    """current_roadmap is sorted descending by total_score after scoring."""
    state = _base_state()
    result = scoring_node(state)
    scores = [e["total_score"] for e in result["current_roadmap"]]
    assert scores == sorted(scores, reverse=True), "Scores must be in descending order"


def test_match_score_range(fixture_data_dir):
    """Every match_score_normalised is between 0.0 and 1.0 inclusive."""
    state = _base_state()
    result = scoring_node(state)
    for entry in result["current_roadmap"]:
        assert 0.0 <= entry["match_score_normalised"] <= 1.0, (
            f"{entry['degree_name']} match_score_normalised out of range: "
            f"{entry['match_score_normalised']}"
        )


def test_capability_blend_applied(fixture_data_dir):
    """Student with 35-point gap in mathematics triggers blend.
    capability_adjustment_applied=True and effective_grade_used['mathematics'] != 80."""
    # mathematics: reported=80, capability=45 → gap=35 ≥ 25 → blend triggers
    subject_marks = {"mathematics": 80, "physics": 75, "chemistry": 70, "english": 85}
    capability_scores = {"mathematics": 45, "physics": 70, "chemistry": 68, "english": 80}

    state = _base_state(subject_marks=subject_marks, capability_scores=capability_scores)
    result = scoring_node(state)

    for entry in result["current_roadmap"]:
        assert entry["capability_adjustment_applied"] is True, (
            f"{entry['degree_name']} should have capability blend applied"
        )
        assert entry["effective_grade_used"]["mathematics"] != 80, (
            "Effective mathematics grade must differ from reported 80 after blend"
        )


def test_capability_blend_not_applied(fixture_data_dir):
    """Student with ≤20-point gap in all subjects has capability_adjustment_applied=False."""
    # All gaps < 25 — no blend triggers for any subject
    subject_marks = {"mathematics": 80, "physics": 75, "chemistry": 70, "english": 85}
    capability_scores = {"mathematics": 65, "physics": 61, "chemistry": 55, "english": 70}
    # gaps: math=15, physics=14, chem=15, english=15

    state = _base_state(subject_marks=subject_marks, capability_scores=capability_scores)
    result = scoring_node(state)

    for entry in result["current_roadmap"]:
        assert entry["capability_adjustment_applied"] is False, (
            f"{entry['degree_name']} should NOT have blend applied (all gaps < 25)"
        )


def test_mismatch_notice_triggers(fixture_data_dir):
    """Student whose stated_preferences contains a low-FV, low-scoring degree
    gets a non-null mismatch_notice when the score gap is >= 20 on 0-100 scale.

    Verification (student R=32 I=45 A=28 S=31 E=38 C=42, theoretical_max=2160):
      CS  match=1129/2160=0.52, FV=8.5 → total=0.6*0.52+0.4*0.85=0.65
      Textile match=957/2160=0.44, FV=3.0 → total=0.6*0.44+0.4*0.30=0.39
      gap=(0.65-0.39)*100≈26 ≥ 20 and FV=3.0 < 6.0 → triggers.
    """
    roadmap = [
        _make_roadmap_entry("computer_science", "neduet_bs_cs", "BS Computer Science"),
        _make_roadmap_entry("electrical_engineering", "neduet_bs_ee", "BS Electrical Engineering"),
        _make_roadmap_entry("textile_engineering", "neduet_bs_textile", "BS Textile Engineering"),
    ]
    state = _base_state(roadmap=roadmap, stated_preferences=["Textile Engineering"])
    result = scoring_node(state)
    assert result["mismatch_notice"] is not None, (
        "Mismatch notice must be set when preferred degree has low score and FutureValue < 6"
    )


def test_mismatch_notice_absent(fixture_data_dir):
    """Student with no stated_preferences has mismatch_notice = None."""
    state = _base_state(stated_preferences=[])
    result = scoring_node(state)
    assert result["mismatch_notice"] is None


def test_effective_grade_used_is_dict(fixture_data_dir):
    """effective_grade_used is a dict keyed by subject name, not a float.
    All subjects from subject_marks are present."""
    state = _base_state()
    result = scoring_node(state)
    for entry in result["current_roadmap"]:
        assert isinstance(entry["effective_grade_used"], dict), (
            f"{entry['degree_name']} effective_grade_used must be dict, "
            f"got {type(entry['effective_grade_used'])}"
        )
        for subject in state["student_profile"]["subject_marks"]:
            assert subject in entry["effective_grade_used"], (
                f"effective_grade_used missing subject '{subject}' for {entry['degree_name']}"
            )


def test_missing_field_id_fallback(fixture_data_dir):
    """Degree with unknown field_id still appears in output with neutral defaults."""
    roadmap = [
        _make_roadmap_entry("computer_science", "neduet_bs_cs", "BS Computer Science"),
        _make_roadmap_entry("unknown_field_xyz", "neduet_bs_unknown", "BS Unknown Field"),
    ]
    state = _base_state(roadmap=roadmap)
    result = scoring_node(state)

    degree_ids = [e["degree_id"] for e in result["current_roadmap"]]
    assert "neduet_bs_unknown" in degree_ids, "Degree with unknown field_id must not be dropped"

    unknown_entry = next(e for e in result["current_roadmap"] if e["degree_id"] == "neduet_bs_unknown")
    assert unknown_entry["match_score_normalised"] == pytest.approx(0.5), (
        "Unknown field_id fallback match_score_normalised must be 0.5"
    )
    assert unknown_entry["future_score"] == pytest.approx(5.0), (
        "Unknown field_id fallback future_score must be 5.0"
    )


def test_existing_formula_tests_still_pass():
    """Meta-test: config constants used by all existing formula tests are unchanged."""
    assert settings.CAPABILITY_BLEND_THRESHOLD == 25
    assert settings.CAPABILITY_BLEND_WEIGHT == pytest.approx(0.25)
    assert settings.CAPABILITY_BLEND_MAX_SHIFT == 10
    assert settings.MISMATCH_SCORE_GAP_THRESHOLD == 20
    assert settings.MISMATCH_FUTURE_VALUE_CEILING == pytest.approx(6.0)
    assert settings.SCORING_WEIGHTS["inter"]["match"] == pytest.approx(0.6)
    assert settings.SCORING_WEIGHTS["inter"]["future"] == pytest.approx(0.4)
    assert settings.SCORING_WEIGHTS["matric_planning"]["match"] == pytest.approx(0.7)
    assert settings.SCORING_WEIGHTS["matric_planning"]["future"] == pytest.approx(0.3)


# ── Existing formula unit tests (pure math — no DB, no JSON needed) ────────────────

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
