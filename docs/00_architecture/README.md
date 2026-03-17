# Architecture Documents

This folder contains all locked architecture decisions for the FYP system.

## Point Files (add these from the Claude project knowledge base)

Download each from the Claude project and place them here:

| File | Contents |
|---|---|
| `POINT_1_FASTAPI_STRUCTURE_v2_1.md` | FastAPI app structure, endpoint definitions, onboarding screens |
| `POINT_2_LANGGRAPH_DESIGN_v2_0.md` | LangGraph agent pipeline, node logic, scoring formulas |
| `POINT_3_DATABASE_SCHEMA_v1_4.md` | All 6 tables, JSONB schemas, Pydantic models |
| `POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md` | JSON file schemas, field definitions, examples |
| `POINT_5_API_SURFACE_v1_2.md` | Complete API contract for all 9 endpoints |
| `POINT_6_REPO_STRUCTURE_v1_0.md` | Definitive repository folder structure |
| `RIASEC_QUIZ_QUESTIONS_v1_1.md` | All 60 quiz questions with Roman Urdu translations |

## Setup Guides (already in this folder)

- `WAQAS_SETUP_GUIDE.md` — Backend environment setup, JWT explanation, daily workflow
- `FAZAL_DATA_GUIDE.md` — How to populate all three JSON data files correctly

## Priority

If any of these documents conflict with `CLAUDE.md` at the repo root:
CLAUDE.md wins for decisions. Point files win for implementation detail.
