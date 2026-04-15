# Data Change — NED University universities.json

**Date:** 2026-04-16
**Author:** Fazal, Waqas
**Affects:** Waqas, Khuzzaim

## What changed
`backend/app/data/neduet_university_verified_04_26.json` populated with verified NED University data.

## Details
- 33 undergraduate degrees added for NEDUET
- Sources: NED Undergraduate Prospectus 2025, official closing merit lists 2021–2024
- Fees verified against Spring 2025 NED fee schedule
- Merit history verified against official NED closing merit lists

## Action required — Waqas
- 13 non-canonical field_ids in this file have no lag_model or affinity entries yet.
  Validation script will fail until these are added.
  field_ids pending: chemical_engineering, telecommunications_engineering,
  industrial_manufacturing_engineering, automotive_engineering,
  metallurgical_engineering, materials_engineering,
  polymer_petrochemical_engineering, urban_infrastructure_engineering,
  construction_engineering, textile_engineering, food_engineering,
  textile_sciences, english_linguistics
- neduet_be_cise must be added to associated_degrees of computer_science
  in lag_model.json alongside neduet_bs_cs

## Action required — Khuzzaim
None immediately. Data will be available once Waqas unblocks the lag_model entries.