# claude-code-2026-05-09-00-00-filter-node-crash-fix.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: FilterNode crash fix — defensive coding for all 4 failure modes

---

## LangSmith Trace Analysis

**CLI status:** `langsmith-cli` is NOT installed in this environment.
`langsmith-cli` command not found (exit 127). Trace `019e0c6c-6ff9-74a3-921e-e349f18cdc4f`
must be retrieved manually from smith.langchain.com.

**Root cause identified via code inspection + direct execution instead:**

Ran `filter_node` directly against real `universities.json` data:

```
CRASH: TypeError: '>=' not supported between instances of 'float' and 'NoneType'
  File filter_node.py, line 348, in filter_node
    if aggregate >= cutoff_max:
```

---

## Root Cause Confirmed

**Active failure mode: Mode 4 (NEW — not in the three documented failure modes)**

- **Exception type:** `TypeError`
- **Exact line:** `filter_node.py:348` — `if aggregate >= cutoff_max:`
- **Trigger:** `iba_bs_economics_mathematics` and `iba_bs_economics_data_science`
  both have `cutoff_range: {"min": null, "max": null}` in universities.json.
  The dict key `cutoff_range` exists (no KeyError), but `cutoff_range["min"]`
  and `cutoff_range["max"]` are Python `None`. Comparing `float >= None` raises
  `TypeError` — not `KeyError`.
- **Context:** These two IBA degrees were set to null cutoffs because they have
  `policy_pending_verification: true` and no confirmed historical cutoff data.

**The three documented failure modes were NOT active in the current data:**
- Mode 1 (entry_test missing): All 5 universities have `entry_test` key present.
- Mode 2 (min_percentage_hssc missing): All degrees have this in eligibility.
- Mode 3 (eligibility_notes stream missing): All conditional streams have matching notes.

---

## Code Changes Made

### Fix 2 — min_percentage_hssc (Check 0) — defensive .get()

**File:** `backend/app/agents/nodes/filter_node.py`

**Before (line 206):**
```python
min_required = float(elig["min_percentage_hssc"])

if unadjusted_inter < min_required:
```

**After:**
```python
_min_hssc = elig.get("min_percentage_hssc")
min_required = float(_min_hssc) if _min_hssc is not None else None

if min_required is not None and unadjusted_inter < min_required:
```

Behavior: if `min_percentage_hssc` is absent, Check 0 is skipped entirely — degree is not hard-excluded. Correct: no floor means no legal disqualification.

---

### Fix 3 — eligibility_notes[stream] (Check 1) — defensive .get() + soft flag

**Before (lines 229-234):**
```python
if stream in elig["fully_eligible_streams"]:
    ...
elif stream in elig["conditionally_eligible_streams"]:
    eligibility_tier = "likely"
    # Direct access per Point 4 — data integrity enforced by validation Rule 5
    eligibility_note = elig["eligibility_notes"][stream]
...
    eligible_list = (
        elig["fully_eligible_streams"]
        + elig["conditionally_eligible_streams"]
    )
```

**After:**
```python
if stream in elig.get("fully_eligible_streams", []):
    ...
elif stream in elig.get("conditionally_eligible_streams", []):
    eligibility_tier = "likely"
    _notes = elig.get("eligibility_notes") or {}
    _note = _notes.get(stream)
    if _note is None:
        logger.warning(...)
        soft_flags.append({
            "type": "eligibility_contact_university",
            ...
        })
    else:
        eligibility_note = _note
...
    eligible_list = (
        elig.get("fully_eligible_streams", [])
        + elig.get("conditionally_eligible_streams", [])
    )
```

Behavior: if stream is in `conditionally_eligible_streams` but not in `eligibility_notes`, degree is included with `eligibility_tier="likely"` and `eligibility_contact_university` soft flag. Never crashes.

---

### Fix 1 — entry_test missing key (Check 3) — defensive .get()

**Before (line 344):**
```python
degree["entry_test"],
```

**After:**
```python
degree.get("entry_test") or {},
```

Behavior: if `entry_test` key is missing, passes empty dict to `calculate_estimated_merit()`. `entry_test.get(weight_key, 0.0)` already handles missing weight keys — so proxy_score becomes 0.0 and falls back to inter-only merit. No crash.

---

### Fix 4 (actual crash) — null cutoff_range min/max (Check 3) — None guard

**Before (lines 347-348):**
```python
aggregate = estimated_merit
cutoff_min: float = degree["cutoff_range"]["min"]
cutoff_max: float = degree["cutoff_range"]["max"]
...
if aggregate >= cutoff_max:
```

**After:**
```python
aggregate = estimated_merit
_cr = degree.get("cutoff_range") or {}
cutoff_min = _cr.get("min")
cutoff_max = _cr.get("max")
...
if cutoff_min is None or cutoff_max is None:
    logger.warning("%s: cutoff_range has null min/max — skipping merit comparison", degree_label)
    merit_tier = "likely"
    soft_flags.append({"type": "policy_unconfirmed", ...})
    trace_merit = "NO CUTOFF DATA (policy pending)"
else:
    cutoff_min = float(cutoff_min)
    cutoff_max = float(cutoff_max)
    # ... merit tier logic unchanged
```

Behavior: if cutoff_range is null or min/max are None, degree is included with `merit_tier="likely"` and `policy_unconfirmed` soft flag. Never crashes. `Check 3b` (entry test difficulty warning) remains outside this block and still fires correctly when `proxy_used=True`.

---

## Data Audit Findings (Task 3)

**Structural audit of non-NED universities run:**
- fast_nuces: 9 degrees — all keys present, all conditionally_eligible streams have notes
- uok: 10 degrees — all keys present
- iba: 9 degrees — all keys present (`cutoff_range` key exists, but min/max values are null for 2 degrees)
- dow: 5 degrees — all keys present

**Issues found:**
- `iba_bs_economics_mathematics`: `cutoff_range: {"min": null, "max": null}`, `policy_pending_verification: true`
- `iba_bs_economics_data_science`: `cutoff_range: {"min": null, "max": null}`, `policy_pending_verification: true`

**NOT data issues — code must handle them gracefully.** The null cutoff values are intentional (policy pending). These are now handled by Fix 4.

**No data file changes were made.** (HARD RULE: data fixes go to Data Chat.)

---

## New Tests Added (Task 4)

**File:** `backend/tests/test_filter_node.py`

Added imports: `copy`, `json`, `pathlib.Path`, `unittest.mock.patch`
Added helper: `_load_patched_universities()` — loads universities.json and applies structural patches to specific degrees for crash resilience testing.

| Test | What it covers |
|---|---|
| `test_missing_entry_test_does_not_crash` (Test A / Test 14) | Patches `neduet_bs_cs` to remove `entry_test` entirely. Verifies no exception, roadmap non-empty. |
| `test_missing_min_percentage_hssc_does_not_crash` (Test B / Test 15) | Patches `neduet_bs_cs` to remove `min_percentage_hssc`. Verifies no crash, degree still in results (not HEC-excluded). |
| `test_stream_in_conditional_not_in_notes_does_not_crash` (Test C / Test 16) | Patches `fast_nuces_bs_cs` to remove Pre-Medical key from `eligibility_notes`. Verifies no crash, `eligibility_contact_university` flag present, `eligibility_tier="likely"`. |
| `test_null_cutoff_range_does_not_crash` (Test D / Test 17) | Runs filter_node against real IBA data with null cutoff_range. Verifies no TypeError, `iba_bs_economics_mathematics` and `iba_bs_economics_data_science` in roadmap with `merit_tier="likely"` and `policy_unconfirmed` flag. |

---

## LangSmith Verification

**Before:** filter_node crashing with TypeError after 0.05s on every pipeline run that
includes IBA universities (all 5 universities loaded by default).

**After:** filter_node runs OK. Verified locally:
```
filter_node ran OK: 61 degrees in roadmap
```
Warning logs emitted for IBA degrees as expected (not errors):
```
IBA BS Economics & Mathematics: cutoff_range has null min/max — skipping merit comparison
IBA BS Economics & Data Science: cutoff_range has null min/max — skipping merit comparison
```

**LangSmith trace `019e0c6c-6ff9-74a3-921e-e349f18cdc4f`** must be confirmed
manually at smith.langchain.com after backend deployment.

---

## Test Results

```
pytest backend/tests/test_filter_node.py -v
17 passed in 0.64s

pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 6.59s
```

---

## Self-Review Checklist

1. filter_node.py: no direct dict access without .get() for keys that may be absent? **YES** — all 4 failure modes addressed.
2. filter_node.py: every exception path logs a warning and continues? **YES** — logger.warning() at each null/missing case.
3. filter_node.py: minimum display rule still fires correctly? **YES** — 61 degrees in roadmap for standard student, rule unchanged.
4. test_filter_node.py: all 13 original tests still pass? **YES** — 13/13 confirmed.
5. test_filter_node.py: at minimum 3 new crash resilience tests added and passing? **YES** — 4 new tests (14-17), all passing.
6. LangSmith: filter_node status shows "success"? **PENDING** — CLI not installed; requires manual verification after deploy.
7. Data audit report produced? **YES** — two IBA degrees with null cutoff_range documented; no data changes made.

---

## What Architecture Chat Should Review

1. **New soft flag type `eligibility_contact_university`** (from Fix 3): This flag type
   is NOT yet in ExplanationNode's `FLAG_DESCRIPTIONS` dict. Unknown flag types are
   silently skipped in ExplanationNode — the flag will never surface in the AI explanation.
   Needs a one-line addition to `explanation_node.py` in a follow-up session:
   ```python
   FLAG_DESCRIPTIONS["eligibility_contact_university"] = (
       "Eligibility for your stream needs direct confirmation with this university's admissions office."
   )
   ```

2. **IBA degrees with null cutoff_range**: The two IBA degrees now receive `merit_tier="likely"`
   with `policy_unconfirmed` flag. This is correct for policy-pending degrees. When IBA's
   cutoff data is confirmed, Fazal should update `universities.json` with real values — at that
   point the null-cutoff code path becomes dead code (but safe to leave).

3. **FAST NUCES entry_test subject weights**: FAST uses `adv_math_weight`, `basic_math_weight`,
   `iq_weight` — none of these match the `ENTRY_TEST_SUBJECT_MAP` keys (`math_weight`,
   `physics_weight`, etc.). So for FAST degrees, `proxy_score` is only driven by `english_weight`
   (the only matching key). This means FAST merit estimates undercount math/IQ components.
   Requires either: (a) adding FAST-specific keys to `ENTRY_TEST_SUBJECT_MAP` in config.py,
   or (b) adding a `subject_map_override` field to the entry_test structure in universities.json.
   This is a data/config decision for Architecture Chat — not a crash, but a silent accuracy issue.

---

## Files Modified

- `backend/app/agents/nodes/filter_node.py` — 4 defensive fixes
- `backend/tests/test_filter_node.py` — 4 new crash resilience tests + helper function + imports
