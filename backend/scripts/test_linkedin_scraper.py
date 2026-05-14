"""
LinkedIn Guest API — feasibility test script.
Fetches 10 Pakistan jobs, validates field extraction, prints data quality report.
No project imports. No data files written. stdlib + requests + bs4 only.
"""

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

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

REQUEST_DELAY = 3
RETRY_WAIT = 60
MAX_RETRIES = 3
TEST_JOB_COUNT = 10

SEARCH_URL = (
    "https://www.linkedin.com/jobs-guest/jobs/api/"
    "seeMoreJobPostings/search"
    "?location=Pakistan&geoId=101022442&sortBy=DD&start=0"
)
DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

LOG_DIR = pathlib.Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"test_linkedin_scraper_{date.today()}.log"


# ---------------------------------------------------------------------------
# STEP 2 — Resilient fetch
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


# ---------------------------------------------------------------------------
# STEP 3 — Parse functions
# ---------------------------------------------------------------------------

def _extract_job_id(card):
    """Try multiple strategies to extract job_id from a card tag."""
    # Strategy 1: data-entity-urn attribute directly on card or child
    urn = card.get("data-entity-urn", "")
    if not urn:
        child = card.find(attrs={"data-entity-urn": re.compile(r"jobPosting")})
        if child:
            urn = child.get("data-entity-urn", "")
    if urn:
        match = re.search(r":(\d+)$", urn)
        if match:
            return match.group(1)

    # Strategy 2: data-job-id attribute
    jid = card.get("data-job-id", "")
    if jid:
        return jid.strip()

    # Strategy 3: href in any <a> tag — job ID is a long number at end of slug or in URL
    for a in card.find_all("a", href=True):
        href = a["href"]
        # Direct numeric ID after /jobs/view/
        m = re.search(r"/jobs/view/(\d+)", href)
        if m:
            return m.group(1)
        # Slugified URL: /jobs/view/some-title-4413549980
        m = re.search(r"-(\d{8,})(?:\?|$|/)", href)
        if m:
            return m.group(1)
        # Number anywhere in URL that looks like a job ID
        m = re.search(r"[/-](\d{9,})(?:\?|&|$)", href)
        if m:
            return m.group(1)

    return None


def parse_search_page(html_text):
    """Parse LinkedIn search result HTML → list of job dicts."""
    jobs = []
    try:
        soup = BeautifulSoup(html_text, "html.parser")

        # LinkedIn guest API wraps each job in a <div data-entity-urn="urn:li:jobPosting:...">
        # These divs are children of <li> elements
        cards = soup.find_all("div", {"data-entity-urn": re.compile(r"jobPosting")})
        if not cards:
            # Fallback: find by class
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
            link_tag = card.find("a", class_=re.compile(r"base-card__full-link|job.*link", re.I)) or card.find("a", href=re.compile(r"/jobs/view/"))
            if link_tag:
                job_url = link_tag.get("href", "").split("?")[0]

            # Posted date
            time_tag = card.find("time")
            if time_tag:
                posted_date = time_tag.get("datetime") or time_tag.get_text(strip=True)
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
        # parse_search_page never raises — returns empty list on total failure
        print(f"[PARSE_WARN] parse_search_page exception: {exc}")

    return jobs


def parse_job_detail(html_text, job_id):
    """Parse job detail HTML → dict with 4 criteria fields."""
    result = {
        "employment_type": None,
        "work_type": None,
        "seniority_level": None,
        "industry": None,
    }
    try:
        soup = BeautifulSoup(html_text, "html.parser")

        # LinkedIn detail page has a criteria list — multiple possible structures
        # Structure A: <ul class="description__job-criteria-list">
        # Structure B: spans with class job-criteria-item__text

        criteria_items = soup.find_all(
            "li", class_=re.compile(r"description__job-criteria-item|job-criteria-item")
        )

        if not criteria_items:
            # Try alternate structure: look for spans with criteria text
            criteria_items = soup.find_all("div", class_=re.compile(r"job-criteria"))

        for item in criteria_items:
            # Header label
            header = item.find(
                ["h3", "span"],
                class_=re.compile(r"criteria.*subheader|criteria.*label|job-criteria.*header", re.I),
            )
            # Value
            value_tag = item.find(
                ["span", "div"],
                class_=re.compile(r"criteria.*text|job-criteria.*text", re.I),
            )

            if not header or not value_tag:
                # Try raw text — first child text = label, second = value
                texts = [t.strip() for t in item.stripped_strings]
                if len(texts) >= 2:
                    header_text = texts[0].lower()
                    value_text = texts[1]
                else:
                    continue
            else:
                header_text = header.get_text(strip=True).lower()
                value_text = value_tag.get_text(strip=True)

            if "seniority" in header_text or "level" in header_text:
                result["seniority_level"] = value_text
            elif "employment" in header_text or "job type" in header_text:
                result["employment_type"] = value_text
            elif "job function" in header_text or "industry" in header_text:
                result["industry"] = value_text
            elif "work" in header_text and ("type" in header_text or "location" in header_text or "model" in header_text):
                result["work_type"] = value_text
            elif "on-site" in value_text.lower() or "remote" in value_text.lower() or "hybrid" in value_text.lower():
                if result["work_type"] is None:
                    result["work_type"] = value_text
            elif "full-time" in value_text.lower() or "part-time" in value_text.lower() or "contract" in value_text.lower():
                if result["employment_type"] is None:
                    result["employment_type"] = value_text

    except Exception as exc:
        print(f"[PARSE_WARN] parse_job_detail job_id={job_id} exception: {exc}")

    return result


# ---------------------------------------------------------------------------
# STEP 4 — Main execution
# ---------------------------------------------------------------------------

def main():
    # Safe console output on Windows (cp1252 can't handle some Unicode chars in location names)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # Set up log function
    log_lines = []

    def log_func(msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {msg}"
        log_lines.append(line)
        print(line)

    def flush_log():
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            for line in log_lines:
                f.write(line + "\n")
        log_lines.clear()

    log_func("=== LinkedIn Scraper Test START ===")
    log_func(f"Log file: {LOG_FILE}")

    session = requests.Session()

    # (c) Fetch search page
    log_func(f"Fetching search URL: {SEARCH_URL}")
    resp = fetch_with_retry(SEARCH_URL, session, log_func)

    # (d) Handle search failure
    if resp is None:
        msg = "SEARCH ENDPOINT FAILED — cannot continue test"
        log_func(msg)
        print(msg)
        flush_log()
        session.close()
        sys.exit(1)

    # (e) Parse search page
    jobs = parse_search_page(resp.text)
    log_func(f"Jobs found on page: {len(jobs)}")

    # (g) Zero jobs
    if len(jobs) == 0:
        msg = "NO JOBS PARSED — check selectors"
        log_func(msg)
        # Log a snippet of the HTML to help diagnose
        log_func(f"HTML snippet (first 2000 chars): {resp.text[:2000]}")
        print(msg)
        flush_log()
        session.close()
        sys.exit(1)

    # (h) Fewer than TEST_JOB_COUNT
    if len(jobs) < TEST_JOB_COUNT:
        log_func(f"Warning: only {len(jobs)} jobs found — continuing with all available")

    # (i) Take first TEST_JOB_COUNT
    jobs_to_test = jobs[:TEST_JOB_COUNT]
    log_func(f"Testing {len(jobs_to_test)} jobs")

    # (j) Fetch each job detail
    results = []
    detail_ok_count = 0
    detail_fail_count = 0

    for idx, job in enumerate(jobs_to_test, 1):
        job_id = job["job_id"]
        log_func(f"--- Job {idx}/{len(jobs_to_test)} | job_id={job_id}")

        time.sleep(REQUEST_DELAY)

        detail_url = DETAIL_URL.format(job_id=job_id)
        detail_resp = fetch_with_retry(detail_url, session, log_func)

        record = dict(job)

        if detail_resp is None:
            record.update({
                "employment_type": None,
                "work_type": None,
                "seniority_level": None,
                "industry": None,
                "detail_status": "FETCH_FAILED",
            })
            detail_fail_count += 1
            log_func(f"SKIP | job_id={job_id} | reason=FETCH_FAILED")
        else:
            detail = parse_job_detail(detail_resp.text, job_id)
            record.update(detail)
            record["detail_status"] = "OK"
            detail_ok_count += 1

        results.append(record)

    session.close()

    # ---------------------------------------------------------------------------
    # STEP 5 — Formatted output
    # ---------------------------------------------------------------------------

    print()
    print("=" * 60)
    print(f"LINKEDIN SCRAPER TEST — {len(results)} JOBS TESTED")
    print("Pakistan | All job types | Sorted by date posted")
    print("=" * 60)

    for i, r in enumerate(results, 1):
        print(f"\nJob {i}:")
        print(f"  ID:             {r.get('job_id', 'N/A')}")
        print(f"  Title:          {r.get('title', 'N/A')}")
        print(f"  Company:        {r.get('company', 'N/A')}")
        print(f"  Location:       {r.get('location_raw', 'N/A')}")
        print(f"  Posted:         {r.get('posted_date', 'N/A')}")
        print(f"  Employment:     {r.get('employment_type', 'N/A')}")
        print(f"  Work Type:      {r.get('work_type', 'N/A')}")
        print(f"  Seniority:      {r.get('seniority_level', 'N/A')}")
        print(f"  Industry:       {r.get('industry', 'N/A')}")
        print(f"  Detail Status:  {r.get('detail_status', 'N/A')}")
        print("  ---")

    # Data quality counts
    ok_results = [r for r in results if r.get("detail_status") == "OK"]
    n_ok = len(ok_results)

    def field_count(field):
        return sum(1 for r in ok_results if r.get(field) is not None)

    def pct(num, denom):
        return f"{int(num / denom * 100)}%" if denom > 0 else "N/A"

    print()
    print("=" * 60)
    print("DATA QUALITY REPORT")
    print("=" * 60)
    print(f"Search endpoint:     OK")
    print(f"Jobs found on page:  {len(jobs)}")
    print(f"Jobs tested:         {len(results)}")
    print(f"Detail fetches:      {detail_ok_count} succeeded / {detail_fail_count} failed")
    print()
    print(f"Field population (of {n_ok} successful detail fetches):")
    et = field_count("employment_type")
    wt = field_count("work_type")
    sl = field_count("seniority_level")
    ind = field_count("industry")
    print(f"  employment_type:   {et}/{n_ok} ({pct(et, n_ok)})")
    print(f"  work_type:         {wt}/{n_ok} ({pct(wt, n_ok)})")
    print(f"  seniority_level:   {sl}/{n_ok} ({pct(sl, n_ok)})")
    print(f"  industry:          {ind}/{n_ok} ({pct(ind, n_ok)})")
    print()
    print(f"Log file written to: logs/test_linkedin_scraper_{date.today()}.log")
    print()

    # Verdict logic
    search_ok = True
    details_ok_ratio = detail_ok_count >= 7
    et_ratio = (et / n_ok >= 0.60) if n_ok > 0 else False

    if search_ok and details_ok_ratio and et_ratio:
        verdict = "PROCEED"
        verdict_reason = "All conditions met"
    else:
        verdict = "INVESTIGATE"
        reasons = []
        if not details_ok_ratio:
            reasons.append(f"only {detail_ok_count}/10 detail fetches succeeded (need ≥7)")
        if not et_ratio:
            reasons.append(f"employment_type population {pct(et, n_ok)} < 60%")
        verdict_reason = "; ".join(reasons)

    print(f"VERDICT: {verdict}")
    if verdict == "INVESTIGATE":
        print(f"Reason: {verdict_reason}")
    print("=" * 60)

    # Final log line
    log_func(
        f"COMPLETE | jobs_tested={len(results)} | details_ok={detail_ok_count} "
        f"| details_failed={detail_fail_count} | verdict={verdict}"
    )
    flush_log()

    sys.exit(0)


if __name__ == "__main__":
    main()
