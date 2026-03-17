# Contributing Guide
## FYP: AI-Assisted Academic Career Guidance System

Read `CLAUDE.md` before starting any work. It is the single source of truth.

---

## Team

| Member | Area |
|---|---|
| Waqas | All `backend/` Python code |
| Fazal | Data files in `backend/app/data/` |
| Khuzzaim | All `frontend/` Flutter code, `assessment_questions.json`, testing |

---

## Daily Workflow

### Starting work

```bash
git pull origin main          # always pull first
git checkout -b feat/yourname-description
# example: git checkout -b feat/waqas-filter-node
```

### Saving work

```bash
git add -A
git commit -m "feat: short description of what you did"
git push origin feat/yourname-description
```

### Getting your work into main

1. Go to GitHub → your repo → **Pull Requests** → **New Pull Request**
2. Select your branch as source, `main` as target
3. Write a short description of what you changed
4. Assign at least one other team member to review
5. After approval, click **Merge**
6. Delete the branch after merging (GitHub gives you a button for this)

---

## Before merging anything that affects another person

Drop a file in `team-updates/` before the merge. Format:

```
team-updates/YYYY-MM-DD-<type>-<description>.md
```

Types:
- `schema-change` — any Alembic migration → Khuzzaim needs to know
- `api-change` — any endpoint request/response shape change → Khuzzaim needs to know
- `data-change` — any JSON file structural change → Waqas and Khuzzaim need to know
- `config-change` — any constant in `config.py` affecting scoring or quiz → all need to know

Example filename: `2026-03-20-api-change-added-session-id-to-chat-request.md`

---

## Commit message format

```
feat: add FilterNode eligibility logic
fix: correct DATA_DIR path in fetch_fees
chore: update universities.json with 5 new entries
test: add persona tests for matric_planning mode
docs: update CLAUDE.md with state management decision
```

---

## Rollback — undoing a merged commit

**Safe rollback (always use this):**
```bash
# Find the merge commit hash on GitHub → Commits page
git revert -m 1 <merge-commit-hash>
git push origin main
```
This creates a new commit that undoes the merge. History is preserved.

**Hard reset (only if no one else has pulled the merge yet):**
```bash
git reset --hard <commit-hash-before-the-merge>
git push --force origin main
```
Check with the team before using `--force`.

---

## Alembic — database schema changes (Waqas only)

```bash
# After changing any model file:
alembic revision --autogenerate -m "describe what changed"
alembic upgrade head

# Post a schema-change file to team-updates/ before pushing
```

Never write raw SQL. Alembic only.

---

## Running the backend

```bash
cd backend
cp .env.example .env        # first time only — fill in your API keys
docker-compose up -d        # start PostgreSQL
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
# API docs at: http://localhost:8000/docs
```

## Running the frontend

```bash
cd frontend
flutter pub get
flutter run -d chrome       # web
flutter run                 # connected device
```

---

## Never do these things

- Never commit directly to `main` — always use a branch and pull request
- Never run `ALTER TABLE` manually — Alembic only
- Never edit `CLAUDE.md` directly — Architecture Chat produces update blocks
- Never hardcode constants that belong in `config.py`
- Never write user_id into request bodies — always read from JWT
