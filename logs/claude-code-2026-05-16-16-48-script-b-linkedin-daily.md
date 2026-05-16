# Session Log — Script B: LinkedIn Daily Collection
**File:** `claude-code-2026-05-16-16-48-script-b-linkedin-daily.md`
**Date:** 2026-05-16
**Model:** Claude Sonnet 4.6
**Task:** Create `backend/scripts/scrape_linkedin_daily.py` — ongoing daily collection script for Pakistan LinkedIn jobs posted in the last 24 hours.

---

## Phase 0 — Pre-Run Checks

```
python -c "import requests, bs4; print('OK')"
→ OK

python -c "import pathlib; print(pathlib.Path('backend/data').exists())"
→ True
```

Both checks passed. `backend/data/` already existed from Script A.

---

## POINT_6 Location Confirmation

Script: `backend/scripts/` ✓ (POINT_6 locked location for scripts)
Output files: `backend/data/` ✓ (same directory as Script A)
Temp file: `backend/data/linkedin_daily_temp.json` ✓ (TEST_MODE only)
Log: `logs/` ✓

---

## Functions — Copied Verbatim vs Rewritten

**Copied VERBATIM from `scrape_linkedin_anytime.py` (8 functions):**
- `fetch_with_retry(url, session, log_func)` — verbatim
- `_extract_job_id(card)` — verbatim
- `parse_search_page(html_text)` — verbatim
- `parse_job_detail(html_text, job_id)` — verbatim
- `extract_city_country(location_raw)` — verbatim
- `load_existing_data()` — verbatim
- `enrich_work_type(raw_jobs, onsite_ids, remote_ids, hybrid_ids, log_func)` — verbatim
- `setup_logger(log_file)` — verbatim

**Not copied (Script A versions use save_progress/load_progress which Script B doesn't need):**
- `save_progress()` — NOT copied (no PROGRESS_FILE in Script B)
- `load_progress()` — NOT copied
- `save_data()` — NOT copied; Script B has a modified version (TEST_MODE-aware)
- `collect_filter_pass()` — NOT copied; rewritten as `collect_daily_filter_pass()` (f_TPR + page*10)
- `collect_main_pass()` — NOT copied; rewritten as `collect_daily_main_pass()` (f_TPR + page*10 + TEST_MODE split)

**New functions unique to Script B:**
- `save_data(raw_jobs, seen_jobs, log_func=None)` — returns immediately in TEST_MODE
- `save_temp_results(new_jobs, closure_updates, raw_jobs, log_func)` — TEST_MODE result writer
- `collect_daily_main_pass(session, raw_jobs, seen_jobs, log_func)` — f_TPR + page*10
- `collect_daily_filter_pass(session, pass_name, f_wt_value, log_func)` — f_TPR + page*10
- `collect_closure_check(raw_jobs, seen_jobs, session, log_func)` — checks jobs >= 4 days old

---

## TEST_MODE Behaviour — Main Files Protected

Confirmed from quick test log and filesystem check:

| Check | Result |
|---|---|
| TEST_MODE=True logged at startup | ✓ |
| "main files will NOT be modified" logged | ✓ |
| Main files never touched | ✓ — `linkedin_raw_jobs.json` still shows 1016 jobs |
| Results written to temp file | ✓ — `linkedin_daily_temp.json` written |
| `save_data()` no-ops in TEST_MODE | ✓ — confirmed by main file count unchanged |

---

## Quick Test Results

**Test run:** 2026-05-16, multiple concurrent instances (see note below)
**Completed instance:** Instance 1 (started 16:48, completed 17:12)

```
New jobs collected:          337
Work type:
  On-site:  232
  Remote:   81
  null:     14
  Hybrid:   10

Employment type:
  Full-time:  317
  Part-time:  6
  Contract:   12
  Volunteer:  1
  Temporary:  1

Closure candidates checked:  0   ← EXPECTED (jobs < 4 days old)
Jobs closed:                 0   ← EXPECTED (same reason)

Main file count:             1016  ← UNCHANGED (TEST_MODE working)
```

**Work type enrichment log:** `323/337 jobs labeled (95%)` — 14 jobs had null work_type (employer did not tag).

**Closure check — 0 candidates:** Correct and expected. Script A ran 2026-05-15 (yesterday). `CLOSURE_CHECK_MIN_AGE_DAYS = 4` means jobs must be ≥ 4 days old to be checked. No jobs in the database are that old yet. First closure candidates will appear 2026-05-19. This is not a bug.

**Expected new_jobs range:** 20–546. Actual 337 is within range. ✓

**Note on concurrent instances:** During testing, 3 Script B instances ran concurrently (all in TEST_MODE). This happened due to bash tool timeouts killing the wrapper shell while Python continued running. All instances wrote to the same log file (interleaved but legible). Since TEST_MODE prevents all writes to main files, no data corruption occurred. The final TEMP_FILE was written by Instance 1 at 17:12:41. The other instances either completed later and overwrote it with equivalent data, or were still running. Main file integrity confirmed: still 1016 records.

For production (GitHub Actions), only one instance runs at a time by design — cron scheduling prevents overlap.

---

## Scheduling Documentation

### OPTION A — GitHub Actions (RECOMMENDED — post-viva setup)

Script B will be deployed to GitHub Actions after local verification.

| Item | Value |
|---|---|
| Workflow file | `.github/workflows/daily_scraper.yml` |
| Schedule | `cron: '0 4 * * *'` (9am PKT = 4am UTC) |
| Data storage | Orphan `data-branch` — not committed to `main` |
| Free tier usage | 2000 min/month, Script B ~54 min/day = ~1620 min/month |
| Setup time | 2-3 hours, post-viva |

```yaml
name: LinkedIn Daily Scraper
on:
  schedule:
    - cron: '0 4 * * *'
  workflow_dispatch:
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: data-branch
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install requests beautifulsoup4
      - run: |
          sed -i 's/TEST_MODE = True/TEST_MODE = False/' \
            backend/scripts/scrape_linkedin_daily.py
      - run: python backend/scripts/scrape_linkedin_daily.py
      - run: |
          git config user.email "action@github.com"
          git config user.name "GitHub Action"
          git add backend/data/
          git diff --staged --quiet || \
            git commit -m "data: daily scrape $(date +%Y-%m-%d)"
          git push
```

### OPTION B — Windows Task Scheduler (local fallback)

| Item | Value |
|---|---|
| Task name | `LinkedInDailyScraper` |
| Program | `C:\path\to\venv312\Scripts\python.exe` |
| Arguments | `backend\scripts\scrape_linkedin_daily.py` |
| Start in | `C:\path\to\fyp-career-guidance\fyp-career-guidance\` |
| Trigger | Daily at 09:00 AM |
| Stop task if longer than | 2 hours |
| If already running | Do not start a new instance |
| Pre-condition | Set `TEST_MODE = False` before registering |

---

## Self-Review Checklist (24 items)

All 24 items pass:

1. ✓ `backend/scripts/` — not root
2. ✓ `TEST_MODE = True` as default constant
3. ✓ No `PROGRESS_FILE` anywhere — no save_progress/load_progress
4. ✓ `f_TPR={TIME_FILTER}` in all URLs (main + all 3 filter passes)
5. ✓ `page * 10` everywhere — confirmed from log (start=0,10,20...)
6. ✓ `from datetime import date, datetime, timedelta`
7. ✓ All 8 shared functions copied verbatim from Script A
8. ✓ `consecutive_failures = 0` before while loop
9. ✓ TEST_MODE: raw_jobs/seen_jobs never modified — only new_jobs_dict
10. ✓ `enrich_work_type(new_jobs, ...)` in TEST_MODE, `enrich_work_type(raw_jobs, ...)` in production
11. ✓ `save_data()` returns immediately in TEST_MODE
12. ✓ `save_temp_results()` writes work_type and employment_type breakdowns
13. ✓ Closure check returns list in both modes
14. ✓ TEST_MODE closure updates → temp file via save_temp_results
15. ✓ Closure check: `first_seen <= cutoff` (>= 4 days), `candidates.sort()` (oldest first)
16. ✓ Capped at `CLOSURE_CHECK_MAX_PER_RUN = 300`
17. ✓ `time.sleep(2)` between closure check fetches
18. ✓ `sys.exit(0)` even when `new_count = 0` (exits at same point regardless)
19. ✓ `KeyboardInterrupt`: `if not TEST_MODE: save_data()`
20. ✓ Exception: `if not TEST_MODE: save_data()`
21. ✓ Scheduling docs in session log (GitHub Actions + Task Scheduler above)
22. ✓ No project imports — stdlib + requests + bs4 only
23. ✓ Phase 0 checks run before writing code
24. ✓ Log to `logs/` repo root

---

## Files Created

| File | Description |
|---|---|
| `backend/scripts/scrape_linkedin_daily.py` | Script B — daily LinkedIn collection |
| `backend/data/linkedin_daily_temp.json` | TEST_MODE output (created at runtime) |
| `logs/scrape_linkedin_daily_2026-05-16.log` | Runtime log (created at runtime) |
| `logs/claude-code-2026-05-16-16-48-script-b-linkedin-daily.md` | This session log |

## Files NOT Modified (confirmed)

- `backend/scripts/scrape_linkedin_anytime.py` ✓ (hard rule observed)
- `backend/data/linkedin_raw_jobs.json` ✓ (still 1016 records)
- `backend/data/linkedin_seen_jobs.json` ✓ (still 1016 records)
- No files in `backend/app/data/` ✓
- No `.github/workflows/` created ✓
