# Render Deployment Log
## FYP: AI-Assisted Academic Career Guidance System
### Date: April 21, 2026
### Author: Architecture Chat v4 + Waqas
### Purpose: Complete record of Render cloud deployment of FastAPI backend

---

## WHAT WAS DEPLOYED

The FastAPI backend for the FYP Career Guidance System was deployed to Render's
cloud platform. This makes the backend accessible from anywhere on the internet
without requiring Waqas's laptop to be running.

**Live URL:** `https://fyp-career-guidance-api.onrender.com`

---

## WHY RENDER

Three platforms were evaluated: Render, Railway, and Fly.io.

- **Railway** was eliminated — no free tier since 2023, replaced with a one-time
  $5 trial credit only.
- **Fly.io** was eliminated — requires Docker knowledge and a CLI-first approach,
  more complex than needed for this project.
- **Render** was selected — free tier available, simplest GitHub auto-deploy,
  native Docker support, FastAPI is officially supported.

**Free tier limitations accepted:**
- Spins down after 15 minutes of inactivity
- First request after spin-down takes ~50 seconds (cold start)
- 512MB RAM, 0.1 CPU
- No persistent disk (not needed — data is on Supabase)

For the demo and viva, the spin-down is manageable — send one warm-up request
before showing the demo. If performance becomes an issue, upgrade to $7/month
Starter plan.

---

## WHY NOT LOCAL / NGROK

Before Render, the only option for Khuzzaim to test against the real backend was:
1. Waqas runs uvicorn on his laptop
2. Waqas runs ngrok to expose it
3. Waqas shares the ngrok URL with Khuzzaim each session
4. The URL changes every session on the free ngrok tier

With Render:
- Khuzzaim uses `https://fyp-career-guidance-api.onrender.com` permanently
- No coordination needed
- Waqas's laptop can be off
- Demo day has no single point of failure

---

## RENDER CONFIGURATION

| Setting | Value |
|---|---|
| Service type | Web Service |
| Runtime | Docker |
| GitHub repo | Waqas01CP/fyp-career-guidance |
| Branch | main |
| Region | Singapore (ap-southeast-1) |
| Root Directory | backend |
| Dockerfile Path | . (default, relative to Root Directory) |
| Instance type | Free |
| Health Check Path | /health |
| Build Filter | backend (only redeploy on backend/ changes) |
| Auto-Deploy | On Commit |

---

## DOCKERFILE USED

The existing `backend/Dockerfile` was used without any changes:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

No Procfile, no render.yaml, no start command override was needed. Render
detected the Dockerfile automatically and used the CMD directly.

---

## ENVIRONMENT VARIABLES SET ON RENDER

All variables from `backend/.env` were added via the Render dashboard
Environment Variables section. The following were added:

```
DATABASE_URL=postgresql+asyncpg://postgres.oialkebjsalutgwaguct:[PASSWORD]@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres
SECRET_KEY=[SECRET]
JWT_ALGORITHM=HS256
JWT_EXPIRY_MINUTES=60
GEMINI_API_KEY=[SECRET]
LLM_MODEL_NAME=gemini-3.1-flash-lite-preview
LANGCHAIN_TRACING_V2=false
LANGCHAIN_PROJECT=fyp-career-guidance
APP_ENV=production
```

`LANGCHAIN_API_KEY` was intentionally omitted — LangSmith tracing is off
(`LANGCHAIN_TRACING_V2=false`) so the key is not needed.

The `.env` file on the local machine is gitignored and was never committed.
Credentials exist only in the local `.env` and in Render's secure environment
variable storage.

---

## BUILD PROCESS — WHAT HAPPENED

1. Render detected the Dockerfile in `backend/`
2. Docker build started — downloaded python:3.12-slim base image
3. pip installed all packages from requirements.txt — took ~42 seconds
4. All packages installed successfully including:
   - fastapi, uvicorn, sqlalchemy, asyncpg
   - langgraph, langgraph-checkpoint-postgres
   - langchain-core, langchain-google-genai, langchain-anthropic
   - psycopg, psycopg-binary (for AsyncPostgresSaver)
   - All other dependencies
5. Docker image built and exported — took ~102 seconds
6. Image pushed to Render's registry — `Upload succeeded`
7. Container started — uvicorn running on 0.0.0.0:8000
8. Health check passed — `GET /health HTTP/1.1 200 OK`
9. Service marked live — `==> Your service is live 🎉`

Total build time: approximately 8 minutes first time.
Subsequent deploys will be faster due to Docker layer caching.

---

## BUILD WARNING — NOT AN ERROR

During the pip install step, this warning appeared:

```
WARNING: Running pip as the 'root' user can result in broken permissions
and conflicting behaviour with the system package manager
```

This is a standard Docker warning that appears in virtually every Docker
deployment. It does not cause any problems and can be safely ignored.

---

## TESTING — CONFIRMED WORKING

### Test 1 — Health endpoint
```powershell
Invoke-WebRequest -Uri "https://fyp-career-guidance-api.onrender.com/health" -UseBasicParsing
```
Response:
```
StatusCode : 200
Content    : {"status":"ok","service":"fyp-career-guidance-api"}
```

### Test 2 — Register endpoint (writes to Supabase)
```powershell
Invoke-WebRequest -Uri "https://fyp-career-guidance-api.onrender.com/api/v1/auth/register" `
  -Method POST `
  -Headers @{"Content-Type"="application/json"} `
  -Body '{"email": "rendertest@test.com", "password": "test1234"}' `
  -UseBasicParsing
```
Response:
```
StatusCode : 201
Content    : {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...","token_type":"bearer"}
```

Both tests confirmed. The deployed backend connects to Supabase correctly and
writes data. The row was created in Supabase's `users`, `student_profiles`, and
`chat_sessions` tables.

---

## DEPLOYMENT ARCHITECTURE — FINAL STATE

```
Flutter App (phone/browser)
         ↓ HTTPS
https://fyp-career-guidance-api.onrender.com
         ↓ PostgreSQL (Session Pooler)
Supabase — aws-1-ap-southeast-1.pooler.supabase.com:5432
```

All three layers are now cloud-hosted. No laptop dependency for any part of
the system during testing or demo.

---

## AUTO-DEPLOY BEHAVIOUR

Every push to the `main` branch on GitHub triggers an automatic Render
redeploy — but only if files inside `backend/` changed (Build Filter).

Pushes that only change `frontend/`, `docs/`, `design/`, or `logs/` will
NOT trigger a backend redeploy. This prevents unnecessary rebuilds when
Khuzzaim pushes frontend changes.

Redeploy time: approximately 3-5 minutes after a push (faster than first
deploy due to Docker layer caching).

---

## HOW TO WAKE THE SERVICE AFTER INACTIVITY

Render free tier spins down after 15 minutes of no traffic. To wake it:

Simply send any HTTP request — opening the health URL in a browser works:
`https://fyp-career-guidance-api.onrender.com/health`

The service wakes in approximately 50 seconds. No dashboard action needed.
Before any demo, send this request first and wait for the 200 response before
showing the demo.

---

## SUPABASE INACTIVITY WARNING

Supabase free tier pauses projects after 1 week of inactivity. If the project
is unused for a week, the database connection will fail.

To prevent this: log into supabase.com once a week and open the project.
Or upgrade to Supabase Pro ($25/month) before the viva.

If the project is already paused when you try to use it:
1. Go to supabase.com
2. Click the project
3. Click "Restore project"
4. Wait 2 minutes
5. Done — DATABASE_URL does not change

---

## SECURITY NOTES

### Credentials exposed in chat
During the Supabase setup session (April 20) and this session (April 21),
the following credentials appeared in plain text in the Architecture Chat
conversation:
- Supabase database password
- Gemini API key
- SECRET_KEY (JWT signing key)

**Action required after demo:** Rotate all three credentials.
- Supabase: Database → Settings → Reset password → update on Render
- Gemini: Google AI Studio → delete key → create new → update on Render
- SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"` →
  update on Render (note: rotating SECRET_KEY invalidates all existing JWTs —
  all logged-in users will need to log in again)

### CORS — action required before Flutter Web deployment
`backend/app/main.py` currently allows these origins:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:8080",
    "http://localhost:8081",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8080",
]
```

When Flutter Web is deployed (Netlify, Vercel, etc.), add that URL to this
list and push to main. Render will auto-redeploy. Without this, browser-based
Flutter Web requests will be blocked by CORS.

Flutter Android/iOS apps are not affected by CORS — only browser-based requests.

### CORS — Android vs Web behaviour (important distinction)

**Flutter Android APK — NOT affected by CORS.**
Native Android apps make HTTP requests directly through the OS network stack.
The OS does not enforce CORS. Khuzzaim can install the APK on any phone and
call `https://fyp-career-guidance-api.onrender.com` immediately with no
CORS configuration needed. This covers the April 29 demo if shown on a phone.

**Flutter Web in browser — IS affected by CORS.**
When Flutter is built as a web app and opened in Chrome or any browser, the
browser enforces CORS. It checks whether the backend explicitly allows requests
from the frontend's domain. If the Flutter Web URL is not in `allow_origins`
in `main.py`, the browser blocks all API requests — even though the backend
is running correctly.

**Current state:** `allow_origins` in `main.py` contains only localhost origins.
This is fine for:
- Flutter Android APK (phone) — always works, CORS irrelevant
- `flutter run -d chrome` locally — works, localhost is already allowed

This will break for:
- Flutter Web deployed to Netlify, Vercel, or any public URL

**Action required when Flutter Web is deployed:**
Add the deployed Flutter Web URL to `allow_origins` in `main.py`, commit,
and push. Render auto-redeploys in 3-5 minutes. Without this step, the web
version of the app will fail silently in the browser — the API calls return
nothing and the user sees no error message, just a frozen UI.

### What is secure
- JWT implementation: correct (HS256, 60min expiry, sub=user_id)
- Bcrypt: correct (direct bcrypt library, not passlib)
- Rate limiting: 10 req/min per IP on /chat/stream
- PII scrubbing: phone and CNIC regex in LLM nodes
- Tenant isolation: user_id always from JWT, never from request body
- Supabase SSL: enforced via `ssl=require` in DATABASE_URL

---

## LOCAL DEVELOPMENT NOTE — Windows uvicorn command

After the core graph was wired (AsyncPostgresSaver uses psycopg3), the local
uvicorn start command changed. psycopg3 requires SelectorEventLoop on Windows,
but Python 3.8+ defaults to ProactorEventLoop.

**Always run uvicorn locally on Windows with:**
```bash
uvicorn app.main:app --reload --loop asyncio
```

**NOT:**
```bash
uvicorn app.main:app --reload
```

Without `--loop asyncio`, the server will fail at startup on Windows when
AsyncPostgresSaver tries to initialize the psycopg3 connection. The error
will appear in the lifespan startup block.

On Render (Linux) and Mac (Linux-based), this flag is not needed. The
Dockerfile CMD does not include it and works correctly on Render.

This was documented in the core graph session log
(`logs/claude-code-2026-04-20-15-00-core-graph.md` — Bug 2 section) but
is easy to forget when starting a new local development session.

---

## PENDING TASKS

| Task | Owner | Priority |
|---|---|---|
| Rotate credentials (Supabase, Gemini, SECRET_KEY) | Waqas | After demo |
| Add Flutter Web URL to CORS allow_origins | Waqas | When Flutter Web deployed |
| Fix Alembic migration missing curriculum_level | Waqas/Backend Chat | After demo |
| Frontend screens — all 16 need to be built | Khuzzaim/Frontend Chat | URGENT — demo April 29 |
| Data files — universities, lag_model, affinity_matrix | Fazal/Data Chat | URGENT — demo April 29 |
| assessment_questions.json | Khuzzaim | URGENT — demo April 29 |

---

## COMMIT REQUIRED

No code changes were made during this deployment. Everything was configured
via the Render dashboard. No commit needed.

The permanent backend URL to share with the team:
`https://fyp-career-guidance-api.onrender.com`

---

*Log written: April 21, 2026*
*Architecture Chat v4 session — Render deployment task*