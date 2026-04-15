Now I have everything I need. Let me produce the complete design system token reference.

---

## Design System Token Reference
### Academic Intelligence — Flutter (Android + Web)
### Extracted from: DESIGN.md + all 12 HTML mockups
### April 2026 — Authoritative for all subsequent screens

---

## 1. Color Tokens

Every color token below appears verbatim in all mockup Tailwind configs. These are consistent across all 12 screens with zero variation — treat them as locked.

### Core Brand

| Token | Hex | Role | Usage Rule |
|---|---|---|---|
| `primary` | `#005c55` | Academic Teal | Authoritative actions, brand markers, active nav, filled buttons |
| `primary-container` | `#0f766e` | Teal Hover/Gradient end | Button hover states, gradient pair with primary |
| `primary-fixed` | `#9cf2e8` | Teal Tint | Icon container backgrounds, feature highlight backgrounds |
| `primary-fixed-dim` | `#80d5cb` | Teal Dim | Inverse primary, chip tints |
| `on-primary` | `#ffffff` | Text on Teal | All text/icons on primary-filled surfaces |
| `on-primary-container` | `#a3faef` | Text on Teal Container | Label text inside primary-container backgrounds |
| `on-primary-fixed` | `#00201d` | Dark on Teal Fixed | Text on primary-fixed backgrounds |
| `on-primary-fixed-variant` | `#00504a` | Mid Teal | Secondary labels on teal-tinted surfaces |
| `surface-tint` | `#006a63` | Teal tint overlay | Not used directly — drives M3 tonal surface computation |

### AI / Tertiary (Future Purple — RESERVED for AI only)

| Token | Hex | Role | Usage Rule |
|---|---|---|---|
| `tertiary` | `#6616d7` | Future Purple | AI state indicators, thinking pulses. **Never for static UI.** |
| `tertiary-container` | `#7f3ef0` | Purple Container | AI action button gradient end |
| `tertiary-fixed` | `#eaddff` | Purple Tint | AI Insight Pulse card background |
| `tertiary-fixed-dim` | `#d2bbff` | Purple Dim | Subtle AI accent backgrounds |
| `on-tertiary` | `#ffffff` | Text on Purple | Text/icons on tertiary-filled surfaces |
| `on-tertiary-container` | `#f1e6ff` | Text on Purple Container | Text inside tertiary-container |
| `on-tertiary-fixed` | `#25005a` | Dark on Purple Tint | Body text inside AI Insight Pulse card |
| `on-tertiary-fixed-variant` | `#5a00c6` | Label on Purple Tint | Uppercase labels inside AI Insight Pulse |

### Secondary (Grounding / Neutral)

| Token | Hex | Role | Usage Rule |
|---|---|---|---|
| `secondary` | `#515f74` | Deep Slate | Body text, sub-headers, secondary labels |
| `secondary-container` | `#d5e3fd` | Slate Container | Feature icon backgrounds (non-AI) |
| `secondary-fixed` | `#d5e3fd` | Slate Fixed | Same as container in light mode |
| `secondary-fixed-dim` | `#b9c7e0` | Slate Dim | Muted chips, disabled states |
| `on-secondary` | `#ffffff` | Text on Slate | Text on secondary-filled surfaces |
| `on-secondary-container` | `#57657b` | Text on Slate Container | Sub-labels inside secondary containers |
| `on-secondary-fixed` | `#0d1c2f` | Dark on Slate Fixed | Body text on slate-fixed backgrounds |
| `on-secondary-fixed-variant` | `#3a485c` | Mid on Slate Fixed | Supporting labels |

### Surfaces (The Tonal Layering System)

| Token | Hex | Level | Usage |
|---|---|---|---|
| `surface` / `background` | `#f7f9fb` | Base (Layer 0) | All screen backgrounds, AppBar fill |
| `surface-bright` | `#f7f9fb` | Same as surface | Modal overlay base before blur |
| `surface-container-low` | `#f2f4f6` | Layer 1 | Section blocks, left-panel in 2-column layout, input field fill |
| `surface-container` | `#eceef0` | Layer 2 | Progress indicator track, divider replacement, password rules container |
| `surface-container-high` | `#e6e8ea` | Layer 3 | Hover state on cards/buttons, chip backgrounds |
| `surface-container-highest` | `#e0e3e5` | Layer 4 (Topmost) | Input fill on contrast surfaces, most elevated non-modal surface |
| `surface-container-lowest` | `#ffffff` | Card White | Content cards, form panels — the "lift" against container-low |
| `surface-variant` | `#e0e3e5` | Same as highest | Segmented control backgrounds |
| `surface-dim` | `#d8dadc` | Dimmed surface | Scrim under modals |

### Text & Outline

| Token | Hex | Role | Usage |
|---|---|---|---|
| `on-surface` | `#191c1e` | Primary text | All headings, body text, high-emphasis content |
| `on-background` | `#191c1e` | Same as on-surface | Interchangeable with on-surface |
| `on-surface-variant` | `#3e4947` | Secondary text | Supporting body text, metadata, validation hints |
| `outline` | `#6e7977` | Medium outline | Placeholder text, icon fill on neutral surfaces, divider text |
| `outline-variant` | `#bdc9c6` | Subtle outline | Ghost border if absolutely required (15% opacity rule), placeholder text fill, social button borders |
| `inverse-surface` | `#2d3133` | Dark surface | Snackbar/toast background |
| `inverse-on-surface` | `#eff1f3` | Light on dark | Text on inverse-surface |
| `inverse-primary` | `#80d5cb` | Light primary | Primary on dark surfaces |

### Semantic

| Token | Hex | Role | Usage |
|---|---|---|---|
| `error` | `#ba1a1a` | Destructive Red | Form validation errors, error icons |
| `error-container` | `#ffdad6` | Error Tint | Error message background |
| `on-error` | `#ffffff` | Text on Error | Text on error-filled backgrounds |
| `on-error-container` | `#93000a` | Text on Error Tint | Body text inside error containers |

### Semantic Colors from FRONTEND_CHAT_INSTRUCTIONS.md

These are the system-level semantic tokens defined in the architecture spec. They bridge the Stitch mockup colors with the locked architecture spec:

| Semantic Role | Hex | Token Alias | Usage |
|---|---|---|---|
| Success / Safe Green | `#10B981` | `success` | Confirmed eligible, Emerging LagScoreBadge |
| Warning / Risk Amber | `#F59E0B` | `warning` | Stretch/likely, OCR low confidence, Peak LagScoreBadge |
| Critical / Error Red | `#EF4444` | `critical` | Improvement needed, Saturated LagScoreBadge |

> Note: `#EF4444` is slightly lighter than the `error` token `#ba1a1a`. Use `error` (`#ba1a1a`) for form validation; use `critical` (`#EF4444`) for merit-tier badges and LagScoreBadge only.

---

## 2. Typography Tokens

**Font family: `Inter` — locked. No fallbacks except `sans-serif` for system safety.**

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|---|---|---|---|---|---|
| `display-lg` | 3.5rem (56px) | 700 Bold | 1.1 | `-0.02em` | Hero stats, large impact numbers on Dashboard |
| `headline-lg` | 2.25rem (36px) | 700 Bold | 1.15 | `-0.02em` | Page hero headlines (Login left panel) |
| `headline-md` | 1.75rem (28px) | 600 SemiBold | 1.2 | `-0.02em` | Section headers |
| `headline-sm` | 1.375rem (22px) | 500 Medium | 1.3 | `0` | Card titles, prominent labels |
| `title-lg` | 1.25rem (20px) | 600 SemiBold | 1.4 | `-0.01em` | AppBar brand name, form section titles |
| `title-md` | 1rem (16px) | 600 SemiBold | 1.5 | `0` | Sub-section titles, feature names |
| `body-lg` | 1rem (16px) | 400 Regular | 1.6 | `0` | Primary reading text, chat messages |
| `body-md` | 0.875rem (14px) | 400 Regular | 1.5 | `0` | Card body, supporting descriptions |
| `body-sm` | 0.75rem (12px) | 400 Regular | 1.5 | `0` | Metadata, timestamps, captions |
| `label-lg` | 0.875rem (14px) | 600 SemiBold | 1.4 | `0` | Button text, tab labels |
| `label-md` | 0.75rem (12px) | 600 SemiBold | 1.3 | `0.05em` | Input labels (uppercase), category chips |
| `label-sm` | 0.6875rem (11px) | 600 SemiBold | 1.3 | `0.08em` | All-caps footer text, social auth dividers, ultra-tight metadata |
| `label-xs` | 0.625rem (10px) | 700 Bold | 1.2 | `0.1em` | Uppercase "OR CONTINUE WITH" dividers, footer copyright |

**Typography rules:**
- `display-lg` and all headline styles: letter-spacing `-0.02em`
- `label-*` styles used ALL-CAPS: always paired with `tracking-widest` (0.1em+)
- `secondary` color (`#515f74`) for sub-headers, metadata, secondary body
- Never use default tracking on display-size text

---

## 3. Border Radius Tokens

From the locked Tailwind config (identical across all 12 mockups):

| Token | Value | Usage |
|---|---|---|
| `radius-xs` (DEFAULT) | `0.125rem` (2px) | Checkbox tick mark, micro-elements |
| `radius-sm` (`lg` in config) | `0.25rem` (4px) | Progress bar cap, tag pills |
| `radius-md` (`xl` in config) | `0.5rem` (8px) — also seen as `rounded-lg` | Buttons, dropdown containers, social auth buttons |
| `radius-lg` | `0.75rem` (12px) — `rounded-xl` in practice | Input fields, password rule container, list item cards |
| `radius-xl` | `1rem` (16px) — `rounded-2xl` | Feature panels, AI Insight Pulse card |
| `radius-2xl` | `2rem` (32px) — `rounded-[2rem]` | Main form card (Login panel) |
| `radius-full` (`full` in config) | `0.75rem` | Pill chips — note: config says 0.75rem not 9999px |
| `radius-circle` | `50%` / `rounded-full` in CSS | Avatar, progress indicator dots |

> **Flutter mapping note:** The config `full` radius is `0.75rem` (12px), not a true pill. For actual circular shapes use `BorderRadius.circular(999)` in Flutter. For the locked chip shape use `BorderRadius.circular(12)`.

---

## 4. Spacing Scale

Based on the 8dp grid system stated in DESIGN.md. All values observed in mockups:

| Token | Value | Flutter equivalent |
|---|---|---|
| `space-1` | 4px | `SizedBox(height: 4)` |
| `space-2` | 8px | `SizedBox(height: 8)` |
| `space-3` | 12px | `SizedBox(height: 12)` |
| `space-4` | 16px | `SizedBox(height: 16)` |
| `space-5` | 20px | `SizedBox(height: 20)` |
| `space-6` | 24px | `SizedBox(height: 24)` |
| `space-8` | 32px | `SizedBox(height: 32)` |
| `space-10` | 40px | `SizedBox(height: 40)` |
| `space-12` | 48px | `SizedBox(height: 48)` |
| `space-16` | 64px | `SizedBox(height: 64)` |

**Page-level padding:** `px-4` (16px) mobile, `px-6` (24px) tablet/desktop
**Card internal padding:** `p-8` (32px) standard, `p-12` (48px) premium form panels
**Item vertical separation (list items, no dividers):** `space-4` (16px) minimum

---

## 5. Elevation & Shadow Tokens

| Token | Value | Usage |
|---|---|---|
| `shadow-editorial` | `0 12px 40px rgba(51, 65, 85, 0.06)` | Main form cards, login panel, signup panel |
| `shadow-card` | `0 4px 16px rgba(51, 65, 85, 0.04)` | University cards, feature cards (derived, lighter than editorial) |
| `shadow-float` | `0 12px 40px rgba(51, 65, 85, 0.06)` | Same as editorial — AI bubbles, floating elements |
| `shadow-primary` | `0 4px 12px rgba(0, 92, 85, 0.10)` | Primary filled buttons |
| `shadow-none` | `none` | All list items, all content within cards |

**Key rule:** No `box-shadow` with pure black (`rgba(0,0,0,...)`). Shadow color is always a tinted version of `on-surface` (`#333441` approx / `rgba(51, 65, 85, ...)`).

**Glassmorphism (for modals only):**
```
background: rgba(247, 249, 251, 0.80)   // surface at 80% opacity
backdrop-filter: blur(20px)
```

---

## 6. Component Specifications

### Button: Primary Filled
```
Background:       primary (#005c55)
Text:             on-primary (#ffffff), label-lg, weight 700
Border radius:    radius-lg (12px)  ← observed as rounded-xl in mockups
Padding:          16px vertical, 24px horizontal
Hover:            primary-container (#0f766e)
Active:           scale(0.98) transform
Shadow:           shadow-primary
Width:            Full-width on mobile (w-full)
Disabled:         opacity 38%, no interaction
```

### Button: Secondary / Ghost
```
Background:       transparent
Border:           outline-variant (#bdc9c6) at ~20% opacity
Text:             secondary (#515f74), label-lg
Border radius:    radius-md (8px)
Hover:            surface-container-low (#f2f4f6)
```

### Button: Social Auth
```
Background:       surface-container-low (#f2f4f6)
Border:           none (Login) or outline-variant (Signup — ghost variant)
Text:             on-surface, label-xs Bold
Border radius:    radius-lg (12px)
Hover:            surface-container-high (#e6e8ea)
Padding:          12px vertical
```

### Button: AI Action (Gradient)
```
Background:       linear-gradient(135deg, tertiary #6616d7, tertiary-container #7f3ef0)
Text:             on-tertiary (#ffffff), label-lg, weight 600
Border radius:    radius-lg (12px)
Usage:            "Generate Roadmap", "Analyze" — AI-triggering actions only
```

### Input Field
```
Background:       surface-container-low (#f2f4f6)
Border:           none (no default border)
Border radius:    radius-lg (12px)
Padding:          16px all sides
Text:             on-surface (#191c1e), body-lg
Placeholder:      outline-variant (#bdc9c6)
Focus state:      border-left: 2px solid primary (#005c55) — left border only, no ring
Icon prefix:      outline (#6e7977), 20px, left-padded 16px
Label:            label-sm, ALL CAPS, tracking-widest, secondary color, above field
Error state:      border-left: 2px solid error (#ba1a1a), error icon right
```

### Label Style (All Input Labels)
```
Font size:        11px (label-sm)
Weight:           600 SemiBold
Case:             ALL CAPS (text-transform: uppercase)
Tracking:         0.08–0.1em (tracking-widest)
Color:            secondary (#515f74)
Position:         Above field, margin-bottom: 8px, left-padded 4px
```

### AI Insight Pulse Card
```
Background:       tertiary-fixed (#eaddff)
Border-left:      4px solid tertiary (#6616d7)
Border radius:    radius-xl (16px)
Padding:          24px
Icon:             auto_awesome, tertiary color
Badge label:      label-xs, ALL CAPS, tracking-widest, on-tertiary-fixed-variant (#5a00c6)
Body text:        on-tertiary-fixed (#25005a), body-md, weight 500
Shadow:           shadow-card
Usage:            EXCLUSIVELY for AI-generated content — never for static facts
```

### Progress Bar (Onboarding)
```
Track:            surface-container-low (#f2f4f6), height: 6px
Fill:             primary (#005c55)
Border radius:    radius-full (pill)
Position:         Fixed, directly below AppBar (top: 52px)
Animation:        transition-all duration-500ms ease
```

### Progress Indicator (Step Dots)
```
Active dot:       primary, 10px diameter
Inactive dot:     outline-variant, 6px diameter
Transition:       300ms ease
```

### Card: Content Card
```
Background:       surface-container-lowest (#ffffff)
Border radius:    radius-xl (16px) standard, radius-2xl (32px) premium
Shadow:           shadow-editorial
Border:           none — tonal contrast with parent background provides edge
Hover:            surface-container (#eceef0) — subtle, no shadow increase
```

### Mismatch Notice / Warning Banner
```
Background:       #FFF8E1 (amber tint — not in token set, observed directly)
Border-left:      4px solid amber-500 / #F59E0B (warning token)
Icon color:       amber-700 / ~#B45309
Title:            body-md, weight 600, amber-900
Body:             label-sm, amber-800
Border radius:    Right side only — rounded-r-lg (8px)
Dismissable:      Yes — X button or "Review Now" CTA
```

### Likert Scale Button (RIASEC Quiz)
```
Default:          surface-container-high (#e6e8ea) background
Active/selected:  primary (#005c55) background, on-primary (#ffffff) text
Border radius:    radius-lg (12px)
Hover:            surface-container-low (#f2f4f6)
Size:             Equal-width set of 5 buttons, full-width container
Label:            Numeric 1–5 + optional text
```

### Password Validation Indicator
```
Container:        surface-container (#eceef0), padding 16px, radius-lg
Pass icon:        check_circle, FILLED, primary (#005c55)
Fail icon:        radio_button_unchecked, outline-variant
Text pass:        on-surface-variant (#3e4947), body-sm weight 500
Text fail:        outline (#6e7977), body-sm weight 500
```

---

## 7. Navigation / AppBar

```
Background:       surface / #f7f9fb
Position:         Fixed top, z-index: 60
Height:           52px (py-3 + icon ~20px)
Brand wordmark:   title-lg, weight 700, primary (#005c55), tracking-tight
Brand icon:       school (Material Symbol), teal-700 (#0f5c5e approx)
Right cluster:    Avatar (40px circle, outline-variant border) + optional nav links
Nav links:        body-md, secondary color; active = primary, weight 700
Step indicator:   body-sm, secondary — "Step X of Y" in onboarding
```

---

## 8. Layout & Grid Tokens

| Context | Grid | Notes |
|---|---|---|
| Mobile (< 768px) | 1 column, 16px gutters | All screens |
| Tablet (768–1024px) | 1–2 column, 24px gutters | Breakpoint: `md:` |
| Desktop (> 1024px) | 12-column, 32px gutters | Breakpoint: `lg:` |
| Login/Signup layout | `lg:grid-cols-2` or `lg:grid-cols-12` | Left branding (5 cols), right form (7 cols) |
| Dashboard layout | `lg:grid-cols-12` | Left main (8 cols), right sidebar (4 cols) |
| Max content width | `max-w-6xl` (1152px) or `max-w-7xl` (1280px) | Dashboard uses 7xl |
| Page horizontal padding | 16px mobile, 24px tablet+ | `px-4` / `px-6` |
| Page top padding | 96px (below fixed header 52px + progress bar 6px + buffer) | `pt-24` on onboarding |

---

## 9. Icon System

**Library:** Material Symbols Outlined (variable font)
**Default settings:** `FILL 0, wght 400, GRAD 0, opsz 24`
**Filled variant class:** `fill-icon` — `font-variation-settings: 'FILL' 1`

| Icon size | Usage |
|---|---|
| 18px (`text-[18px]`) | Inline validation indicators |
| 20px (`text-xl`) | Input prefix icons |
| 24px (default) | AppBar, button suffix, standard UI icons |
| 32px (`text-3xl`) | Feature highlight icons, branding mark |

**Key icons used across screens:**

| Icon name | Usage |
|---|---|
| `school` | Brand mark in AppBar |
| `auto_awesome` | AI Insight Pulse card badge |
| `check_circle` (filled) | Validation pass |
| `radio_button_unchecked` | Validation pending |
| `error` / `info` | Form error state |
| `visibility_off` / `visibility` | Password toggle |
| `person`, `mail`, `lock`, `verified_user` | Input prefix icons (Signup) |
| `arrow_forward` | Submit button suffix |
| `warning` | Mismatch notice banner |
| `language` | Locale toggle |

---

## 10. Glassmorphism (Modal/Float Pattern)

```
Background:       rgba(247, 249, 251, 0.80)  // surface @ 80%
Backdrop filter:  blur(20px)
Border:           none — or outline-variant at 15% opacity max
Border radius:    radius-xl (16px) minimum
Shadow:           shadow-editorial
Class alias:      .glass
```

Used for: floating OCR Verification Modal, context-preserving overlays.

---

## 11. Decorative / Motion Tokens

### Background Blurs (Brand Depth)
```
Primary glow:    rgba(0, 92, 85, 0.05) — 256px circle, blur-3xl, position: bottom-left
Tertiary glow:   rgba(102, 22, 215, 0.05) — 192px circle, blur-2xl, position: top-right
Usage:           Left-panel editorial sections only — never in form or data areas
```

### Transitions
```
Standard:         150–200ms ease
Image hover:      700ms (grayscale-to-color on hover: image reveal)
Progress bar:     500ms (fill animation)
Button active:    scale(0.98), 200ms
Input focus:      border-left appearance, instant (no delay)
```

### Image Treatment (Where used)
```
Default:          grayscale filter
Hover:            grayscale-0 + scale(1.05), 700ms transition
Overlay:          primary/20 + backdrop-blur-sm — "resting" dark overlay
Caption:          white, italic, body-sm weight 500
```

---

## 12. Do's and Don'ts (Enforced Rules)

### Do
- Use `surface-container-low` as the input field fill — always, no exceptions
- Use `border-l-2 border-primary` focus state on inputs — left border only, no ring
- Use `label-sm` ALL CAPS + `tracking-widest` for every input label
- Use `tertiary` / `tertiary-fixed` exclusively for AI-generated content
- Use `shadow-editorial` for all floating card panels
- Use tonal layering (container-low → container-lowest) instead of borders between sections
- Use `success` (#10B981), `warning` (#F59E0B), `critical` (#EF4444) for merit tier badges
- Use `-0.02em` letter-spacing on all display/headline text
- Keep `outline-variant` ghost borders at ≤20% opacity when unavoidable

### Don't
- Don't use `1px solid` borders to divide sections — use background shifts
- Don't use `tertiary` / Future Purple on anything non-AI
- Don't use pure black in shadows — use `rgba(51, 65, 85, ...)` only
- Don't use standard blue for any informational state — use primary (teal) or tertiary (purple)
- Don't use high-intensity shadows — if it looks "floating" it's too dark
- Don't use default Inter letter-spacing on display styles — tighten to `-0.02em`
- Don't use `image_picker` camera on Flutter Web — always branch on `kIsWeb`
- Don't show raw RIASEC scores to students

---

## 13. Flutter Implementation Notes

### ThemeData mapping

```dart
// Colors
static const Color primary        = Color(0xFF005C55);
static const Color primaryContainer = Color(0xFF0F766E);
static const Color tertiary       = Color(0xFF6616D7);
static const Color tertiaryFixed  = Color(0xFFEADDFF);
static const Color secondary      = Color(0xFF515F74);
static const Color surface        = Color(0xFFF7F9FB);
static const Color surfaceContainerLowest = Color(0xFFFFFFFF);
static const Color surfaceContainerLow    = Color(0xFFF2F4F6);
static const Color surfaceContainer       = Color(0xFFECEEF0);
static const Color surfaceContainerHigh   = Color(0xFFE6E8EA);
static const Color onSurface      = Color(0xFF191C1E);
static const Color outline        = Color(0xFF6E7977);
static const Color outlineVariant = Color(0xFFBDC9C6);
static const Color error          = Color(0xFFBA1A1A);
// Semantic
static const Color success        = Color(0xFF10B981);
static const Color warning        = Color(0xFFF59E0B);
static const Color critical       = Color(0xFFEF4444);
```

### TextTheme mapping

```dart
displayLarge:  Inter 56px w700 ls:-0.02em
headlineLarge: Inter 36px w700 ls:-0.02em
headlineMedium: Inter 28px w600 ls:-0.02em
titleLarge:    Inter 20px w600 ls:-0.01em
bodyLarge:     Inter 16px w400 lh:1.6
bodyMedium:    Inter 14px w400 lh:1.5
labelLarge:    Inter 14px w600
labelMedium:   Inter 12px w600 ls:0.05em
labelSmall:    Inter 11px w600 ls:0.08em
```

### InputDecoration standard

```dart
InputDecoration(
  filled: true,
  fillColor: surfaceContainerLow,    // #F2F4F6
  border: OutlineInputBorder(
    borderRadius: BorderRadius.circular(12),
    borderSide: BorderSide.none,
  ),
  focusedBorder: OutlineInputBorder(
    borderRadius: BorderRadius.circular(12),
    borderSide: BorderSide.none,
  ),
  // Left border accent via a Stack + Container overlay in Flutter
  // (Flutter InputDecoration doesn't natively support left-border-only focus)
  contentPadding: EdgeInsets.all(16),
  labelStyle: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, letterSpacing: 0.08),
)
```

> **Flutter left-border focus workaround:** Wrap the `TextField` in a `Stack` with a `Container` positioned left that toggles `color: primary` on focus — or use a `DecoratedBox` parent that responds to `FocusNode.hasFocus`.

### Box shadow

```dart
BoxDecoration(
  boxShadow: [
    BoxShadow(
      color: Color(0x0F334155),   // rgba(51,65,85,0.06)
      blurRadius: 40,
      offset: Offset(0, 12),
    ),
  ],
)
```

---

## 14. Screen-Level Token Checklist

| Screen | AppBar | Progress | Left panel | Form card radius | Input style | Special |
|---|---|---|---|---|---|---|
| Login | Minimal, no step | None | Branding + features | `radius-2xl` (32px) | Standard left-border focus | Glow blobs |
| Signup | Logo + school icon | None | Branding + AI Pulse | Matches page container | Icon-prefix fields | AI Insight Pulse |
| RIASEC Quiz | Full + step "2 of 4" | Fixed 6px primary bar | None | `radius-lg` (12px) per question card | Likert buttons | Progress bar sticky |
| Grades Input | Full + step | Fixed bar | None | Standard | Dropdown + text | OCR upload + verification modal |
| Capability Assessment | Full + step | Fixed bar | None | Standard | MCQ option buttons | Subject tabs |
| Chat Shell | Standard nav | None | None | Bubble radius | N/A | AI bubbles use tertiary, user bubbles use primary |
| Recommendation Dashboard | Full nav + avatar | None | Profile summary | `radius-xl` (16px) cards | N/A | Mismatch banner, merit badges, LagScoreBadge |

---

*Design System v1.0 — April 2026*
*Extracted from: DESIGN.md + 12 HTML mockups (Stitch AI export)*
*Authoritative for all Flutter implementation from this point forward*
*Maintained by: Khuzzaim (Flutter) in coordination with Architecture Chat*