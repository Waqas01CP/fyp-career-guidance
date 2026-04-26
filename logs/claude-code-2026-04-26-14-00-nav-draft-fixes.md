# Session: nav-draft-fixes
**Date:** 2026-04-26 14:00
**Model:** Claude Sonnet 4.6
**Scope:** 4 navigation/draft fixes across 4 onboarding screens

---

## Files Read
1. logs/README.md
2. CLAUDE.md (via system context)
3. frontend/lib/screens/onboarding/riasec_quiz_screen.dart
4. frontend/lib/screens/onboarding/riasec_complete_screen.dart
5. frontend/lib/screens/onboarding/grades_complete_screen.dart
6. frontend/lib/screens/onboarding/assessment_screen.dart
7. frontend/lib/providers/profile_provider.dart
8. frontend/lib/providers/auth_provider.dart

---

## Fix 1 — Back buttons removed from RIASEC Complete and Grades Complete

**riasec_complete_screen.dart:**
- Removed `leading: IconButton(...)` from AppBar
- Added `automaticallyImplyLeading: false` to prevent Flutter auto-inserting back button
- Reason: screen uses pushReplacementNamed; quiz screen has stage guard that routes forward on re-entry — back navigation creates a confusing redirect loop

**grades_complete_screen.dart:**
- Same: removed `leading: IconButton(...)`, added `automaticallyImplyLeading: false`
- AppBar title 'Academic Profile' preserved
- Reason: same as above

**assessment_complete_screen.dart:** NOT touched per task instructions. Back button kept.

---

## Fix 2 — Black screen fix on RIASEC quiz Leave

**riasec_quiz_screen.dart — `_onBackPressed()`:**

Before:
```dart
if (confirmed == true && mounted) {
  Navigator.pushNamedAndRemoveUntil(
      context, '/login', (route) => false);
}
```

After:
```dart
if (confirmed == true && mounted) {
  WidgetsBinding.instance.addPostFrameCallback((_) {
    Navigator.of(context, rootNavigator: true)
        .pushNamedAndRemoveUntil('/login', (route) => false);
  });
}
```

Two changes:
1. `addPostFrameCallback` — defers navigation until after current frame completes, preventing black screen from inconsistent widget tree state during PopScope dialog dismissal
2. `rootNavigator: true` — navigates from root navigator, avoiding nested navigator scope issues

---

## Fix 3 — Assessment draft not restoring on reopen

**assessment_screen.dart — `_initDraft()` rewritten:**

Old behavior:
- Checked `onboardingStage` immediately from `profileProvider`
- Guarded with `if (stage != 'grades_complete')` — this deleted the draft for ANY stage that wasn't exactly 'grades_complete', including 'not_started' (the default before profile loads from backend)
- Result: on cold app start where profile hadn't loaded yet, draft was deleted

New behavior:
- Checks `profile.onboardingStage.isEmpty` to detect unloaded profile and loads it if needed
- Only clears draft (and navigates forward) when `stage == 'assessment_complete'` (already submitted)
- For all pre-assessment stages, attempts to restore draft
- Added corrupt-draft recovery: catches decode errors, deletes corrupt draft, starts fresh

**Note on profile.onboardingStage.isEmpty vs profile.isLoaded:**
The task correction stated that `profile.isLoaded` does not exist in ProfileState. However, `isLoaded` IS present in ProfileState (line 13) and defaults to `false`. The user correction was applied as instructed (`profile.onboardingStage.isEmpty`). Since the default `onboardingStage` is `'not_started'` (not an empty string), the `isEmpty` guard will never trigger a profile reload in practice. The real fix is the removal of the strict `!= 'grades_complete'` guard — the draft now survives any non-`assessment_complete` stage. Post-demo improvement: use `!profile.isLoaded` for the explicit guard since that field exists and correctly signals unloaded state.

---

## Fix 4 — Draft key limitation documented (no code change)

Draft key uses `token.hashCode` — tied to login session. If user logs out and back in, draft is lost even on same account. Post-demo improvement: use user_id from profileProvider as the key instead of token.hashCode.

---

## flutter analyze

```
No issues found! (ran in 73.3s)
```

---

## Physical Device Test

**STATUS: PENDING — DEVICE UNAVAILABLE**

`flutter devices` shows: Windows (desktop), Chrome (web), Edge (web).
No Android physical device connected. Session stopped here per HARD RULES.

Test checklist (to be run after device connection):

**Test 1 — RIASEC Complete no back button:**
Navigate RIASEC quiz → submit → RIASEC Complete. Confirm no back button visible.

**Test 2 — Grades Complete no back button:**
Navigate grades input → submit → Grades Complete. Confirm no back button visible.

**Test 3 — Assessment Complete back button works:**
Navigate assessment → submit → Assessment Complete. Confirm back button visible, tapping goes back to assessment screen.

**Test 4 — RIASEC quiz Leave → no black screen:**
Start RIASEC quiz, press system back, tap "Leave". Confirm no black screen, app lands on Login screen cleanly.

**Test 5 — Assessment draft restores:**
Start assessment, answer 15 questions across subjects. Close app (swipe away from recents). Reopen, log in. Confirm assessment resumes at Q15 with answers visible in question grid.

**Test 6 — No regression on forward navigation:**
Complete full flow: RIASEC → Grades → Assessment → results overlay → View Full Report → Assessment Complete → Continue → Chat placeholder. Confirm each screen transitions correctly.

---

## Commit Status: NOT COMMITTED — awaiting physical device test
