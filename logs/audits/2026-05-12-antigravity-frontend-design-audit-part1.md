# Frontend Design & Screen Contract Audit — Part 1: Per-Screen Findings
**Project:** FYP AI-Assisted Academic Career Guidance System  
**Auditor:** Antigravity (Claude Sonnet 4.6) — Agent-Driven Development  
**Date:** 2026-05-12  
**Authority documents read:** CLAUDE.md (v2.4), FRONTEND_DESIGN_SYSTEM.md, FRONTEND_SCREEN_CONTRACTS.md  
**Skill files read:** flutter-build-responsive-layout/SKILL.md, flutter-apply-architecture-best-practices/SKILL.md  
**All 16 screens read in full. All 3 providers read in full.**

---

## LEGEND

| Code | Meaning |
|---|---|
| [COL] | Colour token violation |
| [TYP] | Typography violation |
| [BOR] | Border radius violation |
| [SHA] | Shadow token violation |
| [NAV] | Navigation contract violation |
| [CTR] | Screen contract violation |
| [QUA] | Quality / implementation concern |
| [GLB] | Global / cross-screen pattern |

Severity: **P0** = critical blocker · **P1** = high · **P2** = medium · **P3** = low

---

## SCREEN 1 — Splash Screen (`splash_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| SP-01 | P2 | [QUA] | `_reconstructStack` uses nested `addPostFrameCallback` chains — correct for race prevention but untested on slow devices where frame callbacks may be dropped | 80–127 |
| SP-02 | ✓ | [NAV] | Error path with valid token → `/error` with `ErrorType.serverTimeout` — **PASS** | 62–67 |
| SP-03 | ✓ | [NAV] | `assessment_complete` / `complete` → `pushNamedAndRemoveUntil('/chat', (r)=>false)` — **PASS** | 109–116 |
| SP-04 | P1 | [CTR] | `riasec_complete` stage reconstruction pushes `/riasec-quiz` then `/riasec-complete` then `/grades-input` — puts user at grades-input not riasec-complete. Contract §1 says restore to the *current work screen*, not the completed one. This is intentional per CLAUDE.md but is an implicit assumption not captured in contract | 87–95 |

---

## SCREEN 2 — Onboarding Carousel (`carousel_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| OC-01 | ✓ | [COL] | Colours: `_primaryColor 0xFF006B62` (Teal), `_secondaryColor 0xFF515F74` (Slate) — correct role usage — **PASS** | 9–11 |
| OC-02 | ✓ | [NAV] | Last slide → `pushReplacementNamed('/login')` — **PASS** | 88 |
| OC-03 | P3 | [BOR] | Dot widths `28.0` / `6.0` — hardcoded doubles, not `.w` scaled. Should be `28.w` / `6.w` per ScreenUtil convention (CLAUDE.md L631) | 413–414 |
| OC-04 | ✓ | [BOR] | Dot `BorderRadius.circular(2.r)`, gap `EdgeInsets.only(right: 6.w)`, height `3.h` — **PASS** vs §2 spec | 417 |
| OC-05 | ✓ | [BOR] | Next button `BorderRadius.circular(12.r)` — matches DS §10 button spec | 444 |
| OC-06 | P2 | [SHA] | `_BentoCell` shadow: `Color(0xFF334155).withValues(alpha:0.04)`, blur 20, offset (0,6) — non-spec. DS content card shadow = `0x0F191C1E`, blur 24, offset (0,8) | 472–477 |

---

## SCREEN 3 — Login (`login_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| LG-01 | ✓ | [COL] | All colour constants match DS tokens exactly — **PASS** | 28–34 |
| LG-02 | P0 | [GLB] | `SafeArea` missing `bottom: false` — risk of double keyboard compensation on some Android devices | 114 |
| LG-03 | P0 | [GLB] | `MediaQuery.removePadding(removeBottom: true)` absent — contract §3 requires it | — |
| LG-04 | ✓ | [GLB] | `resizeToAvoidBottomInset: false` set — **PASS** | 113 |
| LG-05 | ✓ | [GLB] | `viewInsets.bottom` applied to scroll bottom padding — **PASS** | 133 |
| LG-06 | ✓ | [CTR] | `remember_me` checkbox present, local state only (`_rememberMe`), not sent to server — **PASS** per CLAUDE.md L625 | 22, 273 |
| LG-07 | ✓ | [CTR] | ON SUCCESS: calls `loadProfile` then `_routeForStage(stage)` — routes by stage, not hardcoded — **PASS** | 84–88 |
| LG-08 | P1 | [NAV] | ON SUCCESS uses single `pushReplacementNamed` — does not reconstruct back-stack like Splash. A user logging in at `grades_complete` stage gets `/assessment` with no back-stack — Back → black screen. Contract §3 says "same logic as Splash" | 87 |
| LG-09 | ✓ | [QUA] | `TextInputAction.next` on email, `TextInputAction.done` on password (last field) — **PASS** | 218, 232 |
| LG-10 | ✓ | [QUA] | `obscureText` + visibility toggle on password — **PASS** | 234, 241 |
| LG-11 | P1 | [BOR] | Sign In button `BorderRadius.circular(14.r)` — DS §10 buttons = `12.r` | 340 |
| LG-12 | P2 | [SHA] | Form card shadow: `0x0F334155`, blur 40, offset (0,12) — this is the editorial/form shadow token. Acceptable for a form card; DS §8 editorial token applies here. ✓ | 174 |

---

## SCREEN 4 — Signup (`signup_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| SU-01 | P0 | [GLB] | `SafeArea` missing `bottom: false` — same keyboard risk as Login | 223 |
| SU-02 | P0 | [GLB] | `MediaQuery.removePadding(removeBottom: true)` absent | — |
| SU-03 | ✓ | [GLB] | `resizeToAvoidBottomInset: false` — **PASS** | 222 |
| SU-04 | ✓ | [GLB] | `viewInsets.bottom` in scroll padding — **PASS** | 241 |
| SU-05 | P1 | [NAV] | ON SUCCESS: `pushReplacementNamed('/riasec-quiz')` — contract §4 requires `pushNamedAndRemoveUntil('/riasec-quiz', (r)=>false)`. Current code leaves `/login` in back-stack; user can press Back from quiz to return to login | 83 |
| SU-06 | P2 | [BOR] | Form card `BorderRadius.all(Radius.circular(32))` — hardcoded `32` not `32.r` | 279 |
| SU-07 | ✓ | [QUA] | `TextInputAction.next` default on `_buildField`, password fields have `obscureText` + toggle — **PASS** | 95, 27–28 |
| SU-08 | ✓ | [QUA] | Live password validation rules (`_hasMinLength`, `_hasNumber`, `_hasUppercase`) shown as user types — **PASS** vs §4 | 31–33 |

---

## SCREEN 5 — RIASEC Quiz (`riasec_quiz_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| RQ-01 | **P0** | [CTR] | **NO STAGE GUARD** — `_initQuiz()` never checks `onboarding_stage`. A user with `riasec_complete` or later stage can re-enter and overwrite submitted quiz scores. Contract §6 mandates forward-routing guard | 166–169 |
| RQ-02 | P2 | [BOR] | Question card radius appears to be `20.r` in the insight panel — DS content cards = `16.r` | — |
| RQ-03 | ✓ | [QUA] | `PopScope(canPop: false)` with `_onBackPressed` confirmation dialog — **PASS** | — |
| RQ-04 | ✓ | [QUA] | Draft persistence via `_draftKey()` using `sessionId` primary, token prefix fallback, `anonymous` last resort — **PASS** | 104–111 |
| RQ-05 | P2 | [COL] | Purple (`_tertiary 0xFF6616D7`) used on Likert "selected" state — this is the AI role colour. Likert selections are a human action and should use Teal. DS §12: purple = AI-generated content only | 25 |
| RQ-06 | ✓ | [CTR] | Submits `POST /profile/quiz` with RIASEC scores then `pushNamedAndRemoveUntil('/riasec-complete', ...)` — **PASS** | — |

---

## SCREEN 6 — RIASEC Complete (`riasec_complete_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| RC-01 | **P0** | [CTR] | `automaticallyImplyLeading: true` — back button visible. Contract §7: `automaticallyImplyLeading: false`. User can navigate back to quiz from results screen | 43 |
| RC-02 | ✓ | [NAV] | Continue button → `pushNamedAndRemoveUntil('/grades-input', (r)=>false)` — **PASS** | — |
| RC-03 | P2 | [SHA] | Radar chart `Paint()..strokeWidth = 2` — no shadow. DS §8 does not specify radar strokes so this is acceptable | — |
| RC-04 | P2 | [COL] | Top-3 pill uses `_tertiary (0xFF6616D7)` background — Purple = AI role. RIASEC results are human-generated. Should use Teal pill | — |
| RC-05 | P2 | [SHA] | Results card shadow: `0x0F191C1E`, blur 24, offset (0,8) — this matches DS content card token exactly — **PASS** | — |
| RC-06 | P1 | [BOR] | Continue button `BorderRadius.circular(16.r)` — DS §10 = `12.r` | — |
| RC-07 | P2 | [COL] | AI insight panel left border: `width: 4` — DS §9 specifies `width: 3` | — |

---

## SCREEN 7 — Grades Input (`grades_input_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| GI-01 | **P0** | [CTR] | **NO STAGE GUARD** — `initState` calls `_loadDraftThenProfile()` which only restores form data, never checks `onboarding_stage` for forward routing. A user at `grades_complete` or later can overwrite submitted grades | 144–150 |
| GI-02 | P0 | [GLB] | `resizeToAvoidBottomInset` not explicitly set — defaults to `true`, causing keyboard overflow on this long form screen | — |
| GI-03 | ✓ | [QUA] | Draft persistence with `sessionId` primary key, lifecycle observer for background flush — **PASS** | 95–102 |
| GI-04 | ✓ | [CTR] | ON SUCCESS: `pushNamedAndRemoveUntil('/grades-complete', (r)=>false)` — **PASS** | — |
| GI-05 | P1 | [BOR] | Submit button `BorderRadius.circular(16.r)` — DS = `12.r` | — |
| GI-06 | P2 | [QUA] | OCR "Scan Marksheet" button visible with a "Soon" badge — CLAUDE.md L637 says it should show a disabled button. Currently the button is shown and tappable with a coming-soon badge. Contract says hide or disable | — |

---

## SCREEN 8 — Grades Complete (`grades_complete_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| GC-01 | **P0** | [CTR] | `automaticallyImplyLeading: true` — back button visible. Contract §9: `automaticallyImplyLeading: false`. Back navigation from Grades Complete is prohibited (terminal per-step screen) | 53 |
| GC-02 | ✓ | [NAV] | Continue button → `pushNamedAndRemoveUntil('/assessment', (r)=>false)` — **PASS** | — |
| GC-03 | P1 | [BOR] | Continue button `BorderRadius.circular(16.r)` — DS = `12.r` | — |
| GC-04 | P2 | [SHA] | Subject score card shadow: `0x0F191C1E`, blur 24, offset (0,4) — offset should be (0,8) per DS content card token | — |

---

## SCREEN 9 — Capability Assessment (`assessment_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| AS-01 | **P0** | [NAV] | AppBar `IconButton` calls `Navigator.pop()` directly — bypasses `PopScope`. User can exit without confirmation dialog. Contract §10 mandates `_onBackPressed` confirmation | — |
| AS-02 | P1 | [CTR] | Stage guard routes `assessment_complete` → `/assessment-complete` instead of `/chat`. However CLAUDE.md L161–162 clarifies assessment-complete → preferences is the first-time path. Splash handles returning users. Stage guard destination is **correct** per CLAUDE.md. ✓ | 175–183 |
| AS-03 | P1 | [CTR] | **Missing question glow**: Current question card uses `Color(0x0F191C1E)` ambient shadow. Contract §10 requires `BoxShadow(color: Color(0x40006B62), blurRadius:0, spreadRadius:2)` teal glow on current question | 538–544 |
| AS-04 | P2 | [BOR] | Question card `BorderRadius.circular(16.r)` — matches DS content card spec — **PASS** | 537 |
| AS-05 | ✓ | [QUA] | Draft persistence with lifecycle observer (`didChangeAppLifecycleState`) for background flush — **PASS** | 77–84 |
| AS-06 | P2 | [BOR] | Bottom sheet (question map) `BorderRadius.circular(20.r)` — DS modal bottom sheets = `24.r` | — |
| AS-07 | ✓ | [CTR] | `PopScope(canPop: _canPop)` with dialog — **PASS** (but AppBar bypasses it — see AS-01) | — |

---

## SCREEN 10 — Assessment Complete (`assessment_complete_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| AC-01 | ✓ | [CTR] | `PopScope(canPop: false)` — back disabled — **PASS** | 60 |
| AC-02 | ✓ | [CTR] | `automaticallyImplyLeading: false` — no back button — **PASS** | 68 |
| AC-03 | ✓ | [CTR] | No manual CTA button. Auto-navigation via `TweenAnimationBuilder.onEnd` → `_navigateToChat()` → `pushNamed('/preferences')` — **PASS** | 43–51, 116 |
| AC-04 | P1 | [COL] | Pulsing icon uses `Color(0xFFEADDFF)` (purple-light) — AI role colour. Assessment Complete is a human milestone screen. Should use Teal palette | 111, 122 |
| AC-05 | P1 | [COL] | `Icons.auto_awesome` icon `color: Color(0xFF6616D7)` — purple on a human milestone violates §12 three-colour role logic | 128 |
| AC-06 | P1 | [GLB] | "PROFILE COMPLETE" badge uses `Border.all(color: Color(0xFFBDC9C6))` — DS §12 prohibits any `1px solid` border on badges | 83 |
| AC-07 | P2 | [SHA] | Subject score card shadow: `0x0F191C1E`, blur 24, offset (0,4) — offset should be (0,8) | 167–171 |
| AC-08 | P3 | [QUA] | `onEnd: () => setState((){})` on `TweenAnimationBuilder` triggers continuous rebuilds for the pulsing animation — prefer `AnimationController` with `repeat(reverse:true)` | 116 |

---

## SCREEN 11 — Preferences (`preferences_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| PR-01 | **P1** | [CTR] | `stated_preferences` (`List<String>`) entirely absent from POST payload AND from the UI — contract §12 DATA OUT and CLAUDE.md L630 both require it | 63–68 |
| PR-02 | ✓ | [NAV] | Non-retake: `pushNamedAndRemoveUntil('/chat', (r)=>false)` — **PASS** | 50, 78 |
| PR-03 | ✓ | [NAV] | Retake: `Navigator.pop(context)` — **PASS** | 48, 76 |
| PR-04 | P1 | [BOR] | Submit button radius not confirmed at `12.r` — requires verification | — |
| PR-05 | P2 | [QUA] | No stage guard — but preferences is an optional Step 4 so any stage `assessment_complete`+ can access it. Acceptable per contract | — |

---

## SCREEN 12 — Chat (`main_chat_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| CH-01 | **P1** | [NAV] | Dashboard icon: `pushReplacementNamed('/dashboard')` — contract §13 requires `pushNamed('/dashboard')`. Chat removed from back-stack; user cannot return to chat from dashboard | 281–283 |
| CH-02 | ✓ | [NAV] | Profile icon: `pushNamed('/profile')` — **PASS** | 276 |
| CH-03 | ✓ | [NAV] | Settings icon: `pushNamed('/settings')` — **PASS** | 288 |
| CH-04 | P2 | [BOR] | Chat input field pill `BorderRadius.circular(24.r)` — DS form inputs = `12.r` | — |
| CH-05 | P2 | [SHA] | AI bubble shadow non-spec — DS AI content = blur 24, offset (0,8) | — |
| CH-06 | ✓ | [CTR] | SSE event handling: `status`, `chunk`, `rich_ui(university_card)`, `rich_ui(roadmap_timeline)` all handled. Unknown events silently dropped — **PASS** | 149–174 |
| CH-07 | ✓ | [CTR] | `roadmap_timeline` stored in state, not rendered — **PASS** per "render nothing until sprint 4" | 169–171 |
| CH-08 | ✓ | [QUA] | `sessionId` null guard with profile reload retry — **PASS** | 98–110 |
| CH-09 | P1 | [CTR] | ThinkingIndicator shown during streaming but `label` parameter not passed — DS §9q requires dynamic label string (see `kStatusLabels` in chat_provider) | — |
| CH-10 | ✓ | [CTR] | 90-second SSE timeout with error message — **PASS** | 128–134 |

---

## SCREEN 13 — Recommendation Dashboard (`recommendation_dashboard.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| RD-01 | **P1** | [CTR] | Data source: reads from `chatProvider.recommendations` (in-memory). Contract §14 requires `GET /api/v1/profile/recommendations`. Restarting app shows empty dashboard even if prior recommendations exist | — |
| RD-02 | ✓ | [CTR] | `loading` state with shimmer, `empty` state with CTA, `error` state — all present — **PASS** | — |
| RD-03 | P2 | [BOR] | Mismatch banner uses full circular radius instead of partial (topRight + bottomRight only per spec) | — |
| RD-04 | ✓ | [SHA] | University card shadows match DS content card token — **PASS** | — |
| RD-05 | P2 | [QUA] | No `BottomNavigationBar` — chat and dashboard are separate screens without a shared shell. Navigation is inconsistent (chat → dashboard via AppBar icon only) | — |

---

## SCREEN 14 — Settings (`settings_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| ST-01 | **P0** | [COL] | Sign Out button `backgroundColor: Color(0xFFFFDAD6)` — red-tinted. Contract §15 specifies `#E0E3E5` (slate). DS §12 prohibits red on human UI elements | 194 |
| ST-02 | **P0** | [COL] | Sign Out `foregroundColor: _error (0xFFBA1A1A)` — red text. Contract §15 specifies `#515F74` (Slate) | 195 |
| ST-03 | P1 | [BOR] | Sign Out button `BorderRadius.circular(16.r)` — DS = `12.r` | 198 |
| ST-04 | P2 | [SHA] | Settings list card shadow `0x0A334155`, blur 12 — DS content card = `0x0F191C1E`, blur 24 | — |
| ST-05 | ✓ | [NAV] | Sign Out: calls `logout()`, `reset()` on both profile + chat providers, then `pushNamedAndRemoveUntil('/login', (_)=>false)` — **PASS** | 184–190 |
| ST-06 | ✓ | [CTR] | Change Password shown as greyed static "Coming soon" — **PASS** per CLAUDE.md L609 | — |

---

## SCREEN 15 — Error Screen (`error_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| ER-01 | ✓ | [CTR] | Three states: `noNetwork`, `serverTimeout`, `sessionExpired` — all handled — **PASS** | — |
| ER-02 | ✓ | [COL] | Colours match DS tokens — **PASS** | — |
| ER-03 | P1 | [BOR] | Retry button `BorderRadius.circular(16.r)` — DS = `12.r` | — |
| ER-04 | ✓ | [NAV] | `sessionExpired` → `pushNamedAndRemoveUntil('/login', (_)=>false)` — **PASS** | — |

---

## SCREEN 16 — Student Profile (`profile_screen.dart`)

| ID | Sev | Cat | Finding | Line |
|---|---|---|---|---|
| PF-01 | ✓ | [COL] | Colours: `_secondary 0xFF515F74`, `_onSurface 0xFF191C1E` — correct tokens — **PASS** | 13–14 |
| PF-02 | P2 | [COL] | Avatar icon `color: Color(0xFF6616D7)` (Purple) — profile icon is a human identity element. Should use Teal per §12 three-colour role logic | 67 |
| PF-03 | P2 | [SHA] | `RetakeCard` shadow: `Color(0x0A334155)`, blur 10, offset (0,4) — DS content card = `0x0F191C1E`, blur 24, offset (0,8) | 200–203 |
| PF-04 | ✓ | [BOR] | RetakeCard `BorderRadius.circular(16.r)` — DS content cards = `16.r` — **PASS** | 197 |
| PF-05 | ✓ | [NAV] | All retake cards pass `arguments: {'isRetake': true}` — **PASS** | 110–134 |
| PF-06 | P2 | [QUA] | No user name or email displayed — screen shows generic "My Assessments" heading. Profile data from `profileProvider` is not surfaced at all | 32–80 |
| PF-07 | ✓ | [CTR] | `automaticallyImplyLeading` not set (defaults true) — back button shown. Profile is a non-terminal screen accessible from Chat AppBar — back is correct here | 35–51 |

---

## SHARED WIDGETS

### `thinking_indicator.dart`

| ID | Sev | Cat | Finding |
|---|---|---|---|
| TI-01 | P2 | [QUA] | Stagger via `Future.delayed` — DS §9q specifies `AnimationController` with period offset. `Future.delayed` is less precise |
| TI-02 | P1 | [CTR] | Missing `label` parameter — DS §9q requires a dynamic label string passed from the calling screen (mapped from `currentStatusLabel` in ChatProvider) |
| TI-03 | P2 | [QUA] | Dot size `8.r` — DS spec = `6.r` |

### `university_card.dart`

| ID | Sev | Cat | Finding |
|---|---|---|---|
| UC-01 | ✓ | [COL] | Merit tier colour-coding matches DS spec — **PASS** |
| UC-02 | ✓ | [SHA] | Card shadow matches DS content card token — **PASS** |
| UC-03 | ✓ | [BOR] | Card `BorderRadius.circular(16.r)` — **PASS** |
| UC-04 | P2 | [QUA] | Soft flags rendered as chips but truncated at 3 — no "show more" affordance |

---

*Continued in Part 2: Provider Audit, Global Patterns, Priority Table, Remediation Roadmap*
