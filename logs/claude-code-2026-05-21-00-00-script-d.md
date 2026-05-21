# Session Log — Script D: Aggregate Job Counts into lag_model.json
**File:** `claude-code-2026-05-21-00-00-script-d.md`
**Date:** 2026-05-21
**Model:** Claude Sonnet 4.6
**Task:** Create `backend/scripts/aggregate_job_counts.py` — Script D that reads `linkedin_raw_jobs.json` + `job_title_mapping.json` (confirmed only) and writes `raw.monthly_postings_history` per field_id into `lag_model.json`.

---

## Pre-Implementation Findings — All 6 Points

### 1. lag_model.json first entry structure
Total entries: **51**

Top-level keys:
```
field_id, field_name, associated_degrees, lag_category, lifecycle_status,
risk_factor, risk_reasoning, outsourcing_applicable, infrastructure_constrained,
constraint_note, pakistan_now, world_now, world_future, pakistan_future,
lag_parameters, computed, employment_data, career_paths
```

`raw` key: **absent** from all entries (`d[0].get('raw')` returns `None` — key does not exist in any of the 51 entries).

`computed` block of first entry:
```json
{"future_value": 8.92, "last_computed": "2026-05"}
```

### 2. raw block status
`raw` key is absent from all 51 entries. `write_to_lag_model()` correctly initialises it to `{}` via:
```python
if "raw" not in entry or entry["raw"] is None:
    entry["raw"] = {}
```

### 3. computed.future_value
All 51 entries have non-null `future_value`. First entry: `8.92`. No STOP triggered.

### 4. job_title_mapping.json confirmed sample entry
```json
{
  "title": "Educational Counselor",
  "canonical_title": "educational_counselor",
  "primary_field_id": "education_bed",
  "secondary_field_ids": ["social_sciences"],
  "sub_specialisation": "student_advising",
  "confidence": "high",
  "unmapped": false,
  "llm_reasoning": "...",
  "count_in_dataset": 16
}
```
Schema keys: `title, canonical_title, primary_field_id, secondary_field_ids, sub_specialisation, confidence, unmapped, llm_reasoning, count_in_dataset`

`canonical_form` and `is_noise_variant` are **absent** — Script C v2 has not run on this data-branch file yet. Keys are **uppercase** ("Educational Counselor").

### 5. first_seen format and job count
```
2026-05-17 | Admin Manager - Lahore
2026-05-17 | Contact Centre Agent
2026-05-17 | Mobile Application Developer (Fresh)
Total jobs: 2653
```
`first_seen` format: `YYYY-MM-DD`. `[:7]` gives `YYYY-MM`. Total: **2653** (more than expected 1833 — new collections since last pull). No STOP triggered.

### 6. Mapping counts
```
Confirmed total: 1359
Unmapped (no field_id): 0
With primary_field_id: 1357
With secondary_field_ids: 938
Noise variants: 43
```

---

## Critical Deviation from Spec — load_mapping() Key Lowercasing

**Problem discovered:** Mapping keys are uppercase ("Educational Counselor") because Script C v2's `migrate_keys_to_lowercase()` has not run on this data-branch file. Script D's `aggregate_counts()` lowercases titles before lookup:
```python
title = " ".join(title.split()).lower()
entry = confirmed_mapping.get(title)
```
Without handling, this produces 0 matches for all 1359 confirmed entries.

**Fix applied in `load_mapping()`:**
```python
confirmed = {k.lower(): v for k, v in confirmed.items()}
```
One line addition. Makes Script D robust against both Script C v1 (uppercase keys) and Script C v2 (lowercase keys) mapping files. Documented here for Architecture Chat awareness.

---

## Aggregation Result

```
Jobs counted (primary credit):    1817
Secondary credits applied:        1359
Skipped — no title:               0
Skipped — not in confirmed:       834
Skipped — unmapped role:          0
Field_ids with at least one count: 49
```

**Total job credits distributed: 2496.5**

834 jobs skipped (not in confirmed) — these are titles that Script C has not yet mapped (needs_review titles or titles added after the last Script C run).

No WARN entries — all 49 field_ids with counts are present in lag_model.json.

---

## Top 5 Fields by Total Job Credits

| field_id | total credits | future_value |
|---|---|---|
| business_bba | 907.5 | 0.81 |
| software_engineering | 296.0 | 8.92 |
| computer_science | 187.0 | 8.92 |
| finance_accounting | 160.0 | 0.81 |
| mass_communication | 151.5 | 1.35 |

---

## Entries with No Data

Two field_ids received no job credits and got `monthly_postings_history: {}`:
- `polymer_petrochemical_engineering` (future_value=0.57)
- `physical_therapy` (future_value=1.35)

Both are niche fields with low LinkedIn presence — expected and not a failure.

---

## future_value Preservation

Confirmed unchanged. Spot-check:
- `computer_science`: 8.92 (unchanged from pre-run check)
- `artificial_intelligence`: 10.0
- `software_engineering`: 8.92

`computed` block was never touched by Script D — only `raw.monthly_postings_history` was written.

---

## Quick Test Output

```
=== Script D output verification ===

Entries with postings data: 49
Entries with no data:       2

Top 10 fields by total job credits:
  business_bba                               907.5 credits | 1 month(s) | future_value=0.81
  software_engineering                       296.0 credits | 1 month(s) | future_value=8.92
  computer_science                           187.0 credits | 1 month(s) | future_value=8.92
  finance_accounting                         160.0 credits | 1 month(s) | future_value=0.81
  mass_communication                         151.5 credits | 1 month(s) | future_value=1.35
  digital_media                               80.0 credits | 1 month(s) | future_value=0.77
  business_analytics                          74.0 credits | 1 month(s) | future_value=6.42
  data_science                                56.5 credits | 1 month(s) | future_value=9.5
  artificial_intelligence                     45.0 credits | 1 month(s) | future_value=10.0
  education_bed                               43.0 credits | 1 month(s) | future_value=0.27

Fields with no data:
  polymer_petrochemical_engineering        future_value=0.57
  physical_therapy                         future_value=1.35

Spot-check sub_specialisation breakdown:
  computer_science: future_value=8.92
    2026-05: total=187.0
      mobile_development: 5.0
      systems_architecture: 0.5
      qa_testing: 13.5
  artificial_intelligence: future_value=10.0
    2026-05: total=45.0
      business_development: 0.5
      cloud_ml_engineering: 0.5
      ml_engineering: 20.0
  software_engineering: future_value=8.92
    2026-05: total=296.0
      mobile_development: 11.0
      project_management: 28.5
      design: 0.5
```

All expected conditions met:
- 49 entries with data, 2 empty ✓
- future_value values unchanged ✓
- by_specialisation populated correctly ✓
- No null values — empty fields get `{}` ✓

---

## Schema Change Note

Script D adds a new `raw` key to each of the 51 lag_model entries where it did not previously exist. All 51 entries had `raw` absent (key not present). Script D initialised `raw = {}` for all 51 and then set `raw["monthly_postings_history"]` to the computed dict (49 entries) or `{}` (2 entries).

**For Architecture Chat:** `compute_future_values.py` reads from root-level keys (`pakistan_now`, `world_now`, etc.) not from under `raw`. It is unaffected by this addition. The `raw` block is a new organisational grouping for LinkedIn-derived live data.

---

## Self-Review Checklist — All 23 Items

1.  ✓ Script at `backend/scripts/` not root
2.  ✓ Reads `RAW_JOBS_FILE` from `backend/data/`
3.  ✓ Reads `MAPPING_FILE` from `backend/data/`
4.  ✓ Reads and writes `LAG_MODEL_FILE` from `backend/app/data/`
5.  ✓ Only confirmed section used — needs_review never touched
6.  ✓ `unmapped=true` entries skipped entirely
7.  ✓ Title lookup lowercased before lookup — matches Script C v2 normalisation (+ robustness fix for v1 uppercase keys)
8.  ✓ primary_field_id: +1.0 per job
9.  ✓ Each secondary_field_id: +0.5 per job
10. ✓ sub_specialisation tracked per month per field
11. ✓ sub_specialisation null stored as string "null" in by_specialisation dict
12. ✓ month_key extracted as `first_seen[:7]` giving YYYY-MM format
13. ✓ field_ids in counts but NOT in lag_model: logged as WARN and skipped (none triggered this run)
14. ✓ field_ids in lag_model with zero counts: get `{}` not null for monthly_postings_history
15. ✓ raw block initialised to `{}` if missing or null
16. ✓ computed block never modified
17. ✓ future_value never modified
18. ✓ Atomic write used for lag_model.json (.tmp then replace)
19. ✓ Script exits sys.exit(1) if any required file is missing
20. ✓ No external libraries — stdlib only (`json, pathlib, sys, datetime, collections`)
21. ✓ No project module imports
22. ✓ Log written to `logs/` at repo root
23. ✓ Quick test run and output matches expectations

---

## Algorithm Reconstruction Material

### Function signatures
```python
def load_raw_jobs(log_func) -> dict
def load_mapping(log_func) -> dict        # keys lowercased on return
def load_lag_model(log_func) -> list
def aggregate_counts(raw_jobs, confirmed_mapping, log_func) -> dict
def write_to_lag_model(lag_model, counts, log_func) -> list
def save_lag_model(lag_model, log_func)
```

### Core logic of aggregate_counts()
For each job in raw_jobs:
1. Get title → normalize: `" ".join(title.split()).lower()`
2. Look up normalized title in confirmed_mapping
3. If not found → `skipped_not_mapped += 1`, continue
4. If `unmapped=True` → `skipped_unmapped += 1`, continue
5. Extract `month_key = first_seen[:7]` (YYYY-MM)
6. Get `sub_spec = entry.get("sub_specialisation") or "null"`
7. Primary: `counts[primary][month_key]["total"] += 1.0` + `by_specialisation[sub_spec] += 1.0`
8. Each secondary: `counts[sec][month_key]["total"] += 0.5` + `by_specialisation[sub_spec] += 0.5`

Result dict structure: `{field_id: {YYYY-MM: {"total": float, "by_specialisation": {str: float}}}}`
defaultdicts converted to plain dicts at end, sorted by month.

### Concrete input/output example
Input job:
```json
{"title": "Software Engineer", "first_seen": "2026-05-17", "company": "Systems Ltd"}
```
Mapping lookup: `"software engineer"` → `{primary_field_id: "software_engineering", secondary_field_ids: ["computer_science"], sub_specialisation: "backend_development"}`

Output contribution:
- `counts["software_engineering"]["2026-05"]["total"] += 1.0`
- `counts["software_engineering"]["2026-05"]["by_specialisation"]["backend_development"] += 1.0`
- `counts["computer_science"]["2026-05"]["total"] += 0.5`
- `counts["computer_science"]["2026-05"]["by_specialisation"]["backend_development"] += 0.5`

### Edge cases handled
| Case | Handling |
|---|---|
| Job with no title | `skipped_no_title`, continue |
| Job with no `first_seen` | `skipped_no_title`, continue |
| Invalid `first_seen` type | WARN log + `skipped_no_title`, continue |
| Title not in confirmed | `skipped_not_mapped`, continue |
| `unmapped=true` entry | `skipped_unmapped`, continue |
| `primary_field_id` is None | No primary credit applied |
| Empty `secondary_field_ids` | No secondary credits |
| null `sub_specialisation` | Stored as string `"null"` |
| field_id in counts but not in lag_model | WARN log, skipped |
| field_id in lag_model with 0 counts | `monthly_postings_history = {}` |
| `raw` block absent from lag_model entry | Initialised to `{}` |
| Uppercase mapping keys (Script C v1) | Lowercased in `load_mapping()` |

### Constants
No numeric constants beyond the counting weights:
- Primary credit: `1.0`
- Secondary credit: `0.5`
- null sub_spec string: `"null"`

### Failures observed
None. Script ran cleanly with 0 WARN entries.

### What is NOT implemented
- Does NOT recalculate `computed.future_value` — that is `compute_future_values.py`'s job
- Does NOT touch `pakistan_now.job_postings_monthly` — that is a separate stub field
- Does NOT create new lag_model entries for unknown field_ids
- Does NOT filter by date range — all jobs in the file are counted
- Does NOT deduplicate jobs — each job_id counted once

---

## Files Created / Modified

| File | Action |
|---|---|
| `backend/scripts/aggregate_job_counts.py` | Created — Script D |
| `backend/app/data/lag_model.json` | Modified — `raw.monthly_postings_history` added to all 51 entries |
| `logs/claude-code-2026-05-21-00-00-script-d.md` | Created — this session log |

## Files NOT Modified
- `backend/data/linkedin_raw_jobs.json` ✓
- `backend/data/job_title_mapping.json` ✓
- `backend/app/data/affinity_matrix.json` ✓
- No node file or API file modified ✓
- computed block / future_value values unchanged ✓
