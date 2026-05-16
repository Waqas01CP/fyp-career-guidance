"""
Script B — LinkedIn daily collection.
Collects Pakistan jobs posted in the last 24 hours, enriches work_type via
three filter passes, runs a closure check on jobs >= 4 days old.
TEST_MODE=True (default): reads main files, writes results to temp file only.
TEST_MODE=False (production): writes directly to main data files.
No project imports. stdlib + requests + bs4 only.
"""

import json
import pathlib
import random
import re
import sys
import time
from collections import Counter
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# STEP 1 — Configuration
# ---------------------------------------------------------------------------

# Verbatim from scrape_linkedin_anytime.py
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

REQUEST_DELAY = 3
PAGE_DELAY = 2
PASS_DELAY = 15
RETRY_WAIT_BASE = 60
RETRY_WAIT = RETRY_WAIT_BASE   # alias — fetch_with_retry references RETRY_WAIT
MAX_RETRIES = 5
SAVE_INTERVAL = 25
CLOSURE_CHECK_MIN_AGE_DAYS = 4
CLOSURE_CHECK_MAX_PER_RUN = 300
TIME_FILTER = "r86400"
import os
TEST_MODE = os.environ.get("LINKEDIN_TEST_MODE", "true").lower() == "true"
# Default: True (safe for local testing)
# GitHub Actions sets LINKEDIN_TEST_MODE=false to run in production mode

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"
LOG_DIR = REPO_ROOT / "logs"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

RAW_JOBS_FILE  = DATA_DIR / "linkedin_raw_jobs.json"
SEEN_JOBS_FILE = DATA_DIR / "linkedin_seen_jobs.json"
TEMP_FILE      = DATA_DIR / "linkedin_daily_temp.json"
LOG_FILE       = LOG_DIR / f"scrape_linkedin_daily_{date.today()}.log"

# No PROGRESS_FILE — Script B does not need resume capability.
# Re-running is safe — deduplication prevents double-counting.


# ---------------------------------------------------------------------------
# STEP 2 — Shared functions (verbatim from scrape_linkedin_anytime.py)
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
    Extended parse — returns 5 keys.
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
        return None, parts[0]
    return parts[0], parts[-1]


def load_existing_data():
    """Load raw_jobs and seen_jobs from disk. Returns (dict, dict) — both keyed by job_id."""
    raw_jobs = {}
    seen_jobs = {}

    if RAW_JOBS_FILE.exists():
        try:
            with open(RAW_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
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

    total = len(raw_jobs)
    pct = (100 * enriched // total) if total else 0
    log_func(
        f"INFO | Work type enrichment complete — "
        f"{enriched}/{total} jobs labeled ({pct}%)"
    )


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
# STEP 3 — Modified save_data + TEST_MODE temp results
# ---------------------------------------------------------------------------

def save_data(raw_jobs, seen_jobs, log_func=None):
    """
    In TEST_MODE: does nothing — data is saved via save_temp_results.
    In production: atomic write to main files (same pattern as Script A).
    """
    if TEST_MODE:
        return  # temp results handled separately in save_temp_results()

    for path, data in [(RAW_JOBS_FILE, raw_jobs), (SEEN_JOBS_FILE, seen_jobs)]:
        tmp = path.with_suffix(".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp.replace(path)
        except Exception as e:
            if log_func:
                log_func(f"ERROR | save_data failed for {path.name}: {e}")


def save_temp_results(new_jobs, closure_updates, raw_jobs, log_func):
    """
    In TEST_MODE: writes a summary JSON to TEMP_FILE so results can be
    verified without touching the main data files.
    """
    wt_breakdown = dict(Counter(
        j.get("work_type") for j in new_jobs.values()
    ))
    et_breakdown = dict(Counter(
        j.get("employment_type") for j in new_jobs.values()
    ))

    temp_data = {
        "run_date": str(date.today()),
        "test_mode": True,
        "new_jobs_collected": len(new_jobs),
        "work_type_breakdown": wt_breakdown,
        "employment_type_breakdown": et_breakdown,
        "closure_candidates_checked": len(closure_updates),
        "closed_count": sum(
            1 for u in closure_updates if not u.get("still_active", True)
        ),
        "closure_updates": closure_updates,
        "new_jobs": new_jobs,
    }

    tmp = TEMP_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(temp_data, f, indent=2, ensure_ascii=False)
        tmp.replace(TEMP_FILE)
        log_func(f"INFO | TEST_MODE: temp results written to {TEMP_FILE}")
    except Exception as e:
        log_func(f"ERROR | save_temp_results failed: {e}")


# ---------------------------------------------------------------------------
# STEP 4 — Daily main pass and filter pass functions
# ---------------------------------------------------------------------------

def collect_daily_main_pass(session, raw_jobs, seen_jobs, log_func):
    """
    Paginate Pakistan jobs from last 24 hours (f_TPR=r86400), page * 10 increment.
    In TEST_MODE: fetches detail pages for quality data but does NOT write to main files.
    In production: fetches detail pages and saves to main files incrementally.
    Returns (new_count, new_jobs_dict).
    """
    page = 0
    new_count = 0
    new_jobs_dict = {}
    unsaved_count = 0
    consecutive_failures = 0

    log_func(f"INFO | Daily main pass starting (f_TPR={TIME_FILTER})")

    while True:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/"
            "seeMoreJobPostings/search"
            f"?location=Pakistan&geoId=101022442"
            f"&f_TPR={TIME_FILTER}&sortBy=DD&start={page * 10}"
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

            # Deduplicate — skip if already in seen_jobs
            if job_id in seen_jobs:
                try:
                    first = date.fromisoformat(seen_jobs[job_id].get("first_seen", str(date.today())))
                    seen_jobs[job_id]["last_seen"] = str(date.today())
                    seen_jobs[job_id]["duration_days"] = (date.today() - first).days
                except (ValueError, TypeError):
                    seen_jobs[job_id]["last_seen"] = str(date.today())
                continue

            # New job — fetch detail page (same in both modes for data quality)
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
                "source_script": "script_b",
                "source_time_filter": TIME_FILTER,
            }

            seen_record = {
                "first_seen": str(date.today()),
                "last_seen": str(date.today()),
                "duration_days": 0,
                "still_active": True,
            }

            if TEST_MODE:
                # Collect into local dict only — do NOT touch main files
                new_jobs_dict[job_id] = raw_record
            else:
                # Production: write to main files
                raw_jobs[job_id] = raw_record
                seen_jobs[job_id] = seen_record
                unsaved_count += 1
                if unsaved_count >= SAVE_INTERVAL:
                    save_data(raw_jobs, seen_jobs, log_func)
                    log_func(
                        f"INFO | Saved — total: {len(raw_jobs)} | "
                        f"new this session: {new_count + 1}"
                    )
                    unsaved_count = 0

            new_count += 1

        page += 1

    if not TEST_MODE and unsaved_count > 0:
        save_data(raw_jobs, seen_jobs, log_func)

    log_func(
        f"INFO | Daily main pass complete — "
        f"{new_count} new jobs found"
    )
    return new_count, new_jobs_dict


def collect_daily_filter_pass(session, pass_name, f_wt_value, log_func):
    """
    Paginate LinkedIn with work_type filter + 24-hour time filter.
    Collect job_ids only — no detail fetches. page * 10 increment.
    TEST_MODE has no effect — filter passes always run the same way.
    Returns set of job_id strings.
    """
    job_ids = set()
    page = 0
    consecutive_failures = 0

    log_func(f"INFO | {pass_name} (f_WT={f_wt_value}, f_TPR={TIME_FILTER}) starting")

    while True:
        url = (
            "https://www.linkedin.com/jobs-guest/jobs/api/"
            "seeMoreJobPostings/search"
            f"?location=Pakistan&geoId=101022442"
            f"&f_WT={f_wt_value}&f_TPR={TIME_FILTER}&sortBy=DD&start={page * 10}"
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

    log_func(f"INFO | {pass_name} complete — {len(job_ids)} job_ids collected")
    return job_ids


# ---------------------------------------------------------------------------
# STEP 5 — Closure check
# ---------------------------------------------------------------------------

def collect_closure_check(raw_jobs, seen_jobs, session, log_func):
    """
    Check jobs >= CLOSURE_CHECK_MIN_AGE_DAYS old for closure.
    In TEST_MODE: identifies closed jobs but does NOT update main files.
    In production: updates raw_jobs and seen_jobs directly.
    Returns list of closure update dicts for logging/temp file.
    """
    cutoff = date.today() - timedelta(days=CLOSURE_CHECK_MIN_AGE_DAYS)

    # Select candidates: still_active, age >= cutoff, sorted oldest first
    candidates = []
    for job_id, seen_data in seen_jobs.items():
        if not seen_data.get("still_active", True):
            continue
        try:
            first_seen = date.fromisoformat(seen_data.get("first_seen", str(date.today())))
        except (ValueError, TypeError):
            continue
        if first_seen <= cutoff:
            candidates.append((first_seen, job_id))

    candidates.sort()  # oldest first
    candidates = candidates[:CLOSURE_CHECK_MAX_PER_RUN]

    log_func(
        f"INFO | Closure check — {len(candidates)} candidates "
        f"(age >= {CLOSURE_CHECK_MIN_AGE_DAYS} days, cap={CLOSURE_CHECK_MAX_PER_RUN})"
    )

    closure_updates = []

    for first_seen, job_id in candidates:
        detail_url = (
            f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        )
        time.sleep(2)
        response = fetch_with_retry(detail_url, session, log_func)

        duration = (date.today() - first_seen).days

        if response is None or response.status_code == 404:
            still_active = False
            closure_method = "daily_check_404"
        elif "no longer accepting" in response.text.lower():
            still_active = False
            closure_method = "daily_check_expired"
        else:
            still_active = True
            closure_method = None

        update = {
            "job_id": job_id,
            "still_active": still_active,
            "closure_method": closure_method,
            "duration_days": duration,
        }
        closure_updates.append(update)

        if not TEST_MODE:
            # Production: update main files directly
            if job_id in seen_jobs:
                seen_jobs[job_id]["still_active"] = still_active
                seen_jobs[job_id]["last_seen"] = str(date.today())
                seen_jobs[job_id]["duration_days"] = duration
            if job_id in raw_jobs:
                raw_jobs[job_id]["still_active"] = still_active
                raw_jobs[job_id]["last_seen"] = str(date.today())
                raw_jobs[job_id]["duration_days"] = duration
                if closure_method:
                    raw_jobs[job_id]["closure_method"] = closure_method

        if not still_active:
            log_func(
                f"INFO | CLOSED | job_id={job_id} | method={closure_method} | "
                f"duration={duration}d"
            )

    closed_count = sum(1 for u in closure_updates if not u.get("still_active", True))
    log_func(
        f"INFO | Closure check complete — "
        f"{closed_count}/{len(closure_updates)} jobs closed"
    )
    return closure_updates


# ---------------------------------------------------------------------------
# STEP 6 — Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    log_func = setup_logger(LOG_FILE)
    mode_label = "TEST MODE" if TEST_MODE else "PRODUCTION"
    log_func(f"INFO | Script B starting ({mode_label}) — {datetime.now().isoformat()}")
    log_func(f"INFO | Time filter: last 24 hours (f_TPR={TIME_FILTER})")
    if TEST_MODE:
        log_func(f"INFO | TEST_MODE=True — main files will NOT be modified")
        log_func(f"INFO | Results will be written to {TEMP_FILE}")

    raw_jobs, seen_jobs = load_existing_data()
    log_func(f"INFO | Loaded existing data — {len(raw_jobs)} jobs in database")

    session = requests.Session()

    try:
        # Main pass
        log_func("INFO | Starting daily main pass (f_TPR=r86400)")
        new_count, new_jobs = collect_daily_main_pass(
            session, raw_jobs, seen_jobs, log_func
        )
        log_func(f"INFO | Main pass complete — {new_count} new jobs found")

        time.sleep(PASS_DELAY)

        # Filter passes — work_type inference
        log_func("INFO | Starting Pass 1 — On-site (f_WT=1)")
        onsite_ids = collect_daily_filter_pass(session, "onsite", "1", log_func)
        time.sleep(PASS_DELAY)

        log_func("INFO | Starting Pass 2 — Remote (f_WT=2)")
        remote_ids = collect_daily_filter_pass(session, "remote", "2", log_func)
        time.sleep(PASS_DELAY)

        log_func("INFO | Starting Pass 3 — Hybrid (f_WT=3)")
        hybrid_ids = collect_daily_filter_pass(session, "hybrid", "3", log_func)

        # Cross-reference work_type on appropriate dict
        if TEST_MODE:
            enrich_work_type(new_jobs, onsite_ids, remote_ids, hybrid_ids, log_func)
        else:
            enrich_work_type(raw_jobs, onsite_ids, remote_ids, hybrid_ids, log_func)
            save_data(raw_jobs, seen_jobs, log_func)

        # Closure check
        log_func(
            f"INFO | Starting closure check (jobs >= {CLOSURE_CHECK_MIN_AGE_DAYS} days old)"
        )
        closure_updates = collect_closure_check(
            raw_jobs, seen_jobs, session, log_func
        )

        # Save results
        if TEST_MODE:
            save_temp_results(new_jobs, closure_updates, raw_jobs, log_func)
        else:
            save_data(raw_jobs, seen_jobs, log_func)

        # Summary
        total = len(raw_jobs)
        active = sum(1 for j in seen_jobs.values() if j.get("still_active"))
        log_func(
            f"INFO | Script B complete ({mode_label})\n"
            f"  New jobs today:         {new_count}\n"
            f"  Total in database:      {total}\n"
            f"  Still active:           {active}\n"
            f"  Closure updates:        {len(closure_updates)}"
        )
        if TEST_MODE:
            log_func(f"INFO | Verify results at: {TEMP_FILE}")
            log_func(f"INFO | To run in production: set TEST_MODE = False")

        sys.exit(0)

    except KeyboardInterrupt:
        log_func("WARN | Interrupted by user")
        if not TEST_MODE:
            save_data(raw_jobs, seen_jobs, log_func)
        sys.exit(0)

    except Exception as e:
        log_func(f"ERROR | Unexpected: {type(e).__name__}: {e}")
        if not TEST_MODE:
            save_data(raw_jobs, seen_jobs, log_func)
        sys.exit(1)

    finally:
        session.close()
