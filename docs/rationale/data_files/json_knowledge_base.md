# Data Files — JSON Knowledge Base

**Component:** Application runtime data files
**Decided:** Architecture Chat v1-v5 (March-May 2026)
**Status:** Schemas locked in SCHEMA_CONTRACT.md and POINT_4

---

## Why JSON Files (Not a Database Table Per Degree)

Three JSON files hold all degree, market, and university data:
`affinity_matrix.json`, `lag_model.json`, `universities.json`.

**Why not database tables:**
- Degree data changes infrequently (new universities, new programmes)
  but is read on every pipeline run. Database queries per pipeline
  run would add latency without benefit.
- JSON files are version-controlled — every change is tracked in git.
  A database update has no automatic audit trail.
- Fazal (data team member) can edit JSON files without database access
  or SQL knowledge. This is a team capability constraint, not a
  technical one.
- The data is relatively small (50 fields × 50 degrees ≈ 2500 records)
  — well within JSON file performance limits.

---

## affinity_matrix.json

**Purpose:** Maps each canonical degree field_id to its RIASEC affinity
vector, 3D position, prestige tier, capability requirements, and KCIS
sub-scale mapping.

**Why a separate file from lag_model:**
affinity_matrix contains psychological/academic fit data (RIASEC, KCIS,
required_capability). lag_model contains market/economic signal data
(job postings, FutureValue, ai_displacement). These are conceptually
and operationally separate — ScoringNode reads both but for different
parts of the score calculation. Keeping them separate makes each file's
purpose unambiguous and allows Fazal to update market data (lag_model)
without touching fit data (affinity_matrix).

**Key fields:**
- `riasec_affinity`: R/I/A/S/E/C integers 1-10 (minimum 1, never 0)
- `people_things_axis`, `ideas_data_axis`: Prediger 2D coordinates,
  computed from riasec_affinity
- `prestige_tier`: integer 1-10, Karachi social hierarchy
- `required_capability`: dict with numerical/spatial/verbal/logical
  minimum scores — only keys with meaningful requirements included
- `kcis_primary_subscale`, `kcis_secondary_subscale`: exact key names
  from the 24 KCIS sub-scales
- `social_acceptability_tier`: high/moderate/lower (ExplanationNode framing)

---

## lag_model.json

**Purpose:** Holds the Pakistani and global labour market signal for each
field_id. Feeds the FutureValue calculation in ScoringNode.

**FutureValue architecture (three layers):**
```
Layer 1 — pak_now (30%): Current Pakistan job market
  - job_postings_monthly: from LinkedIn scraper (Script D output)
  - yoy_growth_rate: year-over-year growth

Layer 2 — pak_future (20%): Pakistan trend
  - market_phase: computed from monthly_postings_history slope
  - slope: linear regression coefficient
  - ai_displacement: ARS framework scores

Layer 3a — world_now (30% of world weight):
  Current global demand (BLS Occupational Outlook)

Layer 3b — world_future (40% of world weight):
  Projected global demand (BLS 10-year projections)
```

**Why layer3 is split 60/40 (layer3a/layer3b):**
The original design had a single layer3 weight. Testing showed that
future_value scores could exceed the 0-10 range that ScoringNode's
normalization depends on when world_future values are high. Splitting
layer3 into layer3a (60%) and layer3b (40%) constrains the range
while preserving the directional signal.

**LOCAL lag category:**
For LOCAL fields (Medicine, Law, Civil Engineering, Business), layer3
weight is 0 — global demand signals are irrelevant for careers that
are geographically constrained to Pakistan. FutureValue relies on
pak_now and pak_future layers only.

**ai_displacement (ARS framework):**
The AI Resistance Score measures protection from automation (0-100,
higher = more protected). Four sub-dimensions sum to the total:
physical_presence, human_relationship, creative_judgment,
ethical_accountability (each 0-25).
Reference calibration: MBBS=92, Nursing=95, Accounting=25, CS=48.

**gulf_demand_tier:**
"high" / "medium" / "low" / "not_applicable" — signals strong Gulf
(UAE, Saudi, Qatar) market for this field. High for Engineering,
CS, Nursing. Low for Arts, Education. Used by ExplanationNode to
surface international career context for relevant degrees.

---

## universities.json

**Purpose:** All degree programmes at all covered Karachi universities,
with admission requirements, fee structures, and merit cutoff history.

**Degree ID format:** `{university_id}_{canonical_degree_id}`
Example: `neduet_bs_cs`, `fast_nuces_bs_software_eng`, `aku_mbbs`

**Field_id canonical list authority:**
`DATA_CHAT_INSTRUCTIONS.md` holds the canonical field_id list. Any degree
not in the canonical list must have a new field_id added to BOTH
lag_model.json AND affinity_matrix.json before it can be added to
universities.json. FilterNode will silently default to neutral scores
for any field_id not in those files.

**cutoff_year:** Integer — which admissions year the merit cutoff data
is from. ExplanationNode adds a staleness caveat when cutoff_year is
more than one year behind the current year. Better to show slightly
stale data with a caveat than to show no data.

**employer_perception_tier:**
- tier_1: NED, FAST, IBA, AKU, DUHS — top employer recognition
- tier_2: SZABIST, Bahria, Hamdard, SSUET — solid mid-tier
- tier_3: newer or less-known private universities
Used by ExplanationNode to frame graduate employment prospects.

---

## SCHEMA_CONTRACT.md — The Phase 1+ Key Name Authority

SCHEMA_CONTRACT.md was created in Phase 0 to lock all new field key names
before any Phase 1+ implementation begins. This prevents the schema
bootstrap problem where Fazal writes `required_capability` using different
key names than what the nodes expect.

**Authority:** SCHEMA_CONTRACT.md is authoritative for all key names.
POINT_3 is authoritative for table structure and ORM. When they conflict,
SCHEMA_CONTRACT.md wins for key names.

---

## Known Limitations

- JSON files are loaded into memory at startup. For 50+ universities
  with 5+ degrees each, this is negligible. At 500+ universities it
  would require rethinking.
- No validation at runtime — FilterNode silently falls back to defaults
  if a field_id is missing from affinity_matrix or lag_model. The
  validate.py script in backend/app/data/ catches this at commit time.

---

## Future Enhancement Triggers

- If universities.json grows beyond ~200 degrees → consider moving to
  a proper database table with indexed queries
- If lag_model data becomes stale between Script D runs →
  consider real-time API integration for job count data
- If new universities require field_ids not in the canonical list →
  add to DATA_CHAT_INSTRUCTIONS.md and both JSON files before adding
  to universities.json
