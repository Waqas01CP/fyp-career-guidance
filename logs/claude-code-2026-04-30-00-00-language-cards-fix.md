# Session Log — Language Detection Fix + Follow-up Cards
**Date:** 2026-04-30
**Model:** Claude Sonnet 4.6
**Task:** Fix language detection in all three LLM nodes; emit university cards on follow_up intent.

---

## ISSUE 1 — Language detection was wrong in all three nodes

**Before:** Multi-message sampling for language detection.
- `explanation_node.py`: first student message + last 2, deduplicated.
- `answer_node.py`: last 3 student messages.
- `profiler.py`: last 3 student messages.

**Problem:** Student typing English for 5 messages then 1 Roman Urdu message then English
again would cause AI to randomly switch to Roman Urdu on subsequent English messages because
the first message (English) was always included and mixed with the current message.

**After:** Single-message detection — ONLY the most recent HumanMessage is used.

### Changes per file

**explanation_node.py:**
- Extraction block (lines ~384–391) replaced: `recent_text` multi-message build → `current_msg_text = _scrub_pii(human_msgs[-1].content) if human_msgs else ""`
- Call site: `_build_system_prompt(..., recent_text=current_msg_text)` — passes `current_msg_text` as the `recent_text` keyword argument.
- Parameter name `recent_text` kept unchanged in `_build_system_prompt()` signature to preserve 5 existing tests.
- `lang_rule` text updated: "Respond in the SAME language as the student's current message... This overrides any previous language choices... Only the current message determines the response language."
- Label kept as `"Student's recent messages:"` (not changed to "current") to avoid breaking 3 test assertions that check for that exact string.

**answer_node.py:**
- `recent_human = human_msgs[-3:]` + `recent_text = " | ".join(...)` → `current_msg_text = human_msgs[-1].content if human_msgs else ""`
- `language_rule` text updated to same "current message overrides" wording.

**profiler.py:**
- `recent_text` extraction (last 3 messages) → `current_msg_text = human_messages[-1].content if human_messages else "no messages yet"`
- RESPONSE RULES language section updated to "current message overrides" wording.

---

## ISSUE 2 — University cards not emitted on follow_up intent

**Before:** `if current_roadmap and last_intent == "get_recommendation":` — too restrictive.
When SupervisorNode classified a recommendation-related message as "follow_up", no cards emitted
even though `current_roadmap` was already populated from the prior turn.

**After (chat.py):**
```python
should_emit_cards = (
    current_roadmap and
    last_intent in ("get_recommendation", "follow_up")
)
if should_emit_cards:
    for i, degree in enumerate(current_roadmap[:5]):
        card = _build_university_card(degree, i + 1, final_state)
        yield _sse("rich_ui", {"type": "university_card", "payload": card})

    if last_intent == "get_recommendation":
        timeline = _build_roadmap_timeline(...)
        yield _sse("rich_ui", {"type": "roadmap_timeline", "payload": timeline})
        await _write_recommendation(...)  # DB write — only on first recommendation
```

- Cards emitted on `get_recommendation` AND `follow_up`.
- Timeline emitted only on `get_recommendation` (it doesn't change on follow-ups).
- `_write_recommendation` moved inside `last_intent == "get_recommendation"` guard — follow-up
  queries no longer create duplicate recommendation rows.

---

## Test results

```
62 passed, 3 deselected in 1.95s
```

All 62 tests pass. 3 deselected = integration tests marked slow.

---

## Files modified

1. `backend/app/agents/nodes/explanation_node.py`
2. `backend/app/agents/nodes/answer_node.py`
3. `backend/app/agents/nodes/profiler.py`
4. `backend/app/api/v1/endpoints/chat.py`

No other files changed.
