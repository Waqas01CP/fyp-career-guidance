# Claude Code Session Log
**Date:** 2026-04-18 00:00
**Task:** Update filter_node.py per CLAUDE.md v1.9 — add Check 0 (HEC floor), calculate_estimated_merit(), Check 3b (entry test difficulty), shift field, aggregate_formula in output; add 3 new tests. Total: 13/13 tests pass.
**Status:** COMPLETE

## Files Changed
- `backend/app/agents/nodes/filter_node.py` — Added calculate_estimated_merit() helper; Check 0 (HEC/council legal floor, hard exclusion never in hard_excluded_raw); Check 3 updated to use calculate_estimated_merit() instead of direct calculate_aggregate(); Check 3b (entry_test_harder_than_assessed soft flag for hard/extreme difficulty tiers); shift field added to results, hard_excluded_raw, and promoted entries; aggregate_formula added to results and promoted entries (pre-existing omission corrected).
- `backend/app/core/config.py` — Added CAPABILITY_PROXY_DEFAULT (50.0) and ENTRY_TEST_SUBJECT_MAP (maps entry_test weight keys to capability_scores subject names). Neither was present before this session despite being specified in Point 2 Section 15.
- `backend/tests/test_filter_node.py` — Added 3 new tests: test_hec_floor_hard_exclusion, test_entry_test_proxy_flag_present, test_shift_field_in_output.

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md` (v1.9)
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md`
- `backend/app/agents/nodes/filter_node.py` (pre-change)
- `backend/app/core/config.py` (pre-change)
- `backend/tests/test_filter_node.py` (pre-change)
- `backend/app/data/universities.json` (first 160 lines — field structure verification)

## Plan Summary (Phase 1)

Six changes identified:
1. **calculate_estimated_merit()**: standalone helper alongside calculate_aggregate(). Returns (float, bool). When entry_test_weight==0.0 returns (inter_component, False). When >0 builds proxy from ENTRY_TEST_SUBJECT_MAP × capability_scores, defaults to CAPABILITY_PROXY_DEFAULT=50.0 when score missing.
2. **Check 0 (HEC floor)**: `hec_excluded = False` before `hard_exclude = False`. Simple mean of non-zero subject_marks (unadjusted, no subject weights per HEC spec). Compared against `elig["min_percentage_hssc"]`. On failure: thought_trace with governing council, `continue` — never enters `hard_excluded_raw`.
3. **Check 3 update**: replace `calculate_aggregate()` call with `calculate_estimated_merit()`. Append `entry_test_proxy_used` soft flag when proxy_used=True.
4. **Check 3b**: runs when proxy_used=True. Reads `university.get("entry_test_difficulty_tier", "standard")`. Appends `entry_test_harder_than_assessed` for "hard" or "extreme".
5. **shift field**: added to results.append(), both hard_excluded_raw.append() blocks, and minimum display promotion block.
6. **aggregate_formula**: pre-existing omission — added to results.append() and minimum display promotion block.

Config change: CAPABILITY_PROXY_DEFAULT (float) and ENTRY_TEST_SUBJECT_MAP (dict via Field(default_factory)) added to Settings class.

## Deviations from Plan

**aggregate_formula pre-existing omission**: Session log from 2026-04-17 stated "aggregate_formula added to roadmap entries for ScoringNode integration" but the actual code did not contain it in results.append({}). Corrected in this session. Flagged explicitly.

**proxy_used = False in matric_planning branch**: Added to avoid any potential uninitialized variable risk, even though proxy_used is not referenced after the Check 3/3b block. Low-cost defensive initialization.

## Self-Review Findings (Phase 3)

All invariants confirmed:
- hec_excluded never reaches hard_excluded_raw: `continue` at line 225 fires before both `hard_excluded_raw.append()` calls
- capability_scores extracted at line 159, before calculate_estimated_merit() at line 324
- aggregate_formula in results.append() (line 493) and promoted entries (line 523)
- shift in results.append() (line 495), both hard_excluded_raw blocks (lines 274, 318), promoted entries (line 525)
- All 10 existing REQUIRED_FIELDS still present — new fields added, none removed
- No duplicate constants in config.py

## Integration Boundary Check (Phase 4)

ScoringNode reads from state["current_roadmap"]. Fields it requires:
- degree_id ✓ | university_id ✓ | university_name ✓ | degree_name ✓ | field_id ✓
- merit_tier ✓ | soft_flags ✓ | final_tier ✓ | eligibility_tier ✓ | eligibility_note ✓
- aggregate_used ✓ | aggregate_formula ✓ (calls calculate_aggregate() with it)
- fee_per_semester ✓ | shift ✓ (passed through for display)

All required fields confirmed present.

## Test Results

```
tests/test_filter_node.py::test_filter_returns_list PASSED
tests/test_filter_node.py::test_no_blank_screen PASSED
tests/test_filter_node.py::test_hard_exclusion_not_in_output PASSED
tests/test_filter_node.py::test_soft_flag_over_budget PASSED
tests/test_filter_node.py::test_merit_tier_assigned PASSED
tests/test_filter_node.py::test_output_fields_complete PASSED
tests/test_filter_node.py::test_thought_trace_populated PASSED
tests/test_filter_node.py::test_calculate_aggregate_excludes_zero_marks PASSED
tests/test_filter_node.py::test_calculate_aggregate_uses_subject_weights PASSED
tests/test_filter_node.py::test_calculate_aggregate_all_zero_returns_zero PASSED
tests/test_filter_node.py::test_hec_floor_hard_exclusion PASSED
tests/test_filter_node.py::test_entry_test_proxy_flag_present PASSED
tests/test_filter_node.py::test_shift_field_in_output PASSED

13 passed in 1.31s
```

All 13 tests pass. No fixes needed after initial implementation.

## Known Failure Modes

- `filter_node.py:328` — `degree["entry_test"]` accessed directly (no .get()). If any degree in universities.json is missing the `entry_test` key, this raises KeyError inside calculate_estimated_merit(). All NED degrees verified to have this key; only affects future university data entries.
- `filter_node.py:206` — `elig["min_percentage_hssc"]` accessed directly. If any degree is missing this key in universities.json, this raises KeyError. All NED degrees verified to have it.
- `filter_node.py:234` — `elig["eligibility_notes"][stream]` accessed directly when stream is in conditionally_eligible_streams. If the stream is in the list but not in the notes dict, this raises KeyError. Data integrity rule from Point 4.

## Issues Noticed (not fixed)

None found in adjacent code.

## What Architecture Chat Should Review

1. **calculate_estimated_merit() implementation**: The proxy_score builds from ENTRY_TEST_SUBJECT_MAP × entry_test weight keys × capability_scores. For neduet_bs_cs: math_weight=0.25, physics_weight=0.25, chemistry_weight=0.25, english_weight=0.25 (no biology_weight). proxy_score = (65×0.25)+(70×0.25)+(58.3×0.25)+(75×0.25) = 67.075. estimated_merit = (77.75×0.4)+(67.075×0.6) = 71.35. This is below neduet_bs_cs cutoff_min=83.59 → merit_tier=improvement_needed. Confirm this formula is architecturally correct.

2. **Check 0 exclusion path — confirm never touches hard_excluded_raw**: `if hec_excluded: continue` at line 222-225. Both `hard_excluded_raw.append()` calls are at lines 265-276 and 309-320. The `continue` at line 225 skips to the next degree iteration entirely — hard_excluded_raw is never reached. Confirm this is the intended behaviour for the minimum display rule.

3. **config.py constants — were absent, now added**: CAPABILITY_PROXY_DEFAULT and ENTRY_TEST_SUBJECT_MAP were specified in Point 2 Section 15 but were not in the actual config.py before this session. Both have been added. Confirm no other config constants from Point 2 Section 15 are missing.

4. **Entry test proxy confirmed firing**: neduet_bs_cs has entry_test_weight=0.6 in aggregate_formula. test_entry_test_proxy_flag_present passes against NED data, confirming at least one degree in current universities.json triggers the proxy path. All other NED degrees with entry_test_weight > 0 will also generate the entry_test_proxy_used soft flag.

5. **aggregate_formula pre-existing omission**: The 2026-04-17 session log stated aggregate_formula was added to roadmap entries but the code did not contain it. Corrected in this session. Confirm ScoringNode build can now proceed with aggregate_formula in every roadmap entry.

6. **NED entry_test_difficulty_tier is "standard"**: All current NED degrees use "standard" difficulty tier (verified at university level in universities.json line 29). Check 3b will not fire for NED data. When FAST/NUST data is added with "hard"/"extreme" tiers, Check 3b will fire. Architecture Chat should confirm this is expected for the current data state.

## 2026-04-20 Addendum

Added `"entry_test": degree.get("entry_test", {})` to results.append() (after aggregate_formula) and `"entry_test": exc.get("entry_test", {})` to the minimum display promotion block (after aggregate_formula). Required by ExplanationNode to access entry test subject weights when constructing degree explanations. 13/13 tests pass unchanged.
