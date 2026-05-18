# LinkedIn Scraper Pipeline — Design Decisions

**Component:** LinkedIn job market data collection (Scripts A-D)
**Decided:** Architecture Chat v5 (May 2026)
**Status:** Scripts A and B complete and running. Script C prompt ready.

---

## Why LinkedIn (Not Rozee.pk)

**Rozee.pk evaluated and rejected:**
Rozee.pk was the first choice for Pakistani job market data. After testing:
- Total Pakistan jobs accessible: ~79 for software engineering, ~2 for
  mobile development — far too sparse for meaningful market signals
- JavaScript-rendered pages — simple HTTP requests return empty content,
  requiring Playwright (heavyweight dependency)
- No historical data available without login
- Monthly trends not accessible from the public interface

**LinkedIn guest API chosen:**
LinkedIn's unauthenticated guest API (`/jobs-guest/jobs/api/`) provides:
- ~1000-1200 Pakistan jobs accessible without login
- Per-job detail pages with employment_type, seniority_level, industry,
  job_functions
- Reliable daily new postings (~100-550 per day observed)
- No authentication required, no account needed
- Polite scraping with 3-second delays works without blocking

**LinkedIn ToS note:** LinkedIn's ToS prohibits automated scraping.
Courts have ruled (LinkedIn vs hiQ) that scraping publicly accessible,
logged-out data for analytics may be lawful. For an academic FYP with
no commercial intent, the practical risk is zero. LinkedIn pursues
commercial scrapers at scale, not student research projects.

---

## Script A — One-Time Historical Pull

**Purpose:** Build the initial job database from all currently-active
Pakistan LinkedIn jobs (anytime filter — no time restriction).

**The page × 10 discovery (critical fix):**
The original design used `start = page * 25` assuming LinkedIn returns
25 jobs per page. Testing showed only 9-10 jobs per page from the guest
API. The original scraper was skipping positions 10-24, 35-49, etc.
Fixing to `start = page * 10` increased the total from 631 to 1097 jobs.
This fix applies to ALL passes in ALL scripts.

**Four-pass architecture:**
```
Main pass: no f_WT filter → all jobs → per-job detail fetch
  Captures: job_id, title, company, location, employment_type,
            seniority_level, industry, job_functions, posted_date

Pass 1: f_WT=1 (On-site) → job_ids only, no detail fetch
Pass 2: f_WT=2 (Remote) → job_ids only
Pass 3: f_WT=3 (Hybrid) → job_ids only

Cross-reference: match filter pass job_ids against main pass
  Remote > Hybrid > On-site priority if job appears in multiple sets
  ~88% of jobs get work_type labeled (12% untagged by employers)
```

**Why work_type requires filter passes:**
The per-job detail page from the guest API does NOT include work_type
(Remote/Hybrid/On-site). This field is only accessible via the search
filter system. The four-pass approach infers work_type by running
separate searches with each work type filter and cross-referencing.

**Resumability:**
Script A uses a progress file (`linkedin_scrape_progress.json`) to track
the last completed page per pass. If interrupted (laptop closed, network
failure), re-running resumes from the last saved page — not from page 0.
Progress file is deleted on clean completion.

**Incremental saves:**
Data is written to disk every 25 new jobs (SAVE_INTERVAL). Interrupting
the script between saves loses at most 25 jobs' worth of work.

**Atomic writes:**
Both JSON files use a `.tmp` → `.replace()` pattern. If the process is
killed mid-write, the previous valid file is preserved. No corrupted JSON.

---

## Script B — Daily Ongoing Collection

**Purpose:** Collect new Pakistan LinkedIn jobs posted in the last 24 hours
and perform closure checks on existing jobs.

**TEST_MODE via environment variable:**
```python
TEST_MODE = os.environ.get("LINKEDIN_TEST_MODE", "true").lower() == "true"
```
Default is True locally — protects main data files during testing.
GitHub Actions sets `LINKEDIN_TEST_MODE=false` for production runs.
This allows testing Script B locally without any risk to the live database.

**Closure check (4-day threshold):**
Jobs older than 4 days that are still marked `still_active=True` get
checked via a per-job detail fetch. If the response is 404 or contains
"no longer accepting" → job marked closed with `closure_method` recorded.
If still active → `last_seen` and `duration_days` updated.

**Why 4 days (not 1 day):**
Jobs less than 4 days old are unlikely to have closed — checking them
would waste ~300 API requests per day on mostly-active jobs. The 4-day
threshold captures jobs that are realistic closure candidates while
keeping the closure check within the 300-job cap.

**Oldest-first ordering:**
The 300 closure-check candidates are selected oldest-first (sorted by
`first_seen` ascending). This ensures systematic coverage — every job
eventually gets closure-checked in age order, with no job permanently
skipped.

---

## GitHub Actions — Autonomous Daily Collection

**Why GitHub Actions over local Task Scheduler:**
Local Task Scheduler requires the laptop to be on at the scheduled time.
GitHub Actions runs on GitHub's servers regardless of laptop state.
Free tier provides 2000 minutes/month — Script B uses ~54 minutes/day
= ~1620 minutes/month, within the free tier.

**data-branch architecture:**
Main branch holds code only. A separate `data-branch` holds the LinkedIn
JSON data files. GitHub Actions checks out data-branch (to read existing
data), fetches the script from main (to get the latest code), runs Script B,
and commits updated data files back to data-branch.

**Why not an orphan branch:**
The data-branch was created from main using the GitHub website interface
(not an orphan branch) to avoid the git submodule complication with
`.claude/skills/flutter-official` and `.claude/skills/flutter-security`.
These folders contain `.git` directories internally which caused
`git rm -rf .` to fail on orphan branch creation.

**The submodule warning:**
GitHub Actions still shows "fatal: No url found for submodule path
'.claude/skills/flutter-official'" in the Post Checkout cleanup step.
This is cosmetic — the step shows as passed (green), the workflow
succeeds, and the data files are committed correctly. No action needed.

**sed gitignore workaround:**
`backend/data/` is gitignored on main branch (correctly). When GitHub
Actions checks out data-branch, the `.gitignore` from main is inherited.
The workflow uses `sed -i '/backend\/data/d' .gitignore` to remove the
gitignore restriction in the runner's environment before adding data files.
This modification is never committed — it only exists in the runner.

---

## Script C — Gemini LLM Title Mapping (Prompt Ready, Not Yet Executed)

**Purpose:** Map raw LinkedIn job titles to canonical field_ids.
Produces `job_title_mapping.json`.

**Why LLM mapping (not rule-based):**
Pakistani LinkedIn job titles are highly varied:
- Abbreviations: "SE", "SWE", "BE Dev", "Sr. BE (Python)"
- Multi-role: "Backend + AI + Database Engineer"
- Urdu-English mixed: various formats
- Pakistani conventions: "Executive" = mid-level (not C-suite),
  "Officer" = entry-level

Rule-based mapping cannot handle this variety reliably. The LLM sees
the title + company name + industry together and applies the 13
disambiguation rules embedded in the system prompt.

**Three-level output schema:**
- `primary_field_id`: the dominant degree field for this role
- `secondary_field_ids`: other degree fields whose graduates fill this role
- `sub_specialisation`: freeform sub-type tag for future granular analysis

**Key disambiguation rule — CS vs SE:**
CS and SE are separate canonical field_ids with different demand signals.
"Software Engineer" → `software_engineering` (primary), `computer_science`
(secondary). "CS Graduate" → `computer_science` (primary). The LLM must
not collapse these — they represent different market demand patterns
and different degree programmes in Pakistani universities.

**google.generativeai exemption:**
Script C uses `google.generativeai` directly (not `langchain_google_genai`).
This is explicitly permitted for standalone scripts in `backend/scripts/`
that have no LangGraph or FastAPI dependency. Locked in CLAUDE.md v2.7.

**Human review gate:**
Output is split into `confirmed` (high confidence) and `needs_review`
(medium/low confidence). The mapping file is NEVER committed automatically
— Waqas reviews `needs_review` before committing.

**Incremental processing:**
Re-running Script C only processes titles not yet in the existing mapping.
This makes it safe to run every 15 days — only new titles accumulated
since the last run are sent to Gemini.

---

## Script D — Monthly Aggregation (Not Yet Built)

**Purpose:** Read `linkedin_raw_jobs.json` + `job_title_mapping.json`,
aggregate job counts per field_id per month, and update `lag_model.json`
`monthly_postings_history` arrays.

**Counting logic:**
- For each job: look up title in job_title_mapping
- `primary_field_id` count += 1.0 (integer count)
- `secondary_field_ids` count += 0.5 each (partial credit — secondary field)
- Aggregate by `first_seen` month (YYYY-MM format)
- Output: monthly count per field_id

**Run schedule:** Every 15 days alongside Script C.

---

## Data Flow Summary

```
GitHub Actions (daily):
  Script B → appends to data-branch linkedin_raw_jobs.json

Every 15 days (local):
  Pull data-branch → verify → Script C → review mapping →
  Script D → validate lag_model → commit → push → Render redeploys

Backup (after each pull):
  backend/data/seeds/{filename}_backup_{YYYY_MM_DD}_{HHMM}.json
```

---

## Known Limitations

- LinkedIn guest API ceiling: ~1000-1200 jobs for Pakistan (authenticated
  internal API returns 6000+ but is not accessible without login)
- Historical data: only from Script A run date forward (May 2026).
  No pre-May 2026 market history available.
- Work_type: 12% of jobs have no work_type tag from employer — these
  remain null permanently
- GitHub Actions IP: LinkedIn may detect GitHub (AWS) IP ranges and
  rate limit. If consistent blocking occurs, migrate to Oracle Cloud
  Always Free VM for better IP reputation.

---

## Future Enhancement Triggers

- If GitHub Actions IP gets consistently blocked → migrate Script B to
  Oracle Cloud Always Free VM (ARM, 4 cores, 24GB, permanent free tier)
- If 15-day Script C/D cycle is too slow for market signal freshness →
  move Script D to weekly after sufficient mapping coverage
- If job_title_mapping.json grows large (>10,000 titles) → consider
  vector similarity for new title matching before sending to Gemini
