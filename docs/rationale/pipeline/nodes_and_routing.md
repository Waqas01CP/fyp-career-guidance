# Pipeline Nodes and Routing Decisions

**Component:** LangGraph pipeline — all nodes
**Decided:** Architecture Chat v1-v5 (March-May 2026)
**Status:** Locked in CLAUDE.md v2.5

---

## Pipeline Overview

```
Student message
     ↓
SupervisorNode (intent classification)
     ↓
ProfilerNode (constraint collection + tier-aware strategy)
     ↓ [route_after_profiler]
FilterNode (hard exclusion + eligibility) ← auto-rerun on profile_update
     ↓
ScoringNode (3D match + FutureValue)
     ↓
ExplanationNode (personalised recommendation narrative)
     ↓
AnswerNode (follow-up, fee, market queries)
```

---

## SupervisorNode

**Why:** Every student message must be classified before routing. Without
intent classification, the system cannot distinguish "what degrees suit me"
(get_recommendation) from "what is the fee for NED CS" (fee_query).

**Why fail-fast (no retry):** SupervisorNode is explicitly excluded from
`_invoke_with_retry()`. A 30-second delay waiting for Gemini rate limit
recovery would block the entire pipeline for every student turn. If
classification fails, falling back to "follow_up" intent is the correct
graceful degradation — the student gets an answer-type response rather
than a recommendation.

**Valid intents:** get_recommendation, follow_up, fee_query, market_query,
profile_update, clarification, out_of_scope.

---

## FilterNode

**Why pure Python (no LLM):** Filtering degrees by merit cutoffs, budget
constraints, transport zone, and stream eligibility is deterministic logic.
Adding LLM would introduce latency, cost, and non-determinism for no
quality gain.

**Hard exclusion hierarchy:**
1. `hec_excluded: true` — never shown, never counted toward minimum display
2. Merit below floor — excluded but counted toward minimum display trigger
3. Budget exceeds constraint — excluded
4. Transport zone mismatch — excluded

**HEC floor distinction (architectural):**
`hec_excluded` entries are permanently invisible. They never enter
`hard_excluded_raw` and are never eligible for minimum display promotion.
This distinction must be preserved across all FilterNode changes.

**Minimum display rule:** Always show at least 5 degrees regardless of
hard exclusions. If fewer than 5 pass all filters, the system promotes
the best-matching excluded degrees (excluding hec_excluded) with clear
flags explaining why they were included.

**Three-state eligibility:**
- fully_eligible: degree within student's stream, meets all cutoffs
- conditionally_eligible: stream eligibility uncertain, flag for confirmation
- ineligible: degree clearly outside student's stream

---

## ScoringNode

**Why pure Python (no LLM):** Scoring is mathematical — RIASEC dot product,
3D geometric distance, FutureValue calculation. Deterministic computation.

**The 3D match formula:**
```
match_score = 0.6 × geometric_distance_3d
            + 0.3 × dot_product_riasec
            + 0.1 × prestige_alignment
```

**FutureValue layers:**
```
pak_now (30%):    Pakistan current job market signal
pak_future (20%): Pakistan trend (slope from monthly_postings_history)
world_now (25%):  Global current demand (BLS)
world_future (25%): Global trend projection
```
LOCAL lag category fields have layer3 weight = 0 (world_future irrelevant
for Medicine, Law, Civil Engineering in Pakistani context).

**layer3a/layer3b split:** layer3 is split 60/40 to prevent future_value
outputs exceeding the 0-10 range that downstream scoring depends on.

**Capability mismatch flag:** FilterNode sets `capability_mismatch_flag`
when student aptitude scores fall more than 25 points below a degree's
`required_capability` threshold. ScoringNode reads this flag. It does not
exclude the degree but lowers its score and triggers ExplanationNode to
add a preparation note.

---

## ProfilerNode

**Why LLM (unlike Filter and Scoring):** Constraint collection is
conversational. The system must ask about budget, transport zone, and
family expectations in natural language, interpret ambiguous responses,
and decide when enough information has been collected. This requires
judgment that cannot be encoded in rule-based logic.

**PROFILER_REQUIRED_FIELDS = []:**
ProfilerNode does NOT aggressively ping students for budget, transport,
and zone. These come from the Step 4 Preferences screen. The profiler
collects them conversationally only when naturally relevant. Forcing
collection produces poor UX and unreliable data.

**Tier-aware strategy (three modes):**
- `tier1_compensatory`: No Tier 2 data — uses conversational proxy
  questions to infer CAAS-equivalent signals
- `tier2_standard`: CAAS + KCIS present — CAAS concern subscale drives
  staging logic
- `tier3_enriched`: All tiers — adds VNA prestige derivation and
  Big Five framing

**family_context collection:** NOT conversational extraction.
`family_career_field` and `family_career_expectation` come from the
Step 4 Preferences screen (dropdown + radio). ProfilerNode asks
`social_pressure_field` once when `family_career_expectation ==
"expects_specific_field"`. Never repeated.

---

## ExplanationNode

**Why mid-tier model minimum:**
ExplanationNode generates the 4-part recommendation narrative that
students and families read directly. Quality matters — Roman Urdu
handling, nuanced career advice, degree-specific framing. Claude Sonnet
(not Haiku) in production.

**social_acceptability_tier framing:**
ExplanationNode adjusts tone based on the degree's social acceptability
tier. For "lower" tier fields (Social Work, Fine Arts, Education) it
phrases recommendations more carefully given Pakistani family expectations —
acknowledging the career path's value while being realistic about family
approval challenges.

**ai_displacement framing:**
When `ai_resistance_score < 40` (high automation risk), ExplanationNode
frames the degree's career path with specific advice about which roles
within the field are protected vs. automatable. Not a negative signal —
an informative one.

---

## AnswerNode

**Why separate from ExplanationNode:**
AnswerNode handles follow-up, fee, and market queries after a recommendation
has been made. These require different system prompts and different data
retrieval patterns than the initial recommendation generation. Keeping them
separate maintains single-responsibility per node.

**Slim roadmap in follow-up:**
AnswerNode receives a slim roadmap representation (~50 tokens per degree
vs ~200 for the full representation). This reduces the context window
usage for follow-up queries where the full roadmap is rarely needed.

---

## route_after_profiler — The Conditional Edge

**Why this exists:**
When a student updates a constraint mid-conversation ("my budget is
actually higher" or "I can travel further"), the system needs to rerun
the full pipeline with the updated constraints. Without this, recommendations
become stale after any profile update.

**How it works:**
After ProfilerNode runs with `last_intent == "profile_update"` AND
`profiling_complete == True`, `route_after_profiler` returns "filter_node"
instead of END. The full pipeline reruns automatically. The student
sees updated university cards without needing to explicitly ask for
a rerun.

**University cards emission on profile_update:**
When the pipeline reruns via this edge, university cards are emitted
exactly as they are on `get_recommendation`. The `trigger` field in the
recommendation record is set to "profile_update" to distinguish this from
an initial recommendation.

---

## Known Limitations

- ProfilerNode's tier-aware strategy requires Tier 2 data to be present.
  Students who skip Tier 2 assessments get the `tier1_compensatory`
  strategy which uses proxy questions — less accurate but functional.
- ExplanationNode token count (~975 in testing) exceeds the 400-700 token
  target from BACKEND_CHAT_INSTRUCTIONS. The overage is justified by the
  quality requirement — trimming further would remove clinically necessary
  framing for high-pressure degrees.

---

## Future Enhancement Triggers

- If `profile_update` auto-reruns become frequent (>3 per session) →
  consider debouncing (collect multiple updates before triggering rerun)
- If ExplanationNode response quality degrades at Haiku → switch
  ExplanationNode to Sonnet earlier than planned Sprint 3 gate
- MVP-3 Parent Mediation: permanently deferred — `conflict_detected`
  always False. Reinstate only if there is a clear product roadmap for
  parent-facing features
