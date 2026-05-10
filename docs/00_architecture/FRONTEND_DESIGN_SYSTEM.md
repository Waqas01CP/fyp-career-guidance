# Frontend Design System
## FYP: AI-Assisted Academic Career Guidance System
## Flutter-Native Specification
## Date: May 2026 | Authority: Architecture Chat v6
## Replaces: design/screen_mockups/DESIGN_SYSTEM_TOKENS.md

---

> **How to use this document:**
> Read this before writing any widget code.
> It uses Flutter and Material Design 3 terminology — not CSS.
> Every visual decision is resolved here or by Material Design 3.
> Do not invent visual decisions not covered here.
> If this document conflicts with CLAUDE.md — CLAUDE.md wins.

---

## 1. THEME CONFIGURATION

```dart
ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: const Color(0xFF006B62),  // Teal — LOCKED, never change
    brightness: Brightness.light,
  ),
  textTheme: GoogleFonts.interTextTheme(),
  useMaterial3: true,
)
```

ScreenUtilInit configuration (already in main.dart):
```dart
ScreenUtilInit(
  designSize: const Size(390, 844),
  minTextAdapt: true,
  splitScreenMode: false,
)
```

---

## 2. THREE-COLOUR ROLE LOGIC — LOCKED ACROSS ALL 16 SCREENS

This is an architecture decision, not just a style choice. Violating it breaks
the visual language of the entire app.

| Colour | Hex | Role | Used on |
|---|---|---|---|
| **Teal** | `#006B62` | Human actions | AppBars, primary CTAs, progress bars, focus accents, selected states, primary buttons |
| **Slate** | `#515F74` | Secondary/neutral | Secondary text, metadata, ghost buttons, icons, disabled states, "Sign Out" button |
| **Purple** | `#6616D7` | AI content ONLY | AI Insight panels, AI bubble left-border, AI chip labels, AI sparkle icons |

**Purple on any non-AI element is a design error. Never use purple for human
interface elements, buttons, navigation, or anything the student directly acts on.**

---

## 3. MATERIAL DESIGN 3 COLOR ROLES

Use `Theme.of(context).colorScheme.<role>` — never hardcode hex values except
for the named exceptions in Section 4.

| Role | When to use |
|---|---|
| `colorScheme.primary` | Primary buttons, active icons, progress bars, selected Likert buttons, focus accents — maps to teal |
| `colorScheme.onPrimary` | Text/icons ON primary color background |
| `colorScheme.primaryContainer` | Subtle tonal backgrounds, dimension chips |
| `colorScheme.onPrimaryContainer` | Text/icons on primaryContainer |
| `colorScheme.surface` | Card backgrounds, form card backgrounds |
| `colorScheme.onSurface` | Primary body text, input values |
| `colorScheme.surfaceContainerLowest` | Page/Scaffold background |
| `colorScheme.surfaceContainerLow` | Input field fills, page background secondary sections |
| `colorScheme.surfaceContainer` | Unselected Likert buttons, unselected chips |
| `colorScheme.surfaceContainerHigh` | Unselected Likert buttons, alternating table rows, progress bar track |
| `colorScheme.outline` | Input borders when focused |
| `colorScheme.outlineVariant` | Subtle dividers (15% opacity only — never full opacity) |
| `colorScheme.onSurfaceVariant` | Secondary text, placeholder text, captions, metadata |
| `colorScheme.error` | Error states, validation failures, error left-borders |
| `colorScheme.onError` | Text/icons on error color |
| `colorScheme.inverseSurface` | SnackBar background |
| `colorScheme.onInverseSurface` | Text on SnackBar |

---

## 4. NAMED COLOR EXCEPTIONS

These colors cannot be derived from the seed. Use hardcoded hex only for these.

### 4a — AI / Tertiary Purple System
```dart
const Color aiPrimary = Color(0xFF6616D7);         // left borders, chip text, icons
const Color aiBackground = Color(0xFFEADDFF);      // AI panel background (tertiary-fixed)
const Color aiLabelText = Color(0xFF5A00C6);        // "AI INSIGHT" label text
const Color aiBodyText = Color(0xFF25005A);         // AI panel body text
```

### 4b — Amber Warning System (mismatch notice only)
```dart
const Color warningBackground = Color(0xFFFFF8E1);
const Color warningBorder = Color(0xFFF59E0B);
const Color warningText = Color(0xFF78350F);        // amber-900
```

### 4c — Splash screen specific
```dart
const Color splashBackground = Color(0xFF006B62);  // same as primary
const Color splashTagline = Color(0xFFA3FAEF);     // muted teal for tagline text
const Color splashLoadingBar = Color(0xFF00857A);  // loading bar fill
```

### 4d — Form card shadow specific
```dart
// Editorial shadow — for major form cards (login, signup, grades)
BoxShadow(
  color: Color(0x0F334155),
  blurRadius: 40,
  offset: Offset(0, 12),
)
```

---

## 5. TYPOGRAPHY

Font: Google Fonts Inter applied at theme level via `GoogleFonts.interTextTheme()`.
Use `Theme.of(context).textTheme.<style>` for standard text.
For weight/size overrides, use `.copyWith()` on the base style.

### Specific size reference (for overrides)

| Element | Size | Weight | Extra |
|---|---|---|---|
| Screen titles ("Welcome Back", "Academic Grades") | 28 | 700 | `letterSpacing: -0.02em` |
| Hero headline (Carousel slides) | 30 | 700 | `letterSpacing: -0.02em` |
| Question text (RIASEC quiz) | 18 | 600 | `height: 1.5` |
| Primary body, subtitles | 16 | 400 | `height: 1.6` |
| Secondary body, AI panel body | 13 | 400 | `height: 1.6` |
| Section subtitles | 14 | 400 | — |
| Button labels | 15 | 700 | — |
| Input values | 15 | 500 | — |
| Form field labels | 12 | 600 | `letterSpacing: 0.04em` |
| Chip labels | 10 | 700 | uppercase |
| Table headers | 10 | 700 | uppercase |
| Counters, step badges | 11 | 700 | uppercase, `letterSpacing: 0.08em` |
| AI panel label "AI INSIGHT" | 9 | 700 | uppercase, `letterSpacing: 0.10em` |
| Micro-labels, version | 9 | 700 | uppercase, `letterSpacing: 0.08em` |

**Minimum font size on mobile: 13px. Never go below this.**

---

## 6. SPACING (flutter_screenutil)

All spacing uses `.h`, `.w`, `.r` extensions.

| Purpose | Value |
|---|---|
| Page horizontal padding | `16.w` or `20.w` (screens use 20.w) |
| Page vertical padding | `24.h` |
| Between major sections | `24.h` or `32.h` |
| Between card sections | `16.h` |
| Between list items | `12.h` |
| Within a card | `20.h` and `20.w` (standard), `24.h` and `24.w` (form cards) |
| Button height | `52.h` (standard), `56.h` (OCR scan button) |
| Icon size standard | `24.r` |
| Icon size large | `32.r` or `40.r` (hero icons) |
| Icon container (splash, RIASEC hero) | `80.r` |

---

## 7. BORDER RADIUS

Two distinct values — do not confuse them:

| Context | Value | Note |
|---|---|---|
| **Form cards** (login, signup, grades input) | `32.r` | The large rounded container holding the form |
| **Content cards** (dashboard cards, results cards) | `16.r` | Standard content card |
| Primary/elevated buttons | `12.r` | Via `shape` on ElevatedButton |
| Input fields | `12.r` | Via `InputDecoration.border` |
| Chips, Likert buttons | `12.r` | |
| Bottom sheets | `24.r` top corners only | |
| Dialogs | `16.r` | |
| Avatar containers | `20.r` (hero), `50.r` (full circle) | |
| Dot indicators (carousel) | `2.r` | |
| OCR modal | `20.r` | |

---

## 8. SHADOWS — TWO DISTINCT TYPES

**Content card shadow** — for dashboard cards, results cards, settings cards:
```dart
BoxShadow(
  color: Colors.black.withOpacity(0.06),
  blurRadius: 24,
  offset: const Offset(0, 8),
)
```

**Editorial / form card shadow** — for login form card, signup form card, grades form card:
```dart
BoxShadow(
  color: const Color(0x0F334155),
  blurRadius: 40,
  offset: const Offset(0, 12),
)
```

**No hard shadows anywhere.** Only ambient shadows. No `1px solid` borders anywhere
(except the accessibility divider in subject marks table at 15% opacity only).

---

## 9. COMPONENT PATTERNS

### 9a — Primary Button (ElevatedButton)
```dart
ElevatedButton(
  style: ElevatedButton.styleFrom(
    minimumSize: Size(double.infinity, 52.h),
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(12.r),
    ),
  ),
  onPressed: _isLoading ? null : _handleSubmit,
  child: _isLoading
      ? SizedBox(
          height: 20.r, width: 20.r,
          child: const CircularProgressIndicator(strokeWidth: 2,
              color: Colors.white),
        )
      : Text('Label'),
)
```

Button press animation (modernization pass — applies to primary buttons):
```dart
GestureDetector(
  onTapDown: (_) => setState(() => _pressed = true),
  onTapUp: (_) => setState(() => _pressed = false),
  onTapCancel: () => setState(() => _pressed = false),
  child: AnimatedScale(
    scale: _pressed ? 0.97 : 1.0,
    duration: const Duration(milliseconds: 150),
    child: ElevatedButton(...),
  ),
)
```

### 9b — Text Input with Focus Left-Border
```dart
Stack(
  children: [
    TextFormField(
      focusNode: _focusNode,
      decoration: InputDecoration(
        filled: true,
        fillColor: Theme.of(context).colorScheme.surfaceContainerLow,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: BorderSide.none,
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: BorderSide.none,
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12.r),
          borderSide: BorderSide.none,
        ),
        contentPadding: EdgeInsets.symmetric(
            horizontal: 16.w, vertical: 16.h),
      ),
    ),
    // Focus left-border
    AnimatedOpacity(
      opacity: _focusNode.hasFocus ? 1.0 : 0.0,
      duration: const Duration(milliseconds: 150),
      child: Container(
        width: 2,
        height: 52.h,
        decoration: BoxDecoration(
          color: _hasError
              ? Theme.of(context).colorScheme.error
              : Theme.of(context).colorScheme.primary,
          borderRadius: BorderRadius.only(
            topLeft: Radius.circular(12.r),
            bottomLeft: Radius.circular(12.r),
          ),
        ),
      ),
    ),
  ],
)
```

### 9c — Gradient Top Bar (Login / Signup)
```dart
Container(
  height: 3,
  width: double.infinity,
  decoration: const BoxDecoration(
    gradient: LinearGradient(
      colors: [Color(0xFF006B62), Color(0xFF00857A)],
    ),
  ),
)
```
Place this above the form card container.

### 9d — Form Card (Login / Signup / Grades)
```dart
Container(
  decoration: BoxDecoration(
    color: Theme.of(context).colorScheme.surface,
    borderRadius: BorderRadius.circular(32.r),
    boxShadow: const [
      BoxShadow(
        color: Color(0x0F334155),
        blurRadius: 40,
        offset: Offset(0, 12),
      ),
    ],
  ),
  padding: EdgeInsets.all(24.r),
  child: child,
)
```

### 9e — Content Card (Dashboard / Results)
```dart
Container(
  decoration: BoxDecoration(
    color: Theme.of(context).colorScheme.surface,
    borderRadius: BorderRadius.circular(16.r),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.06),
        blurRadius: 24,
        offset: const Offset(0, 8),
      ),
    ],
  ),
  padding: EdgeInsets.all(20.r),
  child: child,
)
```

### 9f — AI Insight Panel (appears on RIASEC Quiz, RIASEC Complete, Chat AI bubbles)
```dart
Container(
  decoration: BoxDecoration(
    color: const Color(0xFFEADDFF),
    borderRadius: BorderRadius.circular(12.r),
    border: const Border(
      left: BorderSide(color: Color(0xFF6616D7), width: 3),
    ),
  ),
  padding: EdgeInsets.all(12.r),
  child: Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Row(children: [
        Icon(Icons.auto_awesome,
             size: 12.r, color: const Color(0xFF6616D7)),
        SizedBox(width: 4.w),
        Text('AI INSIGHT',
          style: TextStyle(
            fontSize: 9.sp, fontWeight: FontWeight.w700,
            color: const Color(0xFF5A00C6),
            letterSpacing: 0.10,
          )),
      ]),
      SizedBox(height: 6.h),
      Text(insightText,
        style: TextStyle(
          fontSize: 13.sp, fontWeight: FontWeight.w400,
          color: const Color(0xFF25005A),
          height: 1.6,
        )),
    ],
  ),
)
```

### 9g — Chat Bubbles
**Student bubble** (right-aligned):
```dart
Align(
  alignment: Alignment.centerRight,
  child: Container(
    margin: EdgeInsets.only(left: 60.w),
    padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.primary,
      borderRadius: BorderRadius.circular(16.r).copyWith(
        bottomRight: Radius.circular(4.r),
      ),
    ),
    child: Text(message,
        style: TextStyle(color: Colors.white, fontSize: 15.sp)),
  ),
)
```

**AI bubble** (left-aligned, with AI panel left border):
```dart
Align(
  alignment: Alignment.centerLeft,
  child: Container(
    margin: EdgeInsets.only(right: 60.w),
    padding: EdgeInsets.symmetric(horizontal: 16.w, vertical: 12.h),
    decoration: BoxDecoration(
      color: Theme.of(context).colorScheme.surfaceContainerLow,
      borderRadius: BorderRadius.circular(16.r).copyWith(
        bottomLeft: Radius.circular(4.r),
      ),
      border: const Border(
        left: BorderSide(color: Color(0xFF6616D7), width: 3),
      ),
    ),
    child: Text(message,
        style: TextStyle(
          color: Theme.of(context).colorScheme.onSurface,
          fontSize: 15.sp)),
  ),
)
```

### 9h — OCR Overlay (Grades Input — DEFERRED, "Soon" badge)
When implemented (Sprint 4):
```dart
BackdropFilter(
  filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
  child: Container(
    color: const Color(0xCCF7F9FB), // rgba(247,249,251,0.80)
    child: Center(
      child: Container(
        constraints: BoxConstraints(maxWidth: 340.w),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20.r),
        ),
        padding: EdgeInsets.all(24.r),
        child: ocrModalContent,
      ),
    ),
  ),
)
```
Note: `import 'dart:ui'` required for `ImageFilter`.

### 9i — RIASEC Radar Chart (CustomPainter)
On RIASEC Complete screen:
```dart
CustomPaint(
  painter: _RiasecRadarPainter(scores: riasecScores),
  child: AspectRatio(aspectRatio: 1.0),
)

// Painter: 6-axis hexagon, 3 concentric tiers (33%/66%/100%)
// Data polygon fill: Color(0xFF006B62).withOpacity(0.15)
// Data polygon stroke: Color(0xFF006B62), width 2
// Grid lines: Color(0xFFE6E8EA)
// Vertex labels: R, I, A, S, E, C — 10sp, 600 weight
// import 'dart:math' for cos/sin/pi
// Wrap in: Semantics(label: 'RIASEC radar chart showing your interest profile')
```

Demo locked score fallback (use if profileProvider has no real scores):
```dart
const Map<String, int> _fallbackScores = {
  'R': 32, 'I': 45, 'A': 28, 'S': 31, 'E': 38, 'C': 42
};
// Renders as: I=88%, C=80%, E=70% (top 3)
```

### 9j — Progress Bars
**RIASEC score bars** (on Student Profile screen):
```dart
LinearProgressIndicator(value: score / 50)  // max raw = 50
```

**Capability score bars** (on Student Profile screen):
```dart
LinearProgressIndicator(value: score / 100)  // percentage 0-100
```

### 9k — Loading States
Full screen:
```dart
Scaffold(body: Center(child: CircularProgressIndicator(
  color: Theme.of(context).colorScheme.primary,
)))
```

Shimmer (content loading):
```dart
Shimmer.fromColors(
  baseColor: Theme.of(context).colorScheme.surfaceContainer,
  highlightColor: Theme.of(context).colorScheme.surfaceContainerHigh,
  child: placeholderWidgets,
)
```

### 9l — Error State
```dart
Center(
  child: Padding(
    padding: EdgeInsets.all(24.r),
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.cloud_off, size: 48.r,
             color: Theme.of(context).colorScheme.error),
        SizedBox(height: 16.h),
        Text('message', style: Theme.of(context).textTheme.titleMedium),
        SizedBox(height: 8.h),
        Text('sub-message', style: Theme.of(context).textTheme.bodyMedium
            ?.copyWith(color: Theme.of(context).colorScheme.onSurfaceVariant)),
        SizedBox(height: 24.h),
        ElevatedButton(onPressed: onRetry, child: const Text('Try Again')),
      ],
    ),
  ),
)
```

### 9m — SnackBar
```dart
ScaffoldMessenger.of(context).showSnackBar(SnackBar(
  content: Text('message'),
  backgroundColor: Theme.of(context).colorScheme.inverseSurface,
  behavior: SnackBarBehavior.floating,
  shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(8.r)),
))
```

### 9n — Mismatch Notice / Warning Banner
```dart
Container(
  decoration: const BoxDecoration(
    color: Color(0xFFFFF8E1),
    border: Border(left: BorderSide(color: Color(0xFFF59E0B), width: 4)),
    borderRadius: BorderRadius.only(
      topRight: Radius.circular(8),
      bottomRight: Radius.circular(8),
    ),
  ),
  padding: EdgeInsets.all(12.r),
  child: Row(children: [
    const Icon(Icons.warning_amber, color: Color(0xFFB45309)),
    SizedBox(width: 8.w),
    Expanded(child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('Notice', style: TextStyle(
          fontWeight: FontWeight.w600, color: const Color(0xFF78350F))),
        Text(warningText, style: const TextStyle(
          color: Color(0xFF92400E), fontSize: 13)),
      ],
    )),
  ]),
)
```

### 9o — Likert Scale Buttons (RIASEC Quiz)
```dart
Container(
  decoration: BoxDecoration(
    color: _answers[questionIndex] == value
        ? Theme.of(context).colorScheme.primary
        : Theme.of(context).colorScheme.surfaceContainerHigh,
    borderRadius: BorderRadius.circular(12.r),
  ),
  child: InkWell(
    borderRadius: BorderRadius.circular(12.r),
    onTap: () => _selectAnswer(value),
    child: Padding(
      padding: EdgeInsets.symmetric(vertical: 12.h),
      child: Center(child: Text('$value',
        style: TextStyle(
          color: _answers[questionIndex] == value
              ? Colors.white
              : Theme.of(context).colorScheme.onSurfaceVariant,
          fontWeight: FontWeight.w600,
        ))),
    ),
  ),
)
```

### 9p — AnimatedSwitcher (RIASEC Quiz question transitions)
```dart
AnimatedSwitcher(
  duration: const Duration(milliseconds: 300),
  child: _buildQuestionCard(
    key: ValueKey(_currentIndex),  // KEY MUST CHANGE per question — required for animation
    question: _questions[_currentIndex],
  ),
)
```

---

## 10. NAVIGATION RULES

| Situation | Navigator call |
|---|---|
| Forward in onboarding (preserving back) | `Navigator.pushNamed(context, '/route')` |
| Lateral replacement (login ↔ signup) | `Navigator.pushReplacementNamed(context, '/route')` |
| Terminal navigation (assessment → chat, logout → login) | `Navigator.pushNamedAndRemoveUntil(context, '/route', (r) => false)` |
| Re-entry guard (stage already passed) | `Navigator.pushReplacementNamed(context, '/next-stage')` |
| 401 from any API call | `Navigator.pushNamedAndRemoveUntil(context, '/login', (r) => false)` |

**PostFrameCallback rule:** Use `WidgetsBinding.instance.addPostFrameCallback((_) { ... })`
when navigating inside dialog dismissal, PopScope callback, or dispose.
Never navigate directly from these contexts.

**rootNavigator rule:** Use `Navigator.of(context, rootNavigator: true)` inside
PopScope callbacks to avoid nested navigator scope issues.

---

## 11. FLUTTER-SPECIFIC RULES

- **`mounted` check** — always check `if (mounted)` before calling `setState()` or
  `Navigator` after an async operation.
- **No `flutter_svg`** — use `Icons.*` or `Container` shapes. No SVG packages.
- **No `CustomPainter` except** the RIASEC radar chart on RIASEC Complete screen.
- **`TextInputType.emailAddress`** on email fields.
- **`TextInputAction.next`** on all fields except the last in a form.
- **`obscureText: true`** with visibility toggle on password fields.
- **`keyboardType: TextInputType.number`** on marks input fields.
- **`resizeToAvoidBottomInset: false`** on Scaffold for screens with forms.
- **Keyboard padding:** Apply `MediaQuery.of(context).viewInsets.bottom` to
  `SingleChildScrollView` bottom padding. Use `SafeArea(bottom: false)` + 
  `MediaQuery.removePadding(removeBottom: true)` to prevent double-compensation.

---

## 12. DO NOT BUILD — GLOBAL RULES

| What | Why |
|---|---|
| Google / GitHub / ORCID SSO buttons | Wrong audience |
| Social proof numbers ("1,200 students") | Fabricated |
| Notification toggles | No notification backend |
| Desktop / tablet layouts | Mobile only (390px) |
| Red Sign Out button | Not destructive — use slate colors |
| Hard drop shadows | Ambient only |
| Any `1px solid` border | No hard borders anywhere |
| Any font other than Inter | Locked |
| Purple on any non-AI element | Violates three-colour role logic |
| `dio` package for SSE | Use `http` with streaming parser |
| `flutter_secure_storage` keys from JWT substring | Use sessionId-first pattern |
| Housing preference field | Removed from schema |
| `material_symbols_icons` package | Use `Icons.*` from SDK |

---

## 13. PACKAGE NAME (fix before APK build)

Current: `com.example.frontend_app`
Required: `com.fyp.career_guidance`

Files to update:
- `android/app/build.gradle.kts` — `namespace` and `applicationId`
- `android/app/src/main/AndroidManifest.xml`
- `android/app/src/main/kotlin/` — rename folder to match package path

---

## 14. DRAFT KEY PATTERN

All quiz/assessment draft keys use sessionId-first:
```dart
String _draftKey() {
  final sessionId = ref.read(profileProvider).sessionId;
  if (sessionId != null) return 'draft_[screen]_$sessionId';
  final token = ref.read(authProvider).token;
  return token != null
      ? 'draft_[screen]_${token.hashCode}'
      : 'draft_[screen]_anonymous';
}
```
Replace `[screen]` with `riasec` or `assessment`.

---

*FRONTEND_DESIGN_SYSTEM.md v1.0 — May 2026*
*Replaces: design/screen_mockups/DESIGN_SYSTEM_TOKENS.md*