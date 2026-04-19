# Sprint 2–3 Build Process
### FYP: AI-Assisted Academic Career Guidance System
### Established: April 2026

---

## Purpose

This file documents the mandatory build, review and test process for every
Sprint 2 and Sprint 3 backend component. Every Claude Code session building
a node or wiring component must follow this process exactly.

---

## Component Build Order

| Step | Component | File | Model | Effort | Prerequisite |
|---|---|---|---|---|---|
| 1 | FilterNode | agents/nodes/filter_node.py | Sonnet | Medium | universities.json has NED data |
| 2 | ScoringNode | agents/nodes/scoring_node.py | Sonnet | Medium | lag_model.json + affinity_matrix.json have NED field stubs |
| 3 | ProfilerNode | agents/nodes/profiler.py | Sonnet | High | FilterNode + ScoringNode verified |
| 4 | SupervisorNode | agents/nodes/supervisor.py | Sonnet | Medium | ProfilerNode verified |
| 5 | AnswerNode | agents/nodes/answer_node.py | Sonnet | Medium | SupervisorNode verified |
| 6 | ExplanationNode | agents/nodes/explanation_node.py | Sonnet | High | ScoringNode verified |
| 7 | core_graph.py wiring | agents/core_graph.py | Sonnet | High | All nodes verified |

Do not begin a step until the previous step has passed Architecture Chat review.

---

## Mandatory Six-Phase Process Per Component

### Phase 1 — Plan
Write a full implementation plan before writing any code. Cover:
- Every function, its inputs and outputs
- Loop and control flow structure
- Output shape and which AgentState fields are written
- Explicit field name verification against actual JSON data files

Review the plan against the relevant Point 2 section. State explicitly that
review is complete and no incoherencies were found, OR list and resolve each one.
Only proceed after this statement.

### Phase 2 — Execute
Implement exactly the plan. If during implementation a necessary improvement or
upgrade becomes apparent (e.g., a missing edge case, a more robust error handler),
implement it — but flag it explicitly in the Phase 6 log under a "Deviations from
Plan" section. Never make improvements silently. Never make changes to files outside
the component being built.

### Phase 3 — Self-review at component level
Re-read every line of code written. Check:
- Every dict key access against actual data file structure
- Output field names against Point 3 roadmap_snapshot schema
- AgentState fields written against state.py TypedDict exactly
Fix all discrepancies before proceeding.

### Phase 4 — Integration boundary check
Read the next component's input spec in Point 2. Confirm field by field that
every field the next component reads is present in this component's output.
This is a document comparison, not execution. Fix any gaps before proceeding.

### Phase 5 — Test
Write pytest tests in backend/tests/test_{component}.py.
Use realistic simulated data — full student profile, not minimal stubs.
All tests must pass before writing the log.

### PHASE 5b — LLM OUTPUT LOG (LLM nodes only)

For every LLM node (ProfilerNode, SupervisorNode, AnswerNode, ExplanationNode),
Claude Code must capture a raw output log immediately after Phase 5 tests pass.

This is separate from the session log. It records actual model outputs word-for-word
so Architecture Chat can review real behaviour, compare models, and diagnose issues
without re-running the node.

**File location:** `logs/llm-output-[nodename]-[YYYY-MM-DD].md`

**What to capture:**
- The exact model string used
- The system prompt sent (full text, no truncation)
- For each test case: the exact human input and the exact raw LLM response
  before any parsing — word for word, as received
- Any JSON parsing errors or fallbacks triggered
- The final extracted fields after merging

**For integrated runs (node X → node Y):** capture the output of each LLM node
in sequence — what went in, what came out, exactly as-is.

This log is committed alongside the session log. It is the reference for:
- Comparing model behaviour before and after a model switch
- Diagnosing prompt failures
- Architecture Chat review of actual LLM compliance

### Phase 6 — Log
Write to logs/claude-code-YYYY-MM-DD-HH-MM-{component}.md.
The log must be detailed enough that someone reading it cold — with no other
context — can reconstruct exactly what was planned, what was built, what was
checked, what passed and what failed, and what remains uncertain. This is the
primary continuity mechanism between sessions.

Log must include:
- Plan summary (what was planned in Phase 1)
- Deviations from plan (any improvements or additions made during Phase 2)
- Self-review findings (Phase 3 — discrepancies found and fixed, or "none found")
- Integration boundary check result (Phase 4 — field-by-field confirmation)
- Test results (exact pytest output, pass/fail per test, fixes made)
- Known failure modes (derivable from code only — no speculation)
- What Architecture Chat should review (specific functions, judgment calls, anything
  where the implementer made a decision not explicitly covered by the Point files)

Update logs/README.md immediately after.

---

## Three-Layer Review Loop

After each component's Claude Code session:

1. **Claude Code self-review** — happens during Phase 3 and 4 inside VS Code
2. **Architecture Chat review** — Waqas pastes the session log and key functions
   into Architecture Chat. Architecture Chat cross-checks against full Point file
   context, catches cross-document inconsistencies, and gives green/red.
3. **Test output review** — test results reviewed here if any unexpected behaviour

**Green from Architecture Chat + Green from Backend Chat = proceed to next component.**
**Red from either = Claude Code corrects, re-tests, re-logs. Loop repeats.**

Architecture Chat reviews first (cross-document consistency, field names, integration
boundaries, AgentState correctness). Backend Chat reviews second (code logic, Python
implementation, error handling, whether the code does what the spec says line by line).
Both must give green before the next component begins.

Do not begin the next component until Architecture Chat gives green.

---

## Known Failure Mode Logging Rules

In the session log, Claude Code logs only failure modes that are:
- Directly derivable from a specific line in the code just written
- Pointing to a real code path (key access, division, file read, etc.)
- Documented with: line number, trigger condition, error or silent wrong result

Claude Code does NOT log:
- Speculative failures ("this might fail if...")
- Infrastructure failures ("could fail if database is slow")
- Failures in other components
- Anything it cannot point to in the specific file just written

---

## Conflict Resolution Rule — STOP and Report

If at any point during implementation a conflict is found between:
- A Point file and the actual data file structure
- Two Point files that contradict each other
- The prompt instructions and CLAUDE.md

Claude Code must STOP immediately and report the conflict in its response.
Do NOT resolve the conflict using independent judgment.
Do NOT proceed with one interpretation and note it in the log.
State exactly: what the conflict is, which documents are in conflict, and what
the two interpretations are. Wait for instruction before continuing.

This rule exists because Point files have previously contained errors
(e.g., session_id missing from Point 3 and Point 5). Silent resolution
propagates errors downstream where they are much harder to diagnose.

---

## Data Availability Gates

| Component | Minimum data required | Who provides |
|---|---|---|
| FilterNode | universities.json with NED (28+ degrees) | Fazal — done |
| ScoringNode | lag_model.json + affinity_matrix.json with NED field_ids (stub values ok) | Fazal — needed before Step 2 |
| ProfilerNode onwards | No data files needed | — |

Fazal must provide stub lag_model and affinity_matrix entries for NED field_ids
before Step 2 begins. Stub means correct structure with placeholder numeric values —
the script compute_future_values.py will overwrite with real values later.

---

## Opus Audit Gate

One Opus session only: after all nodes and core_graph.py are complete and tested,
before the April 2026 demo. This is the final integration validation.
Do not run Opus before this point.

---

*Established April 2026 — Architecture Chat v3*