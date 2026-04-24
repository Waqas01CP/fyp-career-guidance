# Claude Code Session Log
**Date:** 2026-04-18 14:00
**Task:** Implement scoring_node.py — full production implementation replacing Sprint 1 stub
**Status:** COMPLETE

---

## Files Changed
- `backend/app/agents/nodes/scoring_node.py` — replaced Sprint 1 stub with full production implementation: per-subject capability blend, RIASEC dot product, FutureValue lookup, total_score, mismatch detection, missing field_id fallback
- `backend/tests/test_scoring_node.py` — added 10 integration tests (kept all 8 existing formula tests unchanged); added fixture infrastructure for all 32 NED field_ids

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md` (v1.9)
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md` (Section 8 in full)
- `docs/00_architecture/POINT_3_DATABASE_SCHEMA_v1_4.md`
- `docs/00_architecture/POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md`
- `backend/app/agents/nodes/scoring_node.py` (stub)
- `backend/app/agents/nodes/filter_node.py`
- `backend/app/agents/state.py`
- `backend/app/core/config.py`
- `backend/tests/test_scoring_node.py` (existing)

---

## PHASE 1 — Plan Summary

**Data loading:** `_load_affinity_matrix()` and `_load_lag_model()` called at node entry (not module-level). Both return dicts keyed by `field_id` for O(1) lookup. `DATA_DIR` is a module-level variable so tests can monkeypatch it.

**Scoring loop:** For each degree in `current_roadmap`:
1. Per-subject capability blend: iterate `subject_marks.items()`, compare each to `capability_scores.get(subject)`. Trigger at `abs(gap) >= 25`. Apply: `raw_eff = reported*0.75 + cap*0.25`, cap at ±10. Build `effective_marks` dict. Pass to `calculate_aggregate(effective_marks, degree["aggregate_formula"])`. `aggregate_formula` read from roadmap entry (FilterNode put it there) — universities.json NOT re-read.
2. RIASEC dot product: `student_vector = [riasec_scores.get(dim,0) for dim in "RIASEC"]`. `theoretical_max = sum(s*10 for s in student_vector)`. `match_score_normalised = raw_match / theoretical_max` (0.0 if theoretical_max=0).
3. FutureValue: `lag_model[field_id]["computed"]["future_value"]`.
4. Total score: `weights["match"] * match_score_normalised + weights["future"] * future_score / 10`.

**Missing field_id fallback:** If not in affinity_matrix or lag_model → log warning to thought_trace, use `match_score_normalised=0.5`, `future_score=5.0`. Degree never dropped.

**Mismatch detection:** After sort, reset `state["mismatch_notice"] = None`. Use pre-resolved formula: `score_gap = (top_match_score - pref_score) * 100`. Trigger when `score_gap >= 20 AND pref_fv < 6.0`. Maximum one notice (break on first trigger).

**AgentState writes:** `current_roadmap` (sorted + 5 new fields per entry), `thought_trace` (appended only), `mismatch_notice` (str or None). All other fields untouched.

## Deviations from Plan
None. Implementation matches plan exactly.

---

## PHASE 3 — Self-review Findings

All checklist items passed:
- `calculate_aggregate` imported from `filter_node`, not rewritten ✓
- Capability blend is per-subject dict ✓
- `effective_grade_used` is `dict[str, float]` with ALL subjects from `subject_marks` ✓
- `aggregate_formula` from roadmap entry (not universities.json) ✓
- Missing field_id fallback present ✓
- `mismatch_notice = None` before detection loop ✓
- `thought_trace` appended, not reset ✓
- All 15 roadmap_snapshot fields present after ScoringNode ✓

---

## PHASE 4 — Integration Boundary Check

All fields ExplanationNode reads from `current_roadmap` and `state` are present after ScoringNode:

| Field | Present? |
|---|---|
| `degree["total_score"]` | ✓ Added by ScoringNode |
| `degree["merit_tier"]` | ✓ From FilterNode, preserved |
| `degree["match_score_normalised"]` | ✓ Added by ScoringNode |
| `degree["future_score"]` | ✓ Added by ScoringNode |
| `degree["fee_per_semester"]` | ✓ From FilterNode, preserved |
| `degree["soft_flags"]` | ✓ From FilterNode, preserved |
| `degree["university_name"]`, `degree["degree_name"]` | ✓ From FilterNode, preserved |
| `state["mismatch_notice"]` | ✓ Set by ScoringNode |
| `state["thought_trace"]` | ✓ Appended by ScoringNode |
| `state["student_profile"]` | ✓ Untouched |
| `state["active_constraints"]` | ✓ Untouched |
| `state["previous_roadmap"]` | ✓ Untouched |
| `state["student_mode"]` | ✓ Untouched |

---

## Verification Result

```
pytest tests/test_scoring_node.py -v
18 passed in 3.66s
```

All 18 tests passed:
- 10 new integration tests (tests 1-10) ✓
- 8 existing formula unit tests ✓

---

## FIXTURE DATA (mandatory)

### Monkeypatch path
```python
import app.agents.nodes.scoring_node as scoring_node_module
monkeypatch.setattr(scoring_node_module, "DATA_DIR", tmp_path)
```

The `_load_affinity_matrix()` and `_load_lag_model()` functions reference `DATA_DIR` at call time. Monkeypatching the module attribute before calling `scoring_node()` routes all file reads to the temp directory. Real files (`backend/app/data/lag_model.json`, `affinity_matrix.json`) are never modified.

### lag_model fixture — complete entry example (cybersecurity)
```json
{
  "field_id": "cybersecurity",
  "field_name": "Cybersecurity",
  "associated_degrees": ["neduet_cybersecurity"],
  "lag_category": "FAST",
  "lifecycle_status": "Stable",
  "risk_factor": "Medium",
  "risk_reasoning": "Test fixture placeholder",
  "outsourcing_applicable": true,
  "infrastructure_constrained": false,
  "constraint_note": "",
  "pakistan_now": {"job_postings_monthly": 500, "yoy_growth_rate": 0.15, "sources": ["rozee.pk"]},
  "world_now": {"us_yoy_growth_rate": 0.12, "uk_yoy_growth_rate": 0.10, "uae_yoy_growth_rate": 0.15, "sources": ["BLS 2024"]},
  "world_future": {"us_bls_4yr_projected_growth": 0.10, "bls_soc_code": "00-0000", "projection_basis": "test fixture"},
  "pakistan_future": {"projected_4yr_growth": 0.20, "derivation": "test fixture"},
  "lag_parameters": {"lag_years": 2.0, "arrival_confidence": "medium", "cultural_barrier": false, "societal_barrier": false, "notes": "test fixture"},
  "computed": {"future_value": 8.0, "last_computed": "2026-04"},
  "employment_data": {"rozee_live_count": 500, "rozee_last_updated": "2026-04-01", "hec_employment_rate": null, "qualitative_pathway": null, "data_source_used": "rozee_live", "data_status": "sufficient"},
  "career_paths": {"entry_level_title": "Graduate", "typical_first_role_salary_pkr": "50,000 – 80,000/month", "common_sectors": ["Industry", "Research"]}
}
```

### All 32 field_ids — future_value and lag_category

| field_id | future_value | lag_category |
|---|---|---|
| architecture | 4.5 | SLOW |
| artificial_intelligence | 9.2 | LEAPFROG |
| automotive_engineering | 4.0 | SLOW |
| biomedical_engineering | 6.5 | MEDIUM |
| business_bba | 5.5 | LOCAL |
| chemical_engineering | 5.5 | MEDIUM |
| chemistry_biochemistry | 4.0 | LOCAL |
| civil_engineering | 4.5 | LOCAL |
| computer_science | 8.5 | LEAPFROG |
| construction_engineering | 3.8 | LOCAL |
| cybersecurity | 8.0 | FAST |
| data_science | 7.8 | FAST |
| digital_media | 6.5 | FAST |
| economics | 5.0 | LOCAL |
| electrical_engineering | 7.0 | MEDIUM |
| electronics_engineering | 6.0 | MEDIUM |
| english_linguistics | 3.5 | LOCAL |
| finance_accounting | 5.5 | LOCAL |
| food_engineering | 5.0 | MEDIUM |
| industrial_manufacturing_engineering | 4.0 | SLOW |
| materials_engineering | 4.0 | SLOW |
| mechanical_engineering | 5.0 | SLOW |
| metallurgical_engineering | 3.5 | SLOW |
| petroleum_engineering | 5.0 | SLOW |
| physics | 3.5 | LOCAL |
| polymer_petrochemical_engineering | 4.5 | SLOW |
| social_work | 3.0 | LOCAL |
| software_engineering | 8.3 | LEAPFROG |
| telecommunications_engineering | 7.0 | FAST |
| textile_engineering | 3.0 | LOCAL |
| textile_sciences | 3.2 | LOCAL |
| urban_infrastructure_engineering | 4.0 | LOCAL |

### affinity_matrix fixture — complete entry example (cybersecurity)
```json
{
  "field_id": "cybersecurity",
  "riasec_affinity": {"R": 5, "I": 9, "A": 2, "S": 4, "E": 5, "C": 8},
  "riasec_description": "cybersecurity RIASEC profile — test fixture",
  "social_acceptability_tier": "moderate",
  "prestige_note": "Test fixture entry"
}
```

### All 32 field_ids — RIASEC affinity vectors

| field_id | R | I | A | S | E | C |
|---|---|---|---|---|---|---|
| architecture | 6 | 5 | 9 | 3 | 4 | 6 |
| artificial_intelligence | 3 | 9 | 5 | 2 | 3 | 7 |
| automotive_engineering | 9 | 6 | 2 | 2 | 3 | 5 |
| biomedical_engineering | 6 | 8 | 3 | 5 | 3 | 5 |
| business_bba | 2 | 5 | 3 | 5 | 9 | 7 |
| chemical_engineering | 7 | 8 | 2 | 2 | 3 | 6 |
| chemistry_biochemistry | 4 | 9 | 3 | 3 | 2 | 7 |
| civil_engineering | 9 | 6 | 2 | 3 | 3 | 7 |
| computer_science | 4 | 9 | 3 | 2 | 3 | 8 |
| construction_engineering | 8 | 5 | 2 | 3 | 4 | 7 |
| cybersecurity | 5 | 9 | 2 | 4 | 5 | 8 |
| data_science | 2 | 9 | 3 | 2 | 3 | 8 |
| digital_media | 3 | 5 | 9 | 4 | 6 | 3 |
| economics | 2 | 8 | 3 | 4 | 6 | 7 |
| electrical_engineering | 8 | 8 | 2 | 2 | 3 | 6 |
| electronics_engineering | 8 | 7 | 2 | 2 | 3 | 6 |
| english_linguistics | 1 | 6 | 8 | 6 | 4 | 4 |
| finance_accounting | 2 | 7 | 2 | 3 | 6 | 9 |
| food_engineering | 6 | 6 | 3 | 4 | 3 | 6 |
| industrial_manufacturing_engineering | 8 | 5 | 2 | 2 | 4 | 7 |
| materials_engineering | 7 | 7 | 2 | 2 | 2 | 6 |
| mechanical_engineering | 9 | 7 | 2 | 2 | 3 | 5 |
| metallurgical_engineering | 7 | 7 | 1 | 2 | 2 | 6 |
| petroleum_engineering | 7 | 7 | 2 | 2 | 4 | 5 |
| physics | 3 | 9 | 4 | 2 | 2 | 7 |
| polymer_petrochemical_engineering | 6 | 7 | 2 | 2 | 3 | 6 |
| social_work | 2 | 4 | 4 | 10 | 5 | 3 |
| software_engineering | 4 | 8 | 4 | 2 | 3 | 7 |
| telecommunications_engineering | 7 | 8 | 2 | 2 | 3 | 6 |
| textile_engineering | 6 | 5 | 4 | 2 | 3 | 6 |
| textile_sciences | 5 | 4 | 6 | 3 | 3 | 6 |
| urban_infrastructure_engineering | 7 | 5 | 3 | 4 | 4 | 7 |

### Assumptions about fixture vs real schema

The fixture includes all required fields per Point 4 schema. The following fields use placeholder values (not real data):
- `pakistan_now.job_postings_monthly = 500` (uniform placeholder)
- `pakistan_now.yoy_growth_rate = 0.15` (uniform placeholder)
- `world_now.*_yoy_growth_rate` fields (uniform placeholder)
- `world_future.us_bls_4yr_projected_growth = 0.10` (uniform placeholder)
- All `lag_parameters` fields (placeholders)

**Critical:** `computed.future_value` values are realistic (not uniform). They are the only values ScoringNode reads from lag_model at runtime. All other fields are structurally valid but contain placeholder values — the fixture will pass Point 4 schema validation for structure but not for data quality.

---

## ASSUMPTIONS

1. **`effective_grade_used` includes 0-mark subjects.** Subject marks with value 0 (e.g. `biology=0` for a Pre-Engineering student) are included in `effective_marks` and capability blend is applied if the gap is ≥25. This is what the spec text implies (iterate over all `subject_marks.items()`). No explicit exception for 0-mark subjects is documented in Point 2. **Verify with Architecture Chat:** should biology=0 be excluded from capability blend the same way calculate_aggregate excludes 0-mark subjects from the aggregate calculation?

2. **Thought trace appended per-degree even when missing field_id.** A warning entry is appended to thought_trace when field_id not found, followed by a regular scoring entry. Both entries use the same degree_label. This is consistent with the "append only" rule but doubles the trace entries for that degree.

3. **`aggregate_formula` used for capability blend is from the roadmap entry.** FilterNode adds `aggregate_formula` to each roadmap entry. ScoringNode reads `degree["aggregate_formula"]` to call `calculate_aggregate(effective_marks, ...)`. This is correct per spec but means the aggregate formula used in the capability-blend context is the same formula FilterNode used for merit estimation. This is the intended design.

4. **Mismatch preference matching is substring.** `pref.lower() in d["degree_name"].lower()` — a stated preference of "Computer Science" matches "BS Computer Science". If a student states "Engineering" it would match ALL engineering degrees. The spec uses this exact pattern (Point 2 Section 8) so this is correct, but it means broad preferences may match many degrees and only the first (highest-scoring after sort) is used. This is the intended behaviour per "pref_entries[0]".

5. **`calculate_aggregate` used with `effective_marks` (not `subject_marks`).** The function is imported from filter_node and used with the blended effective_marks dict. Note that `calculate_aggregate` skips 0-value marks. If capability blend converts a 0-mark subject to a non-zero effective value (e.g. biology=0 blended to 10), that blended value will be included in the aggregate. Assumption #1 applies here.

---

## Known Failure Modes

- `scoring_node.py:29` — `_load_affinity_matrix()`: If `DATA_DIR / "affinity_matrix.json"` doesn't exist, raises `FileNotFoundError` without handling. Current behaviour: exception propagates and crashes the node. This is acceptable for Sprint 3 since data files are expected to exist. Sprint 4 error handling should wrap this.
- `scoring_node.py:36` — `_load_lag_model()`: Same as above for `lag_model.json`.
- `scoring_node.py:97` — `settings.SCORING_WEIGHTS[student_mode]`: If `student_mode` has an unexpected value (not "inter" or "matric_planning"), raises `KeyError`. FilterNode and session setup guarantee this won't happen in normal flow.

---

## Issues Noticed (not fixed)

- `backend/tests/test_filter_node.py` has a stale fee comment (`60475 → 64475`) noted in the previous session log (2026-04-18-12-00). Still present — flag for Waqas.

---

## What Architecture Chat Should Review

1. **Assumption #1 (0-mark subject blend):** Should `biology=0` be excluded from capability blend the same way `calculate_aggregate` excludes 0-mark subjects? The current implementation applies blend to all subjects in `subject_marks` regardless of whether the mark is 0. If the answer is "yes, exclude", a one-line guard is needed: `if reported_grade == 0: effective_marks[subject] = 0; continue`.

2. **`aggregate` not actually used in ScoringNode total_score.** The capability blend computes `effective_marks` and then `calculate_aggregate(effective_marks, aggregate_formula)` — but the resulting `aggregate` value is not used in the `total_score` formula (which only uses `match_score_normalised` and `future_score`). The spec's capability blend section says "effective_marks passed to calculate_aggregate() — dict[str, float], not a single float". ScoringNode computes the aggregate to produce `effective_grade_used` but does not feed it into `total_score`. This matches the spec (total_score only uses RIASEC match and FutureValue). Confirm this is the intended design — the blend affects merit display but not the scoring rank.

3. **Mismatch detection for `pref_future_value` when field_id missing.** If a stated preference matches a degree whose `field_id` is not in `lag_model`, `pref_future_value` defaults to 5.0. Since 5.0 < 6.0, a mismatch could trigger based on score gap alone even though we have no real FutureValue data. Is 5.0 the right neutral value here, or should the mismatch check be skipped entirely for unknown field_ids?

---

## Architecture Chat Review Fix — 2026-04-18

Two fixes applied to `backend/app/agents/nodes/scoring_node.py` only.
No other files changed. 18/18 tests still pass.

### Fix 1 — Exclude 0-mark subjects from capability blend

**Location:** capability blend loop, after `if capability is None: continue`.

**Change added:**
```python
if reported_grade == 0:
    effective_marks[subject] = 0
    continue
```

**Rationale:** A subject mark of 0 means "not taken" (e.g. biology=0 for a
Pre-Engineering student). Blending 0 against a capability score produced a
misleading non-zero effective mark. `calculate_aggregate` already skips
0-mark subjects — the blend now matches that behaviour. Inconsistency
eliminated. The 0 is written to `effective_marks` so the subject still
appears in `effective_grade_used` (no missing key), but the value stays 0.

### Fix 2 — Skip mismatch check for unknown field_ids

**Location:** mismatch detection block, `else` branch of `if pref_field_id in lag_model`.

**Change:** replaced `pref_future_value = 5.0` with `continue`.

**Rationale:** The mismatch notice cites a specific FutureValue to the
student. A placeholder 5.0 default could trigger a notice with a fabricated
market outlook figure. Since 5.0 < 6.0 (the ceiling), any large enough
score gap would have triggered a misleading notice for an unknown field_id.
Skipping entirely is safer — no notice is better than a notice with bad data.

### Test results

```
pytest tests/test_scoring_node.py -v
18 passed in 1.29s
```

All 18 tests pass. The existing `test_missing_field_id_fallback` test
verified the degree still appears in output with neutral scoring defaults —
that behaviour is unchanged. The mismatch skip only affects the detection
loop, not degree scoring or sorting.

---

## Fix — Independent OR-branch fallback — 2026-04-24

**Triggered by:** Opus pre-demo gate check Session 2 (2026-04-24) — latent CONCERN
(scoring fallback OR branch discards real data when one source is missing).

### Lines changed

`backend/app/agents/nodes/scoring_node.py` — lines 119–154 (post-fix line numbers).
No test files changed. No other files changed.

### Before

```python
# ── RIASEC match score + FutureValue ──────────────────────────────
if field_id not in affinity_matrix or field_id not in lag_model:
    match_score_normalised = 0.5
    future_score = 5.0
else:
    riasec_affinity = affinity_matrix[field_id]["riasec_affinity"]
    degree_vector = [
        riasec_affinity.get(dim, 1) for dim in ("R", "I", "A", "S", "E", "C")
    ]
    raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
    match_score_normalised = (
        raw_match / theoretical_max if theoretical_max > 0 else 0.0
    )
    future_score = float(lag_model[field_id]["computed"]["future_value"])
```

### After

```python
# ── RIASEC match score ────────────────────────────────────────────
if field_id in affinity_matrix:
    riasec_affinity = affinity_matrix[field_id]["riasec_affinity"]
    degree_vector = [
        riasec_affinity.get(dim, 1) for dim in ("R", "I", "A", "S", "E", "C")
    ]
    raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
    match_score_normalised = (
        raw_match / theoretical_max if theoretical_max > 0 else 0.0
    )
else:
    logger.warning(
        "%s — field_id %s not in affinity_matrix. Using default match=0.5.",
        degree_label, field_id,
    )
    state["thought_trace"].append(
        f"{degree_label} — field_id {field_id} not in affinity_matrix. "
        "match_score_normalised defaulted to 0.5."
    )
    match_score_normalised = 0.5

# ── FutureValue ───────────────────────────────────────────────────
if field_id in lag_model:
    future_score = float(lag_model[field_id]["computed"]["future_value"])
else:
    logger.warning(
        "%s — field_id %s not in lag_model. Using default future_score=5.0.",
        degree_label, field_id,
    )
    state["thought_trace"].append(
        f"{degree_label} — field_id {field_id} not in lag_model. "
        "future_score defaulted to 5.0."
    )
    future_score = 5.0
```

### Why

The OR-branch coupled two independent data sources into one condition. When
`affinity_matrix.json` was empty (as it is pre-Fazal population) but
`lag_model.json` was fully populated, the `or` short-circuited on the first
missing source and discarded the real `future_value` from lag_model, replacing
it with the neutral 5.0 default. The inverse was also true: a missing lag_model
entry discarded the real RIASEC match and forced 0.5. The Opus audit identified
this as the mechanism collapsing `total_score` to a constant 0.5×0.6 + 0.5×0.4
= 0.5 across all degrees when `affinity_matrix.json` was `[]`.

Two independent lookups with independent defaults fix this. Each source reads
what it can; a missing entry in one source never contaminates the other.

### Test result

```
pytest tests/test_scoring_node.py -v
18 passed in 1.65s

pytest tests/ -v -m "not slow"
62 passed, 3 deselected in 14.51s
```
