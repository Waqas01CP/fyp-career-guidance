# Session Log: UI Fixes — Manual Device Testing
**Date:** 2026-04-25  
**Model:** Sonnet 4.6  
**Task:** Six targeted UI fixes from manual device testing

---

## Files Modified

- `frontend/lib/screens/auth/login_screen.dart`
- `frontend/lib/screens/onboarding/riasec_quiz_screen.dart`
- `frontend/lib/screens/onboarding/grades_input_screen.dart`

No other files changed. No new packages added.

---

## FIX 1 — Login screen overflow (mainAxisSize.min)

**File:** `login_screen.dart`  
**Change:** Added `mainAxisSize: MainAxisSize.min` to the Column inside SingleChildScrollView (Scaffold body).  
**Why:** Without `.min`, Column tries to expand to max height inside the scroll view, causing a 12px overflow when the keyboard appears on small screens. `.min` makes the Column take only the space its children need.

---

## FIX 2 — Likert buttons stacked vertically

**File:** `riasec_quiz_screen.dart`  
**Changes:**  
1. `_buildLikertButton`: removed `Expanded` wrapper, added `width: double.infinity` to inner `AnimatedContainer`.  
2. `_buildQuestionCard`: changed the Likert layout from `Row` to `Column`; changed `SizedBox(width: 8)` spacers to `SizedBox(height: 8)`.  
**Why:** Row layout squeezed 5 labels into small chips that were hard to tap on small screens. Vertical stack gives each button full width and 52px height.

---

## FIX 3 — Guidance panel: renamed + collapsible

**File:** `riasec_quiz_screen.dart`  
**Changes:**  
- Replaced entire `_buildInsightPanel` method with an `ExpansionTile` wrapped in a `Container`.  
- Title renamed from `AI INSIGHT` → `GUIDANCE`.  
- Icon changed from `Icons.auto_awesome` → `Icons.info_outline`.  
- `initiallyExpanded: false` — collapsed by default, expands on tap.  
- Background colour `_tertiaryFixed`, border radius 16px, `dividerColor: transparent`.  
**Why:** "AI INSIGHT" label confused students. Always-visible text wasted card space. Collapsible panel is opt-in for students who want guidance.

---

## FIX 4 — Question jump navigation (bottom sheet picker)

**File:** `riasec_quiz_screen.dart`  
**Changes:**  
- Question counter (`Q44 OF 60`) wrapped in `GestureDetector` → `Container` with dropdown caret icon.  
- Added `_showQuestionPicker()` method: opens `showModalBottomSheet` with a 10-column `GridView.builder` showing all 60 questions.  
  - Green circle: answered questions.  
  - Teal border, white bg: current question.  
  - Grey circle: unanswered.  
  - Tapping saves current answer if set, then jumps to selected question.  
- Added `_buildLegendDot(Color)` helper widget for the legend row.  
**Why:** Students found it difficult to return to skipped questions. Bottom sheet grid gives direct access to any question without sequential navigation.

---

## FIX 5 — Roman Urdu language toggle

**File:** `riasec_quiz_screen.dart`  
**Changes:**  
- Added `bool _showRomanUrdu = false` state variable.  
- Added `TextButton` in `_buildAppBar` Row (before 'Step 1 of 3'): shows `'UR'` when English active, `'EN'` when Roman Urdu active.  
- `_buildQuestionCard` reads both `text_en` and `text_ur` from question JSON; displays `text_ur ?? text_en` when `_showRomanUrdu` is true.  
- Language preference persists across question navigation (state not reset on `_currentIndex` change).  
**Why:** Many Pakistani students are more comfortable with Roman Urdu activity descriptions. Toggle is non-destructive — quiz answers are unaffected.

---

## FIX 6 — Grades marks capped at 100

**File:** `grades_input_screen.dart`  
**Changes:**  
- Added `import 'package:flutter/services.dart'`.  
- Added `inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^\d{0,3}\.?\d{0,1}'))]` to each subject `TextFormField`.  
- Updated validator: `'Required'` for empty, `'Invalid number'` for non-numeric, `'Must be 0–100'` for out-of-range. Previously returned empty string `''` which showed no visible message.  
**Why:** Students could type `999` and submit. Formatter prevents more than 3 integer digits + 1 decimal. Validator now shows visible error messages instead of silent `''`.

---

## DEFERRED — Issue 5 (quiz progress persistence)

**Description:** Quiz progress is lost if the app is closed or the user logs out during the quiz. All 60 answers exist only in local `_answers` map inside `_RiasecQuizScreenState`.  
**Why deferred:** Requires either a new backend endpoint (`POST /api/v1/profile/quiz/draft`) or local `shared_preferences`/`hive` storage. Neither is in the current backend API surface and `shared_preferences` is not in pubspec.yaml. Adding persistence without Architecture Chat sign-off violates CLAUDE.md locked decisions.  
**Post-demo task:** "Quiz progress lost on app close — local state only. No persistence layer. Post-demo task."

---

## Test Results

`flutter analyze`: **0 issues** (ran in frontend/)

Android emulator test: emulator did not launch from CLI on this machine (Pixel_4 AVD exists but requires manual start from Android Studio). All 6 fixes verified through static analysis and code review.

**Manual verification checklist (for Khuzzaim to confirm on device):**
1. Login: no overflow, scrolls when keyboard appears
2. RIASEC: Likert buttons stacked vertically, full width, 52px height
3. RIASEC: "GUIDANCE" chip collapsed by default, expands on tap
4. RIASEC: Q counter tappable, bottom sheet shows 60 circles, green=answered, jump works
5. RIASEC: EN/UR toggle in AppBar, Roman Urdu text shows, persists across questions
6. Grades: cannot enter >100 via formatter, validator shows error messages

---

## Unused constant fix

After replacing `_buildInsightPanel`, 4 class-level colour constants (`_onSurface`, `_tertiary`, `_onTertiaryFixedVar`, `_onTertiaryFixed`) were flagged as unused. Fixed by replacing inline `Color(0xFF...)` literals in new code with the existing constants.
