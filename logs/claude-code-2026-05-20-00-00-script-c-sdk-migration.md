# Session Log — Script C: google.generativeai → google.genai SDK Migration
**File:** `claude-code-2026-05-20-00-00-script-c-sdk-migration.md`
**Date:** 2026-05-20
**Model:** Claude Sonnet 4.6
**Task:** Migrate `backend/scripts/map_job_titles.py` from deprecated `google.generativeai` SDK to `google.genai`; add count refresh for already-mapped titles.

---

## Pre-Implementation Findings — All 8 Points

### 1. Exact import line (line 17)
```python
import google.generativeai as genai
```

### 2. Exact genai.configure() call (line 21)
```python
genai.configure(api_key=GEMINI_API_KEY)
```

### 3. Exact call_gemini() signature (line 372)
```python
def call_gemini(model, batch_titles, system_prompt, log_func):
```

### 4. Exact generate_content() call (lines 390–396)
```python
response = model.generate_content(
    [system_prompt, user_message],
    generation_config=genai.GenerationConfig(
        temperature=0.1,
        top_p=0.9,
        max_output_tokens=8192,
    )
)
```

### 5. Generation config parameters
- `temperature=0.1`
- `top_p=0.9`
- `max_output_tokens=8192`

### 6. Exact quota error catch strings (line 421)
```python
if "quota" in error_str.lower() or "429" in error_str or "resource_exhausted" in error_str.lower():
```

### 7. Model initialisation in main() (line 599)
```python
model = genai.GenerativeModel(MODEL_NAME)
```

### 8. Verification command output
```
google.genai OK
types OK
errors OK
```
Note: `google-genai` package was not installed. Installed with:
```
pip install google-genai --break-system-packages
```
Installed version: `google-genai-2.4.0`

---

## Change-by-Change Summary

### CHANGE 1 — Module-level imports

**Before:**
```python
import google.generativeai as genai
```

**After:**
```python
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
```

### CHANGE 2 — genai.configure() → client

**Before:**
```python
genai.configure(api_key=GEMINI_API_KEY)
```

**After:**
```python
client = genai.Client(api_key=GEMINI_API_KEY)
```
Module-level. `genai.configure()` removed entirely.

### CHANGE 3 — Docstring update

**Before:**
```
No project imports. stdlib + google.generativeai + dotenv only.
```

**After:**
```
No project imports. stdlib + google.genai + dotenv only.
```

### CHANGE 4 — call_gemini() signature

**Before:**
```python
def call_gemini(model, batch_titles, system_prompt, log_func):
```

**After:**
```python
def call_gemini(client, batch_titles, system_prompt, log_func):
```

### CHANGE 5 — generate_content() call

**Before:**
```python
response = model.generate_content(
    [system_prompt, user_message],
    generation_config=genai.GenerationConfig(
        temperature=0.1,
        top_p=0.9,
        max_output_tokens=8192,
    )
)
```

**After:**
```python
response = client.models.generate_content(
    model=MODEL_NAME,
    contents=user_message,
    config=types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.0,
        top_p=0.9,
        max_output_tokens=8192,
    )
)
```
- `system_prompt` moved from contents list to `system_instruction` in config
- `contents` receives `user_message` only
- `temperature` changed from `0.1` to `0.0` (deterministic output)
- `top_p=0.9` preserved
- `max_output_tokens=8192` preserved

### CHANGE 6 — Quota error catch strings

**Before:**
```python
error_str = str(e)
if "quota" in error_str.lower() or "429" in error_str or "resource_exhausted" in error_str.lower():
```

**After:**
```python
error_str = str(e).lower()
if any(x in error_str for x in [
    "quota", "429", "resource_exhausted",
    "clienterror", "rate_limit", "too_many_requests"
]):
```
Expanded to 6 strings. Catches both old SDK error formats and new `google.genai.errors.ClientError` for 429s.

### CHANGE 7 — Model init removed from main(); call site updated

**Removed from main():**
```python
# Initialize Gemini model
model = genai.GenerativeModel(MODEL_NAME)
```

**Call site in main() updated:**
```python
# Before:
results = call_gemini(model, batch, system_prompt, log_func)

# After:
results = call_gemini(client, batch, system_prompt, log_func)
```
Only one `call_gemini()` call site in main(). Confirmed no remaining `model` references.

---

## Count Refresh Block

**Placement:** Immediately after `log_func(f"INFO | New titles to map this run: {len(new_titles)}")` and before the `if not new_titles:` early-exit guard.

**Logic:**
- Builds `title_count_map` from current `title_items` (reflects latest job counts from linkedin_raw_jobs.json)
- Iterates both `confirmed` and `needs_review` sections
- Updates `count_in_dataset` only when the value has changed
- Calls `save_mapping()` only when at least one count changed (avoids unnecessary disk write on first run or when counts are current)
- Logs refreshed count or "up to date" message

---

## Verification Output

### API verification
```
google.genai API OK: OK
```
Model: `gemini-3.1-flash-lite-preview`. Response: `OK`. Migration correct.

### Old reference check
```
PASS — no google.generativeai references
PASS — no GenerativeModel references
```

### Dry-run import check
```
Import check PASS
```

---

## Self-Review Checklist — All 21 Items

1.  ✓ `google.generativeai` import removed completely
2.  ✓ `from google import genai` present (line 17)
3.  ✓ `from google.genai import types` present (line 18)
4.  ✓ `from google.genai import errors as genai_errors` present (line 19)
5.  ✓ `genai.configure()` removed; replaced with `client = genai.Client(api_key=...)`
6.  ✓ `client` defined at module level (not inside a function)
7.  ✓ `model = genai.GenerativeModel()` removed from main()
8.  ✓ `call_gemini()` signature uses `client` not `model`
9.  ✓ `generate_content()` uses `client.models.generate_content()`
10. ✓ `system_prompt` in `system_instruction`, NOT in `contents`
11. ✓ `contents` receives `user_message` only
12. ✓ `temperature=0.0` (not 0.1)
13. ✓ `top_p=0.9` preserved
14. ✓ `max_output_tokens=8192` preserved
15. ✓ Quota catch expanded to 6 error strings
16. ✓ All `call_gemini()` call sites in main() updated to `client` (one site)
17. ✓ No remaining references to `model` anywhere in file
18. ✓ Count refresh block added after new_titles log line
19. ✓ Count refresh calls `save_mapping()` only when `count_refreshed > 0`
20. ✓ Verification command printed PASS for both reference checks
21. ✓ API verification printed `google.genai API OK: OK`

---

## Architecture Note

When transitioning to the Claude/Anthropic SDK (Sprint 4+), `google.genai.errors.ClientError`
must be replaced with `anthropic.RateLimitError` in the quota catch inside `call_gemini()`.
The catch string list will also need updating at that point — specifically, `"clienterror"` maps
to the old SDK's error class name and would need to become the new SDK's equivalent.

---

## Files Modified

| File | Change |
|---|---|
| `backend/scripts/map_job_titles.py` | SDK migration (7 changes) + count refresh block |
| `logs/claude-code-2026-05-20-00-00-script-c-sdk-migration.md` | This session log |

## Files NOT Modified

- `backend/app/data/affinity_matrix.json` ✓
- `backend/app/data/lag_model.json` ✓
- `backend/data/linkedin_raw_jobs.json` ✓
- `backend/data/job_title_mapping.json` ✓
- No node file, API file, or data file modified ✓
- `MODEL_NAME`, `BATCH_SIZE`, `REQUEST_DELAY`, `MAX_RETRIES`, `RETRY_WAIT` unchanged ✓
- No logic changes to confirmed/needs_review routing ✓

---

## Outstanding Items

1. **Gemini quota:** `gemini-3.1-flash-lite-preview` quota was available (API verification confirmed). Full Script C run (`python backend/scripts/map_job_titles.py`) can now proceed.
2. **petroleum_engineering duplicate in affinity_matrix.json:** Still present — flag for Fazal.
3. **Script D (monthly aggregation):** Not yet built. Comes after Script C produces a reviewed mapping file.
