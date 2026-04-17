# Fazal Data Population Guide
## How to populate universities.json, lag_model.json, and affinity_matrix.json

**This guide is derived directly from POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md.**
Point 4 is the single authoritative source. If anything here conflicts with
Point 4, Point 4 wins always. Read Point 4 before starting anything.

The fourth data file — assessment_questions.json — is Khuzzaim's responsibility,
not Fazal's. It is not covered in this guide.

---

## Setup (one time)

Install Python 3.12 and VS Code. Clone the repo. You do NOT need Docker.
You only work with JSON files and the validation script.

```bash
pip install jsonschema
```

---

## The three files and what they are

**universities.json** — the degree catalog. FilterNode reads this to run all 5
constraint checks. AnswerNode reads this for fee queries and deadline questions.

**lag_model.json** — market outlook per degree field. ScoringNode reads only
computed.future_value. AnswerNode reads employment_data and career_paths
when a student asks about jobs or salaries.

**affinity_matrix.json** — RIASEC match scores per degree field. ScoringNode
uses these as vectors in a dot product against the student's RIASEC scores.

---

## Critical linking rules — read before writing a single field

1. Every degree_id in universities.json must appear in lag_model.json's
   associated_degrees array. Violation = validation Rule 1 failure.

2. Every field_id used in a degree must exist in lag_model.json.
   Violation = validation Rule 2 failure.

3. Every field_id used in a degree must exist in affinity_matrix.json.
   Violation = validation Rule 3 failure.

4. Every field_id in affinity_matrix must exist in lag_model.
   Violation = validation Rule 4 failure.

5. Every stream in conditionally_eligible_streams must have a matching key
   in eligibility_notes. FilterNode uses direct key access, no .get().
   Missing key = KeyError crash at runtime. Violation = validation Rule 5 failure.

Run the validation script after every save. Do not commit if it fails.

---

## PART 1 — universities.json

### University-level schema

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
  "degrees": []
}
```

Note on zone: The zone integer appears at both the university top level and inside
location.zone. FilterNode reads degree["location"]["zone"] — the nested path on
the degree object. The university-level zone is for convenience in natural language
responses only. Always set both to the same value.

---

### Locked university_id strings — use EXACTLY these, no variations:

```
neduet, fast_nuces, uok, iba, szabist, ssuet, iqra, bahria,
hamdard, dow, aku, indus_valley, paf_kiet, dadabhoy,
greenwich, cbm, kasbit, newports, khi_univ_arts, khi_univ_science
```

---

### Degree-level schema — complete

```json
{
  "degree_id": "neduet_bs_cs",
  "name": "BS Computer Science",
  "field_id": "computer_science",
  "field_category": "CS",
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

---

### Field-by-field explanations — universities.json degree level

**degree_id**
Format: {university_id}_{canonical_degree_id}. Globally unique.
Examples: neduet_bs_cs, fast_nuces_bs_cs, iba_bba, uok_bs_chemistry.
Use underscores throughout.

**name**
Full display name of the degree. Example: "BS Computer Science".

**field_id**
Links this degree to lag_model.json and affinity_matrix.json. Must be one of
the canonical strings listed below. Multiple degrees at different universities
can share the same field_id.

**field_category**
Broad grouping for display. Exactly one of:
"CS", "Engineering", "Business", "Medical", "Science", "Arts", "Law", "Education".

**eligibility — ALL fields must be nested inside this object**

The entire eligibility block must be nested. FilterNode reads:
degree["eligibility"]["fully_eligible_streams"]
NOT degree["fully_eligible_streams"]
Flat placement will silently break FilterNode.

- fully_eligible_streams: streams that apply directly, no conditions.
  Values: "Pre-Engineering", "Pre-Medical", "ICS", "Commerce", "Humanities".

- conditionally_eligible_streams: streams eligible with extra requirements.
  FilterNode marks these as eligibility_tier: "likely".

- eligibility_notes: CRASH RISK. FilterNode accesses this as
  degree["eligibility"]["eligibility_notes"][stream] — direct key access, no .get().
  Every stream in conditionally_eligible_streams must have a matching key here.
  Missing key = KeyError at runtime. Validation Rule 5 checks this.

- mandatory_subjects: subjects the student must have. MUST BE TITLE CASE:
  "Mathematics", "Physics", "Chemistry", "Biology", "English".
  FilterNode uses these strings directly as keys in subject_waivers lookup with
  no case conversion. Wrong casing = silent failure.

- min_percentage_hssc: hard floor for application. Float, e.g. 60.0.
  FilterNode excludes any student aggregate below this.

- policy_pending_verification: true if eligibility rules are unconfirmed.
  FilterNode adds a policy_unconfirmed soft flag.

- subject_waivers: dict keyed by subject name (Title Case, matching mandatory_subjects).
  For degrees with no waivers: {}. Never omit the field — always include it, even empty.

**aggregate_formula**
How this university computes the student's admission aggregate. FilterNode's
calculate_aggregate() helper reads this object to compute each student's specific
aggregate for this degree before comparing against cutoff_range.
Different degrees at the same university can have different formulas.
- matric_weight, inter_weight, entry_test_weight must sum to 1.0.
- subject_weights: multipliers applied to Inter subject marks. "other" covers
  subjects not explicitly listed.

entry_test_weight — must be 0.0 (not omitted, not null) for degrees with no entry test. FilterNode's calculate_estimated_merit() reads this field directly from aggregate_formula to determine whether to build an entry test proxy. If omitted, it defaults to 0.0 via .get() which is safe, but explicit 0.0 is required for clarity and validation script checks.

**fee_per_semester**
Integer, in PKR. FilterNode reads this directly as degree["fee_per_semester"].
If a university publishes annual fees, divide by 2 before storing here.
Never store as annual. Never nest inside another object.

**admission_fee_pkr**
One-time admission fee. Display only.

**estimated_total_cost_pkr**
Full programme cost estimate. Display only.

**merit_history**
Historical merit cutoffs. Array of {"year": ..., "cutoff": ...} objects.
At least 3 years required before a degree can go live. 4 years preferred.
cutoff_range.min and cutoff_range.max are derived from this history.

**cutoff_range**
min = lowest cutoff across merit_history. max = highest.
Exactly two fields: min and max. No year field inside cutoff_range.

**confidence_band**
max minus min from merit_history. Display only. Not in FilterNode logic.

**location — per-degree object**
```json
"location": {
  "area": "University Road, Karachi",
  "zone": 3
}
```
FilterNode reads degree["location"]["zone"] — the nested path on the degree.
NOT the university-level zone field.

**entry_test — per-degree object, NOT at university level**

For Engineering and CS (ECAT-style):
```json
{
  "required": true,
  "test_name": "ECAT",
  "math_weight": 0.40,
  "physics_weight": 0.30,
  "english_weight": 0.15,
  "chemistry_weight": 0.15,
  "difficulty": "high"
}
```

For Medical (MDCAT-style):
```json
{
  "required": true,
  "test_name": "MDCAT",
  "biology_weight": 0.40,
  "chemistry_weight": 0.30,
  "physics_weight": 0.20,
  "english_weight": 0.10,
  "difficulty": "high"
}
```

For degrees with no entry test (many Business, Arts, Social Science programs):
```json
{
  "required": false,
  "test_name": null,
  "difficulty": null
}
```
When required is false, omit ALL weight fields entirely. Do not include them as null.

Weight field names — exactly these five, no others, no variations:
math_weight, physics_weight, chemistry_weight, biology_weight, english_weight

All weight fields present must sum to 1.0. ExplanationNode reads these by exact
name. Any variation (maths_weight, bio_weight, cs_weight) silently fails.

**application_window**
AnswerNode reads this for deadline queries. website must always be populated.
Set data_cycle to the year the data reflects.

For universities with multiple intakes, set multiple_rounds: true and populate round_details:
```json
"round_details": [
  {"round": "Fall 2025", "open": "June 2025", "close": "August 2025"},
  {"round": "Spring 2026", "open": "November 2025", "close": "January 2026"}
]
```
When multiple_rounds is false, set round_details: null.

---

### Canonical field_id values — use EXACTLY these strings, no others:

```
computer_science, artificial_intelligence, software_engineering,
cybersecurity, data_science, digital_media, electrical_engineering,
mechanical_engineering, civil_engineering, biomedical_engineering,
electronics_engineering, robotics_iot, medicine_mbbs, dentistry_bds,
pharmacy, mathematics, physics, chemistry_biochemistry, architecture,
fine_arts, psychology, social_work, education_bed, business_bba,
economics, finance_accounting, law_llb, mass_communication,
agriculture, veterinary_science
```

These are the only valid values. english_literature, medicine, business_administration,
accounting, law, media_studies do not exist in the canonical list.

---

### Adding a new canonical field_id

When a university offers a program not in the canonical list above
(e.g. petroleum_engineering, automotive_engineering), follow these
steps exactly. Do not skip or reorder them.

**Step 1 — Choose the name.**
Use snake_case. Use the full field name. No abbreviations.
Follow the existing pattern: `petroleum_engineering` not `petrol_eng`.
Check the canonical list to confirm no overlap or near-duplicate exists.

**Step 2 — Flag to Waqas immediately.**
New field_ids must be added to the canonical list in DATA_CHAT_INSTRUCTIONS.md,
POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md, and CLAUDE.md. Fazal does not update
these files directly. Message Waqas: "New field_id needed: [name]. Adding
to universities.json, lag_model.json, affinity_matrix.json in this commit."
Waqas produces the update blocks and applies them.

**Step 3 — Add to lag_model.json immediately.**
In the same commit as the university entry that uses this new field_id.
Not in a later commit. Populate all raw data fields per Part 2 of this guide.
Leave computed.future_value as 0.0 — Waqas runs the compute script.
Choose lag_category from the table in Part 2.
Add every degree_id from universities.json that uses this field_id to the
associated_degrees array.

**Step 4 — Add to affinity_matrix.json immediately.**
Same commit. Use the RIASEC reference table in Part 3 as a starting point.
Compare to the closest existing field and adjust by 1-2 points if your
research justifies it. Set social_acceptability_tier and write prestige_note.
Never enter 0 for any RIASEC dimension — minimum is 1.

**Step 5 — Run validation script.**
```bash
cd backend/app/data
python validate.py
```
All five rules must pass (exit code 0) before committing.
Exit code 1 means errors must be fixed first — never commit a failing state.

**The three-file rule:** universities.json, lag_model.json, and
affinity_matrix.json must always be committed together when a new
field_id is introduced. A new field_id in universities.json without
matching entries in the other two files will fail validation and crash
the pipeline at runtime.

### Karachi transport zones:

| Zone | Areas |
|---|---|
| 1 | North Karachi, Gulberg, New Karachi, Surjani |
| 2 | Gulshan-e-Iqbal, Johar, Nazimabad, North Nazimabad |
| 3 | Defence, Clifton, Saddar, PECHS, Bahadurabad |
| 4 | Malir, Landhi, Korangi, Shah Faisal |
| 5 | SITE, Orangi, Baldia, Lyari |

---

## PART 2 — lag_model.json

### Complete per-field schema

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
    "derivation": "pakistan_now growth rate + world_future signal adjusted for lag"
  },

  "lag_parameters": {
    "lag_years": 2.0,
    "arrival_confidence": "high",
    "cultural_barrier": false,
    "societal_barrier": false,
    "notes": "Banking/telecom/government sectors driving strong domestic demand already."
  },

  "computed": {
    "future_value": 0.0,
    "last_computed": null
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

---

### Field-by-field explanations — lag_model.json

**field_id**
Must match the field_id used in universities.json and affinity_matrix.json.
Use only the canonical strings from the list in Part 1.

**field_name**
Human-readable name. Can include slash variants.

**associated_degrees — CRITICAL FOR VALIDATION**
Array of every degree_id string from universities.json that uses this field_id.
When you add a new degree to universities.json that uses field_id: "cybersecurity",
you must add that degree's degree_id to this array too.
Validation Rule 1 fails for any degree_id not listed here.

**lag_category**
Exactly one of: LEAPFROG, FAST, MEDIUM, SLOW, LOCAL.
Field name is lag_category — NOT lag_type.

| Category | Pakistan follows global | Typical fields |
|---|---|---|
| LEAPFROG | Very fast 1-2 years | CS, AI, Software Engineering |
| FAST | Fast 2-3 years | Cybersecurity, Data Science, Digital Media |
| MEDIUM | Moderate 3-5 years | Cloud, Electrical, Biomedical Engineering |
| SLOW | Slow 5-8 years | Robotics, IoT, Embedded |
| LOCAL | No global lag applies | Medicine, Law, Civil Engineering, Business |

**lifecycle_status**
Exactly one of: "Emerging", "Peak", "Stable", "Declining".
"Saturated" is NOT a valid value.

**risk_factor**
Exactly one of: "Low", "Medium", "High".
This is a string — NOT a float like 1.2.

**risk_reasoning**
One or two sentences explaining why the risk level is what it is.

**outsourcing_applicable**
true for fields where Pakistani graduates can work remotely for foreign companies.
false for LOCAL fields: Medicine, Law, Civil Engineering, Education.

**infrastructure_constrained**
true when field growth in Pakistan is limited by physical infrastructure.
Example: Robotics needs factory automation. false for most software fields.

**constraint_note**
Short explanation when infrastructure_constrained is true.
Empty string "" when false — never omit the field.

**pakistan_now — Layer 1 data**
Search Rozee.pk for the field keyword and note the current job count.
- job_postings_monthly: integer, current Rozee.pk live count.
- yoy_growth_rate: decimal. 0.38 means 38% year-on-year growth.
- sources: array of strings where you got the data.

**world_now — Layer 2 data**
Current global market evidence from LinkedIn Talent Trends, BLS, or equivalent.
- us_yoy_growth_rate, uk_yoy_growth_rate, uae_yoy_growth_rate: decimals.
  Include UAE data where Pakistani diaspora employment is relevant.
- sources: where you got this data.

**world_future — Layer 3 data**
Forward-looking global projections. Primary source: BLS Occupational Outlook
Handbook at https://www.bls.gov/ooh/. Find the closest SOC code.
- us_bls_4yr_projected_growth: decimal projected growth over 4 years.
- bls_soc_code: the SOC code used.
- projection_basis: citation string.

**pakistan_future — derived projection**
- projected_4yr_growth: your estimate for Pakistan over 4 years. Use
  pakistan_now.yoy_growth_rate as base. Adjust upward for LEAPFROG and FAST
  fields that are known to be accelerating.
- derivation: one sentence explaining how you derived the number.

**lag_parameters**
- lag_years: float, how many years behind the global trend Pakistan currently is.
- arrival_confidence: one of "high", "medium", "low".
  high = the global trend has clearly arrived (CS, Software).
  medium = arriving, mixed signals.
  low = uncertain if and when it will arrive.
- cultural_barrier: true if there is cultural resistance in Pakistani families.
- societal_barrier: true if broader societal factors limit uptake.
- notes: free text explanation of the lag dynamics.

**computed**
Leave as "future_value": 0.0 and "last_computed": null.
Waqas runs scripts/compute_future_values.py which writes both fields.
Never manually edit future_value.

**employment_data**
Rozee data goes HERE — not at the top level of the entry.
- rozee_live_count: integer, current live job count from Rozee.pk.
- rozee_last_updated: date string "YYYY-MM-DD".
- hec_employment_rate: float 0.0-1.0 from HEC Graduate Tracer Study. null if not available.
- qualitative_pathway: written description of career pathway for niche fields. null if not needed.
- data_source_used: one of "rozee_live", "hec_tracer", "qualitative", "proxy_adjacent".
- data_status: one of "sufficient", "partial", "insufficient".

A field must NEVER go live with data_status: "insufficient".
At least one of rozee_live_count, hec_employment_rate, or qualitative_pathway
must be non-null. If all three are null, set data_status: "insufficient" and
find data before committing.

Missing data for niche fields (Fine Arts, Social Work, NGO, Education):
- Rozee.pk may have zero listings — this is expected for these fields.
- Use hec_employment_rate from the HEC Graduate Tracer Study if available.
- Use qualitative_pathway to write a description of typical career paths.
- For NGO and Social Work fields: check BrightSpyre.com as an alternative source.
- Set data_source_used: "qualitative" and data_status: "partial" for these fields.

**career_paths**
AnswerNode reads this for market queries from students.
- entry_level_title: first job title most graduates take.
- typical_first_role_salary_pkr: string range. Example: "60,000 – 90,000/month".
  Always a range string, never a precise number.
- common_sectors: array of 3-5 sectors where graduates typically work.

---

**Migration context for Gulf-pathway fields:**
For fields where physical migration to Gulf countries is a well-documented
career pathway — specifically petroleum_engineering, medicine_mbbs, and
civil_engineering — populate career_paths as follows:

- common_sectors: include Gulf employers alongside domestic ones.
  Example for petroleum_engineering:
  ["OGDCL", "PPL", "Sui Networks", "Saudi Aramco", "ADNOC", "Kuwait Oil Company"]
- qualitative_pathway: write one sentence describing the migration pathway.
  Example: "Pakistani petroleum engineers are regularly recruited by Saudi
  Aramco, ADNOC, and Kuwait Oil Company for upstream operations; Gulf
  employment is a primary career route for this field."
- data_source_used: "qualitative"
- data_status: "partial" (Rozee live count captures domestic demand only;
  Gulf demand is described qualitatively)

This does not change the FutureValue formula. It ensures AnswerNode gives
a complete picture when a student asks about career prospects in these fields.
For all other fields, leave qualitative_pathway as null.

---

### LOCAL category — formula difference

For lag_category: "LOCAL" fields (Medicine, Law, Civil Engineering, Business):
- Layer 3 weight is 0.0 in the compute script — world_future data has no weight.
- FutureValue is driven only by Layer 1 (local jobs) and Layer 2 (local GDP data).
- outsourcing_applicable must be false for all LOCAL fields.
- world_future and world_now may still be populated (Gulf data is useful for
  Civil Engineering and Medicine) but their weight in the formula is zero.
- This is handled automatically by the compute script. Just set lag_category: "LOCAL".

---

## PART 3 — affinity_matrix.json

### Complete per-field schema

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

---

### Field-by-field explanations — affinity_matrix.json

**riasec_affinity**
Integer scores 1-10 for each of the six RIASEC dimensions.
Minimum is 1, never 0. A score of 1 means the dimension is almost entirely
absent. A score of 10 means it is strongly dominant.

Meaning of each dimension:
- R Realistic: hands-on, physical, tools, machines, outdoor work
- I Investigative: analytical, research, problem-solving, intellectual
- A Artistic: creative, expressive, open-ended, aesthetic
- S Social: helping others, teaching, interpersonal, community
- E Enterprising: leadership, persuasion, business, sales, management
- C Conventional: organised, systematic, detail-oriented, structured data

ScoringNode computes:
raw_match = sum(student[dim] * affinity[dim] for each dimension)
theoretical_max = sum(student_score * 10 for each dimension)
match_score_normalised = raw_match / theoretical_max

The formula normalises for students who score high across all dimensions.
Scores reflect alignment, not absolute magnitude.

**riasec_description**
Field name is riasec_description — NOT description.
Plain English description of the dominant RIASEC profile for this field.
ExplanationNode uses this to explain RIASEC match to the student in natural language.
One to two sentences. Mention the top 2-3 dominant dimensions.

**social_acceptability_tier**
NOT optional. Exactly one of: "high", "moderate", "lower".

| Tier | Fields |
|---|---|
| "high" | MBBS, all Engineering, Computer Science, BBA at top institutions |
| "moderate" | Science degrees, Psychology, Mass Communication, Architecture, Pharmacy |
| "lower" | Fine Arts, Social Work, Education B.Ed |

ExplanationNode adjusts its tone based on this value. For "lower" tier fields it
phrases recommendations more carefully given Pakistani family expectations.

**prestige_note**
Optional free text. One or two sentences about how this field is perceived in
Pakistan's job market. ExplanationNode may use this. Keep neutral and factual.

Fields that must NOT appear in affinity_matrix entries:
- description: wrong field name, use riasec_description
- primary_dimensions: not in schema
- field_name: not in schema

---

### Reference RIASEC values for all canonical fields:

| field_id | R | I | A | S | E | C |
|---|---|---|---|---|---|---|
| computer_science | 5 | 9 | 4 | 3 | 5 | 7 |
| artificial_intelligence | 4 | 10 | 5 | 3 | 4 | 7 |
| software_engineering | 5 | 8 | 5 | 3 | 5 | 7 |
| cybersecurity | 5 | 9 | 2 | 4 | 5 | 8 |
| data_science | 4 | 9 | 4 | 3 | 5 | 8 |
| digital_media | 3 | 5 | 9 | 6 | 6 | 4 |
| electrical_engineering | 8 | 7 | 3 | 2 | 4 | 6 |
| mechanical_engineering | 9 | 7 | 3 | 2 | 4 | 5 |
| civil_engineering | 8 | 6 | 4 | 3 | 5 | 6 |
| biomedical_engineering | 7 | 8 | 3 | 5 | 4 | 6 |
| electronics_engineering | 8 | 7 | 3 | 2 | 4 | 6 |
| robotics_iot | 8 | 8 | 4 | 2 | 4 | 6 |
| medicine_mbbs | 4 | 8 | 3 | 9 | 5 | 5 |
| dentistry_bds | 5 | 7 | 4 | 8 | 4 | 5 |
| pharmacy | 4 | 7 | 3 | 7 | 4 | 7 |
| mathematics | 3 | 10 | 5 | 3 | 3 | 8 |
| physics | 5 | 10 | 4 | 3 | 3 | 7 |
| chemistry_biochemistry | 5 | 9 | 3 | 4 | 3 | 7 |
| architecture | 7 | 6 | 9 | 4 | 5 | 6 |
| fine_arts | 2 | 4 | 10 | 6 | 5 | 3 |
| psychology | 2 | 7 | 6 | 9 | 5 | 4 |
| social_work | 1 | 4 | 5 | 10 | 5 | 4 |
| education_bed | 2 | 5 | 6 | 9 | 5 | 5 |
| business_bba | 2 | 4 | 4 | 6 | 9 | 7 |
| economics | 3 | 8 | 4 | 5 | 7 | 7 |
| finance_accounting | 2 | 5 | 2 | 4 | 7 | 9 |
| law_llb | 2 | 6 | 5 | 7 | 8 | 6 |
| mass_communication | 3 | 4 | 9 | 7 | 7 | 3 |
| agriculture | 8 | 6 | 3 | 5 | 4 | 5 |
| veterinary_science | 7 | 7 | 3 | 7 | 3 | 5 |

These values are starting points based on Holland (1997). Adjust by 1-2 points
if your research on Pakistani market context suggests a different emphasis.

---

## PART 4 — Validation Script

Save this as validate.py in backend/app/data/ and run it after every change.

```python
import json, sys

unis     = json.load(open("universities.json"))
lag      = json.load(open("lag_model.json"))
affinity = json.load(open("affinity_matrix.json"))

lag_field_ids      = {entry["field_id"] for entry in lag}
affinity_field_ids = {entry["field_id"] for entry in affinity}
lag_degree_ids     = set()
for field in lag:
    lag_degree_ids.update(field.get("associated_degrees", []))

errors = []

for uni in unis:
    for degree in uni["degrees"]:
        if degree["degree_id"] not in lag_degree_ids:
            errors.append(
                f"ORPHANED degree_id: '{degree['degree_id']}' in {uni['name']} "
                f"has no lag_model entry"
            )

for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in lag_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in lag_model.json"
            )

for uni in unis:
    for degree in uni["degrees"]:
        if degree["field_id"] not in affinity_field_ids:
            errors.append(
                f"MISSING field_id: '{degree['field_id']}' on degree "
                f"'{degree['degree_id']}' not found in affinity_matrix.json"
            )

for entry in affinity:
    if entry["field_id"] not in lag_field_ids:
        errors.append(
            f"ORPHANED affinity field_id: '{entry['field_id']}' "
            f"not found in lag_model.json"
        )

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

Run from backend/app/data/:
```bash
cd backend/app/data
python validate.py
```

Exit code 0 = all checks pass — safe to commit.
Exit code 1 = listed errors must be fixed before committing.

---

## PART 5 — Data completeness gates

Before any degree goes live in universities.json:
- merit_history has at least 3 years (4 preferred)
- cutoff_range.min and cutoff_range.max computed from history
- fee_per_semester is set — not null, not zero
- Either fully_eligible_streams or conditionally_eligible_streams has values
- application_window.website is populated even if dates are null
- entry_test block is populated for all universities that require one

Before any field entry goes live in lag_model.json:
- computed.future_value has been populated by Waqas running the compute script
- At least one of employment_data.rozee_live_count, hec_employment_rate,
  or qualitative_pathway is non-null
- data_status is "sufficient" or "partial" — never "insufficient"

---

## PART 6 — Workflow

For each university, always do all three files together — never batch:

1. Add the university entry to universities.json with all required fields
2. For each degree in that university, add the degree_id to the matching
   field_id entry's associated_degrees array in lag_model.json.
   If that field_id does not yet have an entry in lag_model, create it now.
3. For each new field_id in lag_model, add a matching entry to affinity_matrix.json
4. Run python validate.py — must return "All integrity checks passed."
5. Only then commit and move to the next university

Sprint 1 priority — 5 universities:
1. NED University (neduet) — Engineering and CS programs
2. FAST-NUCES Karachi (fast_nuces) — CS and Software Engineering
3. University of Karachi (uok) — Sciences, Business, Arts
4. Aga Khan University (aku) — Medicine programs only
5. IBA Karachi (iba) — BBA and Economics only

Sprint 2 — expand to all 20 universities.

Before viva:
Run compute_future_values.py one final time to ensure all FutureValues are current.
Copy all three files to backend/app/data/seeds/backup/ — the Golden Copy.
Never overwrite files in that backup folder.
