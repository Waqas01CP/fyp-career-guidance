# claude-code-2026-04-26-16-00-nav-architecture.md
## Session: Nav Architecture + Keyboard + Draft Fixes
### Date: 2026-04-26 | Model: Sonnet 4.6

---

## INPUT PROMPT SUMMARY

Four issues found during device testing on Pixel 4:
1. Login overflows when keyboard appears
2. No natural back navigation (pushReplacementNamed destroys stack)
3. Assessment back button missing
4. Assessment draft not saving reliably (debounce race on close)

---

## FILES READ

1. logs/README.md
2. CLAUDE.md
3. frontend/lib/main.dart
4. frontend/lib/screens/splash_screen.dart
5. frontend/lib/screens/auth/login_screen.dart
6. frontend/lib/screens/auth/signup_screen.dart
7. frontend/lib/screens/onboarding/riasec_quiz_screen.dart
8. frontend/lib/screens/onboarding/riasec_complete_screen.dart
9. frontend/lib/screens/onboarding/grades_input_screen.dart
10. frontend/lib/screens/onboarding/grades_complete_screen.dart
11. frontend/lib/screens/onboarding/assessment_screen.dart
12. frontend/lib/screens/onboarding/assessment_complete_screen.dart

---

## CHANGES MADE

### FIX 1 — Keyboard overflow (login_screen.dart, signup_screen.dart)

Both files:
- Added `resizeToAvoidBottomInset: false` to Scaffold
- Moved `SafeArea` inside `LayoutBuilder` (was outside before)
- `LayoutBuilder` now reads `MediaQuery.of(context).viewInsets.bottom`
- `isCompact` threshold changed from `constraints.maxHeight < 680` to
  `availableHeight < 600` (availableHeight = maxHeight - keyboardHeight)
- Added `ConstrainedBox(minHeight: constraints.maxHeight)` around scrollable content
- Added keyboard-aware bottom padding:
  `keyboardHeight > 0 ? keyboardHeight + 16.h : 24.h`
- Removed leading topPadding `SizedBox` (now in `Padding.top`)
- Removed trailing `SizedBox(vGap)` (now in `Padding.bottom`)

### FIX 2 — Navigation architecture

Navigation type rules applied:
- `pushNamed` for all forward onboarding steps (preserves back stack)
- `pushNamedAndRemoveUntil('/chat', ...)` from assessment to chat (clean break)
- `pushReplacementNamed` for splash → screens, login ↔ signup lateral, re-entry guards
- `pushNamedAndRemoveUntil('/login', ...)` for Leave quiz / 401 paths (unchanged)

Per-file changes:

**login_screen.dart:**
- "Sign Up" GestureDetector: `pushReplacementNamed('/signup')` → `pushNamed('/signup')`
  WHY: test requires back from signup → login; pushReplacementNamed destroyed login

**riasec_quiz_screen.dart (submission path only):**
- After successful POST /profile/quiz: `pushReplacementNamed('/riasec-complete')` → `pushNamed('/riasec-complete')`
- Leave confirmation path (pushNamedAndRemoveUntil + addPostFrameCallback) UNCHANGED per Note 2

**riasec_complete_screen.dart:**
- `automaticallyImplyLeading: false` → `automaticallyImplyLeading: true`
  (system back arrow appears, goes back to riasec quiz)
- Continue button: `pushReplacementNamed('/grades-input')` → `pushNamed('/grades-input')`

**grades_input_screen.dart:**
- After successful POST /profile/grades: `pushReplacementNamed('/grades-complete')` → `pushNamed('/grades-complete')`
- Existing custom leading `maybePop` back button left unchanged (equivalent to system back)

**grades_complete_screen.dart:**
- `automaticallyImplyLeading: false` → `automaticallyImplyLeading: true`
  (system back arrow appears, goes back to grades input)
- Continue button: `pushReplacementNamed('/assessment')` → `pushNamed('/assessment')`

**assessment_screen.dart:**
- Results sheet "View Full Report": `pushReplacementNamed('/assessment-complete')` →
  `pushNamedAndRemoveUntil('/assessment-complete', (route) => false)`
  WHY: clears entire onboarding stack so chat has no back to assessment

**assessment_complete_screen.dart:**
- Removed custom leading `IconButton` (was `pushReplacementNamed('/assessment')` — wrong)
- Added `automaticallyImplyLeading: false` (no back: reached via pushNamedAndRemoveUntil)
- Continue button: `pushReplacementNamed('/chat')` →
  `pushNamedAndRemoveUntil('/chat', (route) => false)`

### FIX 3 — Draft save on app pause (assessment_screen.dart, riasec_quiz_screen.dart)

Both files:
- Added `WidgetsBindingObserver` mixin to state class
- `initState`: added `WidgetsBinding.instance.addObserver(this)`
- `dispose`: added `WidgetsBinding.instance.removeObserver(this)` (before cancel/dispose)
- Added `didChangeAppLifecycleState` override:
  - Triggers on `AppLifecycleState.paused` or `AppLifecycleState.detached`
  - Cancels pending debounce timer, then calls `_saveDraft()` immediately
  - Guarantees draft is written before OS terminates the app

### FIX 4 — Assessment AppBar back button (assessment_screen.dart)

- Added `leading: IconButton(icon: arrow_back, onPressed: _onBackPressed)` to AppBar
- Changed `titleSpacing: 12` → `titleSpacing: 0` (no double-gap with leading button)
- `_onBackPressed` already existed (shows "Leave assessment?" dialog, Navigator.pop on confirm)
- `PopScope(canPop: false)` still active — system back button also triggers dialog

---

## BACK STACK AFTER CHANGES

```
[Login] →pushNamed→ [Login, Signup]
         back ↑ (Login restored)

[Login] →login success→ [target screen] (pushReplacementNamed — correct)

[RIASEC Quiz] →submit→ [RIASEC Quiz, RIASEC Complete]
               back ↑ (RIASEC quiz with answers still in memory)

[RIASEC Complete] →Continue→ [RIASEC Quiz, RIASEC Complete, Grades Input]
                   back ↑ (RIASEC Complete)

[Grades Input] →submit→ [RIASEC Quiz, RIASEC Complete, Grades Input, Grades Complete]
                back ↑ (Grades Input)

[Grades Complete] →Continue→ [..., Grades Complete, Assessment]
                   back ↑ → dialog → pop → Grades Complete

[Assessment] →View Full Report→ [Assessment Complete]  ← pushNamedAndRemoveUntil clears all
[Assessment Complete] →Continue→ [Chat]  ← pushNamedAndRemoveUntil clears all
```

---

## SELF-REVIEW CHECKLIST

1. login_screen: resizeToAvoidBottomInset: false ✓, viewInsets.bottom ✓
2. signup_screen: same keyboard fix ✓
3. riasec_quiz_screen: submission → pushNamed to /riasec-complete ✓
4. riasec_complete_screen: Continue → pushNamed to /grades-input ✓
5. grades_input_screen: submission → pushNamed to /grades-complete ✓
6. grades_complete_screen: Continue → pushNamed to /assessment ✓
7. assessment_screen: View Full Report → pushNamedAndRemoveUntil to /assessment-complete ✓
8. assessment_complete_screen: Continue → pushNamedAndRemoveUntil to /chat ✓
9. assessment_screen: WidgetsBindingObserver + didChangeAppLifecycleState ✓
10. riasec_quiz_screen: same WidgetsBindingObserver pattern ✓
11. assessment_screen: AppBar has leading back button with dialog ✓
12. riasec_complete + grades_complete: automaticallyImplyLeading: true (no custom back buttons) ✓
13. login pushNamed for Sign Up (back stack preserved) ✓
14. flutter analyze: 0 errors ✓

---

## DEVICE TEST RESULTS

Physical device test REQUIRED before committing.
Device not available during this session.

Expected test outcomes:
1. Login keyboard — open login, tap email field, keyboard appears: no overflow, no yellow stripes
2. Natural back navigation:
   - Login → Sign Up → back → Login (pushNamed restores login)
   - RIASEC quiz → submit → RIASEC Complete → back → RIASEC quiz (answers in memory)
   - RIASEC Complete → Continue → Grades Input → back → RIASEC Complete
   - Grades Complete → Continue → Assessment → AppBar back → dialog → Leave → Grades Complete
3. Assessment draft on close:
   - Answer 10 questions, close app immediately, reopen → resume at correct question
4. Assessment → Chat (no back):
   - View Full Report → Assessment Complete → Continue → Chat
   - Press back → stays on Chat (stack cleared by pushNamedAndRemoveUntil)
5. No regression: full flow login → chat without overflow or navigation errors

---

## flutter analyze OUTPUT

```
Analyzing frontend...
No issues found! (ran in 33.1s)
```

---

## STATUS

NOT COMMITTED — physical device test required before commit.
