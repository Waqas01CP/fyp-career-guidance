# Design System Specification: The Academic Intelligence Framework

This document outlines the visual and structural language for a high-end, AI-assisted academic career guidance platform. This design system moves beyond generic SaaS patterns to create a "Digital Curator" experience—merging the prestige of a traditional institution with the kinetic energy of advanced artificial intelligence.

---

## 1. Creative North Star: The Scholarly Edge
The "Digital Curator" philosophy treats the interface not as a software dashboard, but as a high-end editorial publication. We break the "template" look by utilizing intentional white space, rhythmic typography, and **Tonal Layering** rather than structural lines. The goal is to make the user feel as though they are interacting with an intelligent, living document that prioritizes clarity, authority, and future-forward insight.

**Core Principles:**
*   **Intentional Asymmetry:** Use the 8dp grid to create unbalanced but harmonious layouts that guide the eye naturally toward primary insights.
*   **Breathing Room:** White space is not "empty"; it is a functional element that signifies prestige and reduces cognitive load during complex career planning.
*   **Kinetic Sophistication:** AI interactions are never jarring. They are signaled through soft, purple-tinted transitions and glass-like overlays.

---

## 2. Color & Surface Philosophy

We employ a "No-Line" rule. Traditional 1px borders are prohibited for sectioning. Boundaries are defined through background shifts and nested tonal hierarchies.

### The Color Palette (Material Design Tokens)
*   **Primary (`#005c55` / `#0f766e`):** Academic Teal. Use for authoritative actions and brand markers.
*   **Secondary (`#515f74`):** Deep Slate. Used for grounding elements and secondary information.
*   **Tertiary (`#6616d7` / `#7f3ef0`):** Future Purple. Reserved exclusively for AI-generated insights, recommendations, and "thinking" states.
*   **Surface (`#f7f9fb`):** Paper White. The foundation of the editorial experience.

### Surface Hierarchy & Nesting
Instead of a flat grid, treat the UI as a series of stacked sheets.
1.  **Base Layer:** `surface` (#f7f9fb)
2.  **Sectioning:** `surface-container-low` (#f2f4f6) for large background blocks.
3.  **Content Cards:** `surface-container-lowest` (#ffffff) to create a subtle "lift" against the background.
4.  **Floating UI/Modals:** Use `surface-bright` with a **Glassmorphism** effect: 80% opacity with a `20px` backdrop-blur to maintain context of the underlying data.

**The "Glass & Gradient" Signature:**
To provide visual soul, main CTAs or "Career Path" headers should utilize a subtle linear gradient: `primary` (#005c55) to `primary-container` (#0f766e) at a 135-degree angle. This adds a depth that flat hex codes cannot achieve.

---

## 3. Typography: The Editorial Scale

We use **Inter** exclusively, leaning on its variable weight capabilities to create an authoritative hierarchy.

| Level | Size | Weight | Role |
| :--- | :--- | :--- | :--- |
| **display-lg** | 3.5rem | 700 (Bold) | Hero stats and impact numbers. |
| **headline-md** | 1.75rem | 600 (Semi-Bold) | Section headers. |
| **title-lg** | 1.375rem | 500 (Medium) | Card titles and prominent labels. |
| **body-lg** | 1rem | 400 (Regular) | Primary reading text; high line-height (1.6) for legibility. |
| **label-md** | 0.75rem | 600 (Semi-Bold) | All-caps metadata or category tags. |

**Editorial Note:** Use `headline-sm` in `secondary` (#515f74) for sub-headers to create a sophisticated, muted contrast against `primary` titles.

---

## 4. Elevation & Depth (Tonal Layering)

Traditional drop shadows are largely replaced by **Tonal Layering**.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. The difference in hex value creates a soft, natural edge.
*   **Ambient Shadows:** For floating elements (like AI assistant bubbles), use an ultra-diffused shadow: `box-shadow: 0 12px 40px rgba(51, 65, 85, 0.06);`. The shadow color is a tinted version of `on-surface`, not pure black.
*   **The Ghost Border:** If a divider is mandatory for accessibility, use `outline-variant` at 15% opacity. Never use 100% opaque lines.

---

## 5. Components

### Buttons
*   **Primary:** Filled with `primary` (#005c55), `on-primary` text. Border-radius: `md` (0.375rem). No shadow.
*   **AI Action:** Gradient fill (`tertiary` to `tertiary-container`). Use for "Generate Career Roadmap" or "Analyze CV."
*   **Secondary:** Ghost style. No background, `outline` token for the border at 20% opacity.

### Cards & Lists
*   **The Rule of No Dividers:** Forbid horizontal lines between list items. Use 16px of vertical white space (from the 8dp grid) and `body-sm` metadata to separate items.
*   **Hover State:** Shift background from `surface-container-lowest` to `surface-container-high` for a tactile, non-shadowed response.

### AI Thinking States (Unique Component)
*   **The Insight Pulse:** A `tertiary-fixed` (#eaddff) container with a subtle `2px` soft-glow. This houses AI-assisted suggestions, separating "human data" from "AI prediction."

### Input Fields
*   **Style:** Minimalist. No bottom line or box. Use `surface-container-highest` as a solid background fill with a `sm` radius.
*   **Focus State:** The background remains static, but a `2px` `primary` left-border appears to indicate activity, mimicking a cursor in a text editor.

---

## 6. Do’s and Don’ts

### Do
*   **Do** use asymmetrical margins (e.g., 64px left, 32px right) for dashboard layouts to create an editorial feel.
*   **Do** use `tertiary` (Future Purple) sparingly—only for elements where the AI is actively "adding value."
*   **Do** leverage the `surface-container` tiers to group related academic data without using boxes.

### Don't
*   **Don't** use 1px solid borders to separate sidebar and main content. Use a background color shift instead.
*   **Don't** use standard "Information" blue. All guidance-related info should use `primary` (Teal) or `tertiary` (Purple).
*   **Don't** use high-intensity shadows. If it looks like it’s "floating," the shadow is too dark. It should feel like it’s "resting."
*   **Don't** use default Inter tracking. Tighten `display` styles by `-0.02em` for a more premium, "inked" appearance.

---

## 7. Applied Colour Refinements
Document these confirmed changes made during
screen generation. These override Section 2 values:

Primary teal: #005c55 → #006B62 (brightened for
younger audience, keeps authority role)
Primary container: #0f766e → #00857A
Surface tint: updated to #007A71
All other colour tokens unchanged from Section 2.

Student demo persona locked across all screens:
Name: Ali Raza Khan
Education: Inter Part 2, Pre-Engineering,
Karachi Board
Budget: PKR 25,000 – 45,000 per month
Location: Karachi

---

## 8. Confirmed Component Decisions
Document these decisions made during critique
and generation that are not in Sections 1-6:

Border radius scale:
- Form cards: border-radius 2rem
- Buttons primary: border-radius 12-16px
- Chat bubbles: 18px 18px 4px 18px (student),
  18px 18px 18px 4px (AI)
- Chips and pills: border-radius 20px
- Input fields: border-radius 12px
- Modals: border-radius 20px

Shadow confirmed:
0 12px 40px rgba(51,65,85,0.06) — all floating elements

Input field pattern confirmed:
background-color surface-container-low (#f2f4f6),
no border, 2px left-border primary on focus,
border-radius 12px

AI panel pattern confirmed:
background #eaddff, border-left 4px solid #6616d7,
always includes auto_awesome icon in #6616d7,
label text uppercase 9px font-weight 700

Error states: always neutral slate — never error-red
except destructive confirmation dialogs.
Logout button: neutral surface styling, not error-red.

Three-colour role logic (locked — enforced across
all 16 screens):
- Teal #006B62: human actions, AppBars, primary
  CTAs, progress bars, focus accents
- Slate #515f74: secondary text, metadata, icons,
  ghost buttons, disabled states
- Purple #6616d7: AI-generated content ONLY.
  Never appears on non-AI elements under any
  circumstance.

---

## 9. Screen-Specific Component Decisions
Decisions made per screen during generation
and critique:

Chat screen:
- Student bubbles: right-aligned, #006B62 background,
  white text
- AI bubbles: left-aligned, white on
  surface-container-low, 3px #6616d7 left-border
- Suggested chips: all neutral default state
  (#515f74 text, #f2f4f6 background)

RIASEC Quiz:
- One question at a time (not scrollable list)
- Mobile AI panel: collapsed pill row visible only
  on mobile showing top 2 codes

Capability Assessment:
- Subject tabs: overflow-x scroll with right
  fade gradient overlay
- Current question: glow 0 0 0 2px rgba(0,107,98,0.25)

Assessment Complete screen:
- No button — auto-navigation only via progress bar
- Progress bar fills over 3 seconds then navigates

Error screen — 3 states confirmed:
- State 1: wifi_off icon — No Internet
- State 2: cloud_off icon — Server Timeout
- State 3: lock icon — Session Expired 401
  (clears flutter_secure_storage, navigates to login)

Splash screen:
- Dev routing annotation: display:none by default
- onboarding_stage values shown in annotation must
  match CLAUDE.md exactly

Onboarding Carousel:
- Shown only when no token in flutter_secure_storage
- Covers fresh install and post-logout

---

## 10. Viewport and Layout Decisions

All 16 screens use 390px mobile viewport:
meta viewport: width=390, initial-scale=1.0
body: max-width 390px, margin 0 auto,
      overflow-x hidden
html background: #d8dadc (phone surround simulation)
AppBar: sticky (not fixed), approx height 52px
Sprint label: fixed top-left, 9px uppercase,
              #515f74 text on #f2f4f6 background

Typography tracking confirmed:
Display text: letter-spacing -0.02em
Labels and badges: letter-spacing 0.08-0.12em,
                   text-transform uppercase
Body text: line-height 1.6
Minimum body font-size on mobile: 13px

---

## 11. Out of Scope — Do Not Implement

These were identified and removed during design review:
- Forgot Password backend endpoint (demo shows
  static "coming soon" — implement post mid-eval)
- Settings Change Password backend (same)
- GitHub social login button (wrong audience)
- ORCID social login button (wrong audience —
  removed from signup)
- Onboarding Carousel as a separate flow screen
  (it is an intro only, triggered by no-token state)
- Any 1px solid borders anywhere
- Hard drop shadows (only ambient shadows)
- Any font other than Inter
- Purple on any non-AI element
- Desktop/wide layouts (this is 390px mobile only)
- Red styling on logout or non-destructive actions

---

## 12. Change Log

v1.0 — Original specification (DESIGN.md sections 1-6)
v1.1 — Screen generation pass (Step 1):
        16 screens generated, 390px viewport applied,
        design tokens applied, sprint labels added
v1.2 — Design Critique pass (Step 2):
        Primary teal brightened #005c55 → #006B62,
        all 1px border violations fixed,
        raw Tailwind tokens replaced with design system,
        student persona standardised to Ali Raza Khan,
        logout de-escalated from error-red to neutral,
        AI panel pattern standardised across all screens
v1.3 — Architecture fixes (post Step 2):
        Error screen states corrected to match CLAUDE.md
        (wifi_off / cloud_off / lock),
        Assessment Complete button removed,
        Splash onboarding_stage values corrected to match
        CLAUDE.md locked values
v1.4 — UX Copy pass (Step 3 — April 2026):
        71 copy fixes applied across all 16 screens.
        - Persona standardised to Ali Raza Khan
          (Inter Part 2, Pre-Engineering, Karachi Board,
          PKR 25,000–45,000/month) across all screens
        - Technical jargon replaced with plain language
          for Pakistani student audience aged 15-18
        - AI insight panels hedged correctly — guarantee
          language removed throughout
        - Coming soon screens (Forgot Password, Change
          Password) updated with warm messaging
        - RIASEC scores corrected to locked demo values:
          I=88%, C=80%, E=70% (derived from POINT_5
          raw scores R=32,I=45,A=28,S=31,E=38,C=42)
        - Overrides: S-02 kept ("complete" is valid
          onboarding_stage per backend schema),
          CH-03 kept (chat shell is Sprint 1 by convention)
        - Wrong social providers removed (ORCID, GitHub)
        - Fabricated social proof numbers removed
        - Settings ghost nav items removed (no backend)
        - 2FA toggle removed (no backend endpoint)
        - Housing preference field removed (not in schema)
        Screens modified: all 16
v1.5 — Accessibility pass (Step 4 — April 2026):
        #6e7977 replaced with #515f74 for all readable
        text labels across all 16 screens,
        AppBar back buttons standardised to w-12 h-12
        (48px) with aria-label="Go back",
        form label/input pairs associated via id/for,
        ARIA roles added to all progress bars
        (role="progressbar" with aria-valuenow/min/max),
        SVG charts given role="img" with title elements,
        OCR modal given role="dialog" aria-modal aria-labelledby,
        focus-visible:outline indicators added to all CTAs,
        error state containers given role="alert",
        dev annotation dividers given aria-hidden="true",
        bottom nav changed from div to button/a elements
        with min-h-[48px],
        suggested chips padding increased to 12px 16px,
        checkboxes enlarged to h-6 w-6 with label for/id,
        question map cells changed from div to button,
        auto-redirect bar given role="status" aria-live="polite",
        message groups in chat given role="group" aria-label
        Screens modified: all 16

Reference files:
- DESIGN_SYSTEM_TOKENS.md — Step 0 Design System
  plugin output (complete structured token reference)
- CLAUDE.md — locked architecture decisions
  (in fyp-career-guidance repo)