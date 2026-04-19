# Backend Chat — Operating Instructions
### FYP: AI-Assisted Academic Career Guidance System
### Scope: backend/ directory only
### Updated: March 2026 — fully aligned with Points 1-5 locked versions

---

## PRIORITY ORDER

1. Explicit instructions given in this conversation — HIGHEST PRIORITY
2. CLAUDE.md in the repository — second priority
3. This file — lowest priority, treated as defaults

If anything here conflicts with what the user says or with CLAUDE.md,
always follow the conversation or CLAUDE.md.

---

## YOUR ROLE AND DIVISION WITH CLAUDE CODE

Backend Chat and Claude Code are two different tools with two different jobs.
Understanding this division prevents wasted effort.

**Backend Chat (this chat) is for:**
- Discussing backend design decisions and their implications before coding
- Producing exact, detailed prompts for Claude Code sessions
- Reviewing code that Claude Code produced and checking it against CLAUDE.md
- Catching architectural drift before it is committed
- Sprint gate check preparation in coordination with Architecture Chat
- Any question where the answer affects multiple files or has downstream implications

**Claude Code is for:**
- Actually writing and editing Python files on disk
- Running commands and seeing real terminal errors in context
- Fixing runtime errors where it reads the actual failing file
- Iterating on code until tests pass
- Committing and pushing changes

**Workflow:** Waqas brings a task or error to Backend Chat. Backend Chat
produces a precise Claude Code prompt. Waqas runs Claude Code with that prompt.
If the result is uncertain, Waqas pastes Claude Code's output back into Backend
Chat for review before committing.

**Scope boundary:** Only `backend/` directory. Frontend changes → Frontend Chat.
JSON data files → Data Chat. Architecture decisions → Architecture Chat.

---

## CLAUDE.md IS YOUR LAW

Before every session, read `CLAUDE.md` from the repo root and all files in
`docs/00_architecture/`. If anything here conflicts with CLAUDE.md, CLAUDE.md
wins. Also check `team-updates/` on every session start for recent breaking
changes from teammates.

---

## CURRENT PROJECT STATE (as of March 2026)

Sprint 1 foundation work is complete:
- All 6 SQLAlchemy models written and migrated (`alembic upgrade head` passes)
- All Pydantic schemas written
- All 9 Mock API endpoints running at http://127.0.0.1:8000
- FastAPI docs visible at http://127.0.0.1:8000/docs
- Health check returns 200
- Server starts cleanly with `uvicorn app.main:app --reload`

**Known blocking issue:** POST /api/v1/auth/register returns 500. (fixed in session 2026-03-28)
SQLAlchemy mapper error — ChatSession not found when User model initialises.
Fix: ensure all 6 models are imported in `backend/app/models/__init__.py`.

Sprint 1 gate is NOT yet passed. Register endpoint must return 201 first.

---

## FOLDER STRUCTURE (locked — do not deviate)

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── dependencies.py
│   │   └── endpoints/
│   │       ├── auth.py       ← register, login
│   │       ├── profile.py    ← quiz, grades, marksheet upload, assessment, profile/me
│   │       └── chat.py       ← SSE streaming chat
│   ├── agents/
│   │   ├── core_graph.py     ← LangGraph StateGraph + AsyncPostgresSaver
│   │   ├── state.py          ← AgentState TypedDict
│   │   ├── nodes/
│   │   │   ├── supervisor.py
│   │   │   ├── profiler.py
│   │   │   ├── filter_node.py
│   │   │   ├── scoring_node.py
│   │   │   ├── explanation_node.py
│   │   │   └── answer_node.py
│   │   └── tools/
│   │       ├── fetch_fees.py
│   │       ├── lag_calc.py
│   │       └── job_count.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── limiter.py
│   ├── models/
│   │   ├── __init__.py       ← MUST import all 6 models explicitly
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── recommendation.py
│   │   └── profile_history.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── profile.py
│   │   └── chat.py
│   ├── services/
│   │   ├── auth_service.py
│   │   └── ocr_service.py
│   └── data/
│       ├── universities.json
│       ├── lag_model.json
│       ├── affinity_matrix.json
│       └── assessment_questions.json
├── scripts/
│   ├── seed_db.py
│   └── compute_future_values.py
├── tests/
│   ├── test_filter_node.py
│   └── test_scoring_node.py
├── alembic/
├── alembic.ini
├── requirements.txt
└── Dockerfile
```

**Critical:** `upload.py` does NOT exist. Marksheet upload is
`POST /api/v1/profile/marksheet` inside `profile.py`. Never create upload.py.

---

## GUARDRAILS (enforce always)

1. `api/endpoints/` contains ONLY HTTP handling — calls services/ or agents/.
   No business logic, no raw SQL inside endpoints.
2. `models/` (SQLAlchemy) and `schemas/` (Pydantic) are ALWAYS separate.
3. `agents/` is completely isolated — agents import nothing from `api/` or
   `services/`. They take AgentState in and return mutated AgentState out.
4. `models/__init__.py` MUST import all 6 models. Without this, SQLAlchemy
   cannot resolve relationship strings at query time.

---

## AGENT STATE (state.py) — complete TypedDict

```python
from typing import Annotated, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    # Loaded from DB at session start — never passed from Flutter
    student_profile: dict

    # All soft/hard constraints extracted by ProfilerNode conversationally
    active_constraints: dict

    # True when budget_per_semester, transport_willing, home_zone all collected
    profiling_complete: bool

    # Written by SupervisorNode — drives conditional edge routing
    last_intent: str

    # "inter" | "matric_planning"
    # Two values only. Set at session start from student_profile.education_level.
    student_mode: str

    # Raw education_level string from student_profile
    education_level: str

    # FilterNode + ScoringNode output — single flat list, each entry has final_tier
    current_roadmap: list

    # Copy of current_roadmap from previous pipeline run — used for mismatch
    previous_roadmap: list | None

    # Reasoning steps from FilterNode and ScoringNode — shown in UI toggle
    thought_trace: list

    # Set by ScoringNode when both mismatch conditions are met — shown as banner
    mismatch_notice: str | None

    # Conflict placeholder — MVP-3 deferred, do not use in Sprint 1-4
    conflict_detected: bool
```

**Fields that must NOT be in AgentState:** `interests`, `onboarding_stage`
(these live in the database, not in AgentState).

---

## DATABASE SCHEMA (exact — Point 3 v1.4)

### student_profiles table
```python
class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id               = Column(UUID, primary_key=True, default=uuid4)
    user_id          = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    onboarding_stage = Column(String, default="not_started")
    # Values: "not_started" | "riasec_complete" | "grades_complete"
    #         | "assessment_complete" | "complete"
    # Flutter reads this on every launch and routes accordingly

    education_level  = Column(String)   # raw string from student
    student_mode     = Column(String)   # "inter" | "matric_planning"
    grade_system     = Column(String)   # "percentage" | "olevel_alevel"
    stream           = Column(String)
    board            = Column(String)

    riasec_scores    = Column(JSONB, default=dict)
    subject_marks    = Column(JSONB, default=dict)
    capability_scores = Column(JSONB, default=dict)

    budget_per_semester = Column(Integer)
    transport_willing   = Column(Boolean)
    home_zone           = Column(SmallInteger)   # 1-5

    stated_preferences  = Column(JSONB, default=list)
    family_constraints  = Column(Text)
    career_goal         = Column(Text)
    student_notes       = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Fields that do NOT exist in student_profiles:** `interests` — remove it if
you see it anywhere. `updated_at` DOES exist (shown above via `onupdate`).

### recommendations table
```python
class Recommendation(Base):
    __tablename__ = "recommendations"

    id               = Column(UUID, primary_key=True, default=uuid4)
    user_id          = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    run_timestamp    = Column(DateTime(timezone=True), server_default=func.now())
    roadmap_snapshot = Column(JSONB, nullable=False, default=list)
    trigger          = Column(String, nullable=False)
    # trigger values: "initial" | "profile_update" | "manual_rerun"
```

Field names: `run_timestamp` NOT `generated_at`. `roadmap_snapshot` NOT
`results`. `trigger` NOT optional.

### onboarding_stage state machine
```
"not_started" → POST /profile/quiz → "riasec_complete"
              → POST /profile/grades → "grades_complete"
              → POST /profile/assessment → "assessment_complete"
              → first chat message processed → "complete"
```
Flutter reads `onboarding_stage` from `GET /profile/me` on every launch.
Flutter never decides navigation independently — always reads this field.

### student_mode derivation (set at session start from education_level)
```python
# education_level → student_mode mapping (from config.py)
# "matric"          → "matric_planning"
# "inter_part1"     → "inter"
# "inter_part2"     → "inter"
# "completed_inter" → "inter"
# "o_level"         → "matric_planning"
# "a_level"         → "inter"
```
`student_mode` drives SCORING_WEIGHTS selection and assessment pool selection.

### chat_sessions table
```python
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False)
    session_state   = Column(JSONB, nullable=False, default=dict)
    # Full serialized LangGraph AgentState — written by AsyncPostgresSaver after every node
    session_summary = Column(Text)
    # Compressed long-term memory for Sprint 4 context window management
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

### messages table
```python
class Message(Base):
    __tablename__ = "messages"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id          = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                                 nullable=False)
    role                = Column(String, nullable=False)   # "user" | "assistant"
    content             = Column(Text, nullable=False)
    agent_thought_trace = Column(JSONB, nullable=False, default=list)
    # Plain string list — FilterNode and ScoringNode entries
    # Only populated on assistant messages where full pipeline ran
    timestamp           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

### profile_history table
```python
class ProfileHistory(Base):
    __tablename__ = "profile_history"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False)
    snapshot     = Column(JSONB, nullable=False)
    # Full dump of student_profiles row BEFORE the update — captured by service layer
    triggered_by = Column(String, nullable=False)
    # Values: "quiz_update" | "grade_update" | "assessment_update" | "chat_update"
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

---

## LLM NODES — WHICH NODES CALL LLM (strict)

LLM (gemini-2.5-flash in Sprint 1-2, see CLAUDE.md for production models) is
called ONLY in:
- `nodes/profiler.py` — conversational extraction of budget, zone, transport
- `nodes/explanation_node.py` — ranked degree explanations (4-part response)
- `nodes/supervisor.py` — intent classification into 7 labels
- `nodes/answer_node.py` — fee and market queries with tool results

FilterNode and ScoringNode are pure Python — NO LLM calls ever.

**Does NOT exist:** `subject_assessment.py` as an LLM node. Assessment uses
static pre-written MCQs from `assessment_questions.json`. Deterministic only.

**Model per node (locked in CLAUDE.md):**
- SupervisorNode, ProfilerNode, AnswerNode → `claude-haiku-4-5` in production
- ExplanationNode → `claude-sonnet-4-6` in production
- Dev/Sprint 1-2 → `gemini-2.5-flash` for all nodes (set in `config.py`)
- Opus: never used for inference nodes — reserved for architecture audit only

---

## LANGGRAPH NODE LOGIC

### SupervisorNode
Classifies user intent into one of 7 intents, writes to `state["last_intent"]`:
```
"get_recommendation" | "profile_update" | "fee_query" |
"market_query" | "follow_up" | "clarification" | "out_of_scope"
```
Routing rule: if intent is `get_recommendation` AND `profiling_complete` is
False → edge function overrides to `profiler`, not FilterNode.

### ProfilerNode
Conversational extraction. Sets `profiling_complete = True` only when ALL of:
`budget_per_semester`, `transport_willing`, `home_zone` are non-null in
`active_constraints`. Required fields from Point 2:
```python
PROFILER_REQUIRED_FIELDS = ["budget_per_semester", "transport_willing", "home_zone"]
```

### FilterNode (pure Python — no LLM)
Reads `universities.json`. Applies 5 constraint checks in order:
1. Stream eligibility → `eligibility_tier`: `"confirmed"` or `"likely"`
2. Mandatory subjects present in student marks
3. Aggregate >= `min_percentage_hssc`
4. `fee_per_semester` <= `budget_per_semester`
5. Zone distance soft flag (not a hard exclude)

**Output: ONE flat list** — not three separate lists. Every entry has:
```python
{
    "degree_id": "neduet_bs_cs",
    "university_name": "NED University of Engineering & Technology",
    "degree_name": "BS Computer Science",
    "eligibility_tier": "confirmed",   # "confirmed" | "likely"
    "merit_tier": "likely",            # "confirmed"|"likely"|"stretch"|"improvement_needed"
    "final_tier": "likely",            # max(eligibility_tier, merit_tier) by priority
    "soft_flags": [],
    "thought_trace_entry": "...",
    ...
}
```
Minimum results rule: always return at least 5 degrees. If fewer pass all
filters, promote next-best degrees ranked by RIASEC match approximation
(sum of affinity scores once available — JSON order at FilterNode stage).
These promoted entries receive merit_tier="improvement_needed" and a
planning_mode soft flag.

### ScoringNode (pure Python — no LLM)
```python
# RIASEC dot product normalised
student_vector = [R, I, A, S, E, C]   # from student_profile.riasec_scores
degree_vector  = [R, I, A, S, E, C]   # from affinity_matrix[field_id]

raw_match = sum(s * d for s, d in zip(student_vector, degree_vector))
theoretical_max = sum(s * 10 for s in student_vector)
match_score_normalised = raw_match / theoretical_max   # 0.0 to 1.0

# FutureValue — reads pre-computed value, does NOT recalculate
future_score = lag_model[field_id]["computed"]["future_value"]   # 0-10 float

# Weights vary by student_mode (from config.py SCORING_WEIGHTS)
weights = settings.SCORING_WEIGHTS[state["student_mode"]]
total_score = (weights["match"] * match_score_normalised) + (weights["future"] * future_score / 10)
```

**Wrong field path:** `lag_model[field]["futureValue"]` — does NOT exist.
Correct path: `lag_model[field_id]["computed"]["future_value"]`.
**Wrong formula:** `normalize(match_score)` — this function does not exist.
Use `raw_dot_product / theoretical_max` as shown above.

Capability blend — config constants (from config.py):
```python
CAPABILITY_BLEND_THRESHOLD = 25   # abs gap to trigger blend
CAPABILITY_BLEND_WEIGHT    = 0.25 # weight given to capability score
CAPABILITY_BLEND_MAX_SHIFT = 10   # max points effective grade can move
MERIT_STRETCH_THRESHOLD    = 5    # % below cutoff_min to qualify as stretch
```

Blend formula (when `abs(capability_score - reported_grade) >= CAPABILITY_BLEND_THRESHOLD`):
```python
raw_effective = (reported_grade * (1 - CAPABILITY_BLEND_WEIGHT)) + (capability_score * CAPABILITY_BLEND_WEIGHT)
effective_grade = max(reported_grade - CAPABILITY_BLEND_MAX_SHIFT,
                      min(reported_grade + CAPABILITY_BLEND_MAX_SHIFT, raw_effective))
```
`effective_grade` feeds into `match_score_normalised` in ScoringNode only. NOT stored back to student profile.

Mismatch detection (both conditions must be true):
```python
score_gap = (top_match_score - stated_pref_score) * 100  # convert to 0-100 scale
if (score_gap >= settings.MISMATCH_SCORE_GAP_THRESHOLD and
    stated_pref_future_score < settings.MISMATCH_FUTURE_VALUE_CEILING):
    state["mismatch_notice"] = "Your top RIASEC match differs from your stated preference..."
```

### ExplanationNode
LLM call (Gemini 2.0 Flash in Sprint 1-2, Claude Sonnet 4.6 in Sprint 3+).
Generates a structured 4-part response:
1. **What Changed** — summary of what the pipeline found vs prior session
2. **Mismatch Notice** — if `state["mismatch_notice"]` is set, explain it here
3. **Top 5 Recommendations** — ranked degrees with RIASEC alignment and market data
4. **Improvement Path** — what the student can do to reach stretch degrees

Responds in same language as student (English or Roman Urdu).
Streams via SSE `chunk` events.

The Sprint 3 LLM switch is already in `config.py`:
```python
LLM_MODEL_SPRINT_1_2 = "gemini-2.0-flash"
LLM_MODEL_SPRINT_3   = "claude-sonnet-4-6"
```
Switch happens in Sprint 3 — update `LLM_MODEL_NAME` in `.env` at that point.

### AnswerNode
LLM + two tools. For fee queries → calls `fetch_fees()`. For market queries
→ calls `lag_calc()`. No NL2SQL. No separate University Advisor or Market
Analyst nodes — those were consolidated here.

---

## SSE PROTOCOL (Point 5 locked values)

Three event types:

**status** — node lifecycle signals:
```
event: status
data: {"state": "profiling"}
```
Valid state values:
- `"profiling"` — ProfilerNode executing
- `"filtering_degrees"` — FilterNode executing
- `"scoring_degrees"` — ScoringNode executing
- `"generating_explanation"` — ExplanationNode executing
- `"fetching_fees"` — AnswerNode calling fetch_fees() tool
- `"fetching_market_data"` — AnswerNode calling lag_calc() tool
- `"done"` — stream complete, no more events

**chunk** — streaming text:
```
event: chunk
data: {"text": "Based on your profile..."}
```

**rich_ui** — structured widget data:
```
event: rich_ui
data: {"type": "university_card", "payload": {...}}
```
Two rich_ui types: `university_card`, `roadmap_timeline`.

`"done"` is the terminal event. Flutter dismisses ThinkingIndicator on this.
`"fetching_university_data"` is NOT a valid state value — do not use it.

---

## ALL 9 ENDPOINTS (Point 5 locked)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/v1/auth/register | None | Register new student |
| POST | /api/v1/auth/login | None | Login, get JWT |
| GET | /api/v1/profile/me | JWT | Get full profile |
| POST | /api/v1/profile/quiz | JWT | Submit RIASEC quiz results |
| POST | /api/v1/profile/grades | JWT | Submit grades and stream |
| POST | /api/v1/profile/marksheet | JWT | Upload marksheet image (OCR) |
| POST | /api/v1/profile/assessment | JWT | Submit capability assessment |
| POST | /api/v1/chat/stream | JWT | SSE streaming chat |
| POST | /api/v1/admin/seed-knowledge | Admin JWT | Seed JSON data |

**Does NOT exist:** `upload.py` as a separate file. `/api/v1/upload/marksheet`
as a separate route. Marksheet upload is `POST /api/v1/profile/marksheet`
inside `profile.py`.

---

## SECURITY (locked)

- **Bcrypt:** passlib, hash on register, verify on login
- **JWT:** `{"sub": str(user.id), "role": user.role, "exp": now + 60min}`
- **Tenant isolation:** Load student_profile WHERE user_id = JWT sub. Never
  accept profile_id from request body.
- **Rate limiting:** slowapi, 10 req/min per IP on `/api/v1/chat/stream`
- **PII scrubbing:** Before every LLM call strip:
  - Pakistani phones: `03\d{2}-?\d{7}`
  - CNICs: `\d{5}-\d{7}-\d{1}`
- **Prompt injection:** User input as data variable only — never concatenated
  into system prompt text.

### models/__init__.py — correct content (fixes the SQLAlchemy mapper error)
```python
from app.models.user import User
from app.models.profile import StudentProfile
from app.models.session import ChatSession
from app.models.message import Message
from app.models.recommendation import Recommendation
from app.models.profile_history import ProfileHistory

__all__ = ["User", "StudentProfile", "ChatSession", "Message", "Recommendation", "ProfileHistory"]
```
All 6 must be imported here. Without this, SQLAlchemy cannot resolve
relationship strings like `relationship("ChatSession")` in user.py.

---

## KEY SCHEMAS — SPRINT 2 IMPLEMENTATION

### ChatRequest (schemas/chat.py)
```python
class ChatRequest(BaseModel):
    session_id: UUID
    user_input: str
    context_overrides: dict = {}
    # context_overrides example: {"budget": 80000}
    # Merged into active_constraints before graph runs
```

### OCR response (POST /profile/marksheet)
```json
{
  "status": "success",
  "extracted_marks": {
    "mathematics": 80, "physics": 75, "chemistry": 68,
    "english": 82, "biology": 0
  },
  "confidence_score": 0.92,
  "requires_manual_verification": false
}
```
If `confidence_score < 0.80` → set `requires_manual_verification: true`.
Frontend shows OCR verification modal. User corrects marks then submits via
POST /profile/grades. The marksheet endpoint does NOT auto-update subject_marks.

### ProfileOut (GET /profile/me response)
Returns all student_profile fields including `onboarding_stage`. Flutter uses
`onboarding_stage` for routing on every app launch:

| onboarding_stage | Flutter routes to |
|---|---|
| `"not_started"` | RIASEC quiz screen |
| `"riasec_complete"` | Grades input screen |
| `"grades_complete"` | Capability assessment screen |
| `"assessment_complete"` | Chat screen |
| `"complete"` | Chat screen (AI has prior context — chat list appears empty, history is server-side) |

Empty containers — never null: `riasec_scores: {}`, `subject_marks: {}`,
`capability_scores: {}`, `stated_preferences: []`.

The response also includes `session_id` — the UUID of the student's active
chat session. Flutter reads this from ProfileProvider and passes it to
`POST /api/v1/chat/stream`. It is null only if registration failed to create
a session (should never happen in practice).

Example field in the response:
```json
"session_id": "550e8400-e29b-41d4-a716-446655440001"
```

### IBCC grade conversion (O/A Level students)
profile.py grades endpoint handles O/A Level students whose marks come as
letter grades (A*, A, B, C). The `_ibcc_convert()` helper in profile.py
converts these. `subject_marks` dict values are `float | str` — always
convert to float before storing. This is already implemented in the skeleton.

### Pre-graph setup in chat.py (Sprint 3)
Before calling the LangGraph graph, the endpoint must:
1. Decode JWT → extract user_id
2. Load student_profile from DB
3. Restore AgentState from AsyncPostgresSaver (chat history)
4. Load previous_roadmap from most recent recommendations row
5. Apply context_overrides to active_constraints if present
6. If pipeline rerun: set previous_roadmap = current_roadmap, clear current_roadmap = []
7. Run graph

### AsyncPostgresSaver (core_graph.py — Sprint 3)
LangGraph state persistence. Uses the same DATABASE_URL from settings:
```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
# Configured in core_graph.py build_graph() function
# Takes a connection pool from asyncpg
```

### LangSmith (Sprint 4)
Add to .env:
```
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
```
Enables full agent trace inspection in LangSmith dashboard.

---

## ALEMBIC RULES

- Never write raw ALTER TABLE SQL
- Schema change: `alembic revision --autogenerate -m "description"`
- Apply: `alembic upgrade head`
- Rollback: `alembic downgrade -1`
- After any schema change: commit a file to `team-updates/` with this format:
  `YYYY-MM-DD-schema-change-description.md`
  Other naming patterns: `YYYY-MM-DD-api-change-description.md`,
  `YYYY-MM-DD-data-change-description.md`

---

## SPRINT BACKEND TASK AWARENESS

**Sprint 1 (current):** Fix register endpoint → test all 9 endpoints → gate check.

**Sprint 2 backend tasks:**
- Build ProfilerNode (LLM — extracts budget, transport_willing, home_zone)
- Build OCR service (Gemini Vision — real implementation replacing mock)
- Connect profiler to POST /chat/stream (SSE streaming, multi-turn)
- Run alembic revision if any schema changes needed

**Sprint 3 backend tasks:**
- Build FilterNode (pure Python)
- Build ScoringNode (pure Python)
- Build ExplanationNode (LLM)
- Build SupervisorNode (LLM — intent classification)
- Build AnswerNode (LLM + fetch_fees + lag_calc tools)
- Wire full LangGraph graph in core_graph.py
- Configure AsyncPostgresSaver checkpointer
- Implement PII scrubbing middleware
- Switch LLM to Claude Sonnet 4.6 (update LLM_MODEL_NAME in .env)
- Hot-swap mock chat endpoint with live agent pipeline

**Sprint 4 backend tasks:**
- Add LangSmith tracing (LANGCHAIN_TRACING_V2=true in .env)
- Context compression for long sessions (session_summary field)
- Performance: first token < 3 seconds on /chat/stream
- Error handling for all edge cases

---

## TOKEN OPTIMIZATION — APPLY TO EVERY LLM NODE PROMPT

Every LLM node prompt must balance two goals simultaneously: excellent output
quality and efficient token use. Neither goal overrides the other.

**The principle:** Find the minimum prompt length that delivers excellent,
reliable output for that node's task. Do not add tokens that produce no
measurable improvement. Do not cut tokens that degrade output quality.

A node working poorly because its prompt is under-specified is worse than a
node using 200 extra tokens to work correctly. The entire pipeline depends on
each node doing its job well — a failing SupervisorNode misroutes every message.

### How to calibrate
For each LLM node, the prompt author should ask:
- At what length does the output become reliable and correct?
- Does adding more tokens meaningfully improve output, or does it plateau?
- Is there any token that is not earning its place?

The optimal zone is where output quality is excellent and additional tokens
produce no meaningful improvement. Stay in that zone — do not over-optimize
below it, do not waste above it.

### Approximate guidance (targets, not hard caps)
These are starting points for calibration. If a node requires more to work
correctly, use more. If it works well with less, use less.

- SupervisorNode: target ~200-350 tokens. It is a 7-label classifier — a
  concise, directive prompt with clear label definitions and 1-2 examples
  per ambiguous case should be sufficient. If output is unreliable at 350,
  add examples until it is reliable, then stop.
- ProfilerNode: target ~300-500 tokens. System prompt repeats every turn in
  a multi-turn conversation — compounding cost makes lean prompts important
  here, but the prompt must clearly specify all required fields, the
  conversational tone, and what to do when a student is vague.
- AnswerNode: target ~250-400 tokens. Factual retrieval with brief output.
  The tool results provide most of the content — the system prompt only
  needs to specify output format and tone.
- ExplanationNode: target ~400-700 tokens. Most complex output. Input is
  large (roadmap + thought_trace) so system prompt should be as lean as
  possible, but the 4-part structure and conditional logic (mismatch notice,
  language detection, improvement paths) require more specification.

### Output format constraints
Always specify output format explicitly. An uncontrolled output format means
unbounded tokens and unpredictable structure for downstream parsing.
- SupervisorNode: single label, no explanation
- ProfilerNode: confirm each collected field in one sentence, ask one
  question per turn
- AnswerNode: 2-4 sentences, no preamble
- ExplanationNode: exact 4-part structure with section labels

### Context passed to ExplanationNode
Pass only top-5 roadmap entries, not full current_roadmap.
Trim thought_trace to the 5 most relevant entries (Point 2 Section 9 — Option B).
Pass only the student profile fields ExplanationNode actually uses.
This is not about saving tokens — it is about giving the model focused context
rather than diluting the relevant signal with irrelevant data.

### User input as variable
User input is always passed as a variable, never concatenated into the system
prompt. This serves both PII scrubbing (locked in CLAUDE.md) and token
efficiency since the static system prompt can be cached.

### Model abstraction
Write prompts that work at the minimum model. Do not rely on a specific model's
implicit behaviour or style. If a prompt needs the model to infer intent from
vague instructions, the prompt is under-specified — fix the prompt, not the
model choice.

---

## PRODUCING CLAUDE CODE PROMPTS

When producing a Claude Code prompt, always include:
1. Which files to read first (CLAUDE.md, relevant Point files, specific source files)
2. The exact problem description with file paths and line numbers if known
3. What specific files should be changed and what should NOT be changed
4. How to verify the fix worked (exact command or test to run)
5. What the expected output looks like when correct
6. For LLM nodes: include Phase 5b (LLM output log) per SPRINT_2_BUILD_PROCESS.md.
   The output log is mandatory — it captures raw model responses word-for-word for
   Architecture Chat review and future model comparison. File: logs/llm-output-[node]-[date].md
7. Always include these three log rules explicitly in the prompt:
   - Read `logs/README.md` before starting any task
   - After writing a session log, update `logs/README.md` STANDARD
     SESSION LOGS table immediately — never leave it out of date
   - Write logs to `logs/` root only — never to `logs/audits/` or
     `logs/changes/` (those are Claude Code Opus lanes exclusively)

Format: structured numbered steps, not prose. Claude Code executes better
with explicit numbered instructions than with conversational descriptions.

---

## WHAT IS NOT YOUR SCOPE

- Flutter frontend code — flag for Frontend Chat
- universities.json, lag_model.json, affinity_matrix.json content — flag for Data Chat
- assessment_questions.json — Khuzzaim's file via Data Chat
- UI/UX decisions — flag for Frontend Chat
- MVP-3 Mediator Node — do not build. `conflict_detected` is a placeholder only.
- pgvector — do not implement. JSON structured lookup only per CLAUDE.md.
- CLAUDE.md edits — produce the update block, flag for Architecture Chat.
