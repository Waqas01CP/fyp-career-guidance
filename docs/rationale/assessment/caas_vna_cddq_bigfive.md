# Why CAAS, VNA, Hybrid CDDQ, and Hybrid Big Five

**Component:** Assessment — Tier 2 and Tier 3 instruments
**Decided:** Architecture Chat v4-v5 (May 2026)
**Status:** Locked in CLAUDE.md v2.5

---

## Overview

Four additional instruments beyond RIASEC and KCIS:
- **CAAS-5-SF** (Tier 2): career adaptability — will the student persist?
- **VNA** (Tier 3): work values — what does the student want from work?
- **Hybrid CDDQ** (Tier 2): career decision difficulty — information gap or family pressure?
- **Hybrid Big Five** (Tier 3): academic persistence and stress vulnerability

Together these instruments enable the ProfilerNode's tier-aware strategy
and the ExplanationNode's personalised framing.

---

## CAAS-5-SF — Career Adapt-Abilities Scale

### Why CAAS

Career adaptability (Savickas, 2005) predicts whether a student will
persist through degree difficulty and adapt to evolving career demands —
not just whether they are interested in the field. A student with perfect
RIASEC fit for Medicine but very low CAAS Concern (not thinking about the
future) and low CAAS Control (external locus of control) is unlikely to
sustain the 5-year MBBS without significant support.

### The 5 Subscales

Concern (planning ahead), Control (taking responsibility), Curiosity
(exploring options), Confidence (self-efficacy in problem-solving),
Cooperation (working with others — added in the 5-SF version).

### Why Not Full CAAS

The full CAAS-28 has 28 questions across the same 5 subscales. The
short form (CAAS-5-SF, 5-6 questions per subscale = 25-30 total) provides
adequate reliability (α ≥ 0.75) while reducing administration burden.
The Cooperation subscale from the 5-SF is specifically relevant for
Pakistani students in team-based degrees (Engineering, Medicine) where
cooperative learning is required.

### Instrument Source

CAAS is an established instrument. The questions are written originally
for this system inspired by the CAAS framework — not copied verbatim from
any published version. The theoretical structure (5 subscales, Likert
anchoring "Least strongly" to "Most strongly") is the standard CAAS format.

---

## VNA — Vocational Needs Assessment

### Why VNA

Work values predict degree and career satisfaction independently of
interest fit. A student who values Social Status will be dissatisfied in
a high-interest, low-prestige career. A student who values Independence
will struggle in a highly supervised clinical role despite loving medicine.
The VNA captures what the student wants from a career, which ProfilerNode
uses to derive `prestige_preference`.

### Why Not Minnesota Importance Questionnaire (MIQ)

The MIQ (Rounds et al., 1981) is the standard TWA-based work values
instrument. It was rejected on licensing grounds — the MIQ carries a
CC BY-NC license (Creative Commons Attribution-NonCommercial). The FYP
system, while academic, could potentially be commercialised post-viva.
Using MIQ content under CC BY-NC creates licensing risk.

### The Original VNA

The VNA is an original 9-question instrument based on TWA theory
(Dawis & Lofquist, 1964 — public domain). Three active dimensions
(4 Sprint questions each — reduced to 3 each for the current scope):

- **Social Status** — importance of external recognition and prestige
- **Independence** — importance of autonomy and self-direction
- **Achievement** — importance of accomplishment and measurable success

Three additional dimensions deferred to Sprint 4:
- Security, Altruism, Compensation

**Viva description:** "Original VNA grounded in the Theory of Work
Adjustment (Dawis & Lofquist, 1964 — public domain), adapted for
Karachi's 15-18 student population. Questions frame work values through
what the student observes in their parents' careers and imagines for
themselves — appropriate for students without work experience."

---

## Hybrid CDDQ — Career Decision Difficulties Questionnaire

### Why CDDQ

The CDDQ (Gati et al., 1996) identifies the specific type of career
decision difficulty a student faces. Two dimensions are most relevant
for Pakistani students:

- **Information Gap** — student lacks knowledge about what careers
  actually involve day-to-day (triggers ExplanationNode to emphasise
  `field_reality_notes`)
- **External Conflict** — student's preferences conflict with family
  expectations (triggers ProfilerNode to shift to agency-affirming mode)

### Why Hybrid (8 Questions, 2 Dimensions Only)

The full CDDQ has 34 items across 10 difficulty categories. Most categories
are not actionable in the current system:
- "Inconsistent information" — requires the student to have conflicting
  information sources, which we cannot address
- "Dysfunctional beliefs" — requires therapeutic intervention, outside scope

The 8 questions (4 per dimension) covering Information Gap and External
Conflict are the minimum that produce actionable routing signals for
ProfilerNode and ExplanationNode.

---

## Hybrid Big Five

### Why Big Five at All

The Big Five personality model (Costa & McCrae, 1992) is the most
empirically validated personality framework for predicting academic and
career outcomes. The question was whether to include it given RIASEC and
CAAS already cover much of the same space.

Two dimensions have independent predictive value beyond CAAS:

**Conscientiousness:**
- Meta-analytic r=0.24 with academic GPA (strongest Big Five predictor)
- CAAS Control covers only ~15% of Conscientiousness variance —
  insufficient overlap to replace it
- A high-RIASEC-fit student with low Conscientiousness in a high-workload
  degree (MBBS, Engineering) is at risk of academic failure regardless
  of interest fit

**Neuroticism:**
- Predicts degree persistence in high-pressure programmes independently
  of CAAS Confidence (~12-20% overlap)
- High Neuroticism + high-pressure degree → ProfilerNode adds stress
  framing to recommendations
- Cannot be adequately captured by any other instrument in the stack

### Why Only Conscientiousness and Neuroticism

Three Big Five dimensions were dropped:

- **Openness:** CAAS Curiosity covers ~40% of Openness variance —
  sufficient. No independent routing value in the current system.
- **Extraversion:** CAAS Cooperation covers the interpersonal dimension
  adequately for career routing purposes.
- **Agreeableness:** Predicts workplace harmony, not field suitability.
  No routing use case in the current system.

### Why "Hybrid"

The 10-question instrument is called Hybrid Big Five because it measures
only Conscientiousness (6 questions) and Neuroticism (4 questions) —
not the full Big Five. The asymmetry (6 vs 4) reflects Conscientiousness
having stronger independent predictive value.

---

## The Assessment Tier System

These four instruments slot into a tier system that determines ProfilerNode
behaviour:

```
Tier 1 (Gate — system functions):
  RIASEC (60q) + Capability Assessment (MCQs) + Aptitude (32q+12 belief)
  Without Tier 1: no meaningful recommendations possible

Tier 2 (Important — full counsellor adaptation):
  Adds KCIS (96q) + CAAS-5-SF (30q) + Hybrid CDDQ (8q)
  ProfilerNode shifts from proxy questioning to CAAS-driven staging

Tier 3 (Accuracy — enriched framing):
  Adds VNA (9q) + Hybrid Big Five (10q)
  ProfilerNode derives prestige_preference, ExplanationNode adds
  stress/values framing

Tiers are NEVER shown to the student as required/optional.
The Profile Dashboard shows "38% complete" framing.
```

**Tier 2 prompt fires once per session:** After turn_count > 2,
ProfilerNode sends a one-time gentle prompt about completing Tier 2
assessments. It never repeats.

---

## Known Limitations

- All instruments are self-report — susceptible to socially desirable
  responding. Pakistani cultural context makes this more pronounced
  (students may report what they think parents want).
- None of the instruments have been validated on Pakistani secondary
  students. Construct validity is theoretical at launch.
- The 257-question total (all instruments combined) is a significant
  burden. Completion rates need to be monitored post-launch.

---

## Future Enhancement Triggers

- If CDDQ External Conflict scores consistently high across all students →
  the family pressure dimension may need expansion (add Social Conflict
  and Contextual Conflict dimensions from the full CDDQ)
- If VNA Social Status scores are skewed high for all students (ceiling
  effect) → add Security and Altruism dimensions from Sprint 4 backlog
- If EQ-i Youth reinstatement trigger fires (Social-RIASEC degrees >30%
  of recommendation pool) → add ~42-45 questions to Tier 2
