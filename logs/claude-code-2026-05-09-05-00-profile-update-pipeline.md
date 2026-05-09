# claude-code-2026-05-09-05-00-profile-update-pipeline.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: profile_update auto-rerun — route_after_profiler + card emission + trigger fix

---

## Problem

When a student changed a constraint mid-session ("change my budget to 40,000"),
SupervisorNode classified it as `profile_update`, ProfilerNode updated
`active_constraints`, and the graph ended at END. No pipeline rerun, no new
cards emitted, no DB write. The student saw ProfilerNode's text acknowledgement
but their recommendation cards never updated. On app restart, the dashboard
restored the stale pre-change snapshot. Misleading and incorrect.

---

## Changes Made

### core_graph.py — route_after_profiler

Added new conditional edge function after `route_by_intent()`:

```python
def route_after_profiler(state: AgentState) -> str:
    if (
        state.get("last_intent") == "profile_update"
        and state.get("profiling_complete", False)
    ):
        return "filter_node"
    return END
```

Replaced `graph.add_edge("profiler", END)` with:
```python
graph.add_conditional_edges(
    "profiler",
    route_after_profiler,
    {
        "filter_node": "filter_node",
        END: END,
    },
)
```

No new imports — `END` was already imported at line 9.

### chat.py — should_emit_cards

Before:
```python
should_emit_cards = (
    current_roadmap and
    last_intent in ("get_recommendation", "follow_up")
)
```

After:
```python
should_emit_cards = (
    current_roadmap and
    last_intent in ("get_recommendation", "follow_up", "profile_update")
)
```

### chat.py — _write_recommendation call site

Added `elif last_intent == "profile_update":` branch inside `if should_emit_cards:`:
```python
elif last_intent == "profile_update":
    # Auto-rerun completed — save updated recommendations to DB
    # No timeline on profile_update (roadmap path unchanged)
    await _write_recommendation(
        db, current_user.id, current_roadmap, previous_roadmap, last_intent
    )
```

Timeline is NOT emitted on `profile_update` — only on `get_recommendation`. ✓

### chat.py — trigger logic restored in _write_recommendation()

Before (broken — stored raw intent string):
```python
trigger=last_intent,
```

After (restored correct semantic logic):
```python
trigger=(
    "initial"
    if not previous_roadmap
    else "profile_update"
    if last_intent == "profile_update"
    else "manual_rerun"
),
```

`"profile_update"` trigger is now a real case, not dead code.

---

## route_after_profiler Logic

| last_intent | profiling_complete | result |
|---|---|---|
| "profile_update" | True | "filter_node" (pipeline reruns) |
| "profile_update" | False | END (rare edge case — profiling incomplete) |
| "get_recommendation" | True/False | END (initial profiling — student must ask again) |
| any other | any | END |

---

## Path A Trace — Initial profiling (must NOT auto-rerun)

- `profiling_complete = False`, student says "I want recommendations"
- SupervisorNode: `last_intent = "get_recommendation"`
- `route_by_intent`: `get_recommendation` + `profiling_complete False` → `"profiler"`
- ProfilerNode runs, asks for budget
- `route_after_profiler`: `last_intent == "profile_update"` → **False** → returns `END`
- Graph ends. Student asked for budget. ✓ CORRECT — Situation 1 unchanged.

## Path B Trace — Profile update with existing recommendations

- `profiling_complete = True`, student says "change my budget to 40,000"
- SupervisorNode: `last_intent = "profile_update"`
- `route_by_intent`: `profile_update` → `"profiler"`
- ProfilerNode updates `active_constraints.budget = 40000`
- `route_after_profiler`: `last_intent == "profile_update"` AND `profiling_complete True` → `"filter_node"`
- FilterNode → ScoringNode → ExplanationNode
- `should_emit_cards`: `profile_update in (...)` → True → cards emitted
- `elif last_intent == "profile_update":` → `_write_recommendation()` called
- `trigger`: `not previous_roadmap → False`, `last_intent == "profile_update" → True` → `"profile_update"`
- DB updated with new snapshot. ✓ CORRECT — constraint change reflected immediately.

---

## CLAUDE.md Delta (for Architecture Chat)

LOCKED DECISIONS in CLAUDE.md states:
"University cards emission: rich_ui university_card events emitted on both
get_recommendation and follow_up intents."

This session adds `profile_update` to the emission condition. Architecture Chat
should update the locked decision to:
"rich_ui university_card events emitted on get_recommendation, follow_up, and
profile_update intents (when profile_update auto-reruns the pipeline).
roadmap_timeline only emitted on get_recommendation."

---

## Test Results

```
Graph module imported successfully
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 1.83s
```

No test files cover core_graph.py or chat.py stream logic — no test updates required.
