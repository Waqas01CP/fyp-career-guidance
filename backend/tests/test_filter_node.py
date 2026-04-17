"""
test_filter_node.py — Sprint 3 production tests for FilterNode.

Uses simulated but realistic student profile against actual NED universities.json.
Test 3 uses stream="Pre-Medical" to force a hard exclusion on Pre-Engineering-only degrees.
Test cases cover: non-empty list, minimum display rule, hard exclusion, over_budget flag,
merit tier assignment, output field completeness, thought_trace population.

Run: pytest backend/tests/test_filter_node.py -v
"""

import pytest

from app.agents.nodes.filter_node import calculate_aggregate, filter_node
from app.core.config import settings

# ── Base simulated student profile ───────────────────────────────────────────

BASE_STUDENT_PROFILE = {
    "riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
    "subject_marks": {
        "mathematics": 82,
        "physics": 78,
        "chemistry": 71,
        "english": 80,
        "biology": 0,
    },
    "capability_scores": {
        "mathematics": 65.0,
        "physics": 70.0,
        "chemistry": 58.3,
        "biology": 0.0,
        "english": 75.0,
    },
    "education_level": "inter_part2",
    "grade_system": "percentage",
    "stream": "Pre-Engineering",
}


def _make_state(
    stream: str = "Pre-Engineering",
    budget: int = 60000,
    subject_marks: dict | None = None,
    student_mode: str = "inter",
    home_zone: int = 2,
) -> dict:
    profile = dict(BASE_STUDENT_PROFILE)
    profile["stream"] = stream
    if subject_marks is not None:
        profile["subject_marks"] = subject_marks
    return {
        "student_profile": profile,
        "active_constraints": {
            "budget_per_semester": budget,
            "transport_willing": True,
            "home_zone": home_zone,
        },
        "student_mode": student_mode,
        "thought_trace": [],
        "current_roadmap": [],
        "messages": [],
        "profiling_complete": True,
        "last_intent": "get_recommendation",
        "education_level": "inter_part2",
        "previous_roadmap": None,
        "mismatch_notice": None,
        "conflict_detected": False,
    }


# ── Test 1: result is a non-empty list ───────────────────────────────────────

def test_filter_returns_list():
    """filter_node must return a non-empty list for a standard Pre-Engineering student."""
    state = _make_state()
    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]

    assert isinstance(roadmap, list), "current_roadmap must be a list"
    assert len(roadmap) > 0, (
        "current_roadmap must be non-empty for a valid Pre-Engineering student "
        "with NED data loaded"
    )


# ── Test 2: minimum display rule — always >= FILTER_MINIMUM_RESULTS_SHOWN ────

def test_no_blank_screen():
    """Always >= FILTER_MINIMUM_RESULTS_SHOWN entries regardless of marks."""
    state = _make_state()
    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]

    assert len(roadmap) >= settings.FILTER_MINIMUM_RESULTS_SHOWN, (
        f"Expected at least {settings.FILTER_MINIMUM_RESULTS_SHOWN} results "
        f"(minimum display rule), got {len(roadmap)}"
    )


# ── Test 3: hard-excluded degree does not appear ──────────────────────────────

def test_hard_exclusion_not_in_output():
    """
    neduet_be_electrical has fully_eligible_streams=["Pre-Engineering"] only.
    No conditionally_eligible_streams. policy_pending_verification=false.

    A Pre-Medical student fails Check 1 (stream not in any eligible list, no policy waiver)
    → hard excluded → must NOT appear in results.

    Pre-Medical student is given high budget so minimum display rule is unlikely to
    promote neduet_be_electrical (NED has many degrees accepting Pre-Medical).
    """
    pre_medical_marks = {
        "biology": 88,
        "chemistry": 75,
        "physics": 70,
        "english": 78,
        "mathematics": 0,  # Pre-Medical students don't take Mathematics
    }
    state = _make_state(
        stream="Pre-Medical",
        budget=200000,
        subject_marks=pre_medical_marks,
        home_zone=3,
    )

    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]
    degree_ids_in_results = {entry["degree_id"] for entry in roadmap}

    # neduet_be_electrical: only Pre-Engineering eligible — must be hard excluded
    # for Pre-Medical stream with no pathway and no policy waiver
    assert "neduet_be_electrical" not in degree_ids_in_results, (
        "neduet_be_electrical (Pre-Engineering only, no conditional, "
        "policy_pending=false) must be hard-excluded for Pre-Medical student"
    )

    # Exclusion must be recorded in thought_trace
    trace_text = " ".join(result_state["thought_trace"])
    assert "excluded" in trace_text.lower(), (
        "thought_trace must contain exclusion entries for hard-excluded degrees"
    )


# ── Test 4: over_budget flag appears, degree is still included ────────────────

def test_soft_flag_over_budget():
    """
    neduet_bs_cs has fee_per_semester=60475. Budget=60000.
    60475 > 60000 → over_budget soft flag must appear.
    Degree must still be in results (budget never hard-excludes).
    """
    state = _make_state(budget=60000)
    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]

    # At least one over_budget entry must exist
    over_budget_entries = [
        e for e in roadmap
        if any(f["type"] == "over_budget" for f in e["soft_flags"])
    ]
    assert len(over_budget_entries) > 0, (
        "Expected at least one entry with over_budget flag "
        "(neduet_bs_cs fee=60475 > budget=60000)"
    )

    # neduet_bs_cs specifically must appear (not excluded despite over budget)
    neduet_bs_cs = next(
        (e for e in roadmap if e["degree_id"] == "neduet_bs_cs"), None
    )
    assert neduet_bs_cs is not None, (
        "neduet_bs_cs must appear in results even when fee exceeds budget"
    )
    flag_types = {f["type"] for f in neduet_bs_cs["soft_flags"]}
    assert "over_budget" in flag_types, (
        "neduet_bs_cs must carry over_budget flag when fee=60475 > budget=60000"
    )


# ── Test 5: merit_tier assigned on all inter-mode entries ─────────────────────

def test_merit_tier_assigned():
    """In inter mode, every entry must have a valid merit_tier (not None)."""
    state = _make_state(student_mode="inter")
    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]

    assert len(roadmap) > 0, "Roadmap must be non-empty"

    valid_tiers = {"confirmed", "likely", "stretch", "improvement_needed"}
    for entry in roadmap:
        assert entry["merit_tier"] is not None, (
            f"{entry['degree_id']}: merit_tier must not be None in inter mode"
        )
        assert entry["merit_tier"] in valid_tiers, (
            f"{entry['degree_id']}: merit_tier '{entry['merit_tier']}' is invalid"
        )


# ── Test 6: every output entry has all required fields ───────────────────────

REQUIRED_FIELDS = {
    "degree_id",
    "field_id",
    "university_id",
    "university_name",
    "degree_name",
    "eligibility_tier",
    "merit_tier",
    "final_tier",
    "aggregate_used",
    "fee_per_semester",
    "soft_flags",
    "eligibility_note",
}


def test_output_fields_complete():
    """Every roadmap entry must contain all required fields with valid types."""
    state = _make_state()
    result_state = filter_node(state)
    roadmap = result_state["current_roadmap"]

    assert len(roadmap) > 0, "Roadmap must be non-empty"

    for i, entry in enumerate(roadmap):
        missing = REQUIRED_FIELDS - set(entry.keys())
        assert not missing, (
            f"Entry {i} ({entry.get('degree_id', '?')}) missing fields: {missing}"
        )
        assert entry["eligibility_tier"] in ("confirmed", "likely"), (
            f"Entry {i} eligibility_tier '{entry['eligibility_tier']}' invalid"
        )
        assert entry["final_tier"] in (
            "confirmed", "likely", "stretch", "improvement_needed"
        ), f"Entry {i} final_tier '{entry['final_tier']}' invalid"
        assert isinstance(entry["soft_flags"], list), (
            f"Entry {i} soft_flags must be a list"
        )
        assert isinstance(entry["fee_per_semester"], (int, float)), (
            f"Entry {i} fee_per_semester must be numeric"
        )


# ── Test 7: thought_trace is populated after node runs ───────────────────────

def test_thought_trace_populated():
    """state['thought_trace'] must contain plain strings after filter_node."""
    state = _make_state()
    result_state = filter_node(state)
    trace = result_state["thought_trace"]

    assert isinstance(trace, list), "thought_trace must be a list"
    assert len(trace) > 0, "thought_trace must be non-empty after filter_node"

    for entry in trace:
        assert isinstance(entry, str), (
            f"Each thought_trace entry must be a plain string, got: {type(entry)}"
        )


# ── Unit tests for calculate_aggregate helper ─────────────────────────────────

def test_calculate_aggregate_excludes_zero_marks():
    """Subjects with mark==0 must not affect the weighted average."""
    formula = {
        "subject_weights": {"mathematics": 1.0, "physics": 1.0, "other": 1.0}
    }
    marks_with_zero = {"mathematics": 80, "physics": 70, "biology": 0}
    marks_without_zero = {"mathematics": 80, "physics": 70}

    agg_with = calculate_aggregate(marks_with_zero, formula)
    agg_without = calculate_aggregate(marks_without_zero, formula)

    assert abs(agg_with - agg_without) < 0.01, (
        f"biology=0 must not change aggregate: with={agg_with:.2f}, "
        f"without={agg_without:.2f}"
    )
    assert abs(agg_with - 75.0) < 0.01, (
        f"(80+70)/2 = 75.0, got {agg_with:.2f}"
    )


def test_calculate_aggregate_uses_subject_weights():
    """Higher weight on mathematics should pull aggregate toward math score."""
    formula = {
        "subject_weights": {"mathematics": 2.0, "physics": 1.0, "other": 1.0}
    }
    marks = {"mathematics": 90, "physics": 60}
    agg = calculate_aggregate(marks, formula)
    # (90*2 + 60*1) / (2+1) = 240/3 = 80.0
    assert abs(agg - 80.0) < 0.01, f"Expected 80.0, got {agg:.2f}"


def test_calculate_aggregate_all_zero_returns_zero():
    """All-zero subject_marks must return 0.0 without division by zero."""
    formula = {"subject_weights": {"mathematics": 1.0}}
    assert calculate_aggregate({"mathematics": 0}, formula) == 0.0
    assert calculate_aggregate({}, formula) == 0.0
