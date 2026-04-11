# Title: Known Limitation — Physical Migration Pathways Not Modelled in FutureValue

## Statement:

The FutureValue formula models two career pathways: domestic Pakistani market demand (Layer 1 and Layer 2) and outsourcing-compatible global demand (Layer 3). Physical migration — where Pakistani graduates permanently relocate abroad for employment — is not captured in the formula.

## Why the data does not exist at the required granularity:

The Bureau of Emigration and Overseas Employment (BEOE) publishes annual emigration figures broken down by broad profession category (Engineers, Doctors, Teachers, Technicians) but not by degree field. Pakistani petroleum engineers, electrical engineers, mechanical engineers, and civil engineers are all aggregated into a single "Engineers" figure. In 2024, BEOE recorded 8,018 total engineer emigrants — but this number cannot be disaggregated by specialisation from any public source.

The Pakistan Institute of Development Economics (PIDE) explicitly documents this gap: BEOE data "comprises a significant portion of unskilled and semi-skilled workers, missing the emigration of professionals such as doctors, teachers, IT experts and others." A 2025 Konrad Adenauer Stiftung policy brief on Pakistani skilled migration confirms the same finding: the percentage of highly skilled migrants is reported in aggregate (under 10% of total emigrants in 2023), not broken down by field.

The gap is structural, not temporary. BEOE records only emigrants who register through official channels and proceed on work visas to Gulf countries. Skilled professionals migrating to Europe, North America, and Australia — who are not required to register with BEOE — are entirely absent from the dataset. Pakistan's Ministry of Overseas Pakistanis and HEC have acknowledged the need for a centralised migration data system with degree-field granularity, framing it as future policy work.

## Decision:

Physical migration pathways are identified as a known limitation of the FutureValue model. Incorporating migration data is deferred to future work, pending availability of field-level emigration statistics from BEOE or an equivalent body. For fields where Gulf migration is a well-documented pathway (petroleum engineering, medicine, civil engineering), career destination context is surfaced via AnswerNode's career_paths.common_sectors field in natural language responses, providing partial mitigation without altering the formula.

## Sources:

Bureau of Emigration and Overseas Employment (BEOE), Government of Pakistan — Annual Emigration Statistics 2024
PIDE Research Paper KB-112:2024 — "Pakistan's Emigration: Trends and Insights"
Gulf Research Centre / Konrad Adenauer Stiftung — "Highly Skilled Migration from Pakistan" (March 2025)
Gallup Pakistan / BEOE — "Pakistan Migration Patterns" (March 2025)

