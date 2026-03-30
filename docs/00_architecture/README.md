# Architecture Documents

This folder contains all locked architecture decisions for the FYP system.
Read `CLAUDE.md` at the repo root first, then use this folder as your reference library.

---

## Instruction Files (read these during implementation)

| File | Who uses it | Purpose |
|---|---|---|
| `BACKEND_CHAT_INSTRUCTIONS.md` | Waqas + Claude Code | FastAPI rules, schemas, node logic, guardrails |
| `FRONTEND_CHAT_INSTRUCTIONS.md` | Khuzzaim + Claude Code | Flutter architecture, Riverpod patterns, SSE |
| `DATA_CHAT_INSTRUCTIONS.md` | Fazal + Claude Code | JSON file schemas, validation rules |
| `CLAUDE_CODE_RULES.md` | Claude Code | Session rules, hard constraints, log format |
| `SPRINT_PLAN.md` | All team | Task breakdown per sprint, gate conditions |
| `WAQAS_SETUP_GUIDE.md` | Waqas | Backend environment setup, daily workflow |
| `FAZAL_DATA_GUIDE.md` | Fazal | How to populate all three JSON data files |
| `KHUZZAIM_SETUP_GUIDE.md` | Khuzzaim | Flutter setup, Riverpod intro, screen guide |

---

## Point Files (detailed architecture reference)

| File | Contents |
|---|---|
| `POINT_1_FASTAPI_STRUCTURE_v2_1.md` | FastAPI app structure, student modes, assessment architecture |
| `POINT_2_LANGGRAPH_DESIGN_v2_0.md` | LangGraph pipeline, node logic, scoring formulas |
| `POINT_3_DATABASE_SCHEMA_v1_4.md` | All 6 tables, JSONB schemas, exact ORM models |
| `POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md` | JSON file schemas, field definitions, examples |
| `POINT_5_API_SURFACE_v1_2.md` | Complete API contract for all 9 endpoints + SSE protocol |
| `POINT_6_REPO_STRUCTURE_v1_0.md` | Definitive repository folder structure |
| `RIASEC_QUIZ_QUESTIONS_v1_1.md` | All 60 quiz questions with Roman Urdu translations |

---

## Priority

CLAUDE.md wins for decisions. Point files win for implementation detail.
If an instruction file conflicts with a Point file, flag it in Architecture Chat.