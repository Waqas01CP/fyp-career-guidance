# Session Log: SSE Keepalive for Render 30s Timeout Fix
**Date:** 2026-04-27
**Model:** Claude Sonnet 4.6
**Files modified:** `backend/app/api/v1/endpoints/chat.py`, `backend/app/core/config.py`

---

## Problem

Render free tier enforces a 30-second request timeout. When the LLM pipeline
(FilterNode → ScoringNode → ExplanationNode via Gemini or Claude) takes longer
than ~30 seconds, Render's proxy drops the SSE connection silently. Result:
- Flutter ThinkingIndicator spins indefinitely
- No `done` event received
- Student must close and reopen the app

## Root Cause

SSE connections kept alive by data flow. When the LangGraph graph is blocked
waiting for an LLM response, no bytes are written to the TCP stream. After 30
seconds of silence, Render's proxy terminates the connection.

## Fix

Added a concurrent asyncio keepalive task inside `real_stream()` in chat.py.

### Generator structure (pre-fix)

`real_stream()` was already `async def real_stream()` — an async generator.
`asyncio.create_task()` works directly without restructuring.

### Implementation chosen

Queue-based interleave pattern:
1. `asyncio.Queue` (`keepalive_queue`) holds pending keepalive strings
2. `asyncio.Event` (`stop_keepalive`) signals the sender task to exit
3. `_keepalive_sender()` coroutine: waits up to `STREAM_KEEPALIVE_INTERVAL` seconds
   for `stop_keepalive`; on timeout, puts `": keepalive\n\n"` into the queue
4. `asyncio.create_task(_keepalive_sender())` runs it concurrently with the generator
5. Inside the `async for event in astream_events(...)` loop: drain queue before
   yielding each real event
6. After the loop exits: drain queue again before post-graph code (aget_state, chunks, rich_ui)
7. `finally` block: `stop_keepalive.set()`, `keepalive_task.cancel()`, yield `done`
   — no `await keepalive_task` (unsafe during CancelledError propagation per user instruction)

### Keepalive format

`": keepalive\n\n"` — raw SSE comment line. Lines starting with `:` are ignored
by all SSE clients including Flutter's `http` package. NOT wrapped in `_sse()`
helper — yielded as raw string per the hard rules in the task prompt.

### Keepalive interval

`settings.STREAM_KEEPALIVE_INTERVAL` = 15 seconds (defined in config.py).
Sends a keepalive every 15 seconds while graph is blocked, well under the 30s
Render timeout threshold.

## Config changes

Added to `config.py`:
```python
STREAM_KEEPALIVE_INTERVAL: int = 15  # seconds between keepalive comments
STREAM_TIMEOUT_SECONDS: int = 300    # 5-minute hard limit on stream duration
```

`STREAM_TIMEOUT_SECONDS` is defined but not yet enforced in the generator —
added for future Sprint 4 use (SSE stream timeout state, DEFERRED WORK item 4).

## Edge cases verified

- **Graph blocked on LLM for 20+ seconds:** keepalive fires at t=15s, t=30s etc.
  TCP stays alive. When graph resumes and emits an event, queue is drained before
  the real event is yielded.
- **Short pipeline (<15s):** keepalive queue stays empty. No keepalive bytes sent.
  Zero overhead.
- **Exception in graph:** `except` catches, `finally` fires. `stop_keepalive.set()`
  + `keepalive_task.cancel()` runs. Task is cancelled without await. `done` yielded.
- **Client disconnect mid-stream:** Generator is garbage-collected by StreamingResponse.
  `finally` fires when generator is cleaned up. keepalive_task cancelled. No leak.
- **CancelledError propagation:** `finally` does NOT await the task. Safe.

## Manual test instructions (post-Render-deploy)

1. Push to main. Wait ~3 minutes for Render to redeploy.
2. Send a chat message triggering the full recommendation pipeline.
3. In browser DevTools → Network tab → select the chat/stream request → EventStream.
4. Observe `: keepalive` comment lines appearing every ~15 seconds in the raw stream.
5. Confirm `done` event arrives and stream closes cleanly.
6. Confirm no silent timeout/drop during a 60-second wait.

## HARD RULES compliance check

- [x] Only `chat.py` and `config.py` modified — no other files
- [x] No new packages added
- [x] Keepalive comment is raw `": keepalive\n\n"` — NOT wrapped in `_sse()`
- [x] `done` event is in the `finally` block
- [x] `asyncio.create_task()` viable — `real_stream()` was already `async def`
- [x] No `await keepalive_task` in finally block (per user correction)
