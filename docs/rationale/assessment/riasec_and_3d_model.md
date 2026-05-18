# Why RIASEC and the 3D Spherical Model

**Component:** Personality assessment — primary instrument
**Decided:** Architecture Chat v3-v5 (April-May 2026)
**Status:** Locked in CLAUDE.md v2.5

---

## What This Is

The system uses Holland's RIASEC theory as its primary personality
assessment, extended to a 3D spherical model using Prediger's 2D
projection plus a Pakistan-specific prestige dimension.

---

## Why RIASEC — The Base Instrument

**Empirical validation:**
Holland's RIASEC theory (1997) is the most empirically validated career
interest framework — 50+ years of research, meta-analyses across cultures,
and explicit use in O*NET (US Department of Labor). HEC Pakistan's career
counselling guidelines reference RIASEC as the appropriate framework for
degree guidance.

**Scale:**
60 questions, 5-point Likert, 10 questions per dimension (R, I, A, S, E, C).
Range 10-50 per dimension (summed, not averaged). This scale was chosen
after evaluating the standard 3-point agree/neutral/disagree scale —
5-point captures more variance and reduces ceiling effects at the top
of each dimension.

**Practical fit:**
RIASEC questions are answerable by 15-18 year old students without work
experience. The questions reference activities and preferences, not job
titles or workplace scenarios. A student who has never worked can still
answer "how much do you enjoy solving puzzles" or "how much do you enjoy
helping others."

---

## Why the Flat Hexagon is Insufficient

The standard RIASEC hexagon represents the six types as a flat 2D shape.
This creates two problems for the Pakistani context:

**Problem 1 — Adjacent types are not discriminated well enough:**
CS and Biomedical Engineering both score high Investigative (I) on the
hexagon. A student with I=45/50 gets both recommended with similar scores
despite them being genuinely different career paths. The flat model lacks
the granularity to discriminate within a single dominant type.

**Problem 2 — Prestige is invisible:**
In Pakistan, family approval and social prestige are primary drivers of
degree choice — not just personal interest fit. A student whose RIASEC
profile perfectly matches Social Work (high S) will face strong family
resistance if that degree is perceived as low-prestige. The flat hexagon
has no mechanism to represent this dimension. Recommendations produced
without prestige awareness are systematically misaligned with Pakistani
family decision-making.

---

## Why the 3D Prediger Model

**The Prediger 2D projection:**
David Prediger (1982) proposed mapping the RIASEC hexagon onto two
orthogonal axes derived from existing RIASEC scores:

```
people_things = 0.5*(E+S) - 0.5*(R+I)
  Positive = People pole (social, enterprising)
  Negative = Things pole (realistic, investigative)

ideas_data    = 0.5*(C+E) - 0.5*(A+I)
  Positive = Data/Structure pole (conventional, enterprising)
  Negative = Ideas pole (artistic, investigative)
```

These axes require no new questions — they are computed from existing
RIASEC scores. CS sits in the Things + Ideas quadrant. Biomedical
Engineering sits in the Things + People quadrant. The 2D projection
separates them where the flat hexagon does not.

**The prestige dimension (Pakistan-specific):**
The Personal Globe Inventory-Sphere (PGI-S) adds a prestige/status
dimension to the Prediger 2D model, producing a spherical representation.
For Pakistan, the prestige dimension (1-10 scale) maps directly to the
Karachi social hierarchy:

```
10 — Medicine/MBBS (universal family approval)
 9 — Engineering at NED/top institutions
 8 — CS/Software Engineering
 7 — Law/LLB
 6 — Business/BBA at IBA
 5 — Education/Teaching
 4 — Social Sciences
 3 — Social Work, Fine Arts
```

**The 3D match formula:**
```
total_match = 0.6 × geometric_distance_3d
            + 0.3 × dot_product_riasec
            + 0.1 × prestige_alignment
```

The 60% geometric distance captures overall profile fit. The 30% dot
product captures directional alignment within the hexagon. The 10%
prestige alignment ensures that when two degrees score similarly on fit,
the one matching the student's stated prestige preference ranks higher.

---

## Key Design Decisions

1. **Prestige preference derived, not asked directly:** Students are not
   asked "how important is prestige to you?" — this produces socially
   desirable responses. Instead, ProfilerNode derives `prestige_preference`
   (0-10 float) from `family_context` (what the family expects) and
   `vna_scores` (the student's own values). This is more reliable than
   self-report.

2. **Prediger axes stored in affinity_matrix:** `people_things_axis` and
   `ideas_data_axis` are pre-computed from each field's RIASEC affinity
   vector and stored in affinity_matrix.json. They are not recomputed
   per student — the field position is fixed, only the student's position
   changes. This is computationally efficient.

3. **prestige_tier per field in affinity_matrix:** Integer 1-10, assigned
   based on Karachi social reality. Reflects family approval probability,
   not objective career quality. A degree can be excellent for the student
   but low-prestige in family context — the system surfaces this tension
   rather than hiding it.

---

## Known Limitations

- The prestige hierarchy is Karachi-specific and may not transfer to other
  Pakistani cities. Lahore and Islamabad have somewhat different prestige
  orderings (e.g., medical colleges differ by city).
- The Prediger axes assume Holland's theoretical structure is universal.
  Some cross-cultural research suggests the hexagon ordering differs
  in non-Western contexts. Post-viva: validate axis positions against
  Pakistani employer data.

---

## Future Enhancement Triggers

- If KCIS data shows systematic misalignment between Prediger position and
  actual student sub-scale scores → recalibrate people_things and ideas_data
  values in affinity_matrix
- If employer feedback shows prestige_tier values are wrong for specific
  fields → update prestige_tier without changing the formula
- Post-FYP: CABIN-NET (20 basic interest scales under RIASEC domains) is a
  direct upgrade path — same affinity_matrix structure, different keys
