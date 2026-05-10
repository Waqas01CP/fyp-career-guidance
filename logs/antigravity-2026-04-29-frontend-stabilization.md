# Execution Log: Frontend Stabilization — Issues #1–#4
**Date**: 2026-04-29
**Session**: Antigravity (Gemini / Claude)

---

## Context
This session addressed a set of frontend issues identified during a comprehensive audit of the Academic Career Guidance Flutter app. The objective was to fix incorrect UI, data loss, navigation bugs, and server cold-start hangs before the April 2026 demo. All changes are frontend-only. The backend API and schema were not modified.

---

## Completed Tasks

### Issue #1 — Academic Grades UI Redesign
**Commit**: `c95dd9c`
**File**: `frontend/lib/screens/onboarding/grades_input_screen.dart`

**Problem**: The grades screen used static subject lists with no distinction between local and Cambridge curricula. O/A Level subjects were hardcoded incorrectly. Matric streams were missing. The Karachi Board BSEK requirement for Sindhi was absent. Boards (Cambridge/Local) were not filtered by education level. Year range was too narrow.

**Solution implemented**:
- Replaced monolithic `_streamOptions` and `_boardOptions` with separate `_matricStreams`, `_interStreams`, `_localBoards`, `_cambridgeBoards` lists.
- `_currentStreamOptions` getter returns the correct list based on selected level.
- `_currentBoardOptions` getter returns local boards for Matric/Inter, Cambridge boards for O/A Level.
- Matric streams corrected to: `Science (Biology)`, `Science (Computer)`, `General (Arts)` — each with 8 subjects including `Urdu / Sindhi (Compulsory)`.
- Inter streams corrected to: `Pre-Engineering`, `Pre-Medical`, `ICS`, `Commerce`, `Humanities` — each with 6 subjects including Islamiyat/Pak Studies.
- O Level: 5 fixed compulsory subjects (IBCC-required) + dynamic `+ Add Optional Subject` rows (no hard cap; pool of 10 Cambridge electives).
- A Level: fully dynamic slate with `+ Add A-Level Subject` rows (pool of 12 subjects; no compulsory).
- `_onLevelChanged()` clears all state (stream, board, dynamic rows) when level is switched.
- Year dropdown expanded from 7 years to full range 1980–2026.
- Dynamic marks from optional rows merged into `subject_marks` flat dict on submit — zero backend schema change needed.

**Research performed**: Verified BSEK Class 10 subject requirements (Sindhi compulsory), IBCC O Level equivalency (5 compulsory + min 3 optional = 8 minimum, no hard max ~14), A Level IBCC requirements (3 minimum, no compulsory subjects mandated).

---

### Issue #2 — Draft Persistence for Grades Input
**Commit**: `87823c7`
**File**: `frontend/lib/screens/onboarding/grades_input_screen.dart`

**Problem**: If the app was closed mid-entry, all entered marks were lost. No local storage existed for the grades screen, unlike RIASEC and Assessment screens which already used `flutter_secure_storage`.

**Solution implemented**:
- Added `_storage`, `_draftKey = 'grades_draft'`, and `Timer? _debounce` state fields.
- `_loadDraft()` called in `initState`: reads stored JSON from `flutter_secure_storage`, restores level/stream/board/year/marks and any dynamic O/A Level subject rows.
- `_scheduleSaveDraft()`: debounces 500ms on every state change (any mark typed, any dropdown changed, any dynamic row added/removed).
- `_saveDraft()`: serializes full form state to JSON and writes to secure storage.
- `_clearDraft()`: called after successful `/profile/grades` API submit — deletes the draft so the screen is blank on fresh retake.
- `_debounce?.cancel()` added to `dispose()` to prevent setState after unmount.
- All `onChanged` handlers for stream, board, year, and mark controllers wired to `_scheduleSaveDraft()`.
- Corrupted draft is silently deleted (try/catch around JSON decode in `_loadDraft`).

---

### Issue #3 — Splash Screen Navigation Reconstruction
**Commit**: `4f78cc2`
**File**: `frontend/lib/screens/splash_screen.dart`

**Problem**: When a student closed the app mid-Assessment (Step 3), the backend stage was still `grades_complete` (assessment not yet submitted). The splash `_reconstructStack` for `grades_complete` routed to `/grades-complete` as the active screen. The student had to manually tap "Continue" to reach Assessment, or was stuck with an infinite submit spinner.

**Solution implemented**:
- `grades_complete` case now pushes `/assessment` as the final (active) screen.
- Full back-stack preserved: `/riasec-quiz` → `/riasec-complete` → `/grades-input` → `/grades-complete` → `/assessment`.
- One-line addition. No other file touched.

---

### Issue #4 — HTTP Client Timeouts (Cold-Start Protection)
**Commit**: (pending below)
**File**: `frontend/lib/services/api_service.dart`

**Problem**: Both `get()` and `post()` used raw `http` calls with no timeout. When the Render free-tier backend sleeps (after 15 min inactivity), it takes ~50 seconds to wake. During that time: splash froze, login spinner ran forever, grades submit hung indefinitely. Users had no feedback and no way out.

**Note on file restriction**: `api_service.dart` was previously in the "do not touch" category. This change was explicitly approved by the user as a targeted, safe, additive-only fix (two lines).

**Solution implemented**:
- Added `import 'dart:async'` (for `TimeoutException`).
- Added `static const Duration _timeout = Duration(seconds: 30)`.
- Appended `.timeout(_timeout)` to both `http.get(...)` and `http.post(...)` calls.
- `TimeoutException` propagates into the existing `catch (_)` blocks in every screen, triggering the already-present "No connection. Check your internet." snackbar and re-enabling the submit button.
- Zero behavior change when the server is awake (responds in <2s, well within 30s window).

---

## Validation
- `flutter analyze` run after each issue: **0 issues found** on all four.
- No backend files modified in any of the four issues.
- All changes conform to the design token system (`_primary: 0xFF006B62`, `_secondary: 0xFF515F74`).

---

## Remaining Issue
- **Issue #5 — Markdown Rendering in Chat**: Integrate `flutter_markdown` in the chat bubble widget so AI responses with bold, headers, and bullet points render correctly instead of showing raw asterisks and hashtags.
