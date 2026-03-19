# Point 1 — FastAPI App Structure
## FYP: AI-Assisted Academic Career Guidance System
### Status: CONSOLIDATED — v2.0
### Change Log:
### v1.0 — Initial lock
### v1.1 — curriculum_level expanded to 3 values, transport zones, matric planning
###         mode, education_level, improvement_needed tier, soft filter philosophy
### v1.2 — Full O/A Level student handling: IBCC conversion, grade_system field,
###         stream inference, unusual combination handling, O Level guidance logic
### v1.3 — scripts/ folder added to repo structure (compute_future_values.py)
### v1.4 — answer_node.py added to nodes/, recommendation.py added to models/
### v1.5 — planning_mode added to soft flags table; recommendation.py added to decisions table
### v2.0 — Consolidated: all detail from v1.0–v1.5 merged into single authoritative file

---

## FINAL FOLDER STRUCTURE

```
backend/
├── app/
│   ├── main.py                          ← FastAPI app object, router registration, lifespan hooks
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py              ← POST /auth/register, POST /auth/login
│   │       │   ├── chat.py              ← POST /chat/stream (SSE)
│   │       │   └── profile.py           ← GET /profile/me, POST /profile/quiz,
│   │       │                               POST /profile/grades, POST /profile/marksheet,
│   │       │                               POST /profile/assessment
│   │       └── dependencies.py          ← get_db, get_current_user, require_admin
│   ├── agents/
│   │   ├── state.py                     ← AgentState TypedDict
│   │   ├── core_graph.py                ← LangGraph StateGraph + AsyncPostgresSaver
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
│   ├── services/
│   │   ├── auth_service.py
│   │   └── ocr_service.py
│   ├── models/
│   │   ├── user.py
│   │   ├── profile.py
│   │   ├── session.py
│   │   ├── message.py
│   │   ├── recommendation.py
│   │   └── profile_history.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── profile.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   └── data/
│       ├── universities.json            ← schema locked in Point 4
│       ├── lag_model.json               ← schema locked in Point 4
│       ├── affinity_matrix.json         ← schema locked in Point 4
│       └── assessment_questions.json    ← schema locked in Point 4
├── tests/
│   ├── test_filter_node.py
│   └── test_scoring_node.py
├── alembic/
│   ├── versions/
│   └── env.py
├── scripts/                             ← Developer/data tools. NOT part of running server.
│   ├── compute_future_values.py         ← Fazal runs this to recompute FutureValue scores
│   └── seed_db.py                       ← Seeds PostgreSQL from JSON files
├── alembic.ini
├── requirements.txt
├── .env.example
└── Dockerfile
```

---

## LAYER-BY-LAYER RATIONALE

### `api/v1/endpoints/`
HTTP boundary only. Each file handles request parsing and delegates to `services/` or
`agents/`. Zero business logic. Zero raw SQL. The `v1/` prefix enables future `/v2/`
routes without breaking existing clients — costs nothing now, prevents rewrites later.

**Endpoint files (3 total, not 4):**
- `auth.py` — register and login only
- `chat.py` — SSE streaming only
- `profile.py` — all profile-building operations: quiz, grades, marksheet upload,
  assessment, get profile

**Why marksheet upload is in `profile.py` and not a separate `upload.py`:**
The upload exists solely to populate `subject_marks` in the student profile. It is not a
general-purpose file storage endpoint. A separate `upload.py` would imply a generality
that doesn't exist. All profile-building routes live together in `profile.py`.

### `agents/`
**No FastAPI imports inside this directory. Ever.**

Every agent node must be runnable in a Python console without starting a server. If
any node imports from `fastapi`, it cannot be tested in isolation, and bugs hide until
full integration — which is the worst time to find them.

Nodes take `AgentState`, return mutated `AgentState`. That is the complete contract.

### `services/`
Business logic that is not a graph node. Called directly by API endpoints.

- `auth_service.py` — JWT creation, Bcrypt hashing, token validation
- `ocr_service.py` — Gemini Vision calls for marksheet parsing

These are not agent nodes because they don't participate in the LangGraph graph.
Keeping them separate from endpoints makes them independently testable.

### `models/` vs `schemas/` — ALWAYS SEPARATE
`models/` = SQLAlchemy ORM = how data is stored in Postgres.
`schemas/` = Pydantic = what goes in and out of the API.

These must never import from each other. Mixing them causes:
1. Database internals exposed through the API (security problem)
2. FastAPI dependency injection circular import failures (debugging nightmare)

### `core/`
App-wide infrastructure. Three files, no more.
- `config.py` — reads `.env`, exposes typed settings via Pydantic Settings. All
  tuneable constants live here — never hardcoded in nodes or endpoints.
- `security.py` — Bcrypt + JWT only
- `database.py` — SQLAlchemy engine and session factory

### `data/`
Runtime application dependencies loaded at server startup. These ship inside the Docker
image alongside the code that reads them. This is why they live inside `app/` and not at
the repo root. The repo root `/data/raw/` is for human-reference research sources only.

### `scripts/`
Developer and data tools. Never imported by the server. Never in Docker image.
Two files:
- `compute_future_values.py` — reads raw data from each field entry in
  `lag_model.json`, applies per-lag-category weights and lag confidence
  multiplier, writes `computed.future_value` back to the JSON. Fazal runs
  this once during Phase A data build and once per semester when data updates.
- `seed_db.py` — seeds PostgreSQL from JSON files on first deploy.

**Why scripts/ is at backend/ root, not inside app/:** These tools are not
application modules. Placing them inside app/ would make pytest discover them
as test targets and create import path confusion.

### `tests/`
At `backend/tests/`, NOT `backend/app/tests/`. If tests are inside the `app/` package,
pytest treats them as application modules, causing import path collisions.

---

## WHAT WAS EXPLICITLY NOT ADDED

| Pattern | Reason not added |
|---|---|
| `repositories/` layer | Adds abstraction with no benefit at this team size and timeline |
| `middlewares/` folder | PII scrubbing and rate limiting configured in `main.py` directly |
| `utils/` folder | Becomes a dumping ground. Code belongs in `core/`, a service, or an agent tool |
| `upload.py` endpoint | Merged into `profile.py` — upload exists only to populate subject_marks |

---

## STUDENT MODES — TWO DISTINCT PIPELINES

Determined during onboarding Screen 2 by the student's `education_level` selection.
Stored in `student_profiles.student_mode` and carried in `AgentState.student_mode`.

### Mode 1 — Inter Mode (primary)
For students in Inter Part 1, Inter Part 2, completed Inter, or A Levels.
Full pipeline: FilterNode applies all checks including merit cutoff tiers.
All five constraint checks active.

### Mode 2 — Matric Planning Mode
For students currently in Matric or O Levels (matric equivalent).
FilterNode skips merit cutoff checks entirely — no Inter marks to compare.
Stream check replaced by planning question: "What stream are you considering for Inter?"
ScoringNode runs on RIASEC + capability scores only with modified weights (match: 0.7,
future: 0.3) — no marks-based component.
ExplanationNode uses planning-framing output instead of recommendation-framing output.

Example planning-framing output:
*"To reach NED BS CS, take Pre-Engineering in Inter and aim for 80%+ aggregate.
Your assessment shows your Mathematics foundation is solid — strengthen Physics in
Part 1."*

**FilterNode and ExplanationNode check student_mode.
ScoringNode uses config weights per mode.
ProfilerNode and SupervisorNode are mode-agnostic.**

---

## EDUCATION LEVELS — COMPLETE MAPPING TABLE

| education_level | student_mode | curriculum_level | grade_system |
|---|---|---|---|
| `"matric"` | `"matric_planning"` | `"matric"` | `"percentage"` |
| `"inter_part1"` | `"inter"` | `"inter_part1"` | `"percentage"` |
| `"inter_part2"` | `"inter"` | `"inter_part2"` | `"percentage"` |
| `"completed_inter"` | `"inter"` | `"inter_part2"` | `"percentage"` |
| `"o_level"` | `"matric_planning"` | `"matric"` | `"olevel_alevel"` |
| `"a_level"` | `"inter"` | `"inter_part2"` | `"olevel_alevel"` |

**`grade_system`** is a field in `student_profiles`. When `"olevel_alevel"`, the
`POST /profile/grades` endpoint runs IBCC conversion before storing marks as
percentages. After conversion, the rest of the pipeline treats O/A Level students
identically to Pakistani board students — no special-casing downstream.

---

## ONBOARDING — THREE SEQUENTIAL SCREENS

The `onboarding_stage` field in `student_profiles` tracks progress. Flutter reads this
on every app launch via `GET /profile/me` and routes the student to exactly where they
left off — whether they closed the app mid-RIASEC, mid-grades, or mid-assessment.
The frontend never decides navigation independently — it always follows `onboarding_stage`.

`onboarding_stage` progression:
```
"not_started" → "riasec_complete" → "grades_complete" → "assessment_complete"
```

**App resume:** If student closes app mid-onboarding, they return to the exact screen
they left. If `onboarding_stage = "assessment_complete"`, they go directly to chat
with their prior session restored via AsyncPostgresSaver.

**Extensibility:** Adding a new onboarding screen requires: new endpoint, new
`onboarding_stage` value, new Flutter screen. Existing screens and the chat graph
are unaffected.

### Screen 1 — RIASEC Quiz
60 personality/interest questions, 10 per RIASEC dimension. 5-point Likert per question (1 = Strongly Dislike → 5 = Strongly Like). Scores summed per dimension. Range: 10–50 per dimension.
Endpoint: `POST /profile/quiz`
Writes: `riasec_scores` to `student_profiles`
Sets: `onboarding_stage = "riasec_complete"`

### Screen 2 — Academic Profile (O/A Level aware)

**For Pakistani board students (Matric, Inter Part 1, Inter Part 2, Completed Inter):**
Student enters:
- Education level (determines `student_mode` + `curriculum_level`)
- Stream (Pre-Engineering, Pre-Medical, ICS, Commerce, Humanities)
- Subject marks as percentages
- Board (Karachi Board, Federal Board, AKU, Cambridge, Other)

**For O Level students:**
Student selects education level = O Level, then enters subject grades.
Screen presents two sub-modes:

*Sub-mode A — IBCC certificate available (preferred):*
Student enters the final IBCC percentage directly. Most accurate. Stored as-is.

*Sub-mode B — IBCC certificate not yet obtained:*
Student enters grades per subject (A*, A, B, C, D, E, U).
On Submit (not before — conversion is not real-time), system applies IBCC
approximation table:

| Grade | Marks used |
|---|---|
| A* | 90 (conservative approximation — see note) |
| A | 85 |
| B | 75 |
| C | 65 |
| D | 55 |
| E | 45 |
| U | 0 |

**A* note:** IBCC publishes A* equivalent marks per subject per exam session
(values range ~90–95 depending on subject difficulty that year). Since the exact
value is session-specific and unknown in advance, the system uses 90 as a conservative
approximation. Screen shows disclaimer: *"A* marks vary by subject and session. This
estimate uses 90%. Your actual IBCC percentage may be higher. Update this once you
receive your IBCC certificate."*

Converted percentages are stored in `subject_marks`. The pipeline never sees raw
grades again.

**For A Level students:**
Same two sub-modes as O Level (IBCC certificate or grade entry).
Student enters 3 principal subjects (minimum).
Additional Mathematics and Further Mathematics are NOT counted as principal subjects
per IBCC rules — screen excludes them from principal subject slots.
Students may add a 4th+ subject (e.g., Urdu) to improve overall IBCC equivalence.

After grade entry for O Level or A Level, ProfilerNode handles stream confirmation
conversationally in the first chat session (Stage 3).

Endpoint: `POST /profile/grades`
Writes: `subject_marks`, `stream` (if Pakistani board), `education_level`,
        `student_mode`, `grade_system`
Sets: `onboarding_stage = "grades_complete"`

### Screen 3 — Capability Assessment
12 MCQs per subject × 5 subjects = 60 questions total.
Questions drawn from pool matching the student's `curriculum_level`.
O Level students get matric pool. A Level students get inter_part2 pool.
Endpoint: `POST /profile/assessment`
Writes: `capability_scores` to `student_profiles`
Sets: `onboarding_stage = "assessment_complete"`

After Screen 3: student enters chat. Prior session restored via AsyncPostgresSaver
if one exists.

---

## O/A LEVEL — STREAM HANDLING IN PROFILER NODE

Because O/A Level students don't have a formal Pakistani stream, ProfilerNode handles
stream confirmation as an additional required step during the first chat session,
triggered when `grade_system == "olevel_alevel"`.

### A Level Stream Inference and Confirmation

ProfilerNode infers stream from A Level subject combination and presents it for
confirmation:

| A Level subjects | Inferred stream |
|---|---|
| Physics + Chemistry + Mathematics | Pre-Engineering equivalent |
| Biology + Chemistry + Physics | Pre-Medical equivalent |
| Mathematics + Computer Science + any | ICS equivalent |
| Business Studies + Accounting + Economics | Commerce equivalent |
| Other | Humanities / General |

ProfilerNode message example:
*"Based on your A Level subjects — Physics, Chemistry, and Mathematics — you appear to
be on a Pre-Engineering track. Is that right?"*
Student confirms or corrects.

**Unusual combinations (e.g., Mathematics + Biology + Chemistry, no Physics):**
These don't map cleanly to any standard stream. The system does not block or force an
assignment. ProfilerNode says:
*"Your subject combination doesn't fall into one standard stream. I'll include degrees
from multiple tracks in your results. Note that Engineering programs typically require
Physics at A Level — for those specific programs, contact the university admissions
office directly to confirm your eligibility."*

FilterNode still runs for all degrees. ExplanationNode adds an
`eligibility_contact_university` soft flag note to affected Engineering degrees.

### O Level Stream Guidance

O Level students are in matric_planning mode — they don't have A Level subjects yet.
ProfilerNode asks what they're interested in and recommends which A Level subjects to
take.

**If student expresses interest in a clear direction:**
ProfilerNode recommends the standard subject combination for that direction.

**If student says they want both Medical AND Engineering, or says they're unsure:**
ProfilerNode responds:
*"If you want to keep both Medicine and Engineering options open, consider taking
Mathematics, Physics, Chemistry, and Biology at A Level. This combination qualifies
you for both Pre-Engineering and Pre-Medical tracks. Be aware this is four subjects
instead of the minimum three — it's a heavier workload. Many students manage it, but
it requires strong time management. Would you like me to proceed with both tracks in
your plan?"*

**If O Level student has already selected a poor combination for their stated goal:**
ProfilerNode flags it directly:
*"To apply for Engineering programs, universities typically require Physics and
Mathematics at A Level. Your current plan doesn't include Physics — this would close
off most Engineering options. Would you like to reconsider your A Level subject
selection?"*

The system recommends. It never instructs. Final choice is always the student's.

---

## ASSESSMENT ARCHITECTURE

### What the assessment is
A structured capability screening completed before the chat session begins.

**Primary purpose:** Detect whether reported exam marks reflect genuine ability or
external factors (tutoring pressure, rote learning, grade inflation). Provides a second
signal alongside self-reported grades for ScoringNode to use.

**Secondary purpose:** Entry test benchmarking — ExplanationNode uses capability scores
to flag which subjects to strengthen for specific university entry tests.

### What it is NOT
- Not LLM-generated questions — LLMs produce questions with incorrect answer keys for
  calculation-heavy subjects like Mathematics and Physics. Deterministic scoring would
  be broken.
- Not delivered conversationally through the Profiler Node.
- Not dynamic — questions are static, verified, pre-written by Khuzzaim.

### Subjects Assessed (5 total)
Mathematics, Physics, Chemistry, Biology, English (analytical)

All five subjects are assessed regardless of the student's stated preference or stream.
Rationale: the stated preference is an input to the system, not a constraint on what
we measure. Hidden aptitude must be discoverable — a student who says "I want CS" might
have stronger Biology aptitude that makes Medicine a better match.

### Curriculum Levels — Three Values

| curriculum_level | Pool contains |
|---|---|
| `"matric"` | Matric syllabus topics only |
| `"inter_part1"` | FSc Part 1 topics — no calculus, no organic chemistry |
| `"inter_part2"` | Full FSc — all Part 1 topics plus Part 2-specific topics |

**Question tagging approach:** Every question is tagged with its `curriculum_level`.
A `inter_part2` student's pool includes all `inter_part1`-tagged questions plus
`inter_part2`-tagged ones — the assessment engine filters by tag at selection time.
Khuzzaim writes one unified set with accurate level tags, not three separate banks.

```python
EDUCATION_TO_CURRICULUM = {
    "matric":           "matric",
    "inter_part1":      "inter_part1",
    "inter_part2":      "inter_part2",
    "completed_inter":  "inter_part2",
    "o_level":          "matric",
    "a_level":          "inter_part2"
}
```

### Question Pool Per Subject Per Curriculum Level

| Difficulty | Pool size | 12-question session | 20-question session |
|---|---|---|---|
| Easy | 20 | 3 | 5 |
| Medium | 32 | 5 | 8 |
| Hard | 24 | 4 | 7 |
| **Total** | **76** | **12** | **20** |

Bell curve rationale: medium-difficulty questions produce the most aptitude signal.
Easy questions most students answer correctly regardless of ability (low signal).
Hard questions most students fail regardless of ability (low signal).
The medium band discriminates between strong and average students (high signal).

### Scaling Flexibility
The session draw config is a single variable in `config.py`:

```python
ASSESSMENT_QUESTIONS_PER_SESSION = {
    "easy": 3,
    "medium": 5,
    "hard": 4
}
```

To scale to 20 questions per subject (5 easy, 8 medium, 7 hard), change only this
variable. No data file changes. No schema changes. No endpoint changes. The pool of
76 questions supports up to 4 non-repeating sessions at 20 questions/session.

### Repetition Protection
At 12 questions/session: 6+ sessions before any difficulty band repeats.
At 20 questions/session: 3–4 sessions before any difficulty band repeats.
In practice a student takes the assessment once. Repetition is a non-issue.

### Entry Test Benchmarking
ExplanationNode compares `capability_scores` against per-university entry test
difficulty profiles stored in `universities.json`. If a student scores below 65% in
a subject heavily weighted in a target university's entry test, the explanation
includes subject-strengthening advice. This is a prompt instruction in ExplanationNode
— no new node, no new data structure beyond what's in `universities.json`.

### Delivery
Structured Flutter quiz screen (same UI component as RIASEC quiz, reused).
Endpoint: `POST /profile/assessment`
Scoring: deterministic — `(correct_answers / total_questions) * 100` per subject.
Results written to `capability_scores` in student profile before chat begins.

### Domain-to-AgentState Mapping — In Code, Not JSON
```python
DOMAIN_TO_STATE_FIELD = {
    "mathematics": "capability_scores.mathematics",
    "physics":     "capability_scores.physics",
    "chemistry":   "capability_scores.chemistry",
    "biology":     "capability_scores.biology",
    "english":     "capability_scores.english"
}
```

The JSON file stores `"domain": "mathematics"`. The code owns the mapping from domain
to where the score lives in AgentState. These never cross.

---

## ASSESSMENT_QUESTIONS.JSON — SCHEMA PREVIEW
(Full schema locked in Point 4 alongside other JSON files)

```json
{
  "id": "math_inter_part2_042",
  "subject": "mathematics",
  "curriculum_level": "inter_part2",
  "topic": "calculus",
  "difficulty": "medium",
  "question": "What is the derivative of x³ with respect to x?",
  "options": ["x²", "3x²", "3x³", "x⁴/4"],
  "correct_index": 1
}
```

Fields:
- `id` — unique string, format: `{subject}_{level}_{number}`
- `subject` — `"mathematics"` | `"physics"` | `"chemistry"` | `"biology"` | `"english"`
- `curriculum_level` — `"matric"` | `"inter_part1"` | `"inter_part2"`
- `topic` — specific topic within the subject (for debugging and pool analysis)
- `difficulty` — `"easy"` | `"medium"` | `"hard"`
- `question` — full question text
- `options` — array of exactly 4 strings
- `correct_index` — integer 0–3, index into options array

---

## PROFILER NODE — REQUIRED AND OPTIONAL FIELDS

```python
PROFILER_REQUIRED_FIELDS = [
    "budget_per_semester",    # Rs. amount
    "transport_willing",      # bool — willing to travel far?
    "home_zone",              # int 1-5 — student's Karachi zone
]

PROFILER_OPTIONAL_FIELDS = [
    "stated_preferences",     # list — degree fields mentioned
    "family_constraints",     # str — family expectations
    "career_goal",            # str — post-graduation goal
    "student_notes",          # str — freeform context
]
```

`profiling_complete = True` when all `PROFILER_REQUIRED_FIELDS` are non-null.

For O/A Level students, stream confirmation is an additional required step before
`profiling_complete = True`, triggered by `grade_system == "olevel_alevel"`.

**Extensibility:** Add a field name to either list. ProfilerNode's completion check
and LLM prompt automatically pick it up. No node rewrite required.

---

## TRANSPORT ZONES — KARACHI

| Zone | Areas |
|---|---|
| 1 | North Karachi, Gulberg, New Karachi, Surjani |
| 2 | Gulshan-e-Iqbal, Johar, Nazimabad, North Nazimabad |
| 3 | Defence, Clifton, Saddar, PECHS, Bahadurabad |
| 4 | Malir, Landhi, Korangi, Shah Faisal |
| 5 | SITE, Orangi, Baldia, Lyari |

Each university in `universities.json` has a `zone` integer (1–5).
Zone distance = `abs(student_zone - university_zone)`.
0–1 = easy commute, 2 = moderate, 3+ = difficult.
Transport is always a soft flag. Never a hard exclusion.

---

## FILTER NODE — SOFT FILTER PHILOSOPHY

### Hard Exclusions — Only Two Conditions
1. Stream has no pathway (not in `fully_eligible_streams` OR `conditionally_eligible_streams`) AND no conditional stream waiver exists
2. Mandatory subject missing from student's marks AND no subject waiver exists

**Marks never produce a hard exclusion.** Low-marks students still see all degrees,
ranked by RIASEC match score with merit tiers and improvement paths clearly shown.

### Merit Tiers
| merit_tier | Condition |
|---|---|
| `"confirmed"` | Aggregate above historical cutoff maximum |
| `"likely"` | Aggregate within historical cutoff range |
| `"stretch"` | Within 5% below historical minimum |
| `"improvement_needed"` | More than 5% below historical minimum |

### Soft Flags (never exclude — always inform)
| type | Trigger |
|---|---|
| `over_budget` | Fee exceeds stated budget |
| `commute_distance` | Zone difference ≥ 2 |
| `stretch_merit` | stretch merit tier |
| `improvement_needed` | improvement_needed merit tier — includes subject-specific advice |
| `bridge_course_required` | Conditional stream or subject waiver applies |
| `policy_unconfirmed` | `policy_pending_verification: true` in JSON |
| `eligibility_contact_university` | Unusual A Level combination — student must verify directly |
| `planning_mode` | All entries in matric_planning mode — includes Inter stream/marks guidance |

### Minimum Display Rule
Always show ≥5 degrees regardless of merit tier, ranked by RIASEC match score.
Student with very low marks sees 5 best aptitude matches with improvement paths.
Zero results is never an acceptable outcome.

---

## CONFIG.PY — CONSTANTS REFERENCE

All tuneable system constants. Never hardcoded in nodes or endpoints.

```python
ASSESSMENT_QUESTIONS_PER_SESSION = {"easy": 3, "medium": 5, "hard": 4}

CAPABILITY_BLEND_THRESHOLD = 25        # abs gap before blend triggers
CAPABILITY_BLEND_WEIGHT    = 0.25      # weight of capability in blended grade
CAPABILITY_BLEND_MAX_SHIFT = 10        # max points shift from blending

SCORING_WEIGHTS = {
    "inter":            {"match": 0.6, "future": 0.4},
    "matric_planning":  {"match": 0.7, "future": 0.3}
}

FUTURE_VALUE_WEIGHTS = {
    "LEAPFROG": {"layer1": 0.30, "layer2": 0.20, "layer3": 0.50},
    "FAST":     {"layer1": 0.35, "layer2": 0.25, "layer3": 0.40},
    "MEDIUM":   {"layer1": 0.40, "layer2": 0.30, "layer3": 0.30},
    "SLOW":     {"layer1": 0.45, "layer2": 0.35, "layer3": 0.20},
    "LOCAL":    {"layer1": 0.60, "layer2": 0.40, "layer3": 0.00}
}

LAG_CONFIDENCE = {
    "LEAPFROG": 1.00,
    "FAST":     0.95,
    "MEDIUM":   0.85,
    "SLOW":     0.70,
    "LOCAL":    1.00
}

PROFILER_REQUIRED_FIELDS = ["budget_per_semester", "transport_willing", "home_zone"]
PROFILER_OPTIONAL_FIELDS = ["stated_preferences", "family_constraints",
                             "career_goal", "student_notes"]

MERIT_STRETCH_THRESHOLD       = 5     # % below cutoff_min to qualify as "stretch"
FILTER_MINIMUM_RESULTS_SHOWN  = 5     # always show at least this many degrees
CHAT_RATE_LIMIT               = "10/minute"

LLM_MODEL_SPRINT_1_2 = "gemini-2.0-flash"
LLM_MODEL_SPRINT_3   = "claude-sonnet-4-6"

MISMATCH_SCORE_GAP_THRESHOLD     = 20  # min gap to trigger mismatch notice
MISMATCH_FUTURE_VALUE_CEILING    = 6   # pref FV must be below this too
ROADMAP_SIGNIFICANT_CHANGE_COUNT = 2   # min top-5 changes to show "What Changed"
```

---

## DECISIONS LOCKED IN POINT 1

| Decision | Choice |
|---|---|
| Upload endpoint location | Merged into `profile.py` as `POST /profile/marksheet` |
| API versioning | All routes prefixed `/api/v1/` from day one |
| Tests location | `backend/tests/`, not `backend/app/tests/` |
| scripts/ location | `backend/scripts/` — not inside app/ |
| compute_future_values.py | In scripts/ — run by Fazal, never by server |
| Assessment delivery | Structured pre-chat flow, NOT Profiler Node conversational |
| Assessment questions | Static, verified, pre-written by Khuzzaim — NOT LLM-generated |
| Subjects assessed | Mathematics, Physics, Chemistry, Biology, English (all 5 regardless of stream) |
| Questions per session | 12 (3 easy, 5 medium, 4 hard) — configurable via single `config.py` variable |
| Pool size per subject per level | 76 (20 easy, 32 medium, 24 hard) |
| Curriculum levels | 3 values: matric / inter_part1 / inter_part2 (tag-based, not separate files) |
| O Level assessment pool | matric pool |
| A Level assessment pool | inter_part2 pool |
| Domain mapping | In code (`scoring_node.py`), not in JSON |
| LLM role in assessment | Interpretation of scores only — never question generation |
| Student modes | "inter" and "matric_planning" — determined by education_level |
| education_level values | matric / inter_part1 / inter_part2 / completed_inter / o_level / a_level |
| O Level student_mode | matric_planning |
| A Level student_mode | inter |
| grade_system field | "percentage" or "olevel_alevel" |
| IBCC conversion timing | On Submit of Screen 2 — not real-time |
| A* approximation | 90% with disclaimer shown on screen |
| IBCC certificate path | Enter percentage directly if certificate available |
| A Level principal subjects | Minimum 3; Additional Maths and Further Maths excluded per IBCC rules |
| A Level 4th subject | Allowed (e.g., Urdu) to improve IBCC overall equivalence |
| A Level stream inference | ProfilerNode confirms conversationally in first chat session |
| Unusual A Level combos | Inform student + `eligibility_contact_university` flag — never block |
| O Level stream guidance | Recommend A Level subjects — never instruct — student decides |
| O Level unsure students | Suggest 4-subject combo (Maths+Physics+Chem+Bio) with workload warning |
| Transport | 5 zones, soft flag only, never hard exclusion |
| home_zone | Required field — ProfilerNode collects conversationally |
| Marks filtering | Never hard-exclude — use merit_tier instead |
| improvement_needed tier | 4th merit tier — subject-specific improvement advice generated |
| Minimum display | Always ≥5 degrees regardless of merit tier |
| planning_mode soft flag | Added to every entry in matric_planning mode — not an exclusion |
| recommendation.py model | Stores one roadmap snapshot per pipeline run per user |
| App resume | onboarding_stage field — Flutter reads on every launch |
| Application deadlines | Static in universities.json — 2025 cycle data, staleness labelled |
| RIASEC quiz format | 60 questions, 10 per dimension, 5-point Likert (1–5 per question), summed per dimension, range 10–50 |
| RIASEC aggregation | SUM — frontend sums 10 responses per dimension and sends integer 10–50 per key |
| RIASEC items | Adapted from O*NET Short Form for Pakistani students; Roman Urdu alongside each question |

---

*Point 1 v1.0 — March 2026 (initial lock)*
*Point 1 v1.1 — March 2026 (curriculum levels, transport zones, student modes, soft filter philosophy)*
*Point 1 v1.2 — March 2026 (full O/A Level handling: IBCC conversion, stream inference, unusual combos)*
*Point 1 v1.3 — March 2026 (scripts/ folder: compute_future_values.py, seed_db.py)*
*Point 1 v1.4 — March 2026 (answer_node.py added to nodes/; recommendation.py added to models/)*
*Point 1 v1.5 — March 2026 (planning_mode soft flag; recommendation.py in decisions table)*
*Point 1 v2.0 — March 2026 (consolidated: all detail from v1.0–v1.5 merged into single file)*
*Point 1 v2.1 — March 2026 (RIASEC quiz: 30→60 questions, scale corrected to 5-point Likert summed, range 10–50)*
