# Why Agentic AI and LangGraph

**Component:** Core system architecture
**Decided:** Architecture Chat v1-v3 (March-April 2026)
**Status:** Locked in CLAUDE.md

---

## What This Is

The FYP uses a LangGraph agentic pipeline instead of a traditional
ML recommendation system. This decision affects every other architectural
choice in the system and is the primary defense point at the viva.

---

## Why Agentic AI — The Rejected Alternatives

### Why Not Traditional ML Recommendation Systems

**Collaborative filtering rejected:**
Collaborative filtering recommends degrees based on what similar students
chose. This requires a large dataset of students with measured profiles
who made career choices and had measurable outcomes. No such dataset
exists for Pakistani secondary students. The cold start problem is fatal —
the system has zero users at launch, making all similarity-based
recommendations impossible.

**Content-based filtering rejected:**
Content-based filtering matches student attributes to degree attributes
using feature vectors. This reduces the recommendation to a lookup table.
It cannot handle the conversational nature of constraint collection
(budget, transport zone, family pressure), cannot adapt its questioning
strategy based on what it already knows about the student, and cannot
answer follow-up questions about WHY a degree was recommended.

**Neural recommendation models rejected:**
Deep learning recommendation models (NCF, BERT4Rec etc.) require even
larger training datasets than collaborative filtering and produce
black-box predictions. A Pakistani family asking "why is CS ranked first?"
cannot be answered with "because the embedding distance was 0.73."

### Why Not a Static Rule Engine

A pure rule engine (if-then-else on marks and stream) was the starting
point before the architecture was designed. It was rejected because:
- It cannot handle natural language input about preferences and constraints
- It cannot explain recommendations in the student's language
- It cannot adapt to new universities or degrees without code changes
- It treats the recommendation as a lookup rather than a reasoning process

---

## Why Agentic AI — The Positive Case

**The recommendation is a reasoning process, not a lookup.**
The system must: collect a profile conversationally → filter by hard
constraints → score by psychological fit → rank by market signal →
explain in the student's context. Each step requires judgment, not
just arithmetic. Agentic AI models this correctly.

**Explainability is a requirement, not a feature.**
Pakistani families need to understand and challenge recommendations.
"Your RIASEC profile shows high Investigative and Conventional scores,
which aligns strongly with CS and Data Science. Your 78% aggregate
meets NED's merit cutoff for CS (typically 75-80%). The job market
for software engineering roles in Pakistan has grown 23% YoY."
This reasoning chain is impossible with black-box ML.

**Constraint handling requires real-time reasoning.**
Budget per semester, transport zone (home_zone 1-5), entry test
requirements, stream eligibility, family career expectations — these
cannot be pre-computed as static features. The ProfilerNode asks about
them conversationally and incorporates them dynamically.

**Linguistic diversity is built-in.**
Pakistani students write in Roman Urdu, English, and code-switched
combinations. Gemini handles this natively without NLP preprocessing
pipelines. An ML system would require separate language detection,
transliteration, and normalization stages.

**The graph structure is extensible.**
Adding new assessment instruments (KCIS, CAAS, VNA) adds new data
fields and updates node logic — it does not require retraining.
Adding new universities updates JSON data files — no model retraining.
This is critical given the FYP timeline and post-viva enhancement plans.

---

## Why LangGraph v1.1 Specifically

**AsyncPostgresSaver with psycopg3:**
LangGraph's checkpoint system persists conversation state between
requests. AsyncPostgresSaver writes checkpoints to Supabase PostgreSQL
using psycopg3. This means a student can close the app mid-conversation
and resume exactly where they left off. Without this, every session
would start from scratch.

**Conditional edges:**
The `route_after_profiler` conditional edge allows the pipeline to
auto-rerun when a student updates a constraint mid-conversation.
A student who says "actually my budget is higher" triggers a full
pipeline rerun automatically, producing updated recommendations without
the student needing to ask again.

**`astream_events` + `aget_state()`:**
LangGraph's streaming API allows the frontend to receive partial results
as they are generated. University recommendation cards appear as the
pipeline processes each degree — the student sees results building
rather than waiting for the full pipeline to complete.

---

## Key Design Decisions

1. **SupervisorNode fail-fast:** SupervisorNode is excluded from LLM retry
   logic. A 30-second delay on intent classification would block the entire
   pipeline. Fail-fast and fall back to "follow_up" is correct here.

2. **Pure Python for FilterNode and ScoringNode:** No LLM in these nodes.
   Filtering by merit cutoffs and scoring by RIASEC fit are deterministic
   calculations. Adding LLM would add latency, cost, and non-determinism
   for no quality gain.

3. **LangChain message objects in all agent nodes:** All nodes use
   `langchain_google_genai.ChatGoogleGenerativeAI` with LangChain
   `HumanMessage`/`SystemMessage` objects. This enables system prompt
   caching, consistent PII scrubbing, and clean model swapping.
   Exception: standalone scripts in `backend/scripts/` may use
   `google.generativeai` directly (locked in CLAUDE.md v2.7).

4. **Gemini for dev, Claude for production:** gemini-3.1-flash-lite-preview
   in development (free tier, 500 RPD). Claude Haiku/Sonnet in production
   Sprint 3+. The abstraction is in `config.py` — swapping models requires
   no code changes.

---

## Known Limitations

- **Gemini API dependency:** If the Gemini API is down, the system fails.
  Post-viva mitigation: transition to Together AI + Qwen3 8B self-hosted.
- **Rate limits:** ResourceExhausted errors handled by `_invoke_with_retry()`
  with 30s/60s/90s backoff. Sprint 4: switch to `anthropic.RateLimitError`
  when migrating to Claude API.
- **LangGraph checkpoint growth:** AsyncPostgresSaver checkpoints accumulate
  in Supabase. Requires periodic cleanup post-viva.

---

## Future Enhancement Triggers

- Transition to Together AI + Qwen3 8B: when privacy requirements increase
  or API costs become significant at scale
- Fine-tuning: when enough student conversation data exists to improve
  ProfilerNode's extraction accuracy on Pakistani cultural context
- Multi-agent: when the system needs to handle parent and student
  simultaneously (MVP-3 Parent Mediation — permanently deferred for now)
