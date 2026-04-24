# Opus Gate Check — Session 2: Data and SSE Contract
## Date: 2026-04-24
## Model: Opus 4.7, high effort
## Session 1 reference: logs/audits/2026-04-24-opus-gate-check-part1-backend.md

---

## FILES READ

1. logs/README.md
2. logs/audits/2026-04-24-opus-gate-check-part1-backend.md
3. CLAUDE.md — Sprint 4 cleanup items 6–10 (in system context)
4. docs/00_architecture/POINT_5_API_SURFACE_v1_2.md — Endpoint 8 in full
5. backend/app/api/v1/endpoints/chat.py — real_stream, _build_university_card,
   _build_roadmap_timeline, _write_recommendation, NODE_STATUS_MAP
6. backend/app/data/affinity_matrix.json
7. backend/app/data/lag_model.json
8. backend/app/data/universities.json (+ spot-check script over all 33 degrees)

Extra targeted read: scoring_node.py lines 20–50 and 120–158 to confirm the
missing-field_id fallback path (relevant to 6a).

---

## AREA 5 — SSE Contract

### 5a — Status events

`NODE_STATUS_MAP` in chat.py lines 46–51 covers 4 of the 7 valid states:
`profiling`, `filtering_degrees`, `scoring_degrees`, `generating_explanation`.

| state | Emitted? | Evidence |
|---|---|---|
| `profiling` | ✓ | NODE_STATUS_MAP["profiler"] |
| `filtering_degrees` | ✓ | NODE_STATUS_MAP["filter_node"] |
| `scoring_degrees` | ✓ | NODE_STATUS_MAP["scoring_node"] |
| `generating_explanation` | ✓ | NODE_STATUS_MAP["explanation_node"] |
| `fetching_fees` | ✗ | Not emitted from any tool-call site. Sprint 4 item #7. |
| `fetching_market_data` | ✗ | Same as above. Sprint 4 item #7. |
| `done` | ✓ | chat.py line 321 — emitted inside the `finally:` block of real_stream(). Guaranteed terminal even on exception. |

The `on_chain_start` hook (line 272) fires when a node starts — correct
semantics per Point 5 ("when the node begins executing").

**Verdicts**
- `done` in finally: **PASS.**
- `fetching_fees` / `fetching_market_data` missing: **CONCERN** — already
  logged as Sprint 4 item #7, so ACCEPTABLE for demo per precedence Rule 3.

### 5b — university_card 20 fields

Cross-check of `_build_university_card()` (chat.py lines 59–85) vs Point 5:

| # | Field | Present | Source in code | Null in current demo data? |
|---|---|---|---|---|
| 1 | rank | ✓ | argument (loop index+1) | No |
| 2 | degree_id | ✓ | roadmap entry (FilterNode) | No |
| 3 | degree_name | ✓ | roadmap entry | No |
| 4 | university_id | ✓ | roadmap entry | No |
| 5 | university_name | ✓ | roadmap entry | No |
| 6 | field_id | ✓ | roadmap entry | No |
| 7 | total_score | ✓ | ScoringNode | No |
| 8 | match_score_normalised | ✓ | ScoringNode | **Default 0.5 for all** — affinity_matrix.json empty |
| 9 | future_score | ✓ | ScoringNode | No (lag_model.computed populated) |
| 10 | merit_tier | ✓ | FilterNode | No |
| 11 | eligibility_tier | ✓ | FilterNode | No |
| 12 | eligibility_note | ✓ | FilterNode | Often null (legitimate) |
| 13 | fee_per_semester | ✓ | FilterNode (from universities.json) | No |
| 14 | aggregate_used | ✓ | FilterNode | No |
| 15 | soft_flags | ✓ (default `[]`) | FilterNode | Array, never null |
| 16 | lifecycle_status | ✓ | lag_model | No — populated for all 32 |
| 17 | risk_factor | ✓ | lag_model | No — populated for all 32 |
| 18 | rozee_live_count | ✓ | lag_model.employment_data | **Null for all 32** — stub data |
| 19 | rozee_last_updated | ✓ | lag_model.employment_data | **Null for all 32** — stub data |
| 20 | policy_pending_verification | ✓ | hardcoded `False` | **Hardcoded** — ignores `eligibility.policy_pending_verification` in universities.json |

**Verdicts**
- Field presence (all 20): **PASS.**
- `policy_pending_verification` hardcoded False is a **CONCERN**:
  universities.json does carry the field per-degree under
  `eligibility.policy_pending_verification` but chat.py never reads it.
  Low demo impact (NED data has it `false` everywhere) but technically
  wrong. Flag for Architecture Chat.

### 5c — roadmap_timeline 4 steps

`_build_roadmap_timeline()` (chat.py lines 88–154) emits exactly 4 steps:

| # | label | status (code) | Point 5 spec | Match? |
|---|---|---|---|---|
| 0 | Current Status | "complete" | "complete" | ✓ |
| 1 | Recommended Degree | "next" | "next" | ✓ |
| 2 | Industry Entry | "future" | "future" | ✓ |
| 3 | 2030 Outlook | "future" | "future" | ✓ |

- Step 2 `entry_level_title` sourced from `lag_entry.career_paths.entry_level_title`
  (line 114) with fallback `"Industry professional role"`. career_paths **is
  populated** for every field in lag_model.json — entry_level_title present on
  all 32 entries. **PASS.**
- Step 3 `job_count` falls back to `employment.rozee_live_count` then conditions
  `if job_count:` before emitting (lines 117–127). Handles null gracefully
  (emits growth string without the "X active roles" clause). **PASS.**
- `growth_pct` (pakistan_future.projected_4yr_growth) is null for all 32 entries
  → every Step 3 will use the fallback string
  `"Strong growth outlook (score: X.X/10)."`. Legitimate, readable. **PASS.**
- `field_id` and `degree_id` top-level fields present (lines 152–153). **PASS.**

### 5d — chunk streaming

chat.py lines 291–294:

```python
words = content.split(" ")
for i, word in enumerate(words):
    chunk = word if i == len(words) - 1 else word + " "
    yield _sse("chunk", {"text": chunk})
```

- Last word: no trailing space. **PASS.**
- Other words: trailing space. **PASS.**
- Empty content guarded at line 290 (`if content:`) — loop skipped.
  **PASS.**
- Note: uses `.split(" ")` (single space) not `.split()`. Multiple
  consecutive spaces would produce empty-string chunks but each is harmless
  — Flutter appends empty string. **ACCEPTABLE.**

### 5e — recommendations write timing

`_write_recommendation` (chat.py lines 157–185) called at line 313, guarded
on lines 300 by:

```python
if current_roadmap and last_intent == "get_recommendation":
```

Conditions:
- Non-empty `current_roadmap`: **PASS.**
- `last_intent == "get_recommendation"`: **PASS.**
- Timing: runs after chunk stream and rich_ui events, **before** the
  `finally` block emits `done`. Ordering: rich_ui emitted → DB write →
  `done` event. **PASS.**
- Dead `profile_update` trigger branch (line 167): already flagged as
  Sprint 4 item #6 per CLAUDE.md and S1 audit. **ACCEPTABLE.**

---

## AREA 6 — Data Completeness

### 6a — affinity_matrix.json

**Entry count: 0.** File contents: literal `[]`. Expected: 32 (one per
NED field_id, per CLAUDE.md v1.7).

Scoring impact (scoring_node.py lines 120–132): for any `field_id` not
present in `affinity_matrix`, ScoringNode takes the fallback branch and
writes `match_score_normalised = 0.5` and `future_score = 5.0`. However
`future_score` is only set to 5.0 *also when the field_id is missing from
`lag_model`*, because the condition is an OR:

```python
if field_id not in affinity_matrix or field_id not in lag_model:
```

All 32 NED field_ids ARE present in lag_model.json (confirmed in 6b), so
`match_score_normalised = 0.5` will be taken for every degree, but
`future_score` will also be forced to 5.0 because the same branch sets
both values. **This means `total_score` collapses to a constant for every
degree regardless of future_score.**

Ranking impact:
- With the current fallback, every degree gets
  total_score = (0.6 × 0.5) + (0.4 × 5.0/10) = 0.3 + 0.2 = 0.5.
- Every NED degree will have an identical total_score.
- Sorting becomes input-order dependent (Python's sort is stable, so
  FilterNode's emission order is preserved).
- RIASEC personalisation: **completely non-functional.**
- Future-value personalisation: **also non-functional** because the
  fallback bypasses the lag_model lookup.

Rating: **BLOCKING.** The entire demo narrative is "the system ranks
degrees based on your RIASEC profile and market outlook". With an empty
affinity matrix, ranking is deterministic/constant and the pitch falls
apart the moment a viewer asks "why is CS ranked first?" (answer: because
FilterNode emitted it first).

Fazal must populate affinity_matrix.json with at least the 32 NED
field_ids — each with a `riasec_affinity` block keyed R/I/A/S/E/C
(values 1–10) — before April 29.

**ScoringNode fallback structural bug (separate from data gap):**
Lines 120–132 use a single OR branch for two independent data sources.
If `field_id` is in `lag_model` but not in `affinity_matrix`, the code
still discards the real `future_value` and substitutes 5.0. This should
be two independent lookups with independent defaults. Filing as
**CONCERN** — Architecture Chat item. Not fixable by data alone; data
fix (populating affinity_matrix) masks it but the bug remains latent.

### 6b — lag_model.json

**Entry count: 32.** All 32 NED field_ids present.

Per-field completeness (surveyed all 32 entries by inspection):

| Field | Populated | Null | Notes |
|---|---|---|---|
| `computed.future_value` | 32/32 | 0 | Values 3.0–9.2, all precomputed 2026-04-19. **PASS.** |
| `pakistan_now.job_postings_monthly` | 32/32 | 0 | **Populated but stubby:** 28 of 32 entries share the placeholder value `180`. Only CS, AI/ML, Software Engineering, Cybersecurity, Data Science, Electrical Engineering have distinct numbers. Stub, not null. |
| `pakistan_now.yoy_growth_rate` | 32/32 | 0 | Same stub pattern — 28 of 32 set to `0.08`. |
| `employment_data.rozee_live_count` | 0/32 | 32 | **All null.** |
| `employment_data.rozee_last_updated` | 0/32 | 32 | **All null.** |
| `lifecycle_status` | 32/32 | 0 | "Emerging"/"Stable"/"Peak" values present. |
| `risk_factor` | 32/32 | 0 | "Low"/"Medium". |
| `career_paths.entry_level_title` | 32/32 | 0 | Populated (some generic like "Graduate Physics"). |
| `pakistan_future.projected_4yr_growth` | 0/32 | 32 | All null. Roadmap step 3 falls back gracefully. |

Downstream impact on university_card:
- `rozee_live_count` null → Flutter must render "—" or hide the
  "X active jobs" line. Frontend-side rendering concern, not backend
  failure. Card still renders.
- `rozee_last_updated` null → "Last updated X days ago" line hidden.
- `lifecycle_status` + `risk_factor` populated → badges render correctly.

Downstream impact on roadmap_timeline:
- Step 3 job_count falls back to
  `pakistan_now.job_postings_monthly` (line 117) which IS populated.
  For 28/32 fields this prints "180 active roles on Rozee today" which
  is the same stub number used across unrelated fields — looks synthetic
  but renders. **DEGRADES** for the demo narrative on non-CS fields.

Rating: `future_value` is the load-bearing field for scoring and it is
complete. The employment/rozee stubs are cosmetic.
**ACCEPTABLE** for demo, with the caveat that Step 3 text will show
"180 active roles" for most non-CS fields — potentially awkward during
Q&A.

### 6c — universities.json

**Universities count: 1.** (NED only.) **Degrees count: 33.**

Spot-check (seed=7) on 3 random degrees —
`neduet_be_urban_planning`, `neduet_be_mechanical`, `neduet_bs_chemistry`:

- All three have `field_id`, `entry_test`, `aggregate_formula`,
  `cutoff_range` with `min`/`max`, non-null `fee_per_semester`,
  `min_percentage_hssc`, and `eligibility_notes` block.

Full sweep of all 33 degrees — required fields check:

| Required field | Missing |
|---|---|
| entry_test | 0 |
| aggregate_formula | 0 |
| cutoff_range | 0 |
| fee_per_semester (non-null, non-zero) | 0 |
| field_id | 0 |
| min_percentage_hssc | 0 |
| eligibility.eligibility_notes | 0 |

All 33 NED degrees pass structural validation. 33/33 have populated
cutoff_range — merit tier classification in FilterNode will work for
every degree. **PASS.**

Only NED is present. The demo is scoped to NED per CLAUDE.md
("1 of 5 priority universities done"). **ACCEPTABLE** for April 29
demo — presenter should frame the demo around NED explicitly.

---

## AREA 7 — Demo-Blocking Gap Assessment

### BLOCKING items

1. **affinity_matrix.json is `[]`** (Check 6a). Collapses every degree's
   `total_score` to 0.5 via the ScoringNode fallback, which ALSO discards
   real `future_value` due to the OR-branched fallback (6a structural
   note). Ranking becomes input-order. RIASEC and future-outlook
   personalisation — the core pitch of the system — do not function.
   **Owner: Fazal. Deadline: April 29.**

### DEGRADES items

1. `rozee_live_count` and `rozee_last_updated` null for all 32 fields
   (Check 6b). university_card "active jobs" line cannot render. Flutter
   must handle `null` gracefully; if it does, cards still look
   complete.
2. `pakistan_now.job_postings_monthly` set to stub `180` for 28/32
   fields (Check 6b). Roadmap timeline Step 3 will print
   "180 active roles on Rozee today" for most non-CS fields —
   suspicious repetition if a demo viewer requests multiple
   recommendations across different fields.
3. SSE status events `fetching_fees` / `fetching_market_data` not
   emitted (Check 5a). Flutter ThinkingIndicator shows nothing during
   fee/market tool calls — perceptible as a pause. Sprint 4 item #7.
4. Only NED present in universities.json. 19 of 20 planned
   universities absent. Scope the demo to NED.

### ACCEPTABLE items

1. `policy_pending_verification` hardcoded `False` in
   `_build_university_card` (Check 5b #20). No wrong render on NED
   data; still a spec drift to flag for Architecture Chat.
2. `pakistan_future.projected_4yr_growth` null for all 32 entries
   (Check 6b). Graceful fallback in Step 3 detail string.
3. ScoringNode OR-branched fallback discarding future_value when
   affinity missing (Check 6a). Latent; masked once affinity_matrix
   is populated. Architecture Chat item.
4. `pakistan_now.job_postings_monthly` stub values (Check 6b) — as
   listed under DEGRADES #2; stays ACCEPTABLE if demo is scripted
   around CS/AI/SE which have distinct numbers.

### Fazal data tasks before April 29

1. **Populate affinity_matrix.json with the 32 NED field_ids** —
   each with a `riasec_affinity` block keyed exactly R/I/A/S/E/C
   (values 1–10). This is the single blocking data gap.
2. *Stretch*: replace the stub `180` / `0.08` pattern in
   `pakistan_now` for non-tech fields so Step 3 narrative does not
   repeat the same number. Not required but strongly recommended.
3. *Stretch*: populate `employment_data.rozee_live_count` +
   `rozee_last_updated` for at least the top 5–10 fields likely to
   appear in the demo run.

### Already-known Sprint 4 items (confirmed ACCEPTABLE)

- #6 — dead `profile_update` trigger branch in `_write_recommendation`.
  Confirmed dead, not wrong. **ACCEPTABLE.**
- #7 — `fetching_fees` / `fetching_market_data` status events not
  emitted. Confirmed missing (Check 5a). **ACCEPTABLE** (listed under
  DEGRADES for visibility but not blocking).
- #8 — `_load_lag_model()` / `_load_affinity_matrix()` caching. Not
  demo-impacting at low load. **ACCEPTABLE.**
- #9 — Alembic migration missing `curriculum_level`. Supabase already
  has it; demo uses Supabase. **ACCEPTABLE.**
- #10 — credential rotation. Post-demo. **ACCEPTABLE.**

---

## OVERALL VERDICT

**AMBER.** One blocking gap: affinity_matrix.json is empty, which
collapses ScoringNode's personalisation output to a constant. Everything
else is either PASS or a known/logged acceptable limitation. The SSE
contract (event types, status values, card/timeline payloads, done-in-
finally, word-chunk semantics, recommendations write-timing) is
structurally correct and matches Point 5 v1.2. universities.json is
clean for NED. lag_model.json has the one load-bearing field
(`computed.future_value`) populated for every field; all remaining
nulls have graceful fallbacks.

**Demo can proceed: YES, with conditions.**
Condition — Fazal must populate affinity_matrix.json with the 32 NED
field_ids before April 29. Without that one data file, the ranking is
deterministic and the core RIASEC-match narrative does not work. Once
that file is populated, no further code changes are required for the
demo path.

---

## POST-AUDIT MAINTENANCE

- logs/README.md updated — new row added to OPUS AUDIT LOGS table.
- No code changes made.
- No data files changed.
