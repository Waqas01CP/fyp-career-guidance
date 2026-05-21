# FYP System Rationale Documentation

This folder is the formal technical reference for the AI-Assisted Academic
Career Guidance System. It documents the *why*, *how*, and *what* behind
every major decision, component, and algorithm.

---

## Purpose

1. **Viva defense** — when an examiner asks "explain your algorithm" or
   "why did you choose this architecture", the answer exists here as a
   formal documented artefact. Not recalled from memory. Opened and shown.
   Documents contain pseudocode, complexity analysis, invariant statements,
   design justification, and system diagrams.

2. **Written FYP report** — these documents feed directly into methodology
   and system design chapters. Written at academic submission standard.

3. **Engineering proof** — formal algorithm specifications, invariant
   analysis, and multi-level diagrams demonstrate that the system was
   designed with rigour, not just built until it worked.

4. **Operational reference** — self-contained. A reader with no prior
   context can understand, operate, maintain, and extend any component
   by reading the relevant document alone.

---

## Documentation Hierarchy

Every component exists at a level in the system hierarchy. Documents
must identify which level(s) they cover and show how each level
connects to the one above.

| Level | What it covers | Example |
|---|---|---|
| Level 1 | Full system — all subsystems and connections | Pre-viva Opus gate check |
| Level 2 | Subsystem — bounded component set, single purpose | LinkedIn Data Pipeline |
| Level 3 | Component — individual script, node, or module | Script C, ExplanationNode |
| Level 4 | Algorithm — formal specification inside a component | Canonical Mapping Algorithm |

A subsystem rationale document covers Levels 2, 3, and 4 in a single
file — subsystem overview, component specifications for every component,
and formal algorithm specifications for every non-trivial algorithm.

---

## Documentation Standard

### What Every Subsystem Document Must Contain

1. **System context diagram** — subsystem as a black box in the Level 1
   system. What feeds into it. What it produces. What depends on it.

2. **Internal component diagram** — all components with data flows,
   file names and formats, trigger conditions, sequential dependencies.

3. **Data flow diagram** — raw input → intermediate representations →
   final output. Every transformation step named and labelled. Every
   file write and read shown.

4. **Component specification** for each component:
   - Purpose (one sentence)
   - Interface contract — exact inputs and outputs with types
   - Operating instructions — how to run, what flags exist, expected
     outputs, what to verify before and after
   - Failure modes — enumerated with symptoms and recovery steps
   - Known limitations — honest, with post-FYP improvement path

5. **Algorithm specification** for each non-trivial algorithm (see below)

All diagrams in ASCII or Mermaid format. Mermaid preferred.

---

### Algorithm Specification Standard

Every non-trivial algorithm must have ALL of the following. Missing any
section means the document is incomplete. This is not a summary — it is
a formal software engineering specification.

#### Name
Precise and unique. Identifies the algorithm distinctly from all others
in the system. Not "the mapping thing" — a full descriptive name.

#### Purpose
One sentence. What problem does this solve and why does it matter in
the context of the system.

#### Input
Every parameter named, typed, and described. Nested structures fully
expanded. Constraints stated explicitly (nullable, bounded, non-empty).
No shorthand. No "a dict of things."

#### Output
Same level of detail as Input. Full type specification.

#### Pseudocode
Formal pseudocode notation. Step-numbered. Not Python. Not prose.
Standard constructs used:

  ←           assignment
  ∈           membership test
  ∅           empty set or empty collection
  ∀           for all / universal quantification
  BEGIN / END block delimiters
  FOR EACH x ∈ collection DO ... END FOR
  IF condition THEN ... ELSE ... END IF
  WHILE condition DO ... END WHILE
  RETURN, CONTINUE, BREAK in capitals

Structure:
  ALGORITHM [Name]
  INPUT:  [param]: [type], ...
  OUTPUT: [type]
  BEGIN
    [numbered steps in formal notation]
    RETURN [output]
  END

#### Complexity
Time complexity and space complexity in O() notation. Define what n
represents. If multiple passes, give complexity per pass and overall.

#### Invariants
Three categories, all mandatory:
  Preconditions  — what must be true before the algorithm runs
  Postconditions — what is guaranteed true after it completes
  Loop invariants — what stays true through each iteration

#### Edge Cases
Enumerated explicitly. For each: the input condition and exactly how
the algorithm handles it. Silently dropped inputs are the most
dangerous defect — they must appear here.

#### Design Rationale
Why this algorithm was chosen. What alternatives were considered and
why they were rejected. What constraints drove the design. Honest about
trade-offs.

---

## When to Write

Write AFTER a component or subsystem is 100% complete and committed.
Not before. Not during.

Implementations change during development. A document written
mid-implementation reflects the initial design, not the final one,
and becomes misleading.

**Trigger:** component or subsystem fully committed and verified →
Architecture Chat produces a Claude Code prompt → document written in
one session → committed alongside the code it describes.

---

## Epistemic Status — NOT Authoritative

Priority order always:
  CLAUDE.md > committed code > current conversation > rationale files

Rationale files describe reasoning correct at the time of writing.
They may be incomplete or outdated if the design changed after
the document was written. Always verify against the actual code.

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
| nodes_and_routing.md | All 6 nodes, route_after_profiler, tier-aware ProfilerNode | ✅ Complete (v1-v4 gaps possible — review before viva) |

### data_files/
| File | Contents | Status |
|---|---|---|
| json_knowledge_base.md | affinity_matrix, lag_model, universities, FutureValue, ARS | ✅ Complete |
| assessment_questions.md | Question format, Roman Urdu, time limits | ⏳ Pending Phase 1B completion |

### scraper/
| File | Contents | Status |
|---|---|---|
| linkedin_scraper_pipeline.md | Full A→D pipeline — Scripts A, B, C, D; all algorithms; all diagrams | ⏳ Pending Script D completion |

### market/
| File | Contents | Status |
|---|---|---|
| pakistani_market_context.md | CS vs SE, prestige, title conventions, Gulf demand | ✅ Complete |

### infrastructure/
| File | Contents | Status |
|---|---|---|
| deployment_and_database.md | Supabase, Alembic, Render, JWT, Flutter/Riverpod | ✅ Complete |

---

## Pending Documents

| Document | Trigger | Owner |
|---|---|---|
| scraper/linkedin_scraper_pipeline.md | Script D complete and committed | Architecture Chat v6 |
| data_files/assessment_questions.md | Phase 1B complete | Architecture Chat |
| Full system Level 1 document | Pre-viva Opus gate check | Opus + Architecture Chat |

---

*Started: May 2026 — Architecture Chat v5*
*Standard updated: May 2026 — Architecture Chat v6*
*Maintained by: Architecture Chat (each version)*