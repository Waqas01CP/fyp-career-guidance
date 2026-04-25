# claude-code-2026-04-25-21-00-bundle1-fixes.md
## Six UI fixes from device testing — Bundle 1

**Date:** 2026-04-25
**Model:** Sonnet 4.6
**Files modified:** 4
- `frontend/lib/screens/auth/login_screen.dart`
- `frontend/lib/screens/onboarding/grades_input_screen.dart`
- `frontend/lib/screens/onboarding/riasec_quiz_screen.dart`
- `frontend/lib/screens/onboarding/assessment_screen.dart`

**Files unchanged (Fix 6 — no "Academic Intelligence" text found):**
- `frontend/lib/screens/onboarding/riasec_complete_screen.dart`
- `frontend/lib/screens/onboarding/assessment_complete_screen.dart`
- `frontend/lib/screens/onboarding/grades_complete_screen.dart`

---

## FIX 1 — Login screen overflow on Samsung A6

**File:** `frontend/lib/screens/auth/login_screen.dart`

**Before:**
```dart
child: SingleChildScrollView(
  padding: EdgeInsets.all(24.r),
  child: Column(
```

**After:**
```dart
child: SingleChildScrollView(
  padding: EdgeInsets.symmetric(horizontal: 24.w, vertical: 24.h),
  child: Column(
```

**Why:** `EdgeInsets.all(24.r)` uses `.r` (min-dimension scale), which on a narrow screen applies the same value to vertical padding too. Separating to `.w` and `.h` reduces vertical padding on small screens, recovering the 45px overflow headroom. The Column already had `mainAxisSize: MainAxisSize.min` and no Spacer() from the previous session's fix.

---

## FIX 2 — Validation message wording in grades

**File:** `frontend/lib/screens/onboarding/grades_input_screen.dart`

**Before:**
```dart
if (n < 0 || n > 100) return 'Must be 0–100';
```

**After:**
```dart
if (n < 0 || n > 100) return 'Enter a value between 1 and 100';
```

One text change only, per spec.

---

## FIX 3 — Guidance chip icon and font size

**File:** `frontend/lib/screens/onboarding/riasec_quiz_screen.dart`
**Method:** `_buildInsightPanel()`

**Before:**
```dart
leading: Icon(Icons.info_outline, size: 16.r, color: _tertiary),
title: Text('GUIDANCE',
    style: TextStyle(
        fontSize: 9.sp,
        fontWeight: FontWeight.w700,
        color: _onTertiaryFixedVar,
        letterSpacing: 0.9.sp)),
```

**After:**
```dart
leading: Icon(Icons.info_outline, size: 18.r, color: _tertiary),
title: Text('GUIDANCE',
    style: TextStyle(
        fontSize: 12.sp,
        fontWeight: FontWeight.w700,
        color: _onTertiaryFixedVar,
        letterSpacing: 1.0.sp)),
```

Three values changed: icon 16→18.r, fontSize 9→12.sp, letterSpacing 0.9→1.0.sp.

---

## FIX 4 — Assessment submit guard

**File:** `frontend/lib/screens/onboarding/assessment_screen.dart`
**Method:** `_onSubmit()` — guard added at start, before token check

**Before:**
```dart
Future<void> _onSubmit() async {
  final token = ref.read(authProvider).token;
  if (token == null) return;
```

**After:**
```dart
Future<void> _onSubmit() async {
  if (_answers.length < _questions.length) {
    final unanswered = _questions.length - _answers.length;
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
            '$unanswered question${unanswered == 1 ? '' : 's'} '
            'still unanswered. Please complete all questions.'),
        backgroundColor: const Color(0xFFBA1A1A),
        duration: const Duration(seconds: 3),
      ),
    );
    return;
  }

  final token = ref.read(authProvider).token;
  if (token == null) return;
```

**Note:** The guard works correctly with the auto-advance timer path — when the timer fires after Q60 is answered, `_answers` has all 60 answers (stored in `_onOptionSelected`), so the guard passes without showing a snackbar.

---

## FIX 5 — RIASEC "View My Results" guard

**File:** `frontend/lib/screens/onboarding/riasec_quiz_screen.dart`

Three changes made:

### 5a — Store answer immediately in Likert button
**Method:** `_buildLikertButton()`

**Before:**
```dart
onTap: () {
  setState(() => _selectedAnswer = score);
  _scheduleDraftSave();
},
```

**After:**
```dart
onTap: () {
  final qId = _questions[_currentIndex]['id'] as int;
  setState(() {
    _selectedAnswer = score;
    _answers[qId] = score;
  });
  _scheduleDraftSave();
},
```

**Why:** Without this, `_answers.length` only reflects questions where the user navigated forward — the current question's answer lives only in `_selectedAnswer`. Storing immediately makes `_answers.length` a reliable count of all answered questions, enabling the guard to compute unansweredCount correctly.

### 5b — Compute unansweredCount in _buildNavRow()
**Before:**
```dart
final isLast      = _currentIndex == _questions.length - 1;
final isPrevDisabled = _currentIndex <= 0;
final isSubmitEnabled = _selectedAnswer != null && !_isSubmitting;
```

**After:**
```dart
final isLast         = _currentIndex == _questions.length - 1;
final isPrevDisabled = _currentIndex <= 0;
final unansweredCount = _questions.length - _answers.length;
final allAnswered     = unansweredCount == 0;
final isSubmitEnabled = _selectedAnswer != null && !_isSubmitting && allAnswered;
```

And the button call updated:
```dart
// Before:
_buildViewResultsButton(isSubmitEnabled)
// After:
_buildViewResultsButton(isSubmitEnabled, unansweredCount)
```

### 5c — Update _buildViewResultsButton() signature and text
**Before:**
```dart
Widget _buildViewResultsButton(bool isEnabled) {
  ...
  : Text(
      'View My Results',
      ...
    ),
```

**After:**
```dart
Widget _buildViewResultsButton(bool isEnabled, int unansweredCount) {
  ...
  : Text(
      unansweredCount > 0
          ? '$unansweredCount left to answer'
          : 'View My Results',
      ...
    ),
```

**Behaviour:** On Q60, if user skipped any earlier questions via the picker, button shows "X left to answer" (disabled). Once all 60 questions are answered, button shows "View My Results" (enabled).

---

## FIX 6 — AppBar title truncation

**Files where "Academic Intelligence" was found and removed:**
- `riasec_quiz_screen.dart` — custom `_buildAppBar()` method
- `assessment_screen.dart` — PreferredSize AppBar title Row

**Files checked but no "Academic Intelligence" text found:**
- `grades_input_screen.dart` — AppBar title is "Academic Profile" (correct, kept)
- `riasec_complete_screen.dart` — no AppBar
- `assessment_complete_screen.dart` — no AppBar
- `grades_complete_screen.dart` — AppBar title is "Academic Profile" (correct, kept)

### riasec_quiz_screen.dart `_buildAppBar()`
**Before:**
```dart
Icon(Icons.school, color: _primary, size: 22.r),
SizedBox(width: 6.w),
Flexible(
  child: Text(
    'Academic Intelligence',
    overflow: TextOverflow.ellipsis,
    style: TextStyle(
      fontSize: 17.sp, fontWeight: FontWeight.w700, color: _primary,
    ),
  ),
),
const Spacer(),
```

**After:**
```dart
Icon(Icons.school, color: _primary, size: 22.r),
const Spacer(),
```

### assessment_screen.dart AppBar title Row
**Before:**
```dart
Icon(Icons.school, color: _primary, size: 20.r),
SizedBox(width: 8.w),
Text(
  'Academic Intelligence',
  style: TextStyle(
    fontSize: 16.sp, fontWeight: FontWeight.w700, color: _primary,
  ),
),
const Spacer(),
```

**After:**
```dart
Icon(Icons.school, color: _primary, size: 20.r),
const Spacer(),
```

---

## OUTCOME

`flutter analyze`: 0 issues.

All 6 fixes applied. Verification checklist (manual device test required):
1. Login: no overflow on Samsung A6 equivalent small screen
2. Grades: "Enter a value between 1 and 100" shown on invalid input
3. RIASEC guidance chip: icon 18.r, title 12.sp — more readable
4. Assessment: cannot submit with unanswered questions; snackbar shows count
5. RIASEC Q60: button shows "X left to answer" when questions skipped; "View My Results" when all 60 answered
6. AppBar in RIASEC quiz + assessment: icon only, no text truncation
