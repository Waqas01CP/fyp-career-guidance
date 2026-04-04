# logs/README.md — Session History Navigation
## FYP: AI-Assisted Academic Career Guidance System
### Read this file first before reading any log file in this directory.
### Last updated: 2026-04-04

This file is the navigation index for all session logs in this directory.
Any Claude Code instance (Sonnet or Opus) that opens this directory must
read this file first. It tells you what happened in prior sessions, where
to find specific records, and how to chain backwards through history when
you need more detail than the summaries here provide.

CLAUDE.md at the repository root references this file. If you were sent
here by CLAUDE.md, you are in the right place.

---

## MAINTENANCE RULES — EVERY CLAUDE CODE INSTANCE MUST FOLLOW THESE

These rules apply to every model (Sonnet, Opus, or any future model) that
writes a log file to this directory or any subdirectory.

1. After writing any log file anywhere in logs/, update the correct
   summary table in this README before ending your session. Never write
   a log file and leave this README out of date.

2. When updating a summary table, add a new row. Never delete or modify
   existing rows — they are the permanent historical record.

3. Write summaries in compressed form: what was done, what changed, what
   the outcome was. No prose. No reasoning. No elaboration beyond what a
   future model needs to orient itself.

4. If you are starting a new session and this README does not have an
   entry for a log file you can see in the directory, read that file and
   add its entry to the correct table before doing anything else.

5. Chain-reading rule: when you need detail beyond what this README
   provides, read the most recent relevant log file first. That file
   references the one before it. Read backwards through the chain only
   as far as you need — stop when you have enough context for your
   current task. This README is the primary context. Individual files
   are for depth only when needed.

6. Never modify the folder structure of logs/ without an explicit
   instruction from the user. The three folders (root, audits/,
   changes/) are defined below and must not change without instruction.

---

## FOLDER STRUCTURE
logs/
├── README.md                        ← this file — read first always
├── session-YYYY-MM-DD-[desc].md              ← existing logs (pre-rules file)
├── claude-code-YYYY-MM-DD-HH-MM-[desc].md   ← new logs (per CLAUDE_CODE_RULES.md)
│                                               Both are standard Claude Code sessions
│                                               (Sonnet or other models)
├── audits/
│   └── [date]-opus-audit-[desc].md  ← Claude Code Opus audit reports only
│                                      Written after Opus audits the repo.
│                                      Never written by Sonnet.
└── changes/
    └── [date]-opus-changes-[desc].md ← Claude Code Opus change records only
                                       Written after Opus applies fixes from
                                       an audit. Contains the input prompt
                                       at the top, then all changes made,
                                       then references to the audit file
                                       that triggered it.
                                       Never written by Sonnet.

**Who writes where:**
- Standard Claude Code sessions (Sonnet, any model): logs/ root only
- Claude Code Opus audit runs: logs/audits/ only
- Claude Code Opus change runs: logs/changes/ only
- No model writes to a folder outside its lane without explicit instruction

---

## STANDARD SESSION LOGS (logs/ root)

These are regular Claude Code sessions — backend fixes, frontend work,
data updates, and other implementation tasks.

| File | Date | Model | What was done | Outcome |
|---|---|---|---|---|
| session-2026-03-28-backend-sprint1-fix.md | 2026-03-28 | Sonnet | Fixed POST /auth/register returning 500. Root causes: (1) SQLAlchemy mapper error — 4 of 6 models not imported in models/__init__.py. Fixed by adding `import app.models` to main.py. (2) passlib 1.7.4 incompatible with bcrypt 5.0.0 — replaced passlib with direct bcrypt calls in security.py. | COMPLETE. Register returns 201. All 9 endpoints passing. Sprint 1 backend gate passed. |
| session-2026-04-01-backend-sprint2-prereq.md | 2026-04-01 | Sonnet | Sprint 2 prerequisite: create ChatSession on register, return session_id from GET /profile/me. Fixed broken auth.py (wrong flush order, new_user typo). Added session query to profile.py get_profile. Added session_id: Optional[UUID] to ProfileOut schema. | COMPLETE. Register 201 ✓. GET /profile/me returns non-null session_id UUID ✓. Commit: 2ace388. |
| session-2026-04-04-logs-readme-setup.md | 2026-04-04 | Sonnet | Created logs/README.md navigation index, logs/audits/ and logs/changes/ subdirectories with .gitkeep files. | COMPLETE. All folders and README verified present. |

---

## OPUS AUDIT LOGS (logs/audits/)

These are structured audit reports produced by Claude Code Opus after a
full system audit. Each was triggered by a prompt generated in the
Claude.ai Opus chat after discussion with the user.

| File | Date | Scope | Summary | Findings count |
|---|---|---|---|---|
| (none yet) | — | — | — | — |

---

## OPUS CHANGE LOGS (logs/changes/)

These are change records produced by Claude Code Opus after applying
fixes identified in an audit. Each file contains the input prompt at
the top and references the audit file that triggered it.

| File | Date | References audit | What was changed | Outcome |
|---|---|---|---|---|
| (none yet) | — | — | — | — |

---

## HOW TO CHAIN-READ WHEN YOU NEED MORE DETAIL

1. Read this README first — always. It is your primary context.
2. If you need more detail on a specific session, find its row in the
   correct table above and open that file.
3. That file will reference the session before it if relevant context
   exists there. Follow the reference only if you need it.
4. Stop chaining when you have enough context for your current task.
   Do not read the entire history unless your task requires it.
5. If you are a Claude Code Opus instance starting an audit or change
   session: read this README, then read the most recent file in
   logs/audits/ if one exists, then read the most recent file in
   logs/changes/ if one exists. Then proceed with your task.
