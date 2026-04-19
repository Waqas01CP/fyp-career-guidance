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
```
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
```

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
| claude-code-2026-04-17-00-00-compute-future-values-rewrite.md | 2026-04-17 | Sonnet | Rewrote compute_future_values.py — fixed 3 bugs: wrong field key (lag_type→lag_category), nonexistent raw sub-object (now reads actual schema fields), wrong weight key (layer3→layer3a/layer3b). Implemented 5-step algorithm: extract raw signals, min-max normalise, missing-signal redistribution, FutureValue formula, write-back. | COMPLETE. Empty array ✓. Single FAST entry → future_value=4.75 ✓. lag_model.json restored to []. |
| claude-code-2026-04-17-11-00-filter-node.md | 2026-04-17 | Sonnet | Implemented FilterNode production code (Sprint 3). Replaced stub with full 5-check constraint filtering: stream eligibility, mandatory subjects, merit tiers, budget soft flag, zone soft flag. calculate_aggregate() helper, minimum display rule, matric_planning bypass. Wrote 10 pytest tests. | COMPLETE. 10/10 tests pass. aggregate_formula added to roadmap entries for ScoringNode integration. 3 items flagged for Architecture Chat review. |
| claude-code-2026-04-18-00-00-filter-node-v2.md | 2026-04-18 | Sonnet | Updated FilterNode per CLAUDE.md v1.9: added Check 0 (HEC/council legal floor, hard exclusion separate from hard_excluded_raw), calculate_estimated_merit() helper (assessment proxy for entry test), Check 3 updated to use estimated_merit, Check 3b (entry_test_harder_than_assessed for hard/extreme tiers), shift field in all roadmap entries, aggregate_formula corrected (pre-existing omission). Added CAPABILITY_PROXY_DEFAULT and ENTRY_TEST_SUBJECT_MAP to config.py. Added 3 new tests. | COMPLETE. 13/13 tests pass. 6 items flagged for Architecture Chat review. |
| claude-code-2026-04-18-12-00-neduet-validation-fixes.md | 2026-04-18 | Sonnet | NED universities.json validation fixes: (1) Fee corrections — Group A: 55045→59045, BS CT: 60475→64475, Arch: 55045→61245 (10 sem), Ind Chem: 55045→60845. (2) Merit history: 6 explicit replacements (order fix + data verified) + 5 additional shift-error corrections (comp_finance, urban_planning, dev_studies, chemistry, textile_science). (3) 2025 cutoffs appended to 29 degrees; 3 range updates triggered. (4) data_last_verified: March→April 2026. | COMPLETE. All 9 verification checks pass. Waqas flagged: test_filter_node.py has stale fee comment (60475 → 64475). |
| neduet-extraction-audit-2026-04-18.md | 2026-04-18 | Sonnet | Read-only extraction of all 33 NED degrees from universities.json (post validation-fixes). Columns: degree_id, name, min_percentage_hssc, fully_eligible_streams, conditionally_eligible_streams, fee_per_semester, duration_years, merit_history_years_present, cutoff_range_min, cutoff_range_max. Corrections appended: (1) neduet_bs_management_sci merit_history replaced (synthetic 71.0–73.81 → verified 66.0–77.0; band 2.81→11.0). (2) neduet_bs_animation min_percentage_hssc 50.0→60.0 (CT programme floor). (3) neduet_bs_chemistry name "BS Chemistry"→"BS Industrial Chemistry". | COMPLETE. 33 rows written. Three correction notes appended to log. |
| claude-code-2026-04-18-14-00-scoring-node.md | 2026-04-18 | Sonnet | Implemented ScoringNode production code (Sprint 3). Replaced stub with full RIASEC dot product normalisation, FutureValue lookup from lag_model computed field, per-subject capability blend (applied before calculate_aggregate), mismatch detection with * 100 scaling per Point 2 Section 8. Missing field_id fallback (match=0.5, future=5.0, degree never dropped). Wrote 10 pytest integration tests + fixture data for all 32 NED field_ids via monkeypatch on DATA_DIR. | COMPLETE. 18/18 tests pass. 3 items flagged for Architecture Chat review: (1) exclude 0-mark subjects from blend? (2) confirm aggregate not fed into total_score? (3) skip mismatch for unknown field_ids vs neutral fallback? |
| claude-code-2026-04-18-22-00-profiler-node.md | 2026-04-18 | Sonnet | Implemented ProfilerNode production code (Sprint 3). Replaced Sprint 1 stub with full LLM-based conversational extraction using ChatGoogleGenerativeAI. Module-level LLM init (temperature=0), PII scrubbing, structured JSON output, null-safe field merging, check_profiling_complete() helper, O/A Level stream confirmation. Created pytest.ini (new). Wrote 4 unit tests + 3 integration tests (real Gemini API). Appended: Architecture Chat 4-fix review. Appended: model switch test; langchain-anthropic added to requirements.txt. Appended 2026-04-19: stated_preferences string→list normalisation fix (3 lines after merge into active_constraints — prevents char-by-char iteration in ScoringNode/ExplanationNode). | COMPLETE. 4/4 unit tests pass. |
| logs/llm-output-profiler-2026-04-19.md | 2026-04-19 | Sonnet | Model output comparison log. Run 1 (gemini-2.5-flash): budget=50000, home_zone=2 ✓. Run 2 (gemini-3.1-flash-lite-preview): same extraction ✓; required content list-flatten fix in profiler.py (Gemini 3.1 returns content as list of parts not string). Config reverted to gemini-2.5-flash. | COMPLETE. |
| claude-code-2026-04-19-13-00-supervisor-node.md | 2026-04-19 | Sonnet | Implemented SupervisorNode production code. Replaced Sprint 1 stub with full LLM intent classifier: module-level init, Gemini 3.1 content list-flatten fix, VALID_INTENTS validation, empty-messages guard, invalid/failure fallbacks. Deviation: Gemini 3.1 requires HumanMessage alongside SystemMessage (lone SystemMessage rejected). 7/7 unit tests pass. Phase 5b: all 7 test messages classified correctly including Roman Urdu. | COMPLETE. 3 items flagged for Architecture Chat review. |
| logs/llm-output-supervisor-2026-04-19.md | 2026-04-19 | Sonnet | SupervisorNode LLM output log. gemini-3.1-flash-lite-preview. 7 test messages all correctly classified. Roman Urdu → market_query ✓. | COMPLETE. |
| claude-code-2026-04-19-14-00-answer-node.md | 2026-04-19 | Sonnet | Implemented AnswerNode production code (Sprint 3). Fixed fetch_fees.py field name bug (university_name→name, degree_name→name). Full intent dispatch: fee_query/market_query/follow_up+clarification/out_of_scope. Entity extraction via short LLM calls with nickname mappings. Empty tool result fallback. LLM failure handling. 8/8 unit tests pass. Phase 5b: fee_query ✓, market_query fallback (lag_model empty — expected) ✓, follow_up ✓, out_of_scope ✓. 4 items flagged for Architecture Chat review. | COMPLETE. |
| logs/llm-output-answer-node-2026-04-19.md | 2026-04-19 | Sonnet | AnswerNode LLM output log. gemini-3.1-flash-lite-preview. fee_query: correct fee data + budget comparison ✓. market_query: fallback (lag_model.json empty — correct) ✓. follow_up: answered from roadmap ✓. out_of_scope: polite decline ✓. | COMPLETE. |

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
