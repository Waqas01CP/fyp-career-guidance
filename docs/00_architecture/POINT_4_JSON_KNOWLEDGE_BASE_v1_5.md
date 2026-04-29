# Point 4 — JSON Knowledge Base Design
## FYP: AI-Assisted Academic Career Guidance System
### Status: COMPLETE AND LOCKED
### Date: March 2026
### Change Log:
### v1.0 — Initial lock. Defines all four JSON files:
###         universities.json, lag_model.json, affinity_matrix.json,
###         assessment_questions.json.
###         Resolves one conflict: DATA_CHAT_INSTRUCTIONS nested fees as
###         financials.fee_per_semester_pkr but Point 2 FilterNode code reads
###         degree["fee_per_semester"] (flat). Point 2 wins — flat field locked.
### v1.5 — Two issues fixed:
###         (1) affinity_matrix.json RIASEC score note corrected from
###             "Khuzzaim" to "Fazal" — affinity_matrix is Fazal's file;
###             Khuzzaim only writes assessment_questions.json.
###         (2) Validation script extended with Rule 5 — checks that every
###             stream in conditionally_eligible_streams has a matching key
###             in eligibility_notes. Without this, the documented crash rule
###             was warned about in prose but not enforced at commit time.

---

## OVERVIEW

Four JSON files live at `backend/app/data/`. They ship inside the Docker image and
are loaded at server startup. They are the read-only knowledge base the pipeline
reasons over. No node writes to these files at runtime.

| File | Owner | Updated by | Read by |
|---|---|---|---|
| `universities.json` | Fazal | Manual + Phase A research | FilterNode, AnswerNode |
| `lag_model.json` | Fazal | `scripts/compute_future_values.py` (once per semester) | ScoringNode, AnswerNode |
| `affinity_matrix.json` | Fazal | Manual (once — Holland's theory) | ScoringNode |
| `assessment_questions.json` | Khuzzaim | Manual (Phase A) | `POST /profile/assessment` endpoint |

**Referential integrity rule:** Every `degree_id` in `universities.json` must appear in
`lag_model.json`'s `associated_degrees` arrays. Run the validation script in
`DATA_CHAT_INSTRUCTIONS.md` before every commit.

**Backup:** Before viva, copy all four files to `backend/app/data/seeds/backup/` — the
Golden Copy. `seed_db.py` uses this folder for demo database restore.

---

## JSON LOADING PATTERN

`universities.json` and `assessment_questions.json` are used as arrays directly. But
`lag_model.json` and `affinity_matrix.json` must be converted to dicts at server startup
so ScoringNode can look up entries by `field_id` in O(1):

```python
# In main.py or a dedicated data_loader.py module — runs once at startup
import json, pathlib

DATA_DIR = pathlib.Path("app/data")

universities     = json.loads((DATA_DIR / "universities.json").read_text())
# Used as a list — FilterNode iterates over all universities and degrees

lag_model        = {
    entry["field_id"]: entry
    for entry in json.loads((DATA_DIR / "lag_model.json").read_text())
}
# Used as a dict — ScoringNode looks up: lag_model[degree["field_id"]]

affinity_matrix  = {
    entry["field_id"]: entry
    for entry in json.loads((DATA_DIR / "affinity_matrix.json").read_text())
}
# Used as a dict — ScoringNode looks up: affinity_matrix[degree["field_id"]]

assessment_questions = json.loads((DATA_DIR / "assessment_questions.json").read_text())
# Used as a list — endpoint filters by subject + curriculum_level + difficulty
```

These four objects are loaded once and passed as dependencies (via FastAPI dependency
injection or as module-level globals). No node re-reads the files from disk at runtime.

---

## FILE 1 — `universities.json`

### Purpose
Complete degree catalog for the top 20 HEC-recognized universities in Karachi.
FilterNode reads this to run all five constraint checks. AnswerNode reads this for fee
queries and application deadline information.

### Top-Level Structure

The file is a JSON array. Each element is one university.

```json
[
  { /* NED University */ },
  { /* FAST-NUCES */     },
  ...
]
```

### Per-University Schema

```json
{
  "university_id": "neduet",
  "name": "NED University of Engineering & Technology",
  "type": "public",
  "zone": 3,
  "location": {
    "area": "University Road, Karachi",
    "zone": 3
  },
  "scholarships": [
    {
      "name": "NED Merit Scholarship",
      "coverage": "Full tuition",
      "criteria": "Top 10% of batch"
    }
  ],
  "data_last_verified": "March 2026",
  "entry_test_difficulty_tier": "standard",
  "degrees": [ /* array of degree objects — see below */ ]
}
```
**`entry_test_difficulty_tier`** — university-level entry test difficulty relative to the
capability assessment proxy. FilterNode uses this to determine `entry_test_harder_than_assessed`
soft flag reliability.

| Value | Universities | Meaning |
|---|---|---|
| `"standard"` | NED, UoK, IBA, Bahria, most others | Assessment proxy is a reasonable approximation |
| `"hard"` | FAST-NUCES | Test is harder than assessed — advise extra prep |
| `"extreme"` | NUST | Test difficulty far exceeds assessment — strong caution flag |

Set this at the university level — it applies to all degrees at that university.

**`zone`** appears at both the top-level and inside `location.zone`. FilterNode reads
`degree["location"]["zone"]` per Point 2 — the nested path is what the code uses.
The top-level `zone` field is kept for convenience (e.g., AnswerNode natural language
responses) but is the same value.

**University ID values (exact strings — use these everywhere):**
```
neduet, fast_nuces, uok, iba, szabist, ssuet, iqra, bahria,
hamdard, dow, aku, indus_valley, paf_kiet, dadabhoy,
greenwich, cbm, kasbit, newports, khi_univ_arts, khi_univ_science
```

### Per-Degree Schema

```json
{
  "degree_id": "neduet_bs_cs",
  "name": "BS Computer Science",
  "field_id": "computer_science",
  "field_category": "CS",
  "shift": "full_day",
  "duration_years": 4,

  "eligibility": {
    "fully_eligible_streams": ["Pre-Engineering", "ICS"],
    "conditionally_eligible_streams": ["Pre-Medical"],
    "eligibility_notes": {
      "Pre-Medical": "Requires 8-week PEC-mandated Mathematics bridge course. Max 40% of intake seats under this pathway."
    },
    "mandatory_subjects": ["Mathematics"],
    "min_percentage_hssc": 60.0,
    "policy_pending_verification": false,
    "subject_waivers": {
      "Mathematics": {
        "waivable_for_streams": ["Pre-Medical"],
        "condition": "Must complete PEC-mandated 8-week bridge course before enrollment",
        "max_intake_percentage": 40
      }
    }
  },

  "aggregate_formula": {
    "matric_weight": 0.10,
    "inter_weight": 0.50,
    "entry_test_weight": 0.40,
    "subject_weights": {
      "mathematics": 2.0,
      "physics": 1.5,
      "other": 1.0
    },
    "notes": "NED uses 10% Matric + 50% Inter + 40% ECAT. Subject weights applied to Inter only."
  },

  "fee_per_semester": 27500,
  "admission_fee_pkr": 15000,
  "estimated_total_cost_pkr": 235000,

  "merit_history": [
    {"year": 2021, "cutoff": 82.5},
    {"year": 2022, "cutoff": 84.1},
    {"year": 2023, "cutoff": 83.8},
    {"year": 2024, "cutoff": 85.0}
  ],
  "cutoff_range": {
    "min": 82.5,
    "max": 85.0
  },
  "confidence_band": 2.5,

  "location": {
    "area": "University Road, Karachi",
    "zone": 3
  },

  "entry_test": {
    "required": true,
    "test_name": "ECAT",
    "math_weight": 0.40,
    "physics_weight": 0.30,
    "english_weight": 0.15,
    "chemistry_weight": 0.15,
    "difficulty": "high"
  },

  "application_window": {
    "data_cycle": "2025",
    "typical_open": "June",
    "typical_close": "August",
    "multiple_rounds": false,
    "round_details": null,
    "website": "https://ned.edu.pk/admissions",
    "last_verified": "March 2026"
  }
}
```

### Field-by-Field Reference

**`degree_id`** — globally unique string. Format: `{university_id}_{canonical_degree_id}`.
Example: `neduet_bs_cs`, `fast_nuces_bs_cs`, `iba_bba`.
For universities with multiple shifts of the same degree, use suffix:
`fast_nuces_bs_cs_morning`, `fast_nuces_bs_cs_evening`. Both entries share the same `field_id`.

**`shift`** — program delivery schedule. Valid values: `"morning"`, `"evening"`, `"full_day"`.
Use `"full_day"` when the university only offers one shift and does not distinguish.
NED, FAST: all undergraduate degrees are `"full_day"` (no evening undergrad programs).
UoK, some private universities: may have `"morning"` and `"evening"` entries.
When a university offers two shifts, create two separate degree entries with different
`degree_id` values (suffix `_morning`/`_evening`), separate `fee_per_semester`, separate
`merit_history` and `cutoff_range`. Both entries share the same `field_id`.
FilterNode passes `shift` through to roadmap entries — no logic change.
ExplanationNode and frontend display shift as part of the degree label.

**`field_id`** — links to `lag_model.json` and `affinity_matrix.json`. Uses the canonical
field IDs (e.g., `"computer_science"`, `"electrical_engineering"`). Multiple degrees at
different universities share the same `field_id`.

**`field_category`** — broad grouping for display. Values: `"CS"`, `"Engineering"`,
`"Business"`, `"Medical"`, `"Science"`, `"Arts"`, `"Law"`, `"Education"`.

**`eligibility.fully_eligible_streams`** — streams that can apply directly, no conditions.

**`eligibility.conditionally_eligible_streams`** — streams that can apply with additional
requirements (bridge course, subject waiver). FilterNode marks these as `eligibility_tier:
"likely"` and attaches the eligibility note.

**`eligibility.mandatory_subjects`** — subjects that must be present in `subject_marks`.
**Title Case** (e.g., `"Mathematics"`, `"Physics"`). This casing must match the keys in
`subject_waivers` exactly — FilterNode looks up the waiver using the same value from this
list with no case conversion. FilterNode hard-excludes if any mandatory subject is missing
AND no subject waiver exists for that stream.

**`eligibility.eligibility_notes`** — dict keyed by stream name. FilterNode accesses this
as `degree["eligibility"]["eligibility_notes"][stream]` — direct key access, no `.get()`.
**Every stream that appears in `conditionally_eligible_streams` must have a matching key
here, or FilterNode crashes with KeyError.** The value is the note shown to the student
explaining the condition.

```json
"eligibility_notes": {
  "Pre-Medical": "Requires 8-week PEC-mandated Mathematics bridge course."
}
```

Rule: `len(conditionally_eligible_streams) == len(eligibility_notes)` and all keys must
match exactly.

**`eligibility.min_percentage_hssc`** — HEC/council legal minimum HSSC percentage.
FilterNode uses the student's unadjusted inter average (simple mean of non-zero
subject marks, no weighting) and compares against this value. If below → hard exclusion
with the governing council cited in the message.

This is a legal disqualification, not a merit judgment. The "merit cutoffs never
hard-exclude" rule applies to `cutoff_range` comparisons only — `min_percentage_hssc`
is a separate, absolute legal floor.

HEC/council minimum categories (stored per-degree — do not deviate from these values):

| Value | Applies to | Governing council |
|---|---|---|
| `60.0` | BE/BSc Engg, MBBS/BDS, Pharm-D, DVM | PEC / PMDC / PCP / PVMC |
| `50.0` | BS CS/SE/AI/Cyber/IT, B.Arch, BSN, DPT | NCEAC / PCATP / PNC |
| `45.0` | LLB, General BS Sciences, BBA, Arts/Humanities | HEC (general) |

Note: `BE Software Engineering` = 60% (PEC). `BS Software Engineering` = 50% (NCEAC).
The degree title prefix determines which council governs — not the subject matter.

**`eligibility.policy_pending_verification`** — when `true`, FilterNode adds a
`policy_unconfirmed` soft flag. Used for NED Pre-Medical → Engineering pathway until
official announcement.

**`eligibility.subject_waivers`** — dict keyed by subject name (Title Case, matching
`mandatory_subjects`). Defines which streams can bypass a missing mandatory subject via
a bridge course or equivalent. FilterNode reads this as:
`degree["eligibility"]["subject_waivers"].get(subject)`. For degrees where no waiver
exists, set to an empty dict `{}` — never omit the field entirely.

```json
"subject_waivers": {
  "Mathematics": {
    "waivable_for_streams": ["Pre-Medical"],
    "condition": "Must complete PEC-mandated 8-week bridge course before enrollment",
    "max_intake_percentage": 40
  }
}
```

For a degree with no subject waivers at all:
```json
"subject_waivers": {}
```

**`aggregate_formula`** — how this university calculates admission aggregate. Contains
subject weights for Inter marks. `calculate_aggregate()` helper in FilterNode reads this
to compute the student's aggregate for this specific degree. Different degrees (even at
the same university) can have different formulas — Engineering weights Maths+Physics
higher than a CS degree might.

**`fee_per_semester`** — flat field, integer, in PKR. FilterNode reads this directly as
`degree["fee_per_semester"]`. This is the fee for one semester. Fazal normalises at data
entry: if a university publishes annual fees, divide by 2 before storing here.

**`merit_history`** — last 4 years of historical merit cutoffs. Array of `{year, cutoff}`
objects. Used by FilterNode to set `cutoff_range.min` and `cutoff_range.max`. Always
store at least 3 years for a meaningful range.

**`cutoff_range`** — `min` is the lowest cutoff in `merit_history`; `max` is the highest.
FilterNode uses these directly for merit tier assignment.

**`confidence_band`** — how much the cutoff typically fluctuates year to year (max - min
from history). Used for UI display only — not in FilterNode logic.

**`location.zone`** — integer 1-5, Karachi zone. FilterNode reads `degree["location"]["zone"]`
for the transport soft flag. Zone mapping matches Point 1:

| Zone | Areas |
|---|---|
| 1 | North Karachi, Gulberg, New Karachi, Surjani |
| 2 | Gulshan-e-Iqbal, Johar, Nazimabad, North Nazimabad |
| 3 | Defence, Clifton, Saddar, PECHS, Bahadurabad |
| 4 | Malir, Landhi, Korangi, Shah Faisal |
| 5 | SITE, Orangi, Baldia, Lyari |

**`entry_test`** — ExplanationNode reads this for entry test benchmarking. If a student's
capability score in a subject is below 65% and that subject carries significant weight
(> 0.25), ExplanationNode includes strengthening advice.

**Standardized weight field names — exactly these five, no others:**

| Field name | Maps to capability_scores subject |
|---|---|
| `math_weight` | `mathematics` |
| `physics_weight` | `physics` |
| `chemistry_weight` | `chemistry` |
| `biology_weight` | `biology` |
| `english_weight` | `english` |

Only include the weight fields that are actually tested by this university's entry test.
All weight fields present must sum to 1.0. ExplanationNode reads these field names
directly — using any other name (e.g., `bio_weight`, `maths_weight`) will silently fail
to trigger advice for that subject.

For degrees **with** an entry test — Engineering/CS (ECAT-style):
```json
"entry_test": {
  "required": true,
  "test_name": "ECAT",
  "math_weight": 0.40,
  "physics_weight": 0.30,
  "english_weight": 0.15,
  "chemistry_weight": 0.15,
  "difficulty": "high"
}
```

For degrees **with** an entry test — Medical (MDCAT-style):
```json
"entry_test": {
  "required": true,
  "test_name": "MDCAT",
  "biology_weight": 0.40,
  "chemistry_weight": 0.30,
  "physics_weight": 0.20,
  "english_weight": 0.10,
  "difficulty": "high"
}
```

For degrees **without** an entry test (many Business, Arts, Social Science programs):
```json
"entry_test": {
  "required": false,
  "test_name": null,
  "difficulty": null
}
```

When `required` is `false`, omit all weight fields entirely — do not include them as
null. ExplanationNode checks `entry_test["required"]` first and skips the benchmarking
logic entirely when false.

**`application_window`** — AnswerNode reads this for deadline queries. Always set
`data_cycle` to indicate which year's data this reflects. For universities with multiple
intakes, populate `round_details` array:
```json
"round_details": [
  {"round": "Fall 2025", "open": "June 2025", "close": "August 2025"},
  {"round": "Spring 2026", "open": "November 2025", "close": "January 2026"}
]
```

### Canonical Field IDs (linking degree to lag_model and affinity_matrix)

```
computer_science, artificial_intelligence, software_engineering,
cybersecurity, data_science, digital_media, electrical_engineering,
mechanical_engineering, civil_engineering, biomedical_engineering,
electronics_engineering, robotics_iot, medicine_mbbs, dentistry_bds,
pharmacy, mathematics, physics, chemistry_biochemistry, architecture,
fine_arts, psychology, social_work, education_bed, business_bba,
economics, finance_accounting, law_llb, mass_communication,
agriculture, veterinary_science, chemical_engineering, telecommunications_engineering,
industrial_manufacturing_engineering, automotive_engineering,
metallurgical_engineering, materials_engineering,
polymer_petrochemical_engineering, urban_infrastructure_engineering,
construction_engineering, textile_engineering, food_engineering,
textile_sciences, english_linguistics, fintech, business_analytics,
nursing, physical_therapy, economics_mathematics, economics_data_science,
social_sciences
```

---

## FILE 2 — `lag_model.json`

### Purpose
Stores the pre-computed `FutureValue` score (0–10) for each degree field along with
the raw evidence used to compute it. ScoringNode reads only `computed.future_value`.
AnswerNode reads `employment_data` and `career_paths` for market queries.

`scripts/compute_future_values.py` writes `computed.future_value` and
`computed.last_computed`. Every other field is set by Fazal during data collection and
is not touched by the script.

### Top-Level Structure

The file is a JSON array. Each element is one field entry.

```json
[
  { /* computer_science */ },
  { /* cybersecurity */    },
  ...
]
```

### Per-Field Schema

```json
{
  "field_id": "cybersecurity",
  "field_name": "Cybersecurity / Network Security",
  "associated_degrees": ["neduet_bs_cybersecurity", "fast_nuces_bs_cybersecurity"],
  "lag_category": "FAST",
  "lifecycle_status": "Emerging",
  "risk_factor": "Low",
  "risk_reasoning": "Demand is structural — breaches increase regardless of tech cycles. Not easily automated.",
  "outsourcing_applicable": true,
  "infrastructure_constrained": false,
  "constraint_note": "",

  "pakistan_now": {
    "job_postings_monthly": 340,
    "yoy_growth_rate": 0.38,
    "sources": ["rozee.pk", "mustakbil.com"]
  },

  "world_now": {
    "us_yoy_growth_rate": 0.31,
    "uk_yoy_growth_rate": 0.22,
    "uae_yoy_growth_rate": 0.35,
    "sources": ["LinkedIn Talent Trends 2025", "BLS 2024"]
  },

  "world_future": {
    "us_bls_4yr_projected_growth": 0.33,
    "bls_soc_code": "15-1212",
    "projection_basis": "BLS Occupational Outlook Handbook 2024-34"
  },

  "pakistan_future": {
    "projected_4yr_growth": 0.52,
    "derivation": "pakistan_now growth + world_future signal adjusted for lag"
  },

  "lag_parameters": {
    "lag_years": 2.0,
    "arrival_confidence": "high",
    "cultural_barrier": false,
    "societal_barrier": false,
    "notes": "Banking/telecom/government sectors driving strong domestic demand already."
  },

  "computed": {
    "future_value": 8.3,
    "last_computed": "2026-03"
  },

  "employment_data": {
    "rozee_live_count": 340,
    "rozee_last_updated": "2026-03-10",
    "hec_employment_rate": null,
    "qualitative_pathway": null,
    "data_source_used": "rozee_live",
    "data_status": "sufficient"
  },

  "career_paths": {
    "entry_level_title": "Junior Security Analyst",
    "typical_first_role_salary_pkr": "60,000 – 90,000/month",
    "common_sectors": ["Banking", "Telecom", "Government IT", "Freelance (remote)"]
  }
}
```

### Field-by-Field Reference

**`field_id`** — must match the `field_id` in `affinity_matrix.json` and the value used
in `universities.json` degree entries. Canonical IDs listed in File 1 section above.

**`associated_degrees`** — array of `degree_id` strings from `universities.json`. Links
this field entry back to specific degrees. Used by the validation script to detect orphaned
degrees.

**`lag_category`** — one of: `LEAPFROG`, `FAST`, `MEDIUM`, `SLOW`, `LOCAL`.
Determines which FutureValue weight set is applied. See Point 2 section 14 for full
per-category weights.

**`lifecycle_status`** — display value for frontend. One of: `"Emerging"`, `"Peak"`,
`"Stable"`, `"Declining"`.

**`risk_factor`** — display value. One of: `"Low"`, `"Medium"`, `"High"`.

**`outsourcing_applicable`** — `true` for fields where Pakistani graduates can work
remotely for foreign companies (all lag-based fields). `false` for LOCAL fields
(Medicine, Law, Civil Engineering). Affects how ExplanationNode frames global data.

**`infrastructure_constrained`** — `true` when the field's growth in Pakistan is limited
by physical infrastructure (e.g., Robotics requires factory automation, IoT requires smart
grid). Informational — used in ExplanationNode tone selection.

**`pakistan_now`** — Layer 1 source data. `yoy_growth_rate` is a float (0.38 = 38% growth).
`job_postings_monthly` is the current Rozee.pk live count.

**`world_now`** and **`world_future`** — Layers 2 and 3 source data. Float rates.

**`computed.future_value`** — the only field ScoringNode reads. Written by
`scripts/compute_future_values.py`. All other fields in `lag_model.json` are inputs to
that script, not read by any node at runtime.

**`employment_data.data_status`** — one of: `"sufficient"`, `"partial"`, `"insufficient"`.
When `"insufficient"`, the field must not go to production. At minimum ONE of
`rozee_live_count`, `hec_employment_rate`, or `qualitative_pathway` must be non-null.
If all three are null, set `data_status: "insufficient"`.

**`employment_data.data_source_used`** — which source was primary: `"rozee_live"`,
`"hec_tracer"`, `"qualitative"`, `"proxy_adjacent"`.

**`career_paths`** — AnswerNode reads this when a student asks about career prospects.
`typical_first_role_salary_pkr` is a string range — not a precise figure.

### LOCAL Category Fields — Formula Difference

For `lag_category: "LOCAL"`, Layer 3 weight is 0.0 (per `FUTURE_VALUE_WEIGHTS` in
`config.py`). FutureValue is driven entirely by domestic demand:

```
FutureValue (LOCAL) = (0.6 × Layer1_normalised) + (0.4 × Layer2_normalised)
```

For LOCAL fields, `outsourcing_applicable` must be `false`. `world_future` and
`world_now` may be populated with Gulf/UAE data where relevant (e.g., Pakistani engineers
in Gulf construction), but their weight in the formula is effectively zero via `layer3: 0.00`.

### Missing Data Fallback

```python
# Fallback order for employment_data in the scraper (Waqas builds)
rozee → mustakbil → jobz → cached_value
```

For fields where Rozee.pk has no listings (niche academic/arts fields), use:
- `hec_employment_rate` from HEC Graduate Tracer Study (percentage, e.g., 0.68)
- `qualitative_pathway` — written text describing typical career paths
- For Social Work / NGO fields: BrightSpyre one-time manual count

---

## FILE 3 — `affinity_matrix.json`

### Purpose
Maps each degree field to RIASEC dimension scores. ScoringNode uses these as vectors
in a dot product against the student's `riasec_scores` to compute `match_score`.

Based on Holland (1997) "Making Vocational Choices." Scores are on a 1–10 scale
representing how strongly each personality type is associated with success and
satisfaction in that field. Minimum is 1 (dimension almost entirely absent from
this field), maximum is 10 (dimension strongly dominant).

### Top-Level Structure

The file is a JSON array. Each element is one field entry.

```json
[
  { /* computer_science */ },
  { /* cybersecurity */    },
  ...
]
```

### Per-Field Schema

```json
{
  "field_id": "cybersecurity",
  "riasec_affinity": {
    "R": 5,
    "I": 9,
    "A": 2,
    "S": 4,
    "E": 5,
    "C": 8
  },
  "riasec_description": "High Investigative (problem-solving, analysis) and Conventional (systematic, rule-following) profile. Realistic component for hands-on technical work.",
  "social_acceptability_tier": "high",
  "prestige_note": "Well-regarded in Pakistan's tech industry. Growing awareness due to banking and fintech sector demand."
}
```

### Field-by-Field Reference

**`field_id`** — must match `field_id` in `lag_model.json` and the `field_id` used in
`universities.json` degree entries. Same canonical IDs throughout.

**`riasec_affinity`** — integer scores 1–10 for each of the six RIASEC dimensions:
- `R` — Realistic: hands-on, practical, physical
- `I` — Investigative: analytical, intellectual, research-oriented
- `A` — Artistic: creative, expressive, unstructured
- `S` — Social: helping, teaching, interpersonal
- `E` — Enterprising: leadership, persuasion, business
- `C` — Conventional: organised, systematic, detail-oriented

Minimum value is 1, not 0. A score of 1 means the dimension is almost entirely absent
from this field. A score of 10 means it is strongly dominant. Fazal should never
enter 0 — use 1 for the weakest possible affinity.

ScoringNode computes match score as:
```python
raw_match = sum(student_riasec[dim] * affinity[dim] for dim in "RIASEC")
theoretical_max = sum(s * 10 for s in student_riasec.values())
match_score_normalised = raw_match / theoretical_max
```

The theoretical max normalises for the fact that students who score high across all
dimensions would otherwise always get high raw scores. This ensures the score reflects
alignment, not absolute magnitude.

**`riasec_description`** — plain English description of the dominant RIASEC profile for
this field. Used by ExplanationNode to explain RIASEC alignment in natural language.

**`social_acceptability_tier`** — one of: `"high"`, `"moderate"`, `"lower"`. Qualitative
assessment of Pakistani social/family perception of this field. Used by ExplanationNode
to adjust tone when discussing socially contested degree choices.

| Tier | Fields |
|---|---|
| `"high"` | MBBS, Engineering, CS, BBA at top institutions |
| `"moderate"` | Science degrees, Psychology, Mass Communication, Architecture |
| `"lower"` | Fine Arts, Social Work, Education (B.Ed) |

**`prestige_note`** — optional free text. ExplanationNode may reference this when
surfacing prestige-related context. Keep neutral and factual.

---

## FILE 4 — `assessment_questions.json`

### Purpose
Bank of pre-written, pre-verified MCQ questions used in the capability assessment.
Read by `POST /profile/assessment` endpoint at question selection time.
No node reads this file — it is an endpoint-level concern only.

Khuzzaim writes and verifies all questions. LLMs can be used to generate questions
or check answer keys — deterministic scoring requires human-verified correct answers.

### Top-Level Structure

The file is a JSON array. Each element is one question.

```json
[
  { /* question 1 */ },
  { /* question 2 */ },
  ...
]
```

### Per-Question Schema

```json
{
  "id": "math_inter_part2_042",
  "subject": "mathematics",
  "curriculum_level": "inter_part2",
  "topic": "calculus",
  "difficulty": "easy",
  "question": "What is the derivative of x³ with respect to x?",
  "options": ["x²", "3x²", "3x³", "x⁴/4"],
  "correct_index": 1
}
```

### Field-by-Field Reference

**`id`** — unique string. Format: `{subject_abbrev}_{level}_{number}`.
Number is zero-padded to 3 digits. Use these exact abbreviations — do NOT use
the full subject name in the ID:

| Subject | Abbreviation used in ID |
|---|---|
| mathematics | `math` |
| physics | `physics` |
| chemistry | `chem` |
| biology | `bio` |
| english | `eng` |

Examples: `math_inter_part2_042`, `physics_matric_007`, `eng_inter_part1_015`,
`chem_inter_part2_003`, `bio_matric_021`.

**`subject`** — exactly one of:
`"mathematics"`, `"physics"`, `"chemistry"`, `"biology"`, `"english"`

**`curriculum_level`** — exactly one of:
`"matric"`, `"inter_part1"`, `"inter_part2"`

O Level students use `"matric"` pool. A Level students use `"inter_part2"` pool
(per EDUCATION_TO_CURRICULUM mapping in `config.py`).

`"inter_part2"` pool = all `"inter_part1"` questions + `"inter_part2"`-specific questions.
Khuzzaim tags each question accurately — Part 2 student sees Part 1 questions too.
He does not write separate pools. One unified bank, tagged correctly.

**`topic`** — specific sub-topic within the subject. Used for pool analysis and debugging
(e.g., ensuring no single topic dominates a session). Not used in selection logic.

**`difficulty`** — exactly one of: `"easy"`, `"medium"`, `"hard"`.
Session draw per `ASSESSMENT_QUESTIONS_PER_SESSION = {"easy": 3, "medium": 5, "hard": 4}`.
Questions drawn randomly from the correct difficulty band within the correct
`curriculum_level` pool.

**`question`** — full question text. Must be unambiguous and self-contained (no
references to diagrams, tables, or "the passage above").

**`options`** — array of exactly 4 strings. All four options must be plausible.
Avoid obvious distractors — the medium band needs to discriminate ability.

**`correct_index`** — integer 0–3. Index into the `options` array. This is what the
scoring function compares against the student's submitted answer index.

### Pool Size Requirements

| Subject | curriculum_level | Questions needed |
|---|---|---|
| Each of 5 subjects | `matric` | 76 (20 easy, 32 medium, 24 hard) |
| Each of 5 subjects | `inter_part1` | 76 (20 easy, 32 medium, 24 hard) |
| Each of 5 subjects | `inter_part2` (NEW, Part 2-specific only) | ~40 (Khuzzaim judges split) |

Total: 1140 questions (76 per subject × 5 subjects × 3 curriculum levels).

76 questions per subject per level supports up to 6 fresh retake sessions (12 drawn
per session) before any question must repeat. The `inter_part2` runtime draw pool is
a superset: students at this level draw from all `inter_part1`-tagged questions plus
`inter_part2`-tagged questions. However, the file itself contains 76 `inter_part2`-tagged
entries — these cover Part 2-specific syllabus topics (calculus, organic chemistry,
coordinate geometry, etc.). Total file entries: 1140. The ~40 figure in earlier
documentation referred to the approximate count of questions covering purely
Part 2-new topics within the 76, not the total Part 2 entries in the file.

**Do NOT include in questions:**
- `"inter_part1"`: calculus, organic chemistry, coordinate geometry (Part 2 syllabus)
- `"matric"`: any FSc-level content

### Scoring Formula (at endpoint, not in any agent node)

```python
capability_score_per_subject = (correct_answers / total_questions_for_subject) * 100
```

Result stored in `student_profiles.capability_scores` as a float, keyed by subject name.

---

## VALIDATION RULES

### Cross-File Integrity

Run this script before every commit. It checks all five rules:

```python
import json, sys

unis     = json.load(open("universities.json"))
lag      = json.load(open("lag_model.json"))
affinity = json.load(open("affinity_matrix.json"))

# Build lookup sets
lag_field_ids      = {entry["field_id"] for entry in lag}
affinity_field_ids = {entry["field_id"] for entry in affinity}
lag_degree_ids     = set()
for field in lag:
    lag_degree_ids.update(field.get("associated_degrees", []))

errors = []

# Rule 1: Every degree_id in universities.json must be in lag_model associated_degrees
for uni in unis:
    for degree in uni["degrees"]:
        if degree["degree_id"] not in lag_degree_ids:
            errors.append(
                f"ORPHANED degree_id: '{degree['degree_id']}' in {uni['name']} "
                f"has no lag_model entry"
            )

# Rule 2: Every degree field_id must exist in lag_model.json
for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in lag_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in lag_model.json"
            )

# Rule 3: Every degree field_id must exist in affinity_matrix.json
for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in affinity_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in affinity_matrix.json"
            )

# Rule 4: Every field_id in affinity_matrix must exist in lag_model
for entry in affinity:
    if entry["field_id"] not in lag_field_ids:
        errors.append(
            f"ORPHANED affinity field_id: '{entry['field_id']}' "
            f"not found in lag_model.json"
        )

# Rule 5: Every stream in conditionally_eligible_streams must have a matching
#          key in eligibility_notes — FilterNode uses direct access, no .get()
for uni in unis:
    for degree in uni["degrees"]:
        cond  = degree["eligibility"].get("conditionally_eligible_streams", [])
        notes = degree["eligibility"].get("eligibility_notes", {})
        for stream in cond:
            if stream not in notes:
                errors.append(
                    f"MISSING eligibility_note: stream '{stream}' in "
                    f"'{degree['degree_id']}' has no entry in eligibility_notes "
                    f"— FilterNode will crash with KeyError at runtime"
                )

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print("All integrity checks passed.")
```

Run from `backend/app/data/`. Exit code 1 if any errors — CI should block commit.

### Required Data Completeness
Before any degree goes live in `universities.json`:
- All 4 years of `merit_history` populated
- `cutoff_range.min` and `cutoff_range.max` computed from history
- `fee_per_semester` set (not null, not zero)
- `eligibility.fully_eligible_streams` or `conditionally_eligible_streams` populated
- `application_window.website` populated (even if dates are `null`)
- `entry_test` block populated for all universities that require one

Before any field entry goes live in `lag_model.json`:
- `computed.future_value` populated by the compute script
- At least one of `employment_data.rozee_live_count`, `hec_employment_rate`,
  `qualitative_pathway` is non-null
- `data_status` is `"sufficient"` or `"partial"` — never `"insufficient"`

---

## DECISIONS LOCKED IN POINT 4

| Decision | Choice |
|---|---|
| Fee field structure | Flat `fee_per_semester` (integer PKR) — not nested under `financials`. FilterNode reads `degree["fee_per_semester"]` directly per Point 2. |
| Annual fees normalisation | Fazal divides annual fees by 2 at data entry — never stored as annual |
| `location.zone` path | Nested at `degree["location"]["zone"]` — FilterNode reads this exact path |
| `field_id` linking | Universities.json degree has `field_id`; lag_model and affinity_matrix keyed by same `field_id` |
| `degree_id` format | `{university_id}_{canonical_degree_id}` — globally unique |
| `aggregate_formula` location | Per-degree in `universities.json` — different degrees can have different formulas |
| `entry_test` block | Per-degree in `universities.json` — ExplanationNode reads for 65% capability threshold |
| `application_window` | Per-degree in `universities.json` — AnswerNode reads for deadline queries |
| FutureValue computation | `scripts/compute_future_values.py` writes `computed.future_value` — ScoringNode reads this field only |
| All other lag_model fields | Input data for the compute script — never read at runtime by any agent node |
| affinity_matrix RIASEC scores | Scale 1–10 per Holland (1997) — minimum 1 (never 0), maximum 10. Normalised in ScoringNode formula. |
| JSON loading pattern | lag_model and affinity_matrix loaded as arrays, converted to dicts keyed by field_id at startup — ScoringNode uses dict-style access |
| `mandatory_subjects` casing | Title Case (e.g., "Mathematics") — must match `subject_waivers` keys exactly; FilterNode uses the value directly as the waiver lookup key |
| `eligibility_notes` coverage | Every stream in `conditionally_eligible_streams` must have a matching key in `eligibility_notes` — FilterNode uses direct access, no `.get()`, crashes with KeyError if missing |
| Assessment question ID format | `{subject_abbrev}_{level}_{number}` — use abbreviations: math, physics, chem, bio, eng |
| `entry_test` weight field names | Exactly five allowed: `math_weight`, `physics_weight`, `chemistry_weight`, `biology_weight`, `english_weight` — matches capability_scores keys |
| `entry_test` when not required | `{"required": false, "test_name": null, "difficulty": null}` — omit weight fields entirely when false |
| Validation script | Checks five rules: degree_id orphans, field_id in lag_model, field_id in affinity_matrix, affinity field_id in lag_model, eligibility_notes covers all conditionally_eligible_streams. Exit code 1 on failure. |
| Assessment questions authorship | Khuzzaim only |
| `correct_index` | Integer 0–3 — never store the correct answer text directly |
| Orphaned degree rule | No `degree_id` in `universities.json` without a matching `associated_degrees` entry in `lag_model.json` |
| Missing data protocol | `data_status: "insufficient"` excludes field from live recommendations |
| Golden copy | Copy to `backend/app/data/seeds/backup/` before viva — never overwrite |

---

*Point 4 v1.0 — March 2026 (initial lock)*
*Point 4 v1.1 — March 2026 (JSON loading pattern; RIASEC scale 1–10)*
*Point 4 v1.2 — March 2026 (subject_waivers; ID abbreviation table; entry_test null-state)*
*Point 4 v1.3 — March 2026 (validation script 4-rule coverage; entry_test weight fields standardized; cs_weight removed)*
*Point 4 v1.4 — March 2026 (mandatory_subjects Title Case; eligibility_notes coverage rule; validation header corrected)*
*Point 4 v1.5 — March 2026 (affinity_matrix owner corrected to Fazal; validation Rule 5 added for eligibility_notes coverage)*
