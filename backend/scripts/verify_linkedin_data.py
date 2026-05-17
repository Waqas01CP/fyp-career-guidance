"""
LinkedIn data integrity verification script.
Run manually after pulling data from data-branch.
Usage: python backend/scripts/verify_linkedin_data.py
"""

import json
import pathlib
from datetime import date, datetime
from collections import Counter

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"
RAW_FILE = DATA_DIR / "linkedin_raw_jobs.json"
SEEN_FILE = DATA_DIR / "linkedin_seen_jobs.json"

def load_data():
    with open(RAW_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    with open(SEEN_FILE, encoding="utf-8") as f:
        seen = json.load(f)
    return raw, seen

def check_file_sync(raw, seen):
    """Check 1: raw_jobs and seen_jobs have same job_ids."""
    raw_ids = set(raw.keys())
    seen_ids = set(seen.keys())
    in_raw_not_seen = raw_ids - seen_ids
    in_seen_not_raw = seen_ids - raw_ids
    passed = not in_raw_not_seen and not in_seen_not_raw
    return {
        "passed": passed,
        "raw_count": len(raw_ids),
        "seen_count": len(seen_ids),
        "in_raw_not_seen": list(in_raw_not_seen)[:5],
        "in_seen_not_raw": list(in_seen_not_raw)[:5],
    }

def check_duplicates(raw):
    """Check 2: no duplicate job_ids (should never happen — dict keys are unique)."""
    # Additional check: job_id field inside record matches the dict key
    mismatches = []
    for key, job in raw.items():
        if job.get("job_id") and job["job_id"] != key:
            mismatches.append({"key": key, "job_id_field": job["job_id"]})
    return {
        "passed": len(mismatches) == 0,
        "total_jobs": len(raw),
        "mismatches_found": len(mismatches),
        "sample_mismatches": mismatches[:3],
    }

def check_closure_consistency(raw, seen):
    """
    Check 3: Internal consistency of closure data.
    - If still_active=False in seen → must have closure_method set
    - If still_active=False in seen → raw_jobs must also show still_active=False
    - If still_active=False in seen → last_seen must not be today
      (closed jobs should not have been seen today)
    """
    issues = []
    closed_jobs = []
    today = str(date.today())

    for job_id, seen_data in seen.items():
        still_active = seen_data.get("still_active", True)

        if not still_active:
            closed_jobs.append(job_id)

            # Check 3a: closure_method must be set
            if not seen_data.get("closure_method"):
                issues.append({
                    "job_id": job_id,
                    "issue": "still_active=False but closure_method is None"
                })

            # Check 3b: raw_jobs must also show closed
            if job_id in raw:
                raw_active = raw[job_id].get("still_active", True)
                if raw_active:
                    issues.append({
                        "job_id": job_id,
                        "issue": "seen_jobs shows closed but raw_jobs shows still_active=True"
                    })

            # Check 3c: last_seen should not be today (closed jobs not seen today)
            if seen_data.get("last_seen") == today:
                issues.append({
                    "job_id": job_id,
                    "issue": f"still_active=False but last_seen is today ({today})"
                })

    return {
        "passed": len(issues) == 0,
        "total_closed": len(closed_jobs),
        "issues_found": len(issues),
        "issues": issues[:10],
        "closure_methods": dict(Counter(
            seen[jid].get("closure_method")
            for jid in closed_jobs
        )) if closed_jobs else {},
    }

def check_active_jobs_freshness(seen):
    """
    Check 4: Active jobs should have last_seen updated recently.
    If last_seen is more than 7 days ago for an active job,
    the daily scraper may not be running correctly.
    """
    today = date.today()
    stale_threshold_days = 7
    stale_jobs = []

    for job_id, data in seen.items():
        if not data.get("still_active", True):
            continue
        last_seen_str = data.get("last_seen")
        if not last_seen_str:
            continue
        try:
            last_seen = date.fromisoformat(last_seen_str)
            days_since = (today - last_seen).days
            if days_since > stale_threshold_days:
                stale_jobs.append({
                    "job_id": job_id,
                    "last_seen": last_seen_str,
                    "days_since_seen": days_since,
                })
        except ValueError:
            pass

    return {
        "passed": len(stale_jobs) == 0,
        "stale_threshold_days": stale_threshold_days,
        "stale_active_jobs": len(stale_jobs),
        "sample_stale": stale_jobs[:5],
        "note": "Stale active jobs may indicate scraper stopped running",
    }

def check_required_fields(raw):
    """
    Check 5: Required fields present in all records.
    job_id, title, company, first_seen, still_active must not be null.
    """
    required = ["job_id", "title", "company", "first_seen", "still_active"]
    issues = []
    for job_id, job in raw.items():
        missing = [f for f in required if job.get(f) is None]
        if missing:
            issues.append({"job_id": job_id, "missing_fields": missing})

    return {
        "passed": len(issues) == 0,
        "records_checked": len(raw),
        "records_with_missing_fields": len(issues),
        "sample_issues": issues[:5],
    }

def check_first_seen_distribution(seen):
    """
    Check 6: Distribution of first_seen dates.
    Shows collection history — useful for spotting gaps.
    """
    dates = Counter(d.get("first_seen", "unknown") for d in seen.values())
    sorted_dates = sorted(dates.items())
    return {
        "passed": True,  # informational only
        "collection_dates": sorted_dates,
        "total_collection_days": len(sorted_dates),
    }

def print_report(checks):
    """Print a clean verification report."""
    print("=" * 60)
    print("LINKEDIN DATA INTEGRITY REPORT")
    print(f"Run date: {date.today()}")
    print("=" * 60)

    all_passed = True
    for name, result in checks.items():
        passed = result.get("passed", True)
        status = "PASS ✓" if passed else "FAIL ✗"
        if not passed:
            all_passed = False
        print(f"\n[{status}] {name}")

        # Print key metrics
        for key, val in result.items():
            if key == "passed":
                continue
            if isinstance(val, list) and len(val) == 0:
                continue
            if isinstance(val, dict) and not val:
                continue
            print(f"  {key}: {val}")

    print("\n" + "=" * 60)
    if all_passed:
        print("OVERALL: ALL CHECKS PASSED ✓")
    else:
        print("OVERALL: ISSUES FOUND — review FAIL items above ✗")
    print("=" * 60)

if __name__ == "__main__":
    print("Loading data files...")
    try:
        raw, seen = load_data()
    except FileNotFoundError as e:
        print(f"ERROR: Data file not found — {e}")
        print("Pull data from data-branch first:")
        print("  git fetch origin data-branch")
        print("  git checkout origin/data-branch -- backend/data/linkedin_raw_jobs.json")
        print("  git checkout origin/data-branch -- backend/data/linkedin_seen_jobs.json")
        exit(1)

    checks = {
        "1. File Sync (raw vs seen)": check_file_sync(raw, seen),
        "2. No Duplicate job_ids": check_duplicates(raw),
        "3. Closure Consistency": check_closure_consistency(raw, seen),
        "4. Active Jobs Freshness": check_active_jobs_freshness(seen),
        "5. Required Fields Present": check_required_fields(raw),
        "6. Collection History": check_first_seen_distribution(seen),
    }

    print_report(checks)