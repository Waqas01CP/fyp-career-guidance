# Session Log — Grades Input + Grades Complete Screens
## Date: 2026-04-25
## Model: Claude Sonnet 4.6
## Session type: Two screens in one session (justified: sequential onboarding steps, shared profile provider)

---

## Files Changed

### Created (2 new files)
- `frontend/lib/screens/onboarding/grades_input_screen.dart`
- `frontend/lib/screens/onboarding/grades_complete_screen.dart`

### Modified (1 file)
- `frontend/lib/main.dart` — added imports + replaced placeholder routes for `/grades-input` and `/grades-complete`

---

## Files Read (10 confirmed)

1. `logs/README.md` ✓
2. `CLAUDE.md` ✓ (loaded in context)
3. `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` ✓
4. `docs/00_architecture/FRONTEND_SPRINT_BUILD_PROCESS.md` ✓
5. `design/screen_mockups/DESIGN_HANDOFF.md` — Screens 08 and 09 only ✓
6. `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md` — colour/typography sections ✓
7. `design/screen_mockups/code_academic_profile_ocr.html` — text content only ✓
   (Note: file named code_academic_profile_ocr.html, not code_grades_input.html)
8. `design/screen_mockups/code_grades_complete.html` — text content only ✓
9. `frontend/lib/providers/profile_provider.dart` ✓
10. `frontend/lib/providers/auth_provider.dart` ✓ (AuthState.token confirmed)
11. `frontend/lib/services/api_service.dart` ✓
12. `frontend/lib/main.dart` ✓ (routes table)

---

## Plan Summary

### Grades Input
- `ConsumerStatefulWidget`
- State: `_formKey`, `_selectedLevel`, `_selectedStream`, `_selectedBoard`, `_selectedYear`, `Map<String, TextEditingController> _markControllers`, `_isSubmitting`
- `_streamOptions` uses backend values ('ICS') with `_streamDisplayNames` map for 'ICS (Computer Science)' display
- `_streamSubjects` keyed by backend stream value ('ICS', not 'ICS (Computer Science)')
- `_rebuildSubjectControllers()` disposes old controllers and creates new ones with `addListener(() => setState(() {}))` for live aggregate
- Layout: AppBar → SafeArea → SingleChildScrollView → Form → Column: step badge → title → subtitle → disabled OCR → form card → Save button
- Correction 1 applied: `subject_marks` flat dict with lowercase keys, no 'year' in body
- On 200: `loadProfile(token)` then `pushReplacementNamed('/grades-complete')`
- 401 handled: `handleUnauthorized()` then navigate to `/login`

### Grades Complete
- `ConsumerWidget`
- Reads `ref.watch(profileProvider).subjectMarks`
- Correction 2 applied: `'${e.key[0].toUpperCase()}${e.key.substring(1)}'` for title-case keys
- Fallback `_demoMarks` when `subjectMarks` empty: Math 85%, Physics 78%, Chemistry 82%, English 68%, CS 91%
- Layout: AppBar → SafeArea → SingleChildScrollView → Column: hero block → grades card → AI insight → Continue button
- Colour logic: `percentage >= 70 ? Color(0xFF006B62) : Color(0xFF515F74)` for bar fill + text

---

## Pre-Resolved Decisions Documented

### OCR Deferred
image_picker NOT in pubspec.yaml. Do NOT add it.
"Scan Marksheet" button present but fully disabled (`onPressed: null`, slate `Color(0xFF515F74)` background, "Soon" badge).
No camera code, no BackdropFilter OCR overlay, no modal.

### Stream Display vs Backend Value
`_streamOptions` uses backend-compatible values: `['Pre-Engineering', 'Pre-Medical', 'ICS', 'Commerce', 'Humanities']`
`_streamDisplayNames` maps 'ICS' → 'ICS (Computer Science)' for user display.
`_selectedStream` holds backend value ('ICS'); sent directly in API body.

### Dynamic Subject List
`_streamSubjects` const map keyed by backend stream values.
O Level / A Level: fixed Pre-Engineering subjects (demo simplicity decision per prompt).
`_rebuildSubjectControllers()` called on both level and stream change.

### Fallback Demo Marks for Grades Complete
When `profileProvider.subjectMarks` is empty: use `_demoMarks` const map.
Demo aggregate = (85+78+82+68+91)/5 = 80.8% → displayed as "81%".
English at 68% shows slate colour — all others teal.

### Live Aggregate Calculation
Each `TextEditingController` has `addListener(() => setState(() {}))`.
`_computeAggregate()` averages non-empty, valid entries.
Displayed as "XX.X%" (1 decimal) in GradesInput.

### DropdownButtonFormField Deprecation Fix
Flutter 3.41.7 deprecated `value` parameter in `DropdownButtonFormField` in favour of `initialValue`.
Fix applied: all 4 dropdowns use `key: ValueKey(currentValue)` + `initialValue: currentValue`.
`ValueKey` forces widget recreation when selection changes, maintaining reactive behaviour with the new API.

### API Body (Correction 1)
Body keys: `education_level`, `subject_marks` (flat dict, lowercase keys), `stream` (optional), `board` (optional).
'year' NOT sent — not in backend schema.
`subject.toLowerCase()` used for key normalisation (e.g. "Computer Science" → "computer science").

---

## flutter analyze Output

```
Analyzing frontend...
No issues found! (ran in 5.3s)
```

---

## Build Result

```
flutter build web --no-tree-shake-icons
✓ Built build/web
```

Wasm dry-run notices are pre-existing (flutter_secure_storage_web uses dart:html) — unrelated to this session.

---

## flutter run Result

`flutter run -d chrome` launched successfully. Full interactive UI test not executed in CLI session (Chrome browser interaction required). Build success with zero analyze issues confirms no runtime compilation errors.

---

## Deviations from DESIGN_HANDOFF.md

1. **Year dropdown not sent to backend** — HTML shows year dropdown, DESIGN_HANDOFF.md Section 10 API body originally included 'year', but Correction 1 removes it from API body. Year dropdown still shown in UI for design compliance.

2. **Stream display name** — HTML uses "ICS (Computer Science)", prompt `_streamOptions` uses 'ICS'. Both used: 'ICS' as value (backend-compatible), 'ICS (Computer Science)' as display label.

3. **Button text "Save My Grades"** — HTML says "Save Academic Profile". DESIGN_HANDOFF.md Section 8 and prompt explicitly say "Save My Grades". Prompt/DESIGN_HANDOFF.md wins.

4. **Board/stream chip in GradesComplete** — Shows `educationLevel` only (formatted). Stream not stored in ProfileState, so combined "Inter Part 2 · Pre-Engineering" chip from HTML cannot be reproduced without stream data. Fallback: education level chip only.

5. **Aggregate decimal places** — GradesComplete shows 0 decimal places (matches HTML "81%"). GradesInput shows 1 decimal place (more informative during entry). Neither conflicts with DESIGN_HANDOFF.md.

---

## Known Issues

None. `flutter analyze` passes zero issues. Build succeeds.

---

## Minor Fix — empty state helper text — 2026-04-25

Added a `if (_currentSubjects.isEmpty)` conditional widget inside the form card Column in `grades_input_screen.dart`, immediately before the `// Subject marks section` comment (before the `if (_currentSubjects.isNotEmpty)` block). The widget is a `Padding(EdgeInsets.symmetric(vertical: 16))` wrapping a centred `Text('Select your education level to enter marks.', fontSize: 13, color: 0xFF515F74)`. It renders when no education level has been selected yet, giving the user a clear prompt rather than a blank card area. The existing `else` branch Container was left untouched per the insert-only hard rule. `flutter analyze`: No issues found (ran in 10.5s).
