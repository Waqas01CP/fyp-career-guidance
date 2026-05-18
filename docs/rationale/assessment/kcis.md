# Why KCIS — Karachi Career Interest Sub-Scale

**Component:** Assessment — within-RIASEC discrimination instrument
**Decided:** Architecture Chat v4-v5 (May 2026)
**Status:** Locked in CLAUDE.md v2.5

---

## What This Is

KCIS (Karachi Career Interest Sub-Scale) is an original instrument
developed for this system. It provides granular sub-scale scores within
each RIASEC type to discriminate between adjacent degree programmes that
the flat RIASEC hexagon cannot separate.

---

## Why KCIS Was Needed

The core problem: two students with identical RIASEC vectors get identical
degree rankings. CS and Biomedical Engineering both load high on
Investigative (I). Civil Engineering and Mechanical Engineering both load
high on Realistic (R). The 3D Prediger projection partially separates
these pairs but not enough for confident within-type discrimination.

Example: A student with I=48, R=42, C=40 gets CS, Biomedical Engineering,
Data Science, and Electrical Engineering all ranked similarly. KCIS asks:
"Do you enjoy working with mathematical formulas and algorithms?" (maps to
`mathematical_computational`) vs "Do you enjoy understanding how biological
systems work?" (maps to `biological_life_sciences`). The sub-scale scores
separate what the hexagon cannot.

---

## Why Not the Strong Interest Inventory (SII)

The SII (CPP Inc.) was the obvious first choice — it is the most widely used
career interest instrument globally and uses Holland's 30 Basic Interest
Scales organised under RIASEC domains. There were two problems:

**Legal:** The SII is proprietary. Using its questions, even modified, in a
student-facing system without a license from CPP Inc. constitutes copyright
infringement. The 30 Basic Interest Scale NAMES are descriptive category
labels for real-world activities — these are not protectable. But the actual
question text is copyrighted.

**Practical:** The SII is designed for the US labour market. Its sub-scales
include categories like "Athletics," "Military Activities," and "Culinary
Arts" — none of which are meaningful discriminators for Pakistani university
degrees in Karachi.

---

## Why an Original Instrument

Writing original questions based on Holland's PUBLIC DOMAIN theory is legally
clean. The RIASEC framework, the concept of measuring interest sub-scales
within each type, and the principle of mapping sub-scales to occupational
categories — all public domain from Holland (1997). The instrument is named
KCIS specifically to distinguish it from SII, exactly as Samsung and Xiaomi
both run Android while their implementations are original.

**Viva defense wording:** "KCIS is an original instrument grounded in
Holland's RIASEC theory (1997, public domain) and adapted for the Karachi
educational context. The sub-scale structure follows the theoretical
framework of the Strong Interest Inventory but uses original question text
and Pakistani-specific degree mappings."

---

## The 24 Sub-Scales

24 sub-scales covering every bachelor's degree category currently in the
Karachi university system. 96 questions total — 4 per sub-scale.

The 24 sub-scales were chosen to cover the canonical field_id list with
sub-scale precision:

```
mathematical_computational, biological_life_sciences,
clinical_health_sciences, physical_sciences, research_analytical,
mechanical_electrical_systems, civil_construction_spatial,
technology_digital_systems, visual_graphic_design,
spatial_interior_fashion, architecture_design, media_journalism_film,
clinical_patient_care, teaching_education, community_counselling,
law_advocacy_governance, business_commerce_entrepreneurship,
leadership_public_service, financial_accounting_actuarial,
data_analytics_information, administrative_organisational,
linguistic_literary_humanities, religious_islamic_studies,
[24th sub-scale reserved]
```

**Stability guarantee:** The 24 sub-scales cover every bachelor's degree
category in Karachi's current university landscape. Adding new universities
to the system requires only populating `affinity_matrix` rows with
`kcis_primary_subscale` — no new KCIS questions needed. The sub-scales are
category-level, not degree-level.

---

## Key Design Decisions

1. **4 questions per sub-scale:** Minimum for internal consistency (Cronbach's
   alpha) with a reasonable administration time. 8 would be more reliable
   but 96 questions is already the largest single assessment in the stack.

2. **Likert-5 format:** Consistent with the rest of the assessment stack.
   Students do not switch between response formats mid-assessment.

3. **Activity framing, not job title framing:** Questions reference activities
   ("How much do you enjoy working with formulas and algorithms?") not
   occupations ("Would you enjoy being a software engineer?"). Activity
   framing works for 15-18 year olds without work experience and avoids
   prestige bias in responses.

4. **Discrimination requirement:** Each KCIS question must be answerable
   differently by students with adjacent interests. A `mathematical_computational`
   question must NOT be answerable identically by a student interested in
   `physical_sciences`. This was the hardest constraint to satisfy in
   question writing.

5. **kcis_primary_subscale in affinity_matrix:** Each field_id has a primary
   and optional secondary KCIS sub-scale. ScoringNode uses these for
   within-RIASEC-type discrimination. A student with high KCIS
   `mathematical_computational` score gets CS ranked above Biomedical
   Engineering even if both have identical RIASEC fit.

---

## Known Limitations

- 96 questions is a significant administration burden. If completion rates
  are low, reducing to 48 questions (12 priority sub-scales) is the fallback.
- The instrument has not been validated on a Pakistani student population —
  post-viva validation study recommended.
- Cronbach's alpha cannot be computed until real student data exists.
  Construct validity relies on theoretical grounding only at launch.

---

## Future Enhancement Triggers

- Completion rate < 60% → reduce to 48 questions covering priority sub-scales
- If sub-scale scores systematically misalign with student-reported interests
  in follow-up conversations → review question wording for Pakistani context
- Post-viva: run factor analysis on real student data to validate sub-scale
  structure and potentially merge or split sub-scales
