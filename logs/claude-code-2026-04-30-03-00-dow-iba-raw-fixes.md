# Session Log — DOW and IBA Raw File Fixes
**File:** `logs/claude-code-2026-04-30-03-00-dow-iba-raw-fixes.md`
**Date:** 2026-04-30
**Model:** Claude Sonnet 4.6
**Task:** Fix estimated_total_cost_pkr (DOW), fee structure (IBA), and data quality issues across both raw files.

---

## Files Read (in order)

1. `logs/README.md`
2. `CLAUDE.md`
3. `docs/00_architecture/DATA_CHAT_INSTRUCTIONS.md`
4. `docs/00_architecture/POINT_4_JSON_KNOWLEDGE_BASE_v1_5.md`
5. `backend/app/data/raw/dow_university_v2 (1).json` (actual filename — note space and `(1)` suffix)
6. `backend/app/data/raw/iba_cleaned.json`

---

## STEP 1 Notes

**DOW file:** Found as `dow_university_v2 (1).json` (not `dow_university_v2.json` as the task specified — space and `(1)` in filename). 5 degrees confirmed.

**IBA file:** Found as `iba_cleaned.json`. **9 degrees found, not 8.** The 9th degree is `iba_bs_economics_data_science` — it already had `policy_pending_verification: true` and empty `merit_history`, indicating it was a newer program added after the task instructions were written. All fee fixes were applied to all 9 degrees.

---

## What Was Done

### DOW — backend/app/data/raw/dow_university_v2 (1).json

**STEP 2 — estimated_total_cost_pkr corrections (schema: fee × semesters only, no admission fee):**

| degree_id | semesters | fee_per_semester | estimated_total_cost_pkr (before) | estimated_total_cost_pkr (after) |
|---|---|---|---|---|
| dow_mbbs | 10 | 24000 | 391500 | **240000** |
| dow_bds | 8 | 100000 | 966500 | **800000** |
| dow_pharmd | 10 | 137500 | 1382500 | **1375000** |
| dow_dpt | 10 | 37500 | 382500 | **375000** |
| dow_bs_nursing | 8 | 27500 | 227500 | **220000** |

All previous values were the result of incorrectly adding `admission_fee_pkr` to the total (old wrong formula: `fee × sems + admission_fee`). Now corrected to `fee × sems` only.

**STEP 3 — dow_dpt min_percentage_hssc:**

| degree_id | field | before | after |
|---|---|---|---|
| dow_dpt | eligibility.min_percentage_hssc | 60.0 | **50.0** |

DPT is governed by NCEAC/PNC category (50.0 floor), not PEC (60.0). DATA_CHAT_INSTRUCTIONS.md lists DPT under the 50.0 category.

**STEP 4 — confidence_band corrections:**

| degree_id | merit_history | correct_band | before | after |
|---|---|---|---|---|
| dow_dpt | all 4 years = 72.5 (min=max=72.5) | max-min = 0.0 | 5.0 | **0.0** |
| dow_bs_nursing | all 4 years = 70.0 (min=max=70.0) | max-min = 0.0 | 5.0 | **0.0** |

---

### IBA — backend/app/data/raw/iba_cleaned.json

**STEP 5 — Fee structure update for all 9 IBA degrees:**

Source: Official IBA fee structure page (iba.edu.pk/fee-structure.php) for Fall 2025.
Calculation: (15 credit hours × Rs. 29,400) + Rs. 7,000 student activity = Rs. 448,000/semester.
Admission charges (one-time): Rs. 115,000.
Total: 448,000 × 8 = Rs. 3,584,000.

| field | before | after | applied to |
|---|---|---|---|
| fee_per_semester | 315000 | **448000** | all 9 degrees |
| admission_fee_pkr | 65000 | **115000** | all 9 degrees |
| estimated_total_cost_pkr | 2620000 | **3584000** | all 9 degrees |

Degrees updated: `iba_bba`, `iba_bs_accounting_finance`, `iba_bs_business_analytics`, `iba_bs_economics`, `iba_bs_ssla`, `iba_bs_cs`, `iba_bs_mathematics`, `iba_bs_economics_mathematics`, `iba_bs_economics_data_science`.

**STEP 6 — iba_bs_economics_mathematics data quality fix:**

The existing merit_history (55.6, 56.7, 55.6, 56.7, 55.6 across 5 years) was identical to iba_bs_mathematics and iba_bs_cs — confirming it was placeholder/copy-pasted data, not verified program-specific cutoffs.

| field | before | after |
|---|---|---|
| eligibility.policy_pending_verification | false | **true** |
| merit_history | 5 entries (placeholder cutoffs) | **[]** |
| cutoff_range.min | 55.6 | **null** |
| cutoff_range.max | 56.7 | **null** |
| confidence_band | 1.1 | **null** |
| aggregate_formula.notes | original text only | **appended merit data notice** |

Note appended to aggregate_formula.notes:
> "Merit history data not available — IBA does not publish program-specific aptitude score cutoffs publicly. Fazal to obtain historical cutoff data directly from IBA admissions office before this degree can go live."

---

## Verification Results

**7a. DOW JSON valid:** PASS
**7b. dow_mbbs total=240000:** PASS (24000×10=240000)
**7c. dow_bds total=800000:** PASS (100000×8=800000)
**7d. dow_pharmd total=1375000:** PASS (137500×10=1375000)
**7e. dow_dpt total=375000:** PASS (37500×10=375000)
**7f. dow_bs_nursing total=220000:** PASS (27500×8=220000)
**7g. dow_dpt min_percentage_hssc=50.0:** PASS
**7h. dow_dpt confidence_band=0.0:** PASS
**7i. dow_bs_nursing confidence_band=0.0:** PASS
**7j. No DOW degree uses (fee×sems)+admission formula:** PASS — all 5 confirmed clean
**7k. IBA JSON valid:** PASS
**7l. All 9 IBA fee_per_semester=448000:** PASS
**7m. All 9 IBA admission_fee_pkr=115000:** PASS
**7n. All 9 IBA estimated_total_cost_pkr=3584000:** PASS
**7o. iba_bs_economics_mathematics merit_history=[] and policy_pending_verification=true:** PASS (cutoff_range.min=null, max=null, confidence_band=null also confirmed)
**7p. No IBA degree has fee_per_semester=315000 remaining:** PASS

---

## Issues Noticed (not fixed)

1. **DOW: `nursing` and `physical_therapy` not in canonical field_id list.** `dow_bs_nursing` uses `field_id: "nursing"` and `dow_dpt` uses `field_id: "physical_therapy"`. Neither appears in the canonical list in CLAUDE.md / DATA_CHAT_INSTRUCTIONS.md / POINT_4. Waqas must add both to CLAUDE.md, DATA_CHAT_INSTRUCTIONS.md, POINT_4, lag_model.json, and affinity_matrix.json before these degrees can go live.

2. **DOW: Non-standard schema fields `fee_data_status` and `conducting_body`.** These exist on `dow_pharmd`, `dow_dpt`, and `dow_bs_nursing` (`fee_data_status`) and on all 5 DOW entry_test blocks (`conducting_body`). Neither field appears in the POINT_4 per-degree schema. Waqas to decide whether to add both fields to the schema or strip them before appending to universities.json.

3. **IBA: `iba_bs_economics_mathematics` has empty merit_history.** Placeholder data cleared in this session. Fazal to obtain historical cutoff data directly from IBA admissions office before this degree can go live.

4. **IBA: `economics_mathematics` and `economics_data_science` not in canonical field_id list.** `iba_bs_economics_mathematics` uses `field_id: "economics_mathematics"` and `iba_bs_economics_data_science` uses `field_id: "economics_data_science"`. Both are non-canonical. Same action required as for nursing/physical_therapy — add to canonical list, lag_model.json, and affinity_matrix.json.

5. **IBA: `entry_test_difficulty_tier` currently set to `"standard"`.** Given the competitive and selective nature of the IBA Aptitude Test (cutoffs around 50–63% out of 360 raw score), Fazal to verify whether IBA should be classified as `"hard"` rather than `"standard"`. NUST=extreme, FAST=hard per CLAUDE.md — IBA may warrant `"hard"` given its selectivity.

6. **IBA: `fee_per_semester` is an approximation.** The updated value (Rs. 448,000) is calculated as 15 credit hours × 29,400 + 7,000 student activity charges. Actual semester cost varies by credit hours taken. Fazal to note this is an estimate based on a standard 15 CH semester load. Actual per-semester billing may differ.

7. **IBA: `iba_bs_ssla` uses `field_id: "social_sciences"` — not in canonical list.** This was not listed in the task's Issues section but was found during review. `social_sciences` does not appear in the canonical field_id list. Same action required — add to canonical list, lag_model.json, and affinity_matrix.json, or remap to an existing canonical field_id (e.g. `social_work` or `psychology` — but neither is an exact match for Social Sciences & Liberal Arts). Waqas and Fazal to agree on the correct canonical mapping.

8. **IBA file count discrepancy.** Task specified 8 degrees; file contains 9. The 9th degree (`iba_bs_economics_data_science`) was already in the file with correct data quality markers (policy_pending_verification=true, empty merit_history). All fee fixes applied to all 9 degrees.

---

## Not Changed

- `merit_history` values for DOW and all IBA degrees except iba_bs_economics_mathematics (cleared as instructed)
- All `eligibility.fully_eligible_streams`, `conditionally_eligible_streams`, `entry_test` fields
- `fee_per_semester` and `admission_fee_pkr` for all DOW degrees
- `universities.json` — both files remain in `raw/` only

---

## Commit Status

NOT committed. Fazal to review and commit after Data Chat sign-off.
