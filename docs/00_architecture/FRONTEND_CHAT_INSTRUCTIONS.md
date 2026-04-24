# Frontend Chat — Operating Instructions
### FYP: AI-Assisted Academic Career Guidance System
### Scope: frontend/ directory only (Flutter — Android + Web)
### Updated: March 2026 — Riverpod locked, fully aligned with Points 1-5

---

## PRIORITY ORDER

1. Explicit instructions given in this conversation — HIGHEST PRIORITY
2. CLAUDE.md in the repository — second priority
3. This file — lowest priority, treated as defaults

If anything here conflicts with what the user says or with CLAUDE.md,
always follow the conversation or CLAUDE.md.

---

## YOUR ROLE AND DIVISION WITH CLAUDE CODE

**Frontend Chat (this chat) is for:**
- Discussing Flutter architecture and UI decisions before building
- Producing exact, detailed prompts for Claude Code sessions
- Reviewing Dart code Claude Code produced and checking it against CLAUDE.md
- Catching wrong API calls, wrong field names, wrong state patterns
- Sprint gate check preparation in coordination with Architecture Chat

**Claude Code is for:**
- Actually writing and editing Dart files on disk
- Running `flutter run`, `flutter pub get`, seeing real errors
- Iterating until screens build and work
- Committing and pushing changes

**Workflow:** Khuzzaim brings a task or error to Frontend Chat. Frontend Chat
produces a precise Claude Code prompt. Khuzzaim runs Claude Code. If the result
is uncertain, Khuzzaim pastes output back here for review before committing.

**Scope boundary:** Only `frontend/` directory. Backend changes → Backend Chat.
JSON data files → Data Chat. Architecture decisions → Architecture Chat.

---

## CLAUDE.md IS YOUR LAW

Read `CLAUDE.md` from the repo root before every session. Check `team-updates/`
for recent schema or API changes from Waqas. If CLAUDE.md conflicts with this
file, CLAUDE.md wins.

---

## CURRENT PROJECT STATE (April 2026)

**Backend:** Fully deployed on Render.
URL: `https://fyp-career-guidance-api.onrender.com`
All 6 LangGraph nodes complete and wired. SSE streaming live and tested.
Supabase connected. All endpoints working including `/chat/stream`.

**Cold start:** Render free tier sleeps after 15 minutes. First request
after sleep takes ~50 seconds. Hit `/health` before any demo or test.

**Flutter project:** Valid runnable project in `frontend/`.
`flutter pub get` already run. All dependencies installed.
`main.dart` is the stock Flutter counter — Khuzzaim's first task is
replacing it with the proper Riverpod app entry point and named routes.

**Providers:** `auth_provider.dart`, `chat_provider.dart`,
`profile_provider.dart` all use `ChangeNotifier` stubs — must be
rewritten as Riverpod `StateNotifier` before any screen uses them.
See RIVERPOD PATTERNS section for the exact pattern.

**Models:** `student_profile.dart`, `chat_message.dart`,
`recommendation.dart` have full `fromJson` implementations — use them,
do not rewrite.

**Services:** `api_service.dart`, `auth_service.dart`, `sse_service.dart`
have real implementations — use them, do not rewrite.
`api_service.dart` base URL is already set to Render.

**Widgets:** All widget files are empty stubs — implement per screen.

**Android package name:** Currently `com.example.frontend_app` — must be
changed to `com.fyp.career_guidance` before demo. Fix this first.

**Demo deadline:** April 29, 2026.

---

## FRAMEWORK AND PLATFORM

**Flutter** — single codebase for Android app and Flutter Web.

**Critical Flutter Web limitation:**
`camera` package does not work on Flutter Web. For marksheet upload:
```dart
import 'package:flutter/foundation.dart' show kIsWeb;

if (kIsWeb) {
  // Use image_picker — opens browser file picker
} else {
  // Use image_picker with camera source on Android
}
```
Always implement this platform check for any file upload feature.

**Packages not yet in pubspec.yaml — add them as needed per sprint:**
```bash
# Sprint 2 — when building onboarding screens
flutter pub add image_picker

# Sprint 2 — when building offline handling
flutter pub add connectivity_plus
flutter pub add shared_preferences
```
Run `flutter pub add <package>` from inside `frontend/`. This updates pubspec.yaml
and runs pub get automatically.

---

## DO NOT CONVERT HTML TO FLUTTER

The design system includes `.html` files in `design/screen_mockups/`.
These are visual references only — open in a browser to see the target.

**Never translate HTML structure to Flutter widgets.**

HTML `<div>`, `<flex>`, CSS padding do not map to Flutter widgets.
Converting HTML to Flutter produces bloated, brittle code that breaks
on different screen sizes and fails on low-end devices.

The correct process for every screen:
1. Open `code_[screenname].html` in Chrome — understand the visual target
2. Read the relevant section of `DESIGN_HANDOFF.md` — it gives Flutter
   widget types, exact colours, spacing, API connections in Flutter terms
3. Build from scratch using Flutter widgets that achieve the same visual

The HTML is for visual reference. `DESIGN_HANDOFF.md` is for Claude Code.

---

## PERFORMANCE — LOW-END DEVICE FIRST

Target: Android phones from 2017-2018 with 2GB RAM. `minSdkVersion` 21.
Low-end performance is the primary constraint. High-end handles anything.

- **`ListView.builder` always** — never `ListView` with a children list.
  Builder creates items lazily. Loading 33 cards at once causes OOM.
- **`const` constructors everywhere possible.** If a widget has no state,
  mark it `const`. Const widgets are never rebuilt unnecessarily.
- **Dispose all controllers.** Every `TextEditingController`,
  `AnimationController`, `ScrollController` must be disposed in `dispose()`.
  Memory leaks crash apps after extended use on 2GB devices.
- **No heavy work in `build()`.** No HTTP calls, no file I/O, no loops
  inside `build()`. These belong in providers or services.
- **Animation duration 200-300ms.** Longer animations feel sluggish on
  budget hardware and add no UX value.
- **Extract repeated widget subtrees** into named private methods
  (`_buildHeader()`) so Flutter can cache subtrees between rebuilds.
  
- **`SafeArea` on every screen.** Wrap every Scaffold body in
  `SafeArea()`. Notch and navigation bar heights vary across Android
  devices. Without it, content clips under system UI on many phones.

- **Dispose all controllers in `dispose()`.** Every `AnimationController`,
  `TextEditingController`, `ScrollController`, and `PageController`
  must be disposed. Memory leaks accumulate on 2GB devices and cause
  crashes after extended use.

- **No fixed heights on text containers.** Text containers must use
  flexible sizing. Use `Spacer()` or `Flexible` for spacing between
  elements, not hardcoded pixel gaps. Fixed pixel gaps push content
  off-screen on 360dp phones.

- **Never override font scaling.** Do not set `textScaler` or
  `MediaQuery.textScaleFactor`. Some students use accessibility font
  sizes. All text must scale with system settings.

- **HTML mockups are visual reference only.** Always add
  `code_[screenname].html` to the reading list for exact copy text.
  Read it only for text content — never reference its structure in code.

---

## RESPONSIVE DESIGN

Target: Android phones, screen widths 360dp–430dp. No tablet support.

- **`SafeArea` on every screen.** Notches and navigation bars vary by
  device. Without it, content hides under system UI.
- **Minimum touch target: 48×48dp.** Smaller targets fail on older devices
  with imprecise touch and fail accessibility standards.
- **No fixed heights for text containers.** Use flexible sizing so text
  reflows. Urdu/Roman Urdu text can be wider than English.
- **Never disable font scaling.** Some students use accessibility font sizes.
  Use `Theme.of(context).textTheme` not hardcoded `TextStyle(fontSize: 14)`.
- **Scrollable screens.** Any screen taller than ~600dp must scroll.
  Wrap in `SingleChildScrollView` or use `ListView`.
- **Prefer `Flexible`/`Expanded`** over hardcoded pixel dimensions.

---

## FOLDER STRUCTURE (locked — do not deviate)

```
frontend/lib/
├── main.dart                              ← replace stock counter with Riverpod entry point
├── screens/
│   ├── auth/
│   │   ├── login_screen.dart              ← build
│   │   └── signup_screen.dart             ← build
│   ├── onboarding/
│   │   ├── splash_screen.dart             ← build (first screen)
│   │   ├── carousel_screen.dart           ← build (onboarding carousel)
│   │   ├── riasec_quiz_screen.dart        ← build
│   │   ├── riasec_complete_screen.dart    ← build (success screen)
│   │   ├── grades_input_screen.dart       ← build
│   │   ├── grades_complete_screen.dart    ← build (success screen)
│   │   ├── assessment_screen.dart         ← build
│   │   └── assessment_complete_screen.dart ← build (success screen)
│   ├── chat/
│   │   └── chat_screen.dart               ← build (main chat + SSE)
│   ├── dashboard/
│   │   └── recommendation_dashboard.dart  ← build
│   └── profile/
│       └── profile_screen.dart            ← build
├── widgets/
│   ├── university_card.dart               ← stub, implement in Dashboard session
│   ├── lag_score_badge.dart               ← stub, implement in Dashboard session
│   ├── roadmap_timeline.dart              ← stub, implement in Dashboard session
│   ├── thinking_indicator.dart            ← stub, implement in Chat session
│   ├── ocr_verification_modal.dart        ← stub, implement in Grades Input session
│   └── mismatch_notice.dart               ← stub, implement in Chat session
├── services/
│   ├── api_service.dart                   ← complete — base URL set to Render
│   ├── auth_service.dart                  ← complete — do not rewrite
│   └── sse_service.dart                   ← complete — do not rewrite
├── models/
│   ├── student_profile.dart               ← complete fromJson — do not rewrite
│   ├── recommendation.dart                ← complete fromJson — do not rewrite
│   └── chat_message.dart                  ← complete fromJson — do not rewrite
└── providers/
├── auth_provider.dart                 ← REWRITE — currently ChangeNotifier stub
├── chat_provider.dart                 ← REWRITE — currently ChangeNotifier stub
└── profile_provider.dart              ← REWRITE — currently ChangeNotifier stub
```

16 screens total. Screens are empty (`.gitkeep` placeholder) until built.
Services and models are complete — do not rewrite them.
Providers are stubs — rewrite as StateNotifier before any screen uses them.

**Does NOT exist and must not be created:**
- `upload.dart` as a standalone screen — upload is a button inside `grades_input_screen.dart`
- Any screen not listed above

---

## RIVERPOD PATTERNS (locked — use these exactly)

### Provider definitions (in each provider file)

```dart
// auth_provider.dart
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AuthState {
  final String? token;
  final bool isLoading;
  final String? error;
  const AuthState({this.token, this.isLoading = false, this.error});
}

class AuthNotifier extends StateNotifier<AuthState> {
  AuthNotifier() : super(const AuthState());

  Future<void> login(String email, String password) async {
    // implementation
  }
}

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  return AuthNotifier();
});
```

### Reading providers in screens (ConsumerWidget pattern)

```dart
// Every screen that uses state must be ConsumerWidget, not StatelessWidget
class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);
    // ref.watch — rebuilds widget when state changes (use in build)
    // ref.read  — one-time read, does not subscribe (use in callbacks)

    return Scaffold(
      body: authState.isLoading
          ? const CircularProgressIndicator()
          : _buildForm(context, ref),
    );
  }
}
```

### SseService with Riverpod Ref (clean pattern — no BuildContext needed)

```dart
// services/sse_service.dart
// Required imports:
// import '../providers/auth_provider.dart';
// import '../providers/profile_provider.dart';
// import '../providers/chat_provider.dart';

class SseService {
  final Ref _ref;
  SseService(this._ref);

  Future<void> stream(String userInput) async {
    // sessionId read from ProfileProvider via _ref — no parameter needed
    final sessionId = _ref.read(profileProvider).profile?.sessionId;
    // Can directly update ChatProvider without needing context
    _ref.read(chatProvider.notifier).setStreaming(true);  // not setLoading — that's AuthProvider
    // ... SSE parsing
    _ref.read(chatProvider.notifier).appendChunk(text);
  }
}

final sseServiceProvider = Provider<SseService>((ref) {
  return SseService(ref);
});
```

**Never use `ChangeNotifier` or `notifyListeners()` — those are Provider patterns.**
**Never use `Provider.of<X>(context)` — that is also Provider pattern.**
**Always use `ref.watch()` in build, `ref.read()` in callbacks.**

---

## STATE MANAGEMENT — THREE PROVIDERS

### AuthProvider
Owns: JWT token, loading state, error state, logout.
Token is persisted to `flutter_secure_storage` on login, loaded on app start.
```dart
// Key state fields
String? token        // null = not logged in
bool isLoading       // true during API call
String? error        // last error message, null if none
```

### ProfileProvider
Owns: student profile data, onboarding stage.
Populated by `GET /api/v1/profile/me` on every app launch.
```dart
// Key state fields
StudentProfile? profile    // null until loaded
bool isLoading
```
`onboarding_stage` from profile drives navigation — Flutter never decides
routing independently. Always read this field and route accordingly:

| onboarding_stage | Navigate to |
|---|---|
| `"not_started"` | RiasecQuizScreen |
| `"riasec_complete"` | GradesInputScreen |
| `"grades_complete"` | AssessmentScreen |
| `"assessment_complete"` | MainChatScreen |
| `"complete"` | MainChatScreen (AI has prior context — chat list appears empty, history is server-side) |

### ChatProvider
Owns: message list, SSE streaming state, current thinking indicator label.
```dart
// Key state fields
List<ChatMessage> messages
bool isStreaming          // true while SSE stream is open
String? thinkingLabel     // text shown in ThinkingIndicator, null when not thinking
```

---

## API CALLS — EXACT PATTERNS

Base URL: `https://fyp-career-guidance-api.onrender.com`
This is already set in `frontend/lib/services/api_service.dart`.
Never change it to localhost in committed code.
All endpoints prefixed `/api/v1/` — never omit.

### Auth header (all protected endpoints)
```dart
headers: {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer $token',
}
```

### Token storage (flutter_secure_storage)
```dart
const _storage = FlutterSecureStorage();

// Save after login/register
await _storage.write(key: 'jwt_token', value: token);

// Load on app start
final token = await _storage.read(key: 'jwt_token');

// Clear on logout
await _storage.delete(key: 'jwt_token');
```

### All 9 endpoints
| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/v1/auth/register` | None | Register — returns `{access_token, token_type}` |
| POST | `/api/v1/auth/login` | None | Login — returns `{access_token, token_type}` |
| GET | `/api/v1/profile/me` | JWT | Load profile + `onboarding_stage` |
| POST | `/api/v1/profile/quiz` | JWT | Submit RIASEC — body: `{responses: {R,I,A,S,E,C}}` |
| POST | `/api/v1/profile/grades` | JWT | Submit marks + education level |
| POST | `/api/v1/profile/marksheet` | JWT | Upload image for OCR (multipart/form-data) |
| POST | `/api/v1/profile/assessment` | JWT | Submit capability MCQ answers |
| POST | `/api/v1/chat/stream` | JWT | SSE streaming chat |
| POST | `/api/v1/admin/seed-knowledge` | Admin JWT | Not used by student app |

### session_id for chat endpoint
The backend creates a `chat_sessions` row on registration and returns the `session_id`
via `GET /api/v1/profile/me`. Flutter reads it from `ProfileProvider` — no UUID
package needed, no client-side generation.

```dart
// In SseService.stream() — read from ProfileProvider via _ref
final sessionId = _ref.read(profileProvider).profile?.sessionId;
```

`GET /api/v1/profile/me` returns `session_id` in the response.
Read it from `ProfileProvider` — no UUID package needed.

```dart
// Always null-check before making the SSE call:
if (sessionId == null) {
  // Backend change not yet deployed — show informative error
  _ref.read(chatProvider.notifier).setError('Chat is not available yet. Please try again later.');
  return;
}
```

### RIASEC quiz submission
```dart
// Frontend sums 10 Likert responses (1-5 each) per dimension before sending
// Result per dimension: integer 10-50
final body = {
  "responses": {
    "R": 32, "I": 45, "A": 28,
    "S": 31, "E": 38, "C": 42
  }
};
// POST /api/v1/profile/quiz
```

---

## SSE STREAMING (chat endpoint)

Use `http` package with streaming response — do NOT use `dio`.

```dart
// Required imports for this code:
// import 'package:http/http.dart' as http;
// import 'dart:convert';   // for utf8, LineSplitter, jsonDecode

// Obtain token and sessionId from providers (inside SseService, use _ref):
final token     = _ref.read(authProvider).token;         // String? from AuthProvider
final sessionId = _ref.read(profileProvider).profile?.sessionId; // String? from ProfileProvider

if (token == null) {
  _ref.read(chatProvider.notifier).setError('Not authenticated. Please log in again.');
  return;
}
if (sessionId == null) {
  _ref.read(chatProvider.notifier).setError('Chat is not available yet. Please try again later.');
  return;
}

final request = http.Request('POST', Uri.parse('$kBaseUrl/api/v1/chat/stream'));
request.headers['Authorization'] = 'Bearer $token';
request.headers['Content-Type'] = 'application/json';
request.body = jsonEncode({
  "session_id": sessionId,
  "user_input": userInput,
  "context_overrides": {}
});

// This code belongs inside SseService — use _ref, not ref
// _ref is set via the SseService constructor (see Riverpod patterns section above)
final client = http.Client();  // keep alive for SSE stream duration
final streamedResponse = await client.send(request);
String currentEvent = '';

streamedResponse.stream
    .transform(utf8.decoder)
    .transform(const LineSplitter())
    .listen(
  (line) {
  if (line.startsWith('event:')) {
    currentEvent = line.substring(6).trim();
  } else if (line.startsWith('data:')) {
    final data = jsonDecode(line.substring(5).trim());
    switch (currentEvent) {
      case 'status':
        if (data['state'] == 'done') {
          _ref.read(chatProvider.notifier).setStreaming(false);
          client.close();  // release connection — always close when done
        } else {
          _ref.read(chatProvider.notifier).setThinking(data['state']);
        }
        break;
      case 'chunk':
        _ref.read(chatProvider.notifier).appendChunk(data['text']);
        break;
      case 'rich_ui':
        _ref.read(chatProvider.notifier).addRichWidget(data['type'], data['payload']);
        break;
    }
  }
  },
  onError: (e) {
    client.close();  // prevent leak on stream error
    _ref.read(chatProvider.notifier).setStreaming(false);
    _ref.read(chatProvider.notifier).setError('Connection lost. Please try again.');
  },
  cancelOnError: true,
);
```

### Valid SSE status state values (exactly these — no others)
- `"profiling"` — ProfilerNode running
- `"filtering_degrees"` — FilterNode running
- `"scoring_degrees"` — ScoringNode running
- `"generating_explanation"` — ExplanationNode running
- `"fetching_fees"` — AnswerNode fee tool
- `"fetching_market_data"` — AnswerNode market tool
- `"done"` — stream complete, dismiss ThinkingIndicator

Map each to a user-friendly label in `ThinkingIndicator`:
```dart
const thinkingLabels = {
  'profiling':               'Building your profile...',
  'filtering_degrees':       'Checking your eligibility...',
  'scoring_degrees':         'Ranking your matches...',
  'generating_explanation':  'Writing your recommendations...',
  'fetching_fees':           'Fetching fee information...',
  'fetching_market_data':    'Checking market outlook...',
};
```

---

## DESIGN SYSTEM (implement exactly)

### Colour palette
| Role | Name | Hex | Usage |
|---|---|---|---|
| Primary | Academic Teal | `#0F766E` | Buttons, user chat bubbles, nav elements |
| Secondary | Deep Slate | `#334155` | Headings, body text |
| AI Indicators | Future Purple | `#7C3AED` | ThinkingIndicator, thought trace panel, FutureValue badges |
| Background | Paper White | `#F8FAFC` | All screen backgrounds |
| Success | Safe Green | `#10B981` | Confirmed eligible, Emerging LagScoreBadge |
| Warning | Risk Amber | `#F59E0B` | Stretch/likely, OCR low confidence, Peak LagScoreBadge |
| Error | Critical Red | `#EF4444` | Improvement needed, Saturated LagScoreBadge, errors |

Future Purple is used **exclusively** for AI elements — never for static UI.

### Typography
All text uses Google Fonts Inter (already in pubspec.yaml).
- Headings: Bold, 24–32px
- Subheadings: SemiBold, 18–20px
- Body/chat text: Regular, 16px, line-height 1.5
- Captions/timestamps: Medium, 12px

### Chat bubbles
- **User bubble:** Right-aligned, Teal background, white text, sharp bottom-right corner
- **Agent bubble:** Left-aligned, white/light-gray background, dark text, sharp top-left corner
- Agent bubbles support embedded rich widgets (UniversityCard rendered inside bubble)
- Agent avatar: abstract geometric hexagon, Future Purple — NOT a human face

### Surface elevation
- Screen backgrounds: flat, no shadow
- Chat bubbles: flat, no shadow
- Rich cards (UniversityCard, RoadmapTimeline): soft shadow (elevation 2)

---

## WIDGETS — SPEC (build in Sprint 3 unless noted)

### UniversityCard
Displayed inside agent chat bubble via `rich_ui` event.

Full payload (20 fields — from Point 5):
```json
{
  "type": "university_card",
  "payload": {
    "rank": 1,
    "degree_id": "neduet_bs_cs",
    "degree_name": "BS Computer Science",
    "university_id": "neduet",
    "university_name": "NED University of Engineering & Technology",
    "field_id": "computer_science",
    "total_score": 0.84,
    "match_score_normalised": 0.89,
    "future_score": 8.4,
    "merit_tier": "likely",
    "eligibility_tier": "confirmed",
    "eligibility_note": null,
    "fee_per_semester": 27500,
    "aggregate_used": 82.5,
    "soft_flags": [
      {"type": "commute_distance", "message": "...", "actionable": "..."}
    ],
    "lifecycle_status": "Emerging",
    "risk_factor": "Low",
    "rozee_live_count": 1240,
    "rozee_last_updated": "2026-03-10",
    "policy_pending_verification": false
  }
}
```
Note: `soft_flags` is an array of objects `{type, message, actionable}` — not a string array.

Display elements:
```
Degree name (bold)
University name + zone badge
Merit tier badge: confirmed (teal) / likely (slate) / stretch (amber) / improvement_needed (red)
FutureValue score with LagScoreBadge (lifecycle_status field)
Soft flags list (if any): over_budget, commute_distance etc.
"Ask about this" button → pre-fills chat input with degree context (e.g., "Tell me more about NED BS Computer Science"). Student can edit before sending.
```
If `policy_pending_verification: true` → show amber banner.
If `eligibility_note` is non-null → show amber banner with the eligibility_note text.
(This covers conditionally eligible streams and unusual A Level combinations.)

### LagScoreBadge
Props: `lifecycle_status` — `"Emerging"` | `"Peak"` | `"Saturated"`
Colors: Emerging = Safe Green ↑, Peak = Risk Amber →, Saturated = Critical Red ↓

### ThinkingIndicator (Sprint 2)
3 pulsing dots + status label text. Future Purple accent.
Shown while `status` events arrive. Dismissed on `"done"`.

### OCRVerificationModal (Sprint 2)
Blocks chat interaction (modal). Shows extracted marks as editable fields.
Confirm → calls `POST /api/v1/profile/grades` with the **user-confirmed marks**
(not the raw OCR `extracted_marks` — user may have edited them).
If `confidence_score < 0.80`: show Risk Amber warning and editable fields.
If `confidence_score >= 0.80`: still show modal for confirmation — ALWAYS show it.
User must confirm or correct before proceeding to chat.

### MismatchNotice (Sprint 3)
Amber banner shown at top of chat when `mismatch_notice` is non-null.
Dismissable with X. Text comes from backend — do not hardcode.
`mismatch_notice` is included in the ExplanationNode's text response —
the LLM naturally opens with the mismatch when one is detected. No
separate SSE event needed. The text stream handles it. Options: (a) backend adds a
`rich_ui` SSE event type for mismatch, or (b) it is returned in a post-stream API call.
Flag for Backend Chat before building this widget.

### RoadmapTimeline (Sprint 3)
Vertical step list rendered inside chat bubble from `rich_ui` SSE event.
One event per recommendation run (not per degree — top-ranked degree only).

Payload structure:
```json
{
  "type": "roadmap_timeline",
  "payload": {
    "steps": [
      {"label": "Current Status", "detail": "...", "status": "complete"},
      {"label": "Recommended Degree", "detail": "...", "status": "next"},
      {"label": "Industry Entry", "detail": "...", "status": "future"},
      {"label": "2030 Outlook", "detail": "...", "status": "future"}
    ],
    "field_id": "computer_science",
    "degree_id": "neduet_bs_cs"
  }
}
```

`status` values → visual: `"complete"` = filled teal circle, `"next"` = teal arrow/highlight,
`"future"` = outline slate circle.

---

## NAVIGATION — APP RESUME RULE

On every app launch:
1. Read token from `flutter_secure_storage`
2. If no token → show LoginScreen
3. If token exists → call `GET /api/v1/profile/me`
4. **While `ProfileProvider.isLoading = true`:** show a loading/splash screen.
   Do NOT attempt to read `onboarding_stage` while profile is null — this will crash.
5. Once loaded: read `onboarding_stage` from response
6. Route to the correct screen (see table in STATE MANAGEMENT section above)

**Never hardcode navigation decisions.** Always follow `onboarding_stage`.

---

## OFFLINE / NETWORK HANDLING

Use `connectivity_plus` package to detect network state.

**When connection drops during SSE stream (implement in Sprint 2):**
- Mark message as "Pending" (grey, clock icon)
- Auto-retransmit on reconnection
- Never lose user's typed message

**Profile caching for mobile:**
Cache latest profile and recommendations locally with `shared_preferences`
so student can view their roadmap without active connection.

---

## MARKSHEET UPLOAD — SPECIFICS

- Use `image_picker` package — do not request `MANAGE_EXTERNAL_STORAGE`
- Compress before upload: max 1920px on longest side, JPEG quality 85%
- Keep text sharp — do not reduce below 72 DPI equivalent
- Upload as `multipart/form-data` with form field name `file` (JPEG or PNG, max 10 MB)
- Show "Scanning..." animation during OCR processing (OCR runs server-side via Gemini Vision)
- After OCR response: show `OCRVerificationModal` — ALWAYS, regardless of confidence
- Only call `POST /api/v1/profile/grades` AFTER user confirms/edits the extracted marks

---

## GUARDRAILS (enforce always)

1. Never call backend endpoints with hardcoded user_id in request body.
   Identity comes from JWT — the backend reads it from the token.
2. Never store JWT in `SharedPreferences` — use `flutter_secure_storage` only.
3. Never show raw RIASEC scores to the student — used internally only.
4. Never concatenate user input directly into API request URLs.
5. `upload.py` does not exist as a backend file — marksheet upload goes to
   `POST /api/v1/profile/marksheet` inside `profile.py`.
6. Do not call `POST /api/v1/admin/seed-knowledge` from the student app.
7. `http` package only for SSE — never `dio` for the streaming endpoint.
8. Never show stack traces or internal error messages to students.
   Show friendly error messages with retry options.
9. **JWT expiry (401 handling):** JWT expires in 60 minutes. On any HTTP 401
   response from any endpoint: clear the stored token from `flutter_secure_storage`,
   set `AuthState.token = null`, and navigate to LoginScreen with message:
   *"Session expired — please log in again."* Never silently retry a 401.
10. **Rate limit (429 handling):** The chat endpoint is rate-limited at 10 req/min
    per IP. On HTTP 429: show message *"Too many requests — please wait a moment"*,
    disable the send button for 60 seconds, then re-enable. Never crash or show
    a raw error code to the student.
11. **BASE_URL never changes in committed code:** The base URL is set to
    `https://fyp-career-guidance-api.onrender.com` in `api_service.dart`.
    Never override this with localhost in any committed file. For local
    backend testing only, change it temporarily and do not commit.

---

## PRODUCING CLAUDE CODE PROMPTS

When producing a Claude Code prompt, always include:
1. Which files to read first (CLAUDE.md, this file, specific source files)
2. Exact problem description with file paths
3. Which files to change and which to leave alone
4. How to verify it worked (`flutter run -d chrome` and test the specific flow)
5. Expected outcome
6. Include these three log rules verbatim in every Claude Code prompt:
   - Read `logs/README.md` before starting any task
   - After writing the session log, update `logs/README.md` immediately —
     add a new row to the STANDARD SESSION LOGS table
   - Write session logs to `logs/` root only (`logs/claude-code-YYYY-MM-DD-HH-MM-description.md`).
     Never write to `logs/audits/` or `logs/changes/` — Opus-reserved folders.

Format: structured numbered steps. Claude Code executes better with explicit
numbered instructions than with prose.

---

## SCREEN BUILD ORDER (priority for April 29 demo)

| Priority | Screen | File | API dependency |
|---|---|---|---|
| 1 FIRST | Fix Android package name | android/ files | none |
| 2 | Splash + Carousel | splash_screen.dart, carousel_screen.dart | none |
| 3 | Login + Signup | login_screen.dart, signup_screen.dart | /auth/register, /auth/login |
| 4 | RIASEC Quiz + Complete | riasec_quiz_screen.dart, riasec_complete_screen.dart | /profile/quiz |
| 5 | Grades Input + Complete | grades_input_screen.dart, grades_complete_screen.dart | /profile/grades |
| 6 | Assessment + Complete | assessment_screen.dart, assessment_complete_screen.dart | /profile/assessment |
| 7 | Chat screen | chat_screen.dart | /chat/stream (SSE) |
| 8 | Recommendation Dashboard | recommendation_dashboard.dart | reads from chat state |
| 9 | Profile screen | profile_screen.dart | /profile/me |

Splash + Carousel can be one session (no API calls).
RIASEC Complete, Grades Complete, Assessment Complete are simple success
screens — bundle each with its parent screen in one session.
All other screens: one per Claude Code session.

---

## VISUAL DESIGN — LOCKED

The app design is complete and locked. All screens are in design/screen_mockups/.

Khuzzaim does NOT make design decisions.
Every visual decision is already made and documented.

For every screen implementation:
- Read DESIGN_HANDOFF.md — implementation guide, one section per screen, exact
  widget types, colours, spacing, API connections, navigation
- Read DESIGN_SYSTEM_TOKENS.md — full token reference
- Open code_[screenname].html — visual reference only.
  DO NOT convert HTML to Flutter. Build from scratch using Flutter widgets
  matching the visual target.

Design files:
- `design/screen_mockups/DESIGN_HANDOFF.md`
- `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md`
- `design/screen_mockups/DESIGN.md` (v1.5 change log)
- `design/screen_mockups/code_[screen].html` (×16)

---

## WHAT IS NOT YOUR SCOPE

- backend/ Python code — flag for Backend Chat
- JSON data files — flag for Data Chat
- CLAUDE.md edits — produce update block, flag for Architecture Chat
- assessment_questions.json content — Khuzzaim writes this directly
  (read `docs/00_architecture/POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md` for the exact schema
  before writing any questions — 1140 questions total)
- pgvector, any vector search feature — not used
- BLoC state management — not used, overkill for this scope
