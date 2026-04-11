# POINT 2 — LangGraph Graph Design
### FYP: AI-Assisted Academic Career Guidance System
### Status: COMPLETE AND LOCKED (v2.1 — comprehensive rebuild)

---

## TABLE OF CONTENTS

1. [Full Graph Topology](#1-full-graph-topology)
2. [AgentState — All Fields](#2-agentstate--all-fields)
3. [Complete Student Journey](#3-complete-student-journey)
4. [SupervisorNode](#4-supervisornode)
5. [Conditional Edge — route_by_intent()](#5-conditional-edge--route_by_intent)
6. [ProfilerNode](#6-profilernode)
7. [FilterNode](#7-filternode)
8. [ScoringNode](#8-scoringnode)
9. [ExplanationNode](#9-explanationnode)
10. [AnswerNode](#10-answernode)
11. [Core Graph — Wiring and Checkpointer](#11-core-graph--wiring-and-checkpointer)
12. [Recommendation Model — Roadmap Persistence](#12-recommendation-model--roadmap-persistence)
13. [Application Deadline Handling](#13-application-deadline-handling)
14. [FutureValue Design — lag_model.json](#14-futurevalue-design--lag_modeljson)
15. [config.py — All Constants](#15-configpy--all-constants)
16. [Decisions Reference Table](#16-decisions-reference-table)

---

## 1. Full Graph Topology

```
                    ┌─────────────────────────────────────────────────┐
Every user          │              ENTRY POINT                        │
message starts ────>│           SupervisorNode                        │
here                │   (LLM — classifies intent, writes last_intent) │
                    └────────────────┬────────────────────────────────┘
                                     │
                         conditional edge: route_by_intent()
                                     │
          ┌──────────────────────────┼────────────────────┬─────────────────┐
          ▼                          ▼                     ▼                 ▼
    "get_recommendation"       "profile_update"     "fee_query"          "out_of_scope"
    (if profiling complete)          │               "market_query"            │
          │                          │               "follow_up"               ▼
          │                          ▼               "clarification"          AnswerNode
          │                    ProfilerNode               │
          │                    (LLM — conversational)     ▼
          │                          │              AnswerNode
          │                          ▼         (LLM + tools: fetch_fees,
          │                         END          lag_calc, current_roadmap)
          │                                            │
          ▼                                            ▼
     FilterNode                                       END
   (pure Python)
          │
          ▼ (always)
     ScoringNode
   (pure Python)
          │
          ▼ (always)
   ExplanationNode
       (LLM)
          │
          ▼
         END
```

**Key routing rule:** If `get_recommendation` intent is detected but `profiling_complete` is `False` in AgentState, the conditional edge overrides to `profiler` instead. SupervisorNode does not check this — the edge function does.

**AnswerNode consolidation (diverges from planning docs):** The planning documents described separate `UniversityAdvisorNode` and `MarketAnalystNode`. Both are replaced by a single `AnswerNode`. Both nodes would receive an intent, extract an entity, call a tool, and generate a natural language answer — the only difference is which tool is called. That difference is two lines of Python inside one node, not two separate files, two graph nodes, and two test suites. Confirmed and locked.

---

## 2. AgentState — All Fields

**File:** `agents/state.py`

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # ── Conversation ──────────────────────────────────────────────────
    messages: Annotated[list[BaseMessage], add_messages]
    # Full conversation history. LangGraph's add_messages reducer
    # appends new messages rather than overwriting. AsyncPostgresSaver
    # checkpoints this to chat_sessions.session_state JSONB after
    # every node execution.

    # ── Student data ──────────────────────────────────────────────────
    student_profile: dict
    # Loaded from DB at session start using JWT sub (user_uuid).
    # Contains: riasec_scores, subject_marks, capability_scores,
    # stream, education_level, grade_system, interests.
    # Never accepted from request body — always loaded from DB.

    active_constraints: dict
    # Extracted by ProfilerNode during conversation.
    # Contains: budget_per_semester, transport_willing, home_zone,
    # stated_preferences, family_constraints, career_goal, student_notes.
    # Separate from student_profile because these are soft/conversational
    # constraints that may be overridden per-session via context_overrides.

    # ── Graph control ─────────────────────────────────────────────────
    profiling_complete: bool
    # Set to True by ProfilerNode when all required fields are collected:
    # budget_per_semester, transport_willing, home_zone all not None.
    # For O/A Level students: stream confirmation is an additional required
    # step before profiling_complete can be True.
    # SupervisorNode's routing edge checks this before allowing
    # get_recommendation to reach FilterNode.

    last_intent: str
    # Written by SupervisorNode on every turn.
    # The route_by_intent() conditional edge function reads this.
    # Values: "get_recommendation" | "profile_update" | "fee_query" |
    #         "market_query" | "follow_up" | "clarification" | "out_of_scope"

    student_mode: str
    # "inter" | "matric_planning"
    # Set at session start from student_profile.education_level.
    # Drives FilterNode (merit cutoff bypass) and ExplanationNode
    # (recommendation framing vs planning framing).
    # education_level mapping:
    #   matric          → matric_planning
    #   inter_part1     → inter
    #   inter_part2     → inter
    #   completed_inter → inter
    #   o_level         → matric_planning
    #   a_level         → inter

    education_level: str
    # "matric" | "inter_part1" | "inter_part2" | "completed_inter"
    # | "o_level" | "a_level"
    # Drives assessment question pool selection (curriculum_level mapping).

    # ── Recommendation data ───────────────────────────────────────────
    current_roadmap: list
    # Written by ScoringNode after a full recommendation pipeline run.
    # Sorted descending by total_score.
    # Each entry: {degree_id, university_id, university_name, degree_name,
    #              merit_tier, soft_flags, total_score, match_score_normalised,
    #              future_score, capability_adjustment_applied, effective_grade_used,
    #              eligibility_tier, eligibility_note, fee_per_semester}
    # AnswerNode reads this for follow_up and clarification intents.
    # Cleared and rebuilt on every full pipeline run.

    previous_roadmap: list | None
    # Loaded from the recommendations table at session start (None if no prior run).
    # Before each full pipeline rerun: current_roadmap is copied here first,
    # then current_roadmap is cleared. This enables within-session diffs
    # (student updates profile and reruns in same session), not just
    # across-session diffs.
    # After ExplanationNode completes: current_roadmap is written to
    # the recommendations table as a new snapshot.

    thought_trace: list
    # Appended to by FilterNode and ScoringNode on every decision.
    # Each entry is a plain string describing one decision.
    # Example: "NED BS CS — stream: CONFIRMED | marks 82%>=60%: PASS |
    #           fee 55k<=60k: PASS → confirmed_eligible"
    # Full trace stored in AgentState for debugging.
    # Only top-5-relevant entries passed into ExplanationNode's prompt.
    # Cleared and rebuilt every full pipeline run.

    mismatch_notice: str | None
    # Written by ScoringNode when both trigger conditions are met:
    # (1) stated preference composite is 20+ points below top match, AND
    # (2) preferred degree FutureValue < 6.
    # ExplanationNode includes this as Part 1 of its response when not None.
    # None means no mismatch — do not show any notice.

    # ── Deferred ──────────────────────────────────────────────────────
    conflict_detected: bool
    # MVP-3 placeholder. Always False in v1. Do not use.
```

### AgentState Field Rules

| Field | Reducer | Reset per run? |
|---|---|---|
| `messages` | `add_messages` — appends only, never overwrites | No |
| `current_roadmap` | Last write wins | **Yes** — cleared before each pipeline run |
| `previous_roadmap` | Last write wins | No — copied from `current_roadmap` before clearing |
| `thought_trace` | Last write wins | **Yes** — cleared before each pipeline run |
| `mismatch_notice` | Last write wins | **Yes** — reset to None before each pipeline run |
| `conflict_detected` | Always `False` | N/A |

**previous_roadmap update sequence (critical):**
1. At session start: load from `recommendations` table (None if no prior run exists)
2. Before each full pipeline rerun: `state["previous_roadmap"] = state["current_roadmap"]`
3. Clear `current_roadmap` and `thought_trace`
4. Run pipeline
5. After ExplanationNode completes: write `current_roadmap` to `recommendations` table

---

## 3. Complete Student Journey

### Stage 1 — Registration (outside the graph)

Student opens the app → register/login screen → email + password → backend creates `users` record and empty `student_profiles` record → JWT returned. No LangGraph involved.

`onboarding_stage` field in `student_profiles` tracks progress:
```
"not_started" → "riasec_complete" → "grades_complete" → "assessment_complete"
```

Flutter calls `GET /profile/me` on every launch. Response includes `onboarding_stage`. Flutter routes student exactly where they left off. If `assessment_complete` → go to chat, restore session via AsyncPostgresSaver. **Frontend never decides navigation independently — always reads `onboarding_stage` from backend.**

---

### Stage 2 — Structured Onboarding (outside the graph, three sequential screens)

Chat is gated behind "Setup Complete". Flutter enforces sequential completion. Backend does not handle partial-profile edge cases.

**Screen 1 — RIASEC Quiz**
60 questions, 10 per RIASEC dimension, 5-point Likert (Strongly Dislike → Strongly Like). ~12–15 minutes. Frontend sums 10 responses per dimension, sends integer 10–50 per key. On completion: `POST /profile/quiz`. `riasec_scores` written to `student_profiles`. `onboarding_stage` → `"riasec_complete"`.

**Screen 2 — Academic Profile**

*Pakistani board students (Matric/Inter):*
- Select education level: Matric / Inter Part 1 / Inter Part 2 / Completed Inter
- Select stream: Pre-Engineering, Pre-Medical, ICS, Commerce, Humanities (Pakistani board only — O/A Level students do NOT select stream here)
- Enter marks per subject
- Select board (Karachi Board, AKU, FBISE, etc.)
- `grade_system` stored as `"percentage"`

*O/A Level students:*
- Select education level: O Level / A Level
- Enter subjects and grades (A*, A, B, C, D, E, U)
- `grade_system` stored as `"olevel_alevel"`
- **Two sub-modes (student chooses):**
  - **IBCC certificate available:** Student enters final percentage directly — most accurate. No conversion needed.
  - **IBCC certificate not yet obtained:** Student enters letter grades → system applies conversion table on submit → displays result with disclaimer: *"Your score is estimated at [X]%. Your actual IBCC percentage may be higher depending on subject and session. Update this when you receive your IBCC certificate."*

IBCC approximate equivalence table (used only when certificate unavailable):
| Grade | Approximate marks |
|---|---|
| A* | 90% (conservative estimate — actual varies by subject and session; disclaimer always shown) |
| A | 85% |
| B | 75% |
| C | 65% |
| D | 55% |
| E | 45% |
| U | 0% (fail) |

**Conversion runs on submit only** — not real-time, not per-field. One conversion pass when student submits all grades. Stored as percentage. All downstream pipeline code sees percentages only — FilterNode has no concept of grading systems.

A Level students: stream is **not** assigned on Screen 2. Subject combination is stored. ProfilerNode handles stream inference conversationally.

`onboarding_stage` → `"grades_complete"` on Screen 2 completion.

**Screen 3 — Capability Assessment**
MCQs drawn from curriculum-appropriate pool. `POST /profile/assessment`. `capability_scores` written to profile. `onboarding_stage` → `"assessment_complete"`.

Assessment: `ASSESSMENT_QUESTIONS_PER_SESSION = {"easy": 3, "medium": 5, "hard": 4}` — 12 questions per subject × 5 subjects = 60 total.

Curriculum level mapping:
| `education_level` | `curriculum_level` (for assessment pool) |
|---|---|
| `matric` | `matric` |
| `inter_part1` | `inter_part1` |
| `inter_part2` | `inter_part2` |
| `completed_inter` | `inter_part2` |
| `o_level` | `matric` |
| `a_level` | `inter_part2` (reuses existing pool — academically comparable) |

Questions are not split into separate pool files per level. Khuzzaim writes one set of questions, each tagged with `curriculum_level: "inter_part1"` or `"inter_part2"`. A Part 2 student's pool includes all Part 1-tagged questions plus Part 2-tagged ones — the assessment engine filters by tag at selection time. `matric` questions are a separate tag. This means Khuzzaim writes one question set with accurate level tags, not three separate banks.

---

### Stage 3 — First Chat Session (graph begins here)

Student arrives at chat. ProfilerNode takes over immediately. It already knows (from DB, loaded into AgentState): RIASEC scores, marks, stream (Pakistani board), education_level. What it still needs conversationally:

**Required (profiling_complete = True only when all present):**
- `budget_per_semester`
- `transport_willing`
- `home_zone`
- For O/A Level students: stream confirmation (additional required step)

**Optional (asked conversationally if not surfaced):**
- `stated_preferences`, `family_constraints`, `career_goal`, `student_notes`

ProfilerNode sets `profiling_complete = True` automatically when required fields are present. Minimum turns: 2-3.

---

### Stage 4 — Recommendation Request

Once `profiling_complete = True`, either:
- Student explicitly asks: *"What degrees should I consider?"*
- ProfilerNode says: *"I have everything I need. Want me to find your best matches now?"* → student says yes

`get_recommendation` + `profiling_complete = True` → FilterNode → ScoringNode → ExplanationNode → SSE stream → Flutter renders recommendation dashboard.

---

### Stage 5 — Follow-up Conversation

All handled by AnswerNode via SupervisorNode — not through the full pipeline:
- *"How much does FAST charge per semester?"* → `fee_query` → `fetch_fees()` tool
- *"What's the job market for CS in 5 years?"* → `market_query` → `lag_calc()` tool
- *"Why did NED rank higher than SZABIST?"* → `follow_up` → AnswerNode reads `current_roadmap`
- *"Show me options 6-10"* → `follow_up` → AnswerNode pulls `current_roadmap[5:]`
- *"My budget increased to 80,000"* → `profile_update` → ProfilerNode → updates `active_constraints` → asks confirmation → student confirms → `get_recommendation` → full pipeline reruns

---

### Returning Student Flow

JWT decoded → `student_profile` loaded from DB → AsyncPostgresSaver restores AgentState from last session → `current_roadmap`, `active_constraints`, `profiling_complete = True` all reinstated. `previous_roadmap` loaded from `recommendations` table. Student picks up exactly where they left off.

---

## 4. SupervisorNode

**File:** `agents/nodes/supervisor.py`
**Type:** LLM node

**Role:** Read the latest user message, classify intent, write `last_intent` to state. Entire job. Does not answer the user. Does not modify any other state field.

### Intent Classification Table

| `last_intent` value | Triggered when |
|---|---|
| `"get_recommendation"` | Student asks for degree/university suggestions, options, what to study |
| `"profile_update"` | Student changes budget, stream, marks, preferences, constraints |
| `"fee_query"` | Student asks about fees, cost, affordability of a specific university/degree |
| `"market_query"` | Student asks about job market, career prospects, future scope of a field |
| `"follow_up"` | Student asks about existing recommendations ("why did X rank higher?") |
| `"clarification"` | Student asks a general question answerable from current state ("what is my match score for NED?") |
| `"out_of_scope"` | Anything outside career/university guidance — homework help, general chat, etc. |

### The LLM Call

```python
SUPERVISOR_SYSTEM_PROMPT = """
You are an intent classifier for an academic career guidance system.
Classify the student's message into exactly one of these intents:
get_recommendation, profile_update, fee_query, market_query,
follow_up, clarification, out_of_scope

Rules:
- If the student mentions changing budget, marks, or preferences: profile_update
- If the student asks about a specific university's fees or costs: fee_query
- If the student asks about careers, jobs, or future scope: market_query
- If the student references their existing recommendations: follow_up or clarification
- If unclear between follow_up and clarification: use follow_up
- Never return anything except one of the seven intent strings above

Student message: {user_input}
Respond with only the intent string. No explanation.
"""
```

**Why LLM and not keyword matching:** Roman Urdu. A student might write *"yaar mujhe batao CS ka scope kya hai Pakistan mein"* — keyword matching on "scope" might not fire correctly, but an LLM classifies this as `market_query`. The intent space is small enough (7 values) that the LLM rarely misclassifies.

**Adding new intents later:** (1) Add the new intent string to the supervisor prompt's list. (2) Add one `elif` branch in `route_by_intent()`. (3) If it routes to a new node, register that node in `core_graph.py`. Steps 1-2 are five lines of code. No existing nodes change.

**Output:** Writes only `last_intent` to AgentState. Returns state.

---

## 5. Conditional Edge — route_by_intent()

A function, not a node. Reads state, returns the name of the next node.

```python
from langgraph.graph import END

def route_by_intent(state: AgentState) -> str:
    intent = state["last_intent"]

    if intent == "get_recommendation":
        if not state["profiling_complete"]:
            return "profiler"       # can't recommend without constraints
        return "filter_node"

    elif intent == "profile_update":
        return "profiler"

    elif intent in ("fee_query", "market_query", "follow_up", "clarification"):
        return "answer_node"

    elif intent == "out_of_scope":
        return "answer_node"                  # returns polite out-of-scope message to student

    else:
        return END                  # safety fallback for unexpected intent values
```

**Registered in core_graph.py:**
```python
graph.add_conditional_edges("supervisor", route_by_intent)
```

**The critical behaviour:** `get_recommendation` with `profiling_complete = False` silently reroutes to ProfilerNode. ProfilerNode handles gracefully — *"before I find your matches, I just need to know your budget."*

---

## 6. ProfilerNode

**File:** `agents/nodes/profiler.py`
**Type:** LLM node (conversational extraction)

**Two activation situations:**
1. `intent = "profile_update"` — student is changing something mid-session
2. `intent = "get_recommendation"` with `profiling_complete = False` — student wants recommendations but system doesn't have enough yet

`last_intent` in state tells it which situation it's in.

### System Prompt

```python
PROFILER_SYSTEM_PROMPT = """
You are the profiling assistant for an academic career guidance system for Pakistani
students. Your job is to collect missing information through natural conversation.

You already know the following about the student:
- Education level: {student_profile.education_level}
- Grade system: {student_profile.grade_system}
- Stream: {student_profile.stream}   [Pakistani board only — may be None for O/A Level]
- Marks: {student_profile.subject_marks}
- RIASEC profile: {student_profile.riasec_scores}
- Capability scores: {student_profile.capability_scores}

Current constraints collected so far:
{active_constraints}

Required fields still missing: {missing_required_fields}
Optional fields not yet collected: {missing_optional_fields}

Rules:
- Ask for ONE missing required field at a time, naturally
- Do not use form-like language ("Please enter your budget")
- If intent is profile_update, acknowledge what changed and confirm the update
- After each student response, extract structured data from it
- When all required fields are present, set profiling_complete to True in your response
- Respond in the same language the student uses (Urdu, Roman Urdu, or English)
- Never mention RIASEC scores or capability scores directly to the student
- For O/A Level students (grade_system = "olevel_alevel"):
  - Stream confirmation is a REQUIRED step before profiling_complete can be True
  - Present the inferred stream from subject combination and ask student to confirm
  - For unusual combinations, present both closest options and ask which direction they lean

Current conversation: {messages}
Student's latest message: {user_input}
"""
```

### Structured Output — How ProfilerNode Writes to State

LLM returns JSON, not plain text:

```json
{
  "reply_to_student": "Got it, Rs. 50,000 per semester. Are you able to travel to any part of Karachi or do you need to stay near a specific area?",
  "extracted_fields": {
    "budget_per_semester": 50000,
    "transport_willing": null,
    "home_zone": null
  },
  "profiling_complete": false,
  "confirmed_stream": null
}
```

ProfilerNode code merges `extracted_fields` into `active_constraints`, sends `reply_to_student` to the student, and updates `profiling_complete` and `student_profile.stream` (for O/A Level) in state.

**Why structured output:** "Fifty thousand", "50k", "50,000", "around 50" all mean the same thing. The LLM handles natural language extraction natively when returning structured output alongside the reply. Brittle regex on conversational text is avoided.

### Required and Optional Fields

```python
PROFILER_REQUIRED_FIELDS = [
    "budget_per_semester",      # must collect before profiling_complete = True
    "transport_willing",        # bool: can student travel anywhere in Karachi?
    "home_zone",                # int 1-5: student's Karachi zone
]

PROFILER_OPTIONAL_FIELDS = [
    "stated_preferences",       # list: degree fields the student mentioned wanting
    "family_constraints",       # str: any family expectations mentioned
    "career_goal",              # str: what the student wants to do after graduation
    "student_notes",            # str: anything freeform the student wants noted
]
```

**Extensibility:** To add a new required question, add the field name to `PROFILER_REQUIRED_FIELDS`. ProfilerNode's completion check automatically requires it. The LLM figures out how to ask conversationally. No node rewrite.

### Completion Logic

```python
def check_profiling_complete(
    active_constraints: dict,
    grade_system: str,
    stream_confirmed: bool
) -> bool:
    base_complete = all(
        active_constraints.get(field) is not None
        for field in PROFILER_REQUIRED_FIELDS
    )
    # For O/A Level students, stream confirmation is an additional required step
    if grade_system == "olevel_alevel":
        return base_complete and stream_confirmed
    return base_complete
```

### A Level Stream Inference (O/A Level students only)

ProfilerNode presents inferred stream and asks student to confirm:

| A Level subjects | Stream equivalent presented |
|---|---|
| Physics + Chemistry + Mathematics | Pre-Engineering |
| Physics + Chemistry + Biology | Pre-Medical |
| Mathematics + Computer Science + Physics/Chemistry | ICS equivalent |
| Business Studies + Accounting + Economics | Commerce |
| Unusual combinations (e.g., Math + Biology + Chem, no Physics) | Both closest options presented; student decides |

**Unusual A Level combinations:** System detects no clean stream mapping. FilterNode still runs. ExplanationNode adds soft flag note to affected degrees: *"Engineering programs typically require Physics at A Level. Your combination may not meet this requirement — contact the university admissions office directly to confirm eligibility."* Soft flag: `eligibility_contact_university`. System does not block.

**A Level note on subjects:** Minimum 3 principal subjects for IBCC equivalence. Additional Mathematics and Further Mathematics do NOT count as principal subjects for IBCC.

**O Level stream guidance:** O Level students in `matric_planning` mode who express interest in both Medical and Engineering, or say they're unsure: ProfilerNode recommends Math + Physics + Chemistry + Biology as a four-subject A Level combination that keeps both paths open, with explicit workload warning. System recommends, never instructs.

### Transport Zone System (Karachi)

ProfilerNode asks: "Which area of Karachi are you based in?" and maps the response to zone 1-5:

| Zone | Areas |
|---|---|
| 1 | North (North Karachi, Gulberg, New Karachi) |
| 2 | Central (Gulshan-e-Iqbal, Johar, Nazimabad) |
| 3 | South (Defence, Clifton, Saddar, PECHS) |
| 4 | East (Malir, Landhi, Korangi) |
| 5 | West (SITE, Orangi, Baldia) |

`home_zone` stored as int 1-5 in `active_constraints`. Each university in `universities.json` has `location.zone` (1-5). FilterNode uses zone difference as a soft flag — never a hard exclusion.

### Profile Update Flow (mid-session)

When `last_intent = "profile_update"`:
1. Acknowledge change: *"Updated your budget to Rs. 80,000 per semester."*
2. Update `active_constraints` with new value
3. Set `profiling_complete = False` momentarily, then back to `True` if all required fields still present
4. Ask: *"Want me to re-run your recommendations with this updated budget?"*
5. Does NOT automatically trigger FilterNode — waits for student confirmation
6. Student's "yes" routes through SupervisorNode as `get_recommendation` → FilterNode

### What ProfilerNode Does NOT Do

- Ask about marks or stream for Pakistani board students — already in `student_profile`
- Ask about RIASEC preferences — already scored from quiz
- Re-ask for fields already in `active_constraints` unless student is updating them
- Administer capability assessment questions
- Assign stream to O/A Level students automatically — always confirms conversationally

### Output State Changes Per Turn

```python
state["active_constraints"] = merged with new extractions
state["profiling_complete"] = True or False
state["messages"]           = appended with ProfilerNode's reply
# For O/A Level: state["student_profile"]["stream"] = confirmed_stream
# last_intent is NOT changed — ProfilerNode does not touch routing state
```

---

## 7. FilterNode

**File:** `agents/nodes/filter_node.py`
**Type:** Pure Python — zero LLM calls, ever

### Inputs from AgentState

```python
stream             = state["student_profile"]["stream"]         # set by ProfilerNode for O/A Level
subject_marks      = state["student_profile"]["subject_marks"]  # all percentages by this point
capability_scores  = state["student_profile"]["capability_scores"]
riasec_scores      = state["student_profile"]["riasec_scores"]
grade_system       = state["student_profile"]["grade_system"]   # "percentage" | "olevel_alevel"
budget             = state["active_constraints"]["budget_per_semester"]
transport_willing  = state["active_constraints"]["transport_willing"]
home_zone          = state["active_constraints"]["home_zone"]
stated_preferences = state["active_constraints"].get("stated_preferences", [])
student_mode       = state["student_mode"]
```

**Important:** For O/A Level students, grades are already converted to percentages at Screen 2 onboarding. FilterNode sees percentages only — has no concept of grading systems.

### Hard Exclusions — Only Two

A degree is hard-excluded and never shown when:
1. Student's stream has **no pathway** to the degree (not in `fully_eligible_streams` AND not in `conditionally_eligible_streams`) AND **no conditional waiver** exists
2. A mandatory subject is missing from the student's profile AND **no subject waiver** exists for their stream

**Marks never hard-exclude.** A student with very low marks still sees their best matches with improvement roadmap guidance. The system must never show a blank screen.

### Filter Philosophy Summary

| Constraint | Type | Behaviour |
|---|---|---|
| Stream eligibility | Hard (if no pathway at all, no conditional waiver) | Exclude |
| Mandatory subjects | Hard (if missing and no subject waiver) | Exclude |
| Merit percentage | Soft | Tier as confirmed/likely/stretch/improvement_needed |
| Budget | Soft | Flag "over budget by X" — never exclude |
| Transport/zone | Soft | Flag commute difficulty — never exclude |

### Merit Tiers

| Tier | Condition |
|---|---|
| `"confirmed"` | Aggregate at or above historical cutoff maximum |
| `"likely"` | Aggregate within historical cutoff range |
| `"stretch"` | Aggregate within `MERIT_STRETCH_THRESHOLD` (5%) below cutoff minimum |
| `"improvement_needed"` | Aggregate more than 5% below cutoff minimum |

### Five Constraint Checks — In Order

Every degree in every university goes through all five checks. Short-circuit on hard failures.

**Check 1 — Stream eligibility:**

```python
if stream in degree["eligibility"]["fully_eligible_streams"]:
    eligibility_tier = "confirmed"

elif stream in degree["eligibility"]["conditionally_eligible_streams"]:
    eligibility_tier = "likely"
    eligibility_note = degree["eligibility"]["eligibility_notes"][stream]

else:
    # Check for conditional waiver (e.g., policy_pending_verification)
    if degree["eligibility"].get("policy_pending_verification"):
        eligibility_tier = "likely"
        soft_flags.append({"type": "policy_unconfirmed", ...})
    else:
        thought_trace.append(f"{univ} {degree} — stream {stream}: BLOCKED → excluded")
        continue   # hard exclusion — no conditional waiver exists
```

**Check 2 — Mandatory subjects (with subject waiver support):**

```python
for subject in degree["eligibility"]["mandatory_subjects"]:
    if subject.lower() not in [s.lower() for s in subject_marks.keys()]:
        waiver = degree["eligibility"]["subject_waivers"].get(subject)
        if waiver and stream in waiver["waivable_for_streams"]:
            eligibility_note += f" | Missing {subject} — bridge course required"
            eligibility_tier = "likely"   # downgrade, do NOT exclude
            soft_flags.append({
                "type": "bridge_course_required",
                "message": f"Missing {subject} — {waiver['condition']}",
                "actionable": "Bridge course required before enrollment"
            })
        else:
            thought_trace.append(
                f"{univ} {degree} — {subject} required, not in profile, no subject waiver → excluded"
            )
            exclude = True
            break   # hard exclusion — no subject waiver exists
```

**Subject waivers in universities.json (example):**
```json
"subject_waivers": {
    "Mathematics": {
        "waivable_for_streams": ["Pre-Medical"],
        "condition": "Must complete PEC-mandated 8-week bridge course before enrollment",
        "max_intake_percentage": 40
    }
}
```

This handles HEC policy: Pre-Medical students can enter Engineering via bridge course. Degree appears with `bridge_course_required` flag, not excluded.

**Check 3 — Merit tier assignment:**

```python
aggregate = calculate_aggregate(subject_marks, degree["aggregate_formula"])
cutoff_min = degree["cutoff_range"]["min"]
cutoff_max = degree["cutoff_range"]["max"]

if aggregate >= cutoff_max:
    merit_tier = "confirmed"
elif aggregate >= cutoff_min:
    merit_tier = "likely"
elif aggregate >= (cutoff_min - MERIT_STRETCH_THRESHOLD):   # MERIT_STRETCH_THRESHOLD = 5
    merit_tier = "stretch"
    soft_flags.append({
        "type": "stretch_merit",
        "message": f"Your aggregate is {cutoff_min - aggregate:.1f}% below {univ} {degree} minimum cutoff",
        "actionable": "Possible in a competitive year; entry test performance is critical"
    })
else:
    merit_tier = "improvement_needed"
    gap_percentage = cutoff_min - aggregate
    soft_flags.append({
        "type": "improvement_needed",
        "gap_percentage": gap_percentage,
        "message": f"Your aggregate is {gap_percentage:.1f}% below {univ} {degree} minimum cutoff of {cutoff_min}%",
        "subject_advice": build_subject_advice(subject_marks, degree),
        "actionable": f"Focus on {weakest_required_subject} to close this gap"
    })
```

`calculate_aggregate()` is a helper in FilterNode. Different degrees weight subjects differently — Engineering weights Maths + Physics higher. Formula stored in `universities.json` per degree.

**Check 4 — Budget (soft flag only, never exclude):**

```python
# universities.json stores fee_per_semester directly
# (Fazal normalises at data entry — annual fees divided by 2)
fee_per_semester = degree["fee_per_semester"]

if fee_per_semester > budget:
    overage = fee_per_semester - budget
    soft_flags.append({
        "type": "over_budget",
        "message": f"Fee is Rs. {fee_per_semester:,}/semester — Rs. {overage:,} above your stated budget",
        "actionable": f"Increasing budget to Rs. {fee_per_semester:,} makes this reachable"
    })
    # Degree still appears — budget is never a hard exclusion
```

**Check 5 — Transport / zone distance (soft flag only, never exclude):**

```python
uni_zone = degree["location"]["zone"]
zone_diff = abs(home_zone - uni_zone)

if zone_diff >= 2:
    soft_flags.append({
        "type": "commute_distance",
        "message": f"{university_name} is in Zone {uni_zone} — {commute_description(zone_diff)} from your area",
        "actionable": f"Travel time approximately {estimate_travel(zone_diff)} minutes"
    })
# Zone difference guide: 0-1 = easy; 2 = moderate; 3+ = difficult
```

### Final Tier Assignment

The most conservative tier wins (stream eligibility vs merit):

```python
tier_priority = {"confirmed": 0, "likely": 1, "stretch": 2, "improvement_needed": 3}
final_tier = max(eligibility_tier, merit_tier, key=lambda t: tier_priority[t])
```

A degree where stream is `confirmed` but merit is `stretch` → placed in `stretch`. Conservative is correct — don't show a degree as `confirmed` when marks are borderline.

### Matric Planning Mode Bypass

```python
if state["student_mode"] == "matric_planning":
    # Skip Check 3 (merit cutoff) — no Inter marks to compare
    # Replace with planning flag
    soft_flags.append({
        "type": "planning_mode",
        "message": "Merit eligibility cannot be assessed without Inter marks",
        "actionable": "Take Pre-Engineering in Inter and aim for 80%+ to reach this program"
    })
    merit_tier = None
    # Checks 1, 2, 4, 5 still run normally
```

### Output Structure

FilterNode produces a **single list** — all non-hard-excluded degrees — each entry with merit tier and soft flags:

```python
# Example degree entry
{
    "degree_id": "fast_bscs",
    "university_id": "fast",
    "university_name": "FAST-NUCES",
    "degree_name": "BS Computer Science",
    "eligibility_tier": "likely",
    "merit_tier": "likely",
    "final_tier": "likely",
    "eligibility_note": None,
    "aggregate_used": 82.5,
    "fee_per_semester": 78000,
    "soft_flags": [
        {
            "type": "over_budget",
            "message": "Fee is Rs. 78,000/semester — Rs. 18,000 above your stated budget",
            "actionable": "Increasing budget to Rs. 78,000 makes this reachable"
        }
    ],
    "hard_excluded": False
}
```

### Minimum Display Rule

Always show at least `FILTER_MINIMUM_RESULTS_SHOWN` (5) degrees regardless of merit tier — ranked by RIASEC match score. Student with very low marks sees 5 best aptitude matches with improvement paths. Never a blank screen.

### Soft Flags — Complete List

| Flag type | Trigger condition |
|---|---|
| `over_budget` | Fee exceeds student's stated budget |
| `commute_distance` | Zone difference ≥ 2 |
| `stretch_merit` | Aggregate within 5% below cutoff minimum |
| `improvement_needed` | Aggregate more than 5% below cutoff minimum |
| `bridge_course_required` | Conditionally eligible stream OR subject waiver applies |
| `policy_unconfirmed` | `policy_pending_verification: true` in universities.json |
| `eligibility_contact_university` | Unusual A Level combination — no clean stream mapping |
| `planning_mode` | All entries in `matric_planning` mode |

### Thought Trace Format (FilterNode)

Plain strings. Readable by a student looking at "Show Reasoning" toggle. No JSON inside `thought_trace`.

```
"NED BS CS — stream Pre-Engineering: CONFIRMED | aggregate 82% in range [80.5%-87.2%]: LIKELY | fee 27.5k <= budget 60k: PASS → likely_eligible"
"FAST BS CS — fee 78k > budget 60k: SOFT FLAG (over_budget) → included with flag"
"KU MBBS — stream Pre-Engineering not in [Pre-Medical]: BLOCKED → excluded"
"NED BS EE — aggregate 55% is 12.5% below cutoff min 67.5%: improvement_needed → included with roadmap flag"
```

### What FilterNode Does NOT Do

- No scoring — ScoringNode's job
- No LLM calls — ever
- No reading from `lag_model.json` or `affinity_matrix.json`
- No writing to `mismatch_notice`
- No converting O/A Level grades — already done at Screen 2

---

## 8. ScoringNode

**File:** `agents/nodes/scoring_node.py`
**Type:** Pure Python — zero LLM calls, ever

### Inputs

```python
state["current_roadmap"]     # single list from FilterNode — all non-excluded degrees
state["student_profile"]     # riasec_scores, subject_marks, capability_scores,
                              # education_level, student_mode
state["active_constraints"]  # stated_preferences, career_goal
```

### The Scoring Formula

```python
# From config.py
SCORING_WEIGHTS = {
    "inter":           {"match": 0.6, "future": 0.4},
    "matric_planning": {"match": 0.7, "future": 0.3}
}

weights = SCORING_WEIGHTS[state["student_mode"]]
total_score = (weights["match"] * match_score_normalised) + (weights["future"] * future_score / 10)
```

- `match_score_normalised` — RIASEC affinity dot product, normalised 0-1
- `future_score` — FutureValue from `lag_model.json`, 0-10 scale
- **Matric planning weight shift:** 70/30 instead of 60/40 — marks component absent, RIASEC weighted higher. Weights configurable in `config.py`.

### Component 1 — match_score (RIASEC)

Source: `affinity_matrix.json` — one RIASEC vector per degree field (not per university).

```python
student_vector = [R_score, I_score, A_score, S_score, E_score, C_score]
degree_vector  = [R_affinity, I_affinity, A_affinity, S_affinity, E_affinity, C_affinity]
                 # each value 1-10

# Dot product
raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))

# Normalise against theoretical maximum
theoretical_max = sum(s * 10 for s in student_vector)  # 10 = max affinity per dimension
match_score_normalised = raw_match / theoretical_max
```

Perfect alignment → `match_score_normalised = 1.0`. Zero overlap → 0. This is why RIASEC is scored independently of stated preferences — the system surfaces aptitude-preference mismatches.

### Component 2 — future_score

Source: `lag_model.json`

ScoringNode reads the pre-computed `computed.future_value`. It does NOT recalculate the three-layer formula. That is Fazal's job in `compute_future_values.py`.

```python
future_score = lag_model[degree["field_id"]]["computed"]["future_value"]  # float 0-10
```

### Capability Score Blend — Corrected Formula

Three config constants:
```python
CAPABILITY_BLEND_THRESHOLD = 25    # minimum gap (points) to trigger any blend
CAPABILITY_BLEND_WEIGHT    = 0.25  # weight given to capability score
CAPABILITY_BLEND_MAX_SHIFT = 10    # maximum points effective grade can move
```

```python
gap = capability_score - reported_grade  # positive = stronger than marks show
                                         # negative = weaker than marks show

if abs(gap) >= CAPABILITY_BLEND_THRESHOLD:   # >= not > — gap of exactly 25 triggers
    raw_effective = (reported_grade * (1 - CAPABILITY_BLEND_WEIGHT)) + (capability_score * CAPABILITY_BLEND_WEIGHT)
    # Hard cap — effective grade never moves more than CAPABILITY_BLEND_MAX_SHIFT points
    effective_grade = max(
        reported_grade - CAPABILITY_BLEND_MAX_SHIFT,
        min(reported_grade + CAPABILITY_BLEND_MAX_SHIFT, raw_effective)
    )
    thought_trace.append(
        f"{degree_name} — capability {capability_score}% vs reported {reported_grade}% "
        f"(gap {gap:+.0f}pts). Effective grade: {effective_grade:.1f}%"
    )
else:
    effective_grade = reported_grade  # no adjustment
```

**Worked examples (verification):**

| Reported | Capability | Gap | Raw effective | After cap | Movement |
|---|---|---|---|---|---|
| 70% | 40% | -30 (triggers) | 62.5% | 60% (capped) | -10 |
| 70% | 30% | -40 (triggers) | 60.0% | 60% (capped) | -10 |
| 70% | 45% | -25 (exactly triggers ≥) | 63.75% | 63.75% | -6.25 |
| 70% | 95% | +25 (triggers) | 76.25% | 76.25% | +6.25 |
| 70% | 100% | +30 (triggers) | 77.5% | 77.5% | +7.5 |
| 80% | 100% | +20 (no trigger — below 25) | — | 80% | 0 |

**Critical:** `effective_grade` used only within ScoringNode for `match_score_normalised`. NOT stored back to student profile. Original reported grade remains unchanged everywhere else.

### Mismatch Detection

After all degrees scored, check whether the student's stated preference scores significantly worse than their top match. **Both** conditions must be true:

```python
stated_prefs   = state["active_constraints"].get("stated_preferences", [])
top_match_score = current_roadmap[0]["total_score"]

for pref in stated_prefs:
    pref_entries = [d for d in current_roadmap if pref.lower() in d["degree_name"].lower()]
    if not pref_entries:
        continue

    pref_score        = pref_entries[0]["total_score"]
    pref_future_value = lag_model[pref_entries[0]["field_id"]]["computed"]["future_value"]
    score_gap         = (top_match_score - pref_score) * 100  # convert to 0-100 scale

    if score_gap >= MISMATCH_SCORE_GAP_THRESHOLD and pref_future_value < MISMATCH_FUTURE_VALUE_CEILING:
        # MISMATCH_SCORE_GAP_THRESHOLD = 20
        # MISMATCH_FUTURE_VALUE_CEILING = 6
        state["mismatch_notice"] = build_mismatch_notice(
            preferred=pref_entries[0],
            top_match=current_roadmap[0],
            gap=score_gap,
            future_value=pref_future_value
        )
        break  # one notice maximum — most significant only
```

### Output Written to AgentState

```python
# Each entry in current_roadmap gains these fields after ScoringNode:
{
    # ...existing FilterNode fields...
    "total_score": 0.74,                       # float 0-1
    "match_score_normalised": 0.81,            # float 0-1
    "future_score": 7.2,                       # float 0-10, read from lag_model.json
    "capability_adjustment_applied": True,     # bool — was blending used?
    "effective_grade_used": 78.4,             # float — grade actually used in calculation
}

# Sorted descending by total_score
state["current_roadmap"] = sorted(current_roadmap, key=lambda x: x["total_score"], reverse=True)
state["thought_trace"]   = appended with scoring entries
state["mismatch_notice"] = str or None
```

### Thought Trace Format (ScoringNode)

```
"BS CS (NED) — RIASEC match: 0.81 | FutureValue: 8.5 | total_score: 0.83"
"BS EE (NED) — RIASEC match: 0.74 | FutureValue: 7.0 | total_score: 0.72 | capability blend: reported 75% → effective 69%"
"BS Physics (KU) — RIASEC match: 0.68 | FutureValue: 3.5 | total_score: 0.55 | MISMATCH: 28pts below top match, FutureValue 3.5 < 6"
```

### What ScoringNode Does NOT Do

- No LLM calls — ever
- No reading from `universities.json`
- No writing to `active_constraints`
- No writing `profiling_complete` or `last_intent`
- No modifying student profile in database
- No recalculating `future_value` — reads pre-computed value from JSON

---

## 9. ExplanationNode

**File:** `agents/nodes/explanation_node.py`
**Type:** LLM node — Gemini 2.0 Flash (Sprint 1-2), Claude Sonnet 4.6 (Sprint 3+)

The only node the student ever directly experiences.

### Inputs

```python
state["current_roadmap"]     # sorted by total_score; top 5 passed to prompt
state["student_profile"]     # full profile
state["active_constraints"]  # budget, home_zone, stated_preferences, career_goal
state["mismatch_notice"]     # str or None — from ScoringNode
state["thought_trace"]       # trimmed to top-5-relevant entries before prompt
state["previous_roadmap"]    # list or None — for computing diff on rerun
state["student_mode"]        # selects prompt framing
```

### Thought Trace Trimming — Option B (Quality, Not Cost)

```python
top5_ids   = [d["degree_id"] for d in state["current_roadmap"][:5]]
prompt_trace = [t for t in state["thought_trace"] if any(id in t for id in top5_ids)]
```

Only top-5-relevant entries pass into the prompt. Full trace stays in AgentState for debugging.

**Why (quality argument):** The ~3,305 extra tokens from including the full trace (Option A) are almost entirely reasoning about degrees ExplanationNode never mentions — FilterNode fail entries for ~55 excluded degrees and ScoringNode entries for ranks 6-45. LLMs with long, low-relevance context produce measurably lower output quality on the relevant content ("lost in the middle" problem). Option B produces more focused, accurate explanations.

**Cost comparison (for reference):**

| | Option B | Option A | Difference |
|---|---|---|---|
| Input tokens per call | ~1,320 | ~4,625 | ~3,305 |
| Cost per call (Sonnet 4.6) | ~$0.0114 | ~$0.0214 | ~$0.01 |
| Per 100 students (Sonnet) | ~$1.14 | ~$2.14 | ~$1.00 |

Cost difference is negligible at FYP scale. Quality argument is the primary reason for Option B.

### Two Prompt Modes — Same Node

ExplanationNode checks `student_mode`:

**Mode 1 — Inter mode:** Standard recommendation framing. "Here are the degrees you can access, here is why they suit you, here is what the market looks like." Merit tiers discussed. Admission likelihood addressed.

**Mode 2 — Matric planning mode:** Future-framing. "Here are the degrees you could reach, here is what stream and marks you need to get there, here is what the market will look like when you graduate." No merit discussion — no Inter marks yet. Planning language throughout.

### Language Handling

ExplanationNode detects language from last 2-3 student messages and responds in the same language. Prompt instruction:

```
LANGUAGE RULE: The student's recent messages are in [detected language].
Respond entirely in that language. If Roman Urdu, use natural conversational
Roman Urdu as a Pakistani student would write it — not formal Urdu transliteration.
Do not mix languages unless the student mixes them.
```

No separate translation node. No language detection library. LLM handles this natively.

### Prompt Structure — Four Sections

**Section 1 — Student identity:**
```
Student profile:
- Marks: Physics 68%, Chemistry 71%, Maths 84%, English 75%
- RIASEC: R:32 I:45 A:28 S:31 E:38 C:42 (dominant: Investigative, Conventional)
- Capability assessment: Maths 78%, Physics 61%, Chemistry 69%
- Education: Inter Part 2, Pre-Engineering, Karachi Board
- Budget: Rs. 65,000/semester
- Home zone: 2 (Gulshan/Johar area)
- Career goal: "wants to work in tech, interested in AI"
- Stated preference: "CS"
```

**Section 2 — Top 5 degrees with evidence:**
```
Rank 1: BS CS — NED University
  total_score: 0.84 | merit_tier: likely | RIASEC match: 0.89 | future_value: 8.4
  Fee: 55,000/semester | Zone: 3 (moderate commute from zone 2)
  Soft flags: commute_distance
  Market: 1,240 active Rozee jobs | trend: rising 38% YoY | global: LinkedIn #3 fastest growing
  Entry test: Maths 40% weight, Physics 30% — capability shows Physics gap (61%)

Rank 2: BS CS — FAST-NUCES
  total_score: 0.79 | merit_tier: likely | RIASEC match: 0.89 | future_value: 8.4
  Fee: 78,000/semester | Zone: 2 (easy commute)
  Soft flags: over_budget (Rs. 13,000 above stated budget)
  ...
```

**Section 3 — Mismatch notice (if applicable):**
```
Mismatch detected: Stated preference "BBA" scores 0.52 vs top match 0.84.
BBA FutureValue: 5.1. Include this notice at the start of your response.
```

**Section 4 — Instructions:**
```
Write a recommendation response for this student. Rules:
- Address the student directly, second person
- Explain WHY each degree suits them using their specific numbers
- Surface soft flags in plain human language — never use technical flag names
- For NED BS CS: mention the commute and ask if that works for them
- For FAST BS CS: mention the budget gap with the exact rupee amount
- For any improvement_needed entries: give subject-specific improvement advice
- Reference actual job numbers — say "1,240 active jobs on Rozee.pk right now"
- Never say "based on my analysis" or "as an AI" — speak as a knowledgeable advisor
- Do not invent information not in the data above
- End with one open question inviting follow-up
- Length: conversational, not exhaustive. Student should feel helped, not overwhelmed.
```

### Response Structure — Up to Four Parts

All parts are conditional except Part 2.

**Part 0 — What Changed (reruns only):**

```python
prev_top5_ids = {d["degree_id"] for d in previous_roadmap[:5]}
curr_top5_ids = {d["degree_id"] for d in current_roadmap[:5]}
entered = curr_top5_ids - prev_top5_ids
dropped = prev_top5_ids - curr_top5_ids

# ROADMAP_SIGNIFICANT_CHANGE_COUNT = 2
significant_change = (len(entered) + len(dropped)) >= ROADMAP_SIGNIFICANT_CHANGE_COUNT
```

Shown when `previous_roadmap` is not None AND ≥2 top-5 entries are different. ExplanationNode opens with a brief diff: *"Since your last recommendations, BS EE at NED has moved into your top 5 because your updated budget now covers the fees. BS Civil Engineering dropped out — here's why."*

**Part 1 — Mismatch notice (when `mismatch_notice` is not None):**

Shown before recommendations. Transparent comparison. Not a rejection — an honest observation with data.

*"You mentioned interest in BBA. Your profile shows strongest alignment with Data Science and Engineering fields. BBA currently has 280 active job postings on Rozee.pk vs 1,240 for CS roles, and your RIASEC scores are more Investigative than Enterprising. I've included BBA in your results — but here's what the comparison looks like."*

**Part 2 — Top 5 recommendations (always):**

Top 5 from `current_roadmap`, in rank order. For each degree:
- Why this degree matches this specific student — RIASEC alignment, marks, capability signal
- What the market looks like — Layer 1 job count, Layer 2 trend, Layer 3 global signal where relevant
- Soft flags surfaced in plain human language — never technical flag names
- Entry test advice if `capability_scores` show weakness in subjects heavily weighted by that university. Trigger: capability score below 65% in a subject that carries significant entry test weight. Data comes from `entry_test` block in `universities.json`:
```json
"entry_test": {
    "required": true,
    "test_name": "NU-FAST Entry Test",
    "math_weight": 0.4,
    "physics_weight": 0.3,
    "english_weight": 0.3,
    "difficulty": "high"
}
```

ExplanationNode prompt instruction: *"If the student's capability score in a heavily-weighted subject is below 65%, mention they should strengthen that subject for this university's entry test."* Example output: *"Your Mathematics assessment suggests you're at 58% — FAST's entry test is Mathematics-heavy (40% weight). Strengthening calculus and algebra before applying would improve your chances."* No new node, no new data structure beyond what's in `universities.json`.

**Part 3 — Improvement roadmap (only for `improvement_needed` merit tier entries):**

Subject-specific advice. Concrete gaps, not generic encouragement.

*"To reach NED BS EE, your aggregate needs to improve by approximately 18%. Your assessment shows Physics at 42% — this is the most critical subject for Engineering admission. Focus there in Inter Part 2."*

### Post-Node Side Effect (in core_graph.py, not inside the node itself)

After ExplanationNode completes, `core_graph.py` writes the current roadmap snapshot to the `recommendations` table:

```python
recommendation_record = {
    "user_id": user_id,
    "run_timestamp": datetime.utcnow(),
    "roadmap_snapshot": [
        {
            "degree_id": d["degree_id"],
            "total_score": d["total_score"],
            "merit_tier": d["merit_tier"],
            "soft_flags": d["soft_flags"]
        }
        for d in state["current_roadmap"]
    ],
    "trigger": determine_trigger(state)  # "initial" | "profile_update" | "manual_rerun"
}
```

### Follow-Up Loop

After ExplanationNode responds, questions route to AnswerNode via SupervisorNode — not back through the full pipeline. Full pipeline reruns only when:
- Student explicitly asks for fresh recommendations
- Student updates their profile (confirmed → ProfilerNode → reruns)

### What ExplanationNode Does NOT Do

- Does not re-rank degrees — ranking from ScoringNode is respected
- Does not override soft flags — surfaces them, never suppresses them
- Does not make admission guarantees — "likely" not "you will get in"
- Does not hallucinate job numbers — all numbers come from the prompt context
- Does not repeat full roadmap for 10+ degrees — top 5 in detail, remainder via AnswerNode

---

## 10. AnswerNode

**File:** `agents/nodes/answer_node.py`
**Type:** LLM node + tools

Handles all post-recommendation queries. Reads `current_roadmap` directly from state — no pipeline rerun.

### Logic

```python
def answer_node(state: AgentState) -> AgentState:
    intent = state["last_intent"]

    if intent == "fee_query":
        entity = extract_university(state)       # LLM extracts university name from message
        data   = fetch_fees(entity)              # tool: reads universities.json
    elif intent == "market_query":
        field = extract_field(state)             # LLM extracts degree field from message
        data  = lag_calc(field)                  # tool: reads lag_model.json
    else:  # follow_up, clarification
        data = state["current_roadmap"]          # already in state — no tool needed

    response = llm.invoke(build_answer_prompt(intent, data, state))
    # append to messages, return state
```

### Tools

| Tool | File | What it does |
|---|---|---|
| `fetch_fees()` | `agents/tools/fetch_fees.py` | Reads `universities.json`, returns fee structure for a specific university |
| `lag_calc()` | `agents/tools/lag_calc.py` | Reads `lag_model.json`, returns FutureValue and market data for a field |
| `job_count()` | `agents/tools/job_count.py` | Returns current Rozee.pk job count for a degree field (Layer 1 data) |

### Top 6-10 Access

When student asks "show me options after the top 5":
- `follow_up` intent → AnswerNode
- Pulls `current_roadmap[5:]` directly — all ranked degrees in state
- Every entry has `total_score`, `merit_tier`, `soft_flags`, `future_score`, `match_score_normalised`
- No `thought_trace` needed — roadmap data is self-contained

### Application Deadlines

Always frames deadline info as: *"Based on the 2025 cycle, [University] typically opens applications in [month] and closes in [month]. The 2026 dates have not been announced yet — check [website] for the current cycle."* Website link included. This is a prompt instruction, not a separate mechanism.

---

## 11. Core Graph — Wiring and Checkpointer

**File:** `agents/core_graph.py`

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from agents.state import AgentState
from agents.nodes.supervisor import supervisor_node
from agents.nodes.profiler import profiler_node
from agents.nodes.filter_node import filter_node
from agents.nodes.scoring_node import scoring_node
from agents.nodes.explanation_node import explanation_node
from agents.nodes.answer_node import answer_node

def build_graph(checkpointer: AsyncPostgresSaver) -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("supervisor",       supervisor_node)
    graph.add_node("profiler",         profiler_node)
    graph.add_node("filter_node",      filter_node)
    graph.add_node("scoring_node",     scoring_node)
    graph.add_node("explanation_node", explanation_node)
    graph.add_node("answer_node",      answer_node)

    # Entry point
    graph.set_entry_point("supervisor")

    # Conditional routing from supervisor
    graph.add_conditional_edges("supervisor", route_by_intent)

    # Fixed edges — recommendation pipeline
    graph.add_edge("filter_node",      "scoring_node")
    graph.add_edge("scoring_node",     "explanation_node")
    graph.add_edge("explanation_node", END)

    # Fixed edges — other paths
    graph.add_edge("profiler",    END)
    graph.add_edge("answer_node", END)

    return graph.compile(checkpointer=checkpointer)
```

**Checkpointer:** `AsyncPostgresSaver`. After every node execution, full `AgentState` serialized to `chat_sessions.session_state JSONB`. Users close and reopen app — full context restored. Configure in `core_graph.py`, not in the endpoint.

**Pre-pipeline side effect (in chat endpoint before graph runs, on rerun only):**
```python
# 1. state["previous_roadmap"] = state["current_roadmap"]
# 2. state["current_roadmap"]  = []
# 3. state["thought_trace"]    = []
# 4. state["mismatch_notice"]  = None
# 5. Run graph
```

**Post-pipeline side effect (in core_graph.py, after ExplanationNode):**
Write roadmap snapshot to `recommendations` table.

---

## 12. Recommendation Model — Roadmap Persistence

**File:** `models/recommendation.py`

```python
# One row per pipeline run per student
{
    user_id:          UUID  # FK → users
    run_timestamp:    datetime
    roadmap_snapshot: JSONB  # list of {degree_id, total_score, merit_tier, soft_flags}
    trigger:          str    # "initial" | "profile_update" | "manual_rerun"
}
```

**Why this exists alongside AsyncPostgresSaver:**
- AsyncPostgresSaver stores full `AgentState` as LangGraph checkpoints — these are operational, not analytically queryable
- `recommendations` table stores minimal roadmap snapshots — queryable via SQL for diffs
- The within-session diff (Part 0 of ExplanationNode response) requires knowing the previous roadmap before the current run was cleared. Reconstructing this from LangGraph checkpoint blobs is possible but operationally awkward

**Scope is narrow:** One row per pipeline run. Not per degree. Not per session turn. Historical snapshots retained for analytics.

---

## 13. Application Deadline Handling

Stored in `universities.json` as historical pattern with explicit cycle labeling. No live web search.

**Standard format:**
```json
"application_window": {
  "data_cycle": "2025",
  "typical_open": "June",
  "typical_close": "August",
  "multiple_rounds": false,
  "round_details": null,
  "website": "https://ned.edu.pk/admissions",
  "last_verified": "March 2026"
}
```

**Multiple intakes (some private universities):**
```json
"application_window": {
  "data_cycle": "2025",
  "multiple_rounds": true,
  "round_details": [
    {"round": "Fall 2025", "open": "June 2025", "close": "August 2025"},
    {"round": "Spring 2026", "open": "November 2025", "close": "January 2026"}
  ],
  "website": "https://szabist.edu.pk/admissions",
  "last_verified": "March 2026"
}
```

AnswerNode prompt instruction: always frame as *"Based on the 2025 cycle, [University] typically opens in [month]... The 2026 dates have not been announced yet — check [website]."*

Fazal populates `application_window` for all 20 universities during Phase A. JSON update + reseed if 2026 dates announced before viva. No architectural change needed.

---

## 14. FutureValue Design — lag_model.json

### What FutureValue Is

A single float (0-10) per degree field. Represents career trajectory strength for graduates of that field, combining Pakistani market data with global signals adjusted by how quickly Pakistan absorbs trends from leading markets (US/UK/UAE).

### Three-Layer Formula

```
FutureValue = weighted_sum(Layer1, Layer2, Layer3) × lag_confidence_multiplier
```

| Layer | Source | Signal | Nature |
|---|---|---|---|
| Layer 1 | Rozee.pk weekly scraper + Mustakbil + Jobz | YoY growth of active Pakistani job postings | Live data, no forecasting |
| Layer 2 | Rozee.pk 3yr historical + Google Trends PK + PSEB export data | Pakistan demand direction — growing, stable, or declining | Direction reading, not forecast |
| Layer 3 | LinkedIn Talent Trends + Stack Overflow Survey + Google Trends Global | US/UK/UAE market momentum | Leading indicator for outsourcing-driven fields |

For LOCAL category fields (Medicine, Law, Civil Engineering, Business): Layer 3 weight = 0. Domestic demand is the signal.

**Pakistan-world weight rationale:** Pakistani tech graduates primarily work for companies in US/UK/UAE markets via outsourcing. Global signal is a direct indicator of what Pakistani graduates will be hired to do — not merely a leading indicator. LEAPFROG and FAST fields are outsourcing-heavy; LOCAL fields are entirely domestic.

### Per-Lag-Category Weights

From `config.py`:

```python
FUTURE_VALUE_WEIGHTS = {
    "LEAPFROG": {"layer1": 0.30, "layer2": 0.20, "layer3": 0.50},
    "FAST":     {"layer1": 0.35, "layer2": 0.25, "layer3": 0.40},
    "MEDIUM":   {"layer1": 0.40, "layer2": 0.30, "layer3": 0.30},
    "SLOW":     {"layer1": 0.45, "layer2": 0.35, "layer3": 0.20},
    "LOCAL":    {"layer1": 0.60, "layer2": 0.40, "layer3": 0.00},
}

LAG_CONFIDENCE = {
    "LEAPFROG": 1.00,   # Already arrived or arriving — full signal weight
    "FAST":     0.95,   # Arriving with high confidence
    "MEDIUM":   0.85,   # Likely to arrive within graduate's career
    "SLOW":     0.70,   # May arrive but uncertain timing
    "LOCAL":    1.00,   # Not lag-based — domestic demand is signal
}
```

### lag_model.json Schema (per field)

```json
{
  "field_id": "computer_science",
  "field_name": "Computer Science / Software Engineering",
  "lag_category": "FAST",
  "data_updated": "2025-01",

  "pakistan_now": {
    "job_postings_monthly": 12000,
    "yoy_growth_rate": 0.23,
    "sources": ["rozee.pk", "linkedin_pk", "indeed_pk"]
  },

  "world_now": {
    "us_yoy_growth_rate": 0.25,
    "uk_yoy_growth_rate": 0.18,
    "uae_yoy_growth_rate": 0.31,
    "sources": ["BLS 2024", "ONS UK 2024", "LinkedIn UAE"]
  },

  "world_future": {
    "us_bls_4yr_projected_growth": 0.17,
    "bls_soc_code": "15-1252",
    "projection_basis": "BLS Occupational Outlook Handbook 2024-34 (interpolated to 4yr)"
  },

  "pakistan_future": {
    "projected_4yr_growth": 0.38,
    "derivation": "pakistan_now growth rate + world_future signal adjusted for lag"
  },

  "lag_parameters": {
    "lag_years": 1.0,
    "arrival_confidence": "high",
    "cultural_barrier": false,
    "societal_barrier": false,
    "notes": "Already arrived and accelerating. Multinational presence driving demand."
  },

  "computed": {
    "future_value": 8.4,
    "last_computed": "2025-01"
  }
}
```

### Computation Script — scripts/compute_future_values.py

Fazal runs during Phase A data build; re-runs each semester. ScoringNode reads `computed.future_value` only — zero runtime computation.

```python
def compute_future_value(field: dict, all_fields: list[dict]) -> float:
    lag_cat    = field["lag_category"]
    weights    = FUTURE_VALUE_WEIGHTS[lag_cat]
    confidence = LAG_CONFIDENCE[lag_cat]

    # Normalise each signal against all fields (min-max) before weighting
    pak_now_score   = normalise(field["pakistan_now"]["yoy_growth_rate"], all_fields, key="pakistan_now.yoy")
    world_now_score = normalise(composite_world_now(field), all_fields, key="world_now_composite")
    pak_fut_score   = normalise(field["pakistan_future"]["projected_4yr_growth"], all_fields, key="pakistan_future")
    world_fut_score = normalise(field["world_future"]["us_bls_4yr_projected_growth"], all_fields, key="world_future")

    raw = (
        pak_now_score   * weights["layer1"] +
        world_now_score * weights["layer3"] +
        pak_fut_score   * weights["layer2"] +
        world_fut_score * weights["layer3"]
    )

    future_value = round(raw * 10 * confidence, 2)  # scale to 0-10
    return future_value
```

Normalisation: each signal normalised independently across all fields. No single field with extreme raw numbers dominates.

Update cadence: once per semester. Script validates all required fields present before writing output.

---

## 15. config.py — All Constants

```python
# ── Assessment ────────────────────────────────────────────────────────
ASSESSMENT_QUESTIONS_PER_SESSION = {"easy": 3, "medium": 5, "hard": 4}
# 12 questions per subject × 5 subjects = 60 total

# ── Scoring weights ───────────────────────────────────────────────────
SCORING_WEIGHTS = {
    "inter":           {"match": 0.6, "future": 0.4},
    "matric_planning": {"match": 0.7, "future": 0.3}
}

# ── Capability blend ──────────────────────────────────────────────────
CAPABILITY_BLEND_THRESHOLD = 25    # minimum gap (points) to trigger any blend
CAPABILITY_BLEND_WEIGHT    = 0.25  # weight given to capability score in blend
CAPABILITY_BLEND_MAX_SHIFT = 10    # maximum points effective grade can move from reported

# ── Filter ────────────────────────────────────────────────────────────
MERIT_STRETCH_THRESHOLD      = 5   # % below cutoff minimum to qualify as stretch (not improvement_needed)
FILTER_MINIMUM_RESULTS_SHOWN = 5   # always show at least this many degrees

# ── Profiler fields ───────────────────────────────────────────────────
PROFILER_REQUIRED_FIELDS = [
    "budget_per_semester",
    "transport_willing",
    "home_zone",
]
PROFILER_OPTIONAL_FIELDS = [
    "stated_preferences",
    "family_constraints",
    "career_goal",
    "student_notes",
]

# ── FutureValue weights (per lag category) ────────────────────────────
FUTURE_VALUE_WEIGHTS = {
    "LEAPFROG": {"layer1": 0.30, "layer2": 0.20, "layer3": 0.50},
    "FAST":     {"layer1": 0.35, "layer2": 0.25, "layer3": 0.40},
    "MEDIUM":   {"layer1": 0.40, "layer2": 0.30, "layer3": 0.30},
    "SLOW":     {"layer1": 0.45, "layer2": 0.35, "layer3": 0.20},
    "LOCAL":    {"layer1": 0.60, "layer2": 0.40, "layer3": 0.00},
}

# ── Lag confidence multipliers ────────────────────────────────────────
LAG_CONFIDENCE = {
    "LEAPFROG": 1.00,
    "FAST":     0.95,
    "MEDIUM":   0.85,
    "SLOW":     0.70,
    "LOCAL":    1.00,
}

# ── Rate limiting ─────────────────────────────────────────────────────
CHAT_RATE_LIMIT = "10/minute"   # slowapi, per IP, on /api/v1/chat/stream

# ── LLM models ────────────────────────────────────────────────────────
LLM_MODEL_SPRINT_1_2 = "gemini-2.0-flash"
LLM_MODEL_SPRINT_3   = "claude-sonnet-4-6"

# ── Mismatch detection ────────────────────────────────────────────────
MISMATCH_SCORE_GAP_THRESHOLD  = 20   # score gap (0-100 scale) to trigger notice
MISMATCH_FUTURE_VALUE_CEILING = 6    # preferred degree FutureValue must be below this to trigger

# ── Roadmap diff ──────────────────────────────────────────────────────
ROADMAP_SIGNIFICANT_CHANGE_COUNT = 2  # min top-5 entries changed to show Part 0
```

---

## 16. Decisions Reference Table

| Decision | Choice | Rationale |
|---|---|---|
| AnswerNode consolidation | Single AnswerNode replaces UniversityAdvisor + MarketAnalyst | Same structure, different tool — two lines of code not two files |
| `profiling_complete` trigger | Automatic (checks required fields after each turn) | Faster for student; can always update via `profile_update` intent |
| Onboarding gate | Frontend-enforced (Flutter navigation gate) | Cheapest to enforce; avoids backend partial-profile edge cases |
| App resume | `onboarding_stage` field in `student_profiles`, read by Flutter on every launch | One source of truth |
| Application deadlines | Static JSON with typical cycle data + website link + cycle label | Honest framing; live search returns stale data (2026 not announced) |
| Budget constraint | Soft flag only — never hard exclude | Merit is the real barrier; system shows "increase budget by X" guidance |
| Transport constraint | Zone-based (5 Karachi zones), soft flag only, implement now | Accurate enough; never hard exclude |
| Merit for low-mark students | `improvement_needed` tier with subject-specific advice; never excluded | System must never show a blank screen |
| Hard exclusions | Only stream (no pathway + no conditional waiver) and mandatory subjects (no subject waiver) | Two rules only. Marks never exclude. |
| O/A Level grade conversion | Screen 2 onboarding — convert to percentage before pipeline | FilterNode sees percentages only; cleaner |
| A Level stream inference | ProfilerNode confirms conversationally (Option B, not automatic) | Fragile combinations exist; student confirms |
| A Level unusual combinations | Soft flag `eligibility_contact_university` — inform, don't block | Defer to university admissions office |
| O Level students | `matric_planning` mode — plan A Level stream, cannot apply for bachelor's yet | Correct academic pathway |
| O Level undecided stream | Recommend 4 subjects (Math+Physics+Chem+Bio) with workload warning | Keeps both medical and engineering paths open |
| A Level curriculum assessment | Reuse `inter_part2` pool | Academically comparable; avoids 380 extra questions |
| O Level English assessment | Matric pool for all 5 subjects | Simplicity; add harder questions if testing reveals issues |
| Capability blend threshold | 25 points (raised from 20) | A 20-point gap between board exam and 12-question MCQ is within normal variance |
| Capability blend weight | 25% (reduced from 40%) | Capability is supplementary — confirms or questions grade, doesn't replace it |
| Capability blend cap | ±10 points hard cap | Prevents overcorrection from extreme divergence |
| Scoring weights | Configurable in `config.py` | Tunable after testing without node rewrite |
| FutureValue computation | Standalone script, pre-computed, stored in JSON | Zero runtime computation; ScoringNode reads one field |
| FutureValue layers | Three layers + lag confidence multiplier | Honest — no forecasting, all observable data |
| Weights per lag category | Per-category dict in `config.py` | LEAPFROG outsourcing-driven (global signal dominant); LOCAL domestic-only |
| Pakistan future signal | Derived from `pakistan_now` growth + lag adjustment | Q3 (Pakistan future) has no direct data source; derived is honest |
| thought_trace in ExplanationNode | Top-5-relevant entries only (Option B) | Quality: "lost in the middle" problem with 3,305 low-relevance tokens |
| Response structure | Up to four parts: 0 (diff), 1 (mismatch), 2 (recommendations), 3 (improvement) | Parts 0, 1, 3 conditional; Part 2 always shown |
| `previous_roadmap` update rule | Copied from `current_roadmap` before each rerun | Enables within-session diffs, not just across-session |
| `recommendation.py` model | One row per pipeline run; narrow scope | Queryable snapshots for diff; AsyncPostgresSaver handles conversation state |
| Roadmap diff threshold | ≥2 top-5 entries different | Meaningful change signal; single swap may be noise |
| `conflict_detected` | Always `False` in v1 | MVP-3 placeholder; deferred permanently |

---

*Point 2 Version 2.0 — March 2026*
*Complete rebuild from conversation transcript. All six nodes locked.*
*Supersedes all prior Point 2 outputs.*
*Point 2 Version 2.1 - April 2026*
*Corrected the route to return to answer node when out of scope work is asked, declining politely*