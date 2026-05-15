"""
Script A — LinkedIn one-time pull.
Paginates all Pakistan jobs on LinkedIn guest API, fetches details, enriches
work_type via filter passes. Writes backend/data/linkedin_raw_jobs.json and
backend/data/linkedin_seen_jobs.json. Resumes from interruption via progress file.
No project imports. stdlib + requests + bs4 only.
"""

import json
import pathlib
import random
import re
import sys
import time
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# STEP 1 — Configuration
# ---------------------------------------------------------------------------

# Verbatim from test_linkedin_scraper.py
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

REQUEST_DELAY = 3        # seconds between per-job detail fetches
PAGE_DELAY = 2           # seconds between search result page fetches
PASS_DELAY = 30          # seconds to wait between passes
RETRY_WAIT_BASE = 60     # base seconds to wait on first 429
RETRY_WAIT = RETRY_WAIT_BASE  # alias — fetch_with_retry (verbatim) references RETRY_WAIT
MAX_RETRIES = 5          # more retries than test script for long-running stability
SAVE_INTERVAL = 25       # write to disk every N new jobs processed
LOG_LEVEL = "INFO"       # INFO or DEBUG

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"
LOG_DIR = REPO_ROOT / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

RAW_JOBS_FILE = DATA_DIR / "linkedin_raw_jobs.json"
SEEN_JOBS_FILE = DATA_DIR / "linkedin_seen_jobs.json"
LOG_FILE = LOG_DIR / f"scrape_linkedin_anytime_{date.today()}.log"
PROGRESS_FILE = DATA_DIR / "linkedin_scrape_progress.json"


# ---------------------------------------------------------------------------
# STEP 2 — Fetch and parse functions
# ---------------------------------------------------------------------------

def fetch_with_retry(url, session, log_func):
    """GET url with retry on 429/Timeout/ConnectionError. Returns Response or None."""
    for attempt in range(1, MAX_RETRIES + 1):
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        t0 = time.monotonic()
        try:
            resp = session.get(url, headers=headers, timeout=15)
            elapsed = int((time.monotonic() - t0) * 1000)
            log_func(f"STATUS {resp.status_code} | {elapsed}ms | {url[:80]}")

            if resp.status_code == 200:
                return resp

            if resp.status_code == 429:
                log_func(f"RETRY {attempt}/{MAX_RETRIES} | reason=429 | url={url[:80]}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_WAIT)
                continue

            # Other non-200
            log_func(f"NON_200 {resp.status_code} | url={url[:80]}")
            return None

        except requests.exceptions.Timeout:
            elapsed = int((time.monotonic() - t0) * 1000)
            log_func(f"RETRY {attempt}/{MAX_RETRIES} | reason=TIMEOUT | url={url[:80]}")
            if attempt < MAX_RETRIES:
                time.sleep(10)

        except requests.exceptions.ConnectionError:
            log_func(f"RETRY {attempt}/{MAX_RETRIES} | reason=CONNECTION ERROR | url={url[:80]}")
            if attempt < MAX_RETRIES:
                time.sleep(10)

        except Exception as exc:
            log_func(f"UNEXPECTED_ERROR | {type(exc).__name__}: {exc} | url={url[:80]}")
            return None

    log_func(f"GAVE UP on {url[:80]}")
    return None


def _extract_job_id(card):
    """Try multiple strategies to extract job_id from a card tag."""
    # Strategy 1: data-entity-urn on card itself or child div
    urn = card.get("data-entity-urn", "")
    if not urn:
        child = card.find(attrs={"data-entity-urn": re.compile(r"jobPosting")})
        if child:
            urn = child.get("data-entity-urn", "")
    if urn:
        m = re.search(r":(\d+)$", urn)
        if m:
            return m.group(1)

    # Strategy 2: data-job-id attribute
    jid = card.get("data-job-id", "")
    if jid:
        return jid.strip()

    # Strategy 3: href — job ID is a long number at end of slug or directly in URL
    for a in card.find_all("a", href=True):
        href = a["href"]
        m = re.search(r"/jobs/view/(\d+)", href)
        if m:
            return m.group(1)
        m = re.search(r"-(\d{8,})(?:\?|$|/)", href)
        if m:
            return m.group(1)
        m = re.search(r"[/-](\d{9,})(?:\?|&|$)", href)
        if m:
            return m.group(1)

    return None


def parse_search_page(html_text):
    """Parse LinkedIn search result HTML → list of job dicts."""
    jobs = []
    try:
        soup = BeautifulSoup(html_text, "html.parser")

        # Primary: divs with data-entity-urn="urn:li:jobPosting:..."
        cards = soup.find_all("div", {"data-entity-urn": re.compile(r"jobPosting")})
        if not cards:
            cards = soup.find_all("div", class_=re.compile(r"base-card|job-search-card"))

        for card in cards:
            job_id = _extract_job_id(card)
            if not job_id:
                continue

            # Title
            title_tag = (
                card.find("h3", class_=re.compile(r"base-search-card__title"))
                or card.find("h3")
                or card.find("span", class_=re.compile(r"title|job.*title", re.I))
            )
            title = title_tag.get_text(strip=True) if title_tag else None

            # Company
            company_tag = (
                card.find("h4", class_=re.compile(r"base-search-card__subtitle"))
                or card.find("h4")
                or card.find("a", class_=re.compile(r"company|employer", re.I))
            )
            company = company_tag.get_text(strip=True) if company_tag else None

            # Location
            loc_tag = (
                card.find("span", class_=re.compile(r"job-search-card__location"))
                or card.find("span", class_=re.compile(r"location", re.I))
            )
            location_raw = loc_tag.get_text(strip=True) if loc_tag else None

            # Job URL
            job_url = None
            link_tag = (
                card.find("a", class_=re.compile(r"base-card__full-link|job.*link", re.I))
                or card.find("a", href=re.compile(r"/jobs/view/"))
            )
            if link_tag:
                job_url = link_tag.get("href", "").split("?")[0]

            # Posted date — try datetime attr first, then visible text, then null
            time_tag = card.find("time")
            if time_tag:
                posted_date = time_tag.get("datetime") or time_tag.get_text(strip=True) or None
            else:
                posted_date = None

            jobs.append({
                "job_id": job_id,
                "title": title,
                "company": company,
                "location_raw": location_raw,
                "job_url": job_url,
                "posted_date": posted_date,
            })

    except Exception as exc:
        print(f"[PARSE_WARN] parse_search_page exception: {exc}")

    return jobs


def parse_job_detail(html_text, job_id):
    """
    Extended parse — returns 5 keys (not 4 like test script).
    job_functions is a list; industry and job_functions are kept separate.
    work_type is always None (guest API does not expose it in detail HTML).
    """
    result = {
        "employment_type": None,
        "seniority_level": None,
        "industry": None,
        "job_functions": [],
        "work_type": None,
    }
    try:
        soup = BeautifulSoup(html_text, "html.parser")

        criteria_items = soup.find_all(
            "li", class_=re.compile(r"description__job-criteria-item|job-criteria-item")
        )
        if not criteria_items:
            criteria_items = soup.find_all("div", class_=re.compile(r"job-criteria"))

        if not criteria_items:
            print(f"[PARSE_WARN] parse_job_detail job_id={job_id} | criteria section not found")

        for item in criteria_items:
            header = item.find(
                ["h3", "span"],
                class_=re.compile(r"criteria.*subheader|criteria.*label|job-criteria.*header", re.I),
            )
            value_tag = item.find(
                ["span", "div"],
                class_=re.compile(r"criteria.*text|job-criteria.*text", re.I),
            )

            if not header or not value_tag:
                texts = [t.strip() for t in item.stripped_strings]
                if len(texts) >= 2:
                    header_text = texts[0].lower()
                    value_text = texts[1]
                else:
                    continue
            else:
                header_text = header.get_text(strip=True).lower()
                value_text = value_tag.get_text(strip=True)

            if not value_text:
                continue

            if "seniority" in header_text or "level" in header_text:
                result["seniority_level"] = value_text
            elif "employment" in header_text or "job type" in header_text:
                result["employment_type"] = value_text
            elif "job function" in header_text or "function" in header_text:
                # Store as list — split on comma+and patterns
                funcs = re.split(r",\s*(?:and\s+)?|\s+and\s+", value_text)
                result["job_functions"] = [f.strip() for f in funcs if f.strip()]
            elif "industri" in header_text:
                result["industry"] = value_text
            elif "full-time" in value_text.lower() or "part-time" in value_text.lower() or "contract" in value_text.lower():
                if result["employment_type"] is None:
                    result["employment_type"] = value_text

    except Exception as exc:
        print(f"[PARSE_WARN] parse_job_detail job_id={job_id} exception: {exc}")

    return result


def extract_city_country(location_raw):
    """
    Split location string into (city, country).
    "Karachi, Pakistan" → ("Karachi", "Pakistan")
    "Lahore, Punjab, Pakistan" → ("Lahore", "Pakistan")
    "Pakistan" → (None, "Pakistan")
    None/"" → (None, None)
    """
    if not location_raw or not location_raw.strip():
        return None, None
    parts = [p.strip() for p in location_raw.split(",")]
    if len(parts) == 1:
        # Could be just a country or just a city
        return None, parts[0]
    # First part = city, last part = country (middle parts = state/province, ignored)
    return parts[0], parts[-1]


# ---------------------------------------------------------------------------
# STEP 3 — File I/O with atomic writes and progress tracking
# ---------------------------------------------------------------------------

def load_existing_data():
    """Load raw_jobs and seen_jobs from disk. Returns (dict, dict) — both keyed by job_id."""
    raw_jobs = {}
    seen_jobs = {}

    if RAW_JOBS_FILE.exists():
        try:
            with open(RAW_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Support both list format and dict-by-job_id format
            if isinstance(data, list):
                raw_jobs = {j["job_id"]: j for j in data if "job_id" in j}
            elif isinstance(data, dict):
                raw_jobs = data
            print(f"[load] Loaded {len(raw_jobs)} raw jobs from {RAW_JOBS_FILE}")
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"[WARN] Malformed {RAW_JOBS_FILE}: {e} — starting with empty dict")

    if SEEN_JOBS_FILE.exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                seen_jobs = json.load(f)
            if not isinstance(seen_jobs, dict):
                print(f"[WARN] {SEEN_JOBS_FILE} not a dict — resetting")
                seen_jobs = {}
            print(f"[load] Loaded {len(seen_jobs)} seen job IDs from {SEEN_JOBS_FILE}")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[WARN] Malformed {SEEN_JOBS_FILE}: {e} — starting with empty dict")

    return raw_jobs, seen_jobs


def save_data(raw_jobs, seen_jobs):
    """Atomically write both data files (.tmp → rename)."""
    for target, data in [(RAW_JOBS_FILE, raw_jobs), (SEEN_JOBS_FILE, seen_jobs)]:
        tmp = target.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp.replace(target)
        except Exception as e:
            print(f"[ERROR] Failed to save {target}: {e}")
            if tmp.exists():
                try:
                    tmp.unlink()
                except Exception:
                    pass


def save_progress(pass_name, page_number):
    """Update PROGRESS_FILE with last completed page for this pass."""
    progress = {}
    if PROGRESS_FILE.exists():
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                progress = json.load(f)
        except (json.JSONDecodeError, TypeError):
            progress = {}
    progress[pass_name] = page_number
    tmp = PROGRESS_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)
        tmp.replace(PROGRESS_FILE)
    except Exception as e:
        print(f"[ERROR] Failed to save progress: {e}")


def load_progress(pass_name):
    """Return last completed page for pass_name, or 0 if none."""
    if not PROGRESS_FILE.exists():
        return 0
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress = json.load(f)
        return int(progress.get(pass_name, 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# STEP 4 — Main pass
# ---------------------------------------------------------------------------

def collect_main_pass(session, raw_jobs, seen_jobs, log_func):
    """
    Paginate all Pakistan jobs (anytime, no work_type filter).
    Fetch detail for each NEW job_id. Save incrementally every SAVE_INTERVAL jobs.
    Returns count of new jobs added this session.
    """
    start_page = load_progress("main_pass")
    page = start_page
    new_jobs_this_session = 0
    unsaved_count = 0
    consecutive_failures = 0

    log_func(f"INFO | Main pass resuming from page {page}")

    while True:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/"
            f"seeMoreJobPostings/search"
            f"?location=Pakistan&geoId=101022442&sortBy=DD&start={page * 10}"
        )

        time.sleep(PAGE_DELAY)
        response = fetch_with_retry(url, session, log_func)

        if response is None:
            consecutive_failures += 1
            log_func(f"WARN | Page {page} fetch failed — consecutive_failures={consecutive_failures}")
            if consecutive_failures >= 3:
                log_func("STOP | 3 consecutive page failures — ending main pass")
                break
            page += 1
            continue

        consecutive_failures = 0
        jobs_on_page = parse_search_page(response.text)
        log_func(f"INFO | Page {page} → {len(jobs_on_page)} cards")

        if not jobs_on_page:
            log_func(f"INFO | Page {page} returned 0 jobs — end of results")
            break

        for job in jobs_on_page:
            job_id = job.get("job_id")
            if not job_id:
                continue

            # Deduplicate — update last_seen and duration for existing jobs
            if job_id in seen_jobs:
                try:
                    first = date.fromisoformat(seen_jobs[job_id].get("first_seen", str(date.today())))
                    seen_jobs[job_id]["last_seen"] = str(date.today())
                    seen_jobs[job_id]["duration_days"] = (date.today() - first).days
                except (ValueError, TypeError):
                    seen_jobs[job_id]["last_seen"] = str(date.today())
                continue

            # New job — fetch detail
            time.sleep(REQUEST_DELAY)
            detail_url = (
                f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            )
            detail_response = fetch_with_retry(detail_url, session, log_func)

            if detail_response is None:
                detail = {
                    "employment_type": None,
                    "seniority_level": None,
                    "industry": None,
                    "job_functions": [],
                }
                log_func(f"WARN | Detail fetch failed for {job_id} — storing nulls")
            else:
                detail = parse_job_detail(detail_response.text, job_id)

            city, country = extract_city_country(job.get("location_raw"))

            raw_record = {
                "job_id": job_id,
                "title": job.get("title"),
                "company": job.get("company"),
                "location_raw": job.get("location_raw"),
                "city": city,
                "country": country,
                "posted_date": job.get("posted_date"),
                "first_seen": str(date.today()),
                "last_seen": str(date.today()),
                "duration_days": 0,
                "still_active": True,
                "closure_method": None,
                "employment_type": detail.get("employment_type"),
                "work_type": None,
                "seniority_level": detail.get("seniority_level"),
                "industry": detail.get("industry"),
                "job_functions": detail.get("job_functions", []),
                "source_script": "script_a",
                "source_time_filter": "anytime",
            }

            seen_record = {
                "first_seen": str(date.today()),
                "last_seen": str(date.today()),
                "duration_days": 0,
                "still_active": True,
            }

            raw_jobs[job_id] = raw_record
            seen_jobs[job_id] = seen_record
            new_jobs_this_session += 1
            unsaved_count += 1

            if unsaved_count >= SAVE_INTERVAL:
                save_data(raw_jobs, seen_jobs)
                save_progress("main_pass", page)
                log_func(
                    f"INFO | Saved — total: {len(raw_jobs)} | "
                    f"new this session: {new_jobs_this_session}"
                )
                unsaved_count = 0

        page += 1

    # Final save after pass completes
    save_data(raw_jobs, seen_jobs)
    save_progress("main_pass", page)
    log_func(
        f"INFO | Main pass complete — "
        f"new jobs: {new_jobs_this_session} | "
        f"total in database: {len(raw_jobs)}"
    )
    return new_jobs_this_session


# ---------------------------------------------------------------------------
# STEP 5 — Filter pass (lightweight — job_ids only, no detail fetch)
# ---------------------------------------------------------------------------

def collect_filter_pass(session, pass_name, f_wt_value, log_func):
    """
    Paginate LinkedIn with work_type filter. Collect job_ids only — no detail fetches.
    Returns set of job_id strings.
    """
    job_ids = set()
    start_page = load_progress(pass_name)
    page = start_page
    consecutive_failures = 0

    log_func(f"INFO | {pass_name} (f_WT={f_wt_value}) resuming from page {page}")

    while True:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/"
            f"seeMoreJobPostings/search"
            f"?location=Pakistan&geoId=101022442"
            f"&f_WT={f_wt_value}&sortBy=DD&start={page * 10}"
        )

        time.sleep(PAGE_DELAY)
        response = fetch_with_retry(url, session, log_func)

        if response is None:
            consecutive_failures += 1
            if consecutive_failures >= 3:
                log_func(f"STOP | {pass_name}: 3 consecutive failures — ending pass")
                break
            page += 1
            continue

        consecutive_failures = 0
        jobs_on_page = parse_search_page(response.text)

        if not jobs_on_page:
            log_func(f"INFO | {pass_name}: page {page} returned 0 jobs — end of results")
            break

        for job in jobs_on_page:
            job_id = job.get("job_id")
            if job_id:
                job_ids.add(job_id)

        page += 1
        save_progress(pass_name, page)

    log_func(f"INFO | {pass_name} complete — {len(job_ids)} job_ids collected")
    return job_ids


# ---------------------------------------------------------------------------
# STEP 6 — Cross-reference work_type
# ---------------------------------------------------------------------------

def enrich_work_type(raw_jobs, onsite_ids, remote_ids, hybrid_ids, log_func):
    """
    Set work_type on each raw_job by cross-referencing filter pass sets.
    Priority: Remote > Hybrid > On-site.
    """
    enriched = 0
    for job_id, job_data in raw_jobs.items():
        if job_id in remote_ids:
            job_data["work_type"] = "Remote"
            enriched += 1
        elif job_id in hybrid_ids:
            job_data["work_type"] = "Hybrid"
            enriched += 1
        elif job_id in onsite_ids:
            job_data["work_type"] = "On-site"
            enriched += 1
        # else: work_type stays None — employer did not tag it

    total = len(raw_jobs)
    pct = (100 * enriched // total) if total else 0
    log_func(
        f"INFO | Work type enrichment complete — "
        f"{enriched}/{total} jobs labeled ({pct}%)"
    )


# ---------------------------------------------------------------------------
# STEP 8 — Logger setup
# ---------------------------------------------------------------------------

def setup_logger(log_file):
    """Returns a log_func that writes timestamped lines to file AND console."""
    log_file.parent.mkdir(exist_ok=True)
    f = open(log_file, "a", encoding="utf-8", buffering=1)  # line-buffered

    def log_func(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line)
        f.write(line + "\n")
        f.flush()

    return log_func


# ---------------------------------------------------------------------------
# STEP 7 — Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Safe console output on Windows
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    log_func = setup_logger(LOG_FILE)
    log_func(f"INFO | Script A starting — {datetime.now().isoformat()}")
    log_func(f"INFO | Output: {RAW_JOBS_FILE}")
    log_func(f"INFO | Log:    {LOG_FILE}")

    raw_jobs, seen_jobs = load_existing_data()
    log_func(f"INFO | Loaded existing data — {len(raw_jobs)} jobs in database")

    session = requests.Session()

    try:
        # Main pass
        log_func("INFO | Starting main pass (anytime, all jobs)")
        new_count = collect_main_pass(session, raw_jobs, seen_jobs, log_func)

        # Wait between passes
        log_func(f"INFO | Waiting {PASS_DELAY}s before filter passes")
        time.sleep(PASS_DELAY)

        # Filter passes (lightweight — job_ids only)
        log_func("INFO | Starting Pass 1 — On-site job_ids (f_WT=1)")
        onsite_ids = collect_filter_pass(session, "pass_onsite", "1", log_func)
        time.sleep(PASS_DELAY)

        log_func("INFO | Starting Pass 2 — Remote job_ids (f_WT=2)")
        remote_ids = collect_filter_pass(session, "pass_remote", "2", log_func)
        time.sleep(PASS_DELAY)

        log_func("INFO | Starting Pass 3 — Hybrid job_ids (f_WT=3)")
        hybrid_ids = collect_filter_pass(session, "pass_hybrid", "3", log_func)

        # Cross-reference work_type
        log_func("INFO | Enriching work_type from filter passes")
        enrich_work_type(raw_jobs, onsite_ids, remote_ids, hybrid_ids, log_func)

        # Final save with enriched work_type
        save_data(raw_jobs, seen_jobs)

        # Summary
        total = len(raw_jobs)
        with_work_type = sum(1 for j in raw_jobs.values() if j.get("work_type") is not None)
        log_func(
            f"INFO | Script A complete\n"
            f"  Total jobs in database: {total}\n"
            f"  New jobs this run:      {new_count}\n"
            f"  Work type labeled:      {with_work_type} "
            f"({100 * with_work_type // total if total else 0}%)\n"
            f"  Output: {RAW_JOBS_FILE}"
        )

        # Clear progress file on clean completion
        if PROGRESS_FILE.exists():
            PROGRESS_FILE.unlink()
            log_func("INFO | Progress file cleared — clean completion")

        sys.exit(0)

    except KeyboardInterrupt:
        log_func("WARN | Interrupted by user — saving current state")
        save_data(raw_jobs, seen_jobs)
        log_func(f"INFO | Saved {len(raw_jobs)} jobs — resume by re-running script")
        sys.exit(0)

    except Exception as e:
        log_func(f"ERROR | Unexpected error: {type(e).__name__}: {e}")
        save_data(raw_jobs, seen_jobs)
        sys.exit(1)

    finally:
        session.close()
