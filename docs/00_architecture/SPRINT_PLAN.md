# Sprint Plan
## FYP: AI-Assisted Academic Career Guidance System

Read CLAUDE.md first. This document contains the granular task breakdown.
Items marked [GATE] must be fully complete before the next sprint starts.
Each sprint ends with an Opus Integration Chat gate check — do not skip this.

**Dates:** Sprint 1 starts now. April 20 is the hard demo deadline (Sprint 3 end).

---

## PRE-SPRINT — Complete before Sprint 1 begins

**Waqas:**
- [ ] Confirm Docker Desktop installed and `docker-compose up -d` starts PostgreSQL
- [ ] Decide state management: Provider or Riverpod — tell Khuzzaim
- [ ] Update the TBD line in CLAUDE.md with the decision
- [ ] Add Point files (1–6 + RIASEC) to `docs/00_architecture/` and push

**Fazal:**
- [ ] Clone repo: `git clone https://github.com/Waqas01CP/fyp-career-guidance.git`
- [ ] Read `docs/00_architecture/FAZAL_DATA_GUIDE.md` fully before writing any JSON
- [ ] Install Python, VS Code, and `pip install jsonschema`

**Khuzzaim:**
- [ ] Clone repo
- [ ] Install Flutter SDK and VS Code with Flutter extension
- [ ] Run `flutter pub get` inside `frontend/`
- [ ] Confirm `flutter run -d chrome` shows the login screen stub

[GATE — Pre-Sprint]: All three teammates have the repo running locally

---

## SPRINT 1: Foundation
### March 2026 — target 10 days

**Goal:** Running Mock API with all 9 endpoints, Flutter login working, 5+ universities in data.

---

### Waqas — Backend

1. Follow `docs/00_architecture/WAQAS_SETUP_GUIDE.md` completely
2. Activate venv, install requirements: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, fill in `SECRET_KEY` and `GEMINI_API_KEY`
4. Start PostgreSQL: `docker-compose up -d`
5. Create all 6 tables: `alembic upgrade head` (The migration file is already in the repo. If you get "No such revision", run `git pull` first.)
6. Verify tables exist:
   ```bash
   docker exec -it fyp_postgres psql -U fyp_user -d fyp_db -c "\dt"
   ```
   Expected: users, student_profiles, chat_sessions, messages, recommendations, profile_history
7. Start server: `uvicorn app.main:app --reload`
8. Open `http://localhost:8000/docs` — confirm all 9 endpoints listed
9. Test POST /api/v1/auth/register in the docs page — confirm 201 + access_token
10. Test POST /api/v1/auth/login — confirm 200 + access_token
11. Test all remaining 7 endpoints using the JWT from step 9
    (click Authorize in docs page → paste `Bearer <token>`)
12. Post to `team-updates/` with filename: `YYYY-MM-DD-api-change-sprint1-mock-api-ready.md`
    Content: the base URL and confirmation all 9 endpoints work
13. Commit: `feat(backend): sprint-1 — alembic tables confirmed, all 9 mock endpoints working`

---

### Khuzzaim — Frontend

*Starts after Waqas posts the team-updates file above.*

**Design reference — read before building any screen:**
- `design/screen_mockups/DESIGN_HANDOFF.md` — implementation guide, one section per screen
- `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md` — colours, typography, spacing tokens
- `design/screen_mockups/code_[screen].html` — visual reference for the screen you are currently building

**Use the session starter in DESIGN_HANDOFF.md for every screen session. One screen per Claude Code session.**

1. Open `frontend/` in VS Code
2. Run `flutter pub get`
3. **Make the state management decision with Waqas** before writing any screen
   — Update `CLAUDE.md` line that says "TBD" with the chosen option
4. Build Splash screen (`screens/splash_screen.dart`):
   - Full screen teal background (#006B62)
   - Brand icon + app name centred
   - Animated loading bar
   - Routing logic: check `flutter_secure_storage` for token → if none navigate
     to `OnboardingCarouselScreen` → if token exists call `GET /profile/me` →
     route based on `onboarding_stage`
   - See DESIGN_HANDOFF.md Screen 01
5. Build Onboarding Carousel (`screens/onboarding/carousel_screen.dart`):
   - 3 slides with PageView
   - Skip → `LoginScreen`
   - Get Started → `LoginScreen`
   - Show only when no token in `flutter_secure_storage` (covers fresh install
     and post-logout)
   - See DESIGN_HANDOFF.md Screen 02
6. Build Login screen (`screens/auth/login_screen.dart`):
   - Email + password fields, Login button
   - On submit: call `AuthService.login(email, password)`
   - On success (token returned): navigate to ChatScreen shell
   - On failure (null returned): show error message
7. Build Signup screen (`screens/auth/signup_screen.dart`):
   - Email + password fields, Register button
   - On submit: call `AuthService.register(email, password)`
   - Same navigation on success
8. Build static Chat screen shell (`screens/chat/main_chat_screen.dart`):
   - Message list area (empty for now)
   - Text input + send button (no functionality yet)
   - AppBar with title
9. Wire navigation: Splash → Carousel → Login → Chat, Signup → Chat
10. Test full flow: register a new account, confirm token stored, confirm Chat screen appears
11. Commit: `feat(frontend): sprint-1 — splash, carousel, login, signup, chat shell wired to mock API`

---

### Fazal — Data

*Can run in parallel with everything above.*

1. Open `backend/app/data/universities.json`
2. Read `docs/00_architecture/FAZAL_DATA_GUIDE.md` — worked example is NED University
3. Add NED University with at least 2 degree programs
4. Run: `cd backend && python scripts/seed_db.py` — must print OK for universities.json
5. Add FAST-NUCES Karachi with at least 2 degree programs
6. Add University of Karachi (UoK) with relevant programs
7. Add Aga Khan University (MBBS only)
8. Add IBA Karachi (BBA/BS Economics)
9. For EACH university added: immediately add matching `field_id` entries to:
   - `lag_model.json` (raw layer values + leave computed.future_value as 0.0)
   - `affinity_matrix.json` (RIASEC values 1–10 per field)
10. Run seed_db.py validation after each university — do not batch
11. Commit: `feat(data): sprint-1 — 5 universities, matching lag_model and affinity entries`
12. Post to `team-updates/`: `YYYY-MM-DD-data-change-sprint1-5-universities-added.md`

---

### [GATE — Sprint 1 Complete — ALL must be true]:
- [ ] `alembic upgrade head` runs clean, all 6 tables confirmed
- [ ] All 9 endpoints tested in FastAPI docs, all return correct shapes
- [ ] Flutter login + signup working end-to-end against mock API
- [ ] JWT token stored and used for protected endpoints
- [ ] `universities.json` has at least 5 universities
- [ ] `lag_model.json` and `affinity_matrix.json` have matching entries for all field_ids used
- [ ] State management decision made and committed to CLAUDE.md

**→ Waqas opens Opus Integration Chat and runs Sprint 1 Gate Check**

---

## SPRINT 2: MVP1 — Profiling & Data Ingestion
### Target: ~2 weeks after Sprint 1 gate

*Starts only after Sprint 1 Gate Check passes.*

---

### Waqas — Backend

1. Implement `ProfilerNode` (LLM — Gemini):
   - Conversational extraction of: budget, transport_willing, home_zone
   - Optional: stated_preferences, family_constraints, career_goal
   - Sets `profiling_complete = True` when all required fields collected
   - For O/A Level students: stream confirmation required before profiling_complete
2. Implement OCR service (`services/ocr_service.py`):
   - Real Gemini Vision API call replacing the Sprint 1 mock
   - Returns extracted_marks + confidence_score
   - `requires_manual_verification = True` when confidence < 0.80
3. Connect profiler to `POST /api/v1/chat/stream` SSE endpoint:
   - ProfilerNode runs via LangGraph, streams status + chunk events
   - Multi-turn conversation — session state persisted via AsyncPostgresSaver
4. Test: 3 full profiler conversations from scratch, confirm all required fields extracted
5. If any schema changes needed: `alembic revision --autogenerate -m "description"`
   Post schema-change to `team-updates/` before pushing
6. Commit: `feat(backend): sprint-2 — profiler node live, OCR service real`

---

### Khuzzaim — Frontend

*Starts after Waqas confirms profiler endpoint is working.*

**Design reference — same as Sprint 1. Read DESIGN_HANDOFF.md section for each screen before building it.**

**New screens confirmed in v1.5 — build alongside the screens below:**
- `screens/onboarding/riasec_complete_screen.dart` — shown on 200 from POST /profile/quiz. Navigates to Grades Input.
- `screens/onboarding/grades_complete_screen.dart` — shown on 200 from POST /profile/grades. Navigates to Capability Assessment.
- `screens/onboarding/assessment_complete_screen.dart` — shown on 200 from POST /profile/assessment. Auto-navigates to Chat after 2–3 seconds with loading animation.
- `screens/error_screen.dart` — three states: no internet (retry), server timeout (retry), 401 session expired (clear token + navigate to login). See CLAUDE.md locked decisions for JWT 401 rule.

7. Build RIASEC Quiz screen (`screens/onboarding/riasec_quiz_screen.dart`):
   - 60 questions displayed as scrollable list or one-at-a-time
   - 5-point Likert buttons per question
   - Progress bar
   - On submit: sum 10 responses per dimension, call `POST /api/v1/profile/quiz`
   - On success: navigate to Grades screen
8. Build Grades Input screen (`screens/onboarding/grades_input_screen.dart`):
   - Education level dropdown (matric/inter/o_level/a_level etc.)
   - Stream dropdown (Pre-Engineering, Pre-Medical, ICS, etc.)
   - Subject marks fields
   - Optional: marksheet upload button → calls `POST /api/v1/profile/marksheet`
   - OCR Verification Modal: shows extracted marks, user confirms or edits
   - On submit: call `POST /api/v1/profile/grades`
9. Build Capability Assessment screen (`screens/onboarding/assessment_screen.dart`):
   - 12 MCQ questions per subject (60 total)
   - Multiple choice A/B/C/D
   - On submit: call `POST /api/v1/profile/assessment`
10a. Add welcome state to Chat screen (`screens/chat/main_chat_screen.dart`):
    - If local messages list is empty, show welcome state
    - Three hardcoded suggested question chips (e.g. "What degrees match my profile?",
      "Which field has the best job market?", "Tell me about engineering at NED")
    - Chip tap pre-fills input field and submits via POST /api/v1/chat/stream
    - No backend involvement — purely frontend empty-state check
10b. Wire Onboarding Carousel (`screens/onboarding/carousel_screen.dart`):
    - Show when no token exists in flutter_secure_storage
    - Covers fresh install and post-logout cases
    - No backend field — purely client-side check
11. Connect Chat screen to real SSE stream:
    - Replace stub with real `SseService.stream()` call
    - Show ThinkingIndicator widget during `status` events
    - Append text to message during `chunk` events
    - Stop on `done` event
12. Commit: `feat(frontend): sprint-2 — onboarding screens, real SSE chat`

---

### Fazal — Data

12. Expand `universities.json` to all 20 Karachi universities
13. Expand `lag_model.json` to all 30+ degree fields
    (Prioritise fields that appear in universities.json first)
14. Complete `affinity_matrix.json` for all fields
15. Run `compute_future_values.py` to populate all `computed.future_value` fields:
    ```bash
    cd backend && python scripts/compute_future_values.py
    ```
16. Run full referential integrity check:
    Every `field_id` in universities.json must exist in both lag_model and affinity_matrix
17. Commit: `feat(data): sprint-2 — 20 universities, full lag model, all FutureValues computed`

---

### [GATE — Sprint 2 Complete — ALL must be true]:
- [ ] ProfilerNode multi-turn conversation works end-to-end
- [ ] OCR upload + verification modal works (test with 3 real marksheet images)
- [ ] RIASEC quiz saves correctly to `student_profiles.riasec_scores`
- [ ] Grades submission works with IBCC conversion for O/A Level
- [ ] Capability assessment saves to `student_profiles.capability_scores`
- [ ] All 20 universities in `universities.json`
- [ ] Full `lag_model.json` with computed FutureValues
- [ ] Full `affinity_matrix.json`

**→ Waqas opens Opus Integration Chat for Sprint 2 Gate Check**

---

## SPRINT 3: MVP2 — Reasoning Pipeline + Live Recommendations
### Must complete by April 20 — 50% demo milestone
### Can begin 3–4 days before Sprint 2 Gate if profiler is working

---

### Waqas — Backend

1. Implement `FilterNode` (pure Python — no LLM):
   - Reads `universities.json`
   - Applies all 5 constraint checks (stream, mandatory subjects, aggregate, fee, zone)
   - Produces `confirmed_eligible`, `likely_eligible`, `stretch` lists
   - Applies minimum display rule: always return ≥5 degrees
   - Writes `thought_trace` entries for every decision
2. Implement `ScoringNode` (pure Python — no LLM):
   - RIASEC dot product normalised against theoretical max
   - FutureValue from `lag_model.json`
   - `total_score = (weights.match × match_score) + (weights.future × future_score/10)`
   - Capability blend when `abs(capability - reported) >= 25`
   - Mismatch detection: sets `mismatch_notice` when conditions met
3. Implement `ExplanationNode` (LLM — Gemini):
   - 4-part response structure (What Changed, Mismatch, Top 5, Improvement)
   - Language detection: responds in same language as student (English or Roman Urdu)
   - Streams via SSE chunk events
4. Implement `SupervisorNode` (LLM — intent classifier, 7 intents)
5. Implement `AnswerNode` (LLM + tools for fee_query and market_query)
6. Wire full LangGraph graph in `core_graph.py`:
   - AsyncPostgresSaver checkpointer configured and connected
   - Replace Sprint 1 mock stream in `chat.py` with real graph invocation
7. Implement PII scrubbing before every LLM call
8. Run all 5 test personas through the full pipeline:
   ```bash
   cd backend && pytest tests/ -v
   ```
   All non-skipped tests must pass
9. Commit: `feat(backend): sprint-3 — full agent pipeline live, all nodes wired`

---

### Khuzzaim — Frontend

10. Build Recommendation Dashboard (`screens/dashboard/recommendation_dashboard.dart`):
    - Profile Summary Card (top RIASEC dimensions in plain language)
    - Mismatch Notice (amber banner — shows when `mismatch_notice` is non-null)
    - Ranked degree cards using `UniversityCard` widget
    - Each card: degree name, university, merit tier badge, total score, FutureValue
    - `LagScoreBadge` widget: Emerging/Peak/Saturated with colour
11. Build `RoadmapTimeline` widget for the rich_ui SSE event
12. Add "Show Reasoning" toggle — displays `thought_trace` content collapsibly
13. Wire "Ask about this degree" button → opens Chat with degree pre-loaded
14. Connect `GET /api/v1/profile/me` to profile display
15. Commit: `feat(frontend): sprint-3 — recommendation dashboard, all widgets`

---

### Khuzzaim — Testing

16. Run all 5 personas (Ali, Fatima, Ahmed, Sara, Omar) through the full pipeline:
    - Do the recommendations make logical sense for each profile?
    - Does the mismatch notice trigger for Ahmed (E+C profile)?
    - Does Fatima (Pre-Medical) see CS as conditionally eligible?
    - Does the minimum 5 results rule work for Omar (low budget)?
17. Write viva preparation document in `docs/01_deliverables/`:
    Answers to: "Why LangGraph?", "Why not ChatGPT?",
    "How do you validate the Lag Model?", "What is your evaluation methodology?"
18. Log any bugs as GitHub Issues with label `sprint-3-bug`

---

### [GATE — April 20 Demo — DEMO MUST SHOW]:
- [ ] Student logs in
- [ ] Completes RIASEC quiz and enters marks (or uploads marksheet)
- [ ] Completes capability assessment
- [ ] Receives ranked degree recommendations with AI explanations
- [ ] Mismatch notice shows when appropriate
- [ ] Can see reasoning behind recommendations (thought_trace)
- [ ] Can ask follow-up questions in chat (fee query, market query)

**→ Waqas opens Opus Integration Chat for April 20 Milestone Check**

---

## SPRINT 4: Polish, Error Handling, Viva Prep
### April 21 – June 14

---

### Waqas — Backend

**Deferred endpoints from v1.5 screen lock — implement in this sprint:**

0a. Implement `GET /api/v1/chat/messages` (`endpoints/chat.py`):
    - Returns prior session messages for the current user's active chat session
    - Flutter loads these on chat screen open; welcome state only shows if list is empty
    - Fixes: welcome state currently shows on every fresh load regardless of prior sessions
0b. Implement `POST /api/v1/auth/forgot-password` (`endpoints/auth.py`):
    - Accepts email, generates OTP, sends via email service (SendGrid or equivalent)
    - OTP flow is locked — do NOT implement as a reset link
    - Add email service dependency to requirements.txt
0c. Implement `POST /api/v1/auth/verify-otp` (`endpoints/auth.py`):
    - Accepts email + OTP, returns short-lived reset token on match
0d. Implement `POST /api/v1/auth/reset-password` (`endpoints/auth.py`):
    - Accepts reset token + new password, updates user record
0e. Implement `POST /api/v1/auth/change-password` (`endpoints/auth.py`):
    - Authenticated endpoint — accepts current_password + new_password
    - Settings screen button is already built and waiting for this endpoint
Implementation order: 0a first (fixes demo UX regression), then 0b–0e together
(share the email service dependency).
1. Replace Gemini with Claude Sonnet 4.6 for ExplanationNode and AnswerNode
   (update `LLM_MODEL_NAME` in config and test)
2. Add LangSmith tracing:
   Set `LANGCHAIN_TRACING_V2=true` in `.env`
   Set `LANGCHAIN_API_KEY` in `.env`
   Verify traces appear in LangSmith dashboard
3. Add context compression for long sessions (session_summary field in chat_sessions)
4. Add proper error responses for all edge cases:
   - Student has no profile yet → clear error, not 500
   - LLM call times out → retry once, then inform student
   - universities.json is empty → clear message, not crash
5. Performance: ensure `/chat/stream` first token < 3 seconds on average
6. Commit: `feat(backend): sprint-4 — claude model, langsmith, error handling`

---

### Khuzzaim — Frontend + Docs

7. Add proper error states to all screens (network errors, empty states)
8. Build Profile screen (`screens/profile/profile_screen.dart`):
   - Shows all collected data
   - Edit buttons for budget, preferences
9. Add PWA manifest so app is installable on Android from browser
10. Write SRS document in `docs/01_deliverables/`
11. Write SDD document in `docs/01_deliverables/`
12. Finalise viva preparation document
13. Commit: `feat(frontend): sprint-4 — error states, profile screen, PWA`

---

### Fazal — Data

14. Verify all FutureValues are current (re-run `compute_future_values.py` if Rozee data updated)
15. Copy all three JSON files to `backend/app/data/seeds/backup/` — this is the Golden Copy
    Never overwrite or delete files in `seeds/backup/`
16. Commit: `feat(data): sprint-4 — golden copy locked in seeds/backup`

---

### All team — Final 2 weeks before viva

- T-14 days: Code freeze — no new features to main
- T-7 days: No schema changes — bug fixes only
- T-1 day: Tag the release: `git tag v1.0-final-viva && git push --tags`
- Make sure `docs/01_deliverables/` has SRS, SDD, and any required university forms

---

## Gate Check Process

At each gate, Waqas opens a **new chat** with the Opus Integration Chat instructions
(from `OPUS_INTEGRATION_CHAT_INSTRUCTIONS.md` in the Claude project knowledge base).

The gate check verifies:
1. All gate conditions are actually met (not just claimed)
2. No architectural drift from CLAUDE.md decisions
3. No blockers for the next sprint

Do not start the next sprint until the gate check passes.
