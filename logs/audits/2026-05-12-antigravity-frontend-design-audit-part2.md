# Frontend Design & Screen Contract Audit — Part 2: Global Findings, Providers & Remediation
**Project:** FYP AI-Assisted Academic Career Guidance System  
**Auditor:** Antigravity (Claude Sonnet 4.6)  
**Date:** 2026-05-12  
**Companion:** Part 1 — `2026-05-12-antigravity-frontend-design-audit-part1.md`

---

## PROVIDER AUDIT

### `auth_provider.dart` (107 lines)

| ID | Sev | Cat | Finding |
|---|---|---|---|
| AP-01 | P1 | [QUA] | `login()` catches all exceptions with `catch (_)` — conflates network timeout, DNS failure, and unexpected errors into one message. Cannot distinguish for better UX |
| AP-02 | P1 | [CTR] | `handleUnauthorized()` calls `AuthService.logout()` fire-and-forget — token deletion could silently fail. Stale token may persist if secure storage throws |
| AP-03 | ✓ | [CTR] | `_restoreToken()` correctly restores token on construction without loading profile. Splash loads profile separately — **PASS** |
| AP-04 | ✓ | [CTR] | CLAUDE.md L602: "401 always clears stored token and shows session expired." `logout()` clears token correctly — **PASS** |

### `profile_provider.dart` (126 lines)

| ID | Sev | Cat | Finding |
|---|---|---|---|
| PP-01 | **P0** | [CTR] | `loadProfile()` on 401 sets `error: 'session_expired'` and clears `sessionId` — but does NOT call `authNotifier.logout()`. `authProvider.token` remains non-null. `authProvider.isAuthenticated` stays `true`. Potential stale token after session expiry via profile endpoint |
| PP-02 | P2 | [QUA] | `ProfileState` has no fields for preferences data (`budget_per_semester`, `transport_willing`, `home_zone`, `career_goal`). After `POST /profile/preferences` → `loadProfile()`, if `/profile/me` returns these fields they are silently discarded |
| PP-03 | P2 | [QUA] | `updateOnboardingStage()` updates stage locally without server re-fetch — risks stage mismatch if backend call fails after local update |
| PP-04 | ✓ | [QUA] | `copyWith` pattern with boolean clear flags (`clearToken`, `clearError`, `clearSessionId`) — correct immutable state pattern — **PASS** |

### `chat_provider.dart` (153 lines)

| ID | Sev | Cat | Finding |
|---|---|---|---|
| CP-01 | P2 | [CTR] | 5 of 6 SSE status label strings deviate from contract §13 exact wording (see table below) |
| CP-02 | ✓ | [CTR] | `roadmapTimeline` stored but not rendered — **PASS** per "render nothing until sprint 4" |
| CP-03 | ✓ | [QUA] | `addRecommendation()` logs parse failures via `debugPrint` in debug builds — good practice — **PASS** |
| CP-04 | ✓ | [QUA] | `reset()` called on logout — chat history cleared correctly — **PASS** |

**SSE label string deviations (CP-01):**

| Status key | Contract exact string | Code actual string |
|---|---|---|
| `profiling` | `"Understanding your profile..."` | `'Analysing your profile...'` |
| `filtering_degrees` | `"Checking your eligibility..."` | `'Checking your eligibility...'` ✓ |
| `scoring_degrees` | `"Ranking your matches..."` | `'Ranking your options...'` |
| `generating_explanation` | `"Writing your recommendations..."` | `'Preparing your recommendations...'` |
| `fetching_fees` | `"Checking fee details..."` | `'Looking up fees...'` |
| `fetching_market_data` | `"Checking job market..."` | `'Checking market data...'` |

---

## GLOBAL PATTERN VIOLATIONS

### GLB-01 — Systematic Button Border Radius (P1)

DS §10 specifies `BorderRadius.circular(12.r)` for all primary action buttons.  
**6 screens use `16.r`:** riasec_complete, grades_complete, grades_input, preferences, error, settings.  
Login uses `14.r`. Assessment complete's auto-nav has no button.  
**Fix:** Search-replace or add `ThemeData.elevatedButtonTheme` with `12.r` globally.

### GLB-02 — Shadow Token Misuse (P1)

DS defines two shadow tokens:
- **Editorial/Form** (for form cards): `Color(0x0F334155)`, blur 40, offset (0,12)
- **Content Card**: `Color(0x0F191C1E)`, blur 24, offset (0,8)

Several screens use editorial shadow on content cards or use non-spec values.  
Carousel `_BentoCell`, Profile `RetakeCard`, Settings cards all use non-spec shadow.

### GLB-03 — Purple on Human UI Elements (P2)

DS §12: Purple (`0xFF6616D7`) = AI-generated content only.  
**Violations found:**
- RIASEC Quiz: Likert selected state (human answer selection)
- RIASEC Complete: Top-3 pills (human RIASEC result display)
- Assessment Complete: Pulsing icon + `auto_awesome` icon (human milestone)
- Student Profile: Avatar icon

### GLB-04 — SafeArea / Keyboard Handling (P0)

Both Login and Signup missing `SafeArea(bottom: false)` and `MediaQuery.removePadding(removeBottom: true)`.  
Both correctly set `resizeToAvoidBottomInset: false` and `viewInsets.bottom` in scroll padding.  
The two missing items risk double keyboard compensation on Android devices with navigation gesture bar.

### GLB-05 — ScreenUtil Scaling Inconsistency (P3)

CLAUDE.md L631: "No hardcoded pixel values permitted anywhere."  
**Violations found:**
- Carousel dot widths: `28.0` and `6.0` (not `.w`)
- Signup form card: `Radius.circular(32)` (not `32.r`)
- RIASEC Complete: radar vertex label `fontSize: 10` (not `.sp`)

---

## SKILL FILE FINDINGS

### From flutter-build-responsive-layout/SKILL.md

| Check | Skill requirement | App status |
|---|---|---|
| `MediaQuery.sizeOf` vs `.size` | Use `sizeOf` | No violations — app uses `MediaQuery.of(context)` for `viewInsets` only |
| `LayoutBuilder` for parent constraints | Use `LayoutBuilder` | Login + Signup both use `LayoutBuilder` correctly for compact mode |
| No orientation locks | Don't lock | No orientation locking found |
| `ListView.builder` for unknown-length lists | Use builder | All chat message lists and shimmer lists use builder |
| `Expanded`/`Flexible` in rows/columns | Correct usage | No violations observed |

### From flutter-apply-architecture-best-practices/SKILL.md

| Check | Skill requirement | App status |
|---|---|---|
| MVVM layering | UI / ViewModel / Data separated | Correct: Screens (View) + Providers (ViewModel) + Services (Data) |
| `ChangeNotifier` / `StateNotifier` | Extend for state | All 3 providers extend `StateNotifier<T>` correctly |
| Immutable state snapshots | `copyWith` pattern | All 3 providers use `copyWith` correctly |
| Services: stateless | No state in services | `ApiService`, `AuthService`, `SseService` all stateless static |
| Repository → Domain Models | Return typed models | `Recommendation.fromJson` is used. `roadmapTimeline` stored as raw `Map<String, dynamic>` — minor deviation |

---

## COMPLETE PRIORITY TABLE (49 findings)

| Priority | ID | Screen/File | Cat | Finding |
|---|---|---|---|---|
| **P0** | ST-01/02 | settings | [COL] | Sign Out: red bg `#FFDAD6` + red text. Spec: `#E0E3E5` / `#515F74` |
| **P0** | RC-01 | riasec_complete | [CTR] | `automaticallyImplyLeading: true` — back button shown, must be false |
| **P0** | GC-01 | grades_complete | [CTR] | `automaticallyImplyLeading: true` — back button shown, must be false |
| **P0** | RQ-01 | riasec_quiz | [CTR] | NO stage guard — user can overwrite submitted quiz scores |
| **P0** | GI-01 | grades_input | [CTR] | NO stage guard — user can overwrite submitted grades |
| **P0** | AS-01 | assessment | [NAV] | AppBar back button bypasses PopScope — no confirmation dialog |
| **P0** | LG-02/03 | login | [GLB] | `SafeArea(bottom:false)` + `removePadding` missing |
| **P0** | SU-01/02 | signup | [GLB] | `SafeArea(bottom:false)` + `removePadding` missing |
| **P0** | PP-01 | profile_provider | [CTR] | 401 on loadProfile does not clear authProvider token |
| **P1** | PR-01 | preferences | [CTR] | `stated_preferences` absent from POST payload and UI |
| **P1** | CH-01 | main_chat | [NAV] | Dashboard nav: `pushReplacementNamed` should be `pushNamed` |
| **P1** | RD-01 | dashboard | [CTR] | Reads cache only — must call `GET /profile/recommendations` |
| **P1** | AS-03 | assessment | [CTR] | Current question glow `BoxShadow(0x40006B62, blur:0, spread:2)` not implemented |
| **P1** | SU-05 | signup | [NAV] | ON SUCCESS: `pushReplacementNamed` should be `pushNamedAndRemoveUntil` |
| **P1** | LG-08 | login | [NAV] | ON SUCCESS: no back-stack reconstruction (contrast with Splash) |
| **P1** | CH-09 | main_chat | [CTR] | `ThinkingIndicator` called without `label` parameter |
| **P1** | TI-02 | thinking_indicator | [CTR] | Missing `label` parameter implementation |
| **P1** | GLB-01 | 6 screens | [BOR] | Systematic button radius `16.r` — spec `12.r` |
| **P1** | GLB-02 | 5 screens | [SHA] | Shadow token misuse (editorial on content cards) |
| **P1** | AC-04/05 | assessment_complete | [COL] | Purple used on human milestone screen |
| **P1** | AC-06 | assessment_complete | [GLB] | Badge `Border.all` — DS prohibits 1px solid border |
| **P1** | AP-01 | auth_provider | [QUA] | `login()` conflates all exception types |
| **P2** | RQ-05 | riasec_quiz | [COL] | Purple on Likert selected state (human action) |
| **P2** | RC-04 | riasec_complete | [COL] | Purple on top-3 pills (human result) |
| **P2** | PF-02 | profile | [COL] | Purple avatar icon on identity/human screen |
| **P2** | GLB-03 | 4 screens | [COL] | Purple on human UI elements (role violation) |
| **P2** | OC-06 | carousel | [SHA] | `_BentoCell` shadow non-spec |
| **P2** | SU-06 | signup | [BOR] | Form card `Radius.circular(32)` not `32.r` |
| **P2** | GC-04 | grades_complete | [SHA] | Card shadow offset (0,4) — spec (0,8) |
| **P2** | AC-07 | assessment_complete | [SHA] | Subject score card offset (0,4) — spec (0,8) |
| **P2** | CH-04 | main_chat | [BOR] | Input pill `24.r` — form inputs spec `12.r` |
| **P2** | CH-05 | main_chat | [SHA] | AI bubble shadow non-spec |
| **P2** | ST-03 | settings | [BOR] | Sign Out button `16.r` — spec `12.r` |
| **P2** | ST-04 | settings | [SHA] | Card shadow `0x0A334155` blur 12 — spec `0x0F191C1E` blur 24 |
| **P2** | RD-03 | dashboard | [BOR] | Mismatch banner radius not partial (spec: topRight + bottomRight only) |
| **P2** | PF-03 | profile | [SHA] | RetakeCard shadow `0x0A334155` blur 10 — spec `0x0F191C1E` blur 24 |
| **P2** | PF-06 | profile | [QUA] | No user name/email displayed from profileProvider |
| **P2** | GI-06 | grades_input | [QUA] | OCR button visible and tappable — CLAUDE.md says disable/hide |
| **P2** | RC-07 | riasec_complete | [COL] | AI panel left border `width:4` — spec `width:3` |
| **P2** | TI-01/03 | thinking_indicator | [QUA] | `Future.delayed` stagger (spec: AnimationController); dot `8.r` (spec `6.r`) |
| **P2** | PP-02 | profile_provider | [QUA] | ProfileState has no preferences fields |
| **P2** | CP-01 | chat_provider | [CTR] | 5 SSE status label strings deviate from contract |
| **P2** | RD-05 | dashboard | [QUA] | No shared navigation shell between chat and dashboard |
| **P2** | AS-06 | assessment | [BOR] | Bottom sheet `20.r` — DS modals = `24.r` |
| **P3** | OC-03 | carousel | [BOR] | Dot widths `28.0`/`6.0` not `.w` scaled |
| **P3** | GLB-05 | 3 locations | [QUA] | Hardcoded pixel values violating ScreenUtil convention |
| **P3** | AC-08 | assessment_complete | [QUA] | `onEnd: setState((){})` causes continuous rebuilds |
| **P3** | RC-08 | riasec_complete | [QUA] | Radar vertex label `fontSize:10` without `.sp` |
| **P3** | AP-02 | auth_provider | [QUA] | `handleUnauthorized()` fire-and-forget logout |

**Total: 8 × P0 | 14 × P1 | 22 × P2 | 5 × P3 = 49 findings**

---

## REMEDIATION ROADMAP

### Sprint 4 — Before Demo (Fix all P0 + high-impact P1)

**Week 1 — P0 Critical Blockers**

| # | Fix | File | Effort |
|---|---|---|---|
| 1 | Sign Out button: change bg to `#E0E3E5`, text to `#515F74` | settings_screen.dart L194–195 | 5 min |
| 2 | `automaticallyImplyLeading: false` on RIASEC Complete | riasec_complete_screen.dart L43 | 2 min |
| 3 | `automaticallyImplyLeading: false` on Grades Complete | grades_complete_screen.dart L53 | 2 min |
| 4 | Add stage guard to RIASEC Quiz `_initQuiz()`: if stage `riasec_complete`+ → `pushReplacementNamed('/riasec-complete')` | riasec_quiz_screen.dart | 20 min |
| 5 | Add stage guard to Grades Input `initState`: if stage `grades_complete`+ → `pushReplacementNamed('/grades-complete')` | grades_input_screen.dart | 20 min |
| 6 | Fix Assessment AppBar: route through `_onBackPressed`, not `Navigator.pop()` | assessment_screen.dart | 10 min |
| 7 | Login/Signup: add `bottom: false` to `SafeArea`, add `MediaQuery.removePadding(context: context, removeBottom: true, child: ...)` wrapper | login_screen.dart, signup_screen.dart | 15 min each |
| 8 | Fix `profile_provider.dart` 401 path: call `ref.read(authProvider.notifier).handleUnauthorized()` when 401 received | profile_provider.dart L93–99 | 10 min |

**Week 1 — P1 High Priority**

| # | Fix | File | Effort |
|---|---|---|---|
| 9 | Add `stated_preferences` chip selector UI + include in POST payload | preferences_screen.dart | 2 hrs |
| 10 | Change dashboard icon nav from `pushReplacementNamed` to `pushNamed` | main_chat_screen.dart L282 | 2 min |
| 11 | Add stage guard to Dashboard: if no cached recommendations, call `GET /profile/recommendations` | recommendation_dashboard.dart | 1 hr |
| 12 | Add question glow to current card: `BoxShadow(color: Color(0x40006B62), blurRadius:0, spreadRadius:2)` | assessment_screen.dart | 10 min |
| 13 | Signup ON SUCCESS: change to `pushNamedAndRemoveUntil('/riasec-quiz', (r)=>false)` | signup_screen.dart L83 | 2 min |
| 14 | Add `label` parameter to `ThinkingIndicator` and pass `currentStatusLabel` from ChatProvider | thinking_indicator.dart, main_chat_screen.dart | 30 min |

**Week 2 — P1 Systematic Fixes**

| # | Fix | Notes |
|---|---|---|
| 15 | Button radius: global `12.r` enforcement | Use `ThemeData.elevatedButtonTheme` or search-replace `16.r` in button shapes |
| 16 | Shadow tokens: update content cards to `0x0F191C1E` blur 24 offset (0,8) | Carousel, Profile, Settings, Assessment |
| 17 | Purple role violations: replace with Teal on all human UI elements | RIASEC Quiz, RIASEC Complete, Assessment Complete, Profile screen |
| 18 | Fix SSE status label strings in `kStatusLabels` | chat_provider.dart L7–15 |
| 19 | Login back-stack reconstruction: implement `_reconstructStack`-equivalent after login | login_screen.dart `_onSubmit` |

### Post-Demo / Sprint 4B (P2 Polish)

- `ProfileState` add preferences fields
- `RetakeCard` and Profile screen shadows
- OCR button: hide or `enabled: false` with no badge
- `ThinkingIndicator`: migrate stagger to `AnimationController`, fix dot size to `6.r`
- Dashboard: implement `GET /profile/recommendations` as primary data source
- Navigation shell: consider `IndexedStack` or `BottomNavigationBar` for chat ↔ dashboard
- ScreenUtil consistency: fix all hardcoded pixel values

---

## FILES READ — COMPLETE MANIFEST

| Category | File | Lines | Status |
|---|---|---|---|
| Authority | CLAUDE.md | 660 | ✓ READ |
| Authority | FRONTEND_DESIGN_SYSTEM.md | 761 | ✓ READ |
| Authority | FRONTEND_SCREEN_CONTRACTS.md | 760 | ✓ READ |
| Skill | flutter-build-responsive-layout/SKILL.md | 140 | ✓ READ |
| Skill | flutter-apply-architecture-best-practices/SKILL.md | 163 | ✓ READ |
| Provider | auth_provider.dart | 107 | ✓ READ |
| Provider | profile_provider.dart | 126 | ✓ READ |
| Provider | chat_provider.dart | 153 | ✓ READ |
| Screen 1 | splash_screen.dart | 292 | ✓ READ |
| Screen 2 | carousel_screen.dart | 484 | ✓ READ |
| Screen 3 | login_screen.dart | 505 | ✓ READ |
| Screen 4 | signup_screen.dart | 521 | ✓ READ |
| Screen 5 | riasec_quiz_screen.dart | 842 | ✓ READ |
| Screen 6 | riasec_complete_screen.dart | 378 | ✓ READ |
| Screen 7 | grades_input_screen.dart | 1185 | ✓ READ |
| Screen 8 | grades_complete_screen.dart | 375 | ✓ READ |
| Screen 9 | assessment_screen.dart | 1252 | ✓ READ |
| Screen 10 | assessment_complete_screen.dart | 330 | ✓ READ |
| Screen 11 | preferences_screen.dart | 356 | ✓ READ |
| Screen 12 | main_chat_screen.dart | 865 | ✓ READ |
| Screen 13 | recommendation_dashboard.dart | 409 | ✓ READ |
| Screen 14 | settings_screen.dart | 394 | ✓ READ |
| Screen 15 | error_screen.dart | 203 | ✓ READ |
| Screen 16 | profile_screen.dart | 250 | ✓ READ |
| Widget | thinking_indicator.dart | 79 | ✓ READ |
| Widget | university_card.dart | 341 | ✓ READ |
| App entry | main.dart | 208 | ✓ READ |

**Total: 27 files read | ~11,900 lines analysed**

---

*Audit complete — 2026-05-12 20:00 PKT*  
*No source files were modified during this audit.*  
*All findings are read-only observations against CLAUDE.md, FRONTEND_DESIGN_SYSTEM.md, and FRONTEND_SCREEN_CONTRACTS.md.*
