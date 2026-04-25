# Post-Demo Technical Decisions
## FYP: AI-Assisted Academic Career Guidance System
## Recorded: April 2026

---

## 1. CORS Configuration

### Current State
`backend/app/main.py` CORSMiddleware currently allows specific
localhost ports (3000, 8080, 8081, 8090). This causes CORS errors
when Flutter Web runs on a different localhost port during development.

### Why It Does Not Affect Android
Android apps make direct HTTP requests — no browser CORS restrictions
apply. CORS is a browser-only enforcement. Testing on Android emulator
or physical device bypasses this entirely.

### What Needs to Happen Post-Demo
When Flutter Web is deployed to a real domain (e.g. Netlify, Vercel,
Firebase Hosting), add that exact URL to allow_origins:

```python
allow_origins=[
    "https://fyp.yourapp.com",  # replace with actual deployed URL
],
```

Note: `allow_origins=["*"]` with `allow_credentials=True` is rejected
by modern browsers in production — explicit origins are required.

### File to Update
`backend/app/main.py` — CORSMiddleware allow_origins list

---

## 2. Flutter Web — How It Works

### Key Facts
- Same Dart codebase builds Android APK and Flutter Web
- Command: `flutter build web` → produces HTML/JS/CSS
- Deploy to any static host: Netlify, Vercel, Firebase Hosting
- No React, no separate codebase needed

### Limitations to Know
- Canvas-based renderer — poor SEO (not relevant for login-gated app)
- Large initial load (~2-4MB Dart runtime downloads before render)
- No desktop-responsive breakpoints currently — mobile layout shows
  on wide screens (looks stretched)
- Tablet layout (768dp+) will look stretched — not target device

### What Works Fine Now
- Mobile browser (360-430dp): looks correct — same as Android app
- Login-gated app with no SEO requirement: Flutter Web is appropriate

---

## 3. Android APK — Device Compatibility

### Current State
- minSdkVersion: 21 (Android 5.0+)
- Package name: com.fyp.career_guidance (confirmed correct)
- Covers all Android phones in use in Pakistan including 2017-2018
  budget devices (2GB RAM)

### Build Commands
```bash
cd frontend
flutter build apk --debug    # for testing — shareable via WhatsApp/USB
flutter build apk --release  # for production — requires signing
```

### Device Coverage
- 360dp width (budget phones: Tecno, Infinix): ✅
- 390dp width (standard mid-range): ✅ designed for this
- 430dp width (large phones: Pixel 7 Pro, Samsung S series): ✅
- 768dp+ (tablets): layout stretches — not target device

---

## 4. Mobile Responsiveness — Current State

### What Is Already Handled
Every screen has:
- `SingleChildScrollView` — content scrolls instead of overflowing
- `SafeArea` — handles notches, navigation bars, status bars
- No fixed heights on text containers — `Flexible`/`Expanded` used
- Font scaling never overridden — text reflows on accessibility sizes

### What Is Not Handled
- Tablet layouts (768dp+): single-column mobile layout looks stretched
- Desktop web: same stretched mobile layout on wide viewport
- No breakpoint-aware navigation (hamburger menu on wide screens etc.)
- No fluid typography (font sizes do not scale with viewport width)

---

## 5. Responsive Design — Post-Demo Plan

### Decision
Do responsive design AFTER all screens are complete and AFTER demo.
Reasons:
- Demo target is Android — responsive web not needed for April 29
- Cannot make good layout decisions for unfinished screens
- Retrofitting responsive is non-destructive — adds a wrapper layer
- Doing it screen-by-screen during build produces inconsistent results
- One dedicated pass after completion is faster and more consistent

### Simple Fix (2-3 hours, one session)
Content-cap approach — makes Flutter Web on desktop look clean
immediately without full responsive implementation:

```dart
// Wrap every screen body with:
Center(
  child: ConstrainedBox(
    constraints: const BoxConstraints(maxWidth: 600),
    child: existingContent,
  ),
)
```

Solves the "stretched mobile layout on wide screen" problem.
Not true responsive but professional-looking for web.

### Full Professional Approach (3-5 sessions)
One dedicated pass after demo covering:
1. Establish breakpoints: mobile (<600dp), tablet (600-1024dp),
   desktop (>1024dp)
2. Add global content width cap via wrapper widget
3. Identify screens that genuinely benefit from two-column layout:
   Dashboard, Chat, Grades Input — likely candidates
4. Fluid typography: TextTheme that scales with screen width
5. Adaptive icons and spacing for touch vs mouse contexts
6. Breakpoint-aware navigation where needed

### Screens Likely to Benefit from Two-Column Layout
- Recommendation Dashboard: degree cards grid on tablet/desktop
- Chat screen: sidebar conversation list + main chat area
- Grades Input: form left + live preview right

### Screens Fine with Width Cap Only
- Splash, Carousel, Login, Signup — single-column always appropriate
- RIASEC Quiz — one question at a time, single column is correct
- Assessment — same as RIASEC Quiz
- Profile — simple settings list

---

## 6. Summary of Post-Demo Tasks Related to This Discussion

| Priority | Task | Effort |
|---|---|---|
| High | Add deployed Flutter Web URL to CORS allow_origins | 5 min |
| High | Build and sign release APK for distribution | 1 session |
| Medium | Content-cap approach for Flutter Web (maxWidth: 600) | 2-3 hours |
| Low | Full responsive breakpoints (tablet + desktop layouts) | 3-5 sessions |
| Low | Fluid typography system | 1 session |
| Low | Two-column layouts for Dashboard, Chat, Grades Input | 3 sessions |

---

## 7. Recommended Order After Demo

1. Fix CORS with deployed URL (when Flutter Web is hosted)
2. Simple content-cap (one session — quick win for web)
3. Release APK signing and distribution setup
4. Full responsive design pass if web usage is significant