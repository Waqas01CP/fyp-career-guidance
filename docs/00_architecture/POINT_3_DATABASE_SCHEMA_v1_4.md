# Point 3 — Database Schema
## FYP: AI-Assisted Academic Career Guidance System
### Status: COMPLETE AND LOCKED
### Date: March 2026
### Change Log:
### v1.0 — Initial lock. Supersedes schema in BACKEND_CHAT_INSTRUCTIONS.md.
###         All Point 1 + Point 2 field additions incorporated.
###         recommendations table fully redesigned per Point 2 decision.
### v1.1 — Two gaps fixed:
###         (1) ForeignKey added to all ORM model Column definitions (was missing
###             from all 5 child tables — Alembic would not have generated FK
###             constraints without this).
###         (2) board field added to student_profiles DDL, ORM, GradesSubmission,
###             ProfileOut, profile_history snapshot, and decisions table.
### v1.2 — roadmap_snapshot entry fields completed (capability_adjustment_applied,
###         effective_grade_used, eligibility_note added per Point 2);
###         MarksheetUploadResponse schema added.
### v1.3 — Five issues patched from comprehensive audit:
###         (1) All DDL TIMESTAMP columns corrected to TIMESTAMPTZ to match
###             SQLAlchemy DateTime(timezone=True) — DDL and ORM now consistent.
###         (2) student_notes added to ProfileOut (was in DDL and ORM, missing
###             from schema).
###         (3) MarksheetUploadResponse moved from schemas/upload.py to
###             schemas/profile.py — upload.py does not exist per Point 1 folder
###             structure (schemas/ has auth.py, chat.py, profile.py only).
###         (4) roadmap_snapshot field count corrected to 15 (aggregate_used is
###             the 15th field, from FilterNode output in Point 2).
###         (5) v1.1 changelog entry (2) restored (was overwritten during v1.2
###             patch).

---

## OVERVIEW

Six tables. No more.

| Table | Purpose |
|---|---|
| `users` | Authentication — email, password hash, role |
| `student_profiles` | Full student record — marks, RIASEC, capability, constraints, onboarding state |
| `chat_sessions` | LangGraph AgentState checkpointed here via AsyncPostgresSaver |
| `messages` | Per-message log with thought trace |
| `recommendations` | Roadmap snapshot per pipeline run |
| `profile_history` | Immutable audit trail of profile changes |

**Alembic manages all schema changes. No manual ALTER TABLE. Ever.**

---

## TABLE 1 — `users`

### SQL DDL

```sql
CREATE TABLE users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR     UNIQUE NOT NULL,
    password_hash VARCHAR     NOT NULL,
    role          VARCHAR     NOT NULL DEFAULT 'student',  -- 'student' | 'admin'
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### SQLAlchemy ORM (`models/user.py`)

```python
import uuid
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role          = Column(String, nullable=False, default="student")
    created_at    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    profile         = relationship("StudentProfile", back_populates="user", uselist=False)
    sessions        = relationship("ChatSession", back_populates="user")
    history         = relationship("ProfileHistory", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")
```

### Notes
- `role` is `"student"` by default. Only `"admin"` can call `POST /api/v1/admin/seed-knowledge`.
- JWT payload: `{"sub": str(user.id), "role": user.role, "exp": datetime + 60min}`.
- Never return `password_hash` in any API response.

---

## TABLE 2 — `student_profiles`

This is the most important table. It stores everything the LangGraph pipeline reads.

### SQL DDL

```sql
CREATE TABLE student_profiles (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Onboarding state machine
    onboarding_stage   VARCHAR     NOT NULL DEFAULT 'not_started',
    -- Values: 'not_started' | 'riasec_complete' | 'grades_complete' | 'assessment_complete'

    -- Education classification (set on Screen 2 submit)
    education_level    VARCHAR,
    -- Values: 'matric' | 'inter_part1' | 'inter_part2' | 'completed_inter' | 'o_level' | 'a_level'

    student_mode       VARCHAR,
    -- Values: 'inter' | 'matric_planning'
    -- Derived from education_level but stored for fast reads in FilterNode/ExplanationNode

    grade_system       VARCHAR,
    -- Values: 'percentage' | 'olevel_alevel'
    -- When 'olevel_alevel', POST /profile/grades runs IBCC conversion before storing

    stream             VARCHAR,
    -- Values: 'Pre-Engineering' | 'Pre-Medical' | 'ICS' | 'Commerce' | 'Humanities'
    -- NULL for O/A Level students until ProfilerNode confirms conversationally

    board              VARCHAR,
    -- Values: 'Karachi Board' | 'Federal Board' | 'AKU' | 'Cambridge' | 'Other'
    -- NULL for O/A Level students (Cambridge implicit via education_level = 'a_level'/'o_level')
    -- Stored for future use — not read by any pipeline node in v1

    -- Assessment scores (JSONB — full schemas below)
    riasec_scores      JSONB       NOT NULL DEFAULT '{}',
    subject_marks      JSONB       NOT NULL DEFAULT '{}',
    capability_scores  JSONB       NOT NULL DEFAULT '{}',

    -- Profiler fields — required
    budget_per_semester INTEGER,
    transport_willing   BOOLEAN,
    home_zone          SMALLINT,
    -- Values: 1 | 2 | 3 | 4 | 5 (Karachi zone, see Point 1 zone table)

    -- Profiler fields — optional (collected conversationally)
    stated_preferences JSONB       NOT NULL DEFAULT '[]',
    -- List of degree fields the student has mentioned: ["CS", "Engineering"]
    family_constraints TEXT,
    career_goal        TEXT,
    student_notes      TEXT,

    created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One profile per user — enforced at DB level
CREATE UNIQUE INDEX student_profiles_user_id_unique ON student_profiles(user_id);

-- Trigger to auto-update updated_at on any row change
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_student_profiles_updated_at
    BEFORE UPDATE ON student_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### SQLAlchemy ORM (`models/profile.py`)

```python
import uuid
from sqlalchemy import (
    Column, String, Integer, SmallInteger, Boolean,
    DateTime, Text, ForeignKey, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    __table_args__ = (UniqueConstraint("user_id"),)

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                                 nullable=False)

    onboarding_stage    = Column(String, nullable=False, default="not_started")
    education_level     = Column(String)
    student_mode        = Column(String)
    grade_system        = Column(String)
    stream              = Column(String)
    board               = Column(String)

    riasec_scores       = Column(JSONB, nullable=False, default=dict)
    subject_marks       = Column(JSONB, nullable=False, default=dict)
    capability_scores   = Column(JSONB, nullable=False, default=dict)

    budget_per_semester = Column(Integer)
    transport_willing   = Column(Boolean)
    home_zone           = Column(SmallInteger)

    stated_preferences  = Column(JSONB, nullable=False, default=list)
    family_constraints  = Column(Text)
    career_goal         = Column(Text)
    student_notes       = Column(Text)

    created_at          = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at          = Column(DateTime(timezone=True), server_default=func.now(),
                                 onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")
```

### JSONB Field Schemas

**`riasec_scores`** — written by `POST /profile/quiz`, read by ScoringNode:
```json
{
  "R": 32,
  "I": 45,
  "A": 28,
  "S": 31,
  "E": 38,
  "C": 42
}
```
Keys are exactly: `R`, `I`, `A`, `S`, `E`, `C`. Values are integers 10–50. Computed by
summing 10 Likert responses (each 1–5) per dimension on the frontend before submission.
Range: 10 (all Strongly Dislike) to 50 (all Strongly Like).

**`subject_marks`** — written by `POST /profile/grades` (after IBCC conversion if applicable),
read by FilterNode and ScoringNode:
```json
{
  "mathematics": 87,
  "physics": 72,
  "chemistry": 65,
  "english": 80,
  "biology": 0
}
```
Keys are lowercase subject names. Values are percentage integers 0–100.
O/A Level grades converted to percentages before storage — pipeline never sees raw letter grades.

**`capability_scores`** — written by `POST /profile/assessment`, read by ScoringNode
and ExplanationNode:
```json
{
  "mathematics": 58.3,
  "physics": 61.0,
  "chemistry": 75.0,
  "biology": 80.0,
  "english": 66.7
}
```
Keys are exactly the five assessed subjects. Values are floats:
`(correct_answers / total_questions) * 100`. Always all five keys — zero-filled if not yet assessed.

**`stated_preferences`** — written by ProfilerNode, read by ExplanationNode:
```json
["Computer Science", "Engineering"]
```
List of degree fields the student has expressed interest in during the conversation.
May be empty list `[]` if student expressed no preference.

### Education Level → Derived Fields Mapping

When `POST /profile/grades` is called, the endpoint derives and stores these fields:

| `education_level` value | `student_mode` stored | `grade_system` stored |
|---|---|---|
| `"matric"` | `"matric_planning"` | `"percentage"` |
| `"inter_part1"` | `"inter"` | `"percentage"` |
| `"inter_part2"` | `"inter"` | `"percentage"` |
| `"completed_inter"` | `"inter"` | `"percentage"` |
| `"o_level"` | `"matric_planning"` | `"olevel_alevel"` |
| `"a_level"` | `"inter"` | `"olevel_alevel"` |

The endpoint never accepts `student_mode` or `grade_system` from the request body — they
are always derived server-side from `education_level`.

### `onboarding_stage` State Machine

```
"not_started"
      ↓ POST /profile/quiz
"riasec_complete"
      ↓ POST /profile/grades
"grades_complete"
      ↓ POST /profile/assessment
"assessment_complete"   ← chat is available from this state onward
```

Flutter reads `onboarding_stage` from `GET /profile/me` on every launch and routes
accordingly. Frontend never decides navigation independently.

---

## TABLE 3 — `chat_sessions`

### SQL DDL

```sql
CREATE TABLE chat_sessions (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_state   JSONB       NOT NULL DEFAULT '{}',
    -- Full serialized LangGraph AgentState — written by AsyncPostgresSaver after every node
    session_summary TEXT,
    -- Compressed long-term memory for context window management (populated in Sprint 4)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_active     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX chat_sessions_user_id_idx ON chat_sessions(user_id);
```

### SQLAlchemy ORM (`models/session.py`)

```python
import uuid
from sqlalchemy import Column, DateTime, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                             nullable=False)
    session_state   = Column(JSONB, nullable=False, default=dict)
    session_summary = Column(Text)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_active     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user     = relationship("User", back_populates="sessions")
    messages = relationship("Message", back_populates="session")
```

### `session_state` JSONB — AgentState Contract

`session_state` is owned and written exclusively by `AsyncPostgresSaver`. The code does not
manually write JSON to this column. However, for documentation and debugging, the structure
mirrors `AgentState` from `agents/state.py`:

```json
{
  "messages": [],
  "student_profile": {},
  "active_constraints": {},
  "profiling_complete": false,
  "last_intent": "",
  "student_mode": "inter",
  "education_level": "inter_part2",
  "current_roadmap": [],
  "previous_roadmap": null,
  "thought_trace": [],
  "mismatch_notice": null,
  "conflict_detected": false
}
```

`conflict_detected` is always `false` in v1. Placeholder only — MVP-3 permanently deferred.

### Notes
- One session per student is the typical case in v1. The schema supports multiple sessions
  per user (for future use) but the application currently loads the most recent session.
- `last_active` is updated by the `/chat/stream` endpoint after each successful response —
  **not** inside the graph nodes.
- `session_summary` is `NULL` in Sprint 1–3. Sprint 4 populates it for context compression.

---

## TABLE 4 — `messages`

### SQL DDL

```sql
CREATE TABLE messages (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          UUID        NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role                VARCHAR     NOT NULL,
    -- Values: 'user' | 'assistant'
    content             TEXT        NOT NULL,
    agent_thought_trace JSONB       NOT NULL DEFAULT '[]',
    -- Populated only on 'assistant' messages that triggered the full pipeline
    -- (get_recommendation intent). Empty array for all other messages.
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX messages_session_id_idx ON messages(session_id);
```

### SQLAlchemy ORM (`models/message.py`)

```python
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id          = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                                 nullable=False)
    role                = Column(String, nullable=False)
    content             = Column(Text, nullable=False)
    agent_thought_trace = Column(JSONB, nullable=False, default=list)
    timestamp           = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    session = relationship("ChatSession", back_populates="messages")
```

### `agent_thought_trace` JSONB Schema

Plain string list. Written by FilterNode and ScoringNode, stored after ExplanationNode completes.
Only populated on assistant messages where a full pipeline run occurred.

```json
[
  "NED BS CS — stream Pre-Engineering: CONFIRMED | aggregate 82% in range [80.5%-87.2%]: LIKELY | fee 27.5k <= budget 60k: PASS → likely_eligible",
  "FAST BS CS — fee 75k > budget 60k: FILTERED",
  "KU MBBS — stream Pre-Engineering not in [Pre-Medical]: BLOCKED",
  "NED BS CS — RIASEC match 0.74 | FutureValue 9.0 | total_score 0.804",
  "FAST BS SE — RIASEC match 0.71 | FutureValue 8.5 | total_score 0.766"
]
```

Plain strings. Human-readable. Shown to student via "Show Reasoning" toggle in the frontend.
No JSON inside individual trace entries — just strings.

---

## TABLE 5 — `recommendations`

This table stores one snapshot per pipeline run. Designed in Point 2. Replaces the
original schema in BACKEND_CHAT_INSTRUCTIONS.md which had a generic `results JSONB` column.

### SQL DDL

```sql
CREATE TABLE recommendations (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    run_timestamp     TIMESTAMPTZ NOT NULL DEFAULT now(),
    roadmap_snapshot  JSONB       NOT NULL DEFAULT '[]',
    -- Ordered list of all non-excluded degrees from the pipeline run
    trigger           VARCHAR     NOT NULL
    -- Values: 'initial' | 'profile_update' | 'manual_rerun'
);

CREATE INDEX recommendations_user_id_idx ON recommendations(user_id);
CREATE INDEX recommendations_run_timestamp_idx ON recommendations(run_timestamp DESC);
```

### SQLAlchemy ORM (`models/recommendation.py`)

```python
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id          = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                              nullable=False)
    run_timestamp    = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    roadmap_snapshot = Column(JSONB, nullable=False, default=list)
    trigger          = Column(String, nullable=False)

    user = relationship("User", back_populates="recommendations")
```

### `roadmap_snapshot` JSONB Schema

Ordered array of all non-excluded degrees from the completed pipeline run, sorted by
`total_score` descending. This is `state["current_roadmap"]` at the moment ExplanationNode
completes — written by `core_graph.py` as a post-node side effect, not inside any node.

```json
[
  {
    "degree_id": "ned_bscs",
    "university_id": "ned",
    "university_name": "NED University",
    "degree_name": "BS Computer Science",
    "total_score": 0.804,
    "match_score_normalised": 0.74,
    "future_score": 9.0,
    "merit_tier": "likely",
    "eligibility_tier": "confirmed",
    "eligibility_note": null,
    "soft_flags": ["stretch_merit"],
    "aggregate_used": 82.5,
    "fee_per_semester": 27500,
    "capability_adjustment_applied": true,
    "effective_grade_used": 79.5
  },
  {
    "degree_id": "fast_bsse",
    "university_id": "fast",
    "university_name": "FAST-NUCES",
    "degree_name": "BS Software Engineering",
    "total_score": 0.766,
    "match_score_normalised": 0.71,
    "future_score": 8.5,
    "merit_tier": "confirmed",
    "eligibility_tier": "likely",
    "eligibility_note": "Requires bridge course for Pre-Medical students",
    "soft_flags": ["over_budget", "bridge_course_required"],
    "aggregate_used": 82.5,
    "fee_per_semester": 75000,
    "capability_adjustment_applied": false,
    "effective_grade_used": 82.5
  }
]
```

15 fields per entry. The 14 fields in Point 2's AgentState comment (`degree_id`,
`university_id`, `university_name`, `degree_name`, `merit_tier`, `soft_flags`,
`total_score`, `match_score_normalised`, `future_score`, `capability_adjustment_applied`,
`effective_grade_used`, `eligibility_tier`, `eligibility_note`, `fee_per_semester`) plus
`aggregate_used` which appears in Point 2's FilterNode output section.

- `aggregate_used` — raw student aggregate before any capability blend
- `effective_grade_used` — grade actually used for scoring; equals `aggregate_used` when no
  blend was applied, differs when `capability_adjustment_applied` is `true`
- `eligibility_note` — `null` when stream is fully eligible; populated string when
  conditionally eligible or an unusual subject combination applies
- `capability_adjustment_applied` — `true` when gap between reported grade and capability
  score was ≥25 points, triggering the blend formula

### How `trigger` is Determined

```python
# In core_graph.py, after ExplanationNode completes:
def determine_trigger(state: AgentState) -> str:
    if state.get("previous_roadmap") is None:
        return "initial"
    elif state["last_intent"] == "profile_update":
        return "profile_update"
    else:
        return "manual_rerun"
```

### How `previous_roadmap` Is Loaded

At session start, `core_graph.py` reads the most recent row from `recommendations` for this
`user_id` and loads `roadmap_snapshot` into `state["previous_roadmap"]`. If no prior row
exists, `previous_roadmap` is `None`. This is what ExplanationNode uses to detect
"What Changed" between runs.

---

## TABLE 6 — `profile_history`

Immutable audit trail. Never updated — only inserted. One row per profile change event.

### SQL DDL

```sql
CREATE TABLE profile_history (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    snapshot     JSONB       NOT NULL,
    -- Full copy of student_profiles row at the time of this event
    triggered_by VARCHAR     NOT NULL,
    -- Values: 'quiz_update' | 'grade_update' | 'assessment_update' | 'chat_update'
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX profile_history_user_id_idx ON profile_history(user_id);
```

### SQLAlchemy ORM (`models/profile_history.py`)

```python
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base

class ProfileHistory(Base):
    __tablename__ = "profile_history"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
                          nullable=False)
    snapshot     = Column(JSONB, nullable=False)
    triggered_by = Column(String, nullable=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="history")
```

### `snapshot` JSONB Schema

Full dump of the `student_profiles` row at the time of the event. Written by the service
layer before the profile is updated — so the snapshot captures the state *before* the change.

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "onboarding_stage": "grades_complete",
  "education_level": "inter_part2",
  "student_mode": "inter",
  "grade_system": "percentage",
  "stream": "Pre-Engineering",
  "board": "Karachi Board",
  "riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
  "subject_marks": {"mathematics": 87, "physics": 72},
  "capability_scores": {},
  "budget_per_semester": 60000,
  "transport_willing": true,
  "home_zone": 2,
  "stated_preferences": [],
  "family_constraints": null,
  "career_goal": null,
  "student_notes": null,
  "updated_at": "2026-03-13T12:00:00Z"
}
```

### `triggered_by` Values

| Value | When written |
|---|---|
| `"quiz_update"` | After `POST /profile/quiz` updates `riasec_scores` |
| `"grade_update"` | After `POST /profile/grades` updates `subject_marks` and `board` |
| `"assessment_update"` | After `POST /profile/assessment` updates `capability_scores` |
| `"chat_update"` | After ProfilerNode writes new fields (budget, zone, preferences, etc.) |

---

## ALEMBIC — MIGRATION RULES

```bash
# NEVER run manual SQL to change schema. Always Alembic.

# Generate a new migration after changing a model:
alembic revision --autogenerate -m "description_of_change"

# Apply all pending migrations:
alembic upgrade head

# Roll back one migration:
alembic downgrade -1

# Check current state:
alembic current
alembic history
```

**After any schema change:**
1. Commit the new migration file to `alembic/versions/`
2. Create a file in `/team-updates/schema-change-YYYY-MM-DD.md` describing:
   - What table(s) changed
   - What the frontend needs to know (new field in API response? field renamed?)
   - What the data team needs to know (new JSONB key expected in any JSON file?)
3. Run `alembic upgrade head` on all environments

**Migration file naming convention:** `{YYYYMMDD}_{short_description}.py`

---

## PYDANTIC SCHEMAS SUMMARY (`schemas/`)

These are the request/response shapes for each endpoint. Models and schemas are always
separate — schemas never import from models.

Point 1 locks the schemas/ folder to three files: `auth.py`, `chat.py`, `profile.py`.
All endpoint schemas live in these three files. There is no `upload.py`.

### `schemas/auth.py`
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

### `schemas/profile.py`
```python
class QuizSubmission(BaseModel):
    responses: dict[str, int]  # {"R": 32, "I": 45, ...} — summed Likert scores, range 10–50 per key

class GradesSubmission(BaseModel):
    education_level: str
    stream: str | None = None           # None for O/A Level students
    subject_marks: dict[str, float]     # Raw — IBCC conversion applied server-side
    board: str | None = None            # None for O/A Level students

class AssessmentSubmission(BaseModel):
    responses: dict[str, list[int]]     # {"mathematics": [1, 0, 1, ...], ...}
    # Per-subject list of 0/1 correct flags matching question order

class MarksheetUploadResponse(BaseModel):
    status: str                          # "success" | "partial" | "failed"
    extracted_marks: dict[str, float]    # {"mathematics": 80, "physics": 75, ...}
    confidence_score: float              # 0.0 – 1.0
    requires_manual_verification: bool  # True when confidence_score < 0.80

# Rule: if confidence_score < 0.80, requires_manual_verification is always True
# regardless of any other condition. Frontend shows the OCR verification modal
# and blocks chat entry until the student confirms or corrects the extracted marks.

class ProfileOut(BaseModel):
    id: UUID
    onboarding_stage: str
    education_level: str | None
    student_mode: str | None
    grade_system: str | None
    stream: str | None
    board: str | None
    riasec_scores: dict
    subject_marks: dict
    capability_scores: dict
    budget_per_semester: int | None
    transport_willing: bool | None
    home_zone: int | None
    stated_preferences: list
    family_constraints: str | None
    career_goal: str | None
    student_notes: str | None
    updated_at: datetime
```

### `schemas/chat.py`
```python
class ChatRequest(BaseModel):
    session_id: UUID
    user_input: str
    context_overrides: dict = {}   # e.g., {"budget": 60000}

class SSEEvent(BaseModel):
    event: str   # 'status' | 'chunk' | 'rich_ui'
    data: dict
```

### SSE Event Shapes
```python
# Status event — emitted as pipeline nodes begin executing
{"event": "status", "data": {"state": "filtering_degrees"}}

# Chunk event — streamed text from ExplanationNode or AnswerNode
{"event": "chunk", "data": {"text": "Based on your profile..."}}

# Rich UI event — structured data for frontend to render a card
{"event": "rich_ui", "data": {"type": "university_card", "payload": {...}}}
```

---

## SECURITY RULES AT THE DATABASE LEVEL

- **Tenant isolation:** Every query touching `student_profiles`, `chat_sessions`,
  `messages`, `recommendations`, or `profile_history` must include
  `WHERE user_id = <JWT sub>`. Never accept a `user_id` from the request body.
- **No raw SQL in endpoints.** Endpoints call `services/` or `agents/`. Services use
  SQLAlchemy ORM. Agents do not touch the database directly (except via AsyncPostgresSaver).
- **PII scrubbing:** Regex strip Pakistani phone numbers and CNICs from `content` in
  `messages` before any LLM call. The stored message in the DB is unstripped — scrubbing
  happens only in the LLM prompt pipeline.

---

## DECISIONS LOCKED IN POINT 3

| Decision | Choice |
|---|---|
| Number of tables | 6 — users, student_profiles, chat_sessions, messages, recommendations, profile_history |
| Schema change method | Alembic only — no manual ALTER TABLE ever |
| Timestamp type | `TIMESTAMPTZ` (TIMESTAMP WITH TIME ZONE) — matches `DateTime(timezone=True)` in all ORM models |
| ForeignKey in ORM models | All child-table `user_id` and `session_id` columns declare `ForeignKey(...)` — required for Alembic to generate FK constraints |
| `student_profiles.student_mode` | Stored explicitly — derived from education_level but not recomputed on read |
| `student_profiles.grade_system` | Stored — IBCC conversion done at write time, never at read time |
| `student_profiles.stream` | Nullable — NULL for O/A Level until ProfilerNode confirms |
| `student_profiles.board` | Stored — collected on Screen 2, NULL for O/A Level, not read by pipeline nodes in v1 but preserved for future use |
| `student_profiles.stated_preferences` | JSONB list — replaces `interests` field from original baseline |
| `student_profiles.onboarding_stage` | State machine with 4 values — frontend always follows this field |
| IBCC conversion location | `POST /profile/grades` endpoint service layer — not in any agent node |
| `recommendations.roadmap_snapshot` entry fields | 15 fields per entry — 14 from Point 2 AgentState spec plus `aggregate_used` from Point 2 FilterNode output |
| `recommendations.trigger` | 'initial' / 'profile_update' / 'manual_rerun' — determined by core_graph.py |
| `recommendations.run_timestamp` | Replaces `generated_at` from original baseline |
| `recommendations` write location | `core_graph.py` post-ExplanationNode side effect — not inside any node |
| `previous_roadmap` loading | At session start from most recent `recommendations` row — None if no prior run |
| `messages.agent_thought_trace` | Populated only on assistant messages from full pipeline runs |
| `profile_history` snapshot timing | Captured BEFORE the profile change (pre-change state) |
| `profile_history.triggered_by` | 4 values: quiz_update / grade_update / assessment_update / chat_update |
| `chat_sessions.session_state` | Written exclusively by AsyncPostgresSaver — never manually |
| `chat_sessions.session_summary` | NULL in Sprint 1–3, populated for context compression in Sprint 4 |
| `conflict_detected` in AgentState | Always False in v1 — placeholder for MVP-3, permanently deferred |
| schemas/ folder | 3 files only: auth.py, chat.py, profile.py — no upload.py (marksheet upload is in profile.py per Point 1) |
| pgvector | Not used. JSON structured lookup only. This is intentional and locked. |
| Tenant isolation | user_id from JWT sub only — never from request body |
| `riasec_scores` value range | Integers 10–50 per dimension — sum of 10 Likert responses (1–5 each) |
| `riasec_scores` aggregation | Frontend sums per dimension before POST /profile/quiz — backend stores directly |

---

*Point 3 v1.0 — March 2026 (initial lock — supersedes schema in BACKEND_CHAT_INSTRUCTIONS.md)*
*Point 3 v1.1 — March 2026 (ForeignKey in all ORM models; board field added throughout)*
*Point 3 v1.2 — March 2026 (roadmap_snapshot 15-field entry; MarksheetUploadResponse added)*
*Point 3 v1.3 — March 2026 (TIMESTAMPTZ in all DDL; student_notes in ProfileOut; MarksheetUploadResponse moved to schemas/profile.py; field count corrected to 15; v1.1 changelog restored)*
*Point 3 v1.4 — March 2026 (riasec_scores range corrected to 10–50 summed integers; QuizSubmission comment updated; profile_history example values corrected)*