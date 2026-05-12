# claude-code-2026-05-12-00-00-phase0b-alembic-migration.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: Phase 0b — Add 6 assessment columns to student_profiles

---

## Pre-Implementation Check Results

### Current profile.py columns (full list — 20 columns before this session)
id, user_id, onboarding_stage, education_level, student_mode, grade_system, stream, board,
riasec_scores, subject_marks, capability_scores, budget_per_semester, transport_willing,
home_zone, stated_preferences, family_constraints, career_goal, student_notes,
created_at, updated_at.

None of the 6 new columns existed. ✓

### Alembic migration files found
- `a09bedc067be_initial_schema.py` (only file — this is the most recent migration)

### Float import status
NOT present in profile.py before this session. Added in Task 1. ✓

### Supabase plugin pre-check (live DB current columns)
21 columns: same 20 as ORM model + `curriculum_level` (known gap from supabase-setup-log-2026-04-20).
None of the 6 new columns existed in the live database. ✓

### alembic_version table state
`version_num = 'a09bedc067be'` — matches the only migration file. Alembic state consistent. ✓

---

## Autogenerate — Unexpected Findings and Resolution

`alembic revision --autogenerate` connected to Supabase successfully (env.py uses
NullPool which is sufficient for reads even without statement_cache_size=0).

Generated file `ab05dd3617b7` contained EXTRA statements beyond 6 ADD COLUMN:

**Unwanted DROP statements detected:**
- `op.drop_table('checkpoint_blobs')` — LangGraph AsyncPostgresSaver table, created at runtime, not tracked by Alembic
- `op.drop_table('checkpoint_writes')` — same
- `op.drop_table('checkpoint_migrations')` — same
- `op.drop_table('checkpoints')` — same
- 5 `op.drop_index()` calls for manually-added application indexes
- `op.drop_column('student_profiles', 'curriculum_level')` — exists in Supabase but not in profile.py ORM (pre-existing gap)

**Resolution:** Per STOP AND REPORT RULE, stopped and reported. Manually curated the migration file to retain ONLY the 6 `op.add_column()` statements and the corresponding 6 `op.drop_column()` statements in downgrade. All DROP TABLE, DROP INDEX, and the DROP COLUMN for curriculum_level were removed. Comment added explaining the curation decision.

---

## Migration File Generated

**File:** `backend/alembic/versions/ab05dd3617b7_add_phase0b_assessment_columns_to_.py`

**Revision chain:** `a09bedc067be` → `ab05dd3617b7`

**Final curated upgrade() content:**
```python
op.add_column('student_profiles', sa.Column('aptitude_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
op.add_column('student_profiles', sa.Column('caas_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
op.add_column('student_profiles', sa.Column('vna_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
op.add_column('student_profiles', sa.Column('family_context', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
op.add_column('student_profiles', sa.Column('prestige_preference', sa.Float(), nullable=False))
op.add_column('student_profiles', sa.Column('misc_assessment_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=False))
```

Exactly 6 op.add_column() calls. No DROP TABLE. No DROP INDEX. No DROP COLUMN. ✓

---

## SQL Applied to Supabase SQL Editor

```sql
ALTER TABLE student_profiles
  ADD COLUMN IF NOT EXISTS aptitude_scores        JSONB NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS caas_scores            JSONB NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS vna_scores             JSONB NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS family_context         JSONB NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS prestige_preference    FLOAT NOT NULL DEFAULT 5.0,
  ADD COLUMN IF NOT EXISTS misc_assessment_scores JSONB NOT NULL DEFAULT '{}';
```

Confirmed executed by Waqas via Supabase SQL Editor.

---

## Supabase Plugin Post-Verification

All 6 columns confirmed present in live student_profiles table:

| Column | Type | Nullable | Default |
|---|---|---|---|
| aptitude_scores | jsonb | NO | '{}' |
| caas_scores | jsonb | NO | '{}' |
| vna_scores | jsonb | NO | '{}' |
| family_context | jsonb | NO | '{}' |
| prestige_preference | double precision | NO | 5.0 |
| misc_assessment_scores | jsonb | NO | '{}' |

---

## Test Results

```
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 13.69s
```

---

## Self-Review Checklist

1. profile.py has all 6 new columns with correct types ✓
2. Float is in SQLAlchemy imports in profile.py ✓
3. kcis_scores NOT added to profile.py ✓
4. Migration file contains only 6 ADD COLUMN statements (after manual curation) ✓
5. No DROP COLUMN or unexpected statements in final migration file ✓
6. Supabase plugin confirms all 6 columns exist in live DB ✓
7. All tests pass (67/67) ✓
8. Only profile.py and migration file were modified ✓

---

## Note for Next Phase

**alembic_version table NOT updated.** The migration `ab05dd3617b7` was applied to
Supabase manually via SQL Editor — NOT via `alembic upgrade head`. Alembic's
`alembic_version` table in Supabase still shows `a09bedc067be` (the initial migration).

If a future session needs to run autogenerate again, it will again detect the 6 new
columns as "to add" because the version table doesn't know they've been applied. This
is the same pattern as `curriculum_level` — applied to DB but not tracked.

**Resolution:** To keep Alembic state consistent, run this in Supabase SQL Editor:
```sql
UPDATE alembic_version SET version_num = 'ab05dd3617b7';
```
This tells Alembic the new migration has been applied, so future autogenerate
won't re-detect the 6 columns as missing.
