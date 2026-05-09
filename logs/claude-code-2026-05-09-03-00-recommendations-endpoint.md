# claude-code-2026-05-09-03-00-recommendations-endpoint.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: GET /api/v1/profile/recommendations endpoint

---

## Pre-Implementation Verification

### Recommendation model columns (full list)
| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key, default uuid4 |
| `user_id` | UUID | ForeignKey("users.id", CASCADE), nullable=False |
| `run_timestamp` | DateTime(timezone=True) | server_default=func.now(), nullable=False |
| `roadmap_snapshot` | JSONB | nullable=False, default=list |
| `trigger` | String | nullable=False, default="initial" |

- `run_timestamp` EXISTS ✓ — used for DESC ordering
- `roadmap_snapshot` EXISTS and is JSONB ✓
- No `created_at` column on Recommendation model

### What _write_recommendation() writes to roadmap_snapshot
A slimmed list — **4 fields per degree only**:
```python
{"degree_id": ..., "total_score": ..., "merit_tier": ..., "soft_flags": [...]}
```
NOT all 15 fields from the full pipeline roadmap. Flutter dashboard cannot reconstruct
full university cards (no `university_name`, `degree_name`, `fee_per_semester`, etc.)
from this endpoint. Flagged for Architecture Chat — `_write_recommendation()` may need
to be expanded to store more fields if the dashboard needs to rebuild full cards from DB.

### profile.py router prefix
`APIRouter(tags=["profile"])` with no prefix, registered with `/api/v1` in main.py.
Path `/profile/recommendations` → `GET /api/v1/profile/recommendations` ✓

### Existing imports in profile.py (no new module-level imports needed)
- `select` (sqlalchemy) ✓ — already at module level
- `get_db` ✓ — already imported
- `get_current_user` ✓ — already imported
- `User` ✓ — already imported
- `desc` and `Recommendation` — added as local imports inside the function body

---

## Endpoint Implementation

**File:** `backend/app/api/v1/endpoints/profile.py`
**Position:** Before `POST /admin/seed-knowledge` (line 280)

```python
@router.get("/profile/recommendations", status_code=200)
async def get_recommendations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import desc
    from app.models.recommendation import Recommendation

    result = await db.execute(
        select(Recommendation)
        .where(Recommendation.user_id == current_user.id)
        .order_by(desc(Recommendation.run_timestamp))
        .limit(1)
    )
    rec = result.scalar_one_or_none()
    if not rec:
        return {"recommendations": []}
    return {"recommendations": rec.roadmap_snapshot or []}
```

---

## Manual Test Results

Manual testing requires a running backend with Supabase connection — not possible
in this local environment (no .env with live credentials). Expected behaviour:

- **With data:** `200 {"recommendations": [{degree_id, total_score, merit_tier, soft_flags}, ...]}`
- **Without data (fresh account):** `200 {"recommendations": []}`
- **Invalid/expired JWT:** `401` (handled by `get_current_user` dependency, unchanged)

---

## Test Suite Results

```
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 3.00s
```

---

## Architecture Chat Note

`roadmap_snapshot` stores only 4 fields per degree. If Flutter needs to display
full university cards (name, fee, field_id, eligibility_tier, aggregate_used, shift, etc.)
from this endpoint, `_write_recommendation()` in chat.py needs to store the full
roadmap entry. This is a data-completeness decision for Architecture Chat — not
a bug in the current implementation.
