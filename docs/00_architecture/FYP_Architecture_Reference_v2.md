# FYP Architecture Discussion Reference — v2
## AI-Assisted Academic Career Guidance System
## Architecture Chat v5 — Post-Demo, Sprint 3+
## Supersedes: FYP_Architecture_Discussion_Reference.md (v1, outdated)
## Compiled: May 2026

---

> **How to use this document:**
> Read Section 10 (Master Sequencing Plan) first for implementation order.
> Use the Table of Contents to jump to any decision. Every decision shows:
> the original question → the answer → any follow-up → the final position.
> **[FINAL]** = locked decision. **[OPEN]** = still pending. **[DEFERRED]** = not now, documented gap.
>
> **Priority order for all decisions:**
> 1. What Waqas says in the current conversation — always highest
> 2. CLAUDE.md from the repository — second
> 3. This document — background context and defaults

---

## TABLE OF CONTENTS

1. [System Algorithms — What They Are and Their Gaps](#1-system-algorithms)
2. [Named vs Custom Algorithms — Does It Matter?](#2-named-vs-custom-algorithms)
3. [Algorithm Validity — Do They Work?](#3-algorithm-validity)
4. [Node-Level Algorithm Audits](#4-node-level-audits)
5. [Counsellor Replication — The Real-World Case Problem](#5-counsellor-replication)
6. [Assessment Instruments — Complete Phase 1 Decisions](#6-assessment-instruments)
7. [Karachi Local Context — All 13 Dimensions](#7-karachi-local-context)
8. [Machine Learning — Why Not and When](#8-machine-learning)
9. [Open Source LLMs vs Gemini API](#9-open-source-llms)
10. [Master Sequencing Plan](#10-master-sequencing-plan)
11. [Dashboard and UX Decisions](#11-dashboard-and-ux)
12. [Research Citations Required](#12-research-citations)
13. [Appendix A — All Decisions Summary](#appendix-a)
14. [Appendix B — Team Ownership Table](#appendix-b)

> **Version history:**
> v2.0 — Initial complete document (May 2026)
> v2.1 — Added: Assessment tiers, subject-specific question confirmation, ProfilerNode
>         incomplete-profile detection, Step 4 family context expansion, session-to-tier
>         mapping. Updated: Dimension 2 family extraction approach, Phase 0c, Phase 2
>         node sequence, Appendix A and B.

---

## 1. SYSTEM ALGORITHMS

### 1.1 Original Five Components

---

#### Algorithm 1: RIASEC Personality Matching
**Original implementation:** Normalised dot product.
```
raw_match = Σ (student[i] × degree[i])
match_score = raw_match / theoretical_max   → 0.0 to 1.0
```
**Problem identified:** Dot product treats all six RIASEC dimensions as independent and geometrically equal. It cannot detect that R and S are opposites, that R and I are adjacent, or that R=90+S=90 is psychologically implausible. Geometrically wrong.

**[FINAL] Upgrade to 3D Spherical Model.** See Section 6.1 for full evolution.

---

#### Algorithm 2: Career Future Value (Multi-Layer Weighted Signal Model)
**What it does:** Answers "will there be jobs when you graduate in 4 years?"

Three data layers:
| Layer | What it Measures | Source |
|---|---|---|
| Layer 1 (`pak_now`) | Current Pakistani job demand | Rozee.pk counts, YoY growth |
| Layer 2 (`pak_future`) | Pakistan trend direction | Google Trends PK, PSEB export data |
| Layer 3a/3b (`world_now/future`) | Global market momentum | BLS, LinkedIn Talent Trends |

Lag categories determine Layer 3 weight:
- **LEAPFROG** (AI, Cloud — already arrived): Layer 3 = 50%
- **FAST** (CS, Cybersecurity): Layer 3 = 40%
- **LOCAL** (Medicine, Law, Civil): Layer 3 = 0%

**Problems identified:** Static score doesn't represent market curve position; cross-field normalisation creates instability when new fields are added; `pak_future` derivation chain has unvalidated lag_multiplier assumptions.

**[FINAL]** Add slope calculation, rank percentile normalisation, coverage penalty, staleness multiplier. See Section 4.3.

---

#### Algorithm 3: Composite Scoring
```
total_score = (w1 × match_score) + (w2 × future_score / 10)
w1 = 0.6, w2 = 0.4 (default for inter mode)
```
**Problem:** Linear, no interaction term. A perfect RIASEC match for a dying field scores similarly to a moderate match in a strong field.

**[FINAL]** Revise to include interaction term after RIASEC upgrade is complete. Do not revise in isolation.

---

#### Algorithm 4: Capability Score Blend
```python
gap = capability_score - reported_grade
if abs(gap) >= 25:
    raw_effective = (reported * 0.75) + (capability * 0.25)
    effective_grade = clamp(raw_effective, reported ± 10)
```
**Known weakness:** Both the 25-point threshold and ±10 cap are arbitrary design choices. Acknowledged; revisit once aptitude data is collected.

---

#### Algorithm 5: FilterNode — Hard Constraint Enforcement
Deterministic rule engine. Not a learned model. Four rules: merit cutoff, budget, eligibility, minimum-display promotion.

**Problems:** Binary eligibility wrong for in-progress students; no aggregate formula validation; merit cutoffs become stale; capability-academic mismatch not detected.

**[FINAL]** Three-state eligibility model, formula validation script, staleness field, capability mismatch flag. See Section 4.1.

---

### 1.2 Missing Algorithms — Three Identified Gaps

**Missing Algorithm A: Hexagonal Congruence (RIASEC Distance)**
Dot product treats dimensions as independent. Full solution is the 3D spherical model — see Section 6.1.

**Missing Algorithm B: Market Trajectory / Slope Calculation**
FutureValue is a static score. A field at Peak vs Emerging may have the same current score but very different prognoses for a student graduating in 4 years.

**[FINAL] Slope formula:**
```python
import numpy as np

def compute_market_phase(time_series: list[float]) -> dict:
    t = np.arange(len(time_series))
    y = np.array(time_series)
    slope = np.polyfit(t, y, 1)[0]
    coeffs = np.polyfit(t, y, 2)
    a, b, c = coeffs
    acceleration = 2 * a
    if a < 0:
        peak_t = -b / (2 * a)
        years_to_peak = max(0, (peak_t - len(time_series)) / 12)
    else:
        years_to_peak = None
    if slope > 0.1 and acceleration > 0:
        phase = "Emerging"
    elif slope > 0.1 and acceleration <= 0:
        phase = "Growth"
    elif abs(slope) <= 0.1:
        phase = "Mature"
    elif slope < -0.1 and acceleration < 0:
        phase = "Declining"
    else:
        phase = "Peak"
    return {"slope": slope, "acceleration": acceleration,
            "years_to_peak": years_to_peak, "market_phase": phase}
```
Data source: Rozee.pk monthly job posting counts → `monthly_postings_history` array in lag_model.json. Script runs automatically to populate `market_phase`, `slope`, `years_to_peak`.

**Missing Algorithm C: Differentiation / Consistency Scoring**
A student with R=90, I=20 (clear profile) needs very different guidance from one with all dimensions at ~50 (flat profile). Current system cannot detect this.

**[FINAL] Implementation:**
```python
def compute_differentiation(riasec: dict) -> float:
    values = list(riasec.values())
    return max(values) - min(values)

ADJACENCY = {
    frozenset(['R','I']): 3, frozenset(['I','A']): 3, frozenset(['A','S']): 3,
    frozenset(['S','E']): 3, frozenset(['E','C']): 3, frozenset(['C','R']): 3,
    frozenset(['R','A']): 2, frozenset(['I','S']): 2, frozenset(['A','E']): 2,
    frozenset(['S','C']): 2, frozenset(['E','R']): 2, frozenset(['C','I']): 2,
    frozenset(['R','S']): 1, frozenset(['I','E']): 1, frozenset(['A','C']): 1,
}

def compute_consistency(riasec: dict) -> int:
    top2 = sorted(riasec.items(), key=lambda x: x[1], reverse=True)[:2]
    pair = frozenset([top2[0][0], top2[1][0]])
    return ADJACENCY.get(pair, 2)

# ProfilerNode strategy routing:
diff = compute_differentiation(riasec)
if diff < 20:   strategy = "exploration_mode"
elif diff < 40: strategy = "clarification_mode"
else:           strategy = "directive_mode"
```

---

## 2. NAMED VS CUSTOM ALGORITHMS

**Question:** Should it matter that the system uses no famous named algorithms (KNN, Random Forest, SVM)?

**Answer:** No. The choice is *appropriate*, not arbitrary. Named alternatives would require:
- KNN: labelled outcome data (student chose X, outcome was Y) — doesn't exist
- Random Forest / SVM: supervised training labels — same problem
- K-Means: outcome data to validate cluster meaning — same problem

**What the system is:** A multi-criteria decision support system combining:
- Psychometrically validated framework (Holland's RIASEC, used by US Dept of Labor O*NET since 1990s)
- Domain-specific knowledge encoding (lag model)
- Deterministic constraint satisfaction (FilterNode)
- LLM-augmented explanation (not decision-making — only articulation)

**The LLM does not pick degrees. The algorithms do.**

**[FINAL] Viva answer:** "We chose algorithms that match the data we have. Supervised ML requires labelled outcome data from thousands of graduated students — that data doesn't exist for Karachi universities at this granularity. Our approach is fully interpretable and auditable. Adding unsupervised clustering without validated outcome labels would be ML theatre."

---

## 3. ALGORITHM VALIDITY

**What works well:**
- FilterNode is deterministic and correct. Students below cutoff never see impossible degrees. This alone exceeds 90% of existing Pakistani guidance tools.
- Dot product RIASEC match produces directionally correct results even with its limitations.
- FutureValue correctly reflects Karachi labour market reality — CS fields score 8-9, traditional arts score 3-4.
- Capability blend provides meaningful correction in edge cases.

**Known limitations (state at viva):**
- RIASEC was designed for work environment compatibility, not academic orientation prediction. Used as one of three inputs, not sole determinant.
- FutureValue is hand-estimated for new fields — data scarcity acknowledged.
- Capability blend thresholds are design choices pending empirical calibration.

**Value proposition:** Combines three inputs no existing Pakistani guidance tool combines: personality (RIASEC), academic eligibility (merit cutoffs), and labour market trajectory (lag model).

---

## 4. NODE-LEVEL AUDITS

### 4.1 FilterNode

#### Gap 1: Binary Eligibility Too Harsh for In-Progress Students
**[FINAL] Three-state model:**
```python
if student_mode in ["matric_complete", "inter_complete"]:
    eligible = aggregate >= cutoff_min
    # If aggregate very low (e.g. 44%): flag "no_eligible_degrees_confirmed"
    # Route ExplanationNode to improvement-counselling mode

elif student_mode in ["matric_planning", "inter_planning"]:
    gap = cutoff_min - current_aggregate
    if gap <= 0:    planning_flag = "already_eligible"
    elif gap <= 10: planning_flag = "minor_improvement_needed"
    elif gap <= 20: planning_flag = "significant_improvement_needed"
    else:           planning_flag = "currently_out_of_range"
    # Show with planning_mode flag — do NOT exclude
```

#### Gap 2: No Aggregate Formula Validation
**[FINAL]** In `validate_universities.py` (CI/build step, not per-request):
```python
for degree in universities:
    formula = degree["aggregate_formula"]
    total_weight = sum(formula.values())
    assert abs(total_weight - 1.0) < 0.01, \
        f"{degree['degree_id']}: weights sum to {total_weight}"
```

#### Gap 3: Merit Cutoffs Become Stale
**[FINAL]** Add `cutoff_year` field to each degree. ExplanationNode caveat when `cutoff_year < current_year`. Admin dashboard for staleness monitoring is post-FYP.

#### Gap 4: Capability-Academic Mismatch Not Detected
**[FINAL]** Add `required_capability` profiles to affinity_matrix:
```json
"required_capability": {"numerical": 70, "logical": 75, "spatial": 50, "verbal": 45}
```
```python
def compute_capability_gap(student_caps, degree_req_caps):
    gaps = {}
    for subject, required in degree_req_caps.items():
        student_val = student_caps.get(subject, 0)
        if student_val < required:
            gaps[subject] = required - student_val
    return gaps
# If total gap > threshold: capability_mismatch_flag = True
```
Fazal writes `required_capability` profiles. Backend adds detection logic.

---

### 4.2 ScoringNode

#### Gap 1: Linear Weighting, No Interaction Term
**[FINAL] After RIASEC upgrade is complete:**
```python
interaction = match * (future / 10)
total = 0.5 * (0.6 * match + 0.4 * (future / 10)) + 0.5 * interaction
```

#### Gap 2: Capability Blend Threshold Arbitrary
**[FINAL]** Acknowledged design choice. Revisit with aptitude data. Do not change now.

#### Gap 3: Two Mismatch Types, Only One Detected
Currently detected: stated preference ≠ RIASEC top match.
Not detected: capability scores below degree requirements.
**[FINAL]** Second mismatch type added via Gap 4 above.

---

### 4.3 FutureValue (Lag Model)

#### Gap 1: Data Quality Flagging
**[FINAL]** Fazal adds to every lag_model entry:
```json
"data_status": {
  "pak_jobs_last_updated": "2025-11",
  "world_bls_year": 2024,
  "missing_signals": [],
  "confidence": "high"
}
```

#### Gap 2: Cross-Field Normalisation Creates Instability
Three severe impacts: (1) adding one outlier field changes all existing scores; (2) missing data inflates scores of fields with partial data; (3) stale data lock-in.

**[FINAL] Solutions:**

*Rank percentile normalisation (recommended):*
```python
from scipy.stats import rankdata
def rank_normalise(values: list[float]) -> list[float]:
    ranks = rankdata(values)
    return [(r - 1) / (len(values) - 1) for r in ranks]
```

*Data coverage penalty:*
```python
coverage_ratio = len(available_signals) / 4
coverage_penalty = 0.85 + 0.15 * coverage_ratio
future_value = raw_future_value * coverage_penalty
```

*Staleness multiplier:*
```python
months_since_update = compute_months_since(data_status["pak_jobs_last_updated"])
if months_since_update > 36:   staleness_multiplier = 0.75
elif months_since_update > 18: staleness_multiplier = 0.90
else:                          staleness_multiplier = 1.0
future_value = future_value * staleness_multiplier
```

#### Gap 3: Pakistan Future Derivation Accuracy
The `lag_multiplier` per lag_category (LEAPFROG=0.8, FAST=0.5, LOCAL=0.0) has no empirical basis. Acknowledged. Calibration against PSEB/Rozee historical data is Sprint 4.

---

### 4.4 ExplanationNode

#### Gap 1: LLM Hallucination Under Information Poverty
**[FINAL]** Add to system prompt:
```python
EXPLANATION_NULL_GUARD = """
CRITICAL RULE: If roadmap_section contains only planning_mode entries or is empty,
begin your response with: "Based on current information, the system has not confirmed
eligible degrees yet. Here is what the pathway looks like from where you are now."
NEVER use the word "processing". NEVER imply the system is still calculating.
"""
```

#### Gap 2: No Confidence Level in Output
**[FINAL]** Compute and pass to all five recommendation cards:
```python
def compute_confidence_level(state: AgentState) -> str:
    score = 0
    if state["student_mode"] in ["inter_complete", "matric_complete"]: score += 3
    elif "planning" in state["student_mode"]: score += 1
    riasec = state["student_profile"]["riasec_scores"]
    differentiation = max(riasec.values()) - min(riasec.values())
    if differentiation >= 40: score += 2
    elif differentiation >= 20: score += 1
    top5 = state["current_roadmap"][:5]
    confirmed = sum(1 for d in top5 if d.get("merit_tier") != "improvement_needed")
    if confirmed >= 3: score += 2
    elif confirmed >= 1: score += 1
    if score >= 6: return "high"
    elif score >= 3: return "moderate"
    else: return "low"
```

---

## 5. COUNSELLOR REPLICATION

### 5.1 What the System Currently Handles
- Mismatch detection (stated preference vs RIASEC top match)
- ProfilerNode 3-stage counsellor strategy
- FutureValue naturally penalises declining fields if data is correct

### 5.2 Five Gaps — What It Does NOT Handle

**Gap 1: AI Displacement Trap**
Field may currently have good FutureValue but is being automated. Solution: `ai_displacement` block in lag_model using AI Resistance Score (ARS) framework.

**ARS framework:** Four sub-dimensions (25 points each): Physical Presence, Human Relationship, Creative Judgment, Ethical Accountability. Higher ARS = more protected. Correlates strongly (r = −0.81) with Frey-Osborne automation probability. Better calibrated than raw Frey-Osborne (which overstated risk).

**[FINAL] Fazal adds to lag_model per field:**
```json
"ai_displacement": {
  "ai_resistance_score": 72,
  "physical_presence": 20,
  "human_relationship": 18,
  "creative_judgment": 15,
  "ethical_accountability": 19,
  "frey_osborne_probability": 0.28,
  "primary_risk": "Routine analysis tasks automatable; advisory roles protected"
}
```
Note: Use 0-100 continuous scale, not 3-category tags (low/medium/high is too coarse).

**Gap 2: Family Context — Not Extracted as First-Class Signal**
**[FINAL]** Add to ProfilerNode extraction schema:
```python
PROFILER_EXTRACTION_FIELDS = {
  "family_profession": str,   # "medicine", "engineering", "business", "other"
  "family_expectation": str,  # "follows family field", "open", "specific: X"
  "social_pressure_field": str,
}
```
ExplanationNode framing for doctor family case: "Your family background in medicine provides real advantages — mentorship, clinical exposure, networks. The question is whether your RIASEC profile and academic trajectory support a medical path. Currently your profile shows [X]."

**Gap 3: Social Acceptability — Field Exists, Not Activated**
`social_acceptability_tier` exists in affinity_matrix but is UNUSED.
**[FINAL]** Activate in ExplanationNode. When tier is "low" or "moderate": "This degree is a strong technical and market match. Career paths here sometimes require navigating family and social expectations early on."
System NEVER blocks — it frames with cultural context, preserving student agency.

**Gap 4: Real-World Case Knowledge — Environmental Feedback**
This is NOT an assessment problem. It is a knowledge base problem.
**[FINAL]** Fazal adds `field_reality_notes` to each field in lag_model:
```json
"field_reality_notes": {
  "karachi_context": "CS graduates face highly competitive market. Top 40% secure roles immediately.",
  "typical_career_trajectory": "Junior dev (1-3 yr) → Mid (3-6 yr) → Senior/Lead (6+ yr)",
  "known_disruptors": "AI tools reducing entry-level hiring by 15-20% annually since 2024",
  "family_social_fit": "high_acceptability",
  "required_commitment": "Continuous learning mandatory — field moves fast"
}
```

**Gap 5: Locus of Control / Agency in Family-Pressure Contexts**
**[FINAL]** ProfilerNode extraction: soft questions about decision agency. When external locus + family pressure detected, ExplanationNode adds framing about decision agency. Formally addressed by CAAS-5-SF Cooperation + Control subscales in the assessment stack.

---

## 6. ASSESSMENT INSTRUMENTS — PHASE 1 DECISIONS

### 6.1 RIASEC Model Evolution — From Dot Product to 3D

#### Stage 1: Original — Dot Product (SUPERSEDED)
Treats six dimensions as independent. Cannot detect R-S opposition or hexagonal adjacency.

#### Stage 2: Prediger 2D Projection
Two bipolar axes:
- **People ↔ Things:** S,E (people) vs R,I (things)
- **Ideas ↔ Data/Structure:** A,I (ideas) vs C,E (data)

```python
def to_prediger_2d(riasec: dict) -> tuple[float, float]:
    R,I,A,S,E,C = [riasec.get(k,0) for k in ('R','I','A','S','E','C')]
    people_things = 0.5*(E+S) - 0.5*(R+I)
    ideas_data    = 0.5*(C+E) - 0.5*(A+I)
    return people_things, ideas_data
```
Fixes adjacency problem. Fixes the R-S opposition detection.

**Research note:** Factor analyses confirm this 2D structure. Research across collectivistic cultures (Turkish, Caribbean) validates the structure better than the flat hexagon.

#### Stage 3: Personal Globe Inventory — 3D Spherical Model (FINAL)
Tracey & Rounds (1996, 2002) found a third dimension: **Prestige**. North pole = high prestige (Medicine), South pole = low prestige. Critical for Pakistan where prestige is the dominant family consideration.

Three dimensions:
1. People ↔ Things (horizontal)
2. Ideas ↔ Data (horizontal, orthogonal to 1)
3. Prestige (vertical)

**The 8 Octant Types in Karachi context:**
| Octant | RIASEC | Karachi Degrees |
|---|---|---|
| Social Facilitating | High S, High Prestige | Medicine, Law, Management |
| Managing | High E, Moderate Prestige | Business, Civil Service |
| Business Detail | High C, Moderate Prestige | Accounting, Finance |
| Data Processing | High I/C, Moderate Prestige | CS, Data Science |
| Mechanical | High R, Low-Moderate Prestige | Engineering |
| Artistic | High A, Variable Prestige | Design, Architecture |
| Helping | High S, Lower Prestige | Social Work, Teaching |
| Nature | High R/I, Lower Prestige | Agriculture, Environmental |

**Implementation plan (no new quiz questions needed):**

Step A: Add Prediger 2D projection to scoring_node.py (~20 lines)
Step B: Derive prestige preference from ProfilerNode's family_profession extraction — NOT a new quiz dimension
Step C: Fazal rebuilds affinity_matrix with 3D coordinates per field:
```json
{"field_id": "cs", "people_things": -3.5, "ideas_data": 2.8, "prestige_tier": 8}
```
Step D: New match score in ScoringNode:
```python
def compute_3d_match(student_riasec, degree_affinity):
    s_pt, s_id = to_prediger_2d(student_riasec)
    d_pt = degree_affinity["people_things"]
    d_id = degree_affinity["ideas_data"]
    max_dist = 200
    distance_2d = ((s_pt-d_pt)**2 + (s_id-d_id)**2)**0.5
    match_2d = 1 - (distance_2d / max_dist)
    dot_match = compute_dot_product_match(student_riasec, degree_affinity)
    return max(0.0, min(1.0, 0.6*match_2d + 0.4*dot_match))
```
Step E: Add differentiation/consistency scoring (see Section 1.2)

#### Hexagonal Triangle Combinations (for ProfilerNode inconsistency detection)
| Triangle | Meaning | Example Degrees |
|---|---|---|
| R-I-C | Things+Data | CS, Data Engineering, Systems Analyst |
| S-E-A | People+Creative | Marketing, NGO, Education Management |
| R-I-A | Technical Creative | Architecture, Game Design, Robotics |
| I-A-S | Research+Social | Psychology, Biomedical Research |
| A-S-E | People+Creative Leader | PR, Education, Media Management |
| S-E-C | Social+Structured | HR, Public Admin |
| E-C-R | Business+Technical | Industrial Eng, Operations |
| C-R-I | Data+Technical | CS, Data Science, Embedded Systems |

If top 3 RIASEC types don't form a triangle (e.g., R, S, C — R and S are opposites): ProfilerNode flags inconsistent profile and probes.

---

### 6.2 KCIS — Karachi-Contextualised Interest Sub-Scales

**Decision:** 96 questions (24 sub-scales × 4 questions each). Covers all Karachi degree categories.

**Sub-scale count clarification:** There are 22 RIASEC-typed sub-scales (grouped within the six RIASEC types) plus 2 cross-cutting sub-scales (Linguistic/Literary and Religious/Islamic Studies) that do not belong strictly within one RIASEC type. Total: 24 sub-scales × 4 questions = 96 questions.

**Legal basis:** Holland's RIASEC theory is public domain. SII's specific 291 items and occupational scoring database are proprietary — not used. Category names are descriptive labels for real-world activity clusters — not protectable. Questions are original. Viva description: "Karachi-Contextualised Interest Sub-Scale (KCIS) built on Holland's public domain RIASEC theoretical framework, extended with 22 domain-specific sub-scales mapped to HEC-recognised degree programmes."

**Why KCIS is stable for new universities:** Sub-scales are designed at the *degree category* level, not the degree level. Any new Karachi bachelor's degree will map to an existing sub-scale. Adding a university requires only populating affinity_matrix rows — no new questions.

**The 22 sub-scales:**

Within Investigative (5):
1. Mathematical/Computational — CS, AI, Data Science, Mathematics, Statistics, Actuarial
2. Biological/Life Sciences — Biology, Biotechnology, Biochemistry, Genetics, Microbiology
3. Clinical/Health Sciences — Medicine, Pharmacy, Allied Health
4. Physical Sciences — Physics, Chemistry, Engineering Sciences, Petroleum
5. Research/Analytical — Pure Sciences research orientation

Within Realistic (3):
6. Mechanical/Electrical/Electronic Systems — ME, EE, Automotive, Industrial
7. Civil/Construction/Spatial — Civil Engineering, structural aspects
8. Technology/Digital Systems — Computer Systems, Telecom, IT Infrastructure

Within Artistic (5):
9. Visual/Graphic Design — Fine Arts, Communication Design, Digital Media
10. Spatial/Interior/Fashion Design — Interior, Textile, Fashion
11. Architecture (design orientation) — Architecture aesthetic aspects
12. Media/Journalism/Film — Mass Comm, Film, Journalism, Advertising
13. (Reserved for future creative sub-scale if needed)

Within Social (4):
14. Clinical/Patient Care — Nursing, DPT, Allied Health, Public Health
15. Teaching/Education — B.Ed, Education, Sports Sciences
16. Community/Counselling — Social Work, Sociology, Psychology, Development Studies
17. Law/Advocacy/Governance — LLB, Political Science, International Relations

Within Enterprising (2):
18. Business/Commerce/Entrepreneurship — BBA, Management, Marketing
19. Leadership/Public Service — Public Admin, Maritime, Civil Service

Within Conventional (3):
20. Financial/Accounting/Actuarial — Accounting, Finance, Islamic Banking, Commerce
21. Data/Analytics/Information Management — Business Analytics, MIS
22. Administrative/Organisational — SCM, HR, Operations, Library & Information Science

Cross-cutting (2):
23. Linguistic/Literary/Humanities — English, Urdu, Arabic, History, Philosophy, Languages
24. Religious/Islamic Studies — Islamic Studies, Quran, Islamic History

*(Note: sub-scales 23-24 are cross-cutting, not strictly within one RIASEC type)*

---

### 6.3 Aptitude Test + Domain-Specific Belief Questions

**Decision:** 44 questions total (8 timed aptitude per dimension × 4 dimensions = 32, plus 3 belief questions per dimension × 4 = 12).

**Why 8 not 6 per dimension:** 6 items is the psychometric minimum for reliable measurement. At 6 timed questions, a single distracted answer moves the score by 16%. At 8 questions, 12%. Aptitude is timed (adding variance) so 8 is the appropriate minimum.

**Four dimensions:**
| Dimension | What It Tests | Predicts |
|---|---|---|
| Numerical/Arithmetic Reasoning | Solve numeric problems under time pressure | Engineering, CS, Economics, Accounting |
| Spatial Reasoning | Mentally rotate shapes, understand 2D/3D | Architecture, Engineering, Design |
| Verbal Reasoning | Analogies, vocabulary in context | Law, Journalism, Teaching, Management |
| Logical/Abstract Reasoning | Pattern completion, sequence identification | CS, Mathematics, Research |

**Note on mobile delivery of spatial questions:** Khuzzaim must ensure spatial reasoning questions render correctly on small screens. This requires careful SVG/image design — flag to Antigravity.

**Why timed:** Aptitude measures processing speed + raw ability, not knowledge recall. Time pressure is the discriminating condition.

**Belief questions (12 total):** After each dimension's 8 timed questions, ask 3 belief-oriented questions. Example for Numerical:
- "How confident are you that you could improve your mathematical ability with practice?"
- "When you find a maths problem difficult, do you believe it's because the topic is hard or because you lack ability?"
- "How often do you attempt maths challenges you are not sure you can solve?"

**Signal detected:**
- High aptitude + low belief → self-limiting student → ExplanationNode: "Your scores suggest more ability than you may believe."
- Low aptitude + high belief → overconfident → ExplanationNode: frames degree requirements honestly.

**Alternatives rejected:**
- Full DAT (8 dimensions, 2+ hours, proprietary, Western norms)
- Raven's Progressive Matrices (carries IQ test stigma, trained administration required)
- ASVAB (US military instrument, culturally inappropriate)

**Effort:** ~1 week total. Fazal writes 32 aptitude questions. Backend adds `aptitude` category (2 hours config). Khuzzaim adds Aptitude tab to existing assessment screen (~4 hours). Assessment infrastructure already exists.

---

### 6.4 CAAS-5-SF — Career Adapt-Abilities Scale (5-Factor Short Form)

**Decision:** CAAS-5-SF, 30 questions, 5 subscales. NOT the standard 4-factor CAAS-4.

**Why CAAS-5-SF not CAAS-4:** The 4-factor CAAS was validated across 13 countries predominantly Western and East Asian — Pakistan was not included. The Control subscale ("I make decisions on my own") assumes individual agency that may not reflect the Pakistani student's actual family-dominated situation. Research recommends a 5th dimension — **Cooperation** — for collectivistic cultures. CAAS-5-SF is the recommended adaptation. Viva answer: "We used CAAS-5-SF specifically because the Cooperation subscale is recommended for collectivistic cultural contexts such as Pakistan."

**Five subscales and system routing:**
| Subscale | System Routing |
|---|---|
| Concern (low) | ProfilerNode: exploratory mode, not directive |
| Control (low) | ProfilerNode: agency-affirming framing |
| Curiosity (low) | ProfilerNode: more structured guidance |
| Confidence (low) | ExplanationNode: softer framing, more encouragement |
| Cooperation (low) | ProfilerNode: explicitly addresses family negotiation |

**Alternatives rejected:**
- Career Maturity Inventory (Crites, 1978): older, CAAS is its modern successor
- Vocational Identity Scale (Holland): narrower, overlaps with CAAS Curiosity+Confidence
- CAAS-4: inadequate for collectivistic cultures

**Con — self-report inflation:** Students aware of "correct" answers (common in Pakistan) may inflate Control scores ("I decide my own path") even under family pressure. The Cooperation subscale partially addresses this — harder to fake. CAAS scores are used as routing signals, not permanent labels.

---

### 6.5 VNA — Vocational Needs Assessment (Original Instrument)

**Decision:** 9 questions covering 3 MIQ dimensions. Original questions written by Waqas/Fazal. NOT Super's WVI. NOT the full MIQ.

**Legal resolution:** Theory of Work Adjustment (Dawis & Lofquist, 1964) is public domain. MIQ is based on this theory — the 20 need dimensions are descriptive categories of real work conditions, not protectable IP. MIQ's CC BY-NC 4.0 license prohibits commercial use. Solution: write original questions grounded in the public domain TWA theory. Viva description: "18-item Vocational Needs Assessment grounded in the Theory of Work Adjustment, adapted for the Karachi educational and occupational context."

**NOTE:** Original plan was 18 questions (6 dimensions). Reduced to 9 questions (3 dimensions) because work values are most actionable for *degree choice* when they map to concrete, age-appropriate conditions. The 3 most degree-relevant dimensions:

| Dimension | Why Degree-Relevant |
|---|---|
| Social Status | Directly maps to Karachi prestige hierarchy — high value → high prestige degree |
| Independence | Structured vs entrepreneurial degree paths — concrete enough for 17-year-olds |
| Achievement | Effort-orientation — high value + low aptitude = motivation-ability mismatch |

**Deferred dimensions (document the gap):**
| Dimension | Priority | When to Add |
|---|---|---|
| Security | **Priority 1** — strongest Karachi signal. Families push Medicine/Engineering for security. | When job recommendation features added |
| Altruism | Priority 2 — differentiates within Social RIASEC | With EQ-i Youth in Sprint 4 |
| Compensation | Priority 3 — salary expectations, more job than degree relevant | Post-FYP |

**Why NOT Super's WVI:** Requires licensing for commercial use. Values are abstract for 17-year-olds without work experience. MIQ's concrete conditions are more answerable at this age.
**Why NOT full MIQ:** CC BY-NC license prohibits commercial use. 14 of 20 dimensions require work experience to answer meaningfully.

---

### 6.6 Hybrid CDDQ — Career Decision-Making Difficulties (8 Questions, 2 Dimensions)

**Decision:** IN. Best effort-to-value ratio in the entire stack.

**What CAAS covers and what it does NOT:**
- CAAS covers: Lack of Readiness/motivation (Concern subscale), Lack of Information About Self (Curiosity subscale)
- CAAS does NOT cover: Lack of Information About Occupations, External Conflicts

**8 questions kept (2 dimensions × 4 items):**

Lack of Information About Occupations:
1. "I don't know enough about what people in different fields actually do day to day"
2. "I am unsure what skills are needed for careers I am considering"
3. "I don't know how to find out more about careers that interest me"
4. "I am not sure which educational path leads to which career"

External Conflicts:
5. "My family has strong views about what career I should choose"
6. "I feel pressure to choose a career that others expect of me"
7. "My preferences differ from what important people in my life think I should do"
8. "I am worried about disappointing someone if I choose a particular path"

**Node routing:** Information gap → ExplanationNode emphasises `field_reality_notes`; External conflict → ProfilerNode shifts to agency-affirming mode.

---

### 6.7 Hybrid Big Five — Conscientiousness + Neuroticism (10 Questions)

**Decision:** 10 questions. Conscientiousness (6) + Neuroticism (4). NOT the full Big Five.

**Why only these two dimensions:**

| Trait | CAAS Coverage | CAAS Coverage Quality | System Verdict |
|---|---|---|---|
| Openness | ~40% via Curiosity | Moderate — acceptable | Dropped |
| Conscientiousness | ~15% via Control | Weak — CAAS Control ≠ academic persistence | **Kept — 6 questions** |
| Extraversion | ~30% via Cooperation | Moderate — acceptable | Dropped |
| Agreeableness | ~25% via Cooperation | Weak but system-irrelevant | Dropped |
| Neuroticism | ~12-20% via Confidence | Very weak — CAAS Confidence ≠ emotional instability | **Kept — 4 questions** |

**Why Conscientiousness:** Strongest Big Five predictor of academic performance (meta-analytic r=0.24 with GPA). CAAS Control asks "will I follow career planning tasks" — different from "will I persist through difficult coursework." System use: ExplanationNode framing for high-demand programmes ("This 5-year MBBS requires sustained effort...").

**Why Neuroticism (reinstated after initial drop):** CAAS Confidence covers only ~12-20% of Neuroticism variance. Neuroticism predicts degree persistence in high-pressure programmes (MBBS, Law) independently of career self-efficacy. A student can believe they can solve career problems (high CAAS Confidence) while being emotionally reactive to academic pressure (high Neuroticism). 4 questions is low cost for meaningful signal.

**Why Openness dropped:** CAAS Curiosity covers exploration-readiness at ~40% quality. Residual Openness (aesthetic sensitivity, abstract thinking) doesn't map to actionable degree routing decisions.
**Why Extraversion dropped:** CAAS Cooperation + Social RIASEC covers the interpersonal dimension adequately.
**Why Agreeableness dropped:** Predicts workplace harmony, not academic field suitability. No clear routing use.

**MBTI — Explicitly Rejected:**
- National Academy of Sciences (1991): "not sufficient, well-designed research to justify MBTI in career counselling"
- 2024 large-scale study: Big Five 2× more accurate, adding MBTI to Big Five provides ~zero incremental value
- MBTI forces binary categories — loses ~38% accuracy vs continuous Big Five
**Viva answer ready:** "MBTI was considered and explicitly rejected."

---

### 6.8 EQ-i Youth (60 Questions) — DEFERRED

**Decision:** Deferred to Sprint 4. Gap documented.

**Unique value:** Detects students who will struggle in high-EQ fields (Medicine, Law, Teaching, Counselling) despite strong Social RIASEC scores. Two students with identical Social RIASEC + identical marks — one with high empathy/emotional regulation, one without — have genuinely different prognoses for Medicine.

**Why deferred:** Current degree pool has limited Social-RIASEC degrees where EQ differentiation matters most. FilterNode already hard-filters Medicine on academic merit. At 60 questions (even reduced to ~42-45 after overlap removal), burden-to-value ratio is too weak for this degree pool size.

**Overlap with existing stack:**
- EQ-i Interpersonal ↔ CAAS Cooperation: ~40% — when added, reduce EQ-i relationship items, keep empathy items
- EQ-i Stress Management ↔ Big Five Neuroticism: ~35% — reduce stress tolerance items, keep flexibility + optimism
- EQ-i Self-Perception ↔ CAAS Confidence: ~25% — small enough, both can coexist

**Trigger for re-inclusion:** (a) degree pool expands significantly into Social-RIASEC degrees (Medicine, Law, Counselling), OR (b) user feedback shows Social-RIASEC students have disproportionate recommendation mismatch.

---

### 6.9 Locus of Control — DEFERRED

**Decision:** Deferred post-FYP. CAAS-5-SF Control + Cooperation subscales cover ~70% of what a standalone Locus of Control instrument would measure. The Cooperation subscale specifically captures the family-authority dynamic that Rotter's original scale misses. 10 additional questions for ~30% more precision is not justified.

---

### 6.10 Overlap Resolution Rule

**[FINAL] Rule for handling instrument overlaps:**
- If Instrument A covers 40-50% of construct X and Instrument B covers 40-50% of the same construct but the questions feel distinct (different facet, different framing) → keep both, rephrase to maximise distinction
- If both cover 80%+ of the same construct with similar framing → keep the better question (higher factor loading evidence), drop the weaker
- The test is NOT percentage overlap alone — it is whether the student's answer to one genuinely tells you something different from their answer to the other

**CAAS is NOT the baseline for overlap calculation.** All instruments are compared against all others in both directions. If a Big Five question measures a construct better than its CAAS equivalent, the Big Five question is kept and the CAAS equivalent is dropped, even if CAAS is the "primary" instrument.

---

### 6.11 UCAB — Not Built

**Decision:** Do not build UCAB (Unified Multi-Construct Assessment Bank) as a technical system.

**What UCAB would do:** Tag every question to one primary construct, identify cross-instrument overlaps, remove overlapping questions from student-facing bank, use all questions for scoring.

**Why not needed:** With the scoped 7-instrument stack (237 total questions), remaining overlaps are small enough that judgment-based question curation handles them during question writing. If a Conscientiousness item and a CAAS Control item are asking nearly the same thing in similar words, rewrite one to target a more distinct aspect. Hours of curation vs weeks of engineering.

**Is UCAB an algorithm?** Technically yes (defined procedure, inputs, outputs) but weakly — it is a data engineering methodology, not a novel computational algorithm. Not worth viva time at this stage.

**Post-FYP:** Build UCAB when the question bank exceeds 400 items and manual curation becomes impractical. Add IRT calibration data from real users at that point.

---

### 6.12 Final Assessment Stack — Complete and Locked

| Module | Questions | Unique Contribution | Status |
|---|---|---|---|
| RIASEC (existing) | 60 | Interest profile across 6 types | **In — core** |
| KCIS (24 sub-scales × 4) | 96 | Granularity within types for Karachi degrees | **In** |
| Aptitude (8/dim) + Belief (3/dim) | 44 | Raw cognitive ability + domain self-efficacy | **In** |
| CAAS-5-SF | 30 | System behaviour adaptation per student | **In** |
| VNA (3 dimensions × 3) | 9 | Social Status + Independence + Achievement | **In** |
| Hybrid CDDQ | 8 | Information gap + External conflict routing | **In** |
| Hybrid Big Five (C + N) | 10 | Academic persistence + Stress vulnerability | **In** |
| Subject capability MCQs (existing) | varies | Subject knowledge per board syllabus — separate from aptitude | **In — unchanged** |
| EQ-i Youth | 60 | High-EQ field differentiation | **Deferred Sprint 4** |
| Locus of Control | 10 | Attribution style | **Deferred post-FYP** |
| Self-efficacy (standalone) | — | Covered by Aptitude Belief questions + CAAS Confidence | **Not built** |
| UCAB | — | Overlap management | **Not built** |
| MBTI | — | Rejected — no scientific validity advantage | **Rejected** |
| Super's WVI | — | Commercial licensing, age-inappropriate | **Rejected** |
| Full MIQ | — | CC BY-NC license prohibits commercial use | **Rejected** |
| Full CDDQ | — | Most dimensions covered by CAAS | **Rejected** |
| Full Big Five | — | 3 traits covered by CAAS adequately | **Rejected** |

**Total student-facing questions: 257**
*(60 + 96 + 44 + 30 + 9 + 8 + 10 — subject capability MCQs excluded, counted separately)*

---

### 6.13 Subject-Specific Capability Questions — Confirmed Present and Unchanged

**Question raised:** With the introduction of the aptitude test and all new instruments, are the subject-specific capability MCQs (physics, maths, chemistry, biology, etc.) still in the system?

**Answer: Yes. Completely unchanged. Nothing was removed.**

The subject capability MCQs and the aptitude test measure two entirely different things and are both needed:

| Assessment | What It Tests | Where It Goes |
|---|---|---|
| Subject capability MCQs (existing) | Subject knowledge — what the student has been taught (e.g. FSc Physics syllabus) | `capability_scores` dict in student profile e.g. `{"physics": 72, "math": 65}` |
| Aptitude test (new) | Raw cognitive ability — what the student can do regardless of education (e.g. spatial reasoning regardless of whether geometry was taught) | `aptitude_scores` dict e.g. `{"numerical": 78, "spatial": 55}` |

Both dicts feed into the system independently. ScoringNode uses capability_scores for the capability blend (grade correction). FilterNode uses aptitude_scores for `required_capability` matching. They are parallel inputs, not replacements for each other.

**The student experiences them as separate tabs in the same assessment screen** — the existing subject tabs are untouched, the Aptitude tab is added as a new tab alongside them.

---

### 6.14 Assessment Tier Grouping

**Context:** 249 questions across 7 instruments raises a valid student exhaustion concern. The tiering system addresses this by ensuring the system works at partial completion and students are never hard-blocked.

---

#### Tier 1 — Absolute Required (system cannot function meaningfully without these)

| Assessment | Questions | Why Non-Negotiable |
|---|---|---|
| Marks Input | ~5 min form | FilterNode requires marks for aggregate, merit cutoff, capability blend |
| RIASEC | 60 | Entire recommendation engine depends on this — remove it and there is nothing to match |
| Subject Capability MCQs | varies | `required_capability` matching and capability blend both need this |
| Aptitude (timed only, no belief questions) | 32 | New `required_capability` matching in FilterNode needs aptitude_scores |

**Total Tier 1: ~92+ questions + marks form.**
A student who completes only Tier 1 still receives a working recommendation. The system is fully functional — just less personalised.

**What each node can do on Tier 1 only:**

| Node | Tier 1 Only — Behaviour |
|---|---|
| FilterNode | ✅ Fully functional. Has marks + aptitude for all hard constraints |
| ScoringNode | ✅ Functional. Has RIASEC for 3D match, aptitude_scores, FutureValue |
| ProfilerNode | ⚠️ Fires more aggressively in chat. caas_scores, vna_scores missing. Compensates by asking conversationally what assessments would have measured. Slower and less reliable than structured assessment. |
| ExplanationNode | ⚠️ confidence_level computes as "low" or "moderate". Framing is cautious, less personalised. |
| AnswerNode | ✅ Unaffected. Generates responses regardless of profile completeness. |

The system degrades gracefully — it does not fail. ProfilerNode compensates by conversational extraction of what Tier 2 would have provided structurally. This is exactly what a real counsellor does with limited intake information.

---

#### Tier 2 — Important (meaningfully improves guidance — system is weaker without these)

| Assessment | Questions | What Is Lost Without It |
|---|---|---|
| KCIS | 88 | Degree discrimination within RIASEC types is lost. CS and Biomedical both score identically as "Investigative." |
| CAAS-5-SF | 30 | ProfilerNode cannot adapt strategy per student. Family pressure goes undetected. Every student gets the same counsellor behaviour. |
| Hybrid CDDQ | 8 | Information gap and external conflict routing never fires. |
| Aptitude Belief questions | 12 | Self-limiting and overconfident student detection never fires. |

**Total Tier 2: ~138 questions.** A Tier 1 + Tier 2 student receives full counsellor adaptation and degree discrimination. This is the recommended minimum for a complete, useful profile.

---

#### Tier 3 — Improves Accuracy (system works without these, but is less nuanced)

| Assessment | Questions | What Is Lost Without It |
|---|---|---|
| Hybrid Big Five (C + N) | 10 | ExplanationNode cannot flag low academic persistence or stress vulnerability for demanding degrees |
| VNA | 9 | Prestige alignment and independence signals absent — inferred from CAAS Cooperation instead of measured directly |

**Total Tier 3: ~19 questions.** These are genuine enhancements. The system produces defensible recommendations without them.

---

#### Tier Framing for Students — NEVER Label as Required/Optional

Do not present tiers to students as "required vs optional" — that causes Tier 2/3 dropout. Instead:

- **Tier 1** is the **onboarding gate** — student cannot reach chat without completing it. This is the current flow (marks + RIASEC are already gated). Aptitude and subject MCQs join this gate.
- **Tier 2** is presented as **"Complete Your Profile"** — shown as an incompleteness indicator in the Profile Dashboard. Format:
  ```
  Your Profile: 38% Complete

  ✅ Academic Marks
  ✅ RIASEC Interest Profile
  ✅ Aptitude Assessment
  ✅ Subject Capability Assessment

  ⬜ Deep Interest Profile (KCIS)        — Unlocks precise degree matching
  ⬜ Career Readiness Assessment (CAAS)  — Helps the counsellor adapt to you
  ⬜ Decision Style Assessment            — Helps identify what's holding you back
  ```
- **Tier 3** is presented as **"Enhance Your Profile"** — shown after Tier 2. Small progress increment.

This framing converts tiers from a student-visible gate into an engagement mechanism.

---

#### EQ-i Youth Tier Placement

EQ-i Youth (60 questions) is deferred to Sprint 4. When reinstated, it joins **Tier 2** — specifically for students whose top RIASEC types include Social as a primary or secondary type. The reinstatement trigger: when Social-RIASEC degrees constitute more than 30% of the active recommendation pool, OR when user feedback shows Social-RIASEC students have disproportionate recommendation mismatch.

Viva defense for deferral: "EQ measurement is architecturally supported. It is deferred pending degree pool expansion into Social-RIASEC fields where it provides the most differentiation value."

---

## 7. KARACHI LOCAL CONTEXT — ALL 13 DIMENSIONS

### Dimension 1: The Prestige Hierarchy
**Problem:** `social_acceptability_tier` EXISTS in affinity_matrix but UNUSED.
**[FINAL]** Activate in ExplanationNode. 3D spherical model encodes prestige mathematically.
Hierarchy: MBBS > FCPS > CS/Software > Electrical/Mechanical Engineering > Business/Finance > Law > Social Sciences > Arts.

### Dimension 2: Doctor/Engineer Family Dynamic
Research: "Pakistani students face parental pressure, over-emphasis on medicine and engineering, imposed decisions. Collectivistic culture means familial influences should be incorporated."

**[FINAL] Family context collected via Step 4 Preferences screen — NOT conversational ProfilerNode extraction.**

Background: ProfilerNode was previously pinging aggressively for budget, transport, and zone data, which is why Step 4 (Preferences screen) was added. `PROFILER_REQUIRED_FIELDS = []` was set empty as a result. The same principle applies to family context — collecting it via a structured onboarding screen is always preferable to ProfilerNode asking for it conversationally, which wastes LLM budget and is less reliable.

**Step 4 Preferences screen expansion (Khuzzaim adds two fields):**
```
Existing fields (unchanged):
  budget_per_semester, transport_willing, home_zone, career_goal

New fields added:
  family_career_field: dropdown
    Medicine / Engineering / Business / Education /
    Law / Computing / Government-Civil Service /
    Arts & Media / Other / Not applicable

  family_career_expectation: single select (radio)
    "My family expects me to follow a specific field"
    "My family has general preferences but I have freedom"
    "My family is fully open to my choice"
```

**Backend changes (Waqas):**
- `POST /profile/preferences` endpoint accepts two new fields
- Both stored in `family_context` JSONB field in student profile (already in migration plan)
- `PROFILER_REQUIRED_FIELDS` remains empty — ProfilerNode reads `family_context` from state, does not ask for it

**The one remaining conversational extraction — `social_pressure_field`:**
The specific degree field the family is pushing (e.g. "MBBS only" vs "engineering broadly") is too nuanced for a dropdown. ProfilerNode asks exactly ONE targeted question, but ONLY when `family_career_expectation = "My family expects me to follow a specific field"`. It fires once and stores the answer. This is not aggressive pinging — it is one contextual follow-up with a clear trigger condition.

**ExplanationNode framing when family_career_field = "Medicine" + expectation = "specific":**
"Your family background in medicine provides real advantages — mentorship, clinical exposure, networks. The question is whether your RIASEC profile supports a medical path. Currently your profile shows [X]."

### Dimension 3: AI Displacement (0-100 Score)
**[FINAL]** Use AI Resistance Score (ARS) 0-100 with four sub-dimension components. NOT a 3-category tag — continuous scale is more accurate and explainable. See Section 5.2 Gap 1.

### Dimension 4: Gender-Specific Constraints
**Principle:** Do NOT encode gender stereotypes. Encode *social barrier awareness* instead.
**[FINAL]** ProfilerNode extraction: "Are there any fields or campus locations your family considers unsuitable?" Surfaces the constraint without the system encoding the bias. Student retains agency.

### Dimension 5: Economic Class and Opportunity Cost
**Problem:** `budget_per_semester` captures fee but not opportunity cost (student expected to start working).
**[FINAL]** ProfilerNode soft question: "Does your family depend on you to start working soon after school?" If yes: flag degrees with strong part-time income potential, contextualise longer academic programmes.

### Dimension 6: Employer Perception of University Brand
**Problem:** CS from NED vs CS from a lesser-known private university has very different market value.
**[FINAL]** Fazal adds `employer_perception_tier` to universities.json: "tier_1", "tier_2", "tier_3". ExplanationNode uses in degree narrative.

### Dimension 7: Religious and Cultural Field Restrictions
**Principle:** System NEVER blocks fields on cultural grounds. FRAMES them.
**[FINAL]** `cultural_notes` field per degree in affinity_matrix. ExplanationNode incorporates when relevant.

### Dimension 8: Peer and Social Media Influence
"Everyone is doing CS" inflates CS interest artificially.
**[FINAL]** ProfilerNode extraction: "Is there a field you are drawn to because of friends or social media?" Triggers deeper mismatch investigation if confirmed.

### Dimension 9: School Type and Academic Ethos
Research: "High SES schools develop pupils for academic university careers; school type powerfully influences post-16 choices."
**[FINAL]** School type (O-level private, Matric government, Matric private) modulates ProfilerNode information density and ExplanationNode framing.

### Dimension 10: The Medical/Engineering Funnel Reality
41,000 students appear in medical entry tests; 5,000 get admission. 70,000+ in engineering; 7,200 admitted.
**[FINAL]** This is the system's strongest Karachi-specific value proposition: FilterNode merit cutoff enforcement means students see what is actually achievable. **State this explicitly at the viva.**

### Dimension 11: Remittance and Gulf Career Paths
Many families value degrees opening Gulf (UAE, Saudi, Qatar) paths.
**[FINAL]** Fazal adds `gulf_demand_tier` to lag_model: "high", "medium", "low". ExplanationNode: "This field has strong Gulf market demand, offering additional career pathways."

### Dimension 12: Entry Test Specificity
ECAT, MDCAT, NED entry test — which test is required dramatically restricts realistic options.
**[FINAL]** ProfilerNode soft question: "Have you done entry test preparation? How are your practice test scores?" Flag when entry test difficulty tier > student readiness.

### Dimension 13: Evening vs Morning Programme Reality
Evening programmes have lower merit cutoffs but carry social stigma in many families.
**[FINAL]** ExplanationNode notes when recommended scenario is evening-shift. `shift` field already in universities.json — use it.

---

## 8. MACHINE LEARNING

### 8.1 Why ML Is Not Used Now

**Formal framing:** The problem is a **Constraint Satisfaction Problem (CSP) with multi-objective scoring over a variable feasible set.**

- Hard constraints: merit cutoffs (binary), budget (hard cap)
- Soft constraints: family preferences, location, social acceptability
- Multi-objective: maximise match AND future value AND satisfy constraints
- Variable constraint space per student: a model cannot learn a uniform mapping because which constraints are active differs per student

**Without outcome labels, ML produces:**
- K-Means: mathematically real clusters, semantically empty without "cluster 3 = Engineering success"
- Supervised classification: predicts what students in Pakistan tend to choose (Medicine/Engineering due to cultural bias) — reproduces biases, not guidance

Research confirms: ML systems achieving 92%+ career prediction accuracy use datasets of 3000+ labelled entries. Karachi universities do not publish this data.

**[FINAL] Viva answer:** "We deliberately avoided ML approaches requiring training data we don't have. Adding unsupervised clustering without validated outcome labels would be ML theatre, not ML utility. Our architecture is designed to collect the user data enabling ML post-launch."

### 8.2 ML Infrastructure — Build Now (2 Hours)

**[FINAL]** Build feedback infrastructure now so post-FYP ML has data to train on:
```sql
CREATE TABLE user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    recommendation_run_id UUID REFERENCES recommendations(id),
    feedback_type TEXT CHECK (feedback_type IN ('1yr', '5yr')),
    feedback_date TIMESTAMPTZ DEFAULT NOW(),
    outcome_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```
Add `POST /api/v1/profile/feedback` endpoint. No frontend needed yet.

**1-year feedback:** Did student accept the recommendation? Which degree did they choose? Initial satisfaction? Reveals recommendation acceptance and short-term directional validity.
**5-year feedback:** Did student graduate? Are they employed in their field? Satisfaction? Ground truth for career guidance correctness.

**When ML becomes viable post-FYP:**
- 500+ users with 1-year feedback → simple collaborative filter
- 1000+ users with 5-year feedback → gradient boosted satisfaction predictor

### 8.3 The Output-vs-Output Comparison (from previous chat)
Once data is collected, comparing "LLM recommended CS" vs "student chose Medicine and is now unhappy" creates a labelled example. After ~1000 such pairs, train a classifier predicting "outcome satisfaction probability" per degree recommendation. This is the target ML product. The collection infrastructure starts now.

---

## 9. OPEN SOURCE LLMS VS GEMINI API

### 9.1 Why Gemini API Is Correct for Now

1. **No GPU on Render** — Render doesn't provide GPU instances. 7B+ models require 16GB+ VRAM
2. **Free tier economics** — Gemini: 15 RPM, 1M tokens/day, $0. Self-hosting GPU cloud: $5-20/month minimum
3. **Quality for use case** — LLM generates *explanations*, not decisions. Open-ended explanation is where API models retain advantage over quantized small models
4. **LLM doesn't pick degrees** — algorithms do. This means lower LLM quality is partially acceptable

### 9.2 GTX 1650 4GB — Local Feasibility

Can run: TinyLlama 1.1B (Q5_K_M), Phi-3.5 Mini 3.8B (Q3_K_M, pushes limits).
Cannot run reliably: Any 7B+ model.
Thermal: 85°C+ under sustained inference, thermal throttling degrades speed.

**Verdict:** Suitable for local development/testing only. Not for student-facing production.

### 9.3 Hosting Alternatives (Not Render)

| Platform | Best For | Cost |
|---|---|---|
| **Together AI** | API-based serving, OpenAI-compatible | $0.0002-$0.001/1K tokens |
| **RunPod** | Custom Docker, serverless, RTX 4090 | ~$0.35/hr, per-second billing |
| **Vast.ai** | Cheapest, least reliable, for training | 40-70% cheaper than RunPod |

**Recommended post-FYP path:** Together AI + Qwen3 8B (strong multilingual, good Urdu). One-line switch from Gemini (Together AI uses OpenAI-compatible API).

**Engineering effort to switch:** 4-6 hours (change 3 node files + config.py). Fine-tuning data collection is the bottleneck (weeks), not the engineering.

### 9.4 Additional Reasons for Open-Source (Beyond Urdu + Privacy)
- Karachi-specific fine-tuning on Pakistani counselling conversations
- Context injection reliability (control temperature, top-p, repetition penalty directly)
- Offline operation — Gemini API down = system fails; self-hosted degrades gracefully
- Rate limit elimination — Task 3 (429 retry logic) disappears entirely
- Long-term cost at scale (50,000 requests/month, Together AI cheaper than Gemini Pro)

**[FINAL]** Keep Gemini for viva. Transition to Together AI + Qwen3 8B in Sprint 4 (4-6 hours). Fine-tune post-FYP when counselling conversation data is available.

---

## 10. MASTER SEQUENCING PLAN

### 10.1 Correct Dependency Order

Four violations in the original sequencing that are now resolved:

1. **Schema Bootstrap Problem:** Aptitude key names (numerical, spatial, verbal, logical) must be agreed BEFORE Fazal writes `required_capability` profiles using those keys. Phase 0 produces a schema contract that everyone reads.

2. **ProfilerNode Before ScoringNode:** ScoringNode's 3D formula reads `prestige_preference` which comes from ProfilerNode's extraction schema. ProfilerNode must be updated before ScoringNode is revised.

3. **FilterNode Before ScoringNode:** ScoringNode reads `capability_mismatch_flag` set by FilterNode. FilterNode additions must be implemented before ScoringNode reads them.

4. **DB Migrations Missing:** Every new profile field (aptitude_scores, caas_scores, family_context) needs an Alembic migration deployed before any node writes to it.

### 10.2 Independent Node Changes

These changes can be done during Phase 2 (parallel with data work) OR in Phase 4 (with all other node changes). Either is acceptable. Choose based on Waqas's available time during Phase 2.

| Change | Why Independent | Allowed Phases |
|---|---|---|
| Prediger 2D projection in ScoringNode | Pure math on existing R,I,A,S,E,C scores. No new keys. No data dependencies. | Phase 2 OR Phase 4 |
| Differentiation + Consistency scoring | Same — reads existing RIASEC scores, computes range and adjacency | Phase 2 OR Phase 4 |
| ExplanationNode null guard | Prompt engineering change. No new fields read. Works regardless of data present. | Phase 2 OR Phase 4 |
| Slope calculation script for lag_model | Utility script that computes from data, not a node change | Phase 2 OR Phase 4 |

All other node changes must wait until Phase 4 (schema stable, migrations deployed, data files complete).

### 10.3 Corrected Sequence

```
Phase 0 — Schema Contract (Waqas, 1-2 days)
│  Define ALL new key names:
│    aptitude keys: ["numerical", "spatial", "verbal", "logical"]
│    caas keys: ["concern", "control", "curiosity", "confidence", "cooperation"]
│    vna keys: ["social_status", "independence", "achievement"]
│    capability_mismatch_flag structure
│    prestige_preference field name
│    family_context field structure
│  Output: schema_contract.md committed to repo
│  EVERYONE reads this before writing any JSON or code
│
Phase 0b — DB Migrations (Waqas, 0.5 days)
│  Alembic migrations for: aptitude_scores (jsonb), caas_scores (jsonb),
│  family_context (jsonb), vna_scores (jsonb), prestige_preference (float)
│  Deploy to Supabase BEFORE any node touches these fields
│
Phase 0c — Marks Reordering + Step 4 Expansion (Waqas + Khuzzaim, 1.5 days)
│  Move marks input to FIRST position in onboarding
│  Add warning/preparation screen before assessments commence
│  Decouple marks from test retake flow
│  Step 4 Preferences screen: add family_career_field dropdown +
│    family_career_expectation radio button
│  POST /profile/preferences: accept two new fields
│  family_context JSONB field: confirm migration covers both new fields
│  [Can run in parallel with Phase 0 / 0b]
│
┌─────────────────────────────────────────────┐
│  Phase 1A and 1B run in parallel after Phase 0│
└─────────────────────────────────────────────┘
│
Phase 1A — Data Files (Fazal, ~2 weeks)
│  affinity_matrix.json:
│    3D coordinates (people_things, ideas_data, prestige_tier)
│    required_capability per field (uses Phase 0 key names)
│    KCIS sub-scale mapping per degree
│    social_acceptability_tier (already exists — ensure populated)
│  lag_model.json:
│    monthly_postings_history arrays (for slope calculation)
│    ai_displacement block (ARS 0-100, 4 components)
│    field_reality_notes per field
│    data_status block per field
│    gulf_demand_tier per field
│  universities.json:
│    employer_perception_tier per university
│    cutoff_year per degree
│
Phase 1B — Assessment Questions (Fazal, ~2 weeks, parallel with 1A)
│  assessment_questions.json:
│    40 KCIS questions (24 sub-scales × ~2 questions — minimum viable)
│    OR 96 KCIS questions (24 sub-scales × 4 — full) — Fazal decides pace
│    32 aptitude questions (4 dimensions × 8, timed)
│    12 belief questions (4 dimensions × 3)
│    30 CAAS-5-SF questions (5 subscales × 6)
│    9 VNA questions (3 dimensions × 3)
│    8 hybrid CDDQ questions
│    10 hybrid Big Five questions (C × 6 + N × 4)
│  All questions: English + Roman Urdu versions
│  [KCIS sub-scale reference: Karachi_Degree_List_KCIS_Reference.md]
│
Phase 1C — Frontend Assessment Screens (Khuzzaim, parallel)
│  Aptitude tab in existing assessment screen (timed per-question)
│  CAAS-5-SF screen (new onboarding screen)
│  VNA questions screen (new or appended to assessment)
│  Hybrid CDDQ + Big Five (can append to existing screens or new screen)
│  NOTE: check with Waqas on exact screen placement before building
│
Phase 2 — Node Updates (Waqas, ~1 week)
│  Priority order (must follow this sequence):
│  1. ProfilerNode: reads family_context from state (set by Step 4 — no extraction),
│     CAAS routing strategy selection,
│     social_pressure_field one-question trigger (fires only when family_career_expectation = "specific"),
│     incomplete-profile detection + agent message for Tier 2 completion,
│     locus_of_control_signal from CAAS-5-SF Control+Cooperation subscales
│  2. FilterNode: three-state eligibility, capability_mismatch_flag
│  3. ScoringNode: 3D match formula, interaction weighting,
│     reads capability_mismatch_flag from FilterNode,
│     reads prestige_preference from state (set by ProfilerNode)
│  4. ExplanationNode: null guard, confidence level,
│     activate social_acceptability_tier, ai_displacement framing,
│     gulf_demand framing, employer_perception context
│  [Independent changes can happen any time during Phase 2:]
│    Prediger 2D projection, differentiation scoring,
│    ExplanationNode null guard, slope calculation script
│
Phase 3 — Profile Summary Pipeline (Waqas, ~1 day)
│  POST /api/v1/profile/generate-summary endpoint
│  6 parallel LLM calls (one per assessment module)
│  1 synthesis LLM call
│  Store all outputs in student profile table
│  NOT part of LangGraph — separate FastAPI endpoint
│
Phase 4 — Feedback Infrastructure (Waqas, 2 hours, any time)
│  user_feedback Supabase table
│  POST /api/v1/profile/feedback endpoint
│  Truly independent — do this whenever there is a gap
```

---

## 11. DASHBOARD AND UX DECISIONS

### 11.1 Dual Dashboard Architecture

**Two separate data paths:**

```
Assessment Data (static profile):
  riasec_scores, aptitude_scores, caas_scores, vna_scores,
  cddq_signals, big_five_persistence, big_five_stress
  → Stored at assessment completion, READ-ONLY after
  → Profile Dashboard reads directly from student profile table
  → No nodes involved — pure data display

Pipeline Data (dynamic roadmap):
  FilterNode → ScoringNode → ExplanationNode → AnswerNode
  → Reads FROM student profile (including all assessment data)
  → Writes TO recommendation table (roadmap_snapshot)
  → Degree Dashboard reads from recommendation table
```

**Profile Dashboard — per-tab structure:**
- RIASEC + KCIS tab: hexagonal radar + 3D position + top sub-scales
- Aptitude + Belief tab: bar chart of 4 dimensions + belief gap visual
- CAAS-5 tab: radar of 5 subscales + lowest subscale interpretation
- Values tab: 3 VNA dimensions ranked + meaning for the student
- Decision Style tab: CDDQ signals + Conscientiousness + Neuroticism signals

### 11.2 LLM Profile Summary Pipeline

**Architecture:** 7 LLM calls total (6 parallel per-module + 1 synthesis). Separate from LangGraph. Triggered once at assessment completion. Stored statically. Only regenerates on retake.

**6 parallel module calls:**
a. RIASEC + KCIS → "Your Interest Profile" (300-400 words)
b. Aptitude + Belief → "Your Cognitive Strengths and Self-Perception"
c. CAAS-5-SF → "Your Career Readiness and Decision Style"
d. VNA → "What You Need From a Career Environment"
e. Hybrid CDDQ + Big Five → "Decision Barriers and Personality Signals"
f. Academic Marks → "Your Academic Standing and Subject Pattern"

**1 synthesis call:** Receives all 6 summaries + raw scores. Produces 600-800 word overall narrative + structured findings (convergent signals, divergent signals, core strengths, growth areas, environmental fit, reality check).

**Reality-hit framing built into prompts (not softened):**
```
RULE: If marks are below typical entry requirements for the student's stated
interest field, state this directly. Do not soften it. Frame as:
"Here is what your marks currently mean for your options, and here is what
would change if they improved by X." NEVER say "don't worry." Say what is
true and what is actionable.
```

**Why 6 parallel calls not 1:** Each module requires domain-specific interpretation context. One call with all modules produces a system prompt of 10,000+ tokens where the LLM loses coherence. Separate focused calls produce better per-module explanations.

### 11.3 Onboarding Flow Reordering

**[FINAL] New onboarding order:**
1. Marks input FIRST (with warning screen before assessments)
2. Warning screen: test types, approximate time, what each measures, preparation option
3. Assessments commence after marks submission
4. Retake flow: marks decoupled — student goes directly to test screen on retake

**Technical benefit:** Marks present in student profile from the start. No risk of pipeline running without marks data.

### 11.4 Back Button Logic

**[FINAL]** Standard psychometric validity practice:
- Within a test: free navigation between questions (question navigator stays as built)
- After test confirmation dialog: locked, no back navigation
- From complete screen: forward only
- Between test sections: once a section is confirmed, it is locked

**Why:** Allowing re-answering after seeing the full test introduces response bias — students adjust earlier answers based on where they think the test is going.

---

### 11.5 Assessment Session Structure Mapped to Tiers

The three-session structure maps directly onto the tier grouping. Sessions are not hard gates — the student can pause mid-session and resume via draft persistence (already implemented in flutter_secure_storage).

**Session 1 — Tier 1 (~45 minutes):**
Marks form + RIASEC quiz (60) + KCIS sub-groups (88) + Subject Capability MCQs.
RIASEC and KCIS are placed together because both measure interest — the student is already in "what do I like?" mode after RIASEC, so KCIS feels like a natural continuation rather than a new burden. KCIS must use collapsible sub-group navigation (by RIASEC type), not a flat 88-question list — this is critical for preventing fatigue.

**Session 2 — Tier 1 completion + Tier 2 start (~30 minutes):**
Aptitude (32 timed, interleaved with 12 belief questions) + CAAS-5-SF (30).
Aptitude questions are interleaved with belief questions per dimension: 8 timed Numerical → 3 belief → 8 timed Spatial → 3 belief → optional break offered → 8 timed Verbal → 3 belief → 8 timed Logical → 3 belief. The 3 belief questions per dimension serve as a micro-rest between timed blocks.
Note for Khuzzaim: spatial reasoning questions must render correctly on small screens — SVG/image design needs care for Samsung A6.

**Session 3 — Tier 2 completion + Tier 3 (~25 minutes):**
Hybrid CDDQ (8) + CAAS was in Session 2 so Tier 2 is complete after Session 2. Session 3 covers VNA (9) + Hybrid Big Five (10) = Tier 3. These are all Likert-scale, move quickly, no time pressure.

**Total: ~100 minutes across 3 sessions.** Each session is under 45 minutes. Research on career assessment completion rates shows 78%+ completion rates when each session is under 30 minutes with visible progress — the 45-minute Session 1 is the risk point. KCIS sub-group navigation is the main mitigation.

---

### 11.6 ProfilerNode Incomplete-Profile Detection

When ProfilerNode detects that Tier 2 assessments are missing from state AND the student has had more than 2 conversational turns, it inserts one structured message before continuing with counsellor questions.

**Detection logic:**
```python
TIER2_SIGNALS = {
    "caas_scores": {
        "missing_signal": "how ready you are to make career decisions",
        "assessment_name": "Career Readiness Assessment",
        "unlock": "I can better adapt my guidance to your specific situation"
    },
    "kcis_scores": {
        "missing_signal": "which specific areas within your interest types appeal most",
        "assessment_name": "Deep Interest Profile",
        "unlock": "I can distinguish between similar degrees much more precisely"
    },
    "vna_scores": {
        "missing_signal": "what you need from a career environment to feel satisfied",
        "assessment_name": "Values Assessment",
        "unlock": "I can factor in what matters most to you beyond interest and marks"
    }
}

missing = [k for k in TIER2_SIGNALS if not state.get(k)]
if missing and state["turn_count"] > 2 and not state.get("tier2_prompt_sent"):
    # Insert the incomplete-profile message once, set flag to not repeat
    state["tier2_prompt_sent"] = True
    # LLM generates message using TIER2_SIGNALS data
```

**The message the LLM generates (tone: transparent, not pushy):**
```
Before I give you my best guidance, I want to be transparent about something.

Right now I can see your marks and your RIASEC interest profile — which tells me
a lot. But I'm missing a few things that would genuinely change how I advise you:

- I don't know how ready you feel to make career decisions yet, or whether
  family expectations are playing a role in your thinking
- I don't know which specific areas within your interest types appeal most —
  for example, whether your Investigative interest leans toward mathematics
  or biology

These are not just nice-to-haves. Without them, my advice will be more generic
and less useful to your specific situation.

It takes about 25 minutes. Would you like to complete the remaining assessments
now, or shall I give you guidance based on what I have?
```

The student can say "give me guidance now" and the system proceeds with Tier 1 data only. The agent never blocks — it informs once and offers. This message fires **once per session** only — no repeat pinging.

**Why the agent message matters more than the Profile Dashboard indicator:**
The Profile Dashboard incompleteness indicator is passive — students may not look at it. The agent message is active — it appears in the flow the student is already engaged in. Contextual prompts within an active session produce significantly higher completion rates than passive dashboard indicators. The agent framing ("I need this to help you better") is more persuasive than a progress bar.

---

### 11.7 Step 4 Preferences Screen — Family Context Expansion

**Background:** ProfilerNode was previously pinging aggressively for budget, transport, and zone. Step 4 was added specifically to solve this. `PROFILER_REQUIRED_FIELDS = []` was set empty. The same principle applies to family career context — structured onboarding collection is always preferable to conversational extraction for known, stable fields.

**[FINAL] Two new fields added to Step 4 Preferences screen:**

```
family_career_field (dropdown):
  Options: Medicine / Engineering / Business / Education /
           Law / Computing / Government & Civil Service /
           Arts & Media / Other / Not applicable

family_career_expectation (radio, single select):
  "My family expects me to follow a specific field"
  "My family has general preferences but I have freedom"
  "My family is fully open to my choice"
```

**What this enables without any ProfilerNode pinging:**
- `family_career_field = "Medicine"` + `expectation = "specific"` → ProfilerNode routes to family-pressure counsellor strategy automatically
- `expectation = "fully open"` → ProfilerNode skips family negotiation strategy entirely, conserving LLM budget
- ExplanationNode receives family_context in state and frames recommendations accordingly

**The one remaining conversational extraction:**
`social_pressure_field` (the specific degree, e.g. "MBBS only" vs "engineering broadly") stays conversational because a dropdown cannot capture this nuance. ProfilerNode asks exactly ONE question, triggered ONLY when `family_career_expectation = "My family expects me to follow a specific field"`. It fires once per session, stores the answer, never repeats.

**Implementation changes:**

| Item | Change | Who |
|---|---|---|
| Step 4 Flutter screen | Add `family_career_field` dropdown + `family_career_expectation` radio | Khuzzaim |
| `POST /profile/preferences` endpoint | Accept two new fields in payload | Waqas |
| `family_context` JSONB field | Confirm Phase 0b migration includes both new fields | Waqas |
| ProfilerNode | Reads `family_context` from state — no extraction for these fields | Waqas |
| `social_pressure_field` | One question, triggered only when expectation = "specific" | Waqas (prompt) |

## 12. RESEARCH CITATIONS REQUIRED

The following decisions need research paper citations in the final defense documentation. Citations document to be produced as a separate file before June 15.

| Decision | Papers Needed |
|---|---|
| RIASEC as foundation | Holland (1959, 1997) — foundational theory |
| Prediger 2D projection | Prediger (1982) — People/Things, Ideas/Data axes |
| PGI 3D spherical model | Tracey & Rounds (1996, 2002) — prestige dimension |
| CAAS-5-SF for collectivistic cultures | CAAS cross-cultural research, Cooperation subscale validation |
| Big Five vs MBTI | National Academy of Sciences (1991), ClearerThinking (2024) |
| Conscientiousness + academic performance | Meta-analytic reviews, GPA prediction studies |
| ARS automation risk framework | Frey & Osborne (2013) — original automation probabilities |
| CDDQ — career decision barriers | Gati (1996) — CDDQ development and validation |
| RIASEC bipolarity assumption | Research confirming R-S opposition, hexagonal adjacency |
| Theory of Work Adjustment (VNA basis) | Dawis & Lofquist (1964) — foundational theory |
| Pakistan career decision making | Local studies on parental pressure, collectivistic factors |
| ML requires labelled outcome data | Studies showing 3000+ labelled examples needed for career ML |
| EQ and career satisfaction | EI meta-analyses showing incremental validity over personality |

---

## APPENDIX A — ALL DECISIONS SUMMARY

| Decision | Status | Section |
|---|---|---|
| RIASEC → 3D spherical model | **DO NOW (Phase 2)** | §6.1 |
| Differentiation + consistency scoring | **DO NOW — independent** | §1.2 |
| KCIS (24 sub-scales, 96 questions) | **DO NOW (Phase 1B)** | §6.2 |
| Aptitude + Belief (44 questions) | **DO NOW (Phase 1B)** | §6.3 |
| CAAS-5-SF (30 questions) | **DO NOW (Phase 1B)** | §6.4 |
| VNA original (9 questions, 3 dimensions) | **DO NOW (Phase 1B)** | §6.5 |
| Hybrid CDDQ (8 questions) | **DO NOW (Phase 1B)** | §6.6 |
| Hybrid Big Five — C + N (10 questions) | **DO NOW (Phase 1B)** | §6.7 |
| Subject capability MCQs | **Unchanged — already built** | §6.13 |
| Assessment tier grouping (Tier 1/2/3) | **DO NOW — governs all UX** | §6.14 |
| KCIS sub-group navigation (not flat list) | **DO NOW (Phase 1C)** | §6.14 |
| Aptitude timed + belief interleaved per dimension | **DO NOW (Phase 1C)** | §11.5 |
| Step 4: family_career_field + family_career_expectation | **DO NOW (Phase 0c)** | §11.7 |
| ProfilerNode reads family_context from state (no pinging) | **DO NOW (Phase 2)** | §11.7 |
| social_pressure_field: one question, triggered once only | **DO NOW (Phase 2)** | §11.7 |
| ProfilerNode incomplete-profile detection + agent message | **DO NOW (Phase 2)** | §11.6 |
| Profile Dashboard incompleteness indicator (38% framing) | **DO NOW (Phase 1C)** | §6.14 |
| ai_displacement block in lag_model | **DO NOW (Phase 1A)** | §5.2 |
| field_reality_notes in lag_model | **DO NOW (Phase 1A)** | §5.2 |
| Activate social_acceptability_tier | **DO NOW (Phase 2)** | §7 D1 |
| FilterNode three-state eligibility | **DO NOW (Phase 2)** | §4.1 |
| Aggregate formula validation script | **DO NOW (Phase 0)** | §4.1 |
| ExplanationNode null guard | **DO NOW — independent** | §4.4 |
| Confidence level computation | **DO NOW (Phase 2)** | §4.4 |
| Slope calculation script | **DO NOW — independent** | §1.2 |
| Rank percentile normalisation + penalties | **DO NOW (Phase 2)** | §4.3 |
| Feedback infrastructure (2 hours) | **DO NOW (any time)** | §8.2 |
| Profile Dashboard + LLM summary pipeline | **DO NOW (Phase 3)** | §11 |
| Marks input reordering + warning screen | **DO NOW (Phase 0c)** | §11.3 |
| employer_perception_tier in universities | **DO NOW (Phase 1A)** | §7 D6 |
| gulf_demand_tier in lag_model | **DO NOW (Phase 1A)** | §7 D11 |
| cutoff_year in universities | **DO NOW (Phase 1A)** | §7 D10 |
| Schema contract document | **MUST DO FIRST (Phase 0)** | §10.3 |
| DB Alembic migrations | **MUST DO BEFORE Phase 2** | §10.3 |
| EQ-i Youth — Tier 2 when Social-RIASEC >30% of pool | Sprint 4 | §6.8, §6.14 |
| LLM transition to Together AI + Qwen3 8B | Sprint 4 | §9.3 |
| Full aptitude test score calibration | Sprint 4 | §6.3 |
| Work Values Inventory (full) | Sprint 4 | — |
| Security + Altruism + Compensation (VNA) | Sprint 4 → Post-FYP | §6.5 |
| Big Five Openness, Extraversion, Agreeableness | Post-FYP | §6.7 |
| Locus of Control standalone | Post-FYP | §6.9 |
| UCAB algorithm | Post-FYP (when bank > 400 items) | §6.11 |
| lag_multiplier empirical calibration | Post-FYP | §4.3 |
| Collaborative filtering (ML) | Post-FYP (500+ users) | §8.3 |
| Admin dashboard (staleness monitoring) | Post-FYP | §7 |
| Chat history endpoint | Sprint 4 | handoff doc |
| LLM fine-tuning on Pakistan counselling data | Post-FYP | §9 |

---

## APPENDIX B — TEAM OWNERSHIP TABLE

| Owner | Item | Reference |
|---|---|---|
| **Waqas** | Schema contract document (Phase 0) | §10.3 |
| **Waqas** | Alembic DB migrations (Phase 0b) — confirm family_context includes family_career_field + family_career_expectation | §10.3, §11.7 |
| **Waqas** | Prediger 2D + differentiation in scoring_node.py | §6.1 |
| **Waqas** | 3D match formula in scoring_node.py | §6.1 |
| **Waqas** | FilterNode three-state eligibility | §4.1 |
| **Waqas** | FilterNode capability mismatch flag | §4.1 |
| **Waqas** | Aggregate formula validation script | §4.1 |
| **Waqas** | ScoringNode interaction weighting + revision | §4.2 |
| **Waqas** | ExplanationNode null guard | §4.4 |
| **Waqas** | ExplanationNode confidence level | §4.4 |
| **Waqas** | ProfilerNode: reads family_context from state (not extracted) | §11.7 |
| **Waqas** | ProfilerNode: social_pressure_field one-question trigger | §11.7 |
| **Waqas** | ProfilerNode: CAAS subscale routing logic | §6.4 |
| **Waqas** | ProfilerNode: incomplete-profile detection + agent message (once per session) | §11.6 |
| **Waqas** | POST /profile/preferences: accept family_career_field + family_career_expectation | §11.7 |
| **Waqas** | Slope calculation script (market_phase) | §1.2 |
| **Waqas** | FutureValue rank normalisation + coverage penalty | §4.3 |
| **Waqas** | Profile summary pipeline endpoint | §11.2 |
| **Waqas** | Feedback infrastructure (Supabase + endpoint) | §8.2 |
| **Fazal** | affinity_matrix: 3D coordinates per field | §6.1 |
| **Fazal** | affinity_matrix: required_capability per field | §4.1 |
| **Fazal** | affinity_matrix: KCIS sub-scale mapping | §6.2 |
| **Fazal** | affinity_matrix: social_acceptability_tier (ensure populated) | §7 D1 |
| **Fazal** | lag_model: monthly_postings_history arrays | §1.2 |
| **Fazal** | lag_model: ai_displacement block (ARS 0-100) | §5.2 |
| **Fazal** | lag_model: field_reality_notes per field | §5.2 |
| **Fazal** | lag_model: data_status block per field | §4.3 |
| **Fazal** | lag_model: gulf_demand_tier per field | §7 D11 |
| **Fazal** | universities.json: employer_perception_tier | §7 D6 |
| **Fazal** | universities.json: cutoff_year per degree | §7 D10 |
| **Fazal** | assessment_questions.json: 96 KCIS questions (24 sub-scales × 4) | §6.2 |
| **Fazal** | assessment_questions.json: 32 aptitude questions (timed) | §6.3 |
| **Fazal** | assessment_questions.json: 12 belief questions | §6.3 |
| **Fazal** | assessment_questions.json: 30 CAAS-5-SF questions | §6.4 |
| **Fazal** | assessment_questions.json: 9 VNA questions (original) | §6.5 |
| **Fazal** | assessment_questions.json: 8 hybrid CDDQ questions | §6.6 |
| **Fazal** | assessment_questions.json: 10 hybrid Big Five questions | §6.7 |
| **Fazal** | All questions: English + Roman Urdu versions | — |
| **Khuzzaim** | Flutter: Step 4 Preferences screen — add family_career_field + family_career_expectation | §11.7 |
| **Khuzzaim** | Flutter: Marks input moved to first position + warning screen | §11.3 |
| **Khuzzaim** | Flutter: Aptitude tab — timed delivery, interleaved with belief questions per dimension | §6.3, §11.5 |
| **Khuzzaim** | Flutter: KCIS sub-group navigation (collapsible by RIASEC type, NOT flat list) | §6.14, §11.5 |
| **Khuzzaim** | Flutter: Spatial reasoning question rendering on Samsung A6 (SVG/image care) | §6.3 |
| **Khuzzaim** | Flutter: CAAS-5-SF screen in onboarding | §6.4 |
| **Khuzzaim** | Flutter: VNA + hybrid CDDQ + Big Five screens | §6.5-6.7 |
| **Khuzzaim** | Flutter: Profile Dashboard — per-tab structure + incompleteness indicator (38% framing) | §11.1, §6.14 |
| **Khuzzaim** | Flutter: Degree Dashboard — unchanged | §11.1 |

---

*FYP Architecture Reference v2.1. Supersedes v1 and v2.0.*
*Last updated: May 2026 — added assessment tiers, Step 4 family context expansion,*
*ProfilerNode incomplete-profile detection, session-to-tier mapping, subject MCQ confirmation.*
*Next review: Before June 15 viva — update CLAUDE.md with all decisions from this document.*
