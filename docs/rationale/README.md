# FYP System Rationale Documentation

This folder documents the **why** behind every major decision in the
AI-Assisted Academic Career Guidance System. It exists for three purposes:

1. **Viva defense** — answer any "why did you choose X" question from examiners
2. **Written report** — feeds directly into the FYP written report sections
3. **Future development** — anyone joining understands the reasoning, not just the code

---

## When to Add a File

A rationale file is written **immediately** when a major component is completed
and committed. Not retrospectively. Architecture Chat produces these.

**Triggers for a new file or addition to existing file:**
- A new component completed (e.g. Script B done and committed)
- A significant architectural decision made or changed
- A deviation from original design with a reason
- An instrument, tool, or approach adopted or rejected
- A phase completed

**Does NOT trigger a rationale entry:**
- Minor bug fixes
- Formatting or style changes
- Adding a single field to a schema
- Routine test additions

---

## File Index

### system/
| File | Contents | Status |
|---|---|---|
| agentic_ai_and_langgraph.md | ML rejection, LangGraph choice, explainability, AsyncPostgresSaver | ✅ Complete |

### assessment/
| File | Contents | Status |
|---|---|---|
| riasec_and_3d_model.md | Holland 1997, Prediger projection, prestige axis, tier system | ✅ Complete |
| kcis.md | SII rejection, custom instrument, 24 sub-scales | ✅ Complete |
| caas_vna_cddq_bigfive.md | CAAS-5-SF, VNA TWA, hybrid CDDQ, Big Five selection | ✅ Complete |
| rejected_instruments.md | MBTI, EQ-i Youth, dropped Big Five dimensions | ✅ Complete |

### pipeline/
| File | Contents | Status |
|---|---|---|
| nodes_and_routing.md | All 6 nodes, route_after_profiler, tier-aware ProfilerNode | ✅ Complete |

### data_files/
| File | Contents | Status |
|---|---|---|
| json_knowledge_base.md | affinity_matrix, lag_model, universities, FutureValue, ARS | ✅ Complete |
| assessment_questions.md | Question format, Roman Urdu, time limits | ⏳ Pending v6 |

### scraper/
| File | Contents | Status |
|---|---|---|
| linkedin_scraper_pipeline.md | Full A-D pipeline, all design decisions | ✅ Complete |

### market/
| File | Contents | Status |
|---|---|---|
| pakistani_market_context.md | CS vs SE, prestige, title conventions, Gulf demand | ✅ Complete |

### infrastructure/
| File | Contents | Status |
|---|---|---|
| deployment_and_database.md | Supabase, Alembic, Render, JWT, Flutter/Riverpod | ✅ Complete |

---

## Pending Files (to be written in v6 and beyond)

- assessment_questions.md — after assessment questions are finalized (Phase 1B)
- Any Phase 2 node update rationale
- Script C and D rationale (after those complete in v6)
- Phase 1A/1B data decisions

---

*Started: May 2026 — Architecture Chat v5*
*Maintained by: Architecture Chat (each version)*
