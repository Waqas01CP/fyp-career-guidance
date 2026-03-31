# Khuzzaim Frontend Setup Guide
## Complete step-by-step from zero to running Flutter app

---

## PART 1 — Install tools (one time only)

### 1.1 Install Flutter SDK
Go to https://flutter.dev/docs/get-started/install and choose your OS.

**Windows:** Download the SDK zip, extract to `C:\flutter`.
Add `C:\flutter\bin` to your PATH via Environment Variables.

**Mac:** Extract to `~/flutter`. Add to PATH in `~/.zshrc`:
```bash
export PATH="$PATH:$HOME/flutter/bin"
```
Then run `source ~/.zshrc` in the same terminal (or open a new one) for the PATH to take effect.

**Linux:** Same as Mac but add to `~/.bashrc` instead.

After setup, open a new terminal and run: `flutter --version`
Must show Flutter 3.x or higher.

### 1.2 Install VS Code
Download from https://code.visualstudio.com
Inside VS Code, install two extensions:
- **Flutter** (by Dart Code)
- **Dart** (by Dart Code)

### 1.3 Install Git
Download from https://git-scm.com — accept all defaults.
Verify: `git --version`

### 1.4 Install Chrome (for web testing)
Flutter Web runs in Chrome during development.
Download from https://www.google.com/chrome if not already installed.

### 1.5 Run Flutter doctor
```bash
flutter doctor
```
Fix any issues it lists. The important ones are Flutter SDK, Dart, and Chrome.
Android toolchain warnings are fine to ignore if you are testing on web.

---

## PART 2 — Clone the repo

```bash
git clone https://github.com/Waqas01CP/fyp-career-guidance.git
cd fyp-career-guidance
```

---

## PART 3 — Set up the Flutter project

```bash
cd frontend
flutter pub get
```

This downloads all packages listed in `pubspec.yaml`:
- `flutter_riverpod` — state management
- `http` — API calls and SSE streaming
- `flutter_secure_storage` — JWT token storage
- `google_fonts` — Inter font

**Verify it works:**
```bash
flutter run -d chrome
```

You should see the Login screen stub open in Chrome.
If you see any errors, check PART 5 below for common fixes.

**Note on missing packages:** The current `pubspec.yaml` has the core packages
(`flutter_riverpod`, `http`, `flutter_secure_storage`, `google_fonts`).
Packages for later sprints (`image_picker`, `connectivity_plus`, `shared_preferences`)
are not there yet — you will add them when you reach those screens. Run:
```bash
flutter pub add <package_name>
```
from inside `frontend/` when needed.

---

## PART 4 — Daily workflow

Every time you sit down to work:

```bash
# Terminal — from repo root
git pull

# Then from frontend/
cd frontend
flutter pub get   # only needed if pubspec.yaml changed
flutter run -d chrome
```

**Hot reload:** While the app is running, press `r` in the terminal to hot reload
after saving a Dart file. Press `R` for a full restart.

To run on Android instead of Chrome:
```bash
flutter run -d android
```
(Requires Android device connected via USB or Android emulator running.)

---

## PART 5 — Understanding the project structure

```
frontend/lib/
├── main.dart                 ← App entry point. ProviderScope wraps everything.
├── screens/                  ← One file per screen
│   ├── auth/                 ← login_screen.dart, signup_screen.dart (Sprint 1)
│   ├── onboarding/           ← quiz, grades, assessment screens (Sprint 2)
│   ├── chat/                 ← main_chat_screen.dart
│   ├── dashboard/            ← recommendation_dashboard.dart (Sprint 3)
│   └── profile/              ← profile_screen.dart (Sprint 4)
├── widgets/                  ← Reusable components (university card, badges etc.)
├── services/                 ← API calls, SSE streaming, token storage
├── models/                   ← Dart classes matching backend response shapes
└── providers/                ← Riverpod state — auth, profile, chat
```

Read `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` for the full spec
of every screen, widget, and state provider.

---

## PART 6 — State management: Riverpod

The app uses **Riverpod** (`flutter_riverpod` package). This is already set up in
`main.dart`. You do not need to change anything there.

**The key rule:** Every screen that reads or writes state must be a
`ConsumerWidget`, not a `StatelessWidget`.

```dart
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/auth_provider.dart';  // import the provider

// Correct — screen that uses state
class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);  // reads state, rebuilds on change
    // ...
  }
}
```

```dart
// In a button callback — use ref.read, not ref.watch
onPressed: () {
  ref.read(authProvider.notifier).login(email, password);
}
```

The three state providers are in `lib/providers/`:
- `auth_provider.dart` — token, login/logout state
- `profile_provider.dart` — student profile, onboarding stage
- `chat_provider.dart` — messages, SSE streaming state

These are currently empty stubs. You fill them in during Sprint 1 and Sprint 2.
Frontend Chat will produce the exact code for each provider when you reach that task.

---

## PART 7 — Connecting to the backend

Waqas runs the backend server locally. The base URL is:
```
http://127.0.0.1:8000
```

All API endpoints are prefixed `/api/v1/`. Examples:
- `POST http://127.0.0.1:8000/api/v1/auth/register`
- `POST http://127.0.0.1:8000/api/v1/auth/login`
- `GET  http://127.0.0.1:8000/api/v1/profile/me`

**For this to work:**
1. Waqas must have Docker running: `docker compose up -d`
2. Waqas must have the server running: `uvicorn app.main:app --reload` from `backend/`
3. You must be on the same network, or using localhost if on the same machine

**If you are on different networks (remote work):**
Waqas can expose the server temporarily using ngrok:
```bash
# Waqas runs this from backend/ (install ngrok from https://ngrok.com)
ngrok http 8000
```
ngrok gives a public URL like `https://abc123.ngrok.io`.
Change `kBaseUrl` in `api_service.dart` to that URL while working remotely.
Change it back to `http://127.0.0.1:8000` when working locally.

Note: ngrok free tier sessions expire after ~2 hours and the URL changes on each restart.
Update `kBaseUrl` each time Waqas restarts ngrok.

To verify the server is reachable, open Chrome and go to:
`http://127.0.0.1:8000/docs`
You should see the FastAPI docs page with all 9 endpoints.

**Getting a JWT token for testing:**
1. Open `http://127.0.0.1:8000/docs`
2. POST `/api/v1/auth/register` with `{"email": "test@test.com", "password": "testpass123"}`
3. Copy the `access_token` from the response
4. Use it as `Authorization: Bearer <token>` in protected endpoint calls

---

## PART 8 — How navigation works (important)

The app never decides which screen to show based on frontend logic alone.
After login, it calls `GET /api/v1/profile/me` and reads `onboarding_stage`:

| `onboarding_stage` | App routes to |
|---|---|
| `"not_started"` | RIASEC quiz screen |
| `"riasec_complete"` | Grades input screen |
| `"grades_complete"` | Capability assessment screen |
| `"assessment_complete"` | Chat screen |
| `"complete"` | Chat screen (AI has prior context — chat list appears empty, history is server-side) |

If a student closes the app mid-onboarding and reopens it, they return exactly
where they left off. This is handled by always reading `onboarding_stage` on
every app launch.

---

## PART 9 — Session logs

After every Claude Code session, write a log file to `logs/` using this format:
```
logs/session-YYYY-MM-DD-frontend-description.md
```

Example: `logs/session-2026-04-01-frontend-login-screen.md`

The log should contain:
- What was built or fixed
- What files were changed
- Verification result (did `flutter run -d chrome` show the expected screen?)
- Any issues noticed
- What the next session should start with

---

## PART 10 — Sprint 1 tasks

Your Sprint 1 tasks in order:

1. Confirm `flutter run -d chrome` shows login stub — no errors
2. Open Frontend Chat in Claude.ai project. Say:
   > "I need to implement the Login screen and Signup screen for Sprint 1.
   > The backend mock API is running at 127.0.0.1:8000. Please read
   > CLAUDE.md and FRONTEND_CHAT_INSTRUCTIONS.md first, then give me
   > the Claude Code prompt."
3. Run the Claude Code prompt Frontend Chat gives you
4. Test: register a new account, confirm token stored, confirm Chat screen appears
5. Write session log
6. Commit: `feat(frontend): sprint-1 — login, signup, chat shell`

**Also Sprint 1 — test personas (parallel task, no coding needed):**
Design 5 student profiles for FilterNode testing. See SPRINT_PLAN.md for the
exact format. These are used by Waqas to test the recommendation pipeline.
At least one must trigger the mismatch notice. At least one must hit a
conditionally eligible stream.

**Also Sprint 1 — begin assessment_questions.json (no coding needed):**
Khuzzaim writes the 1140 assessment questions. Read
`docs/00_architecture/POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md` for the exact
question schema before writing any. The file lives at
`backend/app/data/assessment_questions.json`.

---

## Common errors and fixes

| Error | Cause | Fix |
|---|---|---|
| `flutter: command not found` | Flutter not in PATH | Windows: re-add `C:\flutter\bin` to PATH. Mac/Linux: re-add `export PATH="$PATH:$HOME/flutter/bin"` to `~/.zshrc` or `~/.bashrc`, then restart terminal |
| `No supported devices found` | Chrome not detected | Run `flutter doctor`, ensure Chrome is installed |
| `Connection refused` on API call | Backend not running | Ask Waqas to start the server |
| `flutter pub get` fails | pubspec.yaml changed | Run `flutter clean` then `flutter pub get` again |
| Hot reload not reflecting changes | Logic change, not UI | Press `R` (capital) for full restart instead of `r` |
| `flutter_secure_storage` error on web | Web uses different storage | This is expected — `flutter_secure_storage` falls back to localStorage on web automatically |
| `Target of URI doesn't exist` | A stub file imports a missing package | Run `flutter pub add <missing_package>` then retry |
