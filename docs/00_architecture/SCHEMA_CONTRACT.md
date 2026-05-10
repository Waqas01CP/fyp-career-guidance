# SCHEMA_CONTRACT.md
## FYP: AI-Assisted Academic Career Guidance System
## Phase 0 — Schema Contract
## Produced by: Architecture Chat v5
## Date: May 2026
## Status: LOCKED — read before writing any JSON or code in Phase 1+

---

## PURPOSE

This document defines every new key name, field name, and data structure
introduced by the tier-aware assessment system and related changes.

**Every team member reads this before writing any JSON or code.**
- Fazal: read before writing assessment_questions.json, affinity_matrix.json,
  lag_model.json, or universities.json additions
- Khuzzaim: read before building new assessment screens
- Waqas: read before writing Alembic migrations or node code

**Priority:** This document supersedes any field names mentioned in Reference v2.1
or POINT_2 v2.2 where they conflict. If in doubt, this document wins.

---

## SECTION 1 — NEW DATABASE FIELDS (Alembic Migration — Phase 0b)

Six new columns to add to the `student_profiles` table in Supabase during Phase 0b.
A seventh column (kcis_scores) is defined in Section 1.7 but runs in Phase 1C, not Phase 0b.
All new columns are JSONB or float to maintain the existing flexible schema pattern.

Waqas writes the Alembic migration for all six Phase 0b columns before any Phase 2 node work begins.

### 1.1 aptitude_scores — JSONB

```sql
ALTER TABLE student_profiles
ADD COLUMN aptitude_scores JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty dict until student completes aptitude assessment)
**Written by:** Assessment screen submission endpoint (profile.py)
**Read by:** ScoringNode (required_capability matching), ProfilerNode (belief gap detection)

**Exact key names — LOCKED:**
```python
aptitude_scores = {
    "numerical": float,   # 0.0 to 100.0 — arithmetic/numerical reasoning score
    "spatial":   float,   # 0.0 to 100.0 — spatial reasoning score
    "verbal":    float,   # 0.0 to 100.0 — verbal reasoning score
    "logical":   float,   # 0.0 to 100.0 — logical/abstract reasoning score
}
```

**Belief sub-scores (stored nested under each key):**
After each aptitude dimension, 3 belief questions are asked.
Belief scores are stored inside aptitude_scores as a nested dict:
```python
aptitude_scores = {
    "numerical": 72.0,
    "numerical_belief": 45.0,   # 0-100 belief score for numerical domain
    "spatial":   55.0,
    "spatial_belief": 80.0,
    "verbal":    88.0,
    "verbal_belief": 90.0,
    "logical":   91.0,
    "logical_belief": 60.0,
}
```

**Self-limiting detection:** `aptitude > belief + 25` → self-limiting student
**Overconfidence detection:** `belief > aptitude + 25` → overconfident student

---

### 1.2 caas_scores — JSONB

```sql
ALTER TABLE student_profiles
ADD COLUMN caas_scores JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty until student completes CAAS-5-SF)
**Written by:** Assessment screen submission endpoint (profile.py)
**Read by:** ProfilerNode (strategy selection, Tier 2 prompt routing)

**Exact key names — LOCKED (CAAS-5-SF, 5 subscales):**
```python
caas_scores = {
    "concern":     float,   # 1.0 to 5.0 — career concern/future awareness
    "control":     float,   # 1.0 to 5.0 — sense of control over career decisions
    "curiosity":   float,   # 1.0 to 5.0 — career exploration orientation
    "confidence":  float,   # 1.0 to 5.0 — career decision self-efficacy
    "cooperation": float,   # 1.0 to 5.0 — ability to work within family/relational networks
                            # (5th subscale — CAAS-5-SF, not in standard CAAS-4)
}
```

**Score interpretation:**
- `concern < 2.5` → ProfilerNode: exploration mode
- `cooperation < 2.5` + `family_career_expectation = "expects_specific_field"` → family negotiation strategy

---

### 1.3 vna_scores — JSONB

```sql
ALTER TABLE student_profiles
ADD COLUMN vna_scores JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty until student completes VNA)
**Written by:** Assessment screen submission endpoint (profile.py)
**Read by:** ProfilerNode (prestige_preference derivation), ScoringNode,
             ExplanationNode (values framing)

**Exact key names — LOCKED (6 dimensions: 3 active now, 3 deferred):**
```python
vna_scores = {
    # Active dimensions (implemented now):
    "social_status":  float,   # 0.0 to 100.0 — importance of career prestige
    "independence":   float,   # 0.0 to 100.0 — preference for autonomous vs structured paths
    "achievement":    float,   # 0.0 to 100.0 — effort-orientation and accomplishment drive

    # Deferred dimensions (Sprint 4 — keys reserved, not yet collected):
    # "security":      float,   # job stability preference
    # "altruism":      float,   # desire to help others through work
    # "compensation":  float,   # salary/financial priority
}
```

**Note:** Do not add deferred keys to the assessment questions yet.
Keys are documented here so future implementation uses the same names.

---

### 1.4 family_context — JSONB

```sql
ALTER TABLE student_profiles
ADD COLUMN family_context JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty until student completes Step 4 Preferences screen)
**Written by:** POST /profile/preferences endpoint (profile.py) — Step 4 screen
**Read by:** ProfilerNode (family-pressure strategy routing), ExplanationNode

**Exact key names — LOCKED:**
```python
family_context = {
    "family_career_field": str,
    # Collected via dropdown in Step 4 Preferences screen.
    # Allowed values (exactly as stored in DB):
    #   "medicine" | "engineering" | "business" | "education" |
    #   "law" | "computing" | "government_civil_service" |
    #   "arts_media" | "other" | "not_applicable"

    "family_career_expectation": str,
    # Collected via radio button in Step 4 Preferences screen.
    # Allowed values (exactly as stored in DB):
    #   "expects_specific_field" | "general_preferences" | "fully_open"

    "social_pressure_field": str | None,
    # Collected via ONE ProfilerNode conversational question.
    # Triggered ONLY when family_career_expectation == "expects_specific_field".
    # Free text — student's own words e.g. "MBBS only" or "engineering broadly".
    # None until ProfilerNode extracts it. Never repeatedly asked.
}
```

---

### 1.5 prestige_preference — Float

```sql
ALTER TABLE student_profiles
ADD COLUMN prestige_preference FLOAT NOT NULL DEFAULT 5.0;
```

**Python type:** `float`
**Default:** `5.0` (neutral — neither high nor low prestige priority)
**Range:** `0.0` (low prestige priority) to `10.0` (high prestige priority)
**Written by:** ProfilerNode (derived, not directly collected from student)
**Read by:** ScoringNode (3D match formula prestige axis)

**Derivation logic (ProfilerNode computes this):**
```python
def compute_prestige_preference(
    family_context: dict,
    vna_scores: dict,
) -> float:
    base = 5.0

    field = family_context.get("family_career_field", "not_applicable")
    expectation = family_context.get("family_career_expectation", "fully_open")
    social_status_score = vna_scores.get("social_status", 50.0)

    # High prestige signal from family field
    HIGH_PRESTIGE_FIELDS = {"medicine", "engineering", "law", "government_civil_service"}
    if field in HIGH_PRESTIGE_FIELDS:
        base += 2.0

    # Strong expectation amplifies prestige weight
    if expectation == "expects_specific_field":
        base += 2.0
    elif expectation == "general_preferences":
        base += 1.0

    # VNA social_status score contributes (normalised from 0-100 to 0-3 range)
    base += (social_status_score / 100.0) * 3.0

    return min(10.0, max(0.0, base))
```

---

### 1.6 misc_assessment_scores — JSONB

```sql
ALTER TABLE student_profiles
ADD COLUMN misc_assessment_scores JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty until student completes hybrid Big Five and hybrid CDDQ)
**Written by:** POST /profile/misc-assessment endpoint (profile.py)
**Read by:** ProfilerNode (conscientiousness for tier3_enriched strategy,
             external_conflict for family-pressure routing),
             ExplanationNode (neuroticism framing for high-pressure degrees,
             information_gap for field_reality_notes emphasis)

**Exact key names — LOCKED:**
```python
misc_assessment_scores = {
    # Hybrid Big Five (Conscientiousness + Neuroticism — 10 questions total):
    "conscientiousness": float,   # 0.0 to 100.0 — academic persistence signal
    "neuroticism":       float,   # 0.0 to 100.0 — stress vulnerability signal

    # Hybrid CDDQ (8 questions — 2 dimensions only):
    "information_gap":   float,   # 1.0 to 5.0 — Likert average, lack of occupational info
    "external_conflict": float,   # 1.0 to 5.0 — Likert average, family pressure signal
}
```

**Score interpretation:**
- `conscientiousness < 40.0` + high-workload degree (MBBS, Law, Engineering) →
  ProfilerNode raises this before recommendations
- `neuroticism > 70.0` + high-pressure degree → ExplanationNode adds stress framing
- `information_gap > 3.5` → ExplanationNode emphasises `field_reality_notes`
- `external_conflict > 3.5` → ProfilerNode shifts to agency-affirming mode

**Why one combined column instead of two separate columns:**
Hybrid Big Five (10 questions) and Hybrid CDDQ (8 questions) are small instruments
with 2 scores each. A single JSONB column with 4 keys is cleaner than two separate
columns with 2 keys each.

---

### 1.7 kcis_scores — JSONB (deferred — add when KCIS screen is built in Phase 1C)

```sql
-- Run this migration when KCIS assessment screen is complete in Phase 1C:
ALTER TABLE student_profiles
ADD COLUMN kcis_scores JSONB NOT NULL DEFAULT '{}';
```

**Python type:** `dict`
**Default:** `{}` (empty until student completes KCIS sub-scale assessment)
**Written by:** POST /profile/kcis endpoint (profile.py) — added in Phase 1C
**Read by:** ScoringNode (within-RIASEC-type degree discrimination),
             ProfilerNode (tier2_standard specific sub-field questioning)

Key names: all 23 sub-scale strings from Section 3. Values: float 0.0-100.0.

**Note:** This column is documented here but the migration runs in Phase 1C,
not Phase 0b. Do not include it in the Phase 0b Alembic migration.

---

## SECTION 2 — NEW AGENTSTATE FIELDS (state.py — Phase 2)

Nine new fields added to AgentState in `backend/app/agents/state.py`.
**Do not add these until the Alembic migrations in Section 1 are deployed.**

Waqas adds all 9 fields to state.py in Phase 2 node work.

```python
# These 8 fields are added after conflict_detected in AgentState:

aptitude_scores: dict
# Loaded from student_profiles.aptitude_scores at session start.
# Keys: "numerical", "spatial", "verbal", "logical",
#       "numerical_belief", "spatial_belief", "verbal_belief", "logical_belief"
# All float, 0.0-100.0. Empty dict {} if not yet assessed.

caas_scores: dict
# Loaded from student_profiles.caas_scores at session start.
# Keys: "concern", "control", "curiosity", "confidence", "cooperation"
# All float, 1.0-5.0 Likert average. Empty dict {} if not yet assessed.

kcis_scores: dict
# Loaded from student_profiles.kcis_scores at session start.
# Keys: sub-scale names from Section 3 below → float 0.0-100.0.
# Empty dict {} if not yet assessed.

vna_scores: dict
# Loaded from student_profiles.vna_scores at session start.
# Keys: "social_status", "independence", "achievement" → float 0.0-100.0.
# Empty dict {} if not yet assessed.

family_context: dict
# Loaded from student_profiles.family_context at session start.
# Keys: "family_career_field", "family_career_expectation",
#       "social_pressure_field"
# Empty dict {} if Step 4 not yet completed.

prestige_preference: float
# Loaded from student_profiles.prestige_preference at session start.
# Default 5.0. Updated by ProfilerNode when family_context and
# vna_scores are both available.

tier2_prompt_sent: bool
# Session-only — NOT persisted to DB. Reset to False each session.
# Set to True by ProfilerNode after sending the one-time
# Tier 2 completion message. Prevents repeat pinging.
# Default: False

turn_count: int
# Session-only — NOT persisted to DB. Reset to 0 each session.
# Incremented by SupervisorNode at start of each turn.
# ProfilerNode reads this — Tier 2 prompt fires only when turn_count > 2.
# Default: 0

misc_assessment_scores: dict
# Loaded from student_profiles.misc_assessment_scores at session start.
# Keys: "conscientiousness", "neuroticism" (Big Five hybrid — 10 questions)
#       "information_gap", "external_conflict" (CDDQ hybrid — 8 questions)
# All float. Empty dict {} if not yet assessed.
# ProfilerNode reads conscientiousness and external_conflict for routing.
# ExplanationNode reads neuroticism and information_gap for framing.
```

**IMPORTANT — session-only fields (do NOT add DB columns for these):**
`tier2_prompt_sent` and `turn_count` are NOT stored in `student_profiles`.
They live only in AgentState for the duration of the session.
They reset to defaults (`False` and `0`) at the start of every new session.

**Total AgentState fields: 21** (12 original + 9 new fields from this contract)

---

## SESSION LOADING — How New Fields Enter AgentState (chat.py — Phase 2)

At session start, chat.py loads the student profile from DB. The loading
code must be updated in Phase 2 to load all new DB columns into AgentState:

```python
# In chat.py session initialisation (Phase 2 addition):
initial_state_additions = {
    # New fields loaded from student_profiles DB columns:
    "aptitude_scores":        profile.aptitude_scores or {},
    "caas_scores":            profile.caas_scores or {},
    "vna_scores":             profile.vna_scores or {},
    "family_context":         profile.family_context or {},
    "prestige_preference":    profile.prestige_preference or 5.0,
    "misc_assessment_scores": profile.misc_assessment_scores or {},
    # kcis_scores added in Phase 1C when column exists:
    # "kcis_scores":          profile.kcis_scores or {},

    # Session-only — always fresh, never loaded from DB:
    "tier2_prompt_sent": False,
    "turn_count": 0,
}
```

Waqas implements this in chat.py during Phase 2 node updates.

---

## SECTION 2b — NEW ASSESSMENT SUBMISSION ENDPOINTS (profile.py — Phase 1C/2)

New assessment results need endpoints to write scores to the DB.
Each follows the same pattern as the existing `POST /profile/assessment`.
All are added to `backend/app/api/v1/endpoints/profile.py`.

```
POST /api/v1/profile/aptitude
  Body: {"scores": {"numerical": 72.0, "spatial": 55.0,
                    "verbal": 88.0, "logical": 91.0,
                    "numerical_belief": 45.0, "spatial_belief": 80.0,
                    "verbal_belief": 90.0, "logical_belief": 60.0}}
  Writes to: student_profiles.aptitude_scores
  Returns: 200 {"status": "ok"}

POST /api/v1/profile/caas
  Body: {"scores": {"concern": 3.2, "control": 2.8,
                    "curiosity": 3.5, "confidence": 3.0,
                    "cooperation": 2.1}}
  Writes to: student_profiles.caas_scores
  Returns: 200 {"status": "ok"}

POST /api/v1/profile/vna
  Body: {"scores": {"social_status": 75.0,
                    "independence": 60.0, "achievement": 80.0}}
  Writes to: student_profiles.vna_scores
  Returns: 200 {"status": "ok"}

POST /api/v1/profile/misc-assessment
  Body: {"scores": {"conscientiousness": 72.0, "neuroticism": 35.0,
                    "information_gap": 3.8, "external_conflict": 4.2}}
  Writes to: student_profiles.misc_assessment_scores
  Returns: 200 {"status": "ok"}

POST /api/v1/profile/kcis  (Phase 1C only — after kcis_scores column added)
  Body: {"scores": {"mathematical_computational": 85.0,
                    "biological_life_sciences": 42.0, ...}}
  Writes to: student_profiles.kcis_scores
  Returns: 200 {"status": "ok"}
```

**Endpoint pattern (identical to existing POST /profile/assessment):**
- Requires valid JWT (get_current_user dependency)
- Reads body scores dict
- Writes entire dict to the corresponding JSONB column
- Does NOT validate individual key names — stores as-is
- Returns 200 {"status": "ok"} on success

---

## SECTION 3 — KCIS SUB-SCALE KEY NAMES (assessment_questions.json)

The KCIS sub-scale keys used in `kcis_scores` dict and in
`assessment_questions.json` category tags. Fazal uses these exact strings.

**Note:** `kcis_scores` is NOT yet a DB column — it will be added when
the KCIS assessment screen is built (Phase 1C). The key names are defined
now so Fazal writes the questions with consistent category tags.

**Add DB column when KCIS screen is complete:**
```sql
ALTER TABLE student_profiles
ADD COLUMN kcis_scores JSONB NOT NULL DEFAULT '{}';
```

### Within Investigative (5 sub-scales):
```
"mathematical_computational"   # CS, AI, Data Science, Mathematics, Statistics, Actuarial
"biological_life_sciences"     # Biology, Biotechnology, Biochemistry, Genetics, Microbiology
"clinical_health_sciences"     # Medicine, Pharmacy, Allied Health
"physical_sciences"            # Physics, Chemistry, Engineering Sciences, Petroleum
"research_analytical"          # Pure Sciences research orientation
```

### Within Realistic (3 sub-scales):
```
"mechanical_electrical_systems"  # ME, EE, Automotive, Industrial, Mechatronics
"civil_construction_spatial"     # Civil Engineering, structural Architecture
"technology_digital_systems"     # Computer Systems, Telecom, IT Infrastructure
```

### Within Artistic (4 sub-scales):
```
"visual_graphic_design"          # Fine Arts, Communication Design, Digital Media
"spatial_interior_fashion"       # Interior Design, Textile Design, Fashion Design
"architecture_design"            # Architecture aesthetic/form-making aspects
"media_journalism_film"          # Mass Comm, Film, Journalism, Advertising
```

### Within Social (4 sub-scales):
```
"clinical_patient_care"          # Nursing, DPT, Allied Health, Public Health
"teaching_education"             # B.Ed, Education, Health & Physical Education
"community_counselling"          # Social Work, Sociology, Psychology, Development Studies
"law_advocacy_governance"        # LLB, Political Science, International Relations
```

### Within Enterprising (2 sub-scales):
```
"business_commerce_entrepreneurship"  # BBA, Management, Marketing, Entrepreneurship
"leadership_public_service"           # Public Administration, Maritime, Civil Service
```

### Within Conventional (3 sub-scales):
```
"financial_accounting_actuarial"      # Accounting, Finance, Islamic Banking, Commerce
"data_analytics_information"          # Business Analytics, Information Systems, MIS
"administrative_organisational"       # SCM, HR, Operations, Library & Information Science
```

### Cross-cutting (2 sub-scales):
```
"linguistic_literary_humanities"      # English, Urdu, Arabic, History, Philosophy, Languages
"religious_islamic_studies"           # Islamic Studies, Quran, Islamic History
```

**Total: 23 sub-scale keys** (22 RIASEC-typed + the two cross-cutting categories,
with "clinical_health_sciences" (Investigative) and "clinical_patient_care" (Social)
being distinct despite similar names — one is research-oriented, one is patient-facing).

---

## SECTION 4 — affinity_matrix.json NEW FIELDS (Phase 1A — Fazal)

Each field entry in affinity_matrix.json needs these new fields.
Fazal adds them to all existing AND new entries.

```json
{
  "field_id": "cs",

  // EXISTING FIELDS (unchanged):
  "riasec_affinity": {"R": 3, "I": 9, "A": 4, "S": 4, "E": 6, "C": 8},
  "riasec_description": "...",
  "social_acceptability_tier": "high",

  // NEW FIELDS (add to all entries):
  "people_things_axis": -3.5,
  // Float. Prediger 2D projection — People/Things axis.
  // Positive = People pole, Negative = Things pole.
  // Range approximately -5.0 to +5.0.
  // Computed as: 0.5*(E+S) - 0.5*(R+I) using riasec_affinity values.

  "ideas_data_axis": 2.8,
  // Float. Prediger 2D projection — Ideas/Data axis.
  // Positive = Data/Structure pole, Negative = Ideas pole.
  // Range approximately -5.0 to +5.0.
  // Computed as: 0.5*(C+E) - 0.5*(A+I) using riasec_affinity values.

  "prestige_tier": 8,
  // Integer 1-10. Karachi prestige hierarchy position.
  // 10 = Medicine (highest prestige), 1 = lowest prestige.
  // Reference values:
  //   Medicine/MBBS: 10
  //   Engineering (NED): 9
  //   CS/Software: 8
  //   Law/LLB: 7
  //   Business/BBA: 6
  //   Education/Teaching: 5
  //   Social Work: 3
  //   Fine Arts: 3

  "required_capability": {
    "numerical": 70,
    "spatial": 60,
    "verbal": 45,
    "logical": 75
  },
  // Dict mapping aptitude key names (from Section 1.1) to minimum
  // score (0-100) expected for this field.
  // Only include keys where the field has a meaningful requirement.
  // Omit keys with no meaningful requirement (do not set to 0 — omit entirely).
  // FilterNode uses this for capability mismatch detection.

  "kcis_primary_subscale": "mathematical_computational",
  // String. Primary KCIS sub-scale this degree maps to.
  // Must be one of the exact key names from Section 3.

  "kcis_secondary_subscale": "technology_digital_systems",
  // String or null. Secondary KCIS sub-scale if applicable.
  // null if no meaningful secondary mapping.

  "ai_displacement": {
    "ai_resistance_score": 72,
    // Integer 0-100. AI Resistance Score (ARS framework).
    // Higher = more protected from automation.
    // 75+ = near-zero automation probability.
    // Below 40 = 80%+ automation probability.

    "physical_presence": 20,
    "human_relationship": 18,
    "creative_judgment": 15,
    "ethical_accountability": 19,
    // Four sub-dimensions (0-25 each, sum = ai_resistance_score).

    "frey_osborne_probability": 0.28,
    // Float 0.0-1.0. From Frey-Osborne (2013) or ARS-calibrated estimate.
    // 0.28 = 28% automation probability.

    "primary_risk": "Routine analysis tasks automatable; advisory roles protected"
    // String. Plain English description of what is and isn't at risk.
  }
}
```

---

## SECTION 5 — lag_model.json NEW FIELDS (Phase 1A — Fazal)

Each field entry in lag_model.json needs these new fields.

```json
{
  "field_id": "cs",

  // EXISTING FIELDS (unchanged):
  // ... all current lag_model fields stay as-is ...

  // NEW FIELDS (add to all entries):
  "monthly_postings_history": [1800, 1920, 2050, 2100, 2200, 2180, 2300, 2400, 2500, 2620, 2700, 2800],
  // Array of integers. Monthly job posting counts from Rozee.pk,
  // most recent 12 months, oldest first.
  // Used by slope calculation script to compute market_phase, slope,
  // years_to_peak fields (computed automatically — Fazal does not set these).
  // If Rozee.pk data is unavailable, use null and set data_status.confidence = "low".

  "market_phase": "Growth",
  // String. Computed by slope calculation script — DO NOT set manually.
  // Values: "Emerging" | "Growth" | "Mature" | "Peak" | "Declining"
  // Set to "unknown" initially — script overwrites after monthly_postings_history is populated.

  "slope": null,
  // Float or null. Computed by slope calculation script.
  // Positive = growing, Negative = declining.

  "years_to_peak": null,
  // Float or null. Computed by slope calculation script.
  // null if field is still growing with no visible peak.

  "gulf_demand_tier": "high",
  // String. Gulf (UAE, Saudi Arabia, Qatar) employment demand.
  // Values: "high" | "medium" | "low" | "not_applicable"
  // "high" = strong Gulf job market for this field.

  "data_status": {
    "pak_jobs_last_updated": "2025-11",
    // String. YYYY-MM format. When Rozee.pk data was last collected.

    "world_bls_year": 2024,
    // Integer. Which BLS projection year is used.

    "missing_signals": [],
    // Array of strings. Which of the four FutureValue signals are missing.
    // Values: "pak_now" | "pak_future" | "world_now" | "world_future"

    "confidence": "high"
    // String: "high" | "medium" | "low"
    // "high" = all four signals present and recent.
    // "medium" = some signals missing or older than 18 months.
    // "low" = two or more signals missing or older than 36 months.
  },

  "field_reality_notes": {
    "karachi_context": "CS graduates in Karachi face a highly competitive market. Top 40% secure software roles immediately. Bottom 40% enter IT support or switch fields within 3 years.",
    // String. Karachi-specific market reality. 1-3 sentences.

    "typical_career_trajectory": "Junior dev (1-3 yr) → Mid (3-6 yr) → Senior/Lead (6+ yr)",
    // String. Typical career path after graduation.

    "known_disruptors": "AI coding tools reducing entry-level hiring 15-20% annually since 2024.",
    // String or null. Known threats to this field.

    "family_social_fit": "high_acceptability",
    // String. "high_acceptability" | "moderate_acceptability" | "low_acceptability"
    // Based on Karachi family prestige perceptions.

    "required_commitment": "Continuous learning mandatory — field moves extremely fast"
    // String. What the degree/career demands beyond marks.
  }
}
```

---

## SECTION 6 — universities.json NEW FIELDS (Phase 1A — Fazal)

Per university entry (not per degree):

```json
{
  "university_id": "neduet",
  "name": "NED University of Engineering & Technology",

  // EXISTING FIELDS (unchanged):
  // ...

  // NEW FIELDS:
  "employer_perception_tier": "tier_1",
  // String. Karachi employer recognition.
  // Values: "tier_1" | "tier_2" | "tier_3"
  // tier_1 = NED, FAST, IBA, AKU, DUHS — top employer recognition.
  // tier_2 = SZABIST, Bahria, Hamdard, SSUET — solid mid-tier.
  // tier_3 = newer or less-known private universities.
  // Used by ExplanationNode for framing — never affects scores.
}
```

Per degree entry (within each university):

```json
{
  "degree_id": "neduet_be_civil_construction",

  // EXISTING FIELDS (unchanged):
  // ...

  // NEW FIELDS:
  "cutoff_year": 2025
  // Integer. Which admissions year the merit cutoff data is from.
  // ExplanationNode adds caveat when cutoff_year < current_year - 1.
}
```

---

## SECTION 7 — assessment_questions.json NEW CATEGORIES (Phase 1B — Fazal)

New question categories to add alongside existing capability MCQ categories.

### 7.1 Aptitude questions — category tag format

```json
{
  "question_id": "apt_num_001",
  "category": "aptitude",
  "sub_category": "numerical",
  "text_en": "If a train travels 120 km in 1.5 hours, what is its average speed in km/h?",
  "text_ur": "اگر ٹرین 1.5 گھنٹے میں 120 کلومیٹر سفر کرے تو اس کی اوسط رفتار کیا ہوگی؟",
  "options": ["60", "75", "80", "90"],
  "correct_answer": "80",
  "time_limit_seconds": 25,
  "difficulty": "medium"
}
```

Sub-category values (must match aptitude_scores keys):
- `"numerical"` — arithmetic/numerical reasoning
- `"spatial"` — spatial reasoning (requires image in options)
- `"verbal"` — verbal reasoning/analogies
- `"logical"` — logical/abstract pattern reasoning

### 7.2 Aptitude belief questions — category tag format

```json
{
  "question_id": "apt_belief_num_001",
  "category": "aptitude_belief",
  "sub_category": "numerical",
  "text_en": "How confident are you that you could improve your mathematical ability with practice?",
  "text_ur": "آپ کتنا یقین رکھتے ہیں کہ مشق سے آپ کی ریاضی کی صلاحیت بہتر ہو سکتی ہے؟",
  "response_format": "likert_5",
  "time_limit_seconds": null
}
```

### 7.3 CAAS-5-SF questions — category tag format

```json
{
  "question_id": "caas_concern_001",
  "category": "caas",
  "sub_category": "concern",
  "text_en": "Thinking about what my future will be like.",
  "text_ur": "یہ سوچنا کہ میرا مستقبل کیسا ہوگا۔",
  "response_format": "likert_5",
  "likert_anchor_low": "Least strongly",
  "likert_anchor_high": "Most strongly",
  "time_limit_seconds": null
}
```

Sub-category values (must match caas_scores keys):
- `"concern"` — future orientation
- `"control"` — decision ownership
- `"curiosity"` — exploration
- `"confidence"` — self-efficacy
- `"cooperation"` — relational navigation

### 7.4 VNA questions — category tag format

```json
{
  "question_id": "vna_social_status_001",
  "category": "vna",
  "sub_category": "social_status",
  "text_en": "How important is it that your career is respected in your community?",
  "text_ur": "آپ کے لیے یہ کتنا ضروری ہے کہ آپ کے کیریئر کو معاشرے میں عزت ملے؟",
  "response_format": "likert_5",
  "time_limit_seconds": null
}
```

Sub-category values (must match vna_scores keys):
- `"social_status"` — prestige/community respect
- `"independence"` — autonomy preference
- `"achievement"` — effort-orientation

### 7.5 Hybrid CDDQ questions — category tag format

```json
{
  "question_id": "cddq_info_001",
  "category": "cddq",
  "sub_category": "information_gap",
  "text_en": "I don't know enough about what people in different fields actually do day to day.",
  "text_ur": "میں مختلف شعبوں میں لوگ روزانہ کیا کرتے ہیں اس بارے میں کافی نہیں جانتا۔",
  "response_format": "likert_5",
  "time_limit_seconds": null
}
```

Sub-category values:
- `"information_gap"` — lack of occupational information
- `"external_conflict"` — family pressure / external expectations

### 7.6 Hybrid Big Five questions — category tag format

```json
{
  "question_id": "big5_con_001",
  "category": "big_five",
  "sub_category": "conscientiousness",
  "text_en": "I complete tasks thoroughly before moving to the next one.",
  "text_ur": "میں کسی کام کو اگلے کام پر جانے سے پہلے پوری طرح مکمل کرتا ہوں۔",
  "response_format": "likert_5",
  "time_limit_seconds": null
}
```

Sub-category values:
- `"conscientiousness"` — academic persistence
- `"neuroticism"` — stress/emotional reactivity

### 7.7 KCIS questions — category tag format

```json
{
  "question_id": "kcis_math_comp_001",
  "category": "kcis",
  "sub_category": "mathematical_computational",
  "text_en": "How much do you enjoy working with numbers, formulas, and algorithms to solve problems?",
  "text_ur": "آپ کو مسائل حل کرنے کے لیے نمبروں، فارمولوں اور الگورتھم کے ساتھ کام کرنا کتنا پسند ہے؟",
  "response_format": "likert_5",
  "time_limit_seconds": null
}
```

Sub-category values: must be one of the 23 exact key names from Section 3.

---

## SECTION 8 — SCORING FORMULAS USING NEW FIELDS

Node developers read this to understand how the new fields feed into scores.

### 8.1 Tier detection (ProfilerNode reads, nodes use)

```python
def get_assessment_tier(state: AgentState) -> str:
    has_caas = bool(state.get("caas_scores"))
    has_kcis = bool(state.get("kcis_scores"))
    has_vna  = bool(state.get("vna_scores"))

    if not (has_caas and has_kcis):
        return "tier1"   # basic — RIASEC + aptitude only
    elif not has_vna:
        return "tier2"   # standard — adds CAAS + KCIS
    else:
        return "tier3"   # enriched — all assessments complete
```

### 8.2 3D match formula (ScoringNode)

```python
def compute_3d_match(
    student_riasec: dict,
    degree: dict,
    prestige_preference: float,
) -> float:
    # Step 1: Prediger 2D projection
    R,I,A,S,E,C = [student_riasec.get(k, 0) for k in "RIASEC"]
    student_pt = 0.5*(E+S) - 0.5*(R+I)
    student_id = 0.5*(C+E) - 0.5*(A+I)

    degree_pt = degree["people_things_axis"]
    degree_id = degree["ideas_data_axis"]

    distance_2d = ((student_pt - degree_pt)**2 + (student_id - degree_id)**2) ** 0.5
    max_dist = 14.14  # sqrt(200) — normalisation factor
    match_2d = 1.0 - (distance_2d / max_dist)

    # Step 2: Legacy dot product (transition blending)
    dot_match = compute_dot_product_match(student_riasec, degree["riasec_affinity"])

    # Step 3: Prestige alignment bonus
    degree_prestige = degree.get("prestige_tier", 5)  # 1-10
    prestige_gap = abs(prestige_preference - degree_prestige)
    prestige_alignment = max(0.0, 1.0 - (prestige_gap / 10.0))

    # Step 4: Blend (60% geometric, 30% dot product, 10% prestige)
    match_score = 0.60 * match_2d + 0.30 * dot_match + 0.10 * prestige_alignment

    return max(0.0, min(1.0, match_score))
```

### 8.3 Capability mismatch detection (FilterNode)

```python
def check_capability_mismatch(
    student_aptitude: dict,
    degree_required: dict,
) -> tuple[bool, dict]:
    """Returns (mismatch_detected, gaps_by_dimension)"""
    gaps = {}
    for dimension, required_score in degree_required.items():
        student_score = student_aptitude.get(dimension, 0.0)
        if student_score < required_score:
            gaps[dimension] = required_score - student_score

    mismatch = len(gaps) > 0 and sum(gaps.values()) > 25.0
    return mismatch, gaps
```

---

## SECTION 9 — STEP 4 PREFERENCES SCREEN ADDITIONS (Khuzzaim)

Two new fields added to the existing Step 4 Preferences screen.

### 9.1 POST /profile/preferences endpoint — updated payload

New fields added to the existing endpoint payload:

```python
class PreferencesRequest(BaseModel):
    # EXISTING FIELDS (unchanged):
    budget_per_semester: int | None = None
    transport_willing: bool | None = None
    home_zone: str | None = None
    career_goal: str | None = None

    # NEW FIELDS:
    family_career_field: str | None = None
    # Dropdown value. Must be one of the allowed values from Section 1.4.

    family_career_expectation: str | None = None
    # Radio button value. Must be one of the allowed values from Section 1.4.
```

### 9.2 Flutter widget types

```
family_career_field    → DropdownButtonFormField<String>
family_career_expectation → RadioListTile group (3 options)
```

**Dropdown options for family_career_field (display → stored value):**
```
"Medicine / Healthcare"    → "medicine"
"Engineering"              → "engineering"
"Business"                 → "business"
"Education / Teaching"     → "education"
"Law"                      → "law"
"Computing / Technology"   → "computing"
"Government / Civil Service" → "government_civil_service"
"Arts & Media"             → "arts_media"
"Other"                    → "other"
"Not applicable"           → "not_applicable"
```

**Radio options for family_career_expectation (display → stored value):**
```
"My family expects me to follow a specific field" → "expects_specific_field"
"My family has general preferences but I have freedom" → "general_preferences"
"My family is fully open to my choice" → "fully_open"
```

---

## SECTION 10 — WHAT MUST HAPPEN IN SEQUENCE

```
Phase 0 — THIS DOCUMENT (schema_contract.md committed)
   Everyone reads before writing any JSON or code.

Phase 0b — Alembic migrations (Waqas)
   Add 6 new columns to student_profiles:
     aptitude_scores, caas_scores, vna_scores,
     family_context, prestige_preference, misc_assessment_scores.
   Do NOT add kcis_scores yet — that runs in Phase 1C.
   Deploy to Supabase. Verify all 6 columns exist before Phase 2.

Phase 1A — Data files (Fazal)
   Add new fields to affinity_matrix, lag_model, universities
   using EXACT key names from Sections 4, 5, 6 of this document.

Phase 1B — Assessment questions (Fazal)
   Add all new question categories using EXACT sub_category
   values from Section 7 of this document.

Phase 1C — Frontend screens + kcis migration (Khuzzaim + Waqas)
   Khuzzaim: Step 4 additions (Section 9).
             New assessment screens using sub_category keys from Section 7.
   Waqas: Add kcis_scores column migration (Section 1.7).
          Add new assessment submission endpoints (Section 2b).

Phase 2 — Node updates (Waqas)
   Add 9 new AgentState fields using EXACT names from Section 2.
   Implement scoring formulas from Section 8.
   Update chat.py session loading per SESSION LOADING block.
```

---

## SECTION 11 — KEY NAMES QUICK REFERENCE

The single most important table. Fazal writes JSON against these.
Waqas writes code against these. They must match exactly.

| Source | Key | Used In |
|---|---|---|
| aptitude_scores | "numerical" | affinity_matrix required_capability, ScoringNode |
| aptitude_scores | "spatial" | affinity_matrix required_capability, ScoringNode |
| aptitude_scores | "verbal" | affinity_matrix required_capability, ScoringNode |
| aptitude_scores | "logical" | affinity_matrix required_capability, ScoringNode |
| aptitude_scores | "numerical_belief" | ProfilerNode belief gap detection |
| aptitude_scores | "spatial_belief" | ProfilerNode belief gap detection |
| aptitude_scores | "verbal_belief" | ProfilerNode belief gap detection |
| aptitude_scores | "logical_belief" | ProfilerNode belief gap detection |
| caas_scores | "concern" | ProfilerNode strategy (< 2.5 = early stage) |
| caas_scores | "control" | ProfilerNode agency framing |
| caas_scores | "curiosity" | ProfilerNode exploration mode |
| caas_scores | "confidence" | ExplanationNode confidence framing |
| caas_scores | "cooperation" | ProfilerNode family pressure detection |
| vna_scores | "social_status" | ProfilerNode prestige_preference derivation |
| vna_scores | "independence" | ExplanationNode path framing |
| vna_scores | "achievement" | ExplanationNode effort framing |
| family_context | "family_career_field" | ProfilerNode strategy routing |
| family_context | "family_career_expectation" | ProfilerNode family pressure detection |
| family_context | "social_pressure_field" | ExplanationNode family framing |
| affinity_matrix | "people_things_axis" | ScoringNode 3D match |
| affinity_matrix | "ideas_data_axis" | ScoringNode 3D match |
| affinity_matrix | "prestige_tier" | ScoringNode 3D match |
| affinity_matrix | "required_capability" | FilterNode mismatch detection |
| affinity_matrix | "kcis_primary_subscale" | ScoringNode KCIS discrimination |
| affinity_matrix | "kcis_secondary_subscale" | ScoringNode KCIS discrimination |
| lag_model | "monthly_postings_history" | Slope calculation script |
| lag_model | "market_phase" | ExplanationNode framing (computed) |
| lag_model | "gulf_demand_tier" | ExplanationNode Gulf framing |
| lag_model | "data_status" | ExplanationNode confidence caveat |
| lag_model | "field_reality_notes" | ExplanationNode counsellor reality |
| lag_model | "ai_displacement.ai_resistance_score" | ExplanationNode ARS framing |
| universities | "employer_perception_tier" | ExplanationNode employer context |
| universities | "cutoff_year" | ExplanationNode staleness caveat |
| misc_assessment_scores | "conscientiousness" | ProfilerNode tier3_enriched strategy |
| misc_assessment_scores | "neuroticism" | ExplanationNode stress framing |
| misc_assessment_scores | "information_gap" | ExplanationNode field_reality_notes emphasis |
| misc_assessment_scores | "external_conflict" | ProfilerNode agency-affirming mode |
| kcis_scores | [23 sub-scale keys — see Section 3] | ScoringNode KCIS discrimination, ProfilerNode sub-field questioning |

---

*SCHEMA_CONTRACT.md — Phase 0 lock*
*Produced by Architecture Chat v5 — May 2026*
*All key names in this document are locked.*
*Any change to a key name after this document is committed*
*requires updating this document AND all files that use the key.*
