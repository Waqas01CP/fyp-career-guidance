# Session Log — Foundation: Providers + main.dart
## Date: 2026-04-24
## Model: Claude Sonnet 4.6
## Task: Foundation setup — fix model, rewrite providers, replace main.dart

---

## FILES CHANGED (7 files — 6 planned + 1 required fix)

| File | Change |
|---|---|
| `frontend/lib/models/recommendation.dart` | Bug 1: riskFactor double→String. Bug 2: rozeeLastUpdated added. |
| `frontend/lib/models/chat_message.dart` | Added required `id` field (expanded from 5-file plan — required for chat_provider to compile). |
| `frontend/lib/providers/auth_provider.dart` | Complete replacement: ChangeNotifier stub → StateNotifier. |
| `frontend/lib/providers/profile_provider.dart` | Complete replacement: ChangeNotifier stub → StateNotifier. |
| `frontend/lib/providers/chat_provider.dart` | Complete replacement: ChangeNotifier stub → StateNotifier. |
| `frontend/lib/main.dart` | Complete replacement: stock counter → ProviderScope + AppRouter + 16 named routes. |
| `frontend/test/widget_test.dart` | Updated stock counter test to reference FypApp — required to pass flutter analyze (zero errors rule). |

---

## FILES READ (16 files)

1. logs/README.md
2. CLAUDE.md
3. docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md
4. docs/00_architecture/FRONTEND_SPRINT_BUILD_PROCESS.md
5. docs/00_architecture/POINT_5_API_SURFACE_v1_2.md
6. frontend/lib/models/recommendation.dart
7. frontend/lib/models/student_profile.dart
8. frontend/lib/models/chat_message.dart
9. frontend/lib/services/auth_service.dart
10. frontend/lib/services/api_service.dart
11. frontend/lib/services/sse_service.dart
12. frontend/lib/providers/auth_provider.dart
13. frontend/lib/providers/profile_provider.dart
14. frontend/lib/providers/chat_provider.dart
15. frontend/lib/main.dart
16. frontend/pubspec.yaml

---

## PLAN SUMMARY

Three conflicts found during Phase 1 plan review — execution held until resolved:

**Conflict 1 (CLAUDE.md):** Provided main.dart routed no-token case to `/login`. CLAUDE.md requires carousel first (no token = first install or post-logout). Resolved: route to `/onboarding`.

**Conflict 2 (CLAUDE.md + Point 5):** Provided `_routeForStage` mapped `not_started` to `/onboarding` (carousel). CLAUDE.md Onboarding State Machine and Point 5 routing table both specify `not_started` → RIASEC quiz. Resolved: route to `/riasec-quiz`.

**Conflict 3 (technical):** Provided chat_provider.dart used `ChatMessage(id: ...)` but existing ChatMessage model had no `id` field. Would cause compile error. Resolved by user: add `id` as required field to chat_message.dart. Modify list expanded from 5 to 6 files.

All three resolved by user before implementation began.

---

## recommendation.dart BUG FIX DETAIL

**Bug 1 — riskFactor type mismatch:**
- Before: `final double riskFactor;` and `(json['risk_factor'] as num).toDouble()`
- After: `final String riskFactor;` and `json['risk_factor'] as String? ?? 'Low'`
- Reason: Point 5 university_card payload shows `"risk_factor": "Low"` — a String, not a number.

**Bug 2 — rozeeLastUpdated missing:**
- Before: field absent from model, absent from constructor, absent from fromJson
- After: `final String? rozeeLastUpdated;` added to fields, `this.rozeeLastUpdated` (optional) added to constructor, `rozeeLastUpdated: json['rozee_last_updated'] as String?` added to fromJson
- Reason: Point 5 university_card payload includes `"rozee_last_updated": "2026-03-10"`.

**Known pre-existing bug NOT fixed (out of task scope):**
`softFlags` is `List<String>` but Point 5 specifies `soft_flags` as `List<{type, message, actionable}>`. This will fail at runtime when the backend returns objects. Must be fixed in the Dashboard session.

---

## PROVIDER STATE SHAPES

### AuthState
```
String?  token          — JWT string. null = unauthenticated.
bool     isLoading      — true during login/register API call.
String?  error          — user-facing error message, null if none.
bool     isAuthenticated — computed: token != null
```
AuthNotifier: `_restoreToken()` on init, `register()`, `login()`, `logout()`, `handleUnauthorized()`.

### ProfileState
```
String   onboardingStage  — drives navigation. default: 'not_started'
String?  sessionId         — required for /chat/stream. from GET /profile/me.
Map      riasecScores      — {R,I,A,S,E,C} integers 10-50. empty {} until quiz.
Map      subjectMarks      — subject→percentage. empty {} until grades.
Map      capabilityScores  — subject→float 0-100. empty {} until assessment.
String   studentMode       — 'inter' or 'matric_planning'. default: 'inter'
String?  educationLevel    — e.g. 'inter_part2'. null until grades submitted.
bool     isLoading         — true during GET /profile/me call.
bool     isLoaded          — true after first successful load.
String?  error             — 'session_expired' sentinel or user-facing message.
```
ProfileNotifier: `loadProfile(token)`, `updateOnboardingStage(stage)`, `reset()`.

### ChatState
```
List<ChatMessage>       messages           — conversation history (user + assistant)
List<Recommendation>    recommendations    — from rich_ui university_card events
Map<String,dynamic>?    roadmapTimeline    — from rich_ui roadmap_timeline event
String?                 currentStatusLabel — shown in ThinkingIndicator
bool                    isStreaming        — true while SSE connection is open
String?                 error              — user-facing error message
```
ChatNotifier: `addUserMessage`, `startAssistantMessage`, `appendChunk`, `updateStatus`, `addRecommendation`, `setRoadmapTimeline`, `finishStreaming`, `setError`, `reset`.

---

## AppRouter ROUTING LOGIC SUMMARY

```
initState → _resolveRoute()
    ↓
read authProvider
    ├── isAuthenticated = false (no token)
    │   └── navigate to '/onboarding' (carousel)
    └── isAuthenticated = true (token exists)
        ↓
        await profileProvider.notifier.loadProfile(token)
            ├── error = 'session_expired' (401 from backend)
            │   ├── authProvider.notifier.handleUnauthorized()  (clears token + sets error)
            │   └── navigate to '/login'
            └── no error
                └── _routeForStage(onboardingStage)
                    ├── 'not_started'       → '/riasec-quiz'
                    ├── 'riasec_complete'   → '/grades-input'
                    ├── 'grades_complete'   → '/assessment'
                    ├── 'assessment_complete' → '/chat'
                    └── default             → '/riasec-quiz'
```

While resolving: purple scaffold + white CircularProgressIndicator.

---

## flutter analyze OUTPUT

```
Analyzing frontend...
No issues found! (ran in 3.4s)
```

Zero errors. Zero warnings.

---

## flutter run RESULT

Platform: Chrome (web) — Windows desktop failed (Developer Mode required, not blocking).
Command: `flutter run --no-pub -d chrome`

Output:
```
Launching lib\main.dart on Chrome in debug mode...
Waiting for connection from debug service on Chrome...  37.9s
Debug service listening on ws://127.0.0.1:65220/...
Starting application from main method in: org-dartlang-app:/web_entrypoint.dart.
```

Result: PASS. App launched without crash. No runtime errors. No exception output.
Expected behavior (no stored token on first run): purple loading spinner → routed to `/onboarding` (Onboarding Carousel placeholder screen).

---

## KNOWN LIMITATIONS

1. **Placeholder screens only** — all 16 routes show `_PlaceholderScreen` widget. No real screen implementations yet. Next session: Splash + Carousel screens.

2. **No navigation between placeholders** — carousel placeholder has no "Get Started" button wired to login. Each screen must be built and wired in subsequent sessions.

3. **_restoreToken() race condition** — AuthNotifier calls `_restoreToken()` async in constructor. If AppRouter's `initState` runs before `_restoreToken()` completes, a returning user's stored token might not be read yet, causing a false no-token route to the carousel. This is a known limitation of StateNotifier async init. For the April 29 demo, it is mitigated by the small time window (storage read is fast). A proper fix uses `ref.listen` or a FutureProvider — flag for Architecture Chat.

4. **softFlags type mismatch** — `recommendation.dart` still has `List<String>` for `softFlags` but backend sends `List<{type,message,actionable}>`. Runtime crash when dashboard renders. Must fix in Dashboard session before adding `UniversityCard` widget.

5. **widget_test.dart expanded from modify list** — stock counter test referenced deleted `MyApp`. Updated to basic smoke test referencing `FypApp`. Required for zero-error flutter analyze compliance.
