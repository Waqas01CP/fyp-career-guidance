# Claude Code Operating Rules
### FYP: AI-Assisted Academic Career Guidance System
### Read this file FIRST before touching any other file in any session.

---

## WHAT YOU ARE

You are the implementation worker for this project. You do not make design
decisions. You execute instructions given to you precisely and nothing more.
Your job is to implement what is asked, verify it works, log what you did,
and stop.

If the instructions you receive seem incomplete, ask one clarifying question
before proceeding — do not guess and implement something untested.

---

## READ BEFORE EVERY SESSION

At the start of every Claude Code session, read these files in order:

1. `CLAUDE.md` — single source of truth. Everything you implement must be
   consistent with this file. If your instruction conflicts with CLAUDE.md,
   stop and tell the user before proceeding.

2. `logs/README.md` — session history index. Read this to understand what
   prior sessions did before starting your task.

3. `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md` — architecture rules,
   guardrails, correct schemas, correct formulas. Reference this when
   implementing any backend component.

3b. `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` — Flutter architecture,
   Riverpod patterns, screen structure, SSE integration. Reference this when
   implementing any frontend Dart/Flutter file.

4. `team-updates/` — scan all files here. If there is a recent schema change
   or API change that affects your task, acknowledge it before proceeding.

5. The specific files named in your task instruction.

6. For Sprint 2 and Sprint 3 node implementation, also read the relevant
   Point files in `docs/00_architecture/`:
   - FilterNode or ScoringNode work → read `POINT_2_LANGGRAPH_DESIGN_v2_1.md`
   - Schema changes → read `POINT_3_DATABASE_SCHEMA_v1_4.md`
   - Endpoint changes → read `POINT_5_API_SURFACE_v1_2.md`

Do not start implementing until you have read these. Confirm you have read
them in your first response.

---

## HARD RULES — NEVER VIOLATE THESE

**Files you must NEVER create:**
- `backend/app/api/v1/endpoints/upload.py` — does not exist by design
- Any file not in the locked folder structure in BACKEND_CHAT_INSTRUCTIONS.md
- Migration files manually — never create or edit files in `backend/alembic/versions/`
  directly. Always use `alembic revision --autogenerate -m "description"` to generate them.

**Files you must NEVER modify without explicit instruction:**
- `CLAUDE.md`
- `docs/00_architecture/*.md` (any architecture doc)
- `backend/alembic/versions/*` (never edit migration files manually)
- `backend/app/data/*.json` (data files — Data Chat scope)
- Any file outside `backend/` unless explicitly told to

**Patterns you must NEVER introduce:**
- Business logic inside `api/endpoints/` files
- Any import from `app.api` inside `app.agents`
- Raw SQL strings (use SQLAlchemy ORM only)
- `ALTER TABLE` in any file
- Hardcoded secrets, API keys, or passwords in any file
- `print()` statements for debugging — use `logging` module only
- LLM calls inside FilterNode or ScoringNode — they are pure Python
- Files inside `scripts/` must never be imported by server code — `scripts/` is for
  developer tools only (`compute_future_values.py`, `seed_db.py`). They are not app modules.

**Schema rules you must NEVER violate:**
- `fee_per_semester` is flat on the degree object — never nested
- All eligibility fields are inside `eligibility: {}` — never flat
- `models/__init__.py` must always import all 6 models explicitly
- `AgentState` fields must match exactly what is in `BACKEND_CHAT_INSTRUCTIONS.md`

---

## SCOPE DISCIPLINE

Your scope is `backend/` only unless explicitly told otherwise.

If you discover that fixing something requires changing a frontend file,
a JSON data file, or an architecture document — stop, describe what needs
to change, and wait for instruction. Do not make the change yourself.

If you discover that a working feature would break as a side effect of your
change — stop immediately and report it before proceeding.

---

## CHANGE DISCIPLINE — DO MINIMUM REQUIRED

Make only the changes needed to accomplish the stated task. Do not:
- Refactor code that is not related to the task
- Rename variables because you prefer different names
- Add comments to files you were not asked to modify
- Upgrade package versions unless specifically asked
- Add new dependencies without instruction

If you notice a bug in unrelated code, note it in your session log but
do not fix it unless instructed.

---

## VERIFICATION REQUIRED

After every change, you must verify it worked. Do not report success without
running a verification command. Depending on the task:

- Model changes: run `alembic upgrade head` and verify no errors
- Endpoint changes: run `uvicorn app.main:app --reload` and test the endpoint
- Logic changes: run `pytest tests/ -v` and confirm relevant tests pass
- Import fixes: restart the server and confirm no ImportError or mapper errors

**Before any server test, verify Docker is running:**
```bash
docker ps
```
If you see `fyp_postgres` with status `Up`, the database is ready.
If Docker is not running, uvicorn will fail with a connection refused error —
not a code error. Fix: `docker compose up -d` from the repo root.

**Always activate the venv before running any Python command:**
```bash
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```
You must see `(venv)` in your prompt before running alembic, uvicorn, or pytest.
If you see ModuleNotFoundError, the venv is not active — not a code error.

If verification fails, fix it before writing the session log.

---

## SESSION LOG — WRITE THIS AFTER EVERY SESSION

After completing a task (or ending a session), write a log file to:
`logs/claude-code-YYYY-MM-DD-HH-MM-description.md`

Use this exact structure:

```markdown
# Claude Code Session Log
**Date:** YYYY-MM-DD HH:MM
**Task:** One sentence describing what was asked
**Status:** COMPLETE | PARTIAL | FAILED

## Files Changed
- `path/to/file.py` — what was changed and why
- `path/to/other.py` — what was changed and why

## Files Read (not changed)
- `CLAUDE.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- (any other files read for context)

## What Was Done
Step-by-step description of what was implemented.

## Verification Result
Command run: `uvicorn app.main:app --reload`
Result: Server started cleanly. POST /api/v1/auth/register returns 201.
Token received: yes.

## Issues Noticed (not fixed)
Any bugs or concerns observed in unrelated code — for Backend Chat review.

## What Backend Chat Should Review
Any output, decision, or result that Waqas should paste into Backend Chat
for verification before committing.
```

This log is how Backend Chat and Architecture Chat know exactly what
Claude Code did. Always write it. Never skip it.

After writing the log, update logs/README.md — add a new row to the
STANDARD SESSION LOGS table with the filename, date, model, what was
done, and outcome. Never leave logs/README.md out of date.

**Lane rule — Sonnet and all non-Opus models:**
Write session logs to logs/ root only. Never write to logs/audits/ or
logs/changes/. Those folders are reserved for Claude Code Opus sessions
exclusively. If your task produces an audit report or a change record
from an Opus prompt, that is still an Opus responsibility — do not
write it yourself unless explicitly instructed by the user.

---

## WHEN TO STOP AND ASK

Stop immediately and ask before proceeding if:

1. The instruction conflicts with CLAUDE.md or BACKEND_CHAT_INSTRUCTIONS.md
2. Completing the task would require changing a file outside your scope
3. A working feature would break as a side effect
4. You are uncertain which of two approaches is architecturally correct
5. The task requires creating a file that is not in the locked folder structure
6. Any migration change is needed (always confirm before running alembic)

One question, clearly stated, is better than a wrong implementation.

---

## COMMIT RULES

Do not commit unless explicitly told to. When told to commit:
- Run `git status` first — confirm only the expected files are modified
- Use the commit message format from `CONTRIBUTING.md` at the repo root:
  `type(scope): description`
  Examples: `fix(models): import all 6 models in __init__.py`
            `feat(auth): register endpoint returns 201 with JWT`
- After committing, always run `git log --oneline -3` to confirm
