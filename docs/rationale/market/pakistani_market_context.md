# Pakistani Market Context Decisions

**Component:** Market-specific design choices throughout the system
**Decided:** Architecture Chat v3-v5 (April-May 2026)
**Status:** Locked in CLAUDE.md and affinity_matrix prestige_tier values

---

## CS vs SE — Separate Field_ids with Different Demand Signals

### Why They Are Distinct

In international job market contexts, Computer Science and Software
Engineering are often treated interchangeably. In Pakistan they are not:

**CS (computer_science):**
- More theoretical, mathematics-heavy, research-oriented
- Pakistani employers posting "CS Graduate" roles typically want:
  algorithm-capable candidates, data structures expertise, research-adjacent work
- Common contexts: NCAI-funded projects, university R&D labs, academic
  institutions, government ICT initiatives
- Job market signal: smaller, more specialised pool

**SE (software_engineering):**
- More applied, development-focused, industry-oriented
- Pakistani employers posting "Software Engineer" roles typically want:
  production-ready developers who can build systems immediately
- Common contexts: Systems Limited, 10Pearls, Arbisoft, Netsol, Techlogix,
  VentureDive, Avanza Solutions — the bulk of Pakistan's IT export sector
- Job market signal: much larger, growing strongly with IT exports

### Why This Matters for the System

If both are collapsed into `computer_science`, the slope calculation
for SE demand is diluted by CS demand (which is lower). A student
interested specifically in applied software development gets
FutureValue influenced by research-lab demand patterns that are
irrelevant to their career path.

Separate field_ids produce separate `monthly_postings_history` arrays,
separate `market_phase` values, and separate `slope` calculations.
An SE-interested student sees the IT export sector's strong upward
trend. A CS-interested student sees the more modest but specialised
research role demand.

---

## Pakistani Title Conventions — Disambiguation Rules

These conventions are embedded in Script C's Gemini system prompt
because they are frequently misinterpreted without Pakistani context:

**"Executive" = Mid-level (NOT C-suite):**
In international English, "Executive" signals senior leadership.
In Pakistan's corporate culture, "Executive" is a mid-level individual
contributor title — the standard title for a professional with 2-5 years
of experience in most industries.
- "IT Executive" → IT support or systems administration role
- "HR Executive" → HR generalist at mid-level
- "Marketing Executive" → marketing coordinator or specialist
These are NOT leadership roles. Mapping them to management field_ids
would be incorrect.

**"Officer" = Entry-level:**
"Officer" in Pakistan's formal corporate structure (especially banks,
telecom, FMCG) signals an entry-level professional role — equivalent
to "Analyst" or "Associate" in Western usage.
- "HR Officer" → entry-level HR, likely requires business_bba or psychology
- "Finance Officer" → entry-level accounting, requires finance_accounting
- "Technical Officer" → entry-level technical support

**"Associate" = Context-dependent:**
Unlike the corporate banking usage of "Associate" as a specific senior
tier, in Pakistan "Associate" usually means entry-to-mid level:
- "Research Associate" at a university → PhD/Master's track, CS or relevant
- "Associate Engineer" → graduate engineer, entry level
- "Associate Consultant" → entry-level consulting role

---

## Prestige Hierarchy — Karachi Social Reality

The prestige_tier values in affinity_matrix.json reflect Karachi's
social hierarchy for degree approval, not objective career quality.
A degree can provide excellent career outcomes while being low-prestige
in family perception — the system surfaces this tension honestly.

**Why prestige is encoded (not ignored):**
Pakistani family decision-making in degree choice is heavily prestige-driven.
A recommendation system that ignores prestige will be rejected by families
regardless of how well it matches the student's interests and aptitude.
Encoding prestige allows the system to:
1. Surface the prestige alignment between student's values and the degree
2. Prepare students for family conversations about lower-prestige degrees
3. Allow ExplanationNode to frame lower-prestige degrees with appropriate
   sensitivity

**The Karachi hierarchy (approximate):**
```
10 — Medicine/MBBS: universal family approval, highest social status
 9 — Engineering at NED/FAST/top institutions: strong family approval
 8 — CS/Software Engineering: high approval, growing rapidly
 7 — Law/LLB: respected, legal profession prestige
 6 — Business/BBA at IBA/top institutions: respected in commercial families
 5 — Other Engineering, Pharmacy, Dentistry: moderate approval
 4 — Social Sciences, Economics, Psychology: mixed approval
 3 — Social Work, Fine Arts, Education B.Ed: lower approval in many families
```

**This hierarchy is Karachi-specific:**
Lahore and Islamabad have somewhat different orderings — medical college
prestige varies significantly by city, and certain fields have regional
prestige differences. Post-viva: add city-specific prestige adjustment if
expanding beyond Karachi.

---

## Gulf Demand as a Career Signal

For many Pakistani families, the Gulf market (UAE, Saudi Arabia, Qatar)
is as relevant as the domestic Pakistani market for career planning.
Engineering, medicine, nursing, and construction careers in the Gulf
are major aspirational paths — particularly for families with existing
Gulf connections.

**gulf_demand_tier in lag_model:**
- "high": Civil Engineering, Mechanical Engineering, Medicine, Nursing,
  Construction Engineering — strong Gulf recruitment
- "medium": Electrical Engineering, CS/SE (growing but more domestic)
- "low": Education, Social Work, Psychology — minimal Gulf demand
- "not_applicable": Fine Arts, Mass Communication — Gulf demand exists
  but is niche

ExplanationNode uses `gulf_demand_tier` when framing career prospects
for degrees where Gulf migration is a realistic path. This is especially
important for lower-domestic-demand fields where Gulf demand partially
compensates.

---

## Roman Urdu and Code-Switching

Pakistani students write in Roman Urdu (Urdu language in Latin script),
English, and code-switched combinations of both. Examples from real usage:
- "mujhe CS karni hai" (I want to do CS)
- "which uni best hai Karachi mein?" (which uni is best in Karachi?)
- "budget thora tight hai" (budget is somewhat tight)

**Why native LLM handling (not preprocessing):**
Gemini handles Roman Urdu and code-switching natively without requiring:
- Language detection preprocessing
- Transliteration pipelines
- Separate Arabic-script Urdu models
- Translation steps

The SupervisorNode, ProfilerNode, and ExplanationNode system prompts
include instructions to respond in the same language/script mix as the
student. This is handled in the LLM layer — no code required.

---

## Known Limitations

- The prestige hierarchy was defined by Architecture Chat based on
  general Karachi market knowledge — not validated with a survey of
  Pakistani families. Post-viva validation recommended.
- Gulf demand tiers were assigned based on general knowledge — not
  backed by Gulf job posting data. Post-viva: add Gulf job market
  data source (GulfTalent, Bayt.com) to the scraper pipeline.
- Roman Urdu handling relies entirely on Gemini's training data.
  If Gemini fails on a specific Roman Urdu dialect or regional
  variation, there is no fallback.

---

## Future Enhancement Triggers

- If the system expands beyond Karachi → add city parameter to prestige
  tier lookup, create city-specific prestige tables in affinity_matrix
- If Gulf demand becomes a primary use case → add Gulf job posting
  data source to the scraper pipeline (GulfTalent API or equivalent)
- If Roman Urdu handling degrades after model changes → add explicit
  Roman Urdu examples to SupervisorNode system prompt
