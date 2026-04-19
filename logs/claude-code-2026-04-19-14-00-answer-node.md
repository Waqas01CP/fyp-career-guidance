# Claude Code Session Log
**Date:** 2026-04-19 14:00
**Task:** Implement AnswerNode production code (Sprint 3) + fix fetch_fees.py field name bug
**Status:** COMPLETE

---

## Files Changed
- `backend/app/agents/nodes/answer_node.py` — Replaced Sprint 1 stub with full production implementation: module-level LLM init, intent dispatch (fee_query/market_query/follow_up+clarification/out_of_scope), entity extraction LLM calls, fetch_fees()/lag_calc() tool integration, empty result fallback, LLM failure handling. Content list-flatten fix applied to all 5 LLM call sites.
- `backend/app/agents/tools/fetch_fees.py` — Field name bug fix only: `uni.get("university_name", "")` → `uni.get("name", "")` and `d.get("degree_name")` → `d.get("name")`. Two key name corrections, no logic changes.

## Files Created
- `backend/tests/test_answer_node.py` — 8 unit tests (all pass, no API calls consumed)
- `logs/llm-output-answer-node-2026-04-19.md` — Phase 5b LLM output log

## Files Read (not changed)
- `logs/README.md`
- `CLAUDE.md` (v2.1)
- `docs/00_architecture/CLAUDE_CODE_RULES.md`
- `docs/00_architecture/SPRINT_2_BUILD_PROCESS.md`
- `docs/00_architecture/BACKEND_CHAT_INSTRUCTIONS.md`
- `docs/00_architecture/POINT_2_LANGGRAPH_DESIGN_v2_1.md` (full, focused on Section 10)
- `backend/app/agents/nodes/supervisor.py` (LLM init pattern + content list-flatten reference)
- `backend/app/agents/tools/fetch_fees.py`
- `backend/app/agents/tools/lag_calc.py`
- `backend/app/agents/tools/job_count.py`
- `backend/app/data/universities.json` (first 50 lines — field name verification)
- `backend/app/agents/state.py`
- `backend/app/core/config.py`

---

## What Was Done

### Phase 0 — API Key Validation
Ran same validation as supervisor.py session. `gemini-3.1-flash-lite-preview` responded with "Ok". API key confirmed valid.

### Phase 1 — Plan
Written plan covering: intent dispatch, entity extraction approach (naming conventions + few-shot, no hardcoded ID list), tool result formatting, follow_up/clarification/out_of_scope handling, answer prompt structures per intent, token optimization decisions, empty tool result handling, test plan.
Plan reviewed against Point 2 Section 10 line by line. No incoherencies found.

### Phase 2 — Implementation

**fetch_fees.py fix (two lines):**
- `uni.get("university_name", "")` → `uni.get("name", "")` — universities.json uses `"name"` key at university level
- `d.get("degree_name")` → `d.get("name")` — universities.json uses `"name"` key at degree level

**answer_node.py structure:**
- Module-level `ChatGoogleGenerativeAI` init (same pattern as supervisor.py)
- `_flatten_content()` helper — Gemini 3.x content list-of-parts → string
- `_get_user_input()` helper — extracts latest message content from state
- `_extract_entity()` helper — short LLM call for university_id or field_id extraction
- Intent dispatch: `fee_query` / `market_query` / `out_of_scope` / else (follow_up+clarification)
- `fee_query`: extract → fetch_fees() → format fee section with budget comparison → answer LLM
- `market_query`: extract → lag_calc() → format market section → answer LLM
- `out_of_scope`: answer LLM with polite-decline prompt, no data
- `follow_up`/`clarification`: serialize current_roadmap as JSON → answer LLM

**Content list-flatten applied to:** `_extract_entity()` extraction response (×2), fee answer response, market answer response, out_of_scope response, follow_up/clarification response.

**Empty tool result fallbacks:**
- Empty extraction → direct AIMessage, no tool call
- `fetch_fees({})` → direct fallback AIMessage, no answer LLM call
- `lag_calc({})` → direct fallback AIMessage, no answer LLM call

**LLM failure handling:** All 5 LLM call sites wrapped in try/except. Each appends a fallback AIMessage. No crash path.

### Phase 3 — Self-Review
All 8 checklist items verified. One edge case confirmed safe: fee_data degree formatting uses `d.get("fee_per_semester") and d.get("degree_name")` guard before accessing via `d['degree_name']` — safe because both are truthy before access.

### Phase 4 — Integration Boundary
- `last_intent` read from state ✓ (written by SupervisorNode)
- `current_roadmap` read from state ✓ (written by ScoringNode)
- `active_constraints` read from state ✓ (written by ProfilerNode)
- `state["messages"]` appended only ✓ — not reset
- `job_count.py` NOT imported or called ✓

### Phase 5 — Tests
8 tests written, 8/8 pass. No API calls consumed (all LLM and tool calls mocked).

### Phase 5b — LLM Output Log
Ran all 4 intent paths:
1. fee_query "How much does NED charge per semester?" → correct fee data with budget comparison ✓
2. market_query "What is the job market like for software engineering?" → fallback (expected — lag_model.json empty) ✓
3. follow_up "Why did BS CS rank higher than BS EE?" → correct answer from roadmap data ✓
4. out_of_scope "Can you help me with my physics homework?" → polite decline with redirect ✓

---

## Verification Result

```
pytest backend/tests/test_answer_node.py -v
8 passed in 3.89s
```

All 8 required tests pass. API key validated. LLM output verified for all 4 intent paths.

---

## Deviations from Plan

None. Implementation matches plan exactly.

---

## Self-Review Findings (Phase 3)

No discrepancies found. All key accesses verified against actual data structures.

---

## Integration Boundary Check (Phase 4)

All 5 boundary conditions confirmed. No gaps.

---

## Known Failure Modes (derivable from code only)

| File | Line(s) | Trigger condition | Effect |
|---|---|---|---|
| answer_node.py | 173-178 | `fee_per_semester` value is 0 (falsy) for a degree | Degree shown as "fee not listed" even though 0 is technically a valid value |
| answer_node.py | 234 | `job_count` is 0 (falsy) in lag_model data | Job count line omitted from market section |
| answer_node.py | 237 | `yoy` is exactly 0.0 | `yoy * 100` evaluates to 0%, included correctly (0.0 is falsy in `if yoy is not None` — but `if yoy is not None` check correctly includes 0.0) — ✓ no issue |
| fetch_fees.py | 23 | Large universities.json scanned on every fee_query | O(n) linear scan; acceptable at 20 universities but noted |

---

## SYSTEM PROMPTS

See `logs/llm-output-answer-node-2026-04-19.md` for full text of all 5 system prompt templates.

---

## TOKEN COUNTS

| Prompt type | Estimated total tokens | Within 250-400 target? |
|---|---|---|
| FEE_EXTRACTION | ~100 | Yes |
| MARKET_EXTRACTION | ~110 | Yes |
| FEE_ANSWER (NED 33 degrees) | ~675 | No — exceeds target. Full degree list is necessary signal. |
| MARKET_ANSWER | ~180-280 | Yes |
| FOLLOWUP_ANSWER (large roadmap) | ~390-890 | Varies — depends on roadmap size. Large roadmaps exceed target. |
| OUT_OF_SCOPE | ~65 | Yes |

---

## ASSUMPTIONS

1. **University nickname extraction edge cases:** If the LLM extracts a nickname that doesn't exist in universities.json (e.g., "comsats" which isn't in the system yet), `fetch_fees()` returns `{}` and the empty-result fallback handles it correctly. No crash, clear user message.

2. **Field_id extraction informal names:** Market extraction handles Roman Urdu naturally via the LLM (e.g., "CS ka scope" → "computer_science"). The few-shot examples cover the most common Pakistani shorthand. New fields added to universities.json should have corresponding mappings added to MARKET_EXTRACTION_SYSTEM_PROMPT.

3. **lag_model.json is currently empty:** All market_query Phase 5b tests produced the fallback response. This is correct behaviour, not a bug. When Fazal populates lag_model.json, market_query will return real data without any code changes.

4. **Application deadline handling:** No `application_window` data is read directly by AnswerNode. The follow_up prompt instructs the model to frame deadlines as "Based on the previous cycle..." — but only if the roadmap contains application window data. Currently the roadmap entries from ScoringNode don't include `application_window`. When AnswerNode receives a deadline question, it can only answer if the roadmap entry includes that data. For Architecture Chat review: should `application_window` be included in roadmap entries, or should AnswerNode call a separate tool to look it up from universities.json?

5. **Fee prompt token count with 33 NED degrees:** The formatted fee_data_section for NED (33 degrees) is ~600 tokens, pushing total above the 400-token target. This is acceptable because truncating the degree list would degrade answer quality. Suggest Architecture Chat consider whether fee_query should show all degrees or only the top-N most relevant.

6. **out_of_scope in Point 2 Section 10:** The Section 10 code example's `else` branch says `# follow_up, clarification` — it does not explicitly mention `out_of_scope`. However, Point 2 v2.1 update and Section 5 (route_by_intent) both confirm `out_of_scope` routes to AnswerNode. This implementation adds a separate `elif intent == "out_of_scope"` branch before the `else` catch-all so the polite decline prompt is used instead of passing roadmap data to the model.

---

## What Architecture Chat Should Review

1. **Fee prompt token count:** With 33 NED degrees, fee_data_section is ~600 tokens, exceeding the 400-token target. Should AnswerNode filter the degree list (e.g., show only degrees the student is eligible for, from current_roadmap) rather than all university degrees? This would reduce tokens and improve relevance.

2. **Follow-up roadmap serialization:** Serializing full current_roadmap as JSON could be 2000-4000 tokens for large roadmaps. Consider passing only key fields (degree_name, total_score, merit_tier, fee_per_semester, soft_flags) rather than full ScoringNode output entries. This would reduce tokens without losing answer quality for typical follow-up questions.

3. **Application deadline data access:** Point 2 Section 10 and Section 13 say AnswerNode should frame deadlines as "Based on 2025 cycle...". But `application_window` data is in universities.json, not in current_roadmap entries. AnswerNode currently can only answer deadline questions if the data appears in the roadmap. Should AnswerNode call a separate `fetch_deadlines()` tool, or should `application_window` be included in FilterNode roadmap output? Decision needed.

4. **market_query extraction returns "software_engineering" but lag_model.json has "computer_science" as the field_id:** Once lag_model.json is populated, confirm that field_ids in lag_model.json match the IDs the extraction LLM produces. If "software_engineering" is not a valid field_id, lag_calc() returns {} and the fallback fires. The mapping examples in MARKET_EXTRACTION_SYSTEM_PROMPT should match the actual field_ids Fazal uses.

---

## Follow-up Fix — slim roadmap + student summary + lag_model stub — 2026-04-19

### What changed in answer_node.py follow_up path

**FOLLOWUP_ANSWER_SYSTEM_PROMPT** — added one rule to the Rules section:
`"- For improvement questions: use the student's subject_marks and capability_scores from the student profile above to give specific subject-level advice. Name the exact subject that needs improvement and the approximate gap to close."`

**follow_up / clarification block** — replaced 3-line raw roadmap serialization with:
1. Slim roadmap construction: 9-field dict per entry (`rank`, `degree_name`, `university_name`, `total_score`, `merit_tier`, `fee_per_semester`, `soft_flag_types`, `match_score_normalised`, `future_score`, `eligibility_note`). Reduces ~200 tokens/entry → ~50 tokens/entry. For 33 NED degrees: ~6600 tokens → ~1650 tokens.
2. Student summary construction: 6-field dict (`subject_marks`, `capability_scores`, `stream`, `budget_per_semester`, `stated_preferences`, `career_goal`). ~150 tokens.
3. `roadmap_section` formatted as "Student profile:\n{summary}\n\nDegree roadmap:\n{slim_list}". Empty roadmap fallback retained.

**Token count estimate for updated follow_up prompt:**
- System prompt preamble + rules: ~120 tokens
- Student summary: ~150 tokens
- Slim roadmap (33 entries × ~50 tokens): ~1650 tokens
- Total: ~1920 tokens — down from ~4000-6000 tokens with raw roadmap

### lag_model.json action taken

**Was empty (`[]`).** Created stub with 32 entries covering all NED canonical field_ids:
`computer_science, artificial_intelligence, software_engineering, cybersecurity, data_science, digital_media, telecommunications_engineering, electrical_engineering, electronics_engineering, biomedical_engineering, chemical_engineering, food_engineering, mechanical_engineering, automotive_engineering, metallurgical_engineering, materials_engineering, polymer_petrochemical_engineering, industrial_manufacturing_engineering, petroleum_engineering, civil_engineering, business_bba, urban_infrastructure_engineering, construction_engineering, textile_engineering, textile_sciences, english_linguistics, economics, finance_accounting, social_work, physics, chemistry_biochemistry, architecture`

Each entry has `computed.future_value` set to the ScoringNode fixture values. All other raw data fields are null stubs (`data_status: "partial"`). Career paths use the Pakistani market data specified in the task. `associated_degrees` arrays cover all 33 NED degree_ids. `computer_science` entry covers both `neduet_bs_cs` and `neduet_be_cise`.

Note: `petroleum_engineering` is included although not in the canonical DATA_CHAT_INSTRUCTIONS.md list — it is in NED universities.json and has a specified future_value.

### DATA_CHAT_INSTRUCTIONS.md

Section "ANSWER NODE MAINTENANCE" already existed with near-identical content. Updated one sentence: added "in the same commit" to the first rule paragraph. No duplicate section created.

### CLAUDE.md

Row "AnswerNode field mapping maintenance" already existed. Updated to add "for the exact format" to the reference sentence end.

### Test results

```
pytest backend/tests/test_answer_node.py -v
8 passed in 2.56s  ✓ All 8 answer_node tests pass

pytest backend/tests/ -v -m "not slow"
50 passed, 3 deselected in 2.62s  ✓ Full unit suite passes
```
