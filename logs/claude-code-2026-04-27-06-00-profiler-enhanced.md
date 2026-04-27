# Session Log — ProfilerNode Enhanced Counsellor Prompt
## Date: 2026-04-27
## Model: Claude Sonnet 4.6
## File modified: backend/app/agents/nodes/profiler.py only

---

## CONTEXT

PROFILER_REQUIRED_FIELDS was emptied in the previous session (preferences-endpoint).
Budget/zone/transport now collected via Step 4 onboarding screen.
ProfilerNode's old prompt still said "Ask ONE missing required field at a time" — with no required
fields, this made the node nearly inert. Goal: transform ProfilerNode into a genuine academic
counsellor that enriches the student profile throughout the conversation.

---

## CHANGES MADE

### 1. New helper: `_interpret_riasec()` (lines 113-129)

Added above `_build_system_prompt()`. Converts raw RIASEC dict to a counsellor-readable
summary string ("primarily analytical/investigative and organised/systematic"). Intentionally
avoids exposing numeric scores. Used in profile_block of the system prompt.

Dim mappings:
- R → hands-on/technical
- I → analytical/investigative
- A → creative/artistic
- S → people-oriented/social
- E → leadership/entrepreneurial
- C → organised/systematic

### 2. Rewrote `_build_system_prompt()` (lines 132-257)

Three structural changes:

**role_block:** Replaced generic "profiling assistant collecting fields" description with
expert academic counsellor framing. Explicitly states the 3 goals: fill profile gaps,
help articulate interests/goals, provide personalised guidance.

**profile_block:** Replaced raw RIASEC scores and JSON constraints dump with:
- `_interpret_riasec()` summary (never raw numbers)
- `strong_subjects` (>= 75%) and `weak_subjects` (< 65%) lists from capability_scores
- `conversation_turn` computed from `isinstance(m, HumanMessage)` count (per user correction)
- All existing constraints in human-readable form

**strategy_block:** Three-stage counselling strategy replaces the old rules section:
- EARLY (turns 1-3): general intake questions — interests, career direction, avoid list
- MID (turns 4-8): profile-driven questions — weak subjects, RIASEC-based probes (high I, E, S)
- LATE (turn 9+): generate single most useful question given everything known
- EXTRACTION RULES: budget, transport, career goals, family constraints, stream
- RESPONSE RULES: 3-4 sentences + 1 question, language parity, no numeric leakage

**Final assembly:** `role_block + profile_block + strategy_block + _KARACHI_ZONES + "\n" + olevel_hint + _JSON_SCHEMA`

### 3. No changes to:
- `profiler_node()` — unchanged
- `check_profiling_complete()` — unchanged
- `_parse_llm_response()` — unchanged
- `_JSON_SCHEMA` — unchanged
- All imports — no new imports added

---

## DISCREPANCY NOTED (not blocking)

Point 2 Section 6 (line 477-489) still documents `PROFILER_REQUIRED_FIELDS = [...]` with 3 fields.
Actual `config.py` has `[]`. This is documentation lag from the preferences-endpoint session.
CLAUDE.md is consistent with config.py. Point 2 needs an Architecture Chat update.

---

## TEST RESULTS

### Unit tests
- `pytest backend/tests/test_profiler_node.py -v -m "not slow"`: 4/4 PASS
- `pytest -v -m "not slow"` (full suite): 62/62 PASS

### LLM output test
Throwaway script: `backend/scripts/test_profiler_enhanced.py` (delete after session)
Output log: `logs/llm-output-profiler-enhanced-2026-04-27.md`

| Run | Result |
|-----|--------|
| Turn 1 — fresh student, RIASEC I+C dominant | PASS — asked genuine interest question, not budget/zone |
| Turn 5 — mid-conversation, math=45 weak | PARTIAL PASS — asked location (valid), did not specifically address math weakness |
| Turn 10 — full profile, student asks about abroad | PASS — asked family constraints, contextualised with abroad goal |

---

## PREVIOUS SESSION REFERENCE

`claude-code-2026-04-27-05-00-preferences-endpoint.md` — emptied PROFILER_REQUIRED_FIELDS, 
added preferences endpoint. This session is the follow-on that upgrades the prompt behaviour.
