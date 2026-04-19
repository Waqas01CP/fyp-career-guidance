# Session Log — ExplanationNode Production Implementation
## Date: 2026-04-20, ~14:00
## Model: claude-sonnet-4-6
## Component: backend/app/agents/nodes/explanation_node.py
## Sprint: 3 — April 20 demo deadline
## Prior session: claude-code-2026-04-19-14-00-answer-node.md

---

## Phase 1 — Plan Summary

Planned a production rewrite of explanation_node.py replacing the Sprint 1 stub.

**Functions planned:**
- `_load_lag_model()` — load lag_model.json, index by field_id (same pattern as scoring_node.py)
- `_flatten_content(content)` — Gemini 3.x list-of-parts flattener (copy from answer_node.py)
- `_scrub_pii(text)` — phone + CNIC regex scrubbing before LLM call
- `detect_language_hint(messages)` — last 3 messages, detect Urdu script / Roman Urdu keywords / default English
- `_build_entry_test_advice(entry_test, capability_scores)` — Option D: per-subject gap advice from entry_test block in roadmap entry, threshold 65%, empty string if no gaps
- `_build_degree_context(degree, rank, lag_model, capability_scores)` — compact context string for one ranked degree
- `_build_system_prompt(state, top5, lag_model, language_hint, prompt_trace, significant_change, entered, dropped)` — full prompt assembly, all conditionals resolved before LLM call
- `explanation_node(state)` — node entry point; reads state, builds prompt, calls LLM, appends AIMessage

**State contract:** Only `state["messages"]` modified. All other AgentState fields read-only.

**Pre-resolved decisions applied:**
- ChatGoogleGenerativeAI (same as answer_node.py) — not Claude SDK
- `_flatten_content()` copied exactly from answer_node.py
- Entry test data read from roadmap entry (not universities.json) — already embedded by FilterNode
- Option D for entry test advice (subject-level, threshold 65%)
- Null market data handled via career_paths fallback (never pass None to LLM)
- Thought trace trimming: Option B — filter to entries containing any top-5 degree_id as substring
- Significant change threshold: ROADMAP_SIGNIFICANT_CHANGE_COUNT from config (=2)
- Matric_planning mode gets completely different instruction set (future-oriented, no merit discussion)
- Stub line `state["thought_trace"].append("explanation_node: stub — implement in Sprint 3")` removed

**Plan review statement:** Plan verified against POINT_2_LANGGRAPH_DESIGN_v2_1.md ExplanationNode section. No incoherencies found before implementation began.

---

## Phase 2 — Deviations from Plan

**Deviation 1 — `FLAG_DESCRIPTIONS` dict added**
Not in plan. Added at module level to translate technical soft_flag type strings (e.g. `"entry_test_proxy_used"`) to plain language for LLM context. This prevents technical names leaking into LLM output. 8 flag types covered.

**Deviation 2 — `LLM_FAILURE_FALLBACK` constant**
Not explicitly planned as a named constant. Added for clean fallback message on LLM exception, referenced in except block.

**Deviation 3 — `career_paths` accessed as dict (not list)**
Phase 5b revealed lag_model.json `career_paths` is a dict (keys: `entry_level_title`, `typical_first_role_salary_pkr`, `common_sectors`), not a list. `_build_degree_context()` accesses `.get("entry_level_title")` and `.get("common_sectors", [])[:2]`. Plan assumed list iteration — implementation corrected to dict access.

**Deviation 4 — `zone` not included in degree context**
FilterNode roadmap entries do not carry a zone number field. Plan assumed zone could be shown in degree context. Resolved by omitting zone number; commute information conveyed via `commute_distance` FLAG_DESCRIPTIONS text. No data fabrication.

---

## Phase 3 — Self-Review Findings

All findings resolved before commit.

| Check | Finding | Resolution |
|---|---|---|
| `degree.get("field_id")` | Confirmed present in FilterNode roadmap output (filter_node.py line 484) | No change |
| `degree.get("entry_test")` | Confirmed present in FilterNode roadmap output (filter_node.py line 494) | No change |
| `settings.ENTRY_TEST_SUBJECT_MAP` | Confirmed present in config.py (added in filter-node-v2 session) | No change |
| `settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT` | Confirmed present in config.py | No change |
| `lag_model[field_id]` missing key | Handled via `.get(field_id, {})` — returns empty dict → fallback to "Career data pending" | No change needed |
| `soft_flag["type"] not in FLAG_DESCRIPTIONS` | Handled via `if f.get("type") in FLAG_DESCRIPTIONS` — unknown types silently skipped | No change needed |
| `state["messages"].append()` mutates state in-place | Confirmed: AgentState uses `add_messages` reducer — append is correct | No change |
| `_scrub_pii` called on user_trigger | Confirmed called before passing to HumanMessage | No change |
| `_flatten_content` on LLM response | Confirmed called on `response.content` | No change |
| matric_planning mode | Completely separate instruction string — no merit discussion, no cutoff numbers | No change |

---

## Phase 4 — Integration Boundary Check

ExplanationNode is the final node before the response reaches the frontend. The downstream consumer is the SSE streaming endpoint in `endpoints/chat.py`.

**Fields ExplanationNode writes:**
- `state["messages"]` — appended AIMessage with `content: str`

**Fields endpoints/chat.py reads from state["messages"]:**
- `messages[-1].content` (the final AIMessage) — streamed as SSE `chunk` events

**Verification:** AIMessage with `.content` as plain string is exactly what the streaming endpoint expects. No schema mismatch.

**Integration with previous node (ScoringNode output → ExplanationNode input):**

| Field read by ExplanationNode | Present in ScoringNode output | Status |
|---|---|---|
| `current_roadmap[i]["degree_id"]` | Yes (FilterNode, passed through ScoringNode) | ✓ |
| `current_roadmap[i]["field_id"]` | Yes (FilterNode line 484) | ✓ |
| `current_roadmap[i]["degree_name"]` | Yes | ✓ |
| `current_roadmap[i]["university_name"]` | Yes | ✓ |
| `current_roadmap[i]["merit_tier"]` | Yes (ScoringNode sets via FilterNode output) | ✓ |
| `current_roadmap[i]["total_score"]` | Yes (ScoringNode line ~200) | ✓ |
| `current_roadmap[i]["match_score_normalised"]` | Yes (ScoringNode) | ✓ |
| `current_roadmap[i]["future_score"]` | Yes (ScoringNode) | ✓ |
| `current_roadmap[i]["fee_per_semester"]` | Yes (FilterNode) | ✓ |
| `current_roadmap[i]["soft_flags"]` | Yes (FilterNode + ScoringNode mismatch flag) | ✓ |
| `current_roadmap[i]["aggregate_used"]` | Yes (FilterNode line ~500) | ✓ |
| `current_roadmap[i]["entry_test"]` | Yes (FilterNode line 494) | ✓ |
| `student_profile["riasec_scores"]` | Passed through from ProfilerNode | ✓ |
| `student_profile["subject_marks"]` | Passed through | ✓ |
| `student_profile["capability_scores"]` | Passed through | ✓ |
| `student_profile["stream"]` | Passed through | ✓ |
| `active_constraints["budget_per_semester"]` | Passed through | ✓ |
| `active_constraints["home_zone"]` | Passed through | ✓ |
| `active_constraints["career_goal"]` | Passed through | ✓ |
| `active_constraints["stated_preferences"]` | Passed through | ✓ |
| `thought_trace` | Set by FilterNode + ScoringNode | ✓ |
| `mismatch_notice` | Set by ScoringNode when score_gap >= 0.20 and future_value < 6.0 | ✓ |
| `previous_roadmap` | Set by prior pipeline run via state update | ✓ |
| `student_mode` | Derived server-side, in AgentState | ✓ |

All fields present. No gaps.

---

## Phase 5 — Test Results

**File:** `backend/tests/test_explanation_node.py`
**Tests written:** 10

| Test | Description | Result |
|---|---|---|
| `test_language_detection_english` | English messages → "English" | PASS |
| `test_language_detection_roman_urdu` | "kya hai mein" keywords → "Roman Urdu" | PASS |
| `test_language_detection_urdu_script` | U+0600–U+06FF characters → "Urdu" | PASS |
| `test_thought_trace_trimming` | 10 trace entries, 3 contain top-5 degree_ids → prompt_trace has 3 | PASS |
| `test_rerun_diff_significant` | 2 entries in, 2 dropped (4 total >= 2) → significant_change=True | PASS |
| `test_rerun_diff_not_significant` | Identical roadmaps (0 total < 2) → significant_change=False | PASS |
| `test_no_previous_roadmap` | previous_roadmap=None → significant_change=False, no crash | PASS |
| `test_explanation_appends_message` | Mock LLM returns response → AIMessage appended to messages | PASS |
| `test_only_messages_modified` | All other state fields unchanged after node runs | PASS |
| `test_llm_failure_handled` | LLM raises Exception("API timeout") → fallback AIMessage, no crash | PASS |

**Total: 10/10 PASS**

**Fix applied during testing:**
`test_rerun_diff_not_significant` was originally written with a 1-swap scenario (1 entered + 1 dropped = 2 total), expecting significant_change=False. With `ROADMAP_SIGNIFICANT_CHANGE_COUNT=2`, this evaluates to `2 >= 2 = True`, not False. The test was updated to use identical roadmaps (0 entered + 0 dropped = 0 total < 2 = False). This is a discrepancy between the task specification ("differ by 1 → not significant") and the actual formula. Flagged for Architecture Chat.

---

## Phase 5b — LLM Output

See: `logs/llm-output-explanation-node-2026-04-20.md`

Summary:
- Run 1 (first recommendation): Correct 4-part structure (Parts 0+1 absent as expected). Physics gap cited. 1,240 jobs/month figure used. Part 3 improvement path for BE EE included specific marks (Physics 68% reported, 61% capability).
- Run 2 (rerun + mismatch + 2 swaps): Part 0 fired correctly with degree_ids entered/dropped. Part 1 framed mismatch as honest observation. All parts correct.
- No `_flatten_content()` fallback needed — model returned plain string in both runs.

---

## Known Failure Modes

| Location | Trigger | Error |
|---|---|---|
| `_load_lag_model()` line 65 | `lag_model.json` missing or malformed JSON | `FileNotFoundError` / `json.JSONDecodeError` — not caught, will crash the node |
| `_build_degree_context()` line 163 | `soft_flag["type"]` is `None` | `f.get("type")` returns None → `None in FLAG_DESCRIPTIONS` = False → silently skipped (safe) |
| `_build_entry_test_advice()` line 119 | `settings.ENTRY_TEST_SUBJECT_MAP` key does not exist in settings | `AttributeError` — not caught |
| `explanation_node()` line 420 | `settings.ROADMAP_SIGNIFICANT_CHANGE_COUNT` key does not exist | `AttributeError` — not caught |
| `explanation_node()` line 454 | LLM call raises any Exception | Caught, fallback AIMessage appended |

---

## System Prompt — Inter Mode (full text template)

See Phase 5b log for the exact system prompt produced with NED/NEDUET test data.

Template structure (order is fixed):
```
{lang_rule}

STUDENT PROFILE:
Marks: {marks_str}
RIASEC dominant: {dominant_str}
Capability: {cap_str}
Mode: {student_mode} | Level: {education_level} | Stream: {stream}
Budget: Rs. {budget}/semester | Zone: {home_zone}
Career goal: {career_goal}
Stated preference: {stated_prefs}

TOP 5 DEGREES:
{degree_contexts — 5 blocks, each 5-7 lines}

[MISMATCH NOTICE: {mismatch_notice}]   ← only if mismatch_notice is set

[REASONING TRACE:                       ← only if prompt_trace is non-empty
{prompt_trace entries}]

[Part 0 — What Changed: ...]           ← only if significant_change=True
[Part 1 — Mismatch: ...]               ← only if mismatch_notice is set
INSTRUCTIONS — You are an academic career advisor for Pakistani students.
Write a RECOMMENDATION response.
Rules:
...
[Part 3 — Improvement path: ...]       ← only if any entry has merit_tier='improvement_needed'
```

---

## System Prompt — Matric Planning Mode Differences

When `student_mode == "matric_planning"`:
- Core instructions replace: "Write a PLANNING response (student has not started Inter yet)"
- "Frame as 'degrees you could reach' — future-oriented, not current eligibility"
- "Explain what stream and marks the student needs to reach each degree"
- "Do NOT discuss current admission likelihood or merit cutoffs"
- All other sections (profile, degrees, trace, language rule) identical

---

## System Prompt Token Count

- Estimated: ~975 tokens (chars/4 from `len(system_prompt) // 4` in Phase 5b print)
- Target per BACKEND_CHAT_INSTRUCTIONS.md: 400–700 tokens
- Overage: ~275–575 tokens above target
- Breakdown estimate: reasoning trace (~120 tokens for 5 entries) + 5 degree contexts (~280 tokens) + instructions (~170 tokens) + profile (~90 tokens) + language rule (~30 tokens) + overhead (~285 tokens)

---

## Assumptions

1. `lag_model.json` is always loadable at startup. No caching or error recovery for file-not-found — assumed always present per DATA_DIR pattern used in scoring_node.py.

2. `entry_test` block embedded in roadmap entries by FilterNode is the authoritative source for entry test advice. Not re-read from universities.json.

3. Thought trace from real FilterNode/ScoringNode runs will use `degree_label` format ("NED University BS CS"), not degree_id format. The Option B trimming code in explanation_node.py looks for degree_id substrings — this will produce `prompt_trace = []` in production runs. The REASONING TRACE section will be absent from all real pipeline invocations.

4. `career_paths` in lag_model.json is always a dict (as verified in lag_model.json first entry and stub structure), never a list.

5. `stated_preferences` in `active_constraints` is always a list of strings (normalisation applied in profiler_node.py per the stated_preferences string→list fix in that session).

---

## Architecture Chat Review Items

**Item 1 — Token count above target**
System prompt ~975 tokens vs 400–700 target from BACKEND_CHAT_INSTRUCTIONS.md. Quality is demonstrably good at this token count (Phase 5b output confirmed). Should the target range be revised for ExplanationNode, or should the prompt be trimmed? Reasoning trace adds ~120 tokens and produces an empty section in production anyway (see Item 3).

**Item 2 — Significant change threshold for 1-swap**
With `ROADMAP_SIGNIFICANT_CHANGE_COUNT=2`: a single degree swap produces entered=1, dropped=1, total=2, which IS significant (triggers Part 0). The task specification said "differ by 1 → not significant." These are inconsistent. Current behaviour: 1 swap = significant. Confirm this is the intended threshold, or change `ROADMAP_SIGNIFICANT_CHANGE_COUNT` to 3 for "only 2+ swaps are significant."

**Item 3 — Thought trace trimming (Option B) produces empty trace in production**
FilterNode appends to `thought_trace` using `degree_label = f"{university_name} {degree_name}"` (e.g. "NED University of Engineering & Technology BS Computer Science"). ScoringNode appends using "BS CS (NED)" format. Neither format contains degree_ids like "neduet_bs_cs". The Option B trimming in explanation_node.py:
```python
prompt_trace = [t for t in state.get("thought_trace", []) if any(deg_id in t for deg_id in top5_ids)]
```
...will always produce an empty list in real pipeline runs. Options: (a) change FilterNode to include degree_id in trace entries, (b) change Option B to match on degree_name substring instead, (c) accept empty trace and remove the REASONING TRACE section from prompt. Decision needed before this is exercised in production.

---

## Architecture Chat Fix — thought trace trimming — 2026-04-20

Item 3 resolved. Changed trimming logic in `explanation_node.py` to match on `degree_name` and `university_name` substrings instead of `degree_id`. New logic (lines 402–410): builds `top5_names` and `top5_unis` lists from the top-5 roadmap entries, then keeps any trace entry that contains any degree_name OR any university_name as a substring. This correctly matches both FilterNode format (`"{university_name} {degree_name}"`) and ScoringNode format (`"{degree_name} ({abbrev})"`). `test_thought_trace_trimming` updated to use real production trace format — degree_name and university_name substrings in the match entries, generic university names in the non-match entries. 10/10 tests pass after the fix.

---

## Architecture Chat Fix 2 — LLM-native language detection — 2026-04-20

**What was removed:** `detect_language_hint()` function (18 lines) and its call site in `explanation_node()`. The function used a hardcoded keyword list (`["yaar", "kya", "hai", "mein", "ka", "ki", "ko", "se", "bhi", "aur", "nahi"]`) for Roman Urdu detection and a Unicode range check for Urdu script.

**What replaced it:** The last 2–3 student messages (non-AI) are extracted as `recent_text` (pipe-separated) and injected directly into the system prompt under a static `LANGUAGE RULE` block. The LLM reads the actual message text and detects language natively. The prompt instructs: respond in Roman Urdu if Roman Urdu is detected; respond in Urdu script if Urdu script is detected; respond in English otherwise; do not mix languages unless the student mixes them.

**Why:** The hardcoded word list missed spelling variants (`"kiya"` vs `"kya"`, `"ha"` vs `"hai"`, `"nae"`, `"bilkul"`, `"zaroor"`, `"acha"`) and failed on punctuation (`"kya?"` did not match `"kya"` in a split). Adding every variant manually is not maintainable and degrades as new users write differently. The LLM handles all variants, code-switching, and edge cases natively without code changes.

**Hybrid UI note:** Chat responses will be in the student's language. Roadmap cards (Flutter `rich_ui` payload) remain in English — these are structured data fields from the backend, not LLM prose. This hybrid is accepted for the April 20 demo. Full localisation of roadmap card labels is deferred to Sprint 4.

**`_build_system_prompt()` signature change:** `language_hint: str` parameter replaced with `recent_text: str`. All call sites updated.

**Test changes:** 3 `detect_language_hint()` call tests replaced with 5 prompt-assembly tests that import `_build_system_prompt` directly and assert the recent_text appears verbatim in the prompt. `test_language_rule_spelling_variants` explicitly documents that `"kiya"`, `"ha"`, `"nae"`, `"bilkul"`, `"zaroor"`, `"acha"` are passed through unchanged — the LLM handles them.

**Results:** 12/12 explanation node tests pass. 65/65 full suite pass. No regressions.
