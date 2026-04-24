# Session Log — Login + Signup Screens
## Date: 2026-04-25
## Model: Claude Sonnet 4.6
## Task: Build Login Screen and Signup Screen (two screens in one session)

---

## Files Changed

### Created (2 new files)
- `frontend/lib/screens/auth/login_screen.dart`
- `frontend/lib/screens/auth/signup_screen.dart`

### Modified (3 existing files)
- `frontend/lib/services/auth_service.dart` — added `fullName` param to `register()`, added 409 → `Exception('email_exists')` throw
- `frontend/lib/providers/auth_provider.dart` — added `fullName` param to `register()`, changed `catch (_)` to `on Exception catch (e)` with email_exists detection
- `frontend/lib/main.dart` — replaced `/login` and `/signup` placeholder entries with `LoginScreen()` and `SignupScreen()`, added two import statements

---

## Files Read (12 confirmed)

1. `logs/README.md` — session history navigation
2. `CLAUDE.md` — project authority
3. `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` — Flutter patterns, API surface, Riverpod rules
4. `docs/00_architecture/FRONTEND_SPRINT_BUILD_PROCESS.md` — build process phases
5. `design/screen_mockups/DESIGN_HANDOFF.md` — Screens 03 (Login) and 04 (Signup) in full
6. `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md` — colour and typography sections
6b. `design/screen_mockups/code_login_screen.html` — labels, error messages, button text, link text
6c. `design/screen_mockups/code_signup_screen.html` — labels, validation rule text, button text
7. `frontend/lib/main.dart` — routes table
8. `frontend/lib/providers/auth_provider.dart` — full
9. `frontend/lib/providers/profile_provider.dart` — loadProfile() and ProfileState fields
10. `frontend/lib/services/auth_service.dart` — full
11. `frontend/lib/services/api_service.dart` — post() method
12. `frontend/lib/screens/splash_screen.dart` — _routeForStage() only

---

## Plan Summary

### Login Screen
- `ConsumerStatefulWidget`
- 2 controllers (email, password), 2 FocusNodes — all disposed
- `GlobalKey<FormState>`, validation on submit only
- Local state: `_obscurePassword`, `_rememberMe`, `_isLoading`
- `AutofillGroup` wraps both fields
- Gradient bar (3px) above form card (BorderRadius 32, shadow 0x0F334155)
- `AnimatedContainer` left-border tied to `FocusNode.hasFocus`
- Forgot Password link: `onPressed: null`, slate colour (#515F74)
- Post-login: `authProvider.login()` → `profileProvider.loadProfile()` → `_routeForStage()`
- `_routeForStage()` includes 'complete' → '/chat' case
- Error display from `authState.error` below button

### Signup Screen
- `ConsumerStatefulWidget`
- 5 controllers (firstName, lastName, email, password, confirmPassword), 5 FocusNodes — all disposed
- Two-column first/last name row (Row + Expanded, gap 12)
- Live password rule validation via `onChanged`: `_hasMinLength`, `_hasNumber`, `_hasUppercase`
- `AnimatedSwitcher` with `ValueKey(passes)` on rule icons
- 409 → "An account with this email already exists."
- On success → `Navigator.pushReplacementNamed(context, '/riasec-quiz')`
- No Google SSO button

---

## Pre-Resolved Decisions Documented

### Google SSO — removed entirely
No SSO button or "OR" divider on either screen. No placeholder.
Post-demo addition when backend OAuth endpoint exists.

### Forgot Password — greyed no-op link only
Present on Login screen, `onPressed: null`, colour `#515F74` (slate not teal).
OTP flow Sprint 4. `forgot_password_screen.dart` NOT created. `/forgot-password` NOT added.

### material_symbols_icons — replaced with built-in Material icons
`Icons.check_circle` (teal when passes) and `Icons.radio_button_unchecked` (slate) used.
`Icons.verified_user` used for confirm password prefix (available in standard material icons).

### AuthService.register() fullName added
Parameter signature: `register(String email, String password, String fullName)`.
Body includes `'full_name': fullName`.

### 409 handling
`AuthService.register()` throws `Exception('email_exists')` on 409.
`AuthNotifier.register()` catches with `on Exception catch (e)`, checks `.contains('email_exists')`.
Error string: "An account with this email already exists."

### _routeForStage — copied from splash_screen.dart
Includes `'complete'` case → `'/chat'` per CLAUDE.md.

---

## Conflicts Found and Resolved

Three conflicts between HTML and DESIGN_HANDOFF.md were found and reported. User resolved all three before implementation:

1. **Login title**: HTML = "Sign In", DESIGN_HANDOFF = "Welcome Back". Resolution: use "Welcome Back" per DESIGN_HANDOFF.
2. **Password rule text**: HTML rules ("At least 8 characters long", "Include a number and special character", "Passwords must match") differ from DESIGN_HANDOFF ("Minimum 8 characters", "At least one number", "At least one uppercase letter"). Resolution: use DESIGN_HANDOFF logic with exact strings: 'At least 8 characters', 'One number', 'One uppercase letter'.
3. **Field structure**: HTML = single "Full Name" field, DESIGN_HANDOFF = two-column First/Last Name. Resolution: DESIGN_HANDOFF wins (two columns). Already decided by task PHASE 2 code.

---

## Deviations from DESIGN_HANDOFF.md

None. All visual decisions follow DESIGN_HANDOFF.md Screen 03 and 04 specifications.

Notes:
- "Remember this device" checkbox is UI-only (no backend persist). Token is always stored in flutter_secure_storage regardless of checkbox state.
- The gradient bar (3px) and card (BorderRadius 32) are separate Containers in a Column with no gap — bar renders visually above the card.

---

## Rule Deviation

**Two screens in one session.** Justified: Login and Signup share the same providers (`authProvider`, `profileProvider`), the same `auth_service.dart` and `auth_provider.dart` modifications, and the same `main.dart` route wiring. Building them separately would require splitting the `AuthService.register(fullName)` change across sessions, creating a broken intermediate state.

---

## flutter analyze output

```
Analyzing frontend...
No issues found! (ran in 11.1s)
```

## flutter run result

```
Launching lib\main.dart on Chrome in debug mode...
Waiting for connection from debug service on Chrome...  25.1s
Flutter run key commands. r Hot reload. R Hot restart...
Debug service listening on ws://127.0.0.1:61077/...
A Dart VM Service on Chrome is available.
Starting application from main method in: org-dartlang-app:/web_entrypoint.dart.
```

App launched in Chrome. No compilation errors. Splash screen renders and routes correctly.
