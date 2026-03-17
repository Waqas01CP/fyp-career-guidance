# FYP: AI-Assisted Academic Career Guidance System

An AI-powered career guidance system for Pakistani secondary school students in Karachi.
Recommends HEC-recognized bachelor's degrees from the top 20 Karachi universities based on
RIASEC interest profile, academic marks, capability assessment, budget, and market outlook.

## Team
| Member | Role |
|---|---|
| Waqas | Backend — FastAPI, LangGraph, PostgreSQL |
| Fazal | Data — universities.json, lag_model.json, affinity_matrix.json |
| Khuzzaim | Frontend — Flutter (Android + Web), assessment_questions.json, testing |

## Milestones
- **April 20** — 50% working demo (profiling + recommendations + follow-up chat)
- **June 10–15** — Full system, viva-ready

## Quick Start

### Backend
```bash
cd backend
cp .env.example .env          # fill in your API keys
docker-compose up -d          # start PostgreSQL
pip install -r requirements.txt
alembic upgrade head          # create tables
uvicorn app.main:app --reload  # start server at localhost:8000
```

### Frontend
```bash
cd frontend
flutter pub get
flutter run -d chrome         # web
flutter run                   # connected device
```

## Architecture
See `CLAUDE.md` for all locked architectural decisions.
See `docs/` for SRS, SDD, and thesis documents.

## Sprint Plan
See `CLAUDE.md` — Sprint 1 (Foundation), Sprint 2 (Profiling), Sprint 3 (Reasoning), Sprint 4 (Polish).
