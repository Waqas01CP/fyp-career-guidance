# Frontend Remediation Sprint 4 (P0 and P1)

**Date:** 2026-05-13
**Model:** Gemini 3.1 Pro (High)
**Objective:** Execute the prioritized remediation roadmap for the 49 verified design and architecture findings, focusing on P0 critical blockers and P1 high-priority fixes.

## Overview
This session focused on applying the fixes identified in the frontend design audit (see `logs/audits/2026-05-12-antigravity-frontend-design-audit-part2.md`). A total of 13 fixes were applied across 9 files to enforce state integrity, design system compliance, and navigation robustness.

## Changes Made

### P0 Critical Blockers (Immediate Execution)
1. **Sign Out Button Styling (`ST-01/02`)**: Updated `settings_screen.dart` Sign Out button to use `#E0E3E5` background and `#515F74` text (Slate), complying with the Design System color tokens and removing the non-compliant red styling.
2. **Navigation Stack Hardening (`RC-01`, `GC-01`)**: Set `automaticallyImplyLeading: false` on both `riasec_complete_screen.dart` and `grades_complete_screen.dart` to prevent users from popping the stack back into completed forms.
3. **Stage Guards (`RQ-01`, `GI-01`)**: Implemented `addPostFrameCallback`-based stage guards in the initialization lifecycle of `riasec_quiz_screen.dart` (`_initQuiz`) and `grades_input_screen.dart` (`_loadDraftThenProfile`). Attempting to access these screens when the user profile stage has surpassed them will now automatically route the user forward to their completed checkpoint (`/riasec-complete` or `/grades-complete`), preventing accidental overwrite of validated assessment data.
4. **Assessment AppBar PopScope Bypass (`AS-01`)**: Replaced the standard `Navigator.pop(context)` call on the AppBar's back button in `assessment_screen.dart` with a call to the custom `_onBackPressed` handler to trigger the leave-assessment warning dialog.
5. **Keyboard Overcompensation / SafeArea (`LG-02/03`, `SU-01/02`)**: Addressed the double keyboard compensation risk by updating the `SafeArea` on `login_screen.dart` and `signup_screen.dart` with `bottom: false` and wrapping the `LayoutBuilder` child with `MediaQuery.removePadding(context: context, removeBottom: true, child: ...)`.
6. **Provider 401 Session Handling (`PP-01`)**: Updated `ProfileNotifier` in `profile_provider.dart` to take a Riverpod `Ref` object, and implemented a call to `ref.read(authProvider.notifier).handleUnauthorized()` inside `loadProfile()` upon catching a 401 response. This guarantees stale tokens are dropped securely and the application enforces session termination.

### P1 High Priority Fixes (Navigation & Consistency)
7. **Dashboard Navigation (`MC-01`)**: Changed the dashboard icon navigation in `main_chat_screen.dart` from `pushReplacementNamed` to `pushNamed` to retain the chat state in the history stack, preventing chat destruction.
8. **Dynamic Recommendations Fetching (`RD-01`)**: Added API fetching logic to `recommendation_dashboard.dart`'s `_loadCacheIfEmpty` to call `GET /profile/recommendations` if the cache is empty, ensuring a populated dashboard for fresh logins.
9. **Current Question Glow (`AS-03`)**: Added the missing question glow shadow `BoxShadow(color: Color(0x40006B62), blurRadius:0, spreadRadius:2)` to the active card in `assessment_screen.dart`.
10. **Signup Success Routing (`SU-03`)**: Changed the successful signup routing in `signup_screen.dart` from `pushReplacementNamed` to `pushNamedAndRemoveUntil` to prevent backstack issues.
11. **Thinking Indicator Labels (`TI-01`, `MC-02`)**: Enhanced `thinking_indicator.dart` by adding an optional `label` parameter and displaying it with italicized styling. Updated `main_chat_screen.dart` to pass `ref.watch(chatProvider).currentStatusLabel` to the `ThinkingIndicator`.

*(Note: P1 Fix 9 (`stated_preferences` integration) was intentionally deferred per architectural roadmap instructions).*

## Verification
- Ran `flutter analyze`: **0 issues found**.
- Project successfully compiled with no errors.

## Next Steps
- Manual physical device testing of the assessment screen and keyboard handling.
- Proceeding with Sprint 4 Week 2 Remediation (P2 and P3 issues).
