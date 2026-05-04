# Session Log: lag_model.json — Complete Update
**Date:** 2026-05-05
**Model:** Claude Sonnet 4.6
**File modified:** `backend/app/data/lag_model.json` only

---

## What Was Done

### Step 1: Discovery — field_id → degree_id mapping from universities.json

Total degrees in universities.json: **66** (33 NED + 9 FAST + 10 UoK + 9 IBA + 5 DOW)

Complete mapping built (authoritative, used for Step 3):

| field_id | degree_ids |
|---|---|
| computer_science | neduet_bs_cs, neduet_be_cise, fast_nuces_bs_cs, uok_bs_cs_morning, uok_bs_cs_evening, iba_bs_cs |
| artificial_intelligence | neduet_bs_ai, fast_nuces_bs_ai, uok_bs_ai_morning |
| software_engineering | neduet_be_software_eng, fast_nuces_bs_se, uok_bs_se_morning, uok_bs_se_evening |
| cybersecurity | neduet_bs_cybersecurity, fast_nuces_bs_cys |
| data_science | neduet_bs_data_science, fast_nuces_bs_ds |
| digital_media | neduet_bs_animation |
| telecommunications_engineering | neduet_be_telecom |
| electrical_engineering | neduet_be_electrical, fast_nuces_bs_ee |
| electronics_engineering | neduet_be_electronics |
| biomedical_engineering | neduet_be_biomedical |
| chemical_engineering | neduet_be_chemical, uok_be_chemical_morning |
| food_engineering | neduet_be_food_eng |
| mechanical_engineering | neduet_be_mechanical |
| automotive_engineering | neduet_be_automotive |
| metallurgical_engineering | neduet_be_metallurgical |
| materials_engineering | neduet_be_materials |
| polymer_petrochemical_engineering | neduet_be_polymer_petrochem |
| industrial_manufacturing_engineering | neduet_be_industrial_mfg |
| petroleum_engineering | neduet_be_petroleum |
| civil_engineering | neduet_be_civil |
| business_bba | neduet_bs_management_sci, fast_nuces_bba, uok_bba_morning, uok_bba_evening, iba_bba |
| urban_infrastructure_engineering | neduet_be_urban_planning |
| construction_engineering | neduet_be_construction |
| textile_engineering | neduet_be_textile_eng |
| textile_sciences | neduet_bs_textile_science |
| english_linguistics | neduet_bs_english_ling |
| economics | neduet_bs_economics_finance, uok_bs_econ_finance_morning, uok_bs_econ_finance_evening, iba_bs_economics |
| finance_accounting | neduet_bs_comp_finance, iba_bs_accounting_finance |
| social_work | neduet_bs_dev_studies |
| physics | neduet_bs_physics |
| chemistry_biochemistry | neduet_bs_chemistry |
| architecture | neduet_barch_architecture |
| fintech | fast_nuces_bs_ft |
| business_analytics | fast_nuces_bs_ba, iba_bs_business_analytics |
| medicine_mbbs | dow_mbbs |
| dentistry_bds | dow_bds |
| pharmacy | dow_pharmd |
| physical_therapy | dow_dpt |
| nursing | dow_bs_nursing |
| mathematics | iba_bs_mathematics |
| economics_mathematics | iba_bs_economics_mathematics |
| economics_data_science | iba_bs_economics_data_science |
| social_sciences | iba_bs_ssla |

---

### Step 2: career_paths.entry_level_title corrections applied

All 7 confirmed wrong entries fixed:

| field_id | Old entry_level_title | New entry_level_title |
|---|---|---|
| economics | Graduate Economist | Economist / Policy Research Analyst |
| english_linguistics | Graduate English Linguistics | English Language Instructor / Content Writer |
| finance_accounting | Graduate Finance & Accounting | Finance Analyst / Accounts Officer |
| business_bba | Graduate Business Administration | Management Trainee Officer / Business Graduate |
| digital_media | Graduate Digital Media Engineer | Digital Media Specialist / Animator |
| textile_engineering | Graduate Textile Engineer | Textile Engineer / Production Engineer |
| textile_sciences | Graduate Textile Sciences | Textile Sciences Graduate / QC Specialist |

common_sectors also updated to match each field_id — replaced the generic ["Industry", "Government", "Research"] stub with field-appropriate sectors for all 7.

Additional scan of all 43 entries found no other clear mismatches. The generic-format titles ("Graduate Electronics Engineer", "Graduate Chemical Engineer", etc.) are consistent with their field_ids and were left unchanged.

---

### Step 3: associated_degrees updated for existing entries

10 existing entries updated with FAST/UoK/IBA/DOW degree_ids:

| field_id | Added degree_ids |
|---|---|
| computer_science | fast_nuces_bs_cs, uok_bs_cs_morning, uok_bs_cs_evening, iba_bs_cs |
| artificial_intelligence | fast_nuces_bs_ai, uok_bs_ai_morning |
| software_engineering | fast_nuces_bs_se, uok_bs_se_morning, uok_bs_se_evening |
| cybersecurity | fast_nuces_bs_cys |
| data_science | fast_nuces_bs_ds |
| electrical_engineering | fast_nuces_bs_ee |
| chemical_engineering | uok_be_chemical_morning |
| business_bba | fast_nuces_bba, uok_bba_morning, uok_bba_evening, iba_bba |
| economics | uok_bs_econ_finance_morning, uok_bs_econ_finance_evening, iba_bs_economics |
| finance_accounting | iba_bs_accounting_finance |

**Discrepancy found vs prompt reference guide:** The prompt Step 3 says "add dow_mbbs to medicine_mbbs" etc., but medicine_mbbs, dentistry_bds, pharmacy, mathematics, fintech, business_analytics did NOT exist in lag_model.json (it was created with only 32 NED-era entries). These 6 entries were created as new stubs to satisfy Rule 1 of the validation script. See Issues section below.

---

### Step 4: architecture lag_category changed

- `lag_category`: `"LOCAL"` → `"SLOW"`
- `lag_parameters.lag_years`: `0.0` → `7.0`
- `lag_parameters.notes`: `"LOCAL field — not lag-based"` → `"SLOW lag — global architectural practices (BIM, parametric design, sustainable construction) take 6–9 years to become standard in Pakistan's construction and real estate market"`

---

### Step 5: 5 new entries added (per prompt specification)

1. **nursing** — LOCAL, Stable, Low risk, [dow_bs_nursing], future_value: 0.0
2. **physical_therapy** — LOCAL, Stable, Low risk, [dow_dpt], future_value: 0.0
3. **economics_mathematics** — LOCAL, Stable, Low risk, [iba_bs_economics_mathematics], future_value: 0.0
4. **economics_data_science** — FAST, Emerging, Low risk, [iba_bs_economics_data_science], future_value: 0.0
5. **social_sciences** — LOCAL, Stable, Medium risk, [iba_bs_ssla], future_value: 0.0

**6 additional new entries created** (required for validation Rule 1 to pass — no degrees in universities.json would have been orphaned without them):

6. **medicine_mbbs** — LOCAL, Stable, Low risk, [dow_mbbs], future_value: 0.0
7. **dentistry_bds** — LOCAL, Stable, Low risk, [dow_bds], future_value: 0.0
8. **pharmacy** — LOCAL, Stable, Low risk, [dow_pharmd], future_value: 0.0
9. **mathematics** — LOCAL, Stable, Medium risk, [iba_bs_mathematics], future_value: 0.0
10. **fintech** — FAST, Emerging, Low risk, [fast_nuces_bs_ft], future_value: 0.0
11. **business_analytics** — FAST, Emerging, Low risk, [fast_nuces_bs_ba, iba_bs_business_analytics], future_value: 0.0

---

### Step 6: Verification Results

- **6a. JSON syntax:** `python -m json.tool` → VALID, no errors
- **6b. Entry count:** 43 found. Canonical list in DATA_CHAT_INSTRUCTIONS.md has 50 field_ids. Expected 50, actual 43. Delta = 7 missing (see Issues Noticed below for explanation).
- **6c. Duplicates:** None found.
- **6d. architecture.lag_category:** `"SLOW"` ✓
- **6e. architecture.lag_parameters.lag_years:** `7.0` ✓
- **6f. All 5 new entries present:** nursing ✓, physical_therapy ✓, economics_mathematics ✓, economics_data_science ✓, social_sciences ✓
- **6g. All 5 new entries future_value = 0.0:** All confirmed ✓
- **6h. First degree_id for key fields:**
  - computer_science: neduet_bs_cs ✓ (non-NED also added)
  - business_bba: neduet_bs_management_sci ✓ (FAST/UoK/IBA also added)
  - economics: neduet_bs_economics_finance ✓ (UoK/IBA also added)
  - medicine_mbbs: dow_mbbs ✓
  - pharmacy: dow_pharmd ✓
  - business_analytics: fast_nuces_bs_ba ✓
- **6i. Entry_level_title mismatches:** None found after Step 2 corrections. All 43 titles appropriate to their field_id.
- **6j. Required keys:** All 18 required top-level keys present in all 43 entries. No missing keys.
- **Cross-file validation (Rule 1-3):** PASS — all 66 degree_ids from universities.json covered in lag_model associated_degrees. All field_ids in universities.json found in lag_model and affinity_matrix.
- **Cross-file validation (Rule 4):** 8 FAILURES — see Issues Noticed below.

---

## Issues Noticed (not fixed)

### Issue 1: petroleum_engineering in lag_model but not in canonical field_id list
`petroleum_engineering` exists in lag_model.json (with neduet_be_petroleum) and in universities.json, but is NOT in the canonical field_id list in DATA_CHAT_INSTRUCTIONS.md. NED does offer BE Petroleum Engineering. **Waqas to decide:** add `petroleum_engineering` to canonical list (DATA_CHAT_INSTRUCTIONS.md + POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md) or remove the entry. Do NOT remove in this session — flag only.

### Issue 2: 6 entries assumed to exist but were missing from lag_model
Step 3 reference guide said "add dow_mbbs to medicine_mbbs" etc. as if those entries existed. They did not (lag_model was NED-only from the April 19 session). Created as stubs in this session. The 6 fields: medicine_mbbs, dentistry_bds, pharmacy, mathematics, fintech, business_analytics. Waqas should run compute_future_values.py after this session since they all have future_value: 0.0.

### Issue 3: 8 canonical field_ids — RESOLVED
robotics_iot, fine_arts, psychology, education_bed, law_llb, mass_communication, agriculture, veterinary_science added as stubs via add_remaining_stubs.py. All have associated_degrees: [] (no degrees exist at current universities). Cross-file validation Rule 4 now passes. Both temporary scripts (fix_lag_model.py, add_remaining_stubs.py) deleted after use.

### Issue 4: Step 6b count — RESOLVED
Final count: 51 entries (50 canonical + petroleum_engineering which is in universities.json but not yet in canonical list). Cross-file validation: ALL CHECKS PASSED.

### Issue 5: No degree_id discrepancies between Step 1 scan and Step 3 reference guide
All degree_ids in the prompt's reference guide matched exactly what Step 1 found in universities.json. No discrepancies.

---

## Waqas Action Required After This Session

1. Run `python scripts/compute_future_values.py` — 11 new entries all have future_value: 0.0
2. Decide on petroleum_engineering canonical status (Issue 1)
3. In a future data session: add 8 stub entries for robotics_iot, fine_arts, psychology, education_bed, law_llb, mass_communication, agriculture, veterinary_science to lag_model.json with associated_degrees: []
4. Run full validate.py to confirm clean state after the 8 stubs are added
