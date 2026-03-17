# Waqas Backend Setup Guide
## Complete step-by-step from zero to running server

---

## PART 1 — Install tools (one time only)

### 1.1 Install Python 3.12
Download from https://www.python.org/downloads/
During installation on Windows: tick "Add Python to PATH" before clicking Install.
Verify: open terminal and run `python --version` — must show 3.12.x

### 1.2 Install Git
Download from https://git-scm.com and accept all defaults.
Verify: `git --version`

### 1.3 Install Docker Desktop
Download from https://www.docker.com/products/docker-desktop/
This runs PostgreSQL locally in a container — no manual PostgreSQL install needed.
After installing, open Docker Desktop and leave it running in the background.
Verify: `docker --version`

### 1.4 Install VS Code
Download from https://code.visualstudio.com
Install the Python extension inside VS Code (Extensions panel → search "Python").

---

## PART 2 — Clone the repo

```bash
git clone https://github.com/your-org/fyp-career-guidance.git
cd fyp-career-guidance
```

---

## PART 3 — Virtual environment

### Why both venv AND .env?
They serve completely different purposes:
- **venv** holds Python packages (fastapi, sqlalchemy, etc.) isolated from your system
- **.env** holds secret values (API keys, DB password) that the app reads at runtime

You need both. They do not replace each other.

### Create and activate the venv

```bash
cd backend
python -m venv venv
```

This creates a `venv/` folder inside `backend/`. It is already in `.gitignore`.

**Activate every time you open a new terminal:**

Windows (Command Prompt):
```
venv\Scripts\activate
```
Windows (PowerShell):
```
venv\Scripts\Activate.ps1
```
Mac/Linux:
```bash
source venv/bin/activate
```

You will see `(venv)` at the start of your prompt when it is active.
Always activate before running any Python, alembic, or uvicorn command.

### Install all packages

With venv active:
```bash
pip install -r requirements.txt
```
Takes 1-3 minutes. Do this once per machine.

---

## PART 4 — Configure environment variables

### Create .env
```bash
# From inside backend/
cp .env.example .env
```

### Fill in .env (open it in VS Code)

**DATABASE_URL** — leave exactly as is. It matches the Docker container settings.
```
DATABASE_URL=postgresql+asyncpg://fyp_user:fyp_password@localhost:5432/fyp_db
```

**SECRET_KEY** — generate a random string and paste it in:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output. Example result: `a3f8c2d1e9b7f4a6c8d2e1f3b5a7c9d0e2f4b6a8c0d2e4f6b8a0c2d4e6f8b0`
Your .env line: `SECRET_KEY=a3f8c2d1e9b7f4a6c8d2e1f3b5a7c9d0e2f4b6a8c0d2e4f6b8a0c2d4e6f8b0`

This key is what signs your JWTs. Keep it secret. Never commit it.

**GEMINI_API_KEY** — get from Google AI Studio:
1. Go to https://aistudio.google.com
2. Sign in with a Google account
3. Click "Get API key" → "Create API key in new project"
4. Copy the key and paste: `GEMINI_API_KEY=AIzaSy...`

Leave everything else as-is for Sprint 1.

**Verify .env is gitignored:**
```bash
git status
```
`.env` must never appear in the output. If it does: `echo ".env" >> .gitignore`

---

## PART 5 — Start PostgreSQL

Make sure Docker Desktop is open and running first. Then from the **repo root** (not backend/):
```bash
docker-compose up -d
```

Verify it is running:
```bash
docker ps
```
Look for a row containing `fyp_postgres` with status `Up`.

Stop when done for the day (optional — data is preserved in Docker volume):
```bash
docker-compose down
```

---

## PART 6 — Create database tables

```bash
cd backend
# venv must be active — you should see (venv) in your prompt
alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> abc123, initial tables
```

Verify tables were created:
```bash
docker exec -it fyp_postgres psql -U fyp_user -d fyp_db -c "\dt"
```
Should list: users, student_profiles, chat_sessions, messages, recommendations, profile_history.

---

## PART 7 — Start the server

```bash
cd backend
# venv must be active
uvicorn app.main:app --reload
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Open browser: `http://localhost:8000/docs`
You should see the FastAPI docs with all 9 endpoints listed.

---

## PART 8 — Understanding the JWT (how it works, not what you implement)

The JWT is already implemented in `core/security.py`. You do not write JWT logic.
Here is what happens so you understand the system:

**When register/login succeeds:**
1. `create_access_token(str(user.id), user.role)` is called
2. Encodes `{"sub": "<user-uuid>", "role": "student", "exp": <60 minutes from now>}`
3. Signs it with SECRET_KEY using HS256 algorithm
4. Returns a string like `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOi...`

**When a protected endpoint is called:**
1. Flutter sends `Authorization: Bearer eyJhbGc...` in the HTTP header
2. `dependencies.py` → `get_current_user()` extracts the token
3. Calls `decode_access_token(token)` — verifies signature, checks expiry
4. Extracts `sub` (the user UUID string)
5. Casts it to a real UUID and queries the DB: `SELECT * FROM users WHERE id = <uuid>`
6. Returns the User object to the endpoint function as `current_user`

**The only things you control:**
- `SECRET_KEY` in `.env` — never share it, never commit it
- `JWT_EXPIRY_MINUTES` — currently 60. Change in `.env` if needed.

**Testing with JWT in the docs page:**
1. POST /api/v1/auth/register → copy the `access_token` from the response
2. Click the green "Authorize" button at top of docs page
3. Type `Bearer <paste token here>` → Authorize
4. Now all protected endpoints work in the docs page

---

## PART 9 — Schema changes (when you modify models)

Whenever you change any file in `backend/app/models/`:
```bash
# venv active, from backend/
alembic revision --autogenerate -m "short description of change"
alembic upgrade head
```

Then post a file to `team-updates/` so Khuzzaim knows the schema changed.
See CONTRIBUTING.md for the format.

---

## PART 10 — Daily startup sequence

```bash
# Terminal 1 — from repo root
docker-compose up -d

# Terminal 2 — from backend/
venv\Scripts\activate        # Windows
# or: source venv/bin/activate  # Mac/Linux
uvicorn app.main:app --reload
```

That is it. Server runs at http://localhost:8000

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'fastapi'` | venv not active | Run `venv\Scripts\activate` |
| `connection refused` | Docker not running | Open Docker Desktop, then `docker-compose up -d` |
| `alembic: Can't locate revision` | Running from wrong directory | Must be inside `backend/` |
| `422 Unprocessable Entity` | Wrong request body format | Check exact field names in /docs |
| `Port 8000 already in use` | Another server running | CTRL+C the other uvicorn |
| `.env not found` | Forgot to copy | Run `cp .env.example .env` |
