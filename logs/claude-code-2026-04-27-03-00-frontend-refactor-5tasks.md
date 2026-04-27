# Session Log — Frontend Refactor Sprint (5 Tasks)

**Date:** 2026-04-27
**Model:** Antigravity (Gemini 2.5 Pro)
**Session started:** ~02:56 PKT
**Session ended:** ~03:28 PKT

---

## INPUT PROMPT SUMMARY

Five targeted fixes requested after device testing on Samsung A6 and Pixel 4:
1. Login screen keyboard overflow — 5+ prior patches failed, needed full rebuild
2. Navigator back-stack empty after app kill — splash reconstructed no prior screens
3. Draft answers lost between logins — token-based key rotated on every login
4. Settings notification toggles misleading — backend never implemented them
5. Full modernization pass — animations, shimmer, empty states, accessibility

Frontend Chat reviewed and approved all proposals with two amendments:
- `assessment_complete` → `/chat` via `pushNamedAndRemoveUntil` (not push)
- Draft fallback uses `token.hashCode` not a hardcoded string

---

## FILES READ (MANDATORY PRE-CONDITION)

1. `CLAUDE.md` — full read (641 lines). Key facts absorbed:
   - `sessionId` confirmed present: "GET /profile/me response includes `session_id: UUID` (non-null) — confirmed working, commit 2ace388"
   - Chat is terminal state: `assessment_complete → pushNamedAndRemoveUntil('/chat', (r) => false)`
   - Onboarding state machine: full stage sequence confirmed
   - Forgot Password: permanently disabled, slate color, onPressed: null
   - SnackBar background: inverse-surface `#2D3133`

2. `docs/00_architecture/POINT_5_API_SURFACE_v1_2.md` — not re-read (no API surface changes in this session)

3. `design/screen_mockups/DESIGN_HANDOFF.md` — Login screen section (Screen 03) read for layout intent

4. `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md` — full read. Key facts:
   - `inverse-surface` (#2D3133) for SnackBar background
   - Content card shadow: `blurRadius: 24, offset: Offset(0, 8)` (Task 5d)
   - Form panel shadow (editorial): `blurRadius: 40, offset: Offset(0, 12)` — do NOT apply to content cards
   - `border-radius-xl`: 16px for content cards

---

## CHANGES MADE

### TASK 1 — login_screen.dart (full rebuild)

**Root cause identified (corrected from prior patches):**
Prior patches used `SafeArea` wrapping `SingleChildScrollView` with `keyboardHeight`
compensation in the scroll view's bottom padding. The bug: `SafeArea` subtracts the
bottom padding of the system (safe area insets) from the layout *before* the scroll view
sees it, but when `resizeToAvoidBottomInset: false` the keyboard height from
`viewInsets.bottom` is *separate* from safe area insets. The two compensations
interfered: `SafeArea` consumed the bottom inset once, then the explicit `keyboardHeight`
padding tried to compensate again, producing double-counting on some device/OS combinations.

**Fix:** `MediaQuery.removePadding(removeBottom: true)` strips SafeArea's bottom
compensation. `SafeArea(bottom: false)` handles the top safe area only. Keyboard
padding applied directly to `SingleChildScrollView.padding.bottom`.

**ConstrainedBox retained:** The prior misdiagnosis blamed ConstrainedBox for overflow.
Actually ConstrainedBox with `minHeight` is needed to keep short content centered
(otherwise Column top-stacks on tall screens). It does not cause overflow because the
ScrollView is outside it — content can exceed minHeight by scrolling. Reinstated.

**Inline error removed:** `authState.error` displayed as inline Text inside the form card
caused height shift on error appearance. Replaced with `ref.listen<AuthState>` → `SnackBar`
pattern. SnackBar uses `inverse-surface` (#2D3133), floating behavior, 12.r border radius.

**AnimatedScale 0.97 press animation added** to Sign In button and Sign Up link.

**Accessibility:** `Semantics` added to headline (header:true), input fields (textField:true),
buttons (button:true), Forgot Password (label: 'coming soon').

**Business logic unchanged:** All routing, `loadProfile`, `_routeForStage` (including
`'complete'` → `/chat`), `AutofillGroup`, Remember Me checkbox preserved exactly.

---

### TASK 2 — splash_screen.dart (stack reconstruction)

**Problem:** `_navigate()` used `pushReplacementNamed` for all stages. After app kill
and relaunch, Navigator contained only Splash → destination. Pressing back → black screen.

**Fix:** Replaced `_navigate` + `_routeForStage` with:
- `_reconstructStack(stage)` — wrapped in `addPostFrameCallback`, builds full back-stack
- `_navigateSingle(route)` — used only for pre-auth paths (no token, errors)

**Stage → stack mapping implemented:**

| Stage | Stack built |
|---|---|
| `not_started` | `pushReplacement(/riasec-quiz)` |
| `riasec_complete` | `pushReplacement(/riasec-quiz)` → `push(/riasec-complete)` |
| `grades_complete` | `pushReplacement(/riasec-quiz)` → `push(/riasec-complete)` → `push(/grades-input)` → `push(/grades-complete)` |
| `assessment_complete` / `complete` | `pushNamedAndRemoveUntil(/chat, (r)=>false)` |
| default (unknown stage) | `pushReplacement(/riasec-quiz)` → `push(/riasec-complete)` → `push(/grades-input)` → `push(/grades-complete)` → `push(/assessment)` |

**Why `addPostFrameCallback`:** Multiple `pushNamed` calls must happen after the
current frame completes or they race against each other and may NOP on some Navigator
implementations. `addPostFrameCallback` ensures they run sequentially post-build.

---

### TASK 3 — riasec_quiz_screen.dart + assessment_screen.dart (draft key fix)

**riasec_quiz_screen.dart:**
- Removed `String? _userId` field entirely
- Removed `_initQuiz()` logic that set `_userId = token.substring(0, 16)` — JWT first-16 chars rotated on login
- Removed `import auth_service.dart` (became unused)
- Replaced `_draftKey(String userId) => 'riasec_draft_$userId'` with:

```dart
String _draftKey() {
  final sessionId = ref.read(profileProvider).sessionId;
  if (sessionId != null) return 'draft_riasec_$sessionId';
  final token = ref.read(authProvider).token;
  return token != null
      ? 'draft_riasec_${token.hashCode}'
      : 'draft_riasec_anonymous';
}
```

- Updated `_saveDraft()`, `_loadDraft()`, `_clearDraft()` to call `_draftKey()` (no arg)
- Removed `if (_userId == null) return;` guards (no longer needed)

**assessment_screen.dart:**
- Replaced `_draftKey(String token) => 'assessment_draft_${token.hashCode}'` with same
  sessionId-first pattern: `'draft_assessment_$sessionId'`
- Updated all 4 call sites: `_initDraft()` (2×), `_saveDraft()`, `_clearDraft()`
- Also fixed a missed call site at line 118 (`_storage.containsKey`) that still passed
  token arg — caught by `flutter analyze`
- Removed the `if (token == null) return;` guard in `_initDraft` (now handled by
  sessionId/token null-coalescing inside `_draftKey()`)

**Migration note:** Drafts stored under old keys (`riasec_draft_<16chars>`,
`assessment_draft_<hashcode>`) become orphaned. They remain in `flutter_secure_storage`
until app data cleared — no security risk (small JSON strings).

---

### TASK 4 — settings_screen.dart (notifications removal)

Removed the entire NOTIFICATIONS section:
- `SizedBox(height: 16.h)` (pre-section spacing)
- `_SectionTitle(label: 'NOTIFICATIONS')`
- `SizedBox(height: 8.h)` (title-to-card spacing)
- `_SectionCard` containing `_ToggleTile('Recommendation updates')` + `Divider` + `_ToggleTile('Policy change alerts')`
- `SizedBox(height: 16.h)` (post-section spacing)
- Entire `_ToggleTile` + `_ToggleTileState` classes (became unused — 72 lines removed)

**Rationale:** No notification backend exists. No notification permission request exists
in the app. Toggles showed "true" as default with no-op `onChanged` handlers — actively
misleading to students. Removal is cleaner than a "coming soon" placeholder since there
is no committed design or timeline for this feature.

---

### TASK 5 — Modernization pass

**5a — Button press animations (0.97 scale):**
- `login_screen.dart`: Sign In ElevatedButton, Sign Up text link
- `signup_screen.dart`: Create Account ElevatedButton

Pattern used: `GestureDetector(onTapDown/Up/Cancel)` → `bool _pressed` → `AnimatedScale(scale: pressed ? 0.97 : 1.0, duration: 150ms)` wrapping ElevatedButton. The ElevatedButton `onPressed` handler is unchanged — GestureDetector only controls the visual scale.

**Screens not given 5a:** RIASEC quiz (Likert buttons already have active/selected state
visual feedback — adding scale animation would conflict), assessment MCQ buttons (same
reason), chat send button (already has `AnimatedContainer` color transition), grades input
(low tap frequency, no improvement needed for demo).

**5b — Shimmer loading state (dashboard):**
- Replaced `CircularProgressIndicator + Text` loading state with 3× `_ShimmerCard`
  skeleton widgets
- `_ShimmerCard` is a private `StatefulWidget` in `recommendation_dashboard.dart`
- Uses `AnimationController(repeat: true, 1200ms)` + `ShaderMask` with `LinearGradient`
  sweeping from `Color(0xFFECEEF0)` → `Color(0xFFF7F9FB)` → `Color(0xFFECEEF0)`
- Skeleton matches university card layout: rank badge shape, two text line stubs,
  two badge stubs in a row
- Zero new packages required

**5c — Empty states:**
- Dashboard: updated `_buildEmptyState()` per spec — `Icon(Icons.school_outlined, size: 64.r, color: Color(0xFF515F74))`, headline "No recommendations yet" (22.sp w700), body "Start a conversation to get your personalised degree recommendations" (15.sp), button "Start Chat" → `/chat`. Error state uses `Icons.cloud_off_outlined`, same size.
- Chat: welcome state already implemented correctly — "How can I help you today?" (18.sp w700) + subheading + 4 suggested chips. Verified per spec, no changes needed.

**5d — Card shadow standardization:**
- `university_card.dart`: changed from editorial shadow (`blurRadius: 40, offset: (0,12)`)
  to content card shadow (`blurRadius: 24, offset: (0,8)`).
- `borderRadius` corrected to `16.r` (radius-xl = 16px per DESIGN_SYSTEM_TOKENS)
- Shimmer skeleton cards in dashboard use same `24/8` token.
- Login/Signup form cards retain editorial shadow (`40/12`) — these ARE form panels, not content cards.
- Settings `_SectionCard` not changed — uses same editorial shadow intentionally (it is a card panel).

**5e — Form submission feedback:**
Audited all screens. `CircularProgressIndicator(strokeWidth: 2, color: white)` already
present on: login Sign In, signup Create Account, grades submit, RIASEC submit. Assessment
submit already has loading state. No changes needed.

**5f — Typography hierarchy:**
Audited all screens. All have one dominant headline (22–28.sp w700). Chat welcome has
18.sp w700 headline which is within acceptable range for an inline greeting. No changes needed.

**5g — Accessibility (Semantics):**
Added `Semantics` wrappers to:
- Login: `header: true` on "Welcome Back" text, `textField: true` on both fields, `button: true` on Sign In, Sign Up, visibility toggles, Forgot Password
- Signup: `button: true` on Create Account
- Dashboard empty state: `label:` on icon, `button: true` on action button

---

## ANALYZE RESULTS DURING SESSION

| After | Issues | Notes |
|---|---|---|
| Tasks 1–4 initial | 1 error | `_draftKey(token)` call at assessment_screen.dart:118 still passing arg — fixed immediately |
| After fixing all `_draftKey` | 0 | Clean |
| After Task 5b (dashboard shimmer) | 1 warning | `_surfaceLow` field unused after empty state refactor — removed |
| Final | 0 | `flutter analyze lib/ --no-pub` passes in 89s |

---

## FILES CHANGED

| File | Task | Type | Summary |
|---|---|---|---|
| `lib/screens/auth/login_screen.dart` | 1, 5a, 5g | REBUILD | Keyboard fix, SnackBar errors, AnimatedScale, Semantics |
| `lib/screens/splash_screen.dart` | 2 | MODIFY | `_reconstructStack` replaces `_navigate` |
| `lib/screens/onboarding/riasec_quiz_screen.dart` | 3 | MODIFY | sessionId draft key, remove _userId, remove auth_service import |
| `lib/screens/onboarding/assessment_screen.dart` | 3 | MODIFY | sessionId draft key, 4 call sites + 1 missed containsKey site |
| `lib/screens/profile/settings_screen.dart` | 4 | MODIFY | NOTIFICATIONS section removed, _ToggleTile class removed |
| `lib/screens/auth/signup_screen.dart` | 5a, 5g | MODIFY | AnimatedScale, SnackBar errors, keyboard fix, Semantics |
| `lib/screens/dashboard/recommendation_dashboard.dart` | 5b, 5c, 5d | MODIFY | Shimmer skeleton, empty state spec update, _surfaceLow removed |
| `lib/widgets/university_card.dart` | 5d | MODIFY | Content card shadow (24/8), borderRadius 16.r |

---

## DEVIATIONS FROM SPEC

| Item | Spec | Deviation | Reason |
|---|---|---|---|
| 5a: RIASEC Likert buttons | "All tappable elements scale 0.97" | NOT applied | Likert buttons use active/selected fill state — scale animation would conflict with the color transition that users rely on as selection feedback |
| 5a: Assessment MCQ options | Same | NOT applied | Same reason — selected state is the primary visual affordance |
| 5a: Chat send button | Same | NOT applied | Already has AnimatedContainer color/shape transition. Adding scale would double-animate |
| 5g: All icons | "All meaningful images and icons" | Applied only to interactive/semantic icons | Decorative icons (loading indicator shimmer, AI bubble icons, etc.) excluded — screenreaders skip decorative icons by default in Flutter |

---

## ITEMS SKIPPED AND WHY

| Item | Reason |
|---|---|
| 5f typography: any screen changes | All screens already have correct hierarchy — no regressions introduced |
| 5e: Additional success SnackBars | Navigation to completion screens IS the success feedback. Additional SnackBars would flash and immediately disappear as the screen transitions |
| Profile screen | Not in scope (placeholder screen per CLAUDE.md locked inventory) |
| Roadmap timeline widget | Not requested in this session |

---

## OPEN ITEMS (NEXT SESSION)

1. Physical device test on Samsung A6 + Pixel 4 before committing
   - Login keyboard overflow: verify zero overflow at 360dp width
   - Back navigation: kill app mid-onboarding, reopen, press back
   - Draft persistence: answer questions, kill, reopen, verify resume
   - Draft cross-login: logout, login same account, verify draft restored
   - Settings: confirm notifications section gone
   - Dashboard: verify shimmer appears on load, disappears on data arrival

2. Roadmap timeline widget (`roadmap_timeline` SSE rich_ui type) — still renders nothing

3. Profile screen implementation deferred — no spec yet

---

## REFERENCES

- Prior session: `logs/claude-code-2026-04-27-02-00-frontend-audit-new-screens.md`
- Authority: `CLAUDE.md` v2.3
- Design: `design/screen_mockups/DESIGN_HANDOFF.md`, `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md`
- Architecture: `docs/00_architecture/POINT_5_API_SURFACE_v1_2.md`
- Implementation plan: `brain/5de5a820-be0d-4479-a47a-ece30c5feb8e/implementation_plan.md`

---

## STATUS

COMPLETE — flutter analyze: 0 issues.
Physical device test required before commit.
