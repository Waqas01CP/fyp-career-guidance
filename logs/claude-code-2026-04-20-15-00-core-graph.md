# Claude Code Session Log
**Date:** 2026-04-20 15:00
**Task:** Wire core_graph.py into the live SSE endpoint — replace Sprint 1 mock_stream with real LangGraph pipeline invocation via AsyncPostgresSaver checkpointer
**Status:** COMPLETE

## Files Changed
- `backend/requirements.txt` — added `psycopg[binary]` (psycopg3 required by AsyncPostgresSaver)
- `backend/app/core/config.py` — added `checkpoint_db_url` property (psycopg3 connection string for AsyncPostgresSaver)
- `backend/app/main.py` — replaced TODO lifespan stub with AsyncPostgresSaver initialization, checkpointer.setup(), build_graph(); added Windows event loop note
- `backend/app/api/v1/endpoints/chat.py` — full replacement of mock_stream with real_stream + helpers (_build_university_card, _build_roadmap_timeline, _write_recommendation, NODE_STATUS_MAP)

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md` (v2.1)
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md` (Sections 11 and 12)
- `docs/00_architecture/POINT_5_API_SURFACE_v1_2.md` (Endpoint 7 and SSE spec)
- `backend/app/agents/core_graph.py`
- `backend/app/main.py`
- `backend/app/api/v1/endpoints/chat.py`
- `backend/app/agents/state.py`
- `backend/app/core/config.py`
- `backend/app/core/database.py`
- `backend/app/models/recommendation.py`
- `backend/app/schemas/chat.py`
- `backend/requirements.txt`
- `logs/supabase-setup-log-2026-04-20.md`
- `backend/app/data/lag_model.json` (structure check)
- `backend/app/agents/nodes/filter_node.py` (roadmap entry fields)

## What Was Done

### Phase 0 — Dependency verification
- Added `psycopg[binary]` to requirements.txt
- Installed psycopg3: `pip install "psycopg[binary]"` → psycopg-binary-3.3.3
- Verified `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver` imports cleanly
- Verified `astream_events` attribute exists on compiled StateGraph (returns True)

### Phase 1 — Plan
Written plan covering all 9 items. Reviewed against Point 2 Section 11 and Point 5. No incoherencies found.

**Key pre-resolved deviations from Point 2 noted:**
- `prepare_threshold=0` is NOT added to the URL — `from_conn_string()` already passes it internally to `AsyncConnection.connect()`
- Recommendations row written in `chat.py`, not `core_graph.py` — agents/ must have zero DB imports

### Phase 2 — Implementation

**config.py:**
Added `checkpoint_db_url` property that strips `+asyncpg` from DATABASE_URL and appends `?sslmode=require`. `prepare_threshold=0` is NOT in the URL — `AsyncPostgresSaver.from_conn_string()` already passes it internally.

**main.py:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from app.agents.core_graph import build_graph
    async with AsyncPostgresSaver.from_conn_string(
        settings.checkpoint_db_url
    ) as checkpointer:
        await checkpointer.setup()
        app.state.graph = build_graph(checkpointer)
        yield
```
Imports are inside lifespan to avoid module-level import issues.

**chat.py:**
- Module-level: lag_model.json loaded once → `_LAG_MODEL_MAP` dict keyed by field_id
- `NODE_STATUS_MAP` maps core_graph.py node names → SSE status state values
- 4 helper functions: `_sse()`, `_build_university_card()`, `_build_roadmap_timeline()`, `_write_recommendation()`
- Endpoint has `db: AsyncSession = Depends(get_db)` parameter
- Pre-graph setup: loads StudentProfile, builds config with thread_id=session_id, loads previous_roadmap from recommendations table, builds initial_state with cleared run fields
- `real_stream()` generator: astream_events loop → aget_state() → chunk stream → rich_ui events → recommendation write → done in finally

### Phase 3 — Bug fixes during implementation

**Bug 1 — checkpoint_db_url had `prepare_threshold=0` in URL (invalid for psycopg3 URI):**
psycopg3 does not accept `prepare_threshold` as a URI query parameter (only libpq keywords are valid there). Discovered from `psycopg.ProgrammingError: invalid URI query parameter: "prepare_threshold"`. Fix: removed from URL. `from_conn_string()` already passes `prepare_threshold=0` to `AsyncConnection.connect()` internally.

**Bug 2 — Windows ProactorEventLoop incompatible with psycopg3:**
psycopg3 requires SelectorEventLoop on Windows. Python 3.8+ defaults to ProactorEventLoop. Setting `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())` in `main.py` does NOT work because uvicorn imports the app module INSIDE an already-running event loop (after `asyncio.run()` has been called).

Fix: Run uvicorn with `--loop asyncio --reload` flags. In reload mode, uvicorn spawns a subprocess worker that calls `asyncio_setup(use_subprocess=True)` which sets `WindowsSelectorEventLoopPolicy` BEFORE `asyncio.run()` creates the event loop. This is the correct and supported approach.

Production note: on Linux/Mac (Render, Railway), ProactorEventLoop does not exist — `--loop asyncio` is harmless.

## CONNECTION SETUP
- `checkpoint_db_url` format: `postgresql://postgres.PROJREF:PASS@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require`
- psycopg import confirmed: `from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver` — OK
- `astream_events` availability confirmed: `hasattr(compiled_graph, 'astream_events')` → True
- Password redacted from URL in this log

## INTEGRATION TEST RESULTS

| Test | Result | Details |
|---|---|---|
| Test 1: Server starts without crash | PASS | `Application startup complete.` in logs — checkpointer.setup() and build_graph() succeeded |
| Test 2: GET /health → 200 | PASS | `{"status":"ok","service":"fyp-career-guidance-api"}` |
| Test 3: Register/Login | PASS | Register → 201 with JWT; Login → 200 with JWT |
| Test 4: Full onboarding + profile check | PASS | quiz→riasec_complete, grades→grades_complete, assessment→assessment_complete. session_id non-null: 6f46beaa-f8ff-42e6-9bae-ab30921a8f19 |
| Test 5: POST /chat/stream first message | PASS | SSE stream emitted: status(profiling) → chunk events (word by word) → status(done). Done is always last. |
| Test 6: Server restart + same session_id | PASS | Fresh server startup, same session_id — conversation history restored from checkpointer. ProfilerNode continued from prior context (asked about budget/zone, not re-introduced itself). |

Test command for Windows:
```bash
uvicorn app.main:app --reload --loop asyncio
```

Full test suite: **65/65 passed** — no regressions.

## KNOWN GAPS

### AnswerNode tool-call status events (fetching_fees, fetching_market_data)
Not implemented in this session. The `astream_events` loop only maps `on_chain_start` events for `profiler`, `filter_node`, `scoring_node`, `explanation_node`. AnswerNode does not emit a status event when it calls `fetch_fees()` or `lag_calc()`. This means the Flutter ThinkingIndicator shows no label during fee/market queries (it shows nothing rather than "Fetching fees...").

Gap documented: Sprint 4 enhancement. Implementation would require either:
- Option A: subscribing to tool-call events in the astream_events loop
- Option B: emitting status events from inside AnswerNode itself (currently not possible without architectural change)

Flagged for Architecture Chat review.

## ASSUMPTIONS

**How astream_events node names map to graph node names:**
The `event["name"]` field in `on_chain_start` events matches the string passed to `graph.add_node()` in core_graph.py exactly. Verified against core_graph.py registrations: `"profiler"`, `"filter_node"`, `"scoring_node"`, `"explanation_node"`, `"answer_node"`, `"supervisor"`. Names are exact string matches — no prefix/suffix added by LangGraph.

**How aget_state() handles a thread that has never run:**
When the graph has never run for a thread_id, `aget_state(config)` returns `None` (not a checkpoint with empty values). The code handles this: `checkpoint = await ...; final_state = checkpoint.values if checkpoint else {}`.

**student_profile in initial_state on every call:**
Included on every call (not just first call) to ensure the graph uses the latest DB profile. For subsequent calls, this overwrites the checkpoint's student_profile — which is correct since profile data can change between sessions (e.g., quiz update).

**`previous_roadmap` loaded from recommendations table, not from state["current_roadmap"]:**
The PRE-RESOLVED note in the task prompt specifies this. It is equivalent to Point 2's "copy current_roadmap to previous_roadmap before clearing" — the recommendations table is written after each ExplanationNode run, so the most recent row's `roadmap_snapshot` is the same as what would have been in `current_roadmap`.

## Issues Noticed (not fixed)
- The existing `test_filter_node.py` has a stale comment about fee 60475→64475 (noted in session 2026-04-18-12-00). Not fixed (out of scope for this session).
- `alembic upgrade head` cannot run against Supabase due to asyncpg+pooler incompatibility (documented in supabase-setup-log). Not fixed (known issue, does not affect demo).

## What Architecture Chat / Backend Chat Should Review
1. **AnswerNode tool status events**: is Option A (astream_events tool call detection) or Option B (status events from inside answer_node) preferred for Sprint 4?
2. **`--loop asyncio` for production**: Render and Railway run on Linux — no ProactorEventLoop issue. But document this as the required Windows dev command in a README or Makefile. Waqas should update the dev startup docs.
3. **student_profile refresh strategy**: currently refreshed on every chat call from DB. This means any profile update is immediately visible in the next chat turn. Is this desired behavior, or should we use a session-start-only load?
4. **checkpoint_db_url `prepare_threshold=0` note in CLAUDE.md PRE-RESOLVED section**: the PRE-RESOLVED note says to add `prepare_threshold=0` to the URL but this is incorrect — `from_conn_string()` already passes it internally. The CLAUDE.md note should be corrected in a future Architecture Chat session.
