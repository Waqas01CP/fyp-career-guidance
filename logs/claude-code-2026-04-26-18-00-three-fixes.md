# claude-code-2026-04-26-18-00-three-fixes.md
## Session: Three targeted fixes — keyboard, draft shuffle, PopScope
### Date: 2026-04-26 | Model: Sonnet 4.6

---

## INPUT PROMPT SUMMARY

Three fixes confirmed by Frontend Chat after device testing:
1. Login/Signup: ConstrainedBox causing overflow issues — remove it
2. Assessment draft: shuffle after loading breaks index on restore — check before shuffle
3. Assessment: PopScope blocking Navigator.pop() back to Grades Complete — remove it

---

## FILES READ

1. logs/README.md
2. CLAUDE.md (via system context)
3. frontend/lib/screens/auth/login_screen.dart
4. frontend/lib/screens/auth/signup_screen.dart
5. frontend/lib/screens/onboarding/assessment_screen.dart

---

## CHANGES MADE

### FIX 1 — Remove ConstrainedBox from login and signup

**login_screen.dart** and **signup_screen.dart**:
- Removed `ConstrainedBox(constraints: BoxConstraints(minHeight: constraints.maxHeight))`
- SingleChildScrollView now wraps Padding directly
- All Column children preserved exactly as before

Root cause: ConstrainedBox with minHeight=constraints.maxHeight forces the scrollable
content to take at least the full screen height. When combined with keyboard-aware
Padding.bottom, total height exceeds viewport → overflow. Removing it lets
SingleChildScrollView size to content naturally.

### FIX 2 — Draft-aware question order in assessment

**assessment_screen.dart** — `_loadAssessment()` replaced:

Old: shuffled question pool unconditionally before checking for draft.
New: checks `_storage.containsKey(key: _draftKey(token))` BEFORE shuffling.

When `hasDraft == true`:
- Pool NOT shuffled — questions drawn in stable, deterministic order
- `_initDraft()` then restores `_currentIndex` from draft
- The index correctly points to the same question because order is identical

When `hasDraft == false`:
- Pool shuffled as before — fresh session, random order

Draft key: `'assessment_draft_${token.hashCode}'`
Storage API: `FlutterSecureStorage.containsKey(key:)` returns `Future<bool>`

### FIX 3 — Remove PopScope from assessment build()

**assessment_screen.dart** — `build()` method:
- Removed `PopScope(canPop: false, onPopInvokedWithResult: ..., child: Scaffold(...))`
- `Scaffold` is now the direct return value of `build()`
- Also removed the orphaned closing `)` that belonged to `child: Scaffold(...)` in PopScope

Why this works now:
- Assessment is navigated to via `pushNamed` (from previous session's nav fix)
- AppBar `leading` IconButton calls `_onBackPressed()` which shows dialog, then `Navigator.pop(context)`
- Without PopScope blocking it, `Navigator.pop()` correctly goes back to Grades Complete
- System hardware back button also now works naturally (no PopScope intercepting it)
- `_onBackPressed()` itself was NOT changed — dialog logic is correct

---

## CLOSING PAREN CLEANUP

After removing PopScope, the old `child: Scaffold(...)` trailing `),` became orphaned.
The sequence around the end of build() before fix:

```
            ],         // closes Column children
          ),           // closes Column
        ),             // closes SafeArea
      ),               // ORPHANED — was closing child: Scaffold(...) in PopScope
    );                 // was closing return PopScope(...), now correctly closes return Scaffold(...)
```

Removed the orphaned `      ),` at 6-space indent.
After fix: `],` → `),` Column → `),` SafeArea → `);` end of return Scaffold.

---

## flutter analyze OUTPUT

```
Analyzing frontend...
No issues found! (ran in 5.6s)
```

---

## DEVICE TEST RESULTS

Physical device test required before committing.

Expected outcomes:
1. Login: tap email, keyboard appears — no overflow, no yellow stripes, content scrollable
2. Signup: same — no overflow when keyboard appears
3. Assessment draft: answer 10 questions, close app, reopen — resume at correct question
4. Assessment back button: tapping AppBar back → dialog → Leave → Grades Complete (not black screen)
5. System hardware back on assessment: goes to Grades Complete (PopScope no longer blocking)

---

## STATUS

NOT COMMITTED — physical device test required before commit.
