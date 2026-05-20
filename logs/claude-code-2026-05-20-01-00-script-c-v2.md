# Session Log — Script C v2: Noise Dedup, Lowercase Normalisation, Anchor/Memory System
**File:** `claude-code-2026-05-20-01-00-script-c-v2.md`
**Date:** 2026-05-20
**Model:** Claude Sonnet 4.6
**Task:** Modify `backend/scripts/map_job_titles.py` — Script C v2 with three gap fixes: FORCE_REMAP_NEEDS_REVIEW flag, lowercase title normalisation, and context-augmented prompt with canonical_form/is_noise_variant schema fields, anchor list, and memory index.

---

## Pre-Implementation Findings — All 9 Points

### 1. Current BATCH_SIZE value
`20` — CHANGE 2 (→15) required.

### 2. Rules in GEMINI_SYSTEM_PROMPT — 13 rules
```
RULE 1  — Title alone is insufficient. Use company + industry context.
RULE 2  — CS vs SE: these are DISTINCT fields in Pakistan.
RULE 3  — Multi-role titles: split proportionally.
RULE 4  — Pakistani title conventions.
RULE 5  — Data/Analytics cluster disambiguation.
RULE 6  — Engineering cluster disambiguation.
RULE 7  — Business cluster disambiguation.
RULE 8  — Health sciences disambiguation.
RULE 9  — Civil/Construction cluster.
RULE 10 — Chemical/Material/Textile cluster.
RULE 11 — Urdu/Mixed titles.
RULE 12 — Unmapped roles.
RULE 13 — Sub-specialisation guidance.
```

### 3. call_gemini() signature (line 374)
```python
def call_gemini(client, batch_titles, system_prompt, log_func):
```

### 4. find_new_titles() skip logic (lines 518–522)
```python
all_mapped = (
    set(existing_mapping.get("confirmed", {}).keys()) |
    set(existing_mapping.get("needs_review", {}).keys())
)
return [t for t in title_items if t["title"] not in all_mapped]
```

### 5. extract_unique_titles() whitespace normalisation (line 82)
```python
title = " ".join(title.split())
```
No `.lower()` present — GAP 2 confirmed.

### 6. format() call location (line 624)
```python
system_prompt = GEMINI_SYSTEM_PROMPT.format(field_id_block=field_id_block)
```
Single-placeholder — this line is REMOVED and replaced by CHANGE 11.

### 7. Schema keys (from confirmed entry)
```
['title', 'canonical_title', 'primary_field_id', 'secondary_field_ids',
 'sub_specialisation', 'confidence', 'unmapped', 'llm_reasoning', 'count_in_dataset']
```
`canonical_form` and `is_noise_variant` absent — confirmed safe to add.

### 8. Python check output
```
Confirmed: 1082
Needs review: 448
Entries with canonical_form: 0
Current schema keys: ['title', 'canonical_title', 'primary_field_id',
  'secondary_field_ids', 'sub_specialisation', 'confidence', 'unmapped',
  'llm_reasoning', 'count_in_dataset']
```

### 9. Python check output (title casing)
```
Total jobs: 1833
Titles with uppercase chars: 1832
Sample titles:
  'Admin Manager - Lahore'
  'Contact Centre Agent'
  'Mobile Application Developer (Fresh)'
  'Project Coordinator'
  'Project Coordinator'
```
1832 of 1833 titles have uppercase characters — lowercase normalisation is necessary.

---

## Change-by-Change Summary

### CHANGE 1 — FORCE_REMAP_NEEDS_REVIEW constant
Added after RETRY_WAIT, before HARDCODED_ANCHORS:
```python
FORCE_REMAP_NEEDS_REVIEW = False
```
Default is False — never committed as True.

### CHANGE 2 — BATCH_SIZE 20 → 15
```python
# Before:
BATCH_SIZE = 20

# After:
BATCH_SIZE = 15
```
Reduced because each batch now includes anchor block and memory index in the user message.

### CHANGE 3 — HARDCODED_ANCHORS constant
Added after FORCE_REMAP_NEEDS_REVIEW, 56 entries covering:
Software Development (12), Data and AI (8), QA and DevOps (5),
Management and Business (10), Finance and Accounting (4),
Engineering non-software (7), Design and Media (6),
Healthcare and Sciences (3), Education (1).
`process_engineer`, `lecturer`, `research_associate` deliberately excluded.

### CHANGE 4 — Lowercase normalisation in extract_unique_titles()
```python
# Before:
title = " ".join(title.split())

# After:
title = " ".join(title.split()).lower()
```
Ensures "Software Engineer" and "software engineer" are treated as one title.

### CHANGE 5 — migrate_keys_to_lowercase() function
Added after `load_existing_mapping()`, before `find_new_titles()`.
- Iterates both sections, lowercases all dict keys
- Entry content (including the "title" display field) unchanged
- Idempotent — safe to call on already-migrated data
- Called in main() immediately after `load_existing_mapping()`, before `find_new_titles()`

### CHANGE 6 — find_new_titles() respects FORCE_REMAP_NEEDS_REVIEW
```python
# Before:
all_mapped = (
    set(existing_mapping.get("confirmed", {}).keys()) |
    set(existing_mapping.get("needs_review", {}).keys())
)
return [t for t in title_items if t["title"] not in all_mapped]

# After:
already_confirmed = set(existing_mapping.get("confirmed", {}).keys())
already_review = set(existing_mapping.get("needs_review", {}).keys())

if FORCE_REMAP_NEEDS_REVIEW:
    skip_set = already_confirmed
else:
    skip_set = already_confirmed | already_review

new_titles = [t for t in title_items if t["title"] not in skip_set]

if FORCE_REMAP_NEEDS_REVIEW:
    remap_count = len([t for t in title_items if t["title"] in already_review])
    return new_titles, remap_count

return new_titles, 0
```
Now returns a tuple `(new_titles, remap_count)` — callers updated accordingly.

### CHANGE 7 — compute_dynamic_anchors() function
Added after `migrate_keys_to_lowercase()`.
- threshold=5 (at least 5 distinct noise variants must cite a canonical_form)
- Only eligible if entry has `is_noise_variant=False`, `confidence="high"`, `primary_field_id` not null
- On first run: returns empty set (no entries have canonical_form yet) — correct and expected

### CHANGE 8 — build_memory_index() function
Added after `compute_dynamic_anchors()`.
- Collects all unique `canonical_form` values from confirmed entries
- Filters: `is_noise_variant=False`, not already in effective_anchors, `primary_field_id` not null
- On first run: returns empty list — correct and expected

### CHANGE 9 — GEMINI_SYSTEM_PROMPT updates

**ADDITION A — Two new schema fields:**
```json
"canonical_form": "snake_case base title this maps to",
"is_noise_variant": false,
```
Added between `"unmapped"` and `"llm_reasoning"` fields.

Two new rules added to the schema Rules block:
- `canonical_form`: base title with noise stripped, snake_case; equals canonical_title when already canonical
- `is_noise_variant`: true only when primary_field_id, secondary_field_ids, and sub_specialisation are all identical to canonical_form entry, AND the only difference is location/company/seniority/metadata noise

**ADDITION B — Rule 14 added at end of disambiguation rules:**
`### RULE 14 — Canonical form and noise variant detection`
Includes `{anchor_block}` and `{memory_block}` placeholders (single braces — actual format placeholders).
Includes NOISE/NOT-NOISE categorised lists.
Includes 7 concrete EXAMPLES (frontend_engineer noise variant, react_developer not noise, senior SE AI/ML not noise, SE-Karachi noise, SQA→qa_engineer noise, Django Developer not noise, frontend-Karachi-Remote noise).

### CHANGE 10 — call_gemini() signature and user message

**Before:**
```python
def call_gemini(client, batch_titles, system_prompt, log_func):
    user_message = "Map the following job titles:\n\n"
    for i, item in enumerate(batch_titles, 1):
        ...
```

**After:**
```python
def call_gemini(client, batch, system_prompt, anchor_block, memory_block, log_func):
    anchor_section = ("ANCHOR TITLES...\n" + anchor_block + "\n\n") if anchor_block else ""
    memory_section = ("MEMORY...\n" + memory_block + "\n\n") if memory_block else ""
    user_message = (
        anchor_section + memory_section
        + "Map these job titles:\n\n"
        + json.dumps(batch, indent=2)
    )
```
`system_prompt` used directly in `system_instruction` — no `.format()` call inside `call_gemini()`.
Note: corrected `if memory_section else ""` bug in prompt spec (self-referential) to `if memory_block else ""`.

### CHANGE 11 — main() orchestration

**Removed:** single-placeholder format() call:
```python
system_prompt = GEMINI_SYSTEM_PROMPT.format(field_id_block=field_id_block)
```

**Added after field_id_block computation:**
```python
dynamic_anchors = compute_dynamic_anchors(mapping["confirmed"], threshold=5)
effective_anchors = HARDCODED_ANCHORS | dynamic_anchors
...
memory_titles = build_memory_index(mapping["confirmed"], effective_anchors)
...
anchor_block = "\n".join(sorted(effective_anchors))
memory_block = "\n".join(memory_titles)

# Single format() call — all three placeholders filled
system_prompt = GEMINI_SYSTEM_PROMPT.format(
    field_id_block=field_id_block,
    anchor_block=anchor_block,
    memory_block=memory_block,
)
```

**call_gemini() call site updated:**
```python
# Before:
results = call_gemini(client, batch, system_prompt, log_func)

# After:
results = call_gemini(
    client, batch, system_prompt,
    anchor_block, memory_block, log_func
)
```

**Migration call added before find_new_titles():**
```python
mapping = load_existing_mapping()
mapping = migrate_keys_to_lowercase(mapping, log_func)
save_mapping(mapping, log_func)
new_titles, remap_count = find_new_titles(title_items, mapping)
```

### CHANGE 12 — validate_mapping() schema additions
Added after existing `setdefault("llm_reasoning", "")`:
```python
result.setdefault("canonical_form", result.get("canonical_title", ""))
result.setdefault("is_noise_variant", False)
```

Added validation after secondary_field_ids validation:
```python
if not isinstance(result.get("is_noise_variant"), bool):
    result["is_noise_variant"] = False
    log_func(f"WARN | is_noise_variant not bool...")

if not result.get("canonical_form"):
    result["canonical_form"] = result.get("canonical_title", "")
```

---

## Migration Note

`migrate_keys_to_lowercase()` logic is correct and confirmed by code review.
It was NOT executed this session — this function only runs inside `main()`,
and the full script cannot be run during this session (quota preservation).

**Current state:** 1081 of 1082 confirmed keys have uppercase characters.
**Expected state after first Script C v2 run:** all keys lowercase.

The migration is idempotent — safe to run multiple times. No entry content
is changed, only dict keys.

**Document as:** "Migration logic correct — not yet executed. Will run on
first Script C v2 full run."

---

## Verification Output

### VERIFY 1 — Import and constants check
```
Import check PASS
BATCH_SIZE: 15
FORCE_REMAP_NEEDS_REVIEW: False
HARDCODED_ANCHORS count: 56
process_engineer in anchors: False
lecturer in anchors: False
```
PASS — all expected values confirmed.

### VERIFY 2 — Lowercase key check
```
Confirmed entries: 1082
Keys with uppercase: 1081
NOTE: Migration not yet executed —
migrate_keys_to_lowercase() runs inside
main() which requires a full script run.
This is expected during this session.
```
EXPECTED — uppercase keys present because migration has not run yet.
This is correct and acceptable per the prompt specification.

### VERIFY 3 — Schema fields check
```
Schema keys: ['title', 'canonical_title', 'primary_field_id', 'secondary_field_ids',
  'sub_specialisation', 'confidence', 'unmapped', 'llm_reasoning', 'count_in_dataset']
Entry intact — no content corrupted PASS
```
PASS — existing entries unchanged. `canonical_form` and `is_noise_variant` will
appear in entries after the next full Script C v2 run.

### VERIFY 4 — Anchor and memory index dry run
```
Hardcoded anchors: 56
Dynamic anchors promoted: 0
Effective anchors total: 56
Memory index size: 0
Dynamic: none — expected on first run
Dry run PASS
```
PASS — both 0 on first run because no existing entry has `canonical_form` yet.
Correct and expected. Both populate after the first full Script C v2 run.

### VERIFY 5 — Single format() call check
```
GEMINI_SYSTEM_PROMPT.format() calls: 1
Single format call PASS
system_prompt.format() calls: 0
No format in call_gemini PASS
```
PASS — critical constraint confirmed. Exactly one format() call in main(),
zero in call_gemini().

---

## Self-Review Checklist — All 34 Items

1.  ✓ `FORCE_REMAP_NEEDS_REVIEW = False` (default)
2.  ✓ `BATCH_SIZE = 15` (changed from 20)
3.  ✓ `HARDCODED_ANCHORS` defined at module level
4.  ✓ `HARDCODED_ANCHORS` contains 56 entries (~50 per spec, slightly more)
5.  ✓ `process_engineer` NOT in `HARDCODED_ANCHORS`
6.  ✓ `lecturer` NOT in `HARDCODED_ANCHORS`
7.  ✓ `research_associate` NOT in `HARDCODED_ANCHORS`
8.  ✓ `extract_unique_titles()` uses `.lower()` in normalisation
9.  ✓ `migrate_keys_to_lowercase()` defined after `load_existing_mapping()`
10. ✓ `migrate_keys_to_lowercase()` called in main() before `find_new_titles()`
11. ✓ `find_new_titles()` checks `FORCE_REMAP_NEEDS_REVIEW` and adjusts skip_set
12. ✓ When `FORCE_REMAP_NEEDS_REVIEW=True`, skip_set contains only `already_confirmed`
13. ✓ `compute_dynamic_anchors()` threshold=5
14. ✓ `compute_dynamic_anchors()` eligible_canonicals guard checks `is_noise_variant=False` AND `confidence="high"` AND `primary_field_id` not null
15. ✓ `compute_dynamic_anchors()` returns empty set when no entries have `canonical_form` (VERIFY 4: 0)
16. ✓ `build_memory_index()` filters `is_noise_variant=False`
17. ✓ `build_memory_index()` excludes `effective_anchors`
18. ✓ `build_memory_index()` returns empty list when no entries have `canonical_form` (VERIFY 4: 0)
19. ✓ `GEMINI_SYSTEM_PROMPT` output schema has `canonical_form` and `is_noise_variant` fields
20. ✓ Rule 14 added with `{anchor_block}` and `{memory_block}` placeholders
21. ✓ `call_gemini()` signature has `anchor_block` and `memory_block` parameters
22. ✓ `anchor_section` and `memory_section` prepended to `user_message` in `call_gemini()`
23. ✓ No `.format()` call on `system_prompt` inside `call_gemini()`
24. ✓ `system_instruction=system_prompt` used directly (already formatted)
25. ✓ Old single-placeholder format() call in main() REMOVED
26. ✓ New three-placeholder format() call fills `field_id_block`, `anchor_block`, `memory_block`
27. ✓ New format() call comes AFTER `anchor_block` and `memory_block` are computed
28. ✓ All `call_gemini()` call sites pass `anchor_block` and `memory_block` (one call site)
29. ✓ `validate_mapping()` sets defaults for `canonical_form` and `is_noise_variant`
30. ✓ `validate_mapping()` checks `is_noise_variant` is bool
31. ✓ All 5 verification commands run and results documented in this log
32. ✓ VERIFY 2 uppercase result documented as expected (migration not yet executed)
33. ✓ No project imports added (only `from collections import defaultdict` inside `compute_dynamic_anchors()`)
34. ✓ `REQUEST_DELAY`, `MAX_RETRIES`, `RETRY_WAIT`, `MODEL_NAME` all unchanged

---

## Architecture Note for Script D

Script C v2 produces two new fields in every mapping entry:
- `canonical_form` (str): snake_case base title this entry maps to.
  A noise variant's `canonical_form` points to its anchor (e.g. "frontend_engineer").
  A canonical entry's `canonical_form` equals its own `canonical_title`.
- `is_noise_variant` (bool): True when the title differs from its canonical_form
  only by location/company/seniority/metadata noise.

**Script D impact:**
- Script D looks up every raw job title against the mapping by key (lowercase title string).
  This lookup is unchanged — every title (noise variant or not) has its own entry in the
  mapping file, preserving full count data.
- When building sub_specialisation breakdown in `monthly_postings_history`, Script D can
  use `canonical_form` to group noise variants under their canonical concept rather than
  counting them as separate sub-types.
- `is_noise_variant=True` entries should contribute to the count of their `canonical_form`
  in sub_specialisation aggregation, not create new sub-categories.

**The memory index and dynamic anchor system become meaningful after the first full Script
C v2 run with `FORCE_REMAP_NEEDS_REVIEW=True`**, which will reprocess all 448 needs_review
entries with the improved prompt and schema. After that run, canonical_form and
is_noise_variant will be populated for all confirmed entries, enabling:
- Dynamic anchor promotion (5+ distinct noise variants → anchor eligible)
- Memory index with confirmed non-anchor canonical_forms
- Gemini can reference existing confirmed mappings when classifying new titles

---

## Files Modified

| File | Change |
|---|---|
| `backend/scripts/map_job_titles.py` | 12 changes (v2 upgrade) |
| `logs/claude-code-2026-05-20-01-00-script-c-v2.md` | This session log |

## Files NOT Modified

- `backend/app/data/affinity_matrix.json` ✓
- `backend/app/data/lag_model.json` ✓
- `backend/data/linkedin_raw_jobs.json` ✓
- `backend/data/job_title_mapping.json` ✓ (keys NOT yet lowercased — migration runs on next Script C v2 execution)
- No node file, API file, or data file modified ✓
- `FORCE_REMAP_NEEDS_REVIEW = False` in committed code ✓
- `REQUEST_DELAY`, `MAX_RETRIES`, `RETRY_WAIT`, `MODEL_NAME` unchanged ✓
- Existing entry field_id values not changed ✓
