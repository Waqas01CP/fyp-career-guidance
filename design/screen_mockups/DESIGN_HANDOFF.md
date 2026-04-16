# DESIGN_HANDOFF.md
**Flutter Developer:** Khuzzaim  
**Platform:** Android + Flutter Web (single codebase)  
**State Management:** Riverpod (`flutter_riverpod ^2.5.1`)  
**Design System:** Academic Intelligence — Material Design 3 Tonal Layering  
**Viewport:** 390px mobile (equivalent: `max-width: 390px` → Flutter `BoxConstraints`)  
**Last Updated:** v1.5 (post-accessibility pass)

---

## Screen 01 — Splash Screen

### 1. Screen Name and Purpose
Determines onboarding routing on app cold start; shows animated brand identity for ~2 seconds then navigates based on `onboarding_stage`.

### 2. Flutter File Path
`lib/screens/splash_screen.dart`

### 3. Sprint
Sprint 1

### 4. Demo Status
Full — routing logic is live.

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Full-screen background |
| `#FFFFFF` | `on-primary` | Logo icon, wordmark text |
| `#A3FAEF` | `on-primary-container` | Tagline text (muted white-teal) |
| `#00857A` | `primary-container` | Animated loading bar fill |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| App wordmark "Academic Intelligence" | 22px | 700 | `#FFFFFF` | `letter-spacing: -0.02em` |
| Tagline "Your Career Companion" | 13px | 400 | `#A3FAEF` | `line-height: 1.6` |
| Version annotation (dev only) | 9px | 700 | `#A3FAEF` | `letter-spacing: 0.08em`, uppercase, `opacity: 0.6`, hidden in prod |

### 7. Spacing and Layout
- Full-screen: `Scaffold` with background `Color(0xFF006B62)`
- Content centred vertically and horizontally: `Column(mainAxisAlignment: MainAxisAlignment.center)`
- Logo icon container: `80×80px`, `BorderRadius.circular(20)`, background `rgba(255,255,255,0.15)`
- Gap between icon and wordmark: `20px`
- Gap between wordmark and tagline: `8px`
- Gap between tagline and loading bar: `48px`
- Loading bar: `width: 120px`, `height: 3px`, `BorderRadius.circular(2)`
- Dev annotation block: bottom-aligned, `padding: 20px`, hidden via `display:none` equivalent (`Visibility(visible: false)` or remove in prod)

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Logo icon (`auto_stories`) | `Icon` from `material_symbols_icons` | Static | `size: 40`, `color: Colors.white`, FILL=1 |
| AI sparkle icon (`auto_awesome`) | `Icon` | Static | `size: 16`, overlaid bottom-right of logo container |
| Loading bar | `AnimatedContainer` or `TweenAnimationBuilder` | Animating → complete | Width animates 0→120px over 1.8s, `Curves.easeInOut` |
| Dev annotation | `Positioned` at bottom | Hidden in prod | `Visibility(visible: kDebugMode)` |

### 9. Navigation Trigger
After animation completes (~2s), read `flutter_secure_storage` key `'jwt_token'`:
- No token → `CarouselScreen` (onboarding)
- Token present → call `GET /api/v1/profile/me` to read `onboarding_stage`:
  - `not_started` → `RiasecQuizScreen`
  - `riasec_complete` → `GradesInputScreen`
  - `grades_complete` → `AssessmentScreen`
  - `assessment_complete` → `ChatScreen` (AsyncPostgresSaver restores prior session; recommendations table checked for prior runs)
- 401 response → clear token → `CarouselScreen`

### 10. API Connection
`GET /api/v1/profile/me`  
Headers: `Authorization: Bearer <jwt_token>`  
Response field: `onboarding_stage` (string) → drives routing above.  
If network error → `ErrorScreen` (State 1 or 2).

### 11. State Management
- Reads `flutter_secure_storage` directly (not via provider) at splash
- On success, hydrates `authProvider` with token and `profileProvider` with full profile response
- No writes to providers before network call completes

### 12. Platform Notes
- Android: Standard splash; consider `flutter_native_splash` package for true native splash before Flutter engine loads
- Flutter Web: Loading bar animation may flicker on first paint — wrap in `WidgetsBinding.instance.addPostFrameCallback`

### 13. Flutter-Specific Notes
- Use `Future.delayed(const Duration(milliseconds: 300))` before starting navigation to let animation begin
- Dev annotation div (`display:none` in HTML) → `kDebugMode` guard in Flutter: `if (kDebugMode) ...`
- `onboarding_stage` values are exact strings — match them with a Dart `enum` or `const` strings, do not use `.toLowerCase()` comparisons

---

## Screen 02 — Onboarding Carousel

### 1. Screen Name and Purpose
Introduces the app's three core value propositions to first-time users (or post-logout users with no token). Three slides: Interest Mapping, Academic Intelligence, Career Pathways.

### 2. Flutter File Path
`lib/screens/onboarding/carousel_screen.dart`

### 3. Sprint
Sprint 1

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Active dot indicator, "Next" button bg, logo mark, slide accent elements |
| `#FFFFFF` | `on-primary` | "Next" button text/icon |
| `#E0E3E5` | `surface-container-highest` | Inactive dot indicators |
| `#515F74` | `secondary` | "Skip" button text, body copy |
| `#6616D7` | `tertiary` | AI-labelled chip text + icons on slides |
| `#EADDFF` | `tertiary-fixed` | AI chip background, inner SVG accent |
| `#F2F4F6` | `surface-container-low` | Visual anchor card background |
| `#FFFFFF` | `surface-container-lowest` | Inner bento cards |
| `#F7F9FB` | `surface` / `surface-bright` | Page background |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Brand name "Academic Intelligence" | 14px | 700 | `#006B62` | In header |
| Slide headline | 30px | 700 | `#191C1E` | `letter-spacing: -0.02em`, `line-height: 1.2` |
| Headline emphasis word | 30px | 700 | `#006B62` | italic weight (use `FontStyle.italic`) |
| Slide body | 16px | 400 | `#515F74` | `line-height: 1.6`, `max-width: 90%` |
| Category chip label | 10px | 700 | `#6616D7` | `letter-spacing: 0.12em`, uppercase |
| Skip button | 14px | 600 | `#515F74` | — |
| Next button | 15px | 700 | `#FFFFFF` | — |

### 7. Spacing and Layout
- AppBar equivalent: `Padding(padding: EdgeInsets.symmetric(horizontal: 32, vertical: 24))`
- Visual anchor card: `aspect-ratio 1:1` → use `AspectRatio(aspectRatio: 1.0)`, `BorderRadius.circular(40)`, background `#F2F4F6`
- Inner bento grid: 2-column, 2-row CSS grid → Flutter `GridView` or manual `Row`+`Column` with `gap: 16px`
- Text content: `spacing: 16px` between chip, h1, body
- Footer: `padding: EdgeInsets.fromLTRB(32, 32, 32, 48)`
- Dot indicators: active `width: 28px, height: 3px`; inactive `width: 6px, height: 3px`; `BorderRadius.circular(2)`; gap `6px`
- Avatar stack: `-12px` horizontal overlap → `Stack` with `Positioned` offsets

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Slide carousel | `PageView` | — | `physics: BouncingScrollPhysics()` |
| Dot progress indicators | `AnimatedContainer` row | active / inactive | Animate width change on page change |
| "Skip" button | `TextButton` | default / hover | `minSize: Size(48, 48)`, `focusNode` with `focusColor` |
| "Next" / "Get Started" button | `ElevatedButton` | default / pressed | `BorderRadius.circular(12)`, shadow `BoxShadow(color: Color(0x40006B62), blurRadius: 20, offset: Offset(0,8))` |
| Avatar stack | `SizedBox(width:10, height:10)` `CircleAvatar` | Static | On last slide, "Next" becomes "Get Started" |
| Category chip | `Container` + `Row` | Static | `BorderRadius.circular(20)`, `padding: EdgeInsets.symmetric(horizontal:12, vertical:4)` |

### 9. Navigation Trigger
- "Skip" → jumps directly to `LoginScreen`
- "Next" on slides 1–2 → advances carousel page
- "Get Started" on slide 3 → navigates to `LoginScreen`
- Condition: Shown only when `flutter_secure_storage` has no `'jwt_token'`; also shown after logout

### 10. API Connection
None.

### 11. State Management
Local `StatefulWidget` or `StateProvider<int>` for current page index. No global providers read/written.

### 12. Platform Notes
- Android: `PageView` works natively
- Flutter Web: Add swipe gesture support; keyboard left/right arrow support for accessibility

### 13. Flutter-Specific Notes
- Decorative corner element (top-right gradient circle): `ClipRRect` + `Positioned` outside safe area, `IgnorePointer(ignoring: true)`
- SVG chart inside bento card: use `flutter_svg` package or replace with a custom `CustomPainter`
- The `lg:` desktop layout in HTML (wide-screen panel) → ignored for mobile Flutter target; Flutter Web at 390px equivalent uses same mobile layout

---

## Screen 03 — Login Screen

### 1. Screen Name and Purpose
Authenticates returning users via email/password or Google SSO. Entry point after carousel for users with existing accounts.

### 2. Flutter File Path
`lib/screens/auth/login_screen.dart`

### 3. Sprint
Sprint 1

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Gradient top bar, "Sign In" button bg, focus left-border, checkbox accent, "Sign Up" link |
| `#00857A` | `primary-container` | Gradient end colour (top bar) |
| `#FFFFFF` | `on-primary` | Button text |
| `#F7F9FB` | `surface` | Page background |
| `#FFFFFF` | `surface-container-lowest` | Form card background |
| `#F2F4F6` | `surface-container-low` | Input field fill colour |
| `#515F74` | `secondary` | Labels, helper text, icon colours, "Remember me" text |
| `#191C1E` | `on-surface` | Input text |
| `#BA1A1A` | `error` | Error state left-border ONLY (not background) |
| `#E6E8EA` | `surface-container-high` | Google SSO button background |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Screen title "Welcome Back" | 28px | 700 | `#191C1E` | `letter-spacing: -0.02em` |
| Subtitle | 14px | 400 | `#515F74` | `line-height: 1.6` |
| Form field labels | 12px | 600 | `#515F74` | `letter-spacing: 0.04em` |
| Input text | 15px | 400 | `#191C1E` | — |
| Error message | 12px | 500 | `#BA1A1A` | Below field, with `info` icon |
| "Forgot Password?" link | 13px | 600 | `#006B62` | Right-aligned |
| "Sign In" button | 15px | 700 | `#FFFFFF` | — |
| "Don't have an account? Sign Up" | 14px | 400/700 | `#515F74`/`#006B62` | Mixed: "Sign Up" is bold teal |
| Google SSO label | 14px | 600 | `#191C1E` | — |
| "Remember me" | 13px | 400 | `#515F74` | — |

### 7. Spacing and Layout
- Page: `SingleChildScrollView`, `padding: EdgeInsets.all(24)`
- Gradient top bar: `height: 3px`, `width: double.infinity`, above form card
- Form card: `BorderRadius.circular(32)` (2rem), `padding: EdgeInsets.all(28)`, `BoxShadow(color: Color(0x0F334155), blurRadius: 40, offset: Offset(0,12))`
- Gap between form card and "Sign Up" row: `24px`
- Fields stacked with `16px` gap
- "Forgot Password?" row: `8px` top margin from password field
- "OR" divider: `Row` with `Expanded(Divider())` — use `outlineVariant` at 40% opacity
- Google SSO button: `height: 52px`, full width, `BorderRadius.circular(14)`
- "Remember me" row: `12px` top margin

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Email field | `TextFormField` | default / focused / error | `keyboardType: TextInputType.emailAddress`, `TextInputAction.next` |
| Password field | `TextFormField` | default / focused / error / visible | `obscureText: true` toggle, `visibility_off` suffix icon |
| Focus left-border | `Stack` + `Container` (2px wide, primary colour) | focused / unfocused | `FocusNode.hasFocus` listener; `AnimatedOpacity` |
| Error left-border | `Stack` + `Container` (2px wide, error colour) | error state only | shown when `FormState.validate()` fails |
| "Remember me" checkbox | `Checkbox` | checked / unchecked | `h-6 w-6` (24px), `activeColor: Color(0xFF006B62)` |
| "Sign In" button | `ElevatedButton` | default / loading / disabled | Show `CircularProgressIndicator(strokeWidth: 2, color: Colors.white)` during API call |
| "Forgot Password" | `TextButton` | — | Navigate to `ForgotPasswordScreen` |
| Google SSO | `OutlinedButton` | default / loading | Background `#E6E8EA`, no border; use Google SVG asset |
| Visibility toggle | `IconButton` | visible / hidden | `size: 48px` tap target |

### 9. Navigation Trigger
- Successful login (`POST /api/v1/auth/login` → 200) → store JWT → route based on `onboarding_stage` (same logic as Splash)
- "Forgot Password?" → `ForgotPasswordScreen`
- "Sign Up" → `SignupScreen`

### 10. API Connection
`POST /api/v1/auth/login`  
Body: `{ "email": string, "password": string }`  
Response: `{ "access_token": string, "token_type": "bearer" }`  
→ Store `access_token` in `flutter_secure_storage` key `'jwt_token'`  
→ Immediately call `GET /api/v1/profile/me` to get `onboarding_stage`  
401: show inline error "Incorrect email or password"  
422: show field-level validation errors

### 11. State Management
- `authProvider.notifier.login(email, password)` → sets `AuthState.loading` then `AuthState.authenticated` or `AuthState.error`
- On success, `profileProvider.notifier.loadProfile()` is called

### 12. Platform Notes
- Android: `TextInputAction.done` on password field triggers form submit; `autofillHints: [AutofillHints.email]` on email field
- Flutter Web: `autofillHints` enables browser autofill; ensure `AutofillGroup` wraps both fields

### 13. Flutter-Specific Notes
- Left-border focus effect: Flutter `InputDecoration` has no native left-border-only focus. Use `Stack`: base `TextField` + `Positioned(left:0, top:0, bottom:0, child: AnimatedContainer(width: focused ? 2 : 0, color: primary))`
- Google SSO: integrate `google_sign_in` package. On web, use `renderButton` approach
- Form validation runs on submit only (not on every keystroke) to match the mockup's clean default state

---

## Screen 04 — Sign Up Screen

### 1. Screen Name and Purpose
Registers new users with email, password, and name. Creates account and begins onboarding flow.

### 2. Flutter File Path
`lib/screens/auth/signup_screen.dart`

### 3. Sprint
Sprint 1

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Gradient top bar, "Create Account" button, focus accent, "Sign In" link, check_circle validation icons |
| `#00857A` | `primary-container` | Gradient end |
| `#FFFFFF` | `surface-container-lowest` | Form card |
| `#F2F4F6` | `surface-container-low` | Input fill |
| `#515F74` | `secondary` | Labels, icons, secondary text, unfilled validation circles |
| `#191C1E` | `on-surface` | Input text |
| `#E6E8EA` | `surface-container-high` | Google SSO button bg |

### 6. Typography
| Element | Size | Weight | Colour |
|---------|------|--------|--------|
| Screen title "Create Account" | 28px | 700 | `#191C1E` |
| Subtitle | 14px | 400 | `#515F74` |
| Field labels | 12px | 600 | `#515F74` |
| Input text | 15px | 400 | `#191C1E` |
| Password rule text | 11px | 400 | `#515F74` |
| "Sign In" link | 14px | 700 | `#006B62` |

### 7. Spacing and Layout
- Same form card pattern as Login: `BorderRadius.circular(32)`, ambient shadow
- Two-column layout for first name / last name: `Row` with `Expanded` children, `gap: 12px`
- Icon prefix inside field: `prefixIcon` with `person`, `mail`, `lock`, `verified_user` Material Symbols, colour `#515F74`
- Password validation row: `gap: 8px` between icon and text, `16px` top margin from password field
- `SizedBox(height: 8)` between password and confirm-password fields

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| First/Last name fields | `TextFormField` | default / focused | `TextInputAction.next` |
| Email field | `TextFormField` | default / focused / error | `keyboardType: TextInputType.emailAddress` |
| Password field | `TextFormField` | default / focused / visible | `obscureText` toggle |
| Confirm password | `TextFormField` | default / focused / mismatch error | Validates equality with password field |
| Password rule indicators | `Icon` (`check_circle` filled / `radio_button_unchecked`) | pass / fail | Animate with `AnimatedSwitcher` |
| "Create Account" button | `ElevatedButton` | default / loading | Same as Login |
| Google SSO | `OutlinedButton` | — | Same as Login |

### 9. Navigation Trigger
- Successful registration (`POST /api/v1/auth/register` → 200/201) → store JWT → navigate to `RiasecQuizScreen` (onboarding_stage = `not_started`)
- "Sign In" link → `LoginScreen`

### 10. API Connection
`POST /api/v1/auth/register`  
Body: `{ "email": string, "password": string, "full_name": string }`  
Response: `{ "access_token": string, "token_type": "bearer" }`  
409: show "An account with this email already exists"

### 11. State Management
`authProvider.notifier.register(email, password, fullName)`

### 12. Platform Notes
- Android: `autofillHints: [AutofillHints.newPassword]` on password fields
- Flutter Web: `AutofillGroup` for all fields

### 13. Flutter-Specific Notes
- Password validation rules (check in real-time as user types):
  - Minimum 8 characters
  - At least one number
  - At least one uppercase letter
- `check_circle` FILL=1 in teal, `radio_button_unchecked` FILL=0 in slate — use `font-variation-settings` via `material_symbols_icons` package
- Full name: concatenate first + last name into single `full_name` string before API call

---

## Screen 05 — Forgot Password

### 1. Screen Name and Purpose
Placeholder screen shown when user taps "Forgot Password?". Displays a "coming soon" message — no backend endpoint exists yet.

### 2. Flutter File Path
`lib/screens/auth/forgot_password_screen.dart`

### 3. Sprint
Sprint 1

### 4. Demo Status
Static coming soon — no API call, no form submission.

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#F7F9FB` | `surface` | Page background |
| `#006B62` | `primary` | Back button icon, "Back to Sign In" link |
| `#515F74` | `secondary` | Icon colour, body text |
| `#F2F4F6` | `surface-container-low` | "Coming soon" badge background |
| `#191C1E` | `on-surface` | Title text |

### 6. Typography
| Element | Size | Weight | Colour |
|---------|------|--------|--------|
| "Coming soon" badge | 9px | 700 | `#515F74` | uppercase, `letter-spacing: 0.08em` |
| Screen title | 24px | 700 | `#191C1E` |
| Body copy | 14px | 400 | `#515F74` | `line-height: 1.6` |
| "Back to Sign In" | 14px | 700 | `#006B62` |

### 7. Spacing and Layout
- `lock_reset` icon container: `80×80px`, `BorderRadius.circular(40)` (circle), background `#F2F4F6`
- Icon centred in container: `font-size: 36px`, colour `#515F74`
- Content centred vertically: `Column(mainAxisAlignment: MainAxisAlignment.center)`
- Padding: `EdgeInsets.symmetric(horizontal: 40)`
- Gap: icon → badge `20px`; badge → title `12px`; title → body `8px`; body → link `32px`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Back button | `IconButton` (AppBar leading) | — | `w-12 h-12`, `aria-label: "Go back"` |
| "Coming soon" badge | `Container` chip | Static | `BorderRadius.circular(20)`, `padding: EdgeInsets.symmetric(horizontal:12, vertical:4)` |
| `lock_reset` icon | `Icon` | Static | Size 36 |
| "Back to Sign In" | `TextButton` | — | Navigate to `LoginScreen` |

### 9. Navigation Trigger
- Back button or "Back to Sign In" → `LoginScreen` (`Navigator.pop`)

### 10. API Connection
None.

### 11. State Management
None.

### 12. Platform Notes
No differences.

### 13. Flutter-Specific Notes
This screen is complete as-is. Do not add a form. Do not add email input. The password reset flow is deferred post-mid-evaluation.

---

## Screen 06 — RIASEC Quiz

### 1. Screen Name and Purpose
Administers the 60-question RIASEC interest inventory. One question at a time, 5-point Likert scale. First step of onboarding.

### 2. Flutter File Path
`lib/screens/onboarding/riasec_quiz_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Progress bar fill, selected Likert button bg, "Next" button, dimension chip |
| `#FFFFFF` | `on-primary` | Selected Likert button text/icon, "Next" button text |
| `#E6E8EA` | `surface-container-high` | Unselected Likert button bg, progress bar track |
| `#515F74` | `secondary` | Unselected Likert text, "Previous" ghost button, question counter text, AI chip text (mobile) |
| `#F2F4F6` | `surface-container-low` | AI panel (mobile pill strip) bg, page bg sections |
| `#191C1E` | `on-surface` | Question text |
| `#FFFFFF` | `surface-container-lowest` | Question card bg |
| `#6616D7` | `tertiary` | AI insight panel border-left, AI label, `auto_awesome` icon |
| `#EADDFF` | `tertiary-fixed` | AI insight panel background |
| `#5A00C6` | `on-tertiary-fixed-variant` | AI label text |
| `#25005A` | `on-tertiary-fixed` | AI insight body text |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Question counter "Q12 of 60" | 11px | 700 | `#515F74` | uppercase, `letter-spacing: 0.08em` |
| Dimension chip label (e.g. "Investigative") | 10px | 700 | `#006B62` | uppercase |
| Question text | 18px | 600 | `#191C1E` | `line-height: 1.5` |
| Likert labels ("Strongly Disagree" → "Strongly Agree") | 10px | 600 | `#515F74`/`#FFFFFF` | uppercase |
| "Previous" button | 14px | 600 | `#515F74` | — |
| "Next" / "View My Results" button | 15px | 700 | `#FFFFFF` | — |
| AI panel label "AI Insight" | 9px | 700 | `#5A00C6` | uppercase, `letter-spacing: 0.1em` |
| AI panel body | 13px | 400 | `#25005A` | `line-height: 1.6` |
| Mobile AI pill codes (e.g. "I · C · E") | 10px | 700 | `#515F74` | — |

### 7. Spacing and Layout
- AppBar: `height: 52px`, sticky
- Progress bar: `height: 6px`, positioned `top: 52px` (just below AppBar), sticky — use `SliverPersistentHeader` or `Stack`
- Question card: `margin: EdgeInsets.fromLTRB(20, 20, 20, 0)`, `padding: EdgeInsets.all(24)`, `BorderRadius.circular(20)`, white bg, ambient shadow
- Likert buttons: `height: 52px` each, `BorderRadius.circular(12)`, full width, stacked with `8px` gap
- Nav row (Previous / Next): `padding: EdgeInsets.symmetric(horizontal:20, vertical:16)`
- AI insight panel (inline, below questions): `margin-top: 20px`, `padding: 18px 20px`, `BorderRadius.circular(16)`, `border-left: 4px solid #6616D7`
- Mobile AI pill (collapsed view, top-2 codes only): `height: 36px` row, `border-radius: 20px`, shown at bottom of screen above nav

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Progress bar | `LinearProgressIndicator` or custom `Container` | 0/60 → 60/60 | `value: currentQ / 60`, colour `#006B62` on `#E6E8EA` track |
| Question card | `AnimatedSwitcher` + `Card` | — | Slide animation between questions: `SlideTransition` |
| Likert buttons (×5) | `InkWell` + `Container` | unselected / selected / hover | Selected: `#006B62` bg, white text; Disabled when no selection + Next tapped |
| Dimension chip | `Container` | Static per question | `BorderRadius.circular(20)`, `padding: EdgeInsets.symmetric(horizontal:12, vertical:4)` |
| "Previous" button | `TextButton` | default / disabled (Q1) | Disabled on first question |
| "Next" button | `ElevatedButton` | default / disabled (no selection) | Disabled when `selectedAnswer == null` |
| "View My Results" gradient button | `ElevatedButton` with `Ink(decoration: BoxDecoration(gradient:...))` | default / loading | Only on Q60; gradient `#6616D7 → #7F3EF0` |
| AI Insight panel | `Container` | Static | Shown when AI has a contextual note for current dimension |
| Mobile AI pill strip | `Row` of chips | collapsed | Shows top-2 dimension codes; `overflow: hidden` |

### 9. Navigation Trigger
- "View My Results" on Q60 (after selecting answer) → `POST /api/v1/profile/riasec` → on success → `RiasecCompleteScreen`
- Back button → confirmation dialog ("Are you sure? Progress may be lost") → `LoginScreen` or dismiss

### 10. API Connection
`POST /api/v1/profile/riasec`  
Body: `{ "answers": [{ "question_id": int, "score": int (1-5) }] }` — full 60-answer array  
Response: `{ "onboarding_stage": "riasec_complete", "riasec_scores": { "R": int, "I": int, "A": int, "S": int, "E": int, "C": int } }`  
On success: store scores in `profileProvider`, navigate to `RiasecCompleteScreen`

### 11. State Management
- Local `StateNotifier` or `StateProvider` for: `currentQuestionIndex`, `answers: Map<int, int>`, `isSubmitting`
- On completion, `profileProvider.notifier.updateRiasec(scores)` is called

### 12. Platform Notes
- Android: Hardware back button should show confirmation dialog
- Flutter Web: Keyboard left/right arrow for Previous/Next; Enter to confirm selection

### 13. Flutter-Specific Notes
- Question content (60 questions with their dimension tags) must be bundled as a JSON asset file: `assets/riasec_questions.json` — do not fetch from backend for each question
- RIASEC raw scores: sum of responses per dimension (10 questions × 1–5 scale = 10–50 range). Demo locked values: `R=32, I=45, A=28, S=31, E=38, C=42` → percentages: `I=88%, C=80%, E=70%`
- `AnimatedSwitcher` key must change per question index for animation to trigger
- "Next" disabled state: use `ElevatedButton(onPressed: null, ...)` to get built-in disabled styling, then override colours via `ButtonStyle` to match design tokens

---

## Screen 07 — RIASEC Complete

### 1. Screen Name and Purpose
Displays the user's RIASEC personality profile results with a radar chart and top-3 dimension summary. Transitions to academic grades entry.

### 2. Flutter File Path
`lib/screens/onboarding/riasec_complete_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Radar chart primary axis/fill, top-dimension pills, "Continue" button |
| `#6616D7` | `tertiary` | Radar chart secondary axis, AI insight border-left, AI label icon |
| `#515F74` | `secondary` | Radar chart tertiary axis, pill labels, body text |
| `#EADDFF` | `tertiary-fixed` | AI insight panel background |
| `#5A00C6` | `on-tertiary-fixed-variant` | AI label text |
| `#25005A` | `on-tertiary-fixed` | AI insight body |
| `#FFFFFF` | `surface-container-lowest` | Results card |
| `#F2F4F6` | `surface-container-low` | Page background secondary sections |
| `#ECEEF0` | `surface-container` | Radar chart background |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Badge "RIASEC Profile Complete" | 9px | 700 | `#515F74` | uppercase, `letter-spacing: 0.1em` |
| Screen title | 28px | 700 | `#191C1E` | `letter-spacing: -0.02em` |
| Subtitle | 15px | 400 | `#515F74` | `line-height: 1.6` |
| Dimension pills (e.g. "Investigative · 88%") | 12px | 600 | `#006B62` | — |
| AI panel label | 9px | 700 | `#5A00C6` | uppercase |
| AI panel body | 13px | 400 | `#25005A` | `line-height: 1.6` |
| Radar axis labels | 10px | 600 | varies | R/I/A/S/E/C labels at chart vertices |

### 7. Spacing and Layout
- Hero celebration block: `text-align: center`, `margin-bottom: 32px`
- Icon container: `80×80px` circle, gradient `#006B62 → #00857A` at 135°, `BoxShadow(color: Color(0x4C006B62), blurRadius:32, offset:Offset(0,12))`
- Radar chart: `AspectRatio(aspectRatio: 1.0)` inside results card, `BorderRadius.circular(12)` on chart container
- Top-3 dimension pills row: `Wrap` with `gap: 8px`, `padding: EdgeInsets.symmetric(horizontal: 20)`
- AI insight panel: `margin-bottom: 32px`, same pattern as Quiz screen
- CTA button: full width, `padding: EdgeInsets.all(18)`, `BorderRadius.circular(16)`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Radar chart | `CustomPainter` | Static | Draws hexagonal axes, data polygon, vertex labels; `role="img"` → `Semantics(label: "RIASEC radar chart showing...")` |
| Dimension pills | `Container` chip row | Static | Top-3 from score sort: I, C, E for demo |
| AI Insight panel | `Container` | Static | Same pattern across all screens |
| "Continue to Academic Grades" | `ElevatedButton` | default / pressed | `BorderRadius.circular(16)` |

### 9. Navigation Trigger
"Continue to Academic Grades" → `GradesInputScreen`

### 10. API Connection
None — data already loaded in `profileProvider` from previous API call.

### 11. State Management
Reads `profileProvider.profile.riasecScores` to render radar chart and pills.

### 12. Platform Notes
No differences.

### 13. Flutter-Specific Notes
- Radar chart `CustomPainter`: draw 6-axis hexagon grid (3 concentric tiers), plot data polygon using score values normalized to 10–50 range, fill with `Color(0xFF006B62).withOpacity(0.15)`, stroke `#006B62`
- `Semantics(label: 'RIASEC radar chart. Top dimensions: Investigative 88%, Conventional 80%, Enterprising 70%')` for screen reader
- Locked demo scores: `R=32, I=45, A=28, S=31, E=38, C=42` → render these if `profileProvider` has no real scores yet

---

## Screen 08 — Grades Input (Academic Profile OCR)

### 1. Screen Name and Purpose
Collects the student's academic marks via camera OCR scan of a marksheet or manual entry. Second step of onboarding.

### 2. Flutter File Path
`lib/screens/onboarding/grades_input_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | "Scan Marksheet" button, "Save My Grades" button, focus accents, scan animation line |
| `#FFFFFF` | `on-primary` | Button text |
| `#F2F4F6` | `surface-container-low` | Input fill, dropdowns, step badge bg |
| `#FFFFFF` | `surface-container-lowest` | Form card, OCR preview card |
| `#515F74` | `secondary` | Labels, secondary icons, placeholder text |
| `#191C1E` | `on-surface` | Input values, table text |
| `#6616D7` | `tertiary` | AI instruction text in OCR overlay |
| `#EADDFF` | `tertiary-fixed` | OCR modal overlay tint |
| `rgba(247,249,251,0.80)` | `surface-bright` at 80% | Glassmorphism OCR modal background |
| `#E6E8EA` | `surface-container-high` | Table row alternating bg |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Step badge "Step 2 of 3" | 9px | 700 | `#515F74` | uppercase |
| Screen title "Academic Grades" | 28px | 700 | `#191C1E` | `letter-spacing: -0.02em` |
| Section subtitle | 14px | 400 | `#515F74` | — |
| "Scan Marksheet" button | 15px | 700 | `#FFFFFF` | — |
| Dropdown labels | 12px | 600 | `#515F74` | — |
| Subject table headers | 10px | 700 | `#515F74` | uppercase |
| Marks input values | 15px | 500 | `#191C1E` | — |
| "%" suffix | 13px | 400 | `#515F74` | right of marks input |
| OCR modal instruction | 13px | 400 | `#6616D7` | AI-purple for AI scanning instruction |

### 7. Spacing and Layout
- "Scan Marksheet" button: full width, `height: 56px`, `BorderRadius.circular(16)`, icon + text row
- Form card: `BorderRadius.circular(32)`, `padding: EdgeInsets.all(24)`
- Dropdown row: 2-column grid (`Expanded` × 2), `gap: 12px`
- Subject marks table: `Column` of rows, `padding: EdgeInsets.symmetric(vertical: 12)` per row, `border-bottom: 1px solid #F2F4F6` — exception to "no border" rule (accessibility divider at 15% opacity)
- Marks input field: `width: 72px`, right-aligned number, `TextInputType.number`
- OCR glassmorphism overlay: `BackdropFilter(filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20))`, background `rgba(247,249,251,0.80)`
- OCR modal: `BorderRadius.circular(20)`, centred, max `width: 340px`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| "Scan Marksheet" button | `ElevatedButton` | default / loading | `document_scanner` icon |
| Education Level dropdown | `DropdownButtonFormField` | default / open | Options: Matric, Inter Part 1, Inter Part 2, O Level, A Level |
| Year dropdown | `DropdownButtonFormField` | default | 2020–2026 |
| Stream dropdown | `DropdownButtonFormField` | default / hidden | Hidden for O/A Level; shown for Matric/Inter |
| Board dropdown | `DropdownButtonFormField` | default / hidden | Same hide condition as Stream |
| Subject marks fields | `TextFormField` | default / focused / error | `keyboardType: TextInputType.number`, range 0–100 |
| OCR camera overlay | `Stack` + `BackdropFilter` | active / scanning / complete | Scan line animation: `TweenAnimationBuilder` top→bottom, 2s loop |
| OCR result verification modal | `AlertDialog` or custom modal | — | `role="dialog"`, `aria-modal`, `aria-labelledby` |
| "Save My Grades" button | `ElevatedButton` | default / loading / disabled | Disabled until all required fields filled |

### 9. Navigation Trigger
- Successful grade submission (`POST /api/v1/profile/grades` → 200) → `GradesCompleteScreen`

### 10. API Connection
`POST /api/v1/profile/grades`  
Body: `{ "education_level": string, "year": int, "stream": string, "board": string, "subjects": [{ "name": string, "percentage": float }] }`  
Response: `{ "onboarding_stage": "grades_complete" }`

OCR Upload: `POST /api/v1/profile/grades/ocr`  
Body: `multipart/form-data` with `file` field (image)  
Response: pre-filled subject percentages for user to verify

### 11. State Management
- `profileProvider.notifier.submitGrades(gradesPayload)`
- OCR: local state only (`StatefulWidget`) for overlay visibility and parsed OCR result

### 12. Platform Notes
- Android: `image_picker` → `ImageSource.camera` for OCR scan
- Flutter Web: `image_picker` → file picker dialog (`kIsWeb` check); `dart:html` `FileUploadInputElement` as fallback
- Platform check pattern:
  ```dart
  if (kIsWeb) {
    final result = await ImagePicker().pickImage(source: ImageSource.gallery);
  } else {
    final result = await ImagePicker().pickImage(source: ImageSource.camera);
  }
  ```

### 13. Flutter-Specific Notes
- Stream/Board fields: wrap in `AnimatedCrossFade` or `Visibility(maintainState: true)` based on education level selection
- Subject list is dynamic based on stream: Pre-Engineering (Maths/Physics/Chemistry/English/CS), Pre-Medical (Bio/Chemistry/Physics/English/Urdu), General (varies)
- OCR glassmorphism: `BackdropFilter` only works if it has a non-transparent ancestor; wrap in `ClipRRect`
- Aggregate calculation: `(sum of percentages) / count` — shown live as user enters marks

---

## Screen 09 — Grades Complete

### 1. Screen Name and Purpose
Confirms academic marks have been saved. Displays a summary of captured grades and an AI insight before proceeding to capability assessment.

### 2. Flutter File Path
`lib/screens/onboarding/grades_complete_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Hero icon bg gradient start, progress bar fills (≥70%), button bg, aggregate number |
| `#00857A` | `primary-container` | Hero icon bg gradient end |
| `#515F74` | `secondary` | Step badge, card section label, "Marks Summary" label, aggregate label, progress bar fill (<70%), percentage text (<70%) |
| `#FFFFFF` | `surface-container-lowest` | Grades summary card |
| `#F2F4F6` | `surface-container-low` | Page bg, step badge bg, progress bar track, separator gradient |
| `#E6E8EA` | `surface-container-high` | Progress bar track |
| `#191C1E` | `on-surface` | Subject names, title text |
| `#EADDFF` | `tertiary-fixed` | AI insight bg |
| `#6616D7` | `tertiary` | AI insight border-left, `auto_awesome` icon |
| `#5A00C6` | `on-tertiary-fixed-variant` | AI label text |
| `#25005A` | `on-tertiary-fixed` | AI body text |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Step badge | 9px | 700 | `#515F74` | uppercase |
| Title "Academic Grades Captured" | 28px | 700 | `#191C1E` | `letter-spacing: -0.02em` |
| Subtitle | 15px | 400 | `#515F74` | `line-height: 1.6` |
| Card label "Marks Summary" | 10px | 700 | `#515F74` | uppercase |
| Board/stream chip | 11px | 600 | `#515F74` | — |
| Subject names | 14px | 500 | `#191C1E` | — |
| Percentage values | 14px | 700 | `#006B62` (≥70%) / `#515F74` (<70%) | — |
| "Overall Aggregate" label | 12px | 600 | `#515F74` | — |
| Aggregate value | 22px | 800 | `#006B62` | `letter-spacing: -0.02em` |
| "Continue" button | 15px | 700 | `#FFFFFF` | — |

### 7. Spacing and Layout
- Hero block: `text-align: center`, `margin-bottom: 32px`
- Icon container: `80×80px` circle, gradient, `BoxShadow(color: Color(0x4C006B62), blurRadius: 32, offset: Offset(0,12))`
- Grades card: `padding: EdgeInsets.all(24)`, `BorderRadius.circular(20)`, ambient shadow
- Per-subject row: `padding: EdgeInsets.symmetric(vertical: 12)`, separated by `Container(height: 1, color: Color(0xFFF2F4F6))`
- Progress bar per subject: `width: 80px, height: 4px`, `BorderRadius.circular(2)`
- Aggregate row: `margin-top: 16px`, `padding-top: 16px`, top gradient fade separator: `LinearGradient` from `#F2F4F6` → transparent
- AI insight: `margin-bottom: 32px`
- CTA button: `padding: EdgeInsets.all(18)`, `BorderRadius.circular(16)`, shadow `BoxShadow(color: Color(0x40006B62), blurRadius: 24, offset: Offset(0,8))`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Hero icon | `Container` + `Icon` | Static | `school` icon, FILL=1, `size: 40`, white |
| Subject rows | `ListView` (non-scrollable, `shrinkWrap: true`) | Static | — |
| Mini progress bar | `ClipRRect` + `LinearProgressIndicator` | Static | `value: percentage/100` |
| AI insight panel | `Container` | Static | Standard AI panel pattern |
| "Continue" button | `ElevatedButton` | default / pressed | — |

### 9. Navigation Trigger
"Continue to Capability Assessment" → `AssessmentScreen`

### 10. API Connection
None — data already in `profileProvider`.

### 11. State Management
Reads `profileProvider.profile.grades` to render subject list and calculate aggregate.

### 12. Platform Notes
No differences.

### 13. Flutter-Specific Notes
- Aggregate calculation: average of all subject percentages — `profileProvider` should expose a computed `aggregate` getter
- Colour logic for percentage: `percentage >= 70 ? Color(0xFF006B62) : Color(0xFF515F74)` for both bar fill and text
- English at 68% in demo → slate colour; all others → teal

---

## Screen 10 — Capability Assessment

### 1. Screen Name and Purpose
Administers 60 subject-knowledge MCQs across 5 subjects (12 per subject). Third and final onboarding assessment step.

### 2. Flutter File Path
`lib/screens/onboarding/assessment_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | Progress bar, selected option left-border, selected option letter badge, current question glow, subject tab active underline, "Submit" button |
| `#FFFFFF` | `on-primary` | Selected option letter badge text, button text |
| `#F2F4F6` | `surface-container-low` | Tab bar bg, question map cell default, page bg |
| `#FFFFFF` | `surface-container-lowest` | Question card, MCQ option rows |
| `#515F74` | `secondary` | Unselected tab text, question counter, option text (unselected), map legend text |
| `#191C1E` | `on-surface` | Question text, selected option text |
| `#E6E8EA` | `surface-container-high` | Progress bar track, review map cell |
| `#ECEEF0` | `surface-container` | Question map grid bg |
| `#006B62` at 10% opacity | — | Answered question map cell bg |
| `rgba(0,107,98,0.25)` | — | Current question glow `box-shadow` |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Subject tab labels | 13px | 600 | `#006B62` (active) / `#515F74` (inactive) | — |
| Question counter | 11px | 700 | `#515F74` | uppercase |
| Question text | 17px | 600 | `#191C1E` | `line-height: 1.5` |
| Option letter badge | 13px | 700 | `#006B62` (selected) / `#515F74` (unselected) | — |
| Option text | 14px | 400 | `#191C1E` | — |
| Map legend labels | 10px | 600 | `#515F74` | uppercase |
| "Submit Assessment" button | 15px | 700 | `#FFFFFF` | — |

### 7. Spacing and Layout
- AppBar: `height: 52px`, sticky
- Progress bar: `height: 6px`, sticky below AppBar
- Subject tabs: `ScrollableTabBar`, `overflow-x: scroll` with right fade gradient (`LinearGradient` `Positioned` overlay), `padding: EdgeInsets.symmetric(horizontal: 16)`
- Tab underline (active): `height: 3px`, `width: tab text width`, `BorderRadius.circular(2)`, colour `#006B62`
- Question card: `margin: EdgeInsets.fromLTRB(20, 16, 20, 0)`, `padding: EdgeInsets.all(20)`, `BorderRadius.circular(16)`
- MCQ option row: `padding: EdgeInsets.symmetric(horizontal: 16, vertical: 14)`, `BorderRadius.circular(12)`; selected: `border-left: 3px solid #006B62`, `background: rgba(0,107,98,0.05)`
- Letter badge: `32×32px`, `BorderRadius.circular(8)`
- Current question glow: `BoxDecoration(boxShadow: [BoxShadow(color: Color(0x40006B62), blurRadius: 0, spreadRadius: 2)])` — 2px outline glow
- Question map grid: 10-column grid, each cell `28×28px`, `BorderRadius.circular(6)`, `margin: 3px`
- Question map states: pending=`#F2F4F6`, answered=`#006B62` at 10% + teal text, current=white + teal border, review=`#E6E8EA`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Subject tabs | `TabBar` (scrollable) | active / inactive | Custom indicator; right fade: `ShaderMask` gradient |
| Progress bar | Custom `Container` fill | — | `value: answeredCount / 60` |
| Question card | `AnimatedSwitcher` | — | Transition between questions in same subject |
| MCQ option rows | `InkWell` + `Container` | unselected / selected / hover | `ListTile`-like layout; tap to select |
| Letter badge (A/B/C/D) | `Container` | unselected / selected | Circle/RoundedRect, colour toggles |
| Question map | `GridView` of `InkWell` buttons | pending / answered / current / review | `button` semantics per cell |
| "Mark for Review" toggle | `IconButton` or `Checkbox` | on / off | Changes map cell to review state |
| "Submit Assessment" | `ElevatedButton` | default / disabled / loading | Disabled until all 60 answered |

### 9. Navigation Trigger
- "Submit Assessment" (all 60 answered) → `POST /api/v1/profile/assessment` → on success → `AssessmentCompleteScreen`
- Back: confirmation dialog (progress persists locally until submit)

### 10. API Connection
`POST /api/v1/profile/assessment`  
Body:
```json
{
  "responses": {
    "mathematics": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1],
    "physics":     [1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 1, 0],
    "chemistry":   [0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
    "biology":     [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    "english":     [1, 1, 1, 0, 1, 0, 1, 1, 0, 1, 0, 1]
  }
}
```
Each subject has exactly 12 integers: `1` = correct, `0` = incorrect. Order matches the question sequence delivered to the student.  
Response: `{ "onboarding_stage": "assessment_complete", "capability_scores": { "mathematics": float, "physics": float, "chemistry": float, "biology": float, "english": float } }`

**⚠️ Note for Khuzzaim:** The local `answers` state (`Map<int, String>`) must be converted before submission. Map the student's A/B/C/D selections against `correct_index` from the bundled JSON to produce the 0/1 list per subject. The backend expects binary flags, not letter options.

**Note for Khuzzaim:** No `GET` endpoint for assessment questions exists yet. Bundle questions as `assets/assessment_questions.json` until backend provides `GET /api/v1/profile/assessment/questions`.

### 11. State Management
- Local state: `currentSubject`, `currentQuestionIndex`, `answers: Map<int, String>`, `reviewFlags: Set<int>`
- On submit: convert local `Map<int, String> answers` to `Map<String, List<int>>` per subject (1=correct, 0=incorrect), then call `profileProvider.notifier.submitAssessment(responses)`

### 12. Platform Notes
- Android: Hardware back → confirmation dialog
- Flutter Web: keyboard A/B/C/D hotkeys for option selection

### 13. Flutter-Specific Notes
- `ScrollableTabBar` right-fade: `ShaderMask(shaderCallback: (rect) => LinearGradient(colors: [Colors.white, Colors.transparent], begin: Alignment.centerLeft, end: Alignment.centerRight).createShader(rect))` wrapped around right edge of tab bar
- Question map: use `GridView.builder(gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(crossAxisCount: 10))` with `28px` fixed item size
- Each map cell must be a `button` semantics node: `Semantics(button: true, label: 'Question ${n}, ${state}')`
- Answer state is held locally until final submit — do not call API per question

---

## Screen 11 — Assessment Complete

### 1. Screen Name and Purpose
Confirms all three onboarding assessments are done. Shows a 3-pillar summary and automatically navigates to Chat after 3 seconds via animated progress bar.

### 2. Flutter File Path
`lib/screens/onboarding/assessment_complete_screen.dart`

### 3. Sprint
Sprint 2

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#6616D7` | `tertiary` | Pulsing ring animation, `auto_awesome` icon, summary icon for AI pillar |
| `#EADDFF` | `tertiary-fixed` | Icon container bg, pulsing ring colour |
| `#006B62` | `primary` | Auto-navigate progress bar fill, RIASEC pillar icon, Grades pillar icon |
| `#F2F4F6` | `surface-container-low` | Progress bar track, pillar cards bg |
| `#515F74` | `secondary` | Pillar labels, body text, countdown text |
| `#191C1E` | `on-surface` | Title text |
| `#FFFFFF` | `surface-container-lowest` | Page bg sections |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Badge "Profile Complete" | 9px | 700 | `#515F74` | uppercase |
| Title "You're Ready" (or equivalent) | 28px | 700 | `#191C1E` | `letter-spacing: -0.02em` |
| Subtitle | 15px | 400 | `#515F74` | `line-height: 1.6` |
| Pillar labels | 12px | 700 | `#515F74` | uppercase |
| Pillar values | 14px | 600 | `#191C1E` | — |
| "Taking you to your results…" | 13px | 400 | `#515F74` | below progress bar |
| Auto-redirect status | 13px | 400 | `#515F74` | `role="status"`, `aria-live="polite"` |

### 7. Spacing and Layout
- Full-screen centred: `Column(mainAxisAlignment: MainAxisAlignment.center)`
- Pulsing icon container: `96×96px`, `BorderRadius.circular(48)` (circle), bg `#EADDFF`
- Pulsing ring: `Stack` with outer `AnimatedContainer` expanding `96→120px` over 1.5s loop, opacity 0→0
- 3-pillar row: `Row` of 3 `Expanded` cards, `gap: 12px`, `margin: EdgeInsets.symmetric(horizontal: 20)`
- Auto-nav progress bar: `height: 6px`, full width, fills over exactly 3 seconds
- `margin-top: 24px` above progress bar

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Pulsing ring | `AnimationController` (repeat) + `ScaleTransition` + `FadeTransition` | looping | `duration: Duration(milliseconds: 1500)`, `Curves.easeOut` |
| `auto_awesome` icon | `Icon` | Static | FILL=1, size 40, colour `#6616D7` |
| 3-pillar cards | `Container` row | Static | `BorderRadius.circular(16)`, `padding: EdgeInsets.all(16)` |
| Auto-nav progress bar | `TweenAnimationBuilder<double>` | 0.0 → 1.0 over 3s | `onEnd: () => Navigator.pushReplacement(...)` |
| Status announcement | `Semantics(liveRegion: true)` | — | Announces "Navigating to results" |

### 9. Navigation Trigger
**No button.** `TweenAnimationBuilder` `onEnd` callback → `Navigator.pushReplacement(context, MaterialPageRoute(builder: (_) => MainChatScreen()))` after 3-second fill completes.

### 10. API Connection
`POST /api/v1/profile/assessment/complete` (if exists) or none — `onboarding_stage` already updated by previous screen's submit call. If backend sets `assessment_complete` in the assessment submit response, no additional call needed here.

### 11. State Management
`profileProvider.notifier.markAssessmentComplete()` if a separate endpoint exists; otherwise reads existing state.

### 12. Platform Notes
No differences. Ensure `Future.delayed` fallback if animation callback doesn't fire on web.

### 13. Flutter-Specific Notes
- **No back button** — use `WillPopScope(onWillPop: () async => false)` to prevent hardware back during the 3-second countdown
- Use `AnimationController` with `addStatusListener` to detect `AnimationStatus.completed` for navigation, not `Timer`
- Progress bar must use `Curves.linear` — no easing — for the 3-second fill

---

## Screen 12 — Chat Screen

### 1. Screen Name and Purpose
Primary AI conversation interface. Student sends messages; AI responds with SSE-streamed tokens. First meaningful screen post-onboarding.

### 2. Flutter File Path
`lib/screens/chat/main_chat_screen.dart`

### 3. Sprint
Sprint 1 (shell/static) — Sprint 2 (live SSE streaming)

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | AppBar background, send button, student bubble bg, thinking dot (tertiary for dots — see below) |
| `#FFFFFF` | `on-primary` | AppBar icons/text, student bubble text, send button icon |
| `#F7F9FB` | `surface` | Chat background |
| `#FFFFFF` | `surface-container-lowest` | AI bubble background |
| `#F2F4F6` | `surface-container-low` | Suggested chips bg, input bar area bg |
| `#515F74` | `secondary` | AI avatar border, chip text, input placeholder, AI name text |
| `#191C1E` | `on-surface` | AI bubble text, input text |
| `#6616D7` | `tertiary` | AI bubble left-border (3px), thinking indicator dots, `auto_awesome` in header |
| `#EADDFF` | `tertiary-fixed` | Thinking indicator dot bg |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| AppBar title "AI Advisor" | 16px | 700 | `#FFFFFF` | — |
| AppBar subtitle "Online · Ready" | 11px | 400 | `rgba(255,255,255,0.75)` | — |
| Student bubble text | 15px | 400 | `#FFFFFF` | `line-height: 1.5` |
| AI bubble text | 15px | 400 | `#191C1E` | `line-height: 1.6` |
| Suggested chip text | 13px | 500 | `#515F74` | — |
| Input placeholder | 15px | 400 | `#515F74` | — |
| Input text | 15px | 400 | `#191C1E` | — |
| Timestamp (if shown) | 11px | 400 | `#515F74` at 60% | — |

### 7. Spacing and Layout
- AppBar: `height: 52px`, `background: #006B62`, sticky
- Chat list: `ListView.builder` (reverse: false), `padding: EdgeInsets.fromLTRB(16, 12, 16, 0)`
- Student bubble: `border-radius: 18px 18px 4px 18px` → Flutter: `BorderRadius.only(topLeft: 18, topRight: 18, bottomLeft: 18, bottomRight: 4)` — right-aligned, `max-width: 75%`
- AI bubble: `border-radius: 18px 18px 18px 4px`, `border-left: 3px solid #6616D7` — left-aligned, `max-width: 85%`
- AI bubble left-border: `Container(decoration: BoxDecoration(border: Border(left: BorderSide(color: Color(0xFF6616D7), width: 3))))` 
- Gap between message groups: `16px`; within a group: `4px`
- Suggested chips: `SingleChildScrollView(scrollDirection: Axis.horizontal)`, `padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8)`, `gap: 8px`
- Input bar: `padding: EdgeInsets.fromLTRB(16, 8, 16, 16)` + `SafeArea` bottom
- Input field: `BorderRadius.circular(24)`, `padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12)`, bg `#F2F4F6`
- Send button: `48×48px` circle, `#006B62` bg

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| AppBar | `AppBar` | static / streaming (subtitle changes) | `backgroundColor: Color(0xFF006B62)` |
| AI avatar | `CircleAvatar` | — | `radius: 16`, `smart_toy` icon, `#515F74` |
| Student bubble | `Container` | default | Right-aligned `Row` with `Spacer` |
| AI bubble | `Container` | default / streaming | Streaming: text builds character by character via `chatProvider` |
| Thinking indicator | 3× bouncing dots | visible / hidden | Each dot: `8×8px` circle, `#6616D7`, staggered `TweenAnimationBuilder` bounce |
| Suggested chips | `TextButton` chips | default / pressed | `BorderRadius.circular(20)`, `padding: EdgeInsets.symmetric(horizontal:16, vertical:12)` |
| Input field | `TextField` | default / focused | `maxLines: null` (expands), `textInputAction: TextInputAction.newline` |
| Send button | `IconButton` in `CircleAvatar` | default / disabled | Disabled when input empty or `isStreaming` |
| Message group | `Semantics(container: true, label: '...')` | — | `role="group"` per student+AI exchange |

### 9. Navigation Trigger
- Bottom nav: Chat (current), Dashboard, Settings
- Dashboard icon → `RecommendationDashboard`
- Settings icon → `SettingsScreen`
- No automatic navigation away from Chat

### 10. API Connection
`POST /api/v1/chat/stream` (SSE)  
Body: `{ "session_id": string, "message": string }`  
`session_id` from `profileProvider.profile.sessionId` — never generate client-side  
SSE event types: `status`, `chunk`, `rich_ui`  
- `status`: update `chatProvider.thinkingLabel` (e.g. "Thinking…", "Searching universities…")
- `chunk`: append to current AI bubble via `chatProvider.appendChunk(text)`
- `rich_ui`: render structured card (university card, etc.)
- On `[DONE]`: set `chatProvider.isStreaming = false`
- On 401: clear token, navigate to `LoginScreen`

### 11. State Management
- `chatProvider`: `messages: List<ChatMessage>`, `isStreaming: bool`, `thinkingLabel: String?`
- `chatProvider.notifier.sendMessage(message, sessionId)` opens SSE stream
- `profileProvider`: read `sessionId` from here

### 12. Platform Notes
- Android: `resizeToAvoidBottomInset: true` on `Scaffold` for keyboard push-up; `ScrollController.animateTo(maxScrollExtent)` after each new message
- Flutter Web: SSE via `http` package works; verify CORS headers from backend allow web origin

### 13. Flutter-Specific Notes
- SSE parsing pattern:
  ```dart
  final request = http.Request('POST', Uri.parse('$kBaseUrl/api/v1/chat/stream'));
  request.headers['Authorization'] = 'Bearer $token';
  request.headers['Content-Type'] = 'application/json';
  request.body = jsonEncode({'session_id': sessionId, 'message': message});
  final streamedResponse = await client.send(request);
  streamedResponse.stream.transform(utf8.decoder).transform(const LineSplitter()).listen((line) {
    if (line.startsWith('data: ')) { /* parse JSON */ }
  });
  ```
- Use `http` package only — NOT `dio` — per architecture decision
- Thinking indicator: show when `chatProvider.isStreaming && chatProvider.messages.last.isAI && chatProvider.messages.last.text.isEmpty`
- `ListView` should auto-scroll: `WidgetsBinding.instance.addPostFrameCallback((_) => _scrollController.animateTo(...))`
- `ChatMessage` model needs: `id`, `text`, `isUser`, `isStreaming`, `timestamp`

---

## Screen 13 — Recommendation Dashboard

### 1. Screen Name and Purpose
Displays AI-ranked university/degree recommendations with match scores, merit tiers, and AI-insight badges. Main post-onboarding destination.

### 2. Flutter File Path
`lib/screens/dashboard/recommendation_dashboard.dart`

### 3. Sprint
Sprint 3

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | AppBar, match score bars, rank badge, "Ask about this" button text, tab underline |
| `#FFFFFF` | `on-primary` | AppBar text/icons, rank badge text |
| `#F7F9FB` | `surface` | Page background |
| `#FFFFFF` | `surface-container-lowest` | University cards |
| `#F2F4F6` | `surface-container-low` | Card secondary bg, bottom nav bg |
| `#515F74` | `secondary` | University names, body text, merit labels, "More Details" button |
| `#191C1E` | `on-surface` | Degree names, card titles |
| `#6616D7` | `tertiary` | FutureValue badge border, AI insight elements |
| `#EADDFF` | `tertiary-fixed` | FutureValue badge bg, AI flags bg |
| `#FFF8E1` | — | Mismatch notice banner bg (amber-tinted) |
| `#F59E0B` | — | Mismatch notice border-left, alert icon |
| `#E6E8EA` | `surface-container-high` | Match score bar track, bottom nav active indicator |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| AppBar title | 16px | 700 | `#FFFFFF` | — |
| Mismatch banner text | 13px | 400 | `#191C1E` | `line-height: 1.5` |
| University name | 15px | 700 | `#191C1E` | — |
| Degree programme | 13px | 400 | `#515F74` | — |
| Match score % | 14px | 700 | `#006B62` | — |
| Merit tier badge | 10px | 700 | varies | "High Merit" / "Good Match" etc, uppercase |
| Rank badge "#1" | 13px | 700 | `#FFFFFF` on `#006B62` | — |
| FutureValue badge text | 10px | 700 | `#6616D7` | uppercase |
| "Ask about this" button | 13px | 600 | `#006B62` | ghost button |
| "More Details" button | 13px | 600 | `#515F74` | ghost button |
| AI flag text | 11px | 600 | `#6616D7` | — |
| Bottom nav labels | 11px | 600 | `#006B62` (active) / `#515F74` (inactive) | — |

### 7. Spacing and Layout
- AppBar: `height: 52px`, `background: #006B62`
- Mismatch banner: `margin: EdgeInsets.fromLTRB(16, 16, 16, 0)`, `padding: EdgeInsets.all(16)`, `BorderRadius.circular(12)`, `border-left: 4px solid #F59E0B`, bg `#FFF8E1`
- University card: `margin: EdgeInsets.fromLTRB(16, 12, 16, 0)`, `padding: EdgeInsets.all(20)`, `BorderRadius.circular(20)`, ambient shadow
- Rank badge: `32×32px`, `BorderRadius.circular(8)`, top-left of card content
- Match score bar: `height: 6px`, `BorderRadius.circular(3)`, `width: double.infinity`
- Card action row: `padding-top: 12px`, `Divider` at 15% opacity, `Row(mainAxisAlignment: MainAxisAlignment.spaceBetween)`
- Bottom nav: `height: 64px + safeAreaBottom`, `background: #FFFFFF`, shadow `BoxShadow(color: Color(0x0F334155), blurRadius: 16, offset: Offset(0,-4))`
- Filter chips row (if present): `SingleChildScrollView(horizontal)`, above card list

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| AppBar | `AppBar` | static | `#006B62` background |
| Mismatch banner | `Container` | visible / hidden | Shown when AI detects profile-programme mismatch |
| University card | `Card` / `Container` | default / hover | `InkWell` wrapper for tap |
| Rank badge | `Container` | — | Absolute-positioned top-left |
| Match score bar | `LinearProgressIndicator` | — | `value: matchScore / 100` |
| Merit tier badge | `Container` chip | high / medium / low | Colour varies by tier |
| FutureValue badge | `Container` chip | — | `#EADDFF` bg, `#6616D7` border, purple text |
| Soft flags row | `Wrap` of `Container` chips | — | AI-generated flags; purple accents |
| "Ask about this" | `TextButton` | — | Navigates to Chat with pre-filled query |
| "More Details" | `TextButton` | — | Navigates to detail sheet or Chat |
| Bottom nav | `BottomNavigationBar` or custom | active / inactive | 3 items: Chat, Dashboard (current), Settings |

### 9. Navigation Trigger
- "Ask about this" → `MainChatScreen` with pre-filled message about that university
- Bottom nav items → respective screens
- Dashboard tab is current (do not push, use `IndexedStack`)

### 10. API Connection
`GET /api/v1/recommendations`  
Headers: `Authorization: Bearer <jwt_token>`  
Response: `{ "recommendations": [{ "university": string, "programme": string, "match_score": float, "merit_tier": string, "future_value": string, "flags": [string], "rank": int }] }`

**Note:** `mismatch_notice` field: if the backend sends this in the recommendations response or via a `rich_ui` SSE event, render the amber banner. Check with backend team which delivery mechanism is used.

### 11. State Management
`profileProvider` or a dedicated `recommendationsProvider` (StateNotifier) that loads `GET /api/v1/recommendations` on screen init.

### 12. Platform Notes
- Android: `RefreshIndicator` for pull-to-refresh
- Flutter Web: Ensure cards are scrollable without momentum physics issues; use `BouncingScrollPhysics` on Android, `ClampingScrollPhysics` on Web

### 13. Flutter-Specific Notes
- `thought_trace` panel (if visible in mockup): backend has no endpoint yet — show `Visibility(visible: false)` for now
- Bottom nav: use `button` or `a` semantics, `min-height: 48px` per item
- University cards should be `ListView.builder` (not `Column`) for performance when list grows
- "Ask about this" should pass context to Chat: `chatProvider.notifier.preFillMessage('Tell me more about [University] [Programme]')`

---

## Screen 14 — Student Profile Dashboard

### 1. Screen Name and Purpose
Displays the student's complete academic profile: name, RIASEC scores, subject grades, and capability assessment results. Read-only view of captured data.

### 2. Flutter File Path
`lib/screens/profile/profile_screen.dart`

### 3. Sprint
Sprint 4 (not in locked 15-screen Sprint 3 scope)

### 4. Demo Status
Layout only — static data, no edit functionality.

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | AppBar, RIASEC bars, grade bar fills, profile avatar bg gradient |
| `#00857A` | `primary-container` | Gradient end |
| `#515F74` | `secondary` | Section labels, metadata text, table secondary text |
| `#191C1E` | `on-surface` | Student name, subject names, primary values |
| `#FFFFFF` | `surface-container-lowest` | Cards |
| `#F2F4F6` | `surface-container-low` | Page bg, table alternate rows |
| `#6616D7` | `tertiary` | RIASEC dimension highlight for top codes |
| `#EADDFF` | `tertiary-fixed` | Top RIASEC dimension pill bg |

### 6. Typography
| Element | Size | Weight | Colour |
|---------|------|--------|--------|
| Student name | 22px | 700 | `#191C1E` |
| Education subtitle | 14px | 400 | `#515F74` |
| Section headers | 12px | 700 | `#515F74` | uppercase |
| RIASEC dimension labels | 13px | 600 | `#191C1E` |
| RIASEC percentages | 13px | 700 | `#006B62` |
| Subject names | 14px | 500 | `#191C1E` |
| Grade values | 14px | 700 | `#006B62` |
| Capability scores | 14px | 700 | `#006B62` |

### 7. Spacing and Layout
- Hero section: avatar `80×80px` circle with gradient, name + subtitle below
- Card sections: `BorderRadius.circular(20)`, `padding: EdgeInsets.all(20)`, ambient shadow, `margin-bottom: 16px`
- RIASEC bar rows: `padding: EdgeInsets.symmetric(vertical: 8)`, `16px` gap between items
- Grades table: `Column` of rows, alternating bg
- Padding: `EdgeInsets.symmetric(horizontal: 20)`

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Avatar | `CircleAvatar` with gradient `Container` | Static | Initials fallback if no photo |
| RIASEC bars | `LinearProgressIndicator` | Static | `value: score / 50` (max raw score) |
| Grades table | `Column` of `Row` | Static | — |
| Capability bars | `LinearProgressIndicator` | Static | `value: score / 100` |

### 9. Navigation Trigger
- Back button → previous screen (Dashboard or Settings)

### 10. API Connection
`GET /api/v1/profile/me` — reads existing `profileProvider` data. No additional call if already loaded.

### 11. State Management
Reads `profileProvider.profile` — all fields already loaded.

### 12. Platform Notes
No differences.

### 13. Flutter-Specific Notes
- This screen is Sprint 4 — implement after all Sprint 1–3 screens are verified
- Demo persona: Ali Raza Khan, Inter Part 2, Pre-Engineering, Karachi Board
- Static data acceptable for mid-evaluation demo

---

## Screen 15 — Settings & Security

### 1. Screen Name and Purpose
Account settings screen. Shows security options and a functional Sign Out button. Change Password is deferred (static "coming soon").

### 2. Flutter File Path
`lib/screens/profile/settings_screen.dart`

### 3. Sprint
Sprint 3

### 4. Demo Status
Logout only functional. Change Password = static coming soon.

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#006B62` | `primary` | AppBar, active checkboxes, section accent |
| `#F7F9FB` | `surface` | Page background |
| `#FFFFFF` | `surface-container-lowest` | Settings cards |
| `#F2F4F6` | `surface-container-low` | Bottom nav bg, input fill |
| `#E0E3E5` | `surface-container-highest` | "Sign Out" button background |
| `#515F74` | `secondary` | Section labels, metadata, "Sign Out" button text, checkbox labels, bottom nav inactive icons |
| `#191C1E` | `on-surface` | Setting item labels |
| `#E6E8EA` | `surface-container-high` | Divider between sections (15% opacity only) |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| AppBar title "Settings" | 16px | 700 | `#FFFFFF` | — |
| Section headers | 11px | 700 | `#515F74` | uppercase, `letter-spacing: 0.08em` |
| Setting item labels | 15px | 500 | `#191C1E` | — |
| "Coming soon" text (Change Password) | 13px | 400 | `#515F74` | No button — just text |
| "Sign Out" button | 15px | 600 | `#515F74` | NOT red — neutral surface styling |
| Bottom nav labels | 11px | 600 | active: `#006B62`, inactive: `#515F74` | — |

### 7. Spacing and Layout
- Settings card: `padding: EdgeInsets.all(20)`, `BorderRadius.circular(20)`, ambient shadow
- Section separation: `margin-bottom: 20px` between cards, NO 1px border between sections
- Checkbox rows: `padding: EdgeInsets.symmetric(vertical: 12)`, `Row` with `Expanded` label + `Checkbox`
- "Sign Out" button: full width, `height: 52px`, `BorderRadius.circular(14)`, bg `#E0E3E5`, NO shadow
- Bottom nav: same as Dashboard

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Profile summary row | `Row` with `CircleAvatar` | Static | Shows name + email from `profileProvider` |
| Notification checkboxes | `CheckboxListTile` | checked / unchecked | `h-6 w-6`, `activeColor: Color(0xFF006B62)` |
| Change Password row | `ListTile` with trailing "Coming soon" text | Static | No `onTap` — no navigation |
| "Sign Out" button | `TextButton` or `ElevatedButton` | default / loading | `#E0E3E5` bg, `#515F74` text — NEVER red |
| Bottom nav | `BottomNavigationBar` | — | Same 3-item nav as Dashboard |

### 9. Navigation Trigger
- "Sign Out":
  1. Clear `flutter_secure_storage` key `'jwt_token'`
  2. `ref.invalidate(authProvider)` and `ref.invalidate(profileProvider)`
  3. `Navigator.pushAndRemoveUntil(context, LoginScreen, (route) => false)`
- No API call for logout — client-side only
- Bottom nav → Dashboard or Chat

### 10. API Connection
None. Logout is client-side only.

### 11. State Management
- `authProvider.notifier.logout()` → clears storage + invalidates providers
- `profileProvider`: read for profile display

### 12. Platform Notes
No differences. On web, `flutter_secure_storage` uses `localStorage` fallback — verify this is acceptable for the token.

### 13. Flutter-Specific Notes
- 2FA toggle: removed — no backend endpoint. Do not implement
- "Ghost nav items" (items with no backend): removed. Only show: Profile summary, Notifications, Security (Change Password coming soon), Sign Out
- Logout `Navigator.pushAndRemoveUntil` clears the entire navigation stack — user cannot press back to return to app
- Change Password: render as a `ListTile` with trailing `Text('Coming soon', style: TextStyle(color: Color(0xFF515F74), fontSize: 13))` — no `onTap`

---

## Screen 16 — Network Error Screen

### 1. Screen Name and Purpose
Full-screen error display shown when network, server, or auth failures occur. Three distinct states: No Internet, Server Timeout, Session Expired.

### 2. Flutter File Path
`lib/screens/error_screen.dart`

### 3. Sprint
Sprint 3

### 4. Demo Status
Full

### 5. Colour Tokens
| Hex | Token | Element |
|-----|-------|---------|
| `#F7F9FB` | `surface` | State 1 background |
| `#F2F4F6` | `surface-container-low` | State 2 background, icon container bg, error code badge bg |
| `#515F74` | `secondary` | All icons (all 3 states), error code text, ghost button text, body text |
| `#006B62` | `primary` | Primary action buttons ("Try Again", "Retry", "Sign In") |
| `#FFFFFF` | `on-primary` | Primary button text/icons |
| `#191C1E` | `on-surface` | Error title text |
| `#E6E8EA` | `surface-container-high` | Error code badge bg (alternate) |

### 6. Typography
| Element | Size | Weight | Colour | Notes |
|---------|------|--------|--------|-------|
| Error code badge | 11px | 700 | `#515F74` | uppercase, `letter-spacing: 0.12em` |
| Error title | 24px | 700 | `#191C1E` | `letter-spacing: -0.02em`, `line-height: 1.25` |
| Error body | 14px | 400 | `#515F74` | `line-height: 1.65`, `max-width: 280px` |
| Primary button | 14px | 700 | `#FFFFFF` | — |
| Ghost button | 13px | 600 | `#515F74` | — |

### 7. Spacing and Layout
- Full screen: `Column(mainAxisAlignment: MainAxisAlignment.center)`, `padding: EdgeInsets.symmetric(horizontal: 32, vertical: 48)`
- Icon container: `80×80px` circle, bg `#F2F4F6`, icon `36px`
- Gap: icon → badge `24px`; badge → title `16px`; title → body `10px`; body → primary button `32px`; primary → ghost `12px`
- Primary button: `max-width: 280px`, `height: 52px`, `BorderRadius.circular(14)`, shadow `BoxShadow(color: Color(0x38006B62), blurRadius: 20, offset: Offset(0,6))`
- Ghost button: `min-height: 48px`, no background, no border

### 8. Components
| Component | Flutter Widget | States | Notes |
|-----------|---------------|--------|-------|
| Error container | `Semantics(container: true, liveRegion: true)` | — | `role="alert"` equivalent |
| Icon container | `Container` + `Icon` | — | `wifi_off` / `cloud_off` / `lock`, FILL=1 |
| Error code badge | `Container` chip | Static | — |
| Primary action button | `ElevatedButton` | default / loading | — |
| Ghost "Go to Home" button | `TextButton` | default | — |
| Dev annotation | `Text` with `Visibility(visible: kDebugMode)` | dev only | "Dev: clears flutter_secure_storage..." |

### 9. Navigation Trigger
- **State 1 (No Internet):** "Try Again" → retry last failed request; "Go to Home" → Dashboard or Login based on auth state
- **State 2 (Server Timeout):** "Retry" → same retry logic; "Go to Home" → same
- **State 3 (Session Expired 401):**
  1. Clear `flutter_secure_storage` key `'jwt_token'`
  2. Invalidate providers
  3. "Sign In" → `LoginScreen`
  4. No "Go to Home" ghost button for State 3

### 10. API Connection
None on this screen. Error screen receives its `ErrorType` via constructor/route arguments.

### 11. State Management
- Route argument: `ErrorType` enum (`noNetwork`, `serverTimeout`, `sessionExpired`)
- On State 3: calls `authProvider.notifier.logout()` to clear storage before navigating

### 12. Platform Notes
- Android: `Connectivity` package to detect `wifi_off` vs `cloud_off` distinction
- Flutter Web: `dart:html` `window.navigator.onLine` for connectivity check

### 13. Flutter-Specific Notes
- Implement as: `ErrorScreen(errorType: ErrorType.noNetwork)` — a single screen with 3 presentation modes driven by the constructor parameter
- `ErrorType` enum:
  ```dart
  enum ErrorType { noNetwork, serverTimeout, sessionExpired }
  ```
- Sprint label "Sprint 3" dev annotation: `kDebugMode` guard
- Dev annotation "3 states shown" badge: remove in prod; in dev show `Positioned` `top:8, right:8` chip
- The screen must be `role="alert"` → wrap entire content in `Semantics(container: true, liveRegion: true)`

---

## LOCKED DECISIONS SUMMARY

These decisions from `CLAUDE.md` directly affect Flutter implementation. Every item below is non-negotiable.

| Decision | What Khuzzaim Must Do |
|----------|----------------------|
| Single codebase: Android + Flutter Web | Use `kIsWeb` checks only for platform-specific behaviour (OCR picker, connectivity). All UI code is shared. |
| State management: Riverpod `^2.5.1` | Use `StateNotifierProvider` pattern only. No `ChangeNotifier`, no `GetX`, no `BLoC`. |
| Three providers: `authProvider`, `profileProvider`, `chatProvider` | Do not add new top-level providers without architecture review. |
| HTTP: `http` package only | Do NOT use `dio`. SSE streaming requires `http.Request` + `streamedResponse.stream`. |
| JWT storage: `flutter_secure_storage` only | Key: `'jwt_token'`. Never use `SharedPreferences` or in-memory only storage for the token. |
| Base URL constant | `const String kBaseUrl = 'http://127.0.0.1:8000';` in `lib/constants.dart` |
| `session_id` is server-generated | Read from `profileProvider.profile?.sessionId`. Never generate on client. |
| SSE event types: `status`, `chunk`, `rich_ui` ONLY | Ignore any other event types. Do not crash on unknown events — log and skip. |
| 401 handling | Clear `flutter_secure_storage`, invalidate providers, navigate to `LoginScreen`. No silent token refresh. |
| Logout: client-side only | Clear storage + invalidate providers. No `POST /logout` API call. |
| Onboarding state machine (4 values) | `not_started` → `riasec_complete` → `grades_complete` → `assessment_complete`. Match exact strings. `complete` is NOT a valid stage — it was a design doc error. Terminal stage is `assessment_complete`. |
| Font: Inter only | Use `google_fonts` package: `GoogleFonts.inter(...)`. No system fonts, no other Google Fonts. |
| Colour: Purple (`#6616D7`) on AI elements only | `tertiary` colour must NEVER appear on non-AI UI elements under any circumstance. |
| No 1px solid borders | Use background colour shifts for section separation. `Divider` widget forbidden except with `thickness: 0, color: Color(0x26BDC9C6)` for ghost separators. |
| Shadow token | `BoxShadow(color: Color(0x0F334155), blurRadius: 40, offset: Offset(0, 12))` for all floating elements. No high-intensity shadows. |
| Border radius scale | Form cards: `32px`, buttons: `12–16px`, chat bubbles: custom `BorderRadius.only(...)`, chips: `20px`, inputs: `12px`, modals: `20px`. |
| AppBar | `height: 52px`, sticky (`pinned: true` in `SliverAppBar`). |
| RIASEC: 60 questions, 5-point Likert | Bundle as JSON asset. Raw score range: 10–50 per dimension. |
| Capability: 60 MCQs, 5 subjects, 12 each | Bundle as JSON asset. |
| Assessment Complete: no button | Auto-navigate after 3-second progress bar. `WillPopScope` blocks back. |
| Error screen: 3 states | `wifi_off`, `cloud_off`, `lock` — exact Material Symbols icons. |
| Typography tracking | Display text: `letterSpacing: -0.02em`; labels/badges: `letterSpacing: 0.08–0.12em` + `TextTransform.uppercase` (use `toUpperCase()` in Dart); body: `height: 1.6`. |
| Minimum body font size on mobile | `13px` — never go below this for any readable text. |
| Viewport | `390px` mobile equivalent. Flutter uses `BoxConstraints` — `max-width: 390px` not needed as Flutter fills the screen natively. |
| `image_picker` platform check | `if (kIsWeb) { ImageSource.gallery } else { ImageSource.camera }` |
| Sprint label (dev annotation) | Show in `kDebugMode` only. Position: top-left, fixed, `z-index: 200` equivalent (`Material` with high `elevation` or `Overlay`). |
| Student demo persona | Name: Ali Raza Khan, Education: Inter Part 2 Pre-Engineering Karachi Board, Budget: PKR 25,000–45,000/month, Location: Karachi. Use across all static/demo screens. |
| RIASEC demo scores | R=32, I=45, A=28, S=31, E=38, C=42 → I=88%, C=80%, E=70%. |
| Error states: neutral slate ONLY | Never use `#BA1A1A` error-red on logout, settings, or non-destructive actions. Red only for destructive confirmation dialogs. |
| Forgot Password, Change Password | Static "coming soon" UI. No form, no API call, no email field. |
| Google SSO | Implement with `google_sign_in` package. ORCID and GitHub SSO are removed — do not add. |
| Message history persistence | Deferred. Chat does not persist history between sessions. |
| SSE timeout handling | Deferred. No timeout timer in Sprint 2. |

---

## DEFERRED FEATURES

Features visible in the HTML mockups that have no backend endpoint and must show "coming soon" or be hidden in Flutter.

| Feature | Screen(s) | What to Show in Flutter |
|---------|-----------|------------------------|
| Forgot Password email submission | `forgot_password_screen.dart` | Static page only. Lock icon, "Coming soon" badge, "Back to Sign In" link. No email field, no submit button. |
| Change Password | `settings_screen.dart` | `ListTile` with trailing `Text('Coming soon')`. No navigation, no form. |
| 2FA toggle | `settings_screen.dart` | Removed entirely. Do not render. |
| Message history / chat persistence | `main_chat_screen.dart` | Chat starts empty each session. No history API call on screen init. |
| SSE stream timeout handling | `main_chat_screen.dart` | No timeout timer. If stream hangs, user must manually retry by sending a new message. |
| `thought_trace` / AI reasoning panel | `recommendation_dashboard.dart` | `Visibility(visible: false)` — no backend endpoint. |
| `mismatch_notice` amber banner | `recommendation_dashboard.dart` | Show only if `recommendations` API response includes a `mismatch_notice` field. If field absent, hide banner. Confirm delivery mechanism with backend team. |
| Capability assessment questions API | `assessment_screen.dart` | Bundle 60 questions as `assets/assessment_questions.json`. No `GET /api/v1/profile/assessment/questions` endpoint exists yet. |
| University detail page | `recommendation_dashboard.dart` | "More Details" button → navigate to `MainChatScreen` with pre-filled message about the university. No separate detail screen. |
| Housing preference field | All onboarding screens | Removed from schema. Do not implement. |
| ORCID / GitHub SSO | `login_screen.dart`, `signup_screen.dart` | Removed. Wrong audience. Do not add these buttons. |
| Fabricated social proof ("1,200 students") | `carousel_screen.dart` | Removed. Do not add any social proof numbers. |
| Desktop / wide layout | All screens | 390px mobile only. `maxWidth: 390` constraint not needed in Flutter — fills device width naturally. |
| Red logout / error-red on non-destructive | `settings_screen.dart` | Sign Out button uses `#E0E3E5` bg + `#515F74` text. Never red. |

---

*End of DESIGN_HANDOFF.md — v1.0 for Khuzzaim*  
*Source: DESIGN.md v1.5, CLAUDE.md, FRONTEND_CHAT_INSTRUCTIONS.md, 16 HTML mockups*  
*Generated: April 2026*
