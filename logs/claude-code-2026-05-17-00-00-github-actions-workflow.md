# Session Log — GitHub Actions Workflow: LinkedIn Daily Scraper
**File:** `claude-code-2026-05-17-00-00-github-actions-workflow.md`
**Date:** 2026-05-17
**Model:** Claude Sonnet 4.6
**Task:** Create `.github/workflows/daily_scraper.yml` — GitHub Actions workflow to run Script B daily and commit results to data-branch.

---

## TEST_MODE env var confirmed

Line 45 of `scrape_linkedin_daily.py`:
```python
TEST_MODE = os.environ.get("LINKEDIN_TEST_MODE", "true").lower() == "true"
```
- Default: `True` (local testing — main files never touched)
- GitHub Actions sets `LINKEDIN_TEST_MODE: "false"` → production mode writes to main files

---

## Workflow File Structure

**File created:** `.github/workflows/daily_scraper.yml`

7-step structure in order:

| Step | Name | What it does |
|---|---|---|
| A | Checkout data-branch | Checks out `data-branch` with existing `linkedin_raw_jobs.json` + `linkedin_seen_jobs.json` |
| B | Setup Python | Python 3.12 on ubuntu-latest |
| C | Install dependencies | `pip install requests beautifulsoup4` |
| D | Fetch script from main | `git fetch origin main && git checkout origin/main -- backend/scripts/scrape_linkedin_daily.py` |
| E | Run daily scraper | `LINKEDIN_TEST_MODE=false python backend/scripts/scrape_linkedin_daily.py` |
| F | Verify collection | Python snippet checks `len(jobs) > 0`, exits 1 on failure |
| G | Commit data files | `git add` both data files, `git diff --staged --quiet ||` skips empty commits, `git push origin data-branch` |

**Key design decisions:**
- Code lives on `main`, data lives on `data-branch` — they never mix
- Step A checks out `data-branch` so the script inherits existing data (deduplication works correctly)
- Step D overlays just the script file from `main` onto the data-branch checkout — no other code files needed
- Step F failing (zero jobs) causes the workflow to fail and GitHub emails a notification
- Step G's `git diff --staged --quiet ||` pattern ensures no empty commits on days with no new jobs (all jobs already seen)

**On failure:** GitHub's built-in email notification fires whenever any step exits non-zero. No additional notification config needed.

---

## YAML Syntax Check

No syntax issues found. The workflow uses:
- Standard GitHub Actions syntax (v4 actions for checkout, v5 for Python)
- `workflow_dispatch` with no inputs (allows manual trigger with no parameters)
- Inline Python via `python -c "..."` with escaped inner quotes
- `git diff --staged --quiet ||` pattern — standard idiom for conditional commits

---

## Self-Review Checklist (9 items)

All 9 pass:

1. ✓ Both `schedule` (cron) and `workflow_dispatch` present
2. ✓ Cron `'0 4 * * *'` = 4am UTC = 9am PKT
3. ✓ `ref: data-branch` in Step A checkout
4. ✓ `git checkout origin/main -- backend/scripts/scrape_linkedin_daily.py` in Step D
5. ✓ `LINKEDIN_TEST_MODE: "false"` in Step E env block
6. ✓ Verification checks `len(jobs) == 0` → `sys.exit(1)`
7. ✓ `git diff --staged --quiet ||` skips empty commits
8. ✓ All paths relative — no hardcoded absolute paths
9. ✓ `secrets.GITHUB_TOKEN` — built-in, no manual secret setup

---

## Files Created

| File | Description |
|---|---|
| `.github/workflows/daily_scraper.yml` | GitHub Actions workflow — runs daily at 4am UTC |
| `logs/claude-code-2026-05-17-00-00-github-actions-workflow.md` | This session log |

## Files NOT Modified

- `backend/scripts/scrape_linkedin_daily.py` ✓
- `backend/scripts/scrape_linkedin_anytime.py` ✓
- All data files ✓
- No other workflow files created ✓
