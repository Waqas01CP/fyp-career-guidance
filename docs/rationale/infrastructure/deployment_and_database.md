# Deployment and Database Infrastructure

**Component:** Supabase, Alembic, Render, JWT, Flutter/Riverpod
**Decided:** Architecture Chat v1-v5 (March-May 2026)
**Status:** All deployed and operational

---

## Supabase — Why PostgreSQL via Supabase

**Why PostgreSQL:**
The system requires: relational data (users → student_profiles → recommendations),
JSONB columns for flexible assessment score storage, and reliable concurrent
access. PostgreSQL provides all three natively.

**Why Supabase over raw PostgreSQL:**
- Free tier provides a production-grade PostgreSQL instance with no
  infrastructure management
- Row Level Security (RLS) is available when needed post-viva
- Supabase dashboard provides direct SQL editor access — critical for
  the Alembic workaround (see below)
- Built-in connection pooling via PgBouncer Session Pooler

---

## The Alembic + Supabase Constraint

**The problem:**
`alembic upgrade head` cannot run against Supabase via asyncpg. The
root cause is that Supabase's Session Pooler requires `NullPool` and
`statement_cache_size=0` in the connection configuration. The `alembic upgrade head`
command uses a different connection path that does not apply these settings,
causing the command to hang or fail.

**The workaround (locked in CLAUDE.md):**
1. Generate the migration file with `alembic revision --autogenerate`
2. Manually curate the migration file (remove unwanted DROP statements
   for LangGraph checkpoint tables, manually-added indexes, etc.)
3. Apply the SQL manually via Supabase SQL Editor
4. Update `alembic_version` table manually to match the migration ID

**Why the curation step matters:**
Alembic's autogenerate compares the ORM model against the live database.
The live database contains LangGraph checkpoint tables (created by
AsyncPostgresSaver at runtime), manually-added application indexes, and
columns added via Supabase SQL Editor that are not in the ORM model
(e.g., `curriculum_level`). Autogenerate would generate DROP statements
for all of these. Manual curation removes those DROP statements, keeping
only the intended schema changes.

**Future mitigation:**
Post-viva: investigate using a direct PostgreSQL connection (not through
the Session Pooler) for Alembic commands only. This would allow
`alembic upgrade head` to run normally.

---

## AsyncPostgresSaver — LangGraph Checkpointing

**Why checkpointing:**
LangGraph checkpointing persists the entire conversation state between
HTTP requests. Without it, every request starts a fresh conversation —
the system cannot remember what was said two turns ago.

**Why AsyncPostgresSaver (not MemorySaver):**
`MemorySaver` stores state in-memory — lost on server restart or when
Render spins down the instance after inactivity (Render free tier). Every
Render cold start would reset all conversations. `AsyncPostgresSaver`
persists to Supabase — conversations survive restarts indefinitely.

**psycopg3 requirement:**
AsyncPostgresSaver requires psycopg3 (the new async-native psycopg).
psycopg2 (the older sync library) is not compatible. This was a
non-obvious requirement discovered during setup — the error message was
unhelpful. Documented in `logs/supabase-setup-log-2026-04-20.md`.

---

## Render — Backend Deployment

**Why Render:**
- Free tier provides a persistent web service (not a serverless function)
- LangGraph requires persistent processes for `astream_events` SSE
  streaming — serverless functions time out during long streams
- Auto-deploy from GitHub push — no deployment configuration needed
- Environment variables managed via Render dashboard

**Render sleep behaviour:**
Free tier Render instances sleep after 15 minutes of inactivity. First
request after sleep triggers a cold start (~30 seconds). Acceptable for
a student FYP — post-viva: upgrade to paid tier for always-on service.

**Environment variables on Render:**
JWT_EXPIRY_MINUTES=10080, GEMINI_API_KEY, DATABASE_URL, and others.
These must match `backend/app/core/config.py` settings exactly.

---

## JWT — 7-Day Expiry

**Why 7 days (not 60 minutes, not 30 days):**
The onboarding flow requires completing RIASEC quiz, grades input, and
capability assessment across potentially multiple sessions. A 60-minute
expiry would force re-login mid-onboarding for students who take breaks.
A 30-day expiry is unnecessarily long for a student-facing system.

7 days provides enough coverage for:
- Multi-session onboarding (student completes quiz one day, grades next day)
- Casual re-engagement within a week
- Automatic re-login prompt after a week of inactivity

**Implementation:** JWT_EXPIRY_MINUTES=10080 in config.py AND in Render
environment variables. Do not change one without the other.

---

## Flutter + Riverpod — Frontend State Management

**Why Flutter:**
- Single codebase for iOS and Android
- The team has Dart/Flutter experience (Khuzzaim)
- Hot reload makes UI iteration fast
- `http` package with stream parsing handles SSE natively

**Why Riverpod (not BLoC, not Provider):**
- Provider was the first consideration — rejected as too simple for
  the complex state (authentication + onboarding stage + chat + SSE)
- BLoC was evaluated — rejected as overkill for a 3-person team with
  one frontend developer. BLoC's boilerplate overhead would slow
  Khuzzaim significantly
- Riverpod provides: reactive state without BuildContext dependency,
  clean separation between UI and state, easy async state management
  for SSE streaming

**flutter_screenutil:**
All dimensions use flutter_screenutil for auto-scaling. No hardcoded
pixel values anywhere in the Flutter codebase. This ensures the app
looks correct on the range of Pakistani Android devices (Samsung A6
is the primary test device).

---

## curriculum_level — The ORM Gap

`curriculum_level` is a column that exists in the live Supabase
`student_profiles` table but is NOT in `profile.py` ORM model.
It was added directly to Supabase at some point without a corresponding
ORM update.

**Impact:** Alembic autogenerate sees this as a column to DROP.
The Phase 0b migration was manually curated to remove the DROP statement.

**Fix (pending, no migration needed):**
Add `curriculum_level = Column(String)` to profile.py after the `board`
column. No migration needed — the column already exists in Supabase.
This is a 5-minute fix deferred to a cleanup session.

---

## Known Limitations

- Render free tier sleeps after 15 minutes — cold starts affect first
  user experience
- Supabase free tier has connection limits — LangGraph checkpoint
  connections count toward this limit
- JWT is stored in Flutter secure storage — no refresh token mechanism.
  After 7 days the student must log in again

---

## Future Enhancement Triggers

- When the system goes beyond student FYP use → upgrade Render to paid
  (always-on) and Supabase to paid (higher connection limits)
- When privacy requirements increase → implement refresh token rotation
  instead of fixed 7-day JWT
- Post-viva: investigate direct Alembic connection to bypass Session
  Pooler for migration commands
