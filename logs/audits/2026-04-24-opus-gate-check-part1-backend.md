# Opus Gate Check — Session 1: Backend Correctness
## Date: 2026-04-24
## Model: Opus 4.7, medium effort
## Demo deadline: April 29, 2026
## Session 2: SSE contract + data completeness (separate session)

---

## FILES READ

1. logs/README.md
2. CLAUDE.md (precedence rules applied: CLAUDE.md v2.2 > Point 2)
3. backend/app/agents/state.py
4. backend/app/agents/core_graph.py
5. backend/app/api/v1/endpoints/chat.py
6. backend/app/agents/nodes/supervisor.py
7. backend/app/agents/nodes/profiler.py
8. backend/app/agents/nodes/filter_node.py
9. backend/app/agents/nodes/scoring_node.py
10. backend/app/agents/nodes/explanation_node.py
11. backend/app/agents/nodes/answer_node.py
12. backend/app/agents/tools/fetch_fees.py
13. backend/app/core/config.py
14. docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md (Sections 9-12 in full;
    earlier sections' output contracts only, per reading rules)

Scan reads: failure-mode sections of 4 node logs (filter-v2, scoring, explanation,
answer).

---

## AREA 1 — State Contract

### Check 1a — ExplanationNode does not write thought_trace
**PASS.** explanation_node.py contains NO `state["thought_trace"].append(...)`
calls. grep for `thought_trace` in that file returns only read-side usage at
line 397 (`state.get("thought_trace", [])`). Only write to state is
`state["messages"].append(...)` at lines 447 and 450.

### Check 1b — AnswerNode writes only state["messages"]
**PASS.** answer_node.py mutates only `state["messages"]` (via `.append`).
All five branches (fee_query, market_query, out_of_scope, follow_up,
clarification) confirm this. `state["last_intent"]` is read on line 155 only.

### Check 1c — mismatch_notice reset
**PASS.** Two resets exist, both correct:
- chat.py line 255 — `"mismatch_notice": None` in initial_state at the start
  of every pipeline run.
- scoring_node.py line 167 — `state["mismatch_notice"] = None` at the start
  of the mismatch-detection block (after the scoring loop, before the
  stated-preferences check). Not per-degree. Correct.

### Check 1d — profiling_complete flow
**PASS (all three sub-conditions verified).**
- chat.py initial_state (lines 246-256) does NOT include `profiling_complete`.
  Checkpoint restoration is the source of truth — intentional.
- core_graph.py line 29 uses `state.get("profiling_complete", False)` —
  safe default; no KeyError on first message.
- profiler.py line 244-248 sets `state["profiling_complete"]` via
  `check_profiling_complete()`.
- Minor note: supervisor.py itself never reads profiling_complete; the
  audit instruction referred to the routing layer (core_graph.route_by_intent).
  This is correct — supervisor is classification only.

### Check 1e — SupervisorNode writes only last_intent
**PASS.** supervisor.py lines 61, 85, 89, 95 — every write path sets
`state["last_intent"]`. No other state fields written.

### Check 1f — FilterNode writes current_roadmap, thought_trace, and every
roadmap entry has entry_test
**PASS.** filter_node.py:
- line 547 writes `state["current_roadmap"] = results`.
- line 548 appends to `state["thought_trace"]`.
- Every roadmap entry in the primary path includes `entry_test`
  (line 494: `"entry_test": degree.get("entry_test", {})`).
- Every promoted (minimum display rule) entry includes `entry_test`
  (line 525: `"entry_test": exc.get("entry_test", {})`).
- Note: `hard_excluded_raw` dicts (lines 266-275 and 310-319) do NOT carry
  the `entry_test` field, but the promotion block uses `.get("entry_test", {})`
  with a safe default, so `{}` is substituted. ExplanationNode's
  `_build_entry_test_advice()` handles empty dict via
  `entry_test.get("required")` → falsy → returns "". No KeyError possible.

---

## AREA 2 — Integration Boundaries

### Boundary A — FilterNode output → ScoringNode input

ScoringNode reads from each roadmap entry at lines 82-85:
`field_id`, `degree_name`, `university_name`. All three written by
filter_node.py lines 482-498.

Other per-entry reads inside ScoringNode loop use `student_profile.*`,
not roadmap fields, so no additional boundary dependency.

| Field ScoringNode reads from roadmap | FilterNode writes? |
|---|---|
| field_id | ✓ line 484 |
| degree_name | ✓ line 487 |
| university_name | ✓ line 486 |

**PASS.**

### Boundary B — ScoringNode output → ExplanationNode input

ScoringNode augments each entry with: `total_score`, `match_score_normalised`,
`future_score`, `capability_adjustment_applied`, `effective_grade_used`
(lines 149-153). It does not drop any pre-existing FilterNode field
(in-place mutation of the same dict).

ExplanationNode reads:

| Field | Source | Verified |
|---|---|---|
| degree_id | previous_roadmap-based diff (explanation_node.py 407-408) | FilterNode 483 / stored in recommendations row |
| degree_name | FilterNode 487 | ✓ |
| university_name | FilterNode 486 | ✓ |
| field_id | FilterNode 484 | ✓ |
| total_score | ScoringNode 149 | ✓ |
| match_score_normalised | ScoringNode 150 | ✓ |
| future_score | ScoringNode 151 | ✓ |
| merit_tier | FilterNode 489 | ✓ |
| eligibility_note | FilterNode 491 | ✓ |
| fee_per_semester | FilterNode 495 | ✓ |
| soft_flags | FilterNode 497 | ✓ |
| aggregate_used | FilterNode 492 | ✓ |
| entry_test | FilterNode 494 (and 525 for promoted) | ✓ |

**PASS.**

### Boundary C — ExplanationNode AIMessage content is a string
**PASS.** explanation_node.py line 446 flattens via `_flatten_content()`
before the `.strip()` call and AIMessage construction on line 447.
`_flatten_content` (lines 71-77) converts list-of-parts to a plain string.
Fallback path (line 450) uses the literal string `LLM_FAILURE_FALLBACK`.

### Boundary D — AnswerNode fee_query tool contract
**PASS.** fetch_fees.py returns a dict with:
- `university_id` (line 26)
- `university_name` (line 27) — at **root** level, not per-degree
- `degrees` list (line 28) where each entry is `{degree_name, fee_per_semester}`

answer_node.py line 184 reads `fee_data['university_name']` at root, and
lines 178-181 iterate `fee_data.get("degrees", [])` reading `degree_name`
and `fee_per_semester`. Fully consistent. The field-name bug referenced
in session logs is fixed.

---

## AREA 3 — End-to-End Flow

### Step 1 — Register
**PASS (based on logs/session-2026-04-01-backend-sprint2-prereq.md).**
auth.py creates users + student_profiles + chat_sessions rows on register;
GET /profile/me returns non-null session_id (commit 2ace388). CLAUDE.md
confirms this in locked decisions.

### Step 2 — RIASEC quiz
**PASS (documented working state).** CLAUDE.md API surface table declares
POST /profile/quiz in endpoints/profile.py; onboarding state machine
advances `not_started → riasec_complete`. Implementation file not
re-verified in this session (out of required reading list).

### Step 3 — Grades
**PASS (documented, with one caveat from Sprint 4 cleanup item #9).**
POST /profile/grades advances `riasec_complete → grades_complete`.
**Caveat (already logged, not a finding):** Alembic migration missing
`curriculum_level` column — Supabase has it, fresh local DB would fail.
Demo uses Supabase so does not affect demo.

### Step 4 — Assessment
**PASS (documented).** POST /profile/assessment advances
`grades_complete → assessment_complete`. No pipeline init triggered
(confirmed by CLAUDE.md locked decision "LangGraph pipeline init").

### Step 5 — Profile fetch returns session_id
**PASS.** CLAUDE.md API surface line: "GET /profile/me response includes
session_id: UUID (non-null) — confirmed working, commit 2ace388." chat.py
line 215 uses this value via `payload.session_id` as LangGraph thread_id.

### Step 6 — First chat message, profiling incomplete
**CONCERN (partial deviation from Point 2 spec).**

For intent = `get_recommendation` with profiling_complete False:
- core_graph.route_by_intent lines 27-31 routes to `profiler`. ✓
- profiler emits AIMessage and (when fields incomplete) leaves
  profiling_complete False. ✓
- Flow ends at profiler → END (line 74). ✓

However, Point 2 Step 6 specifies *"SupervisorNode routes to ProfilerNode
regardless of intent"* when profiling_complete is False. The current code
only forces profiler for `get_recommendation` (and always for
`profile_update`). For other intents (`fee_query`, `market_query`,
`follow_up`, `clarification`, `out_of_scope`) a first-time user bypasses
profiling entirely and goes straight to `answer_node`, which will find
no `current_roadmap` and respond "No recommendations available yet."
This is not a runtime crash, but it is a spec deviation and a UX risk
for a student who types a greeting or an off-topic first message.

SSE status progression for the tested profiling path:
`status("profiling")` → chunk stream → `status("done")`. NODE_STATUS_MAP
in chat.py covers `profiler`. ✓

### Step 7 — Recommendation request, profiling complete
**PASS.** Routing edge `get_recommendation` + profiling_complete True →
`filter_node` (core_graph.py line 31). Fixed edges chain
filter → scoring → explanation → END (lines 69-71). SSE status:
`filtering_degrees`, `scoring_degrees`, `generating_explanation` all
present in NODE_STATUS_MAP (chat.py lines 46-51). Rich_ui events and
recommendations-row write happen in chat.py real_stream() after the graph
finishes (lines 300-315). `_write_recommendation` gated on
`last_intent == "get_recommendation"` and non-empty current_roadmap.

### Step 8 — Follow-up question
**PASS.** Routing for `follow_up`/`clarification`/`fee_query`/`market_query`
→ `answer_node` (core_graph.py lines 36-37). answer_node → END (line 75).
AnswerNode emits only chunks (no status mapping for answer_node is
intentional per Point 2 Section 4). Terminal `status("done")` emitted in
chat.py real_stream finally block (line 321). PASS. Note: Sprint 4
cleanup item #7 (fetching_fees / fetching_market_data status events
not emitted by AnswerNode) is already logged and deferred.

---

## AREA 4 — Known Failure Modes

### FilterNode (logs/claude-code-2026-04-18-00-00-filter-node-v2.md)
- KeyError on missing `entry_test` / `min_percentage_hssc` /
  `eligibility_notes[stream]`. **ACCEPTABLE.** NED data (the only
  populated university) verified to contain all required keys. Would
  become DEMO RISK if additional universities are ingested before demo
  without schema validation — Session 2 should re-check universities.json
  completeness.

### ScoringNode (logs/claude-code-2026-04-18-14-00-scoring-node.md)
- FileNotFoundError if affinity_matrix.json or lag_model.json missing.
  **ALREADY FIXED by data availability.** lag_model.json is populated
  (stub for 32 NED fields per answer-node log addendum).
  affinity_matrix.json presence should be re-confirmed in Session 2
  data-completeness audit. Flag as DEMO RISK if file is still empty-array `[]`.
- KeyError on unexpected `student_mode`. **ACCEPTABLE.** student_mode
  is derived server-side from education_level (CLAUDE.md locked decision)
  and constrained to {"inter", "matric_planning"}.

### ExplanationNode (logs/claude-code-2026-04-20-14-00-explanation-node.md)
- FileNotFoundError on lag_model.json: same status as ScoringNode above.
- AttributeError on missing settings (ENTRY_TEST_SUBJECT_MAP,
  ROADMAP_SIGNIFICANT_CHANGE_COUNT). **ALREADY FIXED.** Both keys
  present in config.py (lines 77-83 and line 90).

### AnswerNode (logs/claude-code-2026-04-19-14-00-answer-node.md)
- `fee_per_semester == 0` printed as "fee not listed". **ACCEPTABLE.**
  Zero is not a valid fee value for any university.
- `job_count == 0` line omitted. **ACCEPTABLE.** Graceful degradation.
- O(n) linear scan of universities.json per fee_query. **ACCEPTABLE**
  at 20 universities. Not demo-blocking.

No DEMO BLOCKING items identified in this audit.

---

## ITEMS FOR SESSION 2

1. Verify `affinity_matrix.json` is populated with the 43+ canonical
   field_ids referenced by CLAUDE.md v1.7. FAIL here would silently
   flip every NED degree to default (match=0.5) per scoring_node.py
   lines 131-132.
2. Verify `lag_model.json` is populated with `computed.future_value`
   for every NED field_id used by FilterNode output. The same default
   fallback path applies.
3. Verify `universities.json` every degree has `entry_test`,
   `min_percentage_hssc`, `eligibility_notes` keys, and
   `aggregate_formula` with `inter_weight`/`entry_test_weight`.
4. Full SSE contract walk-through: `status` / `chunk` / `rich_ui` /
   `done` ordering under all intent paths.
5. Confirm `_build_university_card` output payload matches the 20-field
   card locked in CLAUDE.md.
6. lag_calc tool was not in this session's required reading list —
   include in Session 2.
7. Determine whether Step 6 concern (non-get_recommendation intents
   bypassing profiler on first session) warrants a routing change.

---

## ITEMS FOR ARCHITECTURE CHAT DECISION

1. **AREA 3 Step 6 — CONCERN.** Point 2 Section 3 says ProfilerNode is
   entered *regardless of intent* when profiling_complete is False.
   core_graph.route_by_intent only forces profiler for `get_recommendation`
   and `profile_update`. A greeting ("hi"), fee question, or out_of_scope
   as the first-ever message on a fresh session will route to answer_node
   with no roadmap and respond awkwardly. Two options:
   (a) widen the "force profiler when profiling_complete is False" rule
   to every intent (matches Point 2 wording); or
   (b) leave as-is and update Point 2 to reflect the current code.
   Low effort either way; low demo risk since the happy path
   (RIASEC → grades → assessment → chat) starts with a recommendation
   request, but a demo audience member could type something off-path.

2. None other — all other findings are PASS or already-logged deferred work.

---

## POST-AUDIT MAINTENANCE

- logs/README.md updated — new row added to OPUS AUDIT LOGS table.
- No code changes made.
- No data files changed.
