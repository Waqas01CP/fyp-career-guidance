# claude-code-2026-05-09-02-00-policy-unconfirmed-flag.md
## FYP: AI-Assisted Academic Career Guidance System
## Session: FLAG_DESCRIPTIONS — add policy_unconfirmed entry

---

## FLAG_DESCRIPTIONS Before (9 entries)

```
1. over_budget
2. commute_distance
3. stretch_merit
4. improvement_needed
5. entry_test_proxy_used
6. entry_test_harder_than_assessed
7. bridge_course_required
8. planning_mode
9. eligibility_contact_university
```

---

## FLAG_DESCRIPTIONS After (10 entries)

```
1. over_budget
2. commute_distance
3. stretch_merit
4. improvement_needed
5. entry_test_proxy_used
6. entry_test_harder_than_assessed
7. bridge_course_required
8. planning_mode
9. policy_unconfirmed          ← added
10. eligibility_contact_university
```

`policy_unconfirmed` (line 53) is immediately before `eligibility_contact_university` (line 58) — adjacent as required.

---

## Exact Lines Added

**File:** `backend/app/agents/nodes/explanation_node.py`
**Position:** Lines 53–57, immediately before `eligibility_contact_university`

```python
    "policy_unconfirmed": (
        "This degree's entry requirements are pending "
        "official confirmation. Verify directly with "
        "the university before applying."
    ),
```

---

## Test Results

```
pytest backend/tests/ -v -m "not slow"
67 passed, 3 deselected in 2.56s
```

---

## Context

`policy_unconfirmed` is emitted by filter_node in two places:
1. Check 1 — stream with `policy_pending_verification: true` in eligibility
2. Fix 4 — degrees with `cutoff_range: {min: null, max: null}` (IBA policy-pending degrees)

Both cases previously produced flags that ExplanationNode silently skipped.
Now surfaces to the student as: "This degree's entry requirements are pending
official confirmation. Verify directly with the university before applying."
