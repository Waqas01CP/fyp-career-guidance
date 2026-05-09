# claude-code-2026-05-10-00-00-llm-retry-429.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: Gemini 429 retry — _invoke_with_retry() added to 3 LLM nodes

---

## Pre-Implementation Findings

### Sync/async confirmation
All three target nodes use **sync** `llm.invoke()` — not `llm.ainvoke()`. ✓

| Node | Call site count | LLM call type | Existing fallback |
|---|---|---|---|
| explanation_node.py | 1 (line 453) | sync `llm.invoke()` | `LLM_FAILURE_FALLBACK` module constant |
| answer_node.py | 5 (lines 156, 230, 284, 298, 356) | sync `llm.invoke()` | `LLM_FAILURE_FALLBACK` module constant |
| profiler.py | 1 (line 298) | sync `llm.invoke()` | Inline AIMessage fallback (lines 307-314) |

### google-api-core import
`from google.api_core.exceptions import ResourceExhausted` → **OK** ✓

### `time` module status
Not imported at module level in any of the three files.
Imported inside `_invoke_with_retry()` function body per HARD RULES. ✓

---

## _invoke_with_retry Implementation

Added identically to all three files. Local imports inside function body — no new module-level imports.

```python
def _invoke_with_retry(messages: list, max_retries: int = 3):
    from google.api_core.exceptions import ResourceExhausted
    import time
    for attempt in range(max_retries):
        try:
            return llm.invoke(messages)
        except ResourceExhausted:
            if attempt == max_retries - 1:
                raise
            wait_seconds = 30 * (attempt + 1)
            logger.warning("Gemini rate limit hit — retrying in %ds (attempt %d/%d)",
                           wait_seconds, attempt + 1, max_retries)
            time.sleep(wait_seconds)
        except Exception:
            raise
```

**Position in each file:**
- `explanation_node.py`: after `_scrub_pii()`, before `_build_entry_test_advice()`
- `answer_node.py`: after `LLM_FAILURE_FALLBACK` constant, before `_flatten_content()`
- `profiler.py`: after `_scrub_pii()`, before `check_profiling_complete()`

---

## All llm.invoke() Call Sites Replaced

### explanation_node.py (1 site)
- Line 453 (now ~483): `explanation_node()` try block → `_invoke_with_retry()`

### answer_node.py (5 sites — all confirmed)
1. `_extract_entity()` — used by both fee_query and market_query entity extraction
2. fee_query answer call — inside `if intent == "fee_query":` try block
3. market_query answer call — inside `elif intent == "market_query":` try block
4. out_of_scope — inside `elif intent == "out_of_scope":` try block
5. follow_up/clarification — inside `else:` try block

### profiler.py (1 site)
- `profiler_node()` try block → `_invoke_with_retry()`

**Verification:** Grep for `llm\.invoke\(` in the three target files shows only:
1. Inside `_invoke_with_retry()` docstring (text reference)
2. Inside `_invoke_with_retry()` itself: `return llm.invoke(messages)` (correct)
No direct calls remain in node functions. ✓

**supervisor.py untouched:** `llm.invoke()` at line 106 remains — expected. ✓

---

## Temporary Retry Test Result

```
PASSED
invoke call count: 3
sleep calls: [call(30), call(60)]
```

Two 429s followed by success → 3 invocations, sleep(30) + sleep(60) confirmed.
Test was run inline and NOT committed to any test file.

---

## Existing Test Results

```
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 1.89s
```

---

## Architecture Chat Notes

1. **Gemini → Claude/Anthropic model switch (Sprint 4):**
   When transitioning to Claude/Anthropic, `ResourceExhausted` (Google-specific)
   must be replaced with `anthropic.RateLimitError` or `anthropic.APIStatusError`.
   Each `_invoke_with_retry()` function in explanation_node, answer_node, and
   profiler will need updating. The structure of the retry loop stays the same —
   only the caught exception class changes.

2. **answer_node.py — all 5 call sites confirmed:**
   - `_extract_entity()` (1) — entity extraction for both fee and market queries
   - fee answer (1) — `if intent == "fee_query":`
   - market answer (1) — `elif intent == "market_query":`
   - out_of_scope (1) — `elif intent == "out_of_scope":`
   - follow_up/clarification (1) — `else:` branch

3. **Maximum wait on fee_query/market_query turns:**
   If both entity extraction AND the answer call hit sustained rate limiting,
   maximum wait ≈ 3 minutes (entity extraction: up to 90s + answer call: up to 90s).
   The student sees no SSE progress updates during this wait.
   Better than silent failure — but a mid-retry SSE status event (e.g.,
   `event: status / data: {"state": "retrying"}`) would improve UX.
   Consider for Sprint 4.
