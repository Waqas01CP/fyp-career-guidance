# Claude Code Session Log
**Date:** 2026-04-19 13:00
**Task:** Implement SupervisorNode production code — replace Sprint 1 stub with full LLM-based intent classifier
**Status:** COMPLETE

## Files Changed
- `backend/app/agents/nodes/supervisor.py` — replaced Sprint 1 stub with full implementation: module-level LLM init, Gemini 3.1 content list-flatten fix, VALID_INTENTS set, empty messages guard, invalid intent fallback, LLM failure fallback
- `backend/tests/test_supervisor_node.py` — new file, 7 unit tests (all mocked, no API calls)

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md` (v2.1)
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md` (Sections 4 and 5)
- `backend/app/agents/nodes/supervisor.py` (original stub)
- `backend/app/agents/nodes/profiler.py` (lines 1-30 and 190-220 for LLM init + flatten fix)
- `backend/app/agents/state.py`
- `backend/app/core/config.py`
- `backend/tests/test_profiler_node.py` (structure patterns)

## Phase 1 — Plan Summary
1. Extract latest message via `state["messages"][-1].content`; guard empty list → `"get_recommendation"` default
2. Format `SUPERVISOR_SYSTEM_PROMPT` with `user_input`; pass as SystemMessage + HumanMessage (Gemini 3.1 constraint)
3. Apply content list-flatten fix; `strip().lower()`; validate against `VALID_INTENTS`
4. Invalid intent → log warning → `"follow_up"` fallback
5. LLM failure → `logger.error()` → `"follow_up"` → return immediately
6. System prompt ~170 tokens (within 200–350 target)
7. 7 unit tests planned (all mocked)

Plan reviewed against Point 2 Section 4 line by line. No incoherencies found.

## Deviations from Plan

**Gemini 3.1 API constraint — call pattern change:**
Plan said "Pass the formatted prompt as a single SystemMessage to llm.invoke()." First LLM run failed with:
```
No content messages found. The Gemini API requires at least one non-system message
(HumanMessage, AIMessage, etc.) in addition to any SystemMessage.
```
Fix: pass `[SystemMessage(content=formatted_prompt), HumanMessage(content=user_input)]`.
This is the same Gemini 3.1 constraint class as the content list-flatten fix — an API
difference between Gemini 2.x and 3.x that must be adapted to at the call site.
The unit tests (which mock the LLM) are unaffected. The behaviour is identical.
This deviation is flagged for Architecture Chat review.

## Phase 3 — Self-review Findings
No discrepancies found after re-reading every line:
- Only `last_intent` modified — confirmed
- Content list-flatten applied (lines 74-77 in final file)
- Invalid intent → `"follow_up"` ✓
- LLM failure → `"follow_up"` ✓
- Empty messages → `"get_recommendation"` ✓
- All values from settings, never hardcoded ✓

## Phase 4 — Integration Boundary Check (route_by_intent)
All 7 intents SupervisorNode can output have a corresponding route:
- `get_recommendation` → `filter_node` or `profiler` ✓
- `profile_update` → `profiler` ✓
- `fee_query`, `market_query`, `follow_up`, `clarification`, `out_of_scope` → `answer_node` ✓
- Fallback `"follow_up"` (from invalid/exception) → `answer_node` ✓

No intent produces an unhandled case. `route_by_intent` else branch returns `END` as safety net.

## Test Results
```
tests/test_supervisor_node.py::test_valid_intent_returned PASSED         [ 14%]
tests/test_supervisor_node.py::test_intent_whitespace_stripped PASSED    [ 28%]
tests/test_supervisor_node.py::test_invalid_intent_falls_back PASSED     [ 42%]
tests/test_supervisor_node.py::test_llm_failure_falls_back PASSED        [ 57%]
tests/test_supervisor_node.py::test_empty_messages_handled PASSED        [ 71%]
tests/test_supervisor_node.py::test_only_last_intent_modified PASSED     [ 85%]
tests/test_supervisor_node.py::test_roman_urdu_classified PASSED         [100%]

7 passed in 2.40s
```

## SYSTEM PROMPT (full text)
```
You are an intent classifier for an academic career guidance system.
Classify the student's message into exactly one of these intents:
get_recommendation, profile_update, fee_query, market_query,
follow_up, clarification, out_of_scope

Rules:
- If the student mentions changing budget, marks, or preferences: profile_update
- If the student asks about a specific university's fees or costs: fee_query
- If the student asks about careers, jobs, or future scope: market_query
- If the student references their existing recommendations: follow_up or clarification
- If unclear between follow_up and clarification: use follow_up
- Never return anything except one of the seven intent strings above

Student message: {user_input}
Respond with only the intent string. No explanation.
```

## SYSTEM PROMPT TOKEN COUNT
Estimated ~170 tokens. Within the 200–350 target for SupervisorNode per BACKEND_CHAT_INSTRUCTIONS.md.

## Known Failure Modes
- `supervisor.py line 65`: If `last_msg.content` is an empty string, `user_input` will be `""`. The LLM will receive a blank user_input slot in the formatted prompt. This will likely produce a valid intent (possibly `"follow_up"`) rather than crashing. Not a crash condition but may produce arbitrary classification for empty input.

## ASSUMPTIONS
1. **Gemini 3.1 SystemMessage+HumanMessage pattern:** Gemini 3.1 does not accept a lone SystemMessage. Added `HumanMessage(content=user_input)` alongside the SystemMessage. user_input appears twice in the message list (once embedded in the formatted system prompt, once as the HumanMessage). This is redundant but necessary for the API. If Architecture Chat has a cleaner pattern, it should override this.
2. **Roman Urdu handling:** Handled entirely by the LLM without any preprocessing. The spec states this as the primary reason for using LLM over keyword matching. Confirmed working in Phase 5b: "Yaar mujhe CS ka scope batao Pakistan mein" → `market_query`.
3. **`"clarification"` vs `"follow_up"` both route to `answer_node`:** The distinction is cosmetic at the routing level. Phase 5b showed "Why did NED rank higher than SZABIST?" → `clarification`, "What is my RIASEC match score for NED CS?" → `follow_up`. Both are correct since both route to `answer_node`.

## What Architecture Chat Should Review
1. **Gemini 3.1 call pattern:** `[SystemMessage(formatted_prompt), HumanMessage(user_input)]` — user_input is embedded in both. Is there a cleaner approach (e.g., separate system instructions from user_input in the prompt template)?
2. **Phase 5b LLM classifications:** All 7 test messages classified correctly, but "Why did NED rank higher than SZABIST?" → `clarification` while "What is my RIASEC match score for NED CS?" → `follow_up`. The spec says use `follow_up` if unclear. Are there boundary cases where these two labels produce different downstream behaviour via `answer_node`? Currently they don't — both route to `answer_node`.
3. **follow_up as universal fallback:** Both invalid-intent fallback and LLM-failure fallback write `"follow_up"`. This means `answer_node` handles all degraded states. Confirm this is the correct degraded-state behaviour.
