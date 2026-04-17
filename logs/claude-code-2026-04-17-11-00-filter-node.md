# Claude Code Session Log
**Date:** 2026-04-17 11:00
**Task:** Implement FilterNode production code (replace Sprint 1 stub)
**Status:** COMPLETE

---

## Files Changed
- `backend/app/agents/nodes/filter_node.py` — full production implementation replacing Sprint 1 stub
- `backend/tests/test_filter_node.py` — replaced Khuzzaim's Sprint 1 stub tests with 10 Sprint 3 production tests

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md`
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md`
- `docs/00_architecture/POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md`
- `backend/app/agents/state.py`
- `backend/app/agents/nodes/filter_node.py` (stub, read before replacing)
- `backend/app/core/config.py`
- `backend/app/data/universities.json` (read first 1200 lines — full NED dataset)
- `backend/tests/test_filter_node.py` (stub, read before replacing)

---

## Plan Summary (Phase 1)

### Helper functions
1. `calculate_aggregate(subject_marks, aggregate_formula) -> float` — weighted average of subject marks using `aggregate_formula.subject_weights`; excludes marks==0 (not-taken subjects). Judgment call: biology=0 for Pre-Engineering student treated as "not taken" to avoid unfair aggregate drag.
2. `_commute_description(zone_diff)` — returns "easy"/"moderate"/"difficult" commute label
3. `_estimate_travel(zone_diff)` — returns travel time range string
4. `_weakest_required_subject(subject_marks, mandatory_subjects)` — finds weakest mandatory subject for advice text
5. `_build_improvement_needed_flag(...)` — constructs improvement_needed soft flag dict

### Loop structure
Outer loop: universities; inner loop: degrees. Five checks in order. Hard exclusions exit with `continue`; soft fails attach flags. Results collected into `results` list. `hard_excluded_raw` list maintained for minimum display promotion.

### Pre-resolved conflicts applied
- **Conflict A**: `min_percentage_hssc` NOT a hard exclusion — only `cutoff_range.min/max` used in Check 3.
- **Conflict B**: BACKEND_CHAT_INSTRUCTIONS "relax budget/zone" minimum rule superseded by promoted-entries-in-JSON-order approach (affinity_matrix not available in FilterNode).

---

## Deviations from Plan

1. **aggregate_formula included in every roadmap entry** — Phase 4 revealed ScoringNode calls `calculate_aggregate(effective_marks, degree["aggregate_formula"])` from the roadmap entry. Point 2 Section 7 example output does not list this field, but Section 8 code requires it. Added it. Flagged for Architecture Chat review below.

2. **ormsgpack reinstall required before tests** — `ormsgpack` native extension was broken in the dev venv. Ran `pip install --force-reinstall ormsgpack`. This is an environment issue, not a code issue. All 10 tests then passed.

3. **Prior test file replaced** — `test_filter_node.py` contained Khuzzaim's Sprint 1 stub tests (all `@pytest.mark.skip` except `test_filter_node_stub_runs`). These were superseded by 10 production tests covering the 7 required cases plus 3 unit tests for `calculate_aggregate`.

---

## Self-Review Findings (Phase 3)

All field paths verified against actual NED universities.json data:

| Check | Finding |
|---|---|
| `university["name"]` vs `"university_name"` | Correct — actual field is `"name"` |
| `degree["name"]` vs `"degree_name"` | Correct — actual field is `"name"` |
| `degree["location"]["zone"]` | Present at degree level ✓ |
| `degree["fee_per_semester"]` | Flat int field ✓ |
| `degree["eligibility"]["eligibility_notes"][stream]` | Direct access used; guaranteed by validation Rule 5 |
| `subject_weights` case | Lowercase keys match subject_marks lowercase keys ✓ |
| `mandatory_subjects` Title Case vs subject_marks lowercase | Normalized with `.lower()` in Check 2 ✓ |
| `merit_tier=None` in matric_planning | Handled by `if merit_tier is None: final_tier = eligibility_tier` ✓ |

**No discrepancies found** beyond the `aggregate_formula` addition documented in Deviations.

---

## Integration Boundary Check Result (Phase 4)

ScoringNode reads from current_roadmap entries (Point 2 Section 8):

| ScoringNode field access | Present in FilterNode output? |
|---|---|
| `degree["field_id"]` | ✓ |
| `degree["aggregate_formula"]` | ✓ (added as deviation — required by Section 8 code) |
| `degree["degree_name"]` | ✓ |
| `degree["merit_tier"]` | ✓ |
| `degree["soft_flags"]` | ✓ |
| `degree["eligibility_tier"]` | ✓ |
| `degree["eligibility_note"]` | ✓ |
| `degree["fee_per_semester"]` | ✓ |
| `degree["university_name"]` | ✓ |
| `degree["university_id"]` | ✓ |
| `degree["degree_id"]` | ✓ |
| `degree["final_tier"]` | ✓ |
| `degree["aggregate_used"]` | ✓ |

**All ScoringNode inputs confirmed present.**

---

## Test Results

```
platform win32 -- Python 3.11.9, pytest-8.3.3
collected 10 items

tests/test_filter_node.py::test_filter_returns_list                        PASSED
tests/test_filter_node.py::test_no_blank_screen                            PASSED
tests/test_filter_node.py::test_hard_exclusion_not_in_output               PASSED
tests/test_filter_node.py::test_soft_flag_over_budget                      PASSED
tests/test_filter_node.py::test_merit_tier_assigned                        PASSED
tests/test_filter_node.py::test_output_fields_complete                     PASSED
tests/test_filter_node.py::test_thought_trace_populated                    PASSED
tests/test_filter_node.py::test_calculate_aggregate_excludes_zero_marks    PASSED
tests/test_filter_node.py::test_calculate_aggregate_uses_subject_weights   PASSED
tests/test_filter_node.py::test_calculate_aggregate_all_zero_returns_zero  PASSED

10 passed in 1.89s
```

**One pre-run fix required:** `ormsgpack` native extension was broken in venv. Force-reinstall fixed it. Not a code issue.

**Test 3 design note:** NED-only data has no degree that hard-excludes Pre-Engineering stream. Test 3 uses `stream="Pre-Medical"` to test exclusion of `neduet_be_electrical` (fully_eligible: ["Pre-Engineering"] only, no conditionals, policy_pending=false). This is the correct approach given the current data.

---

## Known Failure Modes

| Line | Condition | Error |
|---|---|---|
| ~105 | `elig["eligibility_notes"][stream]` | `KeyError` if validation Rule 5 violated in data — stream is in `conditionally_eligible_streams` but has no key in `eligibility_notes`. Mitigated by data validation script in Point 4. |
| ~118 | `elig["subject_waivers"].get(subject)` where subject is Title Case | `None` returned for missing key is correct. If `subject_waivers` field is entirely absent from a degree (not `{}`), would raise `KeyError`. All NED degrees have `subject_waivers: {}` per actual data — safe. |
| ~157 | `degree["cutoff_range"]["min"]` / `["max"]` | `KeyError` if degree lacks `cutoff_range`. All NED degrees have this field. Future data entries must also include it. |
| ~175 | `degree["location"]["zone"]` | `KeyError` if degree lacks nested `location.zone`. All NED degrees have it. Future entries must include it. |
| ~148 | `calculate_aggregate` returns 0.0 when all marks are 0 | `aggregate=0.0` → `merit_tier="improvement_needed"` for all degrees. Correct behavior for a student with all-zero marks (e.g., matric_planning student accidentally routed through inter mode). |

---

## What Architecture Chat Should Review

### 1. `calculate_aggregate()` function

```python
def calculate_aggregate(subject_marks: dict, aggregate_formula: dict) -> float:
    subject_weights = aggregate_formula.get("subject_weights", {})
    other_weight = float(subject_weights.get("other", 1.0))

    total_weighted = 0.0
    total_weight = 0.0

    for subject, mark in subject_marks.items():
        if mark == 0:
            continue  # treat as not taken
        w = float(subject_weights.get(subject, other_weight))
        total_weighted += mark * w
        total_weight += w

    if total_weight == 0.0:
        return 0.0
    return total_weighted / total_weight
```

**Judgment calls inside:**
- Subjects with `mark == 0` excluded from calculation. Rationale: biology=0 for Pre-Engineering student means "not taken", not "zero score". Including it with weight 1.0 drops aggregate from ~77.75 to ~62.2 unfairly.
- `inter_weight` (0.4 for NED) NOT applied. Rationale: the cutoff_range values in NED data are merit scores (inter + entry test). Applying inter_weight would give a partial score (77.75 × 0.4 = 31.1) that's not comparable to a cutoff of 83.59. The aggregate is used as an approximation of the student's marks component.
- Architecture Chat should confirm: is `mark == 0` the correct sentinel for "not taken"? Or should we check if the subject appears in a "relevant subjects" set per degree?

### 2. Minimum display rule implementation

```python
min_show: int = settings.FILTER_MINIMUM_RESULTS_SHOWN
if len(results) < min_show:
    needed = min_show - len(results)
    for exc in hard_excluded_raw[:needed]:
        exc_agg = (
            round(calculate_aggregate(subject_marks, exc["aggregate_formula"]), 2)
            if student_mode != "matric_planning"
            else None
        )
        results.append({
            ...
            "eligibility_tier": "likely",
            "merit_tier": "improvement_needed",
            "final_tier": "improvement_needed",
            ...
        })
```

**Judgment call:** Promoted entries are taken in JSON iteration order (order they appeared in universities.json). The prompt pre-resolution says "ranked by RIASEC match score approximation (sum of riasec_scores values)" but since all excluded degrees would get the same student RIASEC sum (it's per-student, not per-degree), and affinity_matrix is not available in FilterNode, JSON order is the only viable approximation. Architecture Chat should confirm this is acceptable OR clarify what "sum of riasec_scores values" means in context.

**Promoted entry eligibility_tier**: Set to `"likely"` as a soft default. Architecture Chat should confirm: should hard-excluded promoted entries show as `"likely"` or something more honest like a new tier? For now, the `planning_mode` soft flag and eligibility_note string communicate the situation.

### 3. `aggregate_formula` included in roadmap entries

Point 2 Section 7 example output does NOT list `aggregate_formula` in the roadmap entry. However, Point 2 Section 8 ScoringNode code accesses `degree["aggregate_formula"]` directly. FilterNode includes it so ScoringNode can run `calculate_aggregate(effective_marks, degree["aggregate_formula"])` without re-reading universities.json. Architecture Chat should confirm this addition is intended.

### 4. `eligibility_notes` direct access with empty `conditionally_eligible_streams`

When `conditionally_eligible_streams: []` and `eligibility_notes: {}`, the stream check falls through to the `else` branch (not the `elif` branch). Direct access to `eligibility_notes[stream]` is only executed when `stream in conditionally_eligible_streams` is True, which means the key is guaranteed to exist (by validation Rule 5). This pattern is correct and matches Point 4's documented behavior.

---

## Architecture Chat Review Fix — 2026-04-17

Two fields removed from both roadmap entry dicts (main `results.append` block and minimum display promotion block):

1. **`"aggregate_formula": degree["aggregate_formula"]`** — removed.
   Rationale: not in Point 3's 15-field roadmap_snapshot schema. ScoringNode will re-read `aggregate_formula` from `universities.json` by `degree_id` directly — passing it through the roadmap was unnecessary coupling.

2. **`"hard_excluded": False`** — removed.
   Rationale: every entry in `current_roadmap` is by definition not hard-excluded (hard-excluded entries never reach `results.append`). The field was meaningless and not in the schema.

Note: `hard_excluded_raw` still stores `"aggregate_formula"` internally (used to compute `exc_agg` via `calculate_aggregate()` inside the minimum display promotion block). This is correct — it is internal bookkeeping, not a roadmap output field.

`REQUIRED_FIELDS` in `test_output_fields_complete` already did not include either field — no test changes needed. All 10 tests pass after the fix (1.21s).
