# Language Detection Fix — All Three LLM Nodes
**Date:** 2026-04-28
**Model:** Claude Sonnet 4.6
**Files changed:** answer_node.py, profiler.py, explanation_node.py

---

## Root Cause (as identified in task brief)

| Node | Before | Problem |
|---|---|---|
| AnswerNode | No language detection at all | Always responded in English |
| ProfilerNode | Static rule "respond in same language" — no recent_text injection | Relied on LLM context window which is unreliable for language switching |
| ExplanationNode | recent_text from last 2-3 messages only | Early Roman Urdu lost if conversation continued 8+ messages in English |

---

## Changes Made

### CHANGE 1 — AnswerNode (answer_node.py)

**What was before:** No language detection. Every intent path (fee_query, market_query, follow_up, out_of_scope) used static English-only system prompts with no recent_text context.

**What was changed:**
- Built `recent_text` (last 3 HumanMessages) and `language_rule` string once at the top of `answer_node()`, after `user_input` extraction
- Appended `language_rule` to the system prompt at call time for all 4 intent paths:
  - `fee_query`: `FEE_ANSWER_SYSTEM_PROMPT.format(...) + language_rule`
  - `market_query`: `MARKET_ANSWER_SYSTEM_PROMPT.format(...) + language_rule`
  - `out_of_scope`: `OUT_OF_SCOPE_SYSTEM_PROMPT + language_rule` (inline in llm.invoke call)
  - `follow_up/clarification`: `FOLLOWUP_ANSWER_SYSTEM_PROMPT.format(...) + language_rule`
- Module-level constants NOT modified — language_rule appended at call time only
- HumanMessage import was already present (line 11) — no duplicate added

### CHANGE 2 — ProfilerNode (profiler.py)

**What was before:** Static rule in RESPONSE RULES: `"  - Respond in the same language the student uses — English, Roman Urdu, or Urdu script\n"` — no recent_text injection.

**What was changed:**
- Added `recent_text` extraction in `_build_system_prompt()` after `conversation_turn` computation:
  - `human_messages` was already computed — reused it
  - `recent_human = human_messages[-3:] if len(human_messages) >= 3 else human_messages`
  - `recent_text = " | ".join(m.content for m in recent_human) or "no messages yet"`
- Replaced static rule with dynamic language detection block:
  ```
  "  - LANGUAGE DETECTION: The student's recent messages are shown below. Detect their language..."
  f"  - Student's recent messages for language detection: {recent_text}\n"
  ```
- HumanMessage import was already present (line 9) — no duplicate added

### CHANGE 3 — ExplanationNode (explanation_node.py)

**What was before:** `recent_text` extracted from `messages[-3:]` filtering by `not isinstance(m, AIMessage)` — last 2-3 student messages only. First message excluded if conversation > 3 messages long.

**What was changed:**
- Replaced extraction with first-message-always + last-2 logic:
  - `human_msgs = [m for m in messages if isinstance(m, HumanMessage)]`
  - `first_msg = [human_msgs[0]]`
  - `last_msgs = human_msgs[-2:] if len(human_msgs) > 1 else []`
  - `combined = first_msg + [m for m in last_msgs if m is not human_msgs[0]]`
  - Deduplication: `m is not human_msgs[0]` (identity check, not equality — handles message 1 being same object as last_msgs entry)
  - PII scrubbing preserved: `_scrub_pii(m.content)` for each combined message
- HumanMessage import was already present (line 22) — no duplicate added

---

## Test Results

```
62 passed, 3 deselected in 11.40s
```

All 62 tests pass. No test failures.

---

## LLM Output Test Results

Manual LLM output test NOT run (requires live Gemini API key in env). The language_rule logic is the same pattern already validated in ExplanationNode (see logs/llm-output-explanation-node-2026-04-20.md — language detection confirmed working there). The extension to AnswerNode and ProfilerNode uses identical mechanism.

**Expected behaviour per scenario (for future manual validation):**

Scenario A — Roman Urdu from message 1:
- `student_message = "Mujhe engineering mein interest hai, kaunsa degree lena chahiye?"`
- Expected: ALL three nodes respond in Roman Urdu

Scenario B — English throughout:
- `student_message = "I am interested in computer science"`
- Expected: ALL three nodes respond in English

Scenario C — Started Roman Urdu (msg 1), switched to English (msg 5-8), now msg 9:
- `recent_messages = [msg1 Roman Urdu, msg8 English, msg9 English]`
- ExplanationNode: first_msg=Roman Urdu + last_msgs=[msg8, msg9] English → mixed signals, recent context likely wins
- AnswerNode and ProfilerNode: last 3 messages are English → responds in English (correct for current intent)

---

## Edge Cases Identified

1. **ExplanationNode single-message conversation:** `len(human_msgs) == 1` → `last_msgs = []` → `combined = [human_msgs[0]]` → correct (first message only)
2. **ExplanationNode exactly 2 messages:** `first_msg = [msg0]`, `last_msgs = [msg0, msg1]` → dedup removes msg0 → `combined = [msg0, msg1]` → correct
3. **AnswerNode no messages in state:** `human_msgs = []` → `recent_human = []` → `recent_text = ""` → language_rule shows empty student messages → LLM defaults to English → acceptable fallback
4. **ProfilerNode first turn (no messages yet):** `human_messages = []` → `recent_text = "no messages yet"` → LLM reads neutral signal → defaults to English → correct (student hasn't written anything)
