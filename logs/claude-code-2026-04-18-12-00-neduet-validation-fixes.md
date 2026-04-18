# Session Log — NED University Data Validation Fixes
## Date: 2026-04-18
## Model: Claude Sonnet 4.6
## Scope: backend/app/data/universities.json
## Source: Data Chat prompt validated against NED UG Prospectus 2025 + NED closing merit lists 2021–2025

---

## STEP 0 — All 33 degree_ids discovered

1.  neduet_bs_cs
2.  neduet_bs_ai
3.  neduet_bs_cybersecurity
4.  neduet_bs_data_science
5.  neduet_bs_animation
6.  neduet_be_software_eng
7.  neduet_be_cise
8.  neduet_be_electrical
9.  neduet_be_electronics
10. neduet_be_mechanical
11. neduet_be_civil
12. neduet_be_biomedical
13. neduet_be_chemical
14. neduet_be_petroleum
15. neduet_be_telecom
16. neduet_be_industrial_mfg
17. neduet_be_automotive
18. neduet_be_metallurgical
19. neduet_be_materials
20. neduet_be_polymer_petrochem
21. neduet_be_urban_planning
22. neduet_be_construction
23. neduet_be_textile_eng
24. neduet_be_food_eng
25. neduet_bs_physics
26. neduet_bs_chemistry        ← actual ID for "BS Industrial Chemistry" (field_id: chemistry_biochemistry)
27. neduet_bs_textile_science
28. neduet_bs_management_sci
29. neduet_bs_economics_finance
30. neduet_bs_comp_finance
31. neduet_bs_dev_studies
32. neduet_bs_english_ling
33. neduet_barch_architecture  ← actual ID for "B Architecture" (not "neduet_b_arch")

**Notes on ID discrepancies vs expected names:**
- `neduet_bs_chemistry` is the actual ID for BS Industrial Chemistry — matched by field_id `chemistry_biochemistry`
- `neduet_barch_architecture` is the actual ID for B Architecture — not `neduet_b_arch`
- `neduet_be_urban_planning` is the actual ID for BE Urban Engineering

---

## CHANGE 1 — Fee corrections applied

**Group A (Standard 59,045 × 8 = 472,360 PKR):** 27 degrees updated
fee_per_semester: 55045 → 59045, estimated_total_cost_pkr: 440360 → 472360
- neduet_be_software_eng, neduet_be_cise, neduet_be_electrical, neduet_be_electronics,
  neduet_be_mechanical, neduet_be_civil, neduet_be_biomedical, neduet_be_chemical,
  neduet_be_petroleum, neduet_be_telecom, neduet_be_industrial_mfg, neduet_be_automotive,
  neduet_be_metallurgical, neduet_be_materials, neduet_be_polymer_petrochem,
  neduet_be_urban_planning, neduet_be_construction, neduet_be_textile_eng,
  neduet_be_food_eng, neduet_bs_physics, neduet_bs_management_sci,
  neduet_bs_economics_finance, neduet_bs_comp_finance, neduet_bs_dev_studies,
  neduet_bs_english_ling
  (note: neduet_bs_chemistry and neduet_bs_textile_science also had 55045 but are in
   Group D and Group A respectively — neduet_bs_textile_science updated here,
   neduet_bs_chemistry handled separately in Group D)

**Group B (BS CT: 64,475 × 8 = 515,800 PKR):** 5 degrees updated
fee_per_semester: 60475 → 64475, estimated_total_cost_pkr: 483800 → 515800
- neduet_bs_cs, neduet_bs_ai, neduet_bs_data_science, neduet_bs_cybersecurity, neduet_bs_animation

**Group C (Architecture: 61,245 × 10 = 612,450 PKR):** 1 degree updated
fee_per_semester: 55045 → 61245, estimated_total_cost_pkr: 550450 → 612450
- neduet_barch_architecture (duration_years already 5 — confirmed ✓)

**Group D (Industrial Chemistry: 60,845 × 8 = 486,760 PKR):** 1 degree updated
fee_per_semester: 55045 → 60845, estimated_total_cost_pkr: 440360 → 486760
- neduet_bs_chemistry

---

## CHANGE 2 — Merit history replaced

### Explicit replacements (6 degrees — descending order → ascending order + values confirmed correct)
All 6 had correct VALUES but wrong ORDER (descending 2024→2021, not ascending 2021→2024).
Replaced with ascending order per schema format.

1. **neduet_bs_cs** — cutoff_range: {min: 83.59, max: 89.45}, band: 5.86
2. **neduet_be_electrical** — cutoff_range: {min: 78.74, max: 85.82}, band: 7.08
3. **neduet_be_electronics** — cutoff_range: {min: 75.25, max: 83.41}, band: 8.16
4. **neduet_be_mechanical** — cutoff_range: {min: 73.06, max: 82.86}, band: 9.80
5. **neduet_be_industrial_mfg** — cutoff_range: {min: 73.00, max: 82.14}, band: 9.14
6. **neduet_be_biomedical** — cutoff_range: {min: 62.77, max: 73.00}, band: 10.23

### Additional shift-error corrections (5 degrees — data clearly wrong by comparison)
7. **neduet_bs_comp_finance** — stored [73.5, 74.7, 75.8, 76.27] → authoritative [72.00, 77.91, 72.73, 72.73]
   cutoff_range: {min: 72.00, max: 77.91}, band: 5.91

8. **neduet_be_urban_planning** — stored [76.3, 77.5, 78.5, 79.09] → authoritative [72.00, 76.45, 63.41, 63.40]
   cutoff_range: {min: 63.40, max: 76.45}, band: 13.05

9. **neduet_bs_dev_studies** — stored [62.0, 63.0, 63.8, 64.27] → authoritative [60.00, 75.00, 60.91, 60.09]
   cutoff_range: {min: 60.00, max: 75.00}, band: 15.00

10. **neduet_bs_chemistry** — stored [70.0, 71.0, 72.0, 72.45] → authoritative [58.00, 73.20, 59.54, 59.34]
    cutoff_range: {min: 58.00, max: 73.20}, band: 15.20

11. **neduet_bs_textile_science** — stored [68.5, 69.5, 70.2, 70.72] → authoritative [59.00, 73.32, 61.05, 61.05]
    cutoff_range: {min: 59.00, max: 73.32}, band: 14.32

### Partial-data degrees — no change (data already correct)
- neduet_bs_data_science: [2022=88.40, 2023=83.73] — already correct, policy_pending_verification=true ✓
- neduet_bs_ai: [2022=88.14, 2023=83.50] — already correct, policy_pending_verification=true ✓
- neduet_bs_cybersecurity: [2022=87.82, 2023=83.23] — already correct, policy_pending_verification=true ✓
- neduet_bs_animation: [2023=82.64] — already correct, policy_pending_verification=true ✓

### Degrees with correct data (not replaced)
neduet_be_chemical, neduet_be_civil, neduet_be_textile_eng, neduet_be_food_eng,
neduet_be_construction, neduet_be_petroleum, neduet_be_urban_planning (pre-correction),
neduet_be_materials, neduet_be_automotive, neduet_be_metallurgical, neduet_be_polymer_petrochem,
neduet_bs_physics, neduet_bs_economics_finance, neduet_bs_english_ling,
neduet_bs_management_sci (no authoritative data in Change 2 list — left as-is)

---

## CHANGE 3 — 2025 merit data appended (29 degrees)

All 29 listed degrees received {"year": 2025, "cutoff": X}.
DO NOT append 2025: neduet_bs_data_science, neduet_bs_ai, neduet_bs_cybersecurity, neduet_bs_animation

**Range updates triggered by 2025 data:**
- neduet_bs_comp_finance: 2025=78.98 > old max 77.91 → new: {min: 72.00, max: 78.98}, band: 6.98
- neduet_be_biomedical: 2025=73.88 > old max 73.00 → new: {min: 62.77, max: 73.88}, band: 11.11
- neduet_bs_dev_studies: 2025=59.22 < old min 60.00 → new: {min: 59.22, max: 75.00}, band: 15.78

---

## CHANGE 4 — data_last_verified updated
"March 2026" → "April 2026" at university level ✓

---

## VERIFICATION RESULTS

1. JSON valid (python -m json.tool passes) ✓
2. No degree has fee_per_semester of 55045 or 60475 ✓
3. neduet_barch_architecture: fee=61245, duration_years=5, total=612450 ✓
4. neduet_bs_chemistry: fee=60845, total=486760 ✓
5. All 5 BS CT degrees: fee=64475 ✓
6. 2025 merit entries: 29 ✓
7. neduet_be_electrical 2022 cutoff = 85.82 ✓
8. neduet_be_electronics 2022 cutoff = 83.41 ✓
9. neduet_bs_cs 2021 cutoff = 83.59 ✓

---

## FLAG FOR WAQAS — test file needs review (DO NOT FIX in this session)

File: `backend/tests/test_filter_node.py`

Two items need updating:
1. Any assertion or comment stating `neduet_bs_cs has fee_per_semester=60475` is now wrong — correct value is **64475**.
2. Test 4 uses `budget=60000` to trigger `over_budget` on `neduet_bs_cs`.
   - The over_budget check still works: 64475 > 60000 ✓
   - BUT: any comment in the test file saying the fee is 60475 needs updating to 64475.

Action required: Waqas to search test_filter_node.py for `60475` and `60,475` and update comments/assertions.

---

## FILES MODIFIED

- `backend/app/data/universities.json` — all changes applied
- `logs/claude-code-2026-04-18-12-00-neduet-validation-fixes.md` — this file
- `logs/README.md` — updated below

## FILES NOT MODIFIED (scope boundary respected)
- lag_model.json — not touched
- affinity_matrix.json — not touched
- Any Python files — not touched
- Any files outside backend/app/data/ and logs/
