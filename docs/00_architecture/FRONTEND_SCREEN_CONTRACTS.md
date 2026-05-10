# Frontend Screen Contracts
## FYP: AI-Assisted Academic Career Guidance System
## Flutter-Native Screen Specifications
## Date: May 2026 | Authority: Architecture Chat v6
## Replaces: design/screen_mockups/DESIGN_HANDOFF.md
## Source: POINT_5_API_SURFACE_v1_2.md, CLAUDE.md, SCHEMA_CONTRACT.md

---

> **How to use this document:**
> Read the contract for THIS screen before writing a single line of Dart.
> The contract defines WHAT the screen must do — not HOW it looks.
> Visual decisions are in FRONTEND_DESIGN_SYSTEM.md.
> If this conflicts with CLAUDE.md or POINT_5 — those documents win.

---

## SCREEN INVENTORY (16 screens locked)

| # | Route | Screen | Dart File | Status |
|---|---|---|---|---|
| 1 | `/` | Splash | `screens/splash_screen.dart` | Built |
| 2 | `/onboarding` | Carousel | `screens/onboarding/carousel_screen.dart` | Built |
| 3 | `/login` | Login | `screens/auth/login_screen.dart` | Built |
| 4 | `/signup` | Signup | `screens/auth/signup_screen.dart` | Built |
| 5 | `/forgot-password` | Forgot Password | `screens/auth/forgot_password_screen.dart` | Placeholder |
| 6 | `/riasec-quiz` | RIASEC Quiz | `screens/onboarding/riasec_quiz_screen.dart` | Built |
| 7 | `/riasec-complete` | RIASEC Complete | `screens/onboarding/riasec_complete_screen.dart` | Built |
| 8 | `/grades-input` | Grades Input | `screens/onboarding/grades_input_screen.dart` | Built |
| 9 | `/grades-complete` | Grades Complete | `screens/onboarding/grades_complete_screen.dart` | Built |
| 10 | `/assessment` | Capability Assessment | `screens/onboarding/assessment_screen.dart` | Built |
| 11 | `/assessment-complete` | Assessment Complete | `screens/onboarding/assessment_complete_screen.dart` | Built |
| 12 | `/preferences` | Preferences | `screens/onboarding/preferences_screen.dart` | Built |
| 13 | `/chat` | Main Chat | `screens/chat/main_chat_screen.dart` | Built |
| 14 | `/dashboard` | Recommendation Dashboard | `screens/dashboard/recommendation_dashboard.dart` | Built |
| 15 | `/settings` | Settings | `screens/profile/settings_screen.dart` | Built |
| 16 | `/error` | Error | `screens/error_screen.dart` | Built |
| — | `/profile` | Student Profile | `screens/profile/profile_screen.dart` | Sprint 4 |

No screen may be added without Architecture Chat sign-off and CLAUDE.md update.

---

## STAGE GUARD RULE — applies to all onboarding screens 6–12

Every onboarding screen must check `onboarding_stage` on init. If the student
has already passed this screen's stage, route them forward immediately.
Do not show the screen content. Use `WidgetsBinding.instance.addPostFrameCallback`
to navigate from `initState`.

```dart
void _checkStage() {
  WidgetsBinding.instance.addPostFrameCallback((_) {
    final stage = ref.read(profileProvider).onboardingStage;
    if (stage == 'assessment_complete') {
      Navigator.pushReplacementNamed(context, '/chat');
    } else if (stage == 'grades_complete') {
      Navigator.pushReplacementNamed(context, '/assessment');
    }
    // etc — route forward past current screen's stage
  });
}
```

---

## SCREEN 1 — Splash Screen (`/`)

**Purpose:** Determine routing on app open.

**DATA IN:**
- `flutter_secure_storage` → JWT token (present or absent)
- `GET /api/v1/profile/me` → `onboarding_stage`, `session_id`, all profile fields

**STATES:**
- `loading` — only state. Animated logo (AnimationController 1800ms,
  `Curves.easeInOut`, width 0→120px). Route logic runs concurrently.
- No error state — all failures fall back to `/onboarding`.

**ROUTING LOGIC:**
```
token absent → '/onboarding'
token present → GET /profile/me
  401          → clear token → '/onboarding'
  network error → '/onboarding'  (NEVER → /error from splash)
  200 → route by onboarding_stage:
    'not_started'          → '/riasec-quiz'
    'riasec_complete'      → '/grades-input'
    'grades_complete'      → '/assessment'
    'assessment_complete'  → '/chat'
    any unknown            → '/chat'
```

**ANIMATION:** `AnimationController` 1800ms, `Curves.easeInOut`.
Width animates 0→120px. `kDebugMode` guard on dev annotation.
Always check `mounted` before Navigator call.

**DO NOT:**
- Navigate to `/error` from splash
- Call GET /profile/me more than once
- Show any content besides animated logo

---

## SCREEN 2 — Carousel Screen (`/onboarding`)

**Purpose:** Introduce app to new/logged-out users. 3 slides.

**DATA IN:** None. No API calls.

**STATES:** Local state — current page index (0, 1, 2).

**SLIDE CONTENT:**
- Slide 1: "Interest Mapping" — RIASEC personality concept
- Slide 2: "Academic Intelligence" — marks + aptitude analysis
- Slide 3: "Career Pathways" — ranked university recommendations

**WIDGETS:**
- `PageView.builder`, `BouncingScrollPhysics()`
- Dot indicators: `AnimatedContainer` — active `width: 28, height: 3`;
  inactive `width: 6, height: 3`; `BorderRadius.circular(2)`; gap 6
- "Skip" → `TextButton`
- "Next" / "Get Started" → `ElevatedButton` with shadow

**USER ACTIONS:**
- Skip → `pushReplacementNamed('/login')`
- Next (pages 0–1) → advance `PageController`
- Get Started (page 2) → `pushReplacementNamed('/login')`

**TRIGGER:** Shown only when `flutter_secure_storage` has no JWT token. Covers
fresh install and post-logout. No backend field controls this.

**DO NOT:**
- Add social proof numbers
- Call any API
- Add back button

---

## SCREEN 3 — Login Screen (`/login`)

**Purpose:** Authenticate returning user.

**DATA IN:** Email + password from user input.

**DATA OUT:** `POST /api/v1/auth/login`
```json
{"email": "...", "password": "..."}
```
Response: `{"access_token": "...", "token_type": "bearer"}`
Store token in `flutter_secure_storage`.

**STATES:**
- `idle` — form ready
- `loading` — submit in flight, button shows spinner
- `error_credentials` — 401, inline message "Invalid email or password"
- `error_network` — SnackBar "No internet connection"
- `error_server` — SnackBar "Something went wrong, try again"

**ON SUCCESS:** Call GET /profile/me → route by `onboarding_stage` (same logic as
Splash). Do not hardcode a destination.

**NAVIGATION:**
- "Sign Up" → `pushNamed('/signup')` — NOT pushReplacement (back must work)
- "Forgot Password" → `onPressed: null`, slate color, no navigation

**KEYBOARD HANDLING:**
- `resizeToAvoidBottomInset: false` on Scaffold
- `SafeArea(bottom: false)` for top safe area only
- `MediaQuery.removePadding(removeBottom: true)` prevents double-compensation
- Apply `MediaQuery.of(context).viewInsets.bottom` to
  `SingleChildScrollView` padding bottom

**LAYOUT:**
- Gradient top bar (3px, see FRONTEND_DESIGN_SYSTEM.md 9c)
- Form card with editorial shadow, `BorderRadius.circular(32.r)`
- Focus left-border pattern on both fields (see 9b)
- "Remember me" checkbox (local state only, not sent to backend)

**DO NOT:**
- Add Google/GitHub/ORCID SSO buttons
- Enable Forgot Password

---

## SCREEN 4 — Signup Screen (`/signup`)

**Purpose:** Create new account.

**DATA IN:** Email + password from user input.

**DATA OUT:** `POST /api/v1/auth/register`
```json
{"email": "...", "password": "..."}
```
Response: `{"access_token": "...", "token_type": "bearer"}`
Store token in `flutter_secure_storage`.
Backend auto-creates: user + student_profile + chat_session.

**STATES:**
- `idle`
- `loading`
- `error_exists` — 409, "An account with this email already exists"
- `error_network` — SnackBar
- `error_server` — SnackBar
- `error_validation` — client-side (email format, password ≥ 8 chars)

**PASSWORD VALIDATION (shown inline, live as user types):**
- Minimum 8 characters — pass/fail indicator
- Show before submit, not only on submit attempt

**ON SUCCESS:** `pushNamedAndRemoveUntil('/riasec-quiz', (r) => false)`
New user is always in `not_started` — always routes to RIASEC quiz.

**NAVIGATION:**
- "Sign In" → `pushReplacementNamed('/login')`

**DO NOT:**
- Navigate to GET /profile/me after register — always → /riasec-quiz
- Add SSO buttons

---

## SCREEN 5 — Forgot Password (`/forgot-password`)

**Purpose:** Placeholder only. Password reset deferred to Sprint 4.

**IMPLEMENTATION:** Static screen. Shows "Coming soon" message.
No form. No API calls. Back button works normally.

**DO NOT:** Build any form or OTP flow here.

---

## SCREEN 6 — RIASEC Quiz (`/riasec-quiz`)

**Purpose:** 60-question RIASEC interest inventory. Step 1 of onboarding.

**DATA IN:**
- 60 questions bundled in `frontend/assets/riasec_questions.json` — NO API call
- `isRetake: bool` from route arguments
- Draft from `flutter_secure_storage` (sessionId-first pattern)

**DATA OUT:** `POST /api/v1/profile/quiz`
```json
{"R": 42, "I": 38, "A": 29, "S": 35, "E": 44, "C": 31}
```
Values: summed Likert 10–50 per dimension (10 questions × 1–5 scale).

**STATES:**
- `loading_draft` — init, loading questions + draft
- `active` — quiz in progress (local: `_currentIndex`, `Map<int,int> _answers`,
  `_selectedAnswer`)
- `submitting` — POST in flight after Q60 answered
- `error_submit` — POST failed, retry option

**DRAFT MANAGEMENT:**
- Key: `draft_riasec_$sessionId` (see FRONTEND_DESIGN_SYSTEM.md 14)
- Save on every answer change, debounced 500ms
- Clear on successful submit

**LAYOUT:**
- `PopScope` → `Scaffold` → `SafeArea` → `Column`:
  - AppBar row (52px)
  - `LinearProgressIndicator` (6px, teal fill / surfaceContainerHigh track)
  - `Expanded` → `SingleChildScrollView` → `AnimatedSwitcher` →
    question card with dimension chip, counter, question text, 5 Likert buttons,
    AI Insight panel
  - Navigation row (Previous / Next / "View My Results")

**ANIMATEDSWITCHER:** Key must be `ValueKey(_currentIndex)` — required for
per-question animation. Changing key triggers the animation.

**SUBMISSION:** Aggregate 60 `_answers` into 6 dimension sums → POST.
After 200: call `profileProvider.notifier.loadProfile(token)` → navigate.

**NAVIGATION ON SUCCESS:**
- `isRetake: false` → `pushNamed('/riasec-complete')`
- `isRetake: true` → `pushReplacementNamed('/chat')`

**LEAVE / BACK:** `PopScope` → confirmation dialog → confirmed →
```dart
WidgetsBinding.instance.addPostFrameCallback((_) {
  Navigator.of(context, rootNavigator: true)
      .pushNamedAndRemoveUntil('/login', (r) => false);
});
```

**STAGE GUARD:** If `onboarding_stage` is `riasec_complete` or beyond → route
forward immediately.

**DO NOT:**
- Fetch questions from API (no such endpoint)
- Allow back navigation through individual questions
- Send individual answers — only aggregated dimension sums

---

## SCREEN 7 — RIASEC Complete (`/riasec-complete`)

**Purpose:** Show RIASEC results with radar chart. Bridge to grades input.

**DATA IN:** `profileProvider.profile.riasecScores` — already loaded.

**DEMO LOCKED FALLBACK:** If `riasecScores` is null or empty:
```dart
const Map<String, int> _fallback = {
  'R': 32, 'I': 45, 'A': 28, 'S': 31, 'E': 38, 'C': 42
};
// Top 3 renders as: I=88%, C=80%, E=70%
```

**STATES:** Single state — content display.

**LAYOUT:**
- Hero block: 80×80px gradient circle, psychology icon, badge, title, subtitle
- Results card with `CustomPainter` radar chart — 6-axis hexagon
- Top-3 dimension pills (`Wrap`), sorted descending by score
- AI Insight panel (static text)
- CTA button

**RADAR CHART (`CustomPainter`):**
- 6-axis hexagon grid, 3 concentric tiers at 33%/66%/100%
- Data polygon: fill `Color(0xFF006B62).withOpacity(0.15)`, stroke `#006B62`
- Vertex labels R/I/A/S/E/C, 10sp, 600 weight
- Wrap in `Semantics(label: 'RIASEC radar chart...')`
- `import 'dart:math'` for cos/sin/pi

**NAVIGATION:**
- CTA → `pushNamed('/grades-input')`
- No back button: `automaticallyImplyLeading: false`

---

## SCREEN 8 — Grades Input (`/grades-input`)

**Purpose:** Collect academic marks. Step 2 of onboarding.

**DATA IN:** User input — education level, stream, board, subject marks.
`isRetake: bool` from route arguments.

**DATA OUT:** `POST /api/v1/profile/grades`
```json
{
  "education_level": "intermediate",
  "grade_system": "percentage",
  "stream": "pre_engineering",
  "board": "karachi",
  "subject_marks": {"mathematics": 85, "physics": 78, "chemistry": 71, "english": 88}
}
```

**STATES:**
- `idle` — form
- `loading` — submit in flight
- `error_validation` — client-side (required fields, marks 0–100)
- `error_network` / `error_server` — SnackBar

**LAYOUT:**
- "Scan Marksheet" button (56px height) — DEFERRED: shows "Soon" badge,
  `onPressed: null`. OCR feature is Sprint 4. See FRONTEND_DESIGN_SYSTEM.md 9h
  for when this is implemented.
- Form card (`BorderRadius.circular(32.r)`) with education/stream/board dropdowns
- Subject marks table: `Column` of rows, marks input `width: 72px`,
  `TextInputType.number`, right-aligned
- Accessibility divider between rows: `outlineVariant` at 15% opacity only

**NAVIGATION ON SUCCESS:**
- `isRetake: false` → `pushNamed('/grades-complete')`
- `isRetake: true` → `pushReplacementNamed('/chat')`

**STAGE GUARD:** If `onboarding_stage` is `grades_complete` or beyond → route forward.

---

## SCREEN 9 — Grades Complete (`/grades-complete`)

**Purpose:** Confirm grades submission. Bridge to assessment.

**DATA IN:** None.

**STATES:** Single state.

**NAVIGATION:**
- CTA → `pushNamed('/assessment')`
- No back button: `automaticallyImplyLeading: false`

---

## SCREEN 10 — Capability Assessment (`/assessment`)

**Purpose:** 12 questions per subject × 5 subjects. Step 3 of onboarding.

**DATA IN:**
- Questions from `frontend/assets/assessment_questions.json` — FLUTTER ASSET,
  NOT from API. File was copied from `backend/app/data/assessment_questions.json`.
- `curriculum_level` from `profileProvider` (matric / inter_part1 / inter_part2)
- Draft from `flutter_secure_storage`
- `isRetake: bool` from route arguments

**ASSET LOADING:**
```dart
final raw = await rootBundle.loadString('assets/assessment_questions.json');
final all = json.decode(raw) as List;
// Filter by curriculum_level
final filtered = all.where((q) =>
    q['curriculum_level'] == curriculumLevel).toList();
```

**QUESTION ID TYPE:** String, not int. Use `Map<String, int>` for answers.
```dart
Map<String, int> _answers = {};
// key: q['id'] as String, value: 0 or 1
```

**DATA OUT:** `POST /api/v1/profile/assessment`
```json
{
  "responses": {
    "mathematics": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1],
    "physics": [1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    "chemistry": [0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
    "biology": [1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0],
    "english": [1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1]
  }
}
```
Each list: exactly 12 values (0 or 1). All 5 subjects required.

**STATES:**
- `loading_draft` — init
- `active` — assessment in progress (subject tabs, question display)
- `submitting` — POST in flight
- `error_submit` — retry option

**DRAFT MANAGEMENT:**
- Key: `draft_assessment_$sessionId`
- Only clear draft when `onboarding_stage == 'assessment_complete'`

**LAYOUT:**
- Subject tabs: overflow-x scroll with right fade gradient overlay
- Current question glow: `BoxShadow(color: Color(0x40006B62), blurRadius: 0,
  spreadRadius: 2)` — subtle focus indicator

**NAVIGATION ON SUCCESS:**
- `isRetake: false` → `pushNamed('/assessment-complete')`
- `isRetake: true` → `pushReplacementNamed('/chat')`

**STAGE GUARD:** If `onboarding_stage` is `assessment_complete` → route to `/chat`.

---

## SCREEN 11 — Assessment Complete (`/assessment-complete`)

**Purpose:** Confirm completion. Auto-navigate to chat.

**DATA IN:** None.

**STATES:** Single state.

**AUTO-NAVIGATION:** 3-second progress bar animates to full, then:
```dart
Navigator.pushNamedAndRemoveUntil(context, '/chat', (r) => false)
```

**NO BUTTON** — navigation is automatic only. No manual CTA.

---

## SCREEN 12 — Preferences (`/preferences`)

**Purpose:** Collect family context, budget, transport. Step 4 of onboarding.

**DATA IN:** User input — family career field, family career expectation,
budget per semester, transport willing.

**DATA OUT:** Profile update endpoint (Phase 1C — confirm exact endpoint from
SCHEMA_CONTRACT.md Section 9 before implementing).
Writes to: `student_profiles.family_context`, `budget_per_semester`,
`transport_willing`.

**STATES:**
- `idle`
- `loading`
- `error_network` / `error_server` — SnackBar

**FIELDS:**
- Family career field (text input or dropdown)
- Family career expectation: `no_expectation` | `general_guidance` |
  `expects_specific_field`
- Budget per semester (integer, PKR, `TextInputType.number`)
- Transport willing (boolean toggle)

**NAVIGATION:**
- Success → `pushNamedAndRemoveUntil('/chat', (r) => false)`
- `isRetake: true` → same

**DO NOT:** Add housing preference (removed from schema permanently).

---

## SCREEN 13 — Main Chat Screen (`/chat`)

**Purpose:** Core AI interaction. Student converses with the system.

**DATA IN:**
- `GET /api/v1/chat/messages` — prior messages on load (if endpoint exists),
  or start empty
- `profileProvider.profile.sessionId` — required for SSE request
- SSE stream from `POST /api/v1/chat/stream`

**DATA OUT:** `POST /api/v1/chat/stream`
```json
{
  "session_id": "uuid",
  "user_input": "What CS programs suit my profile?",
  "context_overrides": {}
}
```
Use `http` package with streaming response. Do NOT use `dio`.

**SSE EVENT HANDLING:**
```
event: status → update ThinkingIndicator label
  "profiling"              → "Understanding your profile..."
  "filtering_degrees"      → "Checking your eligibility..."
  "scoring_degrees"        → "Ranking your matches..."
  "generating_explanation" → "Writing your recommendations..."
  "fetching_fees"          → "Checking fee details..."
  "fetching_market_data"   → "Checking job market..."
  "done"                   → dismiss ThinkingIndicator

event: chunk → append text to current AI bubble (typewriter effect)

event: rich_ui type=university_card → render university card widget
event: rich_ui type=roadmap_timeline → render roadmap timeline widget
```

**STATES:**
- `welcome` — no prior messages, show welcome prompt
- `active` — conversation in progress
- `thinking` — SSE stream in flight (ThinkingIndicator visible)
- `error_stream` — SSE failed, show retry

**BUBBLES:**
- Student: right-aligned, primary background, white text (see FRONTEND_DESIGN_SYSTEM.md 9g)
- AI: left-aligned, surfaceContainerLow, purple left-border (see 9g)

**INPUT LOCK:** Disable text input while stream is in flight. Re-enable on "done".

**NAVIGATION:**
- Dashboard icon → `pushNamed('/dashboard')`
- Settings icon → `pushNamed('/settings')`
- No back button — terminal destination

**401 HANDLING:** Clear token → `pushNamedAndRemoveUntil('/login', (r) => false)`

**ROADMAP TIMELINE NOTE:** `roadmap_timeline` rich_ui event is handled but
the rendering widget is not yet implemented. Log it as received but render
nothing until implementation sprint.

---

## SCREEN 14 — Recommendation Dashboard (`/dashboard`)

**Purpose:** Display ranked university recommendations.

**DATA IN:** `GET /api/v1/profile/recommendations`
Returns most recent `roadmap_snapshot` array. Each element: 20-field university card.

**STATES:**
- `loading` — GET in flight, shimmer
- `loaded` — cards list
- `empty` — no recommendations yet, CTA back to chat
- `error_network` / `error_server` — error state with retry

**UNIVERSITY CARD — key fields to display:**
- `university_name`, `degree_name`, `field_id`
- `total_score` (0.0–1.0) → display as percentage match
- `merit_tier` (`likely`/`possible`/`stretch`/`unlikely`) → colored badge
- `eligibility_tier` (`eligible`/`conditionally_eligible`) → badge
- `fee_per_semester` → formatted as "PKR XX,XXX/semester"
- `explanation_text` → AI explanation 2–3 sentences
- `soft_flags` array → each flag as small info chip
- `scholarships` array → list below card

**MISMATCH NOTICE:** If `has_mismatch_notice: true` → show amber warning
banner at top (see FRONTEND_DESIGN_SYSTEM.md 9n).

**NAVIGATION:**
- Any "Discuss this" / card detail action →
  `pushNamed('/chat')` with pre-filled message
- No separate university detail screen

**DO NOT:**
- Build a separate university detail screen
- Show raw score numbers — show percentage + tier badge

---

## SCREEN 15 — Settings Screen (`/settings`)

**Purpose:** Account info and actions.

**DATA IN:** Reads from `profileProvider.profile` — no additional API call on load.

**STATES:** Single state (reads from local provider).

**SECTIONS:**
1. **Profile card:** CircleAvatar with person icon (teal), "Student Account",
   education level badge (teal, from `profileProvider.educationLevel`),
   onboarding stage label
2. **Account:**
   - "Change Password" — "Soon" badge, `onPressed: null`, slate color
   - "Delete Account" — "Soon" badge, `onPressed: null`, slate color
3. **Sign Out:** ElevatedButton — background `#E0E3E5`, text `#515F74`.
   On tap: confirmation AlertDialog.
   On confirm: `authProvider.notifier.logout()` + `profileProvider.notifier.reset()`
   + `chatProvider.notifier.reset()` +
   `pushNamedAndRemoveUntil('/login', (r) => false)`

**DO NOT:**
- Add notification toggles (no backend)
- Use red for Sign Out
- Enable Change Password or Delete Account

---

## SCREEN 16 — Error Screen (`/error`)

**Purpose:** Three distinct error states.

**DATA IN:** `ErrorType` enum from route arguments:
```dart
final args = settings.arguments as Map<String, dynamic>?;
final errorType = args?['errorType'] as ErrorType? ?? ErrorType.noNetwork;
```

**ErrorType enum:**
```dart
enum ErrorType { noNetwork, serverTimeout, sessionExpired }
```

**STATE — noNetwork:**
- Icon: `Icons.wifi_off` (red)
- Title: "No Connection"
- Action: "Try Again" → `Navigator.pop(context)`

**STATE — serverTimeout:**
- Icon: `Icons.cloud_off` (red)
- Title: "Server Unavailable"
- Actions: "Try Again" → pop; "Go Back" → `Navigator.maybePop(context)`

**STATE — sessionExpired:**
- Icon: `Icons.lock_clock` (teal)
- Title: "Session Expired"
- Action: "Sign In" → clear token →
  `pushNamedAndRemoveUntil('/login', (r) => false)`

---

## STUDENT PROFILE SCREEN (`/profile`) — SPRINT 4, DEFERRED

Placeholder in `main.dart`. Implementation pending Phase 1C assessment
dashboard design. Read `docs/00_architecture/FYP_Architecture_Reference_v2.md`
Section 11 for the dual dashboard architecture before building this screen.

---

## GLOBAL DO NOT BUILD

| What | Which screen | Why |
|---|---|---|
| Separate university detail screen | Dashboard | Navigate to Chat with pre-filled message instead |
| Housing preference field | Preferences | Removed from schema permanently |
| OCR functionality | Grades Input | Sprint 4 only — show "Soon" badge |
| Notification toggles | Settings | No notification backend |
| Google/GitHub SSO | Login, Signup | Wrong audience |
| Social proof numbers | Carousel | Fabricated |
| Red Sign Out | Settings | Not destructive |
| Forgot Password form | Forgot Password | Sprint 4 — placeholder only |
| Change Password / Delete Account | Settings | Sprint 4 — placeholder only |

---

*FRONTEND_SCREEN_CONTRACTS.md v1.0 — May 2026*
*Produced by Architecture Chat v6*
*Replaces: design/screen_mockups/DESIGN_HANDOFF.md (API + navigation parts)*
*Source: POINT_5_API_SURFACE_v1_2.md, CLAUDE.md, SCHEMA_CONTRACT.md,*
*design/screen_mockups/DESIGN_HANDOFF.md (ingested before deletion)*