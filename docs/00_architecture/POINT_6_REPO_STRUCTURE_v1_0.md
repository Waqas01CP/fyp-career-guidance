# Point 6 — Repository Root Structure
## FYP: AI-Assisted Academic Career Guidance System
### Status: COMPLETE AND LOCKED
### Date: March 2026
### Change Log:
### v1.0 — Initial lock. Definitive repository folder hierarchy.
###         Supersedes the structure in MASTER_EXECUTION_PLAN.md wherever
###         they conflict. Point 1 (FastAPI Structure v2.1) is the
###         authoritative source for the backend/ subtree. Five known
###         conflicts with the Master Plan are resolved here.

---

## PURPOSE

This document defines the exact folder and file structure of the repository
root. Every team member, every Claude Code session, and every chat uses this
as the single reference for where files live.

**Priority:** Where this document conflicts with MASTER_EXECUTION_PLAN.md,
this document wins — it incorporates all decisions made in Points 1–5 which
post-date the Master Plan. Where this document references backend/ subtree
details, Point 1 is the authoritative source.

---

## KNOWN CONFLICTS WITH MASTER_EXECUTION_PLAN.md

Five places where the Master Plan is superseded by locked Point decisions:

| Location | Master Plan (old) | Locked Decision (current) | Source |
|---|---|---|---|
| `backend/app/api/v1/endpoints/` | Had `upload.py` | No `upload.py` — merged into `profile.py` | Point 1 v1.0 |
| `backend/app/schemas/` | `auth_schema.py`, `chat_schema.py`, `profile_schema.py`, `upload_schema.py` | `auth.py`, `chat.py`, `profile.py` only — no `_schema` suffix, no upload file | Point 1 v1.0 |
| `backend/app/agents/nodes/` | 5 nodes (no answer_node) | 6 nodes — `answer_node.py` added | Point 1 v1.4 |
| `backend/app/data/` | 3 JSON files | 4 JSON files — `assessment_questions.json` added | Point 1 v1.0 |
| `scripts/` | Root-level `scripts/` with `seed_db.py` + `setup.sh` | `scripts/` is at `backend/` level, not repo root | Point 1 v1.3 |

---

## DEFINITIVE REPOSITORY STRUCTURE

```
fyp-career-guidance/
│
├── CLAUDE.md                              ← Single source of truth. Read before every session.
├── README.md                              ← Project overview
├── .gitignore                             ← Python, Flutter, Android, Node
├── docker-compose.yml                     ← PostgreSQL local dev container
├── LICENSE
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py                        ← FastAPI app object, router registration, lifespan hooks
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py            ← POST /auth/register, POST /auth/login
│   │   │       │   ├── chat.py            ← POST /chat/stream (SSE, rate-limited)
│   │   │       │   └── profile.py         ← GET /profile/me, POST /profile/quiz,
│   │   │       │                             POST /profile/grades, POST /profile/marksheet,
│   │   │       │                             POST /profile/assessment,
│   │   │       │                             POST /admin/seed-knowledge
│   │   │       └── dependencies.py        ← get_db, get_current_user, require_admin
│   │   │
│   │   ├── agents/
│   │   │   ├── state.py                   ← AgentState TypedDict (12 fields)
│   │   │   ├── core_graph.py              ← LangGraph StateGraph + AsyncPostgresSaver
│   │   │   ├── nodes/
│   │   │   │   ├── supervisor.py          ← Intent classifier, Conditional Edges (7 intents)
│   │   │   │   ├── profiler.py            ← LLM. Conversational profiling.
│   │   │   │   ├── filter_node.py         ← Pure Python. Three output lists.
│   │   │   │   ├── scoring_node.py        ← Pure Python. Weighted scoring + capability blend.
│   │   │   │   ├── explanation_node.py    ← LLM. Generates explanations (up to 4 parts).
│   │   │   │   └── answer_node.py         ← LLM + tools. Fee/market/follow-up queries.
│   │   │   └── tools/
│   │   │       ├── fetch_fees.py          ← Reads universities.json, returns fee structure
│   │   │       ├── lag_calc.py            ← Reads lag_model.json, returns FutureValue + market data
│   │   │       └── job_count.py           ← Rozee.pk scraper + Mustakbil fallback + cached fallback
│   │   │
│   │   ├── services/
│   │   │   ├── auth_service.py            ← JWT generation/validation (60 min), Bcrypt
│   │   │   └── ocr_service.py             ← Gemini Vision marksheet parsing
│   │   │
│   │   ├── models/                        ← SQLAlchemy ORM — how data is STORED
│   │   │   ├── user.py                    ← users table
│   │   │   ├── profile.py                 ← student_profiles table
│   │   │   ├── session.py                 ← chat_sessions table
│   │   │   ├── message.py                 ← messages table
│   │   │   ├── recommendation.py          ← recommendations table
│   │   │   └── profile_history.py         ← profile_history table
│   │   │
│   │   ├── schemas/                       ← Pydantic schemas — how data is TRANSFERRED
│   │   │   ├── auth.py                    ← UserCreate, UserLogin, TokenResponse
│   │   │   ├── chat.py                    ← ChatRequest, SSEEvent
│   │   │   └── profile.py                 ← ProfileOut, QuizSubmission, GradesSubmission,
│   │   │                                     AssessmentSubmission, MarksheetUploadResponse
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                  ← All tunable constants — never hardcode elsewhere
│   │   │   ├── security.py                ← Bcrypt hash/verify, JWT encode/decode
│   │   │   └── database.py                ← SQLAlchemy engine, SessionLocal, Base
│   │   │
│   │   └── data/                          ← JSON knowledge base — app reads at runtime
│   │       ├── universities.json          ← Top 20 Karachi universities + degrees (Fazal)
│   │       ├── lag_model.json             ← FutureValue with 3-layer breakdown (Fazal)
│   │       ├── affinity_matrix.json       ← RIASEC-to-degree affinity scores (Fazal)
│   │       ├── assessment_questions.json  ← 1140 MCQs across 5 subjects × 3 levels (Khuzzaim)
│   │       └── seeds/
│   │           └── backup/                ← Golden Copy — locked before viva, never overwrite
│   │
│   ├── scripts/                           ← Developer/data tools. NOT part of running server.
│   │   ├── compute_future_values.py       ← Fazal runs to recompute FutureValue scores
│   │   └── seed_db.py                     ← Idempotent DB seeder (reads backend/app/data/)
│   │
│   ├── tests/
│   │   ├── test_filter_node.py            ← Khuzzaim: 5 student persona test cases
│   │   └── test_scoring_node.py           ← Khuzzaim: scoring formula verification
│   │
│   ├── alembic/
│   │   ├── versions/                      ← Auto-generated migration scripts
│   │   ├── env.py
│   │   └── script.py.mako
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/                              ← Flutter — single codebase for Android + Web
│   ├── lib/
│   │   ├── main.dart
│   │   ├── screens/
│   │   │   ├── auth/
│   │   │   │   ├── login_screen.dart
│   │   │   │   └── signup_screen.dart
│   │   │   ├── onboarding/
│   │   │   │   ├── riasec_quiz_screen.dart      ← 60 questions, Likert, progress bar
│   │   │   │   ├── grades_input_screen.dart     ← Education level, stream, marks, OCR
│   │   │   │   └── assessment_screen.dart       ← Capability MCQ quiz (12 per subject)
│   │   │   ├── dashboard/
│   │   │   │   └── recommendation_dashboard.dart
│   │   │   ├── chat/
│   │   │   │   └── main_chat_screen.dart
│   │   │   └── profile/
│   │   │       └── profile_screen.dart
│   │   ├── widgets/
│   │   │   ├── university_card.dart        ← rich_ui: university_card event renderer
│   │   │   ├── lag_score_badge.dart        ← Emerging/Peak/Saturated with colour
│   │   │   ├── roadmap_timeline.dart       ← rich_ui: roadmap_timeline event renderer
│   │   │   ├── thinking_indicator.dart     ← 3 dots + status label (Future Purple)
│   │   │   ├── ocr_verification_modal.dart ← Blocks progress; inline editable fields
│   │   │   └── mismatch_notice.dart        ← Amber banner when mismatch_notice non-null
│   │   ├── services/
│   │   │   ├── api_service.dart            ← Base HTTP client, base URL, auth headers
│   │   │   ├── auth_service.dart           ← Login, register, flutter_secure_storage
│   │   │   └── sse_service.dart            ← SSE stream parser (status/chunk/rich_ui)
│   │   ├── models/
│   │   │   ├── student_profile.dart        ← Mirrors ProfileOut from backend
│   │   │   ├── recommendation.dart         ← university_card payload shape
│   │   │   └── chat_message.dart
│   │   └── providers/                     ← State management (Provider or Riverpod — TBD)
│   │       ├── auth_provider.dart
│   │       ├── chat_provider.dart
│   │       └── profile_provider.dart
│   ├── assets/
│   │   ├── images/
│   │   └── fonts/
│   ├── test/
│   ├── pubspec.yaml
│   └── README.md
│
├── docs/
│   ├── 01_deliverables/                   ← SRS, SDD, Thesis PDFs
│   ├── 02_research/                       ← Market research, policy references, citations
│   └── 03_meeting_logs/                   ← Supervisor meeting notes
│
├── design/
│   ├── architecture/                      ← UML, ERD, LangGraph flow diagrams
│   ├── figma_exports/                     ← UI design exports
│   └── assets/                            ← Logo, colour palette, typography guide
│
├── logs/                                  ← Claude Code session logs (per session, per date)
│   └── .gitkeep
│
└── team-updates/                          ← Cross-team notifications
    └── .gitkeep
```

---

## FILE OWNERSHIP

| File / Folder | Owner | Notes |
|---|---|---|
| `backend/` — all Python code | Waqas | FastAPI, LangGraph, SQLAlchemy, Alembic |
| `backend/app/data/universities.json` | Fazal | Data Chat |
| `backend/app/data/lag_model.json` | Fazal | Data Chat + `compute_future_values.py` |
| `backend/app/data/affinity_matrix.json` | Fazal | Data Chat |
| `backend/app/data/assessment_questions.json` | Khuzzaim | 1140 questions, 3 levels × 5 subjects × 76 |
| `backend/scripts/compute_future_values.py` | Fazal | Run once per semester, not by server |
| `backend/scripts/seed_db.py` | Waqas | Idempotent UPSERT from data/ files |
| `backend/tests/` | Waqas + Khuzzaim | Waqas writes test harness, Khuzzaim writes test cases |
| `frontend/` — all Dart/Flutter code | Khuzzaim | Flutter codebase — Android + Web |
| `docs/` | Khuzzaim | SRS, SDD, thesis, meeting logs |
| `CLAUDE.md` | All (via Architecture Chat) | Never edited directly — Architecture Chat produces update blocks |

---

## TEAM-UPDATES PROTOCOL

Any change that affects another team member's work requires a file committed to
`team-updates/` before merging to `main`. Format: `YYYY-MM-DD-<type>-<description>.md`.

Types:
- `schema-change` — any Alembic migration (Waqas → Khuzzaim needs to know)
- `api-change` — any endpoint request/response shape change (Waqas → Khuzzaim)
- `data-change` — any JSON file structural change (Fazal → Waqas + Khuzzaim)
- `config-change` — any constant change in `config.py` that affects scoring or quiz

---

## WHAT DOES NOT EXIST IN THIS REPO

The following are explicitly absent by locked decision — do not create them:

| Missing item | Why absent |
|---|---|
| `backend/app/api/v1/endpoints/upload.py` | Merged into `profile.py` as `POST /profile/marksheet` |
| `backend/app/schemas/upload_schema.py` | `MarksheetUploadResponse` lives in `schemas/profile.py` |
| `backend/app/schemas/auth_schema.py` etc. | No `_schema` suffix — files are `auth.py`, `chat.py`, `profile.py` |
| `data/seeds/conflict_rules.json` | MVP-3 parent mediation permanently deferred |
| Root-level `scripts/` | Scripts are at `backend/scripts/` |
| `backend/app/agents/nodes/university_advisor.py` | Replaced by `answer_node.py` |
| `backend/app/agents/nodes/market_analyst.py` | Replaced by `answer_node.py` |

---

## DECISIONS LOCKED IN POINT 6

| Decision | Choice |
|---|---|
| Repo root folder name | `fyp-career-guidance/` |
| scripts/ location | `backend/scripts/` — never root-level |
| Schema file naming | No `_schema` suffix — `auth.py`, `chat.py`, `profile.py` |
| upload.py | Does not exist — marksheet endpoint in `profile.py` |
| upload_schema.py | Does not exist — `MarksheetUploadResponse` in `schemas/profile.py` |
| answer_node.py | Exists — replaces university_advisor.py and market_analyst.py |
| assessment_questions.json | In `backend/app/data/` — 1140 questions total |
| seeds/backup/ | In `backend/app/data/seeds/backup/` — Golden Copy, never overwrite |
| team-updates/ protocol | Required before any cross-team impacting merge to main |
| conflict_rules.json | Permanently absent — MVP-3 deferred |

---

*Point 6 v1.0 — March 2026 (initial lock — definitive repository structure)*
