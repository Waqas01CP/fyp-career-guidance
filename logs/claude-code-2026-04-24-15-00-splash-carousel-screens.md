# Session Log — Splash Screen + Carousel Screen
## Date: 2026-04-24
## Model: Sonnet 4.6 | Effort: Medium

---

## Files Changed

### Created (2 new files)
- `frontend/lib/screens/splash_screen.dart`
- `frontend/lib/screens/onboarding/carousel_screen.dart`

### Not modified
- `main.dart`, providers, services, or any existing file — per HARD RULES

---

## Files Read (all 10 confirmed)

1. `logs/README.md` ✓
2. `CLAUDE.md` (loaded via system context) ✓
3. `docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md` ✓
4. `docs/00_architecture/FRONTEND_SPRINT_BUILD_PROCESS.md` ✓
5. `design/screen_mockups/DESIGN_HANDOFF.md` — Screen 01 + Screen 02 sections only ✓
6. `design/screen_mockups/DESIGN_SYSTEM_TOKENS.md` — Section 1 (Color) + Section 2 (Typography) only ✓
6b. `design/screen_mockups/code_onboarding_carousel.html` — slide text only ✓
7. `frontend/lib/main.dart` — routes table ✓
8. `frontend/lib/providers/auth_provider.dart` — AuthState + AuthNotifier ✓
9. `frontend/lib/providers/profile_provider.dart` — ProfileNotifier.loadProfile() ✓
10. `frontend/lib/services/auth_service.dart` — getToken() method ✓

---

## Plan Summary

### Splash Screen
- `ConsumerStatefulWidget` with `SingleTickerProviderStateMixin`
- `AnimationController` 1800ms, `Curves.easeInOut`, width 0→120px
- `_controller.forward()` and `_resolveRoute()` called simultaneously in `initState()` — animation runs concurrently with network call
- Routing: `AuthService.getToken()` → no token → '/onboarding'; token exists → `profileProvider.loadProfile()` → route by `onboardingStage`; 401 → '/onboarding'; network error → '/onboarding' (fail-safe)
- `kDebugMode` guard on DEBUG BUILD annotation
- `mounted` check before `Navigator.pushReplacementNamed()`

### Carousel Screen
- `StatefulWidget`, `PageController` + `int _currentPage` local state
- 3 slides, `PageView.builder`, `BouncingScrollPhysics`
- `AnimatedContainer` for dot indicators (active 28×3, inactive 6×3)
- Skip → '/login'; Next on slides 1–2 → next page; Get Started on slide 3 → '/login'
- Bento grid: simple `Container` + `Row`/`Column` cells — no SVG, no CustomPainter
- `_BentoCell` extracted as private `StatelessWidget` to enable const reuse

---

## Deviations from DESIGN_HANDOFF.md

| Deviation | Reason | Justified by |
|-----------|--------|-------------|
| `Icons.auto_stories` used instead of `material_symbols_icons` package | Prompt explicitly says "use Icons.auto_stories — do NOT import material_symbols_icons" | Explicit task instruction (highest priority) |
| Bento card right column: concentric circles instead of SVG chart | Prompt says "No SVG, no CustomPainter — simple colored rounded containers". DESIGN_HANDOFF.md Screen 02 section 13 suggests `flutter_svg` or `CustomPainter` | Explicit task constraint (no new packages) |
| Network error → '/onboarding' (not ErrorScreen) | Prompt says "Network error → '/onboarding' (fail safe)". DESIGN_HANDOFF.md Screen 01 section 10 says "If network error → ErrorScreen" | Explicit task instruction takes precedence |
| Slide 2 + 3 text sourced from design brief | `code_onboarding_carousel.html` only renders slide 1; slides 2–3 text not in HTML | Only available text source |
| Avatar stack omitted from footer | No local image assets; placeholder circles would add noise. Design shows real photos only | Low-end device first; assets to be added before demo |

---

## flutter analyze output

```
Analyzing frontend...
No issues found! (ran in 8.0s)
```

**Zero errors. Zero warnings.**

---

## flutter run result

**Not executed.** The HARD RULES state "Do NOT modify main.dart". Without route updates, `SplashScreen` and `CarouselScreen` are not accessible via named routes. Both screens resolve correctly in `flutter analyze` and would function as designed once wired.

### Action required before testing
Two lines in `main.dart` need updating (not done in this session per HARD RULES):

```dart
// Line to update in routes table:
'/onboarding': (context) => const CarouselScreen(),
// Import to add:
import 'screens/onboarding/carousel_screen.dart';
```

The `'/'` → `AppRouter` route already handles splash-equivalent logic. `SplashScreen` can replace `AppRouter` as the initial route in a dedicated wiring session:
```dart
'/': (context) => const SplashScreen(),
// Import to add:
import 'screens/splash_screen.dart';
```

Alternatively, test the carousel immediately: temporarily replace the '/onboarding' placeholder in main.dart with `CarouselScreen()`.

---

## Known Issues / Limitations

1. **main.dart not wired** — screens built, analyze-clean, but not yet accessible via routes. Requires separate wiring step (not in scope for this session).
2. **Avatar stack omitted** — HTML footer shows 3 circular avatar photos. Omitted because no local assets exist and network images violate "backend URL never localhost" spirit + offline-first requirement. Add as local assets before demo.
3. **Slide 2–3 bento content** — Slides 2 and 3 bento visual is a simplified concentric-circle pattern (same structure as slide 1, different icons/labels). HTML only shows slide 1 bento so exact visual targets for 2–3 are unknown.

---

## Rule Deviation — Two Screens in One Session

Justified per FRONTEND_SPRINT_BUILD_PROCESS.md "Splash + Carousel can be one session (no API calls)". Both screens are pre-auth with no SSE or complex state. Combined session reduces overhead with no quality risk.
