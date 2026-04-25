# Quiz Progress Persistence — Architecture Decision
## FYP: AI-Assisted Academic Career Guidance System
## Recorded: April 2026
## Issue: RIASEC quiz progress lost when app closes mid-quiz

---

## Problem Statement

When a student closes the app at Q33 and reopens it, they restart
from Q1 with all previous answers lost. This is because `_answers`
(Map of question_id → score) and `_currentIndex` live only in
Flutter widget state — they vanish when the app closes or is
backgrounded by the OS.

---

## Options Considered

### Option A — Local Storage (flutter_secure_storage)
Save `_answers` and `_currentIndex` as JSON in flutter_secure_storage
after every answer. On quiz screen init, check if a draft exists
for the current user and restore it.

Pros:
- No backend changes required
- No new packages (flutter_secure_storage already in pubspec)
- Works offline
- One frontend session to implement

Cons:
- Device-specific — if student switches phones, draft is lost
- Must be carefully cleared after successful submission

### Option B — Backend Draft Endpoint
Add POST /api/v1/profile/quiz/draft and GET equivalent.
Store partial answers in a new quiz_drafts DB table in Supabase.

Pros:
- Device-independent — student can switch phones and resume
- Persistent across reinstalls

Cons:
- New backend endpoint required
- New DB table and Alembic migration required
- Adds latency — every answer triggers a network call
- Requires Backend Chat involvement and a separate backend session
- Disproportionate engineering effort for the use case

### Option C — LangGraph Checkpoint
Not applicable. AsyncPostgresSaver saves chat conversation state
only — RIASEC quiz answers are a separate system with no connection
to LangGraph state.

---

## Decision: Option A Selected

Rationale:
- Target users are secondary school students in Karachi on a single
  device. Phone-switching mid-quiz is not a realistic scenario.
- The primary failure mode being solved is accidental app close,
  OS killing the app in the background, or phone running out of
  battery — all same-device scenarios that Option A handles fully.
- flutter_secure_storage is already in pubspec.yaml — zero new
  dependencies.
- Option B adds 3-4x the implementation complexity (backend
  endpoint, DB migration, network calls per answer) for a benefit
  that does not match the actual user behaviour of the target
  demographic.
- One frontend session vs multiple backend + frontend sessions.

---

## Implementation — Option A Details

### Storage key format
`riasec_draft_{userId}` — keyed by user ID to prevent
cross-user draft contamination on shared devices.

### Data stored
```json
{
  "currentIndex": 33,
  "answers": {
    "1": 4, "2": 3, "3": 5, ...
  }
}
```

### Known Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Draft not cleared after submission | Student resubmits old quiz | Call _clearDraft() after 200 response in _onSubmit() |
| Corrupted JSON in storage | App crash on restore | try/catch around jsonDecode, fallback to fresh start |
| Draft from different user | Wrong user sees wrong draft | Key draft by userId: riasec_draft_{userId} |
| Storage write performance on low-end devices | Sluggish feel per tap | Debounce writes 500ms after last answer using Timer |
| Draft exists but quiz already submitted | Student re-enters completed quiz | Check onboardingStage on init — if riasec_complete or beyond, clear draft and navigate forward |

### Files Modified
- frontend/lib/screens/onboarding/riasec_quiz_screen.dart only
- No backend changes
- No new packages

---

## Future Switch to Option B

If Option B becomes necessary (e.g. multi-device usage becomes
common, or a school lab scenario where students share devices),
the switch requires:
1. New backend endpoint: POST /api/v1/profile/quiz/draft
2. New backend endpoint: GET /api/v1/profile/quiz/draft
3. New DB table: quiz_drafts (user_id, answers_json, current_index, updated_at)
4. New Alembic migration
5. Update riasec_quiz_screen.dart to call backend instead of
   local storage
6. Remove flutter_secure_storage draft logic

Option A code is fully replaceable — the save/load/clear draft
interface stays the same, only the storage backend changes.