# Fazal Data Population Guide
## How to fill universities.json, lag_model.json, and affinity_matrix.json

Read POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md first — it contains the full schema.
This guide shows you the exact workflow for adding entries correctly.

---

## Setup (one time)

Install Python 3.12 and VS Code (same as Waqas does).
Clone the repo. You do NOT need Docker or a virtual environment.
You only work with JSON files and one Python validation script.

Install one package for validation:
```bash
pip install jsonschema
```

---

## The three files and what they are

**universities.json** — the main knowledge base. Every university, every degree program,
every fee, every eligibility rule. FilterNode reads this at request time.

**lag_model.json** — market outlook for each degree field. FutureValue scores,
job market data, growth trajectory. ScoringNode reads this.

**affinity_matrix.json** — RIASEC match scores for each degree field.
How well each dimension (R, I, A, S, E, C) aligns with the field. ScoringNode reads this.

All three use `field_id` as the linking key. A field_id in universities.json must have
a matching entry in BOTH lag_model.json AND affinity_matrix.json before FilterNode
and ScoringNode can process it correctly.

---

## Step 1 — Add a university to universities.json

Open `backend/app/data/universities.json`. It currently contains `[]`.

Replace with a real entry. Here is a complete worked example for NED University:

```json
[
  {
    "university_id": "ned",
    "university_name": "NED University of Engineering and Technology",
    "location": {
      "zone": 3,
      "address": "University Road, Karachi"
    },
    "entry_test": "NET",
    "policy_pending_verification": false,
    "degrees": [
      {
        "degree_id": "ned_bscs",
        "degree_name": "BS Computer Science",
        "field_id": "computer_science",
        "duration_years": 4,
        "fully_eligible_streams": ["Pre-Engineering", "ICS"],
        "conditionally_eligible_streams": ["Pre-Medical"],
        "eligibility_notes": {
          "Pre-Medical": "Bridge course in Mathematics required before admission"
        },
        "mandatory_subjects": ["Mathematics"],
        "subject_waivers": {},
        "min_percentage_hssc": 60.0,
        "cutoff_range": {
          "min": 75.0,
          "max": 92.0,
          "year": 2024
        },
        "fee_per_semester": 27500,
        "total_semesters": 8,
        "seats": 120
      },
      {
        "degree_id": "ned_bsee",
        "degree_name": "BS Electrical Engineering",
        "field_id": "electrical_engineering",
        "duration_years": 4,
        "fully_eligible_streams": ["Pre-Engineering"],
        "conditionally_eligible_streams": [],
        "eligibility_notes": {},
        "mandatory_subjects": ["Mathematics", "Physics"],
        "subject_waivers": {},
        "min_percentage_hssc": 60.0,
        "cutoff_range": {
          "min": 78.0,
          "max": 94.0,
          "year": 2024
        },
        "fee_per_semester": 27500,
        "total_semesters": 8,
        "seats": 90
      }
    ]
  }
]
```

### Field explanations

**university_id** — short lowercase identifier. Use: ned, fast, uok, iqra, bahria, duhs, etc.

**location.zone** — Karachi zone 1-5 (see CLAUDE.md for zone map).
Zone 1: North Karachi, Gulberg. Zone 2: Gulshan, Johar. Zone 3: Defence, Clifton, Saddar.
Zone 4: Malir, Landhi, Korangi. Zone 5: SITE, Orangi, Lyari.

**entry_test** — NET (NED), FAST-NU Test, MDCAT, ECAT, SAT, or None.

**policy_pending_verification** — set true if you are unsure about a rule and need to verify.
FilterNode will attach a soft flag to any degree with this set to true.

**fully_eligible_streams** — students in these streams apply normally. Values from:
"Pre-Engineering", "Pre-Medical", "ICS", "Commerce", "Humanities"

**conditionally_eligible_streams** — eligible but requires something extra (bridge course, etc.)
Always populate eligibility_notes with an explanation for each conditional stream.

**mandatory_subjects** — subjects the student MUST have. If they don't, they are blocked
(unless subject_waivers covers it).

**field_id** — MUST match an entry in lag_model.json and affinity_matrix.json.
Use lowercase with underscores. Standard values:
computer_science, software_engineering, electrical_engineering, mechanical_engineering,
civil_engineering, biomedical_engineering, data_science, cybersecurity, mathematics,
chemistry, physics, medicine, pharmacy, business_administration, accounting, economics,
law, psychology, english_literature, media_studies

**cutoff_range** — use last year's actual cutoff. Check university official admissions page
or Aggregate.pk. min is the lowest aggregate admitted, max is the highest.

**fee_per_semester** — Pakistani Rupees. Check official university fee structure page.

---

## Step 2 — Add matching entries to lag_model.json

For every `field_id` you used in universities.json, add an entry here.

```json
[
  {
    "field_id": "computer_science",
    "field_name": "Computer Science",
    "lag_type": "LEAPFROG",
    "raw": {
      "layer1_job_count": 4200,
      "layer1_source": "Rozee.pk",
      "layer1_date": "2025-01",
      "layer1_normalised": 9.2,
      "layer2_gdp_growth_pct": 8.5,
      "layer2_source": "Pakistan Bureau of Statistics 2024",
      "layer2_normalised": 8.5,
      "layer3_global_trend_score": 9.8,
      "layer3_source": "Google Trends + LinkedIn data",
      "layer3_normalised": 9.8
    },
    "computed": {
      "future_value": 0.0
    },
    "lifecycle_status": "Emerging",
    "risk_factor": 1.2,
    "rozee_live_count": 4200,
    "rozee_last_updated": "2025-01-15",
    "policy_pending_verification": false
  }
]
```

### Field explanations

**lag_type** — determines how much weight goes to global trends vs local jobs.
- LEAPFROG: Pakistan following global trend fast (CS, AI, Software)
- FAST: catching up quickly (Cybersecurity, Data Science, Digital Media)
- MEDIUM: moderate convergence (Cloud, Electrical, Biomedical)
- SLOW: slow convergence (Robotics, IoT, Embedded)
- LOCAL: driven entirely by local economy (Medicine, Law, Civil, Business)

**layer1_job_count** — search Rozee.pk for the field keyword, note the job count.
**layer1_normalised** — scale it 0-10. 1000+ jobs = ~9, 500 jobs = ~6, 100 jobs = ~3.

**layer2_gdp_growth_pct** — find the GDP contribution growth of the relevant sector.
Pakistan Economic Survey (finance.gov.pk) or State Bank annual reports.
Normalise 0-10: 10%+ growth = 9-10, 5-7% = 6-7, 1-3% = 3-4.

**layer3_global_trend_score** — Google Trends score for the field globally + LinkedIn
job posting growth globally. If CS is booming globally: 9-10. If a field is declining: 2-3.

**computed.future_value** — leave as 0.0. Waqas runs `compute_future_values.py`
to fill this in after you populate the raw fields.

**lifecycle_status** — one of: "Emerging", "Peak", "Saturated"
Emerging: growing fast, more demand than supply.
Peak: high demand, competitive salaries, mature market.
Saturated: too many graduates, lower salaries, shrinking demand.

**risk_factor** — float, typically 0.8 to 2.0. Higher = more volatile field.
Stable fields like Medicine: 0.8. Volatile startup fields: 1.8-2.0.

---

## Step 3 — Add matching entries to affinity_matrix.json

For every `field_id`, add a RIASEC affinity entry.

```json
[
  {
    "field_id": "computer_science",
    "field_name": "Computer Science",
    "riasec_affinity": {
      "R": 5,
      "I": 9,
      "A": 4,
      "S": 3,
      "E": 5,
      "C": 7
    },
    "primary_dimensions": ["I", "C"],
    "description": "Highly analytical and structured. Strong Investigative and Conventional fit."
  }
]
```

### RIASEC dimension values (1-10, minimum 1, never 0)

Each value = how strongly this degree field aligns with that RIASEC dimension.
10 = perfect fit. 1 = poor fit but not zero (every dimension has some relevance).

**R (Realistic)** — hands-on, physical, tools, machines.
High R: Mechanical Eng, Civil Eng, Electrical Eng. Low R: Psychology, Literature.

**I (Investigative)** — research, analysis, problem-solving, science.
High I: Computer Science, Medicine, Chemistry, Data Science. Low I: Business Admin.

**A (Artistic)** — creativity, expression, design, open-ended.
High A: Media Studies, Architecture, English Literature. Low A: Accounting, Law.

**S (Social)** — helping, teaching, teamwork, communication.
High S: Medicine, Psychology, Education. Low S: CS/IT technical roles.

**E (Enterprising)** — leadership, persuasion, business, sales.
High E: Business Admin, Law, Marketing. Low E: Pure Sciences.

**C (Conventional)** — structure, data, precision, detail.
High C: Accounting, CS (data/systems), Finance. Low C: Arts, Creative fields.

### Reference values for common fields

| Field | R | I | A | S | E | C |
|---|---|---|---|---|---|---|
| Computer Science | 5 | 9 | 4 | 3 | 5 | 7 |
| Software Engineering | 5 | 8 | 5 | 3 | 5 | 7 |
| Electrical Engineering | 8 | 7 | 3 | 2 | 4 | 6 |
| Mechanical Engineering | 9 | 7 | 3 | 2 | 4 | 5 |
| Civil Engineering | 8 | 6 | 4 | 3 | 5 | 6 |
| Medicine (MBBS) | 4 | 8 | 3 | 9 | 5 | 5 |
| Business Administration | 2 | 4 | 4 | 6 | 9 | 7 |
| Accounting / Finance | 2 | 5 | 2 | 4 | 7 | 9 |
| Psychology | 2 | 7 | 6 | 9 | 5 | 4 |
| Data Science | 4 | 9 | 4 | 3 | 5 | 8 |
| Cybersecurity | 5 | 9 | 3 | 3 | 5 | 7 |
| Law | 2 | 6 | 5 | 7 | 8 | 6 |
| Media / Communications | 3 | 4 | 9 | 7 | 7 | 3 |

---

## Step 4 — Validate your work

After adding entries, run the validation script:
```bash
cd backend
python scripts/seed_db.py
```

This checks that all JSON files are valid and prints record counts.
If it errors, open the file and look for: missing commas, unclosed brackets, wrong field names.

VS Code has a built-in JSON formatter — right-click inside the file → Format Document.
It also highlights JSON errors with red underlines.

---

## Priority order for Sprint 1

Add these first (5 universities, matching lag and affinity entries):
1. NED University
2. FAST-NUCES Karachi
3. University of Karachi (UoK)
4. Aga Khan University (AKU) — Medicine only
5. IBA Karachi — Business programs

For each university: add to universities.json, then immediately add the
matching field_id entries to lag_model.json and affinity_matrix.json.
Run validation after each university — do not wait until all 5 are done.

After Sprint 1 gate: expand to all 20 universities.
