# Supabase Setup Log
## FYP: AI-Assisted Academic Career Guidance System
### Date: April 20, 2026
### Author: Architecture Chat v4 + Waqas
### Purpose: Complete record of Supabase migration (Option B) — errors, solutions, final working state

---

## CONTEXT

This log documents the full process of migrating from local Docker PostgreSQL (Option A)
to Supabase hosted PostgreSQL (Option B). The decision was made on April 20, 2026 —
the demo milestone day — because core_graph.py (which uses AsyncPostgresSaver) had not
yet been built, and it was better to migrate to Supabase now while the database was still
empty rather than later.

**Why Option B over Option A:**
- Option A (local Docker): works, but database only exists on one machine. Demo cannot
  be shown on a different machine. Khuzzaim cannot test against the real backend remotely.
- Option B (Supabase): database accessible from anywhere. Correct long-term home for the project.

---

## WHAT WAS CHANGED IN THE CODEBASE

Only ONE file was changed from the committed codebase:

**`backend/app/core/database.py`** — added `NullPool` and `statement_cache_size=0`
to `create_async_engine`. This is required for asyncpg to work with Supabase's
Session Pooler. See "Why This Works" section below.

Everything else — `config.py`, `alembic/env.py`, `models/`, `endpoints/` — is unchanged
from the last commit.

---

## SUPABASE PROJECT DETAILS

| Field | Value |
|---|---|
| Project name | fyp-career-guidance-v2 |
| Region | Singapore (`ap-southeast-1`) |
| Project ref | `oialkebjsalutgwaguct` |
| Pooler host | `aws-1-ap-southeast-1.pooler.supabase.com` |
| Pooler type | Session Pooler (IPv4 compatible) |
| Port | 5432 |
| Database | postgres |
| Username | `postgres.oialkebjsalutgwaguct` |

**Note on the host:** The host is `aws-1-` not `aws-0-`. This is region-specific.
Never assume `aws-0-` — always copy the exact pooler host from the Supabase Connect modal.
Using `aws-0-` was one of the root causes of repeated `Tenant or user not found` errors
during the failed connection attempts on the first Supabase project.

---

## FINAL .env CONFIGURATION

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres.oialkebjsalutgwaguct:[YOUR-DB-PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres

SECRET_KEY="[YOUR-SECRET-KEY]"
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60

GEMINI_API_KEY="[YOUR-GEMINI-API-KEY]"
LLM_MODEL_NAME=gemini-3.1-flash-lite-preview

LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=your-langsmith-key-here
LANGCHAIN_PROJECT=fyp-career-guidance

APP_ENV=development
```

---

## FINAL database.py

```python
"""
database.py — SQLAlchemy async engine, session factory, and Base.
All models import Base from here. All endpoints use get_db() from dependencies.py.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from app.core.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    poolclass=NullPool,
    connect_args={"ssl": "require", "statement_cache_size": 0},
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency — yields an async DB session. Used via Depends(get_db)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

## WHY THIS WORKS — TECHNICAL EXPLANATION

### The core problem

Supabase's direct connection (`db.PROJECT_REF.supabase.co:5432`) only has an IPv6
address on the free tier. Windows machines in Pakistan typically have IPv4-only
connectivity. asyncpg cannot connect to an IPv6 address on an IPv4-only network.

The Session Pooler (`aws-1-ap-southeast-1.pooler.supabase.com:5432`) is IPv4
compatible, but it uses PgBouncer under the hood. asyncpg by default creates prepared
statements which PgBouncer in session mode does not handle cleanly at startup.

### The fix

Two changes to `create_async_engine`:

1. **`poolclass=NullPool`** — disables SQLAlchemy's own connection pool. This lets
   PgBouncer manage connections rather than having SQLAlchemy and PgBouncer both
   trying to pool simultaneously.

2. **`connect_args={"ssl": "require", "statement_cache_size": 0}`** — `ssl=require`
   because Supabase requires SSL. `statement_cache_size=0` disables asyncpg's
   prepared statement cache, which is what was causing PgBouncer to reject connections.

### Why the username has a dot

The Session Pooler requires the username format `postgres.PROJECT_REF`
(e.g. `postgres.oialkebjsalutgwaguct`). This includes the project reference in the
username so PgBouncer knows which Supabase tenant to route to.

If the username is just `postgres` (without the project ref), Supabase returns
`FATAL: Tenant or user not found`. This was the error we kept hitting.

### Why the host matters

The Supabase pooler is deployed per-region across multiple AWS load balancer clusters.
The cluster assigned to a project is visible only in the project's Connect modal.
For this project it is `aws-1-ap-southeast-1`. Using `aws-0-ap-southeast-1` (a common
assumption from documentation examples) caused `Tenant or user not found` because
the project did not exist on that cluster.

---

## TABLES CREATED ON SUPABASE

Tables were created manually via Supabase SQL Editor because `alembic upgrade head`
could not connect (same asyncpg + pooler incompatibility — Alembic uses asyncpg via
`alembic/env.py`).

### Method

1. Tables created via SQL Editor
2. `alembic_version` table created with the initial migration ID inserted:
   ```sql
   INSERT INTO alembic_version (version_num) VALUES ('a09bedc067be')
   ```
   This tells Alembic that the initial migration has already been applied.
   Future `alembic upgrade head` calls (if Alembic connectivity is restored)
   will not re-run the initial migration.

### SQL used to create all tables

```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID NOT NULL,
    email VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    role VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    session_state JSONB NOT NULL,
    session_summary TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS profile_history (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    snapshot JSONB NOT NULL,
    triggered_by VARCHAR NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- NOTE: First attempt had incorrect student_profiles schema (missing columns).
-- This is the corrected version based on the actual SQLAlchemy model.
CREATE TABLE student_profiles (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    onboarding_stage VARCHAR NOT NULL DEFAULT 'not_started',
    education_level VARCHAR,
    student_mode VARCHAR,
    grade_system VARCHAR,
    stream VARCHAR,
    board VARCHAR,
    curriculum_level VARCHAR,
    riasec_scores JSONB NOT NULL DEFAULT '{}',
    subject_marks JSONB NOT NULL DEFAULT '{}',
    capability_scores JSONB NOT NULL DEFAULT '{}',
    budget_per_semester INTEGER,
    transport_willing BOOLEAN,
    home_zone SMALLINT,
    stated_preferences JSONB NOT NULL DEFAULT '[]',
    family_constraints TEXT,
    career_goal TEXT,
    student_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- NOTE: First attempt had column named 'created_at'. Correct name is 'timestamp'.
-- This is the corrected version.
CREATE TABLE messages (
    id UUID NOT NULL,
    session_id UUID NOT NULL,
    role VARCHAR NOT NULL,
    content TEXT NOT NULL,
    agent_thought_trace JSONB NOT NULL DEFAULT '[]',
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS recommendations (
    id UUID NOT NULL,
    user_id UUID NOT NULL,
    run_timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    roadmap_snapshot JSONB NOT NULL,
    trigger VARCHAR NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num) VALUES ('a09bedc067be')
ON CONFLICT DO NOTHING;
```

### Indexes added (from Point 3 v1.4 specification)

```sql
CREATE INDEX chat_sessions_user_id_idx ON chat_sessions(user_id);
CREATE INDEX messages_session_id_idx ON messages(session_id);
CREATE INDEX recommendations_user_id_idx ON recommendations(user_id);
CREATE INDEX recommendations_run_timestamp_idx ON recommendations(run_timestamp DESC);
CREATE INDEX profile_history_user_id_idx ON profile_history(user_id);
```

---

## SCHEMA VERIFICATION

After all tables were created, the following SQL was run in the SQL Editor to verify
the exact schema against the SQLAlchemy models:

```sql
SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_schema = 'public'
    AND c.table_name IN ('users', 'student_profiles', 'chat_sessions', 'messages',
                         'recommendations', 'profile_history')
ORDER BY c.table_name, c.ordinal_position;
```

### Full CSV output (confirmed correct)

```
table_name,column_name,data_type,is_nullable,column_default
chat_sessions,id,uuid,NO,null
chat_sessions,user_id,uuid,NO,null
chat_sessions,session_state,jsonb,NO,null
chat_sessions,session_summary,text,YES,null
chat_sessions,created_at,timestamp with time zone,NO,now()
chat_sessions,last_active,timestamp with time zone,NO,now()
messages,id,uuid,NO,null
messages,session_id,uuid,NO,null
messages,role,character varying,NO,null
messages,content,text,NO,null
messages,agent_thought_trace,jsonb,NO,'[]'::jsonb
messages,timestamp,timestamp with time zone,NO,now()
profile_history,id,uuid,NO,null
profile_history,user_id,uuid,NO,null
profile_history,snapshot,jsonb,NO,null
profile_history,triggered_by,character varying,NO,null
profile_history,created_at,timestamp with time zone,NO,now()
recommendations,id,uuid,NO,null
recommendations,user_id,uuid,NO,null
recommendations,run_timestamp,timestamp with time zone,NO,now()
recommendations,roadmap_snapshot,jsonb,NO,null
recommendations,trigger,character varying,NO,null
student_profiles,id,uuid,NO,null
student_profiles,user_id,uuid,NO,null
student_profiles,onboarding_stage,character varying,NO,'not_started'::character varying
student_profiles,education_level,character varying,YES,null
student_profiles,student_mode,character varying,YES,null
student_profiles,grade_system,character varying,YES,null
student_profiles,stream,character varying,YES,null
student_profiles,board,character varying,YES,null
student_profiles,curriculum_level,character varying,YES,null
student_profiles,riasec_scores,jsonb,NO,'{}'::jsonb
student_profiles,subject_marks,jsonb,NO,'{}'::jsonb
student_profiles,capability_scores,jsonb,NO,'{}'::jsonb
student_profiles,budget_per_semester,integer,YES,null
student_profiles,transport_willing,boolean,YES,null
student_profiles,home_zone,smallint,YES,null
student_profiles,stated_preferences,jsonb,NO,'[]'::jsonb
student_profiles,family_constraints,text,YES,null
student_profiles,career_goal,text,YES,null
student_profiles,student_notes,text,YES,null
student_profiles,created_at,timestamp with time zone,NO,now()
student_profiles,updated_at,timestamp with time zone,NO,now()
users,id,uuid,NO,null
users,email,character varying,NO,null
users,password_hash,character varying,NO,null
users,role,character varying,NO,null
users,created_at,timestamp with time zone,NO,now()
```

### Audit result

| Table | Columns | Status |
|---|---|---|
| users | 5 | ✓ Matches model exactly |
| chat_sessions | 6 | ✓ Matches model exactly |
| profile_history | 5 | ✓ Matches model exactly |
| recommendations | 5 | ✓ Matches model exactly |
| messages | 6 | ✓ Matches model exactly |
| student_profiles | 21 | ✓ Matches model exactly |

---

## TESTING — CONFIRMED WORKING

### Test 1 — register endpoint (first user)

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email": "test@test.com", "password": "test1234"}' `
  -UseBasicParsing
```

Response:
```
StatusCode        : 201
Content           : {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

### Test 2 — register endpoint (second user, confirmed no duplicate)

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email": "test2@test.com", "password": "test1234"}' `
  -UseBasicParsing
```

Response:
```
StatusCode        : 201
Content           : {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

Both tests confirmed rows written to Supabase:
- `users` table: 2 rows
- `student_profiles` table: 2 rows
- `chat_sessions` table: 2 rows

---

## KNOWN ISSUE — Alembic migration missing curriculum_level

**What it is:** The Alembic migration file `backend/alembic/versions/a09bedc067be_initial_schema.py`
creates `student_profiles` with 20 columns. It is missing `curriculum_level`. The column
was added to the SQLAlchemy model (`backend/app/models/profile.py`) after the migration
was auto-generated, but no follow-up migration was committed.

**Impact on Supabase:** None. Supabase has the correct 21-column table because it was
built from the model directly, not from the migration file.

**Impact on fresh environments:** Anyone who clones the repo and runs `alembic upgrade head`
against a fresh database will get `student_profiles` without `curriculum_level`. The app
will fail when the grades endpoint or assessment endpoint tries to write or read this field.

**Fix required (Backend Chat task):** Generate a new Alembic migration:
```bash
alembic revision --autogenerate -m "add curriculum_level to student_profiles"
```
Then apply the generated SQL to Supabase via SQL Editor:
```sql
ALTER TABLE student_profiles ADD COLUMN IF NOT EXISTS curriculum_level VARCHAR;
```
And commit the new migration file.

**Status:** Logged, not yet fixed. Does not affect the demo.

---

## FULL ERROR HISTORY AND WHAT WAS TRIED

This section documents every connection error encountered and what was learned from each.

### Error 1 — `sslmode parameter must be one of: disable, allow, prefer, require, verify-ca, verify-full`

**URL tried:** `postgresql+asyncpg://...?ssl=true`

**Cause:** asyncpg does not accept `ssl=true`. The correct parameter is `ssl=require`.

**Fix:** Changed `?ssl=true` to `?ssl=require`.

---

### Error 2 — `getaddrinfo failed` (first Supabase project)

**URL tried:** `postgresql+asyncpg://postgres:[password]@db.sznqojlmwaldryfzbmke.supabase.co:5432/postgres?ssl=require`

**Cause:** DNS resolution failure. The direct connection host `db.sznqojlmwaldryfzbmke.supabase.co`
was not resolving on the local network DNS. The ISP DNS did not know this hostname.

**Fix attempted:** Changed DNS to Google DNS (8.8.8.8 / 8.8.4.4) via Windows network
adapter settings. Ran `ipconfig /flushdns`.

**Result:** The direct connection host then resolved — but only to an IPv6 address
(`2406:da18:243:740d:8e98:f:e7a5:8500`). asyncpg failed to connect to it because the
network does not have outbound IPv6 connectivity on port 5432.

**Lesson learned:** Supabase free tier assigns IPv6-only addresses to direct connection
hosts. This is a known Supabase limitation confirmed in their current documentation.

---

### Error 3 — `Tenant or user not found` (first Supabase project, pooler attempts)

**URLs tried:**
- `postgresql+asyncpg://postgres.sznqojlmwaldryfzbmke:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres?ssl=require`
- `postgresql+asyncpg://postgres.sznqojlmwaldryfzbmke:PASSWORD@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?ssl=require`

**Cause (confirmed after research):** Two separate problems:
1. The pooler host was `aws-0-` but the project was assigned to `aws-1-`. Each Supabase
   region has multiple pooler clusters. You must copy the exact host from the project's
   Connect modal, never assume `aws-0-`.
2. asyncpg was mangling the username `postgres.sznqojlmwaldryfzbmke` during URL parsing,
   stripping everything after the dot and sending just `postgres` to the pooler.

**Approaches tried to fix the username parsing:**
- `connect_args={"user": settings.DB_USER, "password": settings.DB_PASSWORD}` with
  separate `DB_USER` and `DB_PASSWORD` env vars
- `URL.create()` from SQLAlchemy to bypass URL string parsing entirely
- Both approaches still hit `Tenant or user not found` because the host was wrong (`aws-0-`)

**Decision:** Delete the first Supabase project and create a new one. The first project
may also have had a pooler initialization issue.

---

### Error 4 — `relation "users" does not exist` (new project, tables not yet created)

**Cause:** Successfully connected to the new Supabase project but the tables had not been
created yet. This was actually the first successful connection.

**Fix:** Created all tables via Supabase SQL Editor.

---

### Error 5 — `column "student_mode" of relation "student_profiles" does not exist`

**Cause:** The SQL used to create `student_profiles` in the first attempt was the same
SQL from the original Supabase project (first attempt). That SQL was missing several
columns that the SQLAlchemy model has — specifically `student_mode` and others. The
model was read incorrectly.

**Fix:** Read the exact model from `backend/app/models/profile.py` via knowledge base
search, then rebuilt the SQL to match every column exactly.

---

### Error 6 — `column "student_mode" of relation "student_profiles" does not exist` (persisting)

**Cause:** The SQL was corrected and run in SQL Editor, but the `DROP TABLE ... CASCADE`
also ran in the same block, dropping and recreating the table. The server was still
running and had the old table cached. The server needed to be restarted.

**Fix:** Restarted uvicorn server.

---

### Error 7 — `column "created_at" of relation "messages"` (discovered during schema audit)

**Cause:** The first SQL for the `messages` table used `created_at` as the timestamp
column name. The SQLAlchemy model uses `timestamp` (exact name matters — SQLAlchemy
generates INSERT statements using the Python attribute name which maps to the DB column name).

**Fix:** Dropped and recreated messages table with correct column name `timestamp`.

---

## PROCESS LESSONS FOR FUTURE SESSIONS

1. **Never assume the Supabase pooler host.** Always copy it from the project's Connect
   modal. The host format is `aws-N-REGION.pooler.supabase.com` where N varies by project.

2. **Supabase free tier direct connections are IPv6 only.** On IPv4-only networks (common
   in Pakistan), always use the Session Pooler.

3. **asyncpg + Supabase Session Pooler requires `NullPool` and `statement_cache_size=0`.**
   Without these, prepared statement errors or connection rejections occur. This is a
   known incompatibility documented in Supabase's community issues.

4. **`alembic upgrade head` cannot run against Supabase via asyncpg.** Use SQL Editor
   to apply schema changes manually. Always run the SQL verification query afterward
   to confirm the schema matches the models.

5. **When building SQL manually, read the SQLAlchemy model files directly** — not the
   Alembic migration file, which may be stale. The model files are always current.

6. **The messages table column is named `timestamp`, not `created_at`.** This is
   unusual (most tables use `created_at`) and caused a failed insert during testing.

7. **Always use the public schema filter** when querying `information_schema.columns`.
   Without `table_schema = 'public'`, Supabase's internal tables (`auth.users`,
   Realtime's `messages`) pollute the results with dozens of extra columns.

---

## COMMIT

```bash
git add backend/app/core/database.py
git commit -m "fix(database): use NullPool and statement_cache_size=0 for Supabase session pooler"
git push origin main
```

Only `database.py` was changed in the codebase. The `.env` file is gitignored and
contains the Supabase credentials — it must be set manually on each machine.

---

*Log written: April 20, 2026*
*Architecture Chat v4 session — Supabase migration task*

---

## DEMO AND DEPLOYMENT CONTEXT

### How Khuzzaim connects for testing

Khuzzaim does not need his own backend or his own database to test the Flutter app.
He connects his Flutter app to Waqas's backend, which runs on Waqas's machine and
connects to the shared Supabase instance. This is the correct setup for all team
testing before deployment.

The only scenario where the missing `curriculum_level` Alembic migration causes a
problem is if Khuzzaim clones the repo and sets up his own local backend with a
fresh database. In that case `alembic upgrade head` would create `student_profiles`
without `curriculum_level` and the grades endpoint would fail. As long as he is
using Waqas's backend and Supabase, there is no issue.

To expose Waqas's local backend to Khuzzaim's device, use ngrok as documented in
`docs/00_architecture/KHUZZAIM_SETUP_GUIDE.md`. ngrok gives a public HTTPS URL
that tunnels to `localhost:8000`.

### Running the app on a phone or browser today

The app cannot be accessed via a public URL or installed from a store yet. Current
state:

- Backend runs on Waqas's laptop at `localhost:8000` — not publicly accessible
  without ngrok
- Flutter app runs via `flutter run` on a connected device or Chrome — not deployed

For the April 29 demo the setup is: Waqas runs the backend on his laptop (connected
to Supabase), exposes it via ngrok, and Khuzzaim runs Flutter pointed at the ngrok URL.

### Production deployment path (post-demo)

When the system is ready for the viva or beyond, the deployment path is:

**Backend:**
Deploy FastAPI to a cloud platform such as Render, Railway, or fly.io. The server
runs 24/7 at a permanent HTTPS URL. Supabase stays as is — it is already hosted.
The only change needed is updating the Flutter base URL from the ngrok URL to the
permanent API URL.

Recommended for viva: Render free tier. Deploy from GitHub, auto-deploys on push
to main, gives a permanent URL like `https://fyp-career-guidance.onrender.com`.

**Flutter Web (browser):**
Run `flutter build web` to produce a static web build. Deploy to Netlify, Vercel,
or Firebase Hosting. Users open a URL in any browser — no download needed.

**Flutter Android (Play Store):**
Run `flutter build apk --release`, sign the APK, upload to Google Play Console.
Requires a one-time $25 Google Play developer account fee.

**Flutter iOS (App Store):**
Requires a Mac, Xcode, and Apple Developer Program membership ($99/year).
Out of scope for this FYP unless specifically required.

**For the viva:** A working demo on a phone or browser via ngrok or Render is
sufficient. Full store deployment is post-FYP scope.
