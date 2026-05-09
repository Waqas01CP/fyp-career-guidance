# claude-code-2026-05-09-04-00-write-recommendation-expansion.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: Expand _write_recommendation() to store complete 20-field cards

---

## Current _write_recommendation() — Before

```python
async def _write_recommendation(
    db: AsyncSession,
    user_id,
    current_roadmap: list,
    previous_roadmap: list,
    last_intent: str,
) -> None:
    """Write a new recommendations row after a successful pipeline run."""
    trigger = (
        "initial"        if not previous_roadmap
        else "profile_update" if last_intent == "profile_update"
        else "manual_rerun"
    )
    rec = Recommendation(
        id=uuid_mod.uuid4(),
        user_id=user_id,
        roadmap_snapshot=[
            {
                "degree_id":   d.get("degree_id"),
                "total_score": d.get("total_score"),
                "merit_tier":  d.get("merit_tier"),
                "soft_flags":  d.get("soft_flags", []),
            }
            for d in current_roadmap
        ],
        trigger=trigger,
    )
    db.add(rec)
    await db.commit()
```

Stored only 4 fields per degree. Flutter dashboard could not reconstruct
university cards from GET /api/v1/profile/recommendations.

---

## _build_university_card() — All 20 Return Keys Confirmed

```
rank, degree_id, degree_name, university_id, university_name,
field_id, total_score, match_score_normalised, future_score,
merit_tier, eligibility_tier, eligibility_note, fee_per_semester,
aggregate_used, soft_flags, lifecycle_status, risk_factor,
rozee_live_count, rozee_last_updated, policy_pending_verification
```

**`final_state` finding:** Parameter declared in signature but NEVER referenced
in the function body. All data comes from `degree` dict and `_LAG_MODEL_MAP`
(module-level). Passing `{}` is safe and correct — confirmed by reading
lines 60-86 of chat.py.

---

## New _write_recommendation() — After

```python
async def _write_recommendation(
    db: AsyncSession,
    user_id,
    current_roadmap: list,
    previous_roadmap: list,
    last_intent: str,
) -> None:
    """
    Persist the current recommendation run to the DB.
    Stores complete 20-field university cards in
    roadmap_snapshot so the dashboard can restore
    full cards on app restart.
    """
    # Build complete cards — same format Flutter receives via SSE.
    # final_state is unused inside _build_university_card() — {} is safe.
    snapshot = []
    for i, degree in enumerate(current_roadmap[:5]):
        card = _build_university_card(degree, i + 1, {})
        snapshot.append(card)

    rec = Recommendation(
        user_id=user_id,
        roadmap_snapshot=snapshot,
        trigger=last_intent,
    )
    db.add(rec)
    await db.commit()
```

Changes from before:
- `roadmap_snapshot`: 4-field sparse dict → 20-field complete card per degree
- `trigger`: computed from previous_roadmap/last_intent logic → `last_intent` directly
- `id=uuid_mod.uuid4()`: removed — model default=uuid.uuid4 handles it
- Capped to `[:5]` — matches what Flutter receives via SSE (top 5 only)

---

## Test Changes Required

None. No test files cover chat.py or _write_recommendation(). Zero tests assert
the 4-field structure of roadmap_snapshot.

---

## Test Results

```
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 2.45s
```

---

## Snapshot Structure Verification (inline check result)

```
Card keys (20): aggregate_used, degree_id, degree_name, eligibility_note,
eligibility_tier, fee_per_semester, field_id, future_score, lifecycle_status,
match_score_normalised, merit_tier, policy_pending_verification, rank,
risk_factor, rozee_last_updated, rozee_live_count, soft_flags, total_score,
university_id, university_name
All required fields present. Snapshot OK: 1 card(s).
```

---

## Architecture Chat Notes

1. **`previous_roadmap` parameter is now unused** in `_write_recommendation()`.
   The trigger logic that used it was replaced by `trigger=last_intent`. The
   parameter remains in the signature (and at the call site) to avoid a breaking
   change in this session. Can be removed from signature and call site in a
   follow-up cleanup session.

2. **`trigger` field inconsistency**: Now stores `"get_recommendation"` (the
   actual `last_intent` value at call time). CLAUDE.md/Point 3 documents valid
   values as `"initial" | "profile_update" | "manual_rerun"`. The DB column is
   VARCHAR with no CHECK constraint — no crash risk. Waqas to decide: align
   `trigger=last_intent` back to the original mapping, or update Point 3 to
   document `"get_recommendation"` as a valid value.
