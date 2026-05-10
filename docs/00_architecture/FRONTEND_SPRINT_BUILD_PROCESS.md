# Frontend Sprint Build Process
## FYP: AI-Assisted Academic Career Guidance System
## Scope: frontend/ directory — Flutter/Dart only

---

## The Build Process — One Screen Per Session

Every screen follows this process. Do not skip steps.

### PHASE 1 — READ BEFORE WRITING
Claude Code reads in this order. Confirm all read before proceeding:
1. logs/README.md
2. CLAUDE.md
3. docs/00_architecture/FRONTEND_CHAT_INSTRUCTIONS.md
4. docs/00_architecture/FRONTEND_SCREEN_CONTRACTS.md — contract for THIS screen only
5. docs/00_architecture/FRONTEND_DESIGN_SYSTEM.md — color roles, components, patterns
6. .claude/skills/flutter-official/flutter-building-layouts/skill.md
7. The relevant provider file(s) that this screen connects to
8. The relevant service file(s) that this screen calls

DO NOT read design/screen_mockups/ — that folder is deprecated and replaced
by FRONTEND_SCREEN_CONTRACTS.md and FRONTEND_DESIGN_SYSTEM.md.

### PHASE 2 — PLAN
Before writing any Dart code, produce a written plan:
- What widgets this screen uses
- What state it reads (which Riverpod provider)
- What API calls it makes (which service method)
- All UI states (loading, loaded, error, empty)
- Navigation triggers (what happens on each outcome)
- How it satisfies FRONTEND_SCREEN_CONTRACTS.md for this screen

State: "Plan reviewed against FRONTEND_SCREEN_CONTRACTS.md. No conflicts found."
Only proceed after this statement.

### PHASE 3 — IMPLEMENT
Build the screen as a single Dart file.
Use only widgets and patterns from DESIGN_HANDOFF.md.
Do not invent design decisions — every visual decision is already made.

### PHASE 4 — SELF-REVIEW
Re-read every line. Check:
1. Colours use ColorScheme roles or named exceptions from FRONTEND_DESIGN_SYSTEM.md
2. Navigation routes match CLAUDE.md screen inventory
3. API calls use the correct service method and handle errors
4. Loading states are shown (ThinkingIndicator or CircularProgressIndicator)
5. No hardcoded strings that should come from the backend

### PHASE 5 — TEST
Run: flutter run (on emulator or connected device)
Verify against FRONTEND_SCREEN_CONTRACTS.md — all states render, all navigation
works, all API calls succeed and handle errors.
Check: layout, colours, navigation, API integration, error states.

Document test result: PASS or FAIL with specific issues.

### PHASE 6 — LOG
Write to: logs/claude-code-YYYY-MM-DD-HH-MM-[screenname]-screen.md

Required sections:
- Files changed
- Files read
- Plan summary
- Deviations from FRONTEND_SCREEN_CONTRACTS.md (if any — must be justified)
- Test result (flutter run output, all states verified)
- Known issues

Then update logs/README.md.

---

## Flutter-Specific Rules

**No venv.** Flutter manages its own dependencies.
**Always run from frontend/ directory.** All flutter commands run from there.
**Run flutter pub get after any pubspec.yaml change.**
**One screen per Claude Code session.**

**Starting a session:**
```bash
cd frontend
flutter pub get
flutter run
```

**After adding a new package:**
```bash
flutter pub add package_name
# OR add to pubspec.yaml manually, then:
flutter pub get
```

**Never commit pubspec.lock conflicts** — run flutter pub get and let it regenerate.

---

## Review Loop

**Full process — do not skip any step:**

```
Architecture Chat produces Claude Code prompt
↓
Frontend Chat reviews the PROMPT (before execution) — catches wrong Riverpod patterns, bad API usage, design deviations — GREEN or issues to fix
↓
Claude Code executes the prompt (VS Code, Sonnet 4.6, Medium effort)
↓
Commit and sync repo
↓
Architecture Chat reviews the LOG — design fidelity, routing correctness, API contract
↓
Frontend Chat reviews the CODE — Dart quality, Riverpod patterns, null safety, performance — GREEN or RED with issues
↓
GREEN → next screen
```

Frontend Chat reviews TWICE — once before execution (prompt review)
and once after (code review). This matches the backend flow exactly.

---

## Log Rules (same as backend)

1. Read logs/README.md before starting any session
2. Write log to logs/ root: logs/claude-code-YYYY-MM-DD-HH-MM-[name].md
3. Update logs/README.md immediately after writing the log