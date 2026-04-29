# CLAUDE.md — Single Source of Truth
## FYP: AI-Assisted Academic Career Guidance System
### Version: 2.0 — April 2026

This file is authoritative. Every Claude Code session, every specialist chat,
and every team member reads this before starting any work.
If this file conflicts with any other document, this file wins.

**Update rule:** No one edits this file directly.
Architecture Chat produces exact update blocks — user pastes them in.
Every change is traceable to an Architecture Chat session.

---

## SYSTEM OVERVIEW

An AI-powered career guidance system for Pakistani secondary school students in Karachi.
Recommends HEC-recognized bachelor's degrees from the top 20 Karachi universities based on
RIASEC interest profile, academic marks, capability assessment, budget, and market outlook.

**Three inputs per student:**
1. RIASEC interest profile — 60-question Likert quiz
2. Academic marks + stream — Matric / Inter / O Level / A Level
3. Capability assessment — 60 MCQs across 5 subjects (12 per subject)

**Output:** Ranked degree recommendations with AI explanations, market data,
eligibility tiers, merit tiers, soft flags, and full reasoning trace.

---

## TECH STACK

| Layer | Choice | Locked |
|---|---|---|
| Backend | Python 3.12 + FastAPI | ✓ |
| Agent orchestration | LangGraph v1.1 | ✓ |
| Database | PostgreSQL (Supabase hosted) + JSONB | ✓ |
| Vector search | Not used — JSON structured lookup only | ✓ |
| LLM | Gemini 2.0 Flash (Sprint 1–2), Claude Sonnet 4.6 (Sprint 3+) | ✓ |
| Frontend | Flutter — single codebase Android + Web | ✓ |
| State management | Riverpod (flutter_riverpod ^2.5.1) | ✓ |
| Rate limiting | slowapi, 10 req/min per IP on /chat/stream | ✓ |

---

## TEAM

| Member | Scope |
|---|---|
| Waqas | All `backend/` Python — FastAPI, LangGraph, SQLAlchemy, Alembic, scripts |
| Fazal | Data files — universities.json, lag_model.json, affinity_matrix.json |
| Khuzzaim | All `frontend/` Flutter — Dart code; assessment_questions.json; testing |

**Prompt engineering:** User's responsibility.
**Testing:** Khuzzaim primary, Fazal assists.
**CLAUDE.md updates:** Architecture Chat only — no direct edits.

---

## MILESTONES

| Date | Milestone |
|---|---|
| April 20 | 50% demo: login → quiz → marks → assessment → recommendation → follow-up chat |
| June 10–15 | Full system, viva-ready |
| T-14 days before viva | Code freeze — no new features to main |
| T-7 days before viva | No schema changes — bug fixes only |
| When end-to-end passes clean | `git tag v1.0-final-viva` |

**Sprint plan:**
- Sprint 1: DB + Alembic + Mock API ✓ | Flutter shells — in progress (Khuzzaim)
- Sprint 2: ProfilerNode + OCR service + onboarding screens connected to real API
- Sprint 3 ← April 20 deadline: FilterNode + ScoringNode + ExplanationNode + SSE live
- Sprint 4: Error handling + LangSmith + performance + viva prep

---

## API SURFACE

**Base prefix:** `/api/v1/` — always. Never omit.
**Auth:** `Authorization: Bearer <token>`
**JWT payload:** `{"sub": "<user_uuid>", "role": "student", "exp": <60min>}`
**Error format:** `{"error_code": "...", "message": "...", "details": [...]}`
**user_id source:** Always JWT sub — never from request body.

| # | Method | Path | Auth | File |
|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/register` | None | `endpoints/auth.py` |
| 2 | POST | `/api/v1/auth/login` | None | `endpoints/auth.py` |
| 3 | GET | `/api/v1/profile/me` | JWT | `endpoints/profile.py` |
| 4 | POST | `/api/v1/profile/quiz` | JWT | `endpoints/profile.py` |
| 5 | POST | `/api/v1/profile/grades` | JWT | `endpoints/profile.py` |
| 6 | POST | `/api/v1/profile/marksheet` | JWT | `endpoints/profile.py` |
| 7 | POST | `/api/v1/profile/assessment` | JWT | `endpoints/profile.py` |
| 8 | POST | `/api/v1/chat/stream` | JWT | `endpoints/chat.py` |
| 9 | POST | `/api/v1/admin/seed-knowledge` | JWT admin | `endpoints/profile.py` |

**No upload.py. No upload_schema.py. Marksheet is in profile.py.**
**GET /profile/me response includes `session_id: UUID` (non-null) — confirmed working, commit 2ace388.**

---

## SSE STREAMING PROTOCOL (Endpoint 8)

Three event types — no others:

```
event: status
data: {"state": "<value>"}

event: chunk
data: {"text": "<fragment>"}

event: rich_ui
data: {"type": "<type>", "payload": {...}}
```

**Status state values (7 total):**

| State | When |
|---|---|
| `"profiling"` | ProfilerNode starts |
| `"filtering_degrees"` | FilterNode starts |
| `"scoring_degrees"` | ScoringNode starts |
| `"generating_explanation"` | ExplanationNode starts |
| `"fetching_fees"` | AnswerNode calls fetch_fees() |
| `"fetching_market_data"` | AnswerNode calls lag_calc() |
| `"done"` | Stream complete — always last event |

**rich_ui types (2 total):** `university_card` (20 fields), `roadmap_timeline` (4 steps).
SupervisorNode emits no status event — internal routing only.

---

## ONBOARDING STATE MACHINE
```
"not_started"
↓  POST /profile/quiz → 200 response → RIASEC Complete screen
"riasec_complete"
↓  POST /profile/grades → 200 response → Grades Complete screen
"grades_complete"
↓  POST /profile/assessment → 200 response → Assessment Complete screen
"assessment_complete"   ← chat is available from here
↓  auto-navigate after 2–3 seconds
Chat screen (welcome state) → first message sent → pipeline runs
↓  recommendation generated
Recommendation Dashboard
```

Flutter reads `onboarding_stage` from GET /profile/me on every launch.
Frontend never decides navigation — always follows this field.

**Completion screen navigation rule:** Flutter trusts the 200 response for
in-session navigation. It does NOT call GET /profile/me again after each
step. The GET /profile/me on launch is a recovery rule only — not a per-step
polling rule.

**LangGraph pipeline initialisation:** The graph is invoked on the first
POST /api/v1/chat/stream message. There is no pre-initialisation step.
Assessment Complete screen triggers nothing on the backend — it only
auto-navigates to chat.

**Onboarding Carousel rule:** Show carousel when no token exists in
`flutter_secure_storage`. This covers both fresh install and post-logout.
No backend field required.

## FULL SCREEN FLOW (locked — no screens may be added without Architecture Chat sign-off)

```
Splash
↓
Onboarding Carousel  ← shown only when no token in flutter_secure_storage
↓
Login / Signup
↓
[if onboarding_stage = not_started]       RIASEC Quiz
↓ 200
RIASEC Complete
↓
[if onboarding_stage = riasec_complete]   Grades Input (with OCR modal)
↓ 200
Grades Complete
↓
[if onboarding_stage = grades_complete]   Capability Assessment
↓ 200
Assessment Complete (auto-nav 2–3s)
↓
[if onboarding_stage = assessment_complete] Chat — welcome state
↓ first message
Chat — active
↓ recommendation received
Recommendation Dashboard
```

**Settings and error screens are accessible outside this linear flow.**

## LOCKED SCREEN INVENTORY (15 screens — Sprint 3 complete set)

| Screen | Dart file | Status for demo |
|---|---|---|
| Splash | `screens/splash_screen.dart` | Full |
| Onboarding Carousel | `screens/onboarding/carousel_screen.dart` | Full |
| Login | `screens/auth/login_screen.dart` | Full |
| Signup | `screens/auth/signup_screen.dart` | Full |
| Forgot Password | `screens/auth/forgot_password_screen.dart` | Static "coming soon" |
| RIASEC Quiz | `screens/onboarding/riasec_quiz_screen.dart` | Full |
| RIASEC Complete | `screens/onboarding/riasec_complete_screen.dart` | Full |
| Grades Input | `screens/onboarding/grades_input_screen.dart` | Full |
| Grades Complete | `screens/onboarding/grades_complete_screen.dart` | Full |
| Capability Assessment | `screens/onboarding/assessment_screen.dart` | Full |
| Assessment Complete | `screens/onboarding/assessment_complete_screen.dart` | Full |
| Chat | `screens/chat/main_chat_screen.dart` | Full |
| Recommendation Dashboard | `screens/dashboard/recommendation_dashboard.dart` | Full |
| Settings | `screens/profile/settings_screen.dart` | Logout only; Change Password = static "coming soon" |
| Network Error | `screens/error_screen.dart` | Full |
| Student Profile | `screens/profile/profile_screen.dart` | Full |

No new screens may be added without Architecture Chat sign-off and a CLAUDE.md update.

---

## EDUCATION LEVEL DERIVATION

| `education_level` received | `student_mode` stored | `grade_system` stored |
|---|---|---|
| `"matric"` | `"matric_planning"` | `"percentage"` |
| `"inter_part1"` | `"inter"` | `"percentage"` |
| `"inter_part2"` | `"inter"` | `"percentage"` |
| `"completed_inter"` | `"inter"` | `"percentage"` |
| `"o_level"` | `"matric_planning"` | `"olevel_alevel"` |
| `"a_level"` | `"inter"` | `"olevel_alevel"` |

`student_mode` and `grade_system` are **always derived server-side** — never accepted from request body.
IBCC conversion (O/A Level grades → percentages) happens at POST /profile/grades service layer only.

---

## AGENT PIPELINE

```
User Input
    ↓
SupervisorNode  (LLM — 7 intents)
    ↓
get_recommendation + profiling_complete → FilterNode → ScoringNode → ExplanationNode
get_recommendation + profiling_incomplete → ProfilerNode
profile_update → ProfilerNode
fee_query / market_query → AnswerNode + tool
follow_up / clarification / out_of_scope → AnswerNode (no tool)
```

**Node types:**
- LLM nodes: SupervisorNode, ProfilerNode, ExplanationNode, AnswerNode
- Pure Python (no LLM ever): FilterNode, ScoringNode

**AgentState — 12 fields:**
`messages`, `student_profile`, `active_constraints`, `profiling_complete`,
`last_intent`, `student_mode`, `education_level`, `current_roadmap`,
`previous_roadmap`, `thought_trace`, `mismatch_notice`, `conflict_detected`

---

## FILTERNODE OUTPUT

Three lists — never binary pass/fail:
- `confirmed_eligible` — fully eligible stream, marks within range, budget ok
- `likely_eligible` — conditionally eligible stream (bridge course required), or marks close
- `stretch` — marks within 5% below historical cutoff minimum

**Three hard exclusions:**
1. Stream not in fully_eligible AND not in conditionally_eligible AND no conditional waiver
2. Mandatory subject missing AND no subject waiver
3. Student's unadjusted inter percentage below `min_percentage_hssc` — HEC/council
   legal minimum. This is a legal disqualification, not a merit judgment.

**Merit cutoffs never hard-exclude.** The minimum always shown is 5 degrees.
`min_percentage_hssc` is the HEC/council legal floor — it is distinct from
`cutoff_range` merit comparisons. Students below the legal floor are shown a clear
explanation with the governing council cited, not a blank exclusion.

**Merit tiers** (based on estimated_merit — composite of inter + assessment proxy when entry test exists):

| Tier | Condition |
|---|---|
| `"confirmed"` | Aggregate above historical cutoff maximum |
| `"likely"` | Aggregate within historical cutoff range |
| `"stretch"` | Within 5% below historical minimum |
| `"improvement_needed"` | More than 5% below historical minimum |

**Soft flags** (never exclude — always inform):
`over_budget`, `commute_distance`, `stretch_merit`, `improvement_needed`,
`bridge_course_required`, `policy_unconfirmed`, `eligibility_contact_university`,
`planning_mode`, `entry_test_proxy_used`, `entry_test_harder_than_assessed`

---

## SCORING FORMULAS (ScoringNode — pure Python)

```python
# RIASEC match
student_vector = [R, I, A, S, E, C]           # values 10-50 (summed Likert)
degree_vector  = [R, I, A, S, E, C]           # affinity values 1-10 from affinity_matrix.json
raw_match         = sum(s * d for s, d in zip(student_vector, degree_vector))
theoretical_max   = sum(s * 10 for s in student_vector)   # 10 = max affinity
match_score_normalised = raw_match / theoretical_max       # 0.0 – 1.0

# Total score
weights    = SCORING_WEIGHTS[student_mode]    # inter: 0.6/0.4 | matric_planning: 0.7/0.3
future_score = lag_model[field_id]["computed"]["future_value"]   # 0-10
total_score  = (weights["match"] * match_score_normalised) + (weights["future"] * future_score / 10)

# Capability blend — per-subject, applied BEFORE calculate_aggregate()
# Triggers per subject when abs(capability - reported) >= 25
effective_marks = {}
for subject, reported_grade in subject_marks.items():
    capability = capability_scores.get(subject)
    if capability is None or abs(capability - reported_grade) < 25:
        effective_marks[subject] = reported_grade
    else:
        raw_eff = (reported_grade * 0.75) + (capability * 0.25)
        effective_marks[subject] = max(reported_grade - 10, min(reported_grade + 10, raw_eff))
# effective_marks passed to calculate_aggregate() — dict[str, float], not a single float

# Estimated merit — FilterNode uses this for cutoff comparison (not ScoringNode)
# Replaces direct calculate_aggregate() in Check 3 when entry_test_weight > 0
inter_component = calculate_aggregate(subject_marks, degree["aggregate_formula"])
inter_weight = aggregate_formula["inter_weight"]
entry_test_weight = aggregate_formula["entry_test_weight"]

if entry_test_weight == 0.0:
    estimated_merit = inter_component   # no entry test — inter is everything
    proxy_used = False
else:
    # Build assessment proxy from entry_test subject weights in universities.json
    entry_test_blocks = degree["entry_test"]
    SUBJECT_MAP = {
        "math_weight": "mathematics", "physics_weight": "physics",
        "chemistry_weight": "chemistry", "biology_weight": "biology",
        "english_weight": "english"
    }
    proxy_score = 0.0
    for weight_key, subject in SUBJECT_MAP.items():
        w = entry_test_blocks.get(weight_key, 0.0)
        score = capability_scores.get(subject, 50.0)  # 50.0 = neutral default
        proxy_score += score * w
    # proxy_score is 0-100 matching entry test scale
    estimated_merit = (inter_component * inter_weight) + (proxy_score * entry_test_weight)
    proxy_used = True

# estimated_merit compared against degree["cutoff_range"]["min/max"] in FilterNode Check 3
# aggregate_used in roadmap entry = estimated_merit (not raw inter component)

# Mismatch notice (ScoringNode sets mismatch_notice when both conditions true)
score_gap = top_match_total_score - preferred_degree_total_score
if score_gap >= 0.20 and preferred_degree_future_value < 6.0:
    mismatch_notice = "..."   # ExplanationNode includes this as Part 1 of response
```

---

## RIASEC QUIZ

- **60 questions**, 10 per dimension (R I A S E C)
- **5-point Likert** per question: 1 (Strongly Dislike) → 5 (Strongly Like)
- **Scoring:** Frontend sums 10 responses per dimension — sends integer **10–50** per key
- **Questions:** Adapted from O*NET Short Form for Pakistani students, with Roman Urdu translations
- **Source file:** `RIASEC_QUIZ_QUESTIONS_v1_1.md` in project knowledge base (Khuzzaim)

---

## CAPABILITY ASSESSMENT

- **5 subjects:** mathematics, physics, chemistry, biology, english
- **12 questions per subject** (3 easy, 5 medium, 4 hard) — configurable in `config.py`
- **Pool:** 76 questions per subject per curriculum level (20E + 32M + 24H)
- **Total in JSON:** 1140 (3 curriculum levels × 5 subjects × 76)
- **Scoring:** `(correct / total) * 100` per subject — deterministic, no LLM
- **Results:** Written to `capability_scores` JSONB field — floats 0–100

**Curriculum levels:**
- `"matric"` pool ← matric + o_level students
- `"inter_part1"` pool ← inter_part1 students
- `"inter_part2"` pool ← inter_part2 + completed_inter + a_level students

---

## DATABASE — 6 TABLES

`users` | `student_profiles` | `chat_sessions` | `messages` | `recommendations` | `profile_history`

**Schema rules:**
- Alembic only — never manual `ALTER TABLE`
- All timestamps are `TIMESTAMPTZ` (DateTime with timezone=True in ORM)
- All child tables declare `ForeignKey(...)` explicitly for Alembic

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

**Key JSONB fields:**
- `riasec_scores`: `{"R": 32, "I": 45, ...}` — integers 10–50
- `subject_marks`: `{"mathematics": 87, ...}` — percentages 0–100, always stored after IBCC conversion
- `capability_scores`: `{"mathematics": 66.7, ...}` — floats 0–100
- `session_state`: owned exclusively by AsyncPostgresSaver — never write manually

---

## JSON KNOWLEDGE BASE

| File | Owner | Count | Status |
|---|---|---|---|
| `backend/app/data/universities.json` | Fazal | 20 universities | 1 of 5 priority universities done (NED) |
| `backend/app/data/lag_model.json` | Fazal | 43+ fields | Empty — blocked until all 5 universities done |
| `backend/app/data/affinity_matrix.json` | Fazal | 43+ fields | Empty — blocked until all 5 universities done |
| `backend/app/data/assessment_questions.json` | Khuzzaim | 1140 questions | Empty — populate Sprint 1 |

**Schemas:** Point 4 — `POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md`

**FutureValue lag categories** (stored in lag_model.json as `lag_type`):

| Category | layer1 | layer2 | layer3a | layer3b | Fields |
|---|---|---|---|---|---|
| `LEAPFROG` | 30% | 20% | 30% | 20% | CS/AI/Software Engineering |
| `FAST` | 35% | 25% | 24% | 16% | Cybersecurity, Digital Media, Data Science, telecommunications_engineering, business_analytics |
| `MEDIUM` | 40% | 30% | 18% | 12% | Cloud, Electrical, Biomedical Engineering, chemical_engineering, food_engineering, fintech |
| `SLOW` | 45% | 35% | 12% | 8% | Robotics, IoT, Embedded, automotive_engineering, metallurgical_engineering, materials_engineering, polymer_petrochemical_engineering, industrial_manufacturing_engineering |
| `LOCAL` | 60% | 40% | 0% | 0% | Medicine, Law, Civil Eng, Business, urban_infrastructure_engineering, construction_engineering, textile_engineering, textile_sciences, english_linguistics |

layer1=pak_now, layer2=pak_future, layer3a=world_now, layer3b=world_future. All rows sum to 1.0.
Old single `layer3` key split to fix double-counting bug (was summing to >1.0 for non-LOCAL categories).

---

## KARACHI TRANSPORT ZONES

| Zone | Areas |
|---|---|
| 1 | North Karachi, Gulberg, New Karachi, Surjani |
| 2 | Gulshan-e-Iqbal, Johar, Nazimabad, North Nazimabad |
| 3 | Defence, Clifton, Saddar, PECHS, Bahadurabad |
| 4 | Malir, Landhi, Korangi, Shah Faisal |
| 5 | SITE, Orangi, Baldia, Lyari |

Zone distance = `abs(student_zone - university_zone)`.
0–1 = easy, 2 = moderate, 3+ = difficult.
Transport is a **soft flag only** — never a hard exclusion.

---

## SECURITY RULES

- JWT sub = user UUID — never accept user_id from request body (tenant isolation)
- Bcrypt for all passwords — direct bcrypt library (passlib removed — incompatible with bcrypt 5.x)
- **PII scrubbing before every LLM call:**
  - Pakistani phone numbers: `03\d{2}[-\s]?\d{7}`
  - CNICs: `\d{5}[-\s]\d{7}[-\s]\d`
- User input placed as data variable in prompt — never concatenated into system prompt
- Rate limit: 10 req/min per IP on /chat/stream via slowapi
- Admin endpoints: require JWT role = "admin"
- seed_db.py: idempotent UPSERT only — never raw INSERT

---

## TEAM-UPDATES PROTOCOL

Before merging any change that affects another team member, commit a file to `team-updates/`:

```
Format: team-updates/YYYY-MM-DD-<type>-<description>.md
```

| Type | When | Who notifies whom |
|---|---|---|
| `schema-change` | Any Alembic migration | Waqas → Khuzzaim |
| `api-change` | Any endpoint request/response shape change | Waqas → Khuzzaim |
| `data-change` | Any JSON file structural change | Fazal → Waqas + Khuzzaim |
| `config-change` | Any constant in config.py affecting scoring or quiz | Waqas → Fazal + Khuzzaim |

---

## DEFERRED WORK — MUST NOT BE FORGOTTEN

These items are explicitly out of scope for the April 20 demo but are
confirmed required for the June 10–15 complete system. Every item here
has a decision already locked — implementation is what is deferred, not
the decision.

| # | Feature | What is needed | Decision already locked |
|---|---|---|---|
| 1 | Message history on reload | `GET /api/v1/chat/messages` endpoint returning prior session messages. Flutter loads these on chat screen open so welcome state does not appear for returning users. | OTP flow locked. Screen design stable. |
| 2 | Forgot Password | `POST /api/v1/auth/forgot-password` — accepts email, sends OTP via email service. `POST /api/v1/auth/verify-otp` — verifies code, returns short-lived reset token. `POST /api/v1/auth/reset-password` — accepts reset token + new password. Requires email service (SendGrid or equivalent) added to backend dependencies. | OTP flow locked. Screen design stable. No redesign needed. |
| 3 | Change Password | `POST /api/v1/auth/change-password` — authenticated endpoint, accepts current_password + new_password. Settings screen button already exists — just needs the endpoint wired. | Same email service dependency as Forgot Password. |
| 4 | SSE stream timeout state | Frontend: if SSE connection drops before `done` event, show specific "Recommendation is taking longer than expected — tap to retry" state, distinct from generic server error. No new backend endpoint needed. | Identified as needed — Frontend Chat to implement in Sprint 4. |
| 5 | Profile edit after onboarding | Settings screen may need edit buttons for budget, home_zone, stated_preferences. Backend: `PATCH /api/v1/profile/me` or reuse existing quiz/grades endpoints. Scope to be confirmed in Sprint 4. | Not yet decided — flag for Architecture Chat in Sprint 4. |

**API endpoints required for items 1–3 (Sprint 4):**

| Endpoint | File | Sprint |
|---|---|---|
| `GET /api/v1/chat/messages` | `endpoints/chat.py` | Sprint 4 |
| `POST /api/v1/auth/forgot-password` | `endpoints/auth.py` | Sprint 4 |
| `POST /api/v1/auth/verify-otp` | `endpoints/auth.py` | Sprint 4 |
| `POST /api/v1/auth/reset-password` | `endpoints/auth.py` | Sprint 4 |
| `POST /api/v1/auth/change-password` | `endpoints/auth.py` | Sprint 4 |

These endpoints do not exist yet. The screen designs are complete and will
not change. Implementation order: message history first (affects demo UX),
then password features.

**Sprint 4 backend code cleanup (non-urgent):**

| # | Item | Detail |
|---|---|---|
| 6 | profile_update trigger dead code | `_write_recommendation()` in chat.py has a `"profile_update"` trigger branch that never fires. `last_intent` is always `"get_recommendation"` when recommendations are written. Remove the dead branch and simplify to: `"initial" if not previous_roadmap else "manual_rerun"`. |
| 7 | AnswerNode tool status events | `"fetching_fees"` and `"fetching_market_data"` SSE status events not emitted. Flutter ThinkingIndicator shows nothing during fee/market queries. Fix requires subscribing to tool-call events in astream_events loop or emitting status events from inside answer_node. |
| 8 | _load_lag_model() and _load_affinity_matrix() caching | Both functions re-read JSON files from disk on every pipeline call. Add module-level caching once Fazal populates real data files. |
| 9 | Alembic migration missing curriculum_level | Migration file missing this column. Supabase has it. Fresh local DB setup via alembic upgrade head will fail on grades endpoint. Fix: generate new migration and apply to Supabase via SQL Editor. |
| 10 | Credential rotation | Supabase password, Gemini API key, and SECRET_KEY appeared in conversation plaintext during setup sessions. Rotate all three after demo. Details in logs/render-deployment-log-2026-04-21.md. |
| Google SSO | Removed from Login and Signup UI entirely — no placeholder button. Requires google_sign_in package + backend OAuth endpoint. Post-demo. |
| Forgot Password screen | Not built. Link present on Login as greyed no-op (onPressed: null, slate colour). OTP flow requires backend endpoint. Post-demo Sprint 4. |

---

## NAVIGATION — WHERE TO FIND DETAILED GUIDANCE

Claude Code: read CLAUDE.md first, then read the file for your component below.

| Working on | Read this file |
|---|---|
| Any backend Python file | `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md` |
| Any frontend Dart/Flutter file | `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` |
| Any JSON data file | `docs/00_architecture/DATA_CHAT_INSTRUCTIONS.md` |
| FilterNode or ScoringNode | `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md` |
| Database schema or models | `docs/00_architecture/POINT_3_DATABASE_SCHEMA_v1_4.md` |
| API endpoints | `docs/00_architecture/POINT_5_API_SURFACE_v1_2.md` |
| Claude Code rules | `docs/00_architecture/CLAUDE_CODE_RULES.md` |
| Sprint tasks and gate conditions | `docs/00_architecture/SPRINT_PLAN.md` |
| All architecture docs index | `docs/00_architecture/README.md` |
| Session history and log navigation | `logs/README.md` |
| Flutter screen implementation | `design/screen_mockups/DESIGN_HANDOFF.md` |

---

## LLM NODE MODEL ASSIGNMENTS

Each LLM node has a minimum required model and an assigned production model.
The prompt must be robust enough that any model at or above the minimum works
correctly without code changes — model swapping is a config change only.

| Node | Minimum model | Dev model (Sprint 1-2) | Production model (Sprint 3+) | Rationale |
|---|---|---|---|---|
| SupervisorNode | Any capable chat model | gemini-3.1-flash-lite-preview | claude-haiku-4-5 | Pure 7-label classification — smallest capable model is correct |
| ProfilerNode | Any capable chat model | gemini-3.1-flash-lite-preview | claude-haiku-4-5 | Multi-turn conversational extraction — straightforward if prompt is well-structured |
| AnswerNode | Any capable chat model | gemini-3.1-flash-lite-preview | claude-haiku-4-5 | Factual retrieval + brief explanation with tool results — within Haiku's capability |
| ExplanationNode | Mid-tier model minimum | gemini-3.1-flash-lite-preview | claude-sonnet-4-6 | Extended prose students read directly — Roman Urdu, nuanced career advice, 4-part structured response — quality matters |

**Model abstraction rule (locked):** Prompts must not rely on model-specific behaviour.
If a prompt works at the minimum model, it must work unchanged at any more capable
model. Swapping `LLM_MODEL_NAME` in `config.py` is the only change required to
upgrade a node's model. No prompt edits, no code changes.

**Never use Opus for inference nodes.** Opus is reserved for the pre-demo
architecture audit (Claude Code Opus, one session). Per-request LLM inference
uses Haiku (classification/extraction) or Sonnet (explanation generation) only.

---

## LOCKED DECISIONS — DO NOT REOPEN

| Decision | Choice |
|---|---|
| Agent framework | LangGraph v1.1 — not CrewAI, not OpenAI Agents |
| Vector search | Not used — JSON structured lookup only |
| Upload endpoint | No upload.py — merged into profile.py |
| Schema files | auth.py, chat.py, profile.py — no _schema suffix |
| FilterNode + ScoringNode | Pure Python — no LLM ever |
| IBCC conversion | POST /profile/grades service layer only |
| student_mode + grade_system | Derived server-side — never from request body |
| MVP-3 Parent Mediation | Permanently deferred — conflict_detected always False |
| OCR → DB write | Never — frontend confirms via POST /profile/grades |
| pgvector | Not used |
| SSE package (Flutter) | http with streaming parser — not dio |
| Mock server | Sprint 1 chat returns mock SSE — hot-swap with real graph in Sprint 3 |
| Alembic | Only method for schema changes — never manual SQL |
| RIASEC scale | 5-point Likert, summed, range 10-50 per dimension |
| Assessment questions | Static, pre-written by Khuzzaim — NOT LLM-generated |
| Minimum results shown | Always ≥5 degrees regardless of marks |
| Marks filtering | Merit cutoffs never hard-exclude — use merit tiers. Exception: `min_percentage_hssc` HEC/council legal floor IS a hard exclusion. This is a legal disqualification, not a merit judgment. |
| Merit estimation | FilterNode Check 3 uses `calculate_estimated_merit()` — composite of inter component + assessment proxy when `entry_test_weight > 0`. Assessment scores used as entry test proxy. |
| Assessment as entry test proxy | Capability scores (0-100) treated as proxy for entry test performance. Subject-matched: `math_weight` maps to `mathematics` capability score, etc. Default 50.0 when a subject score is missing. |
| Entry test difficulty tiers | Three tiers at university level — `standard`, `hard`, `extreme`. NUST=extreme, FAST=hard, all others=standard unless flagged. FilterNode adds `entry_test_harder_than_assessed` soft flag for hard/extreme. |
| Shift field | Degrees offered in multiple shifts get separate degree_id entries with `_morning`/`_evening` suffix. Single-shift degrees use `"shift": "full_day"`. No logic change in FilterNode — shift is passed through to roadmap entry for display. |
| HEC/council inter floor categories | 60%: BE/BSc Engg, MBBS/BDS, Pharm-D, DVM. 50%: BS Computing (CS/SE/AI/Cyber/IT), B.Arch, BSN, DPT. 45%: LLB, General BS Sciences, BBA/Commerce, Arts/Humanities. Stored as `min_percentage_hssc` per degree. |
| scripts/ location | backend/scripts/ — not repo root |
| out_of_scope intent routing | answer_node (polite decline) — NOT silent END |
| JWT 401 handling | No silent refresh — no refresh token endpoint exists. 401 always clears stored token and shows session expired screen. Re-login required. |
| Logout | Client-side only — clear flutter_secure_storage, navigate to login. No backend logout endpoint. JWT is stateless; no token blacklist. |
| LangGraph pipeline init | Triggered by first POST /api/v1/chat/stream message only. No pre-initialisation on assessment completion. |
| Onboarding completion nav | Flutter trusts 200 response for in-session navigation. GET /profile/me is launch-time recovery only, not per-step polling. |
| Chat welcome state | Hardcoded on frontend. Three static suggested question chips. Shown when local messages list is empty. No backend endpoint. |
| Message history on reload | NOT implemented for April 20 demo. Fresh app load always shows welcome state regardless of prior sessions. Deferred — see DEFERRED WORK section. |
| Forgot Password (demo) | Static "coming soon" message. No backend endpoint for demo. Deferred — see DEFERRED WORK section. |
| Change Password (demo) | Static "coming soon" message in Settings screen. No backend endpoint for demo. Deferred — see DEFERRED WORK section. |
| Password reset flow (post-demo) | OTP via email — NOT a reset link. Requires email service (e.g. SendGrid). Screen design: email field → OTP field → new password field. This sequence is locked so the screen does not need redesign when implemented. |
| Onboarding Carousel trigger | Show when no token in flutter_secure_storage. Covers fresh install and post-logout. No backend field. |
| Screen count | 16 screens locked. No additions without Architecture Chat sign-off and CLAUDE.md update. |
| Flutter screen designs | Complete — 16 screens locked in design/screen_mockups/. DESIGN_HANDOFF.md is the implementation guide. DESIGN_SYSTEM_TOKENS.md is the token reference. No new screens without Architecture Chat sign-off per CLAUDE.md screen inventory. |
| Backend deployment | Render free tier — https://fyp-career-guidance-api.onrender.com. Auto-deploys on push to main (backend/ changes only). Cold start ~50s after inactivity — send warm-up request before demo. Dockerfile CMD does not include --loop asyncio (Linux/Render does not need it). |
| Windows local dev command | uvicorn app.main:app --reload --loop asyncio — required on Windows due to psycopg3 + ProactorEventLoop incompatibility. On Linux/Mac/Render: uvicorn app.main:app --reload (no flag needed). |
| context_overrides merge | payload.context_overrides is merged into existing active_constraints, not replaced. Fix applied in chat.py post-core-graph session. |
| profile_update trigger dead code | In _write_recommendation(), the "profile_update" trigger branch never fires because last_intent is always "get_recommendation" when recommendations are written. Dead code, not wrong. Sprint 4 cleanup. |
| Flutter package name | com.fyp.career_guidance — must be updated in android/app/build.gradle.kts (namespace + applicationId), android/app/src/main/AndroidManifest.xml, and android/app/src/main/kotlin/ folder rename. Currently com.example.frontend_app (placeholder — fix before demo). |
| Frontend project state | Valid runnable Flutter project in frontend/. pubspec.yaml correct. flutter pub get already run. main.dart is stock counter — Khuzzaim replaces with Riverpod app entry point as first task. |
| Frontend backend URL | https://fyp-career-guidance-api.onrender.com — set in frontend/lib/services/api_service.dart. Never use localhost in committed code. |
| AnswerNode field mapping maintenance | When new field_ids added to lag_model.json, corresponding nickname mappings must be added to MARKET_EXTRACTION_SYSTEM_PROMPT in answer_node.py in the same commit. See DATA_CHAT_INSTRUCTIONS.md for the exact format. |
| LLM model per node | SupervisorNode, ProfilerNode, AnswerNode → Haiku 4.5 in production. ExplanationNode → Sonnet 4.6 in production. Dev uses gemini-3.1-flash-lite-preview (free tier, 500 RPD, outperforms 2.5 Flash on benchmarks). Opus never used for inference. See LLM NODE MODEL ASSIGNMENTS section. |
| Model abstraction | Prompts must work at minimum model and above without code changes. Model swap = config.py change only. |
| Token optimization | Every LLM node prompt balances output quality against token efficiency. Find the minimum prompt length that delivers excellent, reliable output — do not cut tokens that degrade quality, do not add tokens that produce no improvement. Output format explicitly constrained. User input passed as variable. See TOKEN OPTIMIZATION section in BACKEND_CHAT_INSTRUCTIONS.md. |
| Remember Me checkbox | UI-only — token always stored in flutter_secure_storage regardless of checkbox state. No backend remember_device field exists. Post-demo if needed. |
| flutter_screenutil | Added post-build for responsive scaling. Version ^5.9.3. Baseline 390×844. All fontSize → .sp, SizedBox heights → .h, widths → .w, icons → .r, BorderRadius → .r, EdgeInsets → .r/.h/.w. Approved April 2026. |

---

*CLAUDE.md v1.0 — March 2026 (initial)*
*CLAUDE.md v1.1 — March 2026 (added: SSE protocol, FilterNode details, onboarding state machine,*
*education_level derivation, merit tiers, soft flags, transport zones, assessment pool,*
*lag categories, mismatch trigger, PII scrubbing regex, team-updates protocol)*
*CLAUDE.md v1.2 — March 2026 (state management locked: Riverpod; navigation index added)*
*CLAUDE.md v1.3 — April 2026 (nav index updated to Point 2 v2.1; Sprint 1 backend complete; out_of_scope routing locked)*
*CLAUDE.md v1.4 — April 2026 (logs/README.md added to navigation index; Sprint 1 Flutter shells marked complete)*
*CLAUDE.md v1.5 — April 2026 (screen inventory locked: 15 screens; full onboarding flow with completion screens; JWT 401 handling, logout, pipeline init, welcome state, carousel trigger locked; deferred work section added: message history, forgot/change password, SSE timeout state)*
*CLAUDE.md v1.6 — April 2026 (design phase complete: 16 screen mockups, DESIGN_HANDOFF.md, DESIGN_SYSTEM_TOKENS.md added to design/screen_mockups/; screen count corrected to 16; Student Profile screen added to locked inventory; design/screen_mockups/DESIGN_HANDOFF.md added to navigation index)*
*CLAUDE.md v1.7 — April 2026 (NED University data committed to universities.json; 13 new field_ids added to canonical list; lag_model and affinity_matrix field counts updated to 43+)*
*CLAUDE.md v1.8 — April 2026 (Opus audit fixes landed: FutureValue weights corrected layer3→layer3a/layer3b; capability blend changed to per-subject dict; compute_future_values.py rewritten to read Point 4 schema fields directly)*
*CLAUDE.md v1.9 — April 2026 (FilterNode merit estimation redesigned: assessment proxy for entry test, estimated_merit replaces raw inter comparison; HEC/council hard floor as third hard exclusion; shift field added to degree schema; entry test difficulty tiers locked; HEC minimum percentage categories locked)*
*CLAUDE.md v2.0 — April 2026 (LLM node model assignments locked: Haiku for SupervisorNode/ProfilerNode/AnswerNode, Sonnet for ExplanationNode; model abstraction rule locked; token optimization principle locked; dev model updated to gemini-2.5-flash)*
*CLAUDE.md v2.1 — April 2026 (dev model switched to gemini-3.1-flash-lite-preview — better benchmarks than 2.5 Flash, free tier 500 RPD; langchain-anthropic added to requirements.txt for easy Claude production switch; LLM output log standard added to SPRINT_2_BUILD_PROCESS.md)*
*CLAUDE.md v2.2 — April 2026 (backend demo-ready: all nodes wired, Render deployment live at fyp-career-guidance-api.onrender.com, Supabase persistent, AsyncPostgresSaver confirmed working; Windows --loop asyncio requirement locked; context_overrides merge fix applied; Sprint 4 cleanup items 6-10 logged)*
*CLAUDE.md v2.3 — April 2026 (frontend project valid and runnable; Android package name fix required; frontend development flow documented in FRONTEND_SPRINT_BUILD_PROCESS.md)*