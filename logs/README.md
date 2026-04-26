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
| claude-code-2026-04-19-14-00-answer-node.md | 2026-04-19 | Sonnet | Implemented AnswerNode production code (Sprint 3). Fixed fetch_fees.py field name bug. Full intent dispatch. 8/8 unit tests. Appended follow-up fix: slim roadmap (~50 tokens/entry vs ~200), student summary (~150 tokens) added to follow_up prompt path. lag_model.json stub created (was empty) — 32 NED field entries with computed.future_value set, raw data null stubs. DATA_CHAT_INSTRUCTIONS.md and CLAUDE.md maintenance rule wording updated. 8/8 answer_node tests + 50/50 full suite pass. | COMPLETE. |
| logs/llm-output-answer-node-2026-04-19.md | 2026-04-19 | Sonnet | AnswerNode LLM output log. gemini-3.1-flash-lite-preview. fee_query: correct fee data + budget comparison ✓. market_query: fallback (lag_model.json empty — correct) ✓. follow_up: answered from roadmap ✓. out_of_scope: polite decline ✓. | COMPLETE. |
| claude-code-2026-04-20-14-00-explanation-node.md | 2026-04-20 | Sonnet | Implemented ExplanationNode production code (Sprint 3). Replaced Sprint 1 stub with full LLM recommendation generator: thought trace trimming, rerun diff (Part 0), mismatch notice (Part 1), matric_planning mode, 5-degree context builder, FLAG_DESCRIPTIONS plain-language translation, entry test gap advice (Option D, threshold 65%), null market data fallback to career_paths dict, PII scrubbing. Fix 1: trace trimming changed to degree_name + university_name matching. Fix 2: LLM-native language detection — removed detect_language_hint(), inject recent_text into prompt verbatim; handles all spelling variants natively. 12/12 tests pass. 65/65 full suite. | COMPLETE. |
| logs/llm-output-explanation-node-2026-04-20.md | 2026-04-20 | Sonnet | ExplanationNode LLM output log. gemini-3.1-flash-lite-preview. Run 1 (first recommendation): correct 4-part structure, physics gap cited, 1240 jobs/month used, Part 3 BE EE advice specific ✓. Run 2 (mismatch + 2 swaps): Part 0 fired correctly, mismatch framed as observation not rejection ✓. Token count ~975 (above 400-700 target). Thought trace trimming works in test data (synthetic degree_ids) but not in production (FilterNode uses degree_label format). | COMPLETE. |
| claude-code-2026-04-20-15-00-core-graph.md | 2026-04-20 | Sonnet | Wired core_graph.py into live /chat/stream endpoint. Added psycopg[binary] to requirements.txt. Added checkpoint_db_url property to config.py (psycopg3 URL, sslmode=require only). Replaced lifespan stub in main.py with AsyncPostgresSaver init + checkpointer.setup() + build_graph(). Replaced mock_stream in chat.py with real astream_events pipeline: NODE_STATUS_MAP, lag_model loading, _build_university_card, _build_roadmap_timeline, _write_recommendation helpers, full real_stream() generator. Fixed: psycopg3 URI prepare_threshold error (from_conn_string passes it internally). Fixed: Windows ProactorEventLoop incompatibility (--loop asyncio --reload required). | COMPLETE. 65/65 tests pass. All 6 integration tests pass including session restore across server restart. |
| claude-code-2026-04-24-00-00-android-package-name.md | 2026-04-24 | Sonnet | Changed package name from com.example.frontend_app → com.fyp.career_guidance across all project targets. Android: build.gradle.kts, MainActivity.kt, AndroidManifest.xml, Kotlin folder rename. Web: manifest.json (name/short_name/description), index.html (title/apple-title/description). iOS: Info.plist (CFBundleDisplayName/CFBundleName), project.pbxproj (all 6 PRODUCT_BUNDLE_IDENTIFIER entries). README.md rewritten with project-specific content. Desktop platforms (Windows/macOS/Linux) left as-is — not project targets per CLAUDE.md. | COMPLETE. flutter build apk --debug exit 0. Android+Web+iOS CLEAN. |
| claude-code-2026-04-18-14-00-scoring-node.md (appended) | 2026-04-24 | Sonnet | Fixed OR-branch fallback in scoring_node.py: replaced single `if field_id not in affinity_matrix or field_id not in lag_model` block with two independent lookup blocks, each with its own warning+trace+default. Fix resolves Opus audit CONCERN: empty affinity_matrix.json was forcing total_score to constant 0.5 for all degrees by discarding real future_value from lag_model. | COMPLETE. 18/18 scoring tests pass. 62/62 full suite pass. |
| claude-code-2026-04-24-12-00-foundation-providers-main.md | 2026-04-24 | Sonnet | Frontend foundation: rewrote 3 ChangeNotifier stubs → StateNotifier (auth/profile/chat providers). Fixed recommendation.dart 2 bugs (riskFactor double→String, rozeeLastUpdated missing). Added id field to ChatMessage. Replaced stock counter main.dart with ProviderScope + AppRouter + 16 named routes. Applied 3 CLAUDE.md conflict corrections: no-token→carousel, not_started→riasec-quiz, ChatMessage.id. | COMPLETE. flutter analyze: 0 errors. flutter run (Chrome): clean launch, routes to /onboarding as expected. |
| claude-code-2026-04-24-15-00-splash-carousel-screens.md | 2026-04-24 | Sonnet | Built 2 screens: SplashScreen (ConsumerStatefulWidget, animated loading bar 0→120px 1800ms, routing by onboardingStage) and CarouselScreen (3 slides, PageView BouncingScrollPhysics, AnimatedContainer dots, Get Started on slide 3). No new packages. 3 justified deviations from DESIGN_HANDOFF.md (Icons.auto_stories, no SVG/CustomPainter, network error → /onboarding). main.dart NOT modified per HARD RULES — screens need manual wiring before testing. | COMPLETE. flutter analyze: 0 issues. flutter run not executed (main.dart wiring pending). |
| claude-code-2026-04-24-15-00-splash-carousel-screens.md (appended) | 2026-04-25 | Sonnet | Fix 1: added `case 'complete': return '/chat'` to _routeForStage() in splash_screen.dart — critical bug: returning users after first chat session were routed to RIASEC quiz. Fix 2: bento label in carousel_screen.dart — color 0xFF6E7977→0xFF515F74 (border token→text token), fontSize 7→10 (below 9px accessibility minimum). | COMPLETE. flutter analyze: 0 issues. |
| claude-code-2026-04-25-login-signup.md | 2026-04-25 | Sonnet | Built Login and Signup screens (two screens one session — justified: shared auth flow). Login: ConsumerStatefulWidget, 2 controllers+FocusNodes, gradient bar, AnimatedContainer focus border, Forgot Password greyed no-op (onPressed: null, slate colour), post-login _routeForStage includes 'complete'. Signup: 5 controllers+FocusNodes, two-column first/last name, live password rules (_hasMinLength/_hasNumber/_hasUppercase), AnimatedSwitcher rule icons, 409 email-exists error. AuthService.register() updated with fullName param + 409 handling. AuthNotifier.register() updated with on Exception catch + email_exists detection. main.dart /login and /signup routes wired. 3 HTML vs DESIGN_HANDOFF conflicts reported and resolved before coding. Google SSO removed. | COMPLETE. flutter analyze: 0 issues. App launched in Chrome. |
| claude-code-2026-04-25-riasec-screens.md | 2026-04-25 | Sonnet | Built RIASEC Quiz + RIASEC Complete screens (two screens one session). Quiz: ConsumerStatefulWidget, rootBundle JSON asset load (once in initState), AnimatedSwitcher+SlideTransition per question, 5 Likert buttons, AI insight panel per dimension (verbatim from HTML — 2 unique strings: general for R/I/A/S/E, Conventional-specific for C), PopScope back dialog, dimension totals aggregation before submit. Complete: ConsumerWidget, RiasecRadarPainter CustomPainter (6-axis hexagon, 3 tiers, data polygon), top-3 pills, fallback demo scores. 3 corrections applied: endpoint /profile/quiz, responses body format, PopScope. main.dart routes wired. | COMPLETE. flutter analyze: 0 issues. App launched in Chrome, no runtime errors. |
| claude-code-2026-04-25-grades-screens.md | 2026-04-25 | Sonnet | Built Grades Input + Grades Complete screens (two screens one session). GradesInput: ConsumerStatefulWidget, 4 dropdowns (education level/year/stream/board), dynamic subject list per stream, live aggregate, disabled OCR button (image_picker deferred). Correction 1: subject_marks flat dict lowercase keys, no year in body. Correction 2: title-case keys in GradesComplete from profileProvider. Correction 3: test checklist. Flutter 3.41.7 DropdownButtonFormField.value deprecation fixed: key=ValueKey(currentValue)+initialValue. main.dart /grades-input and /grades-complete routes wired. | COMPLETE. flutter analyze: 0 issues. flutter build web: success. |
| claude-code-2026-04-25-17-00-ui-fixes.md | 2026-04-25 | Sonnet | Six UI fixes from manual device testing: (1) Login Column mainAxisSize.min — prevents 12px overflow on small screens. (2) RIASEC Likert buttons: Row→Column, full width, 52px each. (3) RIASEC guidance panel: AI INSIGHT→GUIDANCE, info_outline icon, ExpansionTile collapsed by default. (4) RIASEC question jump: Q counter tappable, bottom sheet 60-question grid, green=answered, grey=unanswered. (5) RIASEC EN/UR toggle in AppBar, Roman Urdu text from JSON text_ur field. (6) Grades marks: inputFormatters cap at 100, validator shows visible error messages. Deferred: quiz progress persistence (no backend draft endpoint, no local storage package). | COMPLETE. flutter analyze: 0 issues. Android emulator requires manual start from Android Studio for device verification. |
| claude-code-2026-04-25-18-00-quiz-draft-persistence.md | 2026-04-25 | Sonnet | RIASEC quiz draft persistence via flutter_secure_storage (Option A selected over backend draft endpoint). Added _saveDraft/_loadDraft/_clearDraft/_scheduleDraftSave/_initQuiz to riasec_quiz_screen.dart. Key: riasec_draft_{userId} (token-based). 500ms debounce on save. onboarding_stage guard clears stale draft and redirects on re-entry. _clearDraft() called in _onSubmit() after 200. All 5 decision-doc risks mitigated. 1 file only. | COMPLETE. flutter analyze: 0 issues. |
| claude-code-2026-04-25-19-00-assessment-screens.md | 2026-04-25 | Sonnet | Built Assessment + Assessment Complete screens (two screens one session). Assessment: ConsumerStatefulWidget, rootBundle JSON load, 3+5+4 draw per subject × 5 subjects = 60 total, String question IDs (issue resolved pre-build), 800ms auto-advance Timer, feedback states (correct=teal/wrong=red), AnimatedSwitcher+SlideTransition, PopScope confirmation dialog, no Previous button, binary responses body {'responses': {subject: [0,1,...]}}. Complete: ConsumerWidget, 5-subject LinearProgressIndicator bars (≥70 teal/<70 slate), fallback demo scores, Continue→/chat. DESIGN_HANDOFF deviations: no TabBar/question map/pulsing ring/auto-navigate — all overridden by explicit prompt instructions. assessment_questions.json copied to frontend/assets/ and added to pubspec. | COMPLETE. flutter analyze: 0 issues. flutter build apk --debug: exit 0. |
| claude-code-2026-04-25-20-00-screenutil-typography.md | 2026-04-25 | Sonnet | Added flutter_screenutil ^5.9.3 to pubspec.yaml. Wrapped MaterialApp with ScreenUtilInit(390×844). Converted all 9 onboarding/auth screens + main.dart: fontSize→.sp, SizedBox height→.h, SizedBox width→.w, Icon size→.r, BorderRadius→.r, EdgeInsets→.r/.h/.w, Container dims→.w/.h. Removed const from all affected widgets. CustomPainter canvas labelStyle left unconverted (canvas context, not widget tree). 4 intentional non-conversions: letterSpacing ratios, strokeWidth, 1px dividers, canvas TextStyle. | COMPLETE. flutter analyze: 0 issues. No errors. |
| claude-code-2026-04-25-21-00-bundle1-fixes.md | 2026-04-25 | Sonnet | Six UI fixes from device testing: (1) Login SingleChildScrollView padding changed from EdgeInsets.all(24.r) → symmetric(h:24.w, v:24.h) to fix 45px overflow on Samsung A6. (2) Grades validator message: 'Must be 0–100' → 'Enter a value between 1 and 100'. (3) RIASEC guidance chip: icon 16→18.r, fontSize 9→12.sp, letterSpacing 0.9→1.0.sp. (4) Assessment _onSubmit guard: blocks submission if _answers.length < _questions.length, shows snackbar with count. (5) RIASEC results button guard: Likert tap now stores to _answers immediately; button shows 'X left to answer' when questions skipped, disabled until all 60 answered. (6) AppBar Fix 6: removed 'Academic Intelligence' text from riasec_quiz_screen._buildAppBar() and assessment_screen AppBar title Row — icon only remains. | COMPLETE. flutter analyze: 0 issues. 4 files modified. |
| claude-code-2026-04-25-22-00-layout-adaptivity-A.md | 2026-04-25 | Sonnet | Full layout adaptivity pass (Session A). (1) main.dart: replaced routes map with onGenerateRoute + PageRouteBuilder FadeTransition 220ms (all 16 routes). (2) Login: LayoutBuilder isCompact<680 — topPadding/vGap/cardPadding reduce on small screens. (3) Signup: same LayoutBuilder pattern with tighter compact values. (4) Grades: removed TextOverflow.ellipsis from level+stream DropdownMenuItems, added softWrap:true, errorMaxLines:2 on mark fields. (5–8) Font increases: Likert 9→14.sp, chips 9-10→11.sp, counters 11→13.sp, question text 16-17→18.sp, insight body 13→14.sp, carousel chip 10→12.sp, bento labels 9→11.sp, aptitude label 10→12.sp. 10 files modified. | COMPLETE. flutter analyze: 0 issues. |
| claude-code-2026-04-26-assessment-redesign.md | 2026-04-26 | Sonnet | Redesigned assessment_screen.dart — replaced 800ms auto-advance + immediate feedback with answer-first free-navigation flow. New: horizontal subject tabs (X/12 counts), Previous/Next buttons, swipe gesture, question map bottom sheet (grouped 60-dot grid), no correct/wrong colours during quiz, results modal bottom sheet (per-subject bars + overall %) before navigating to /assessment-complete, loadProfile called before results overlay (Item 15), draft persistence via flutter_secure_storage (5 risks mitigated), onboarding_stage guard on init. 1 file changed. | COMPLETE. flutter analyze: 0 issues (full project). Physical device test pending — user committed without test run. |
| claude-code-2026-04-26-nav-draft-rename.md | 2026-04-26 | Sonnet | Fix 1: back navigation added to all 3 completion screens — riasec_complete (AppBar added, pushReplacementNamed→/riasec-quiz), grades_complete (maybePop→pushReplacementNamed /grades-input), assessment_complete (AppBar added, pushReplacementNamed→/assessment). Fix 2: assessment draft persistence confirmed already fully implemented in assessment_screen.dart — no changes. Fix 3: AI INSIGHT→GUIDANCE + Icons.auto_awesome→Icons.info_outline in insight panels for riasec_complete and grades_complete; insight panel icon changed in assessment_complete; hero circles and _ResultsSheet hero block left unchanged. | COMPLETE. flutter analyze: 0 issues. Physical device test required before commit. |
| claude-code-2026-04-26-14-00-nav-draft-fixes.md | 2026-04-26 | Sonnet | Fix 1: back button removed from riasec_complete + grades_complete (automaticallyImplyLeading: false). Fix 2: RIASEC quiz Leave black screen — addPostFrameCallback + rootNavigator:true. Fix 3: _initDraft() rewritten — removed strict grades_complete guard, only clears on assessment_complete, added corrupt-draft recovery. Fix 4: draft key limitation documented (no code change). | flutter analyze: 0 issues. NOT COMMITTED — physical device unavailable. |
| claude-code-2026-04-26-16-00-nav-architecture.md | 2026-04-26 | Sonnet | Full nav architecture overhaul + 3 bug fixes. FIX 1: login + signup keyboard overflow — resizeToAvoidBottomInset:false, viewInsets.bottom in LayoutBuilder, ConstrainedBox, keyboard-aware Padding.bottom. FIX 2: pushNamed for all forward onboarding steps (quiz→complete→input→complete→assessment); pushNamedAndRemoveUntil for assessment→assessment-complete and assessment-complete→chat; login Sign Up → pushNamed (back to login test); riasec_complete + grades_complete automaticallyImplyLeading: true; assessment_complete custom back removed + automaticallyImplyLeading: false. FIX 3: WidgetsBindingObserver + didChangeAppLifecycleState on assessment + riasec quiz — immediate draft save on pause/detach. FIX 4: assessment AppBar leading back button (calls existing _onBackPressed dialog). | flutter analyze: 0 issues. NOT COMMITTED — physical device test required. |

---

## OPUS AUDIT LOGS (logs/audits/)

These are structured audit reports produced by Claude Code Opus after a
full system audit. Each was triggered by a prompt generated in the
Claude.ai Opus chat after discussion with the user.

| File | Date | Scope | Summary | Findings count |
|---|---|---|---|---|
| 2026-04-24-opus-gate-check-part1-backend.md | 2026-04-24 | Pre-demo gate check Session 1: state contract, integration boundaries, end-to-end flow, known failure modes. | All 6 state-contract checks PASS. All 4 integration boundaries PASS. End-to-end Steps 1-5, 7-8 PASS; Step 6 CONCERN (Point 2 says profiler entered "regardless of intent" when profiling_complete is False, but code only forces it for get_recommendation/profile_update). No DEMO BLOCKING items. Session 2 must verify affinity_matrix.json and lag_model.json population. | 1 CONCERN (routing) |
| 2026-04-24-opus-gate-check-part2-data-sse.md | 2026-04-24 | Pre-demo gate check Session 2: SSE contract (event types, 7 status states, university_card 20 fields, roadmap_timeline 4 steps, chunk streaming, write timing) + data completeness (affinity_matrix/lag_model/universities). | SSE contract PASS structurally (all 20 card fields present; 4/7 status states emitted; done-in-finally ✓; rich_ui ordering correct). affinity_matrix.json is `[]` — collapses total_score to constant 0.5 across all degrees, discards future_value via OR-branched fallback in scoring_node.py. lag_model has all 32 computed.future_value populated; rozee fields null for all 32; pakistan_now stubs repeat 180/0.08 for 28/32. universities.json: 1 of 20 universities (NED only, 33 degrees) all required fields present. Verdict AMBER — demo can proceed YES with condition Fazal populates affinity_matrix.json before Apr 29. | 1 BLOCKING (affinity_matrix empty), 4 DEGRADES, 4 ACCEPTABLE, 1 latent CONCERN (scoring fallback OR branch), 1 CONCERN (policy_pending_verification hardcoded) |

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
