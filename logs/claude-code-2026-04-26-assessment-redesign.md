# claude-code-2026-04-26-assessment-redesign.md
## Session: Assessment Screen Redesign
**Model:** Claude Sonnet 4.6
**Date:** 2026-04-26
**Scope:** frontend/ only

---

## Files Changed

| File | Change |
|---|---|
| `frontend/lib/screens/onboarding/assessment_screen.dart` | Complete replacement |

No other files modified. `/assessment-complete` route was already wired in `main.dart` — no update needed.

---

## Design Decisions Made

| Decision | Justification |
|---|---|
| Answer-first flow (no auto-advance Timer) | Core redesign requirement — students feel anxious with immediate feedback |
| No correct/wrong colours during quiz | Non-negotiable per prompt. Selected = solid teal bg + white text. Unselected = surface-low bg. No red/green at any point before submit. |
| `showModalBottomSheet(isDismissible: false, enableDrag: false)` for results | Non-dismissible by accident; stays in context on assessment screen before navigating away |
| `_ResultsSheet` as a separate `StatelessWidget` | Keeps it stable after parent rebuilds during `setState(() => _isSubmitting = false)` |
| Subject tabs as `ListView.builder(scrollDirection: Axis.horizontal)` rather than `TabBar` | Full control over pill shape, animation, count display. `TabBar` doesn't natively support counts. |
| `_draftKey(token) => 'assessment_draft_${token.hashCode}'` | Compact, user-scoped key without decoding JWT or storing userId separately |
| `_activeSubjectIndex` derived from `_questions[_currentIndex]['subject']` string lookup | Safer than `_currentIndex ~/ 12` — tolerates edge cases in question draw |
| `GestureDetector(onHorizontalDragEnd)` wrapping `Expanded` | Swipe gesture sits above scroll view; vertical scroll still works normally |
| `DraggableScrollableSheet` for question map | Allows student to scroll the 60-question grid on small screens |
| `WidgetsBinding.instance.addPostFrameCallback` for tab auto-scroll | Ensures `ScrollController.hasClients` is true before animating |

---

## State Structure

```dart
List<Map<String,dynamic>> _questions      // 60 drawn questions, grouped by subject
int _currentIndex                          // 0–59
Map<String,int> _answers                   // questionId (String) → selected option index
bool _isSubmitting                         // true during POST /profile/assessment
bool _isGoingForward                       // controls AnimatedSwitcher slide direction
Timer? _draftDebounce                      // 500ms debounce handle
ScrollController _tabScrollController     // auto-scrolls active tab into view
```

---

## Draft Persistence — 5 Risks

| Risk | Mitigation |
|---|---|
| 1. Stale draft survives successful submit | `await _clearDraft()` called at line 311, after status 200, BEFORE showing results overlay |
| 2. Storage exceptions crash the app | Every `_storage.read/write/delete` call is wrapped in `try/catch {}` |
| 3. Draft shared across users on same device | Key: `'assessment_draft_${token.hashCode}'` — unique per user's JWT |
| 4. Rapid answer changes thrash storage | `_scheduleDraftSave()` cancels and restarts a 500ms `Timer` on every answer change |
| 5. Stale draft shown when onboarding_stage moved forward | `_initDraft()` checks `stage != 'grades_complete'`; deletes draft and returns early if not at this step |

---

## API Body Format Confirmed

```dart
final Map<String, List<int>> responses = {};
for (final subject in _subjects) {
  responses[subject] = subjectQs.map((q) {
    final selected = _answers[q['id'] as String];   // String ID from JSON
    return (selected == (q['correct_index'] as int)) ? 1 : 0;  // binary flag
  }).toList();
}
// POST body: {'responses': responses}
```

Order matches presentation order per subject. String IDs confirmed from assessment_questions.json (`"math_matric_001"` etc.). Binary 0/1 flags confirmed.

---

## loadProfile Sequence (Item 15)

```dart
// In _onSubmit() after response.statusCode == 200:
await ref.read(profileProvider.notifier).loadProfile(token);  // 1st
await _clearDraft();                                            // 2nd
if (!mounted) return;
setState(() => _isSubmitting = false);
_showResultsBottomSheet();                                      // 3rd — after profile loaded
```

By the time "View Full Report" is tapped, `capabilityScores` is populated in `profileProvider`.

---

## Physical Device Test

**Status: NOT RUN this session.**

User explicitly requested commit without device test. The `flutter analyze` gate passed (0 errors, full project). Visual correctness and swipe gesture behaviour require physical device verification.

**Recommended before demo:** Run on Android device and verify all 10 flows from the prompt (subject tab jumps, draft restore, results overlay, per-subject scores).

---

## flutter analyze

```
No issues found! (ran in 31.7s)
```
Full project clean. Single-file analysis also clean after curly-brace lint fix.

---

## Deviations from Required Behaviour

None. All required behaviours implemented as specified:
- Answer-first flow ✅
- Subject navigation bar with counts ✅
- Question map (bottom sheet with grouped grid) ✅
- Previous/Next navigation ✅
- Submit guard with remaining count ✅
- Draft persistence (all 5 risks) ✅
- Results overlay before /assessment-complete ✅
- API body format ✅
- loadProfile before results (Item 15) ✅
- Minimum 14.sp all text ✅ (fixed 12.sp badge text caught in self-review)
- SnackBar for all errors ✅
