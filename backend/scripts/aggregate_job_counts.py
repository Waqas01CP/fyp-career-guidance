"""
Script D — Aggregate LinkedIn job counts into lag_model.json.
Reads linkedin_raw_jobs.json + job_title_mapping.json (confirmed only).
Writes raw.monthly_postings_history per field_id into lag_model.json.
Pure Python — no LLM, no external API calls.
Idempotent: re-running recalculates from scratch and produces the same result.
"""

import json
import pathlib
import sys
from datetime import datetime
from collections import defaultdict

REPO_ROOT = pathlib.Path(__file__).parent.parent.parent
DATA_DIR = REPO_ROOT / "backend" / "data"
APP_DATA_DIR = REPO_ROOT / "backend" / "app" / "data"
LOG_DIR = REPO_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)

RAW_JOBS_FILE = DATA_DIR / "linkedin_raw_jobs.json"
MAPPING_FILE = DATA_DIR / "job_title_mapping.json"
LAG_MODEL_FILE = APP_DATA_DIR / "lag_model.json"
LOG_FILE = LOG_DIR / (
    f"aggregate_job_counts_"
    f"{datetime.now().strftime('%Y_%m_%d_%H%M')}.log"
)


# ---------------------------------------------------------------------------
# STEP 3 — Load functions
# ---------------------------------------------------------------------------

def load_raw_jobs(log_func) -> dict:
    """Load linkedin_raw_jobs.json. Returns dict keyed by job_id.
    Exits if file missing or malformed."""
    try:
        with open(RAW_JOBS_FILE, encoding="utf-8") as f:
            jobs = json.load(f)
        log_func(f"INFO | Raw jobs loaded: {len(jobs)}")
        return jobs
    except FileNotFoundError:
        log_func(
            f"ERROR | {RAW_JOBS_FILE} not found — "
            f"pull from data-branch first"
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_func(f"ERROR | Malformed JSON in raw jobs: {e}")
        sys.exit(1)


def load_mapping(log_func) -> dict:
    """Load confirmed section of job_title_mapping.json.
    Keys are lowercased on load to match Script C v2 normalisation
    and to be robust against Script C v1 uppercase keys.
    Returns dict of lowercase_title → entry. Exits if missing."""
    try:
        with open(MAPPING_FILE, encoding="utf-8") as f:
            mapping = json.load(f)
        confirmed = mapping.get("confirmed", {})
        # Lowercase keys to match aggregate_counts() lookup normalisation.
        # Handles both Script C v1 (uppercase keys) and v2 (lowercase keys).
        confirmed = {k.lower(): v for k, v in confirmed.items()}
        log_func(
            f"INFO | Confirmed mappings loaded: "
            f"{len(confirmed)}"
        )
        return confirmed
    except FileNotFoundError:
        log_func(
            f"ERROR | {MAPPING_FILE} not found — "
            f"run Script C first and pull from data-branch"
        )
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_func(f"ERROR | Malformed JSON in mapping: {e}")
        sys.exit(1)


def load_lag_model(log_func) -> list:
    """Load lag_model.json. Returns list of field entries.
    Exits if missing or malformed."""
    try:
        with open(LAG_MODEL_FILE, encoding="utf-8") as f:
            lag_model = json.load(f)
        log_func(
            f"INFO | Lag model loaded: "
            f"{len(lag_model)} field entries"
        )
        return lag_model
    except FileNotFoundError:
        log_func(f"ERROR | {LAG_MODEL_FILE} not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        log_func(f"ERROR | Malformed JSON in lag model: {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# STEP 4 — Aggregation function
# ---------------------------------------------------------------------------

def aggregate_counts(raw_jobs, confirmed_mapping, log_func) -> dict:
    """
    For each job in raw_jobs, look up title in confirmed mapping and
    accumulate counts per field_id per month with sub_specialisation
    breakdown.

    Title lookup uses lowercase to match Script C v2 normalisation.

    Returns:
        counts: dict of field_id → {
            YYYY-MM: {
                "total": float,
                "by_specialisation": {sub_spec_or_null: float}
            }
        }
    """
    counts = defaultdict(lambda: defaultdict(
        lambda: {"total": 0.0, "by_specialisation": defaultdict(float)}
    ))

    skipped_no_title = 0
    skipped_not_mapped = 0
    skipped_unmapped = 0
    counted = 0
    secondary_credits = 0

    for job_id, job in raw_jobs.items():
        title = job.get("title")
        if not title:
            skipped_no_title += 1
            continue

        # Normalize — must match Script C v2 lowercase
        title = " ".join(title.split()).lower()

        entry = confirmed_mapping.get(title)
        if entry is None:
            skipped_not_mapped += 1
            continue

        if entry.get("unmapped", False):
            skipped_unmapped += 1
            continue

        # Extract YYYY-MM from first_seen
        first_seen = job.get("first_seen")
        if not first_seen:
            skipped_no_title += 1
            continue
        try:
            month_key = first_seen[:7]
        except (TypeError, IndexError):
            log_func(
                f"WARN | Invalid first_seen for "
                f"{job_id}: {first_seen!r} — skipping"
            )
            skipped_no_title += 1
            continue

        sub_spec = entry.get("sub_specialisation") or "null"

        # Primary field: +1.0
        primary = entry.get("primary_field_id")
        if primary:
            counts[primary][month_key]["total"] += 1.0
            counts[primary][month_key]["by_specialisation"][sub_spec] += 1.0
            counted += 1

        # Secondary fields: +0.5 each
        for sec in entry.get("secondary_field_ids", []):
            if sec:
                counts[sec][month_key]["total"] += 0.5
                counts[sec][month_key]["by_specialisation"][sub_spec] += 0.5
                secondary_credits += 1

    log_func(
        f"INFO | Aggregation complete\n"
        f"  Jobs counted (primary credit):    {counted}\n"
        f"  Secondary credits applied:        {secondary_credits}\n"
        f"  Skipped — no title:               {skipped_no_title}\n"
        f"  Skipped — not in confirmed:       {skipped_not_mapped}\n"
        f"  Skipped — unmapped role:          {skipped_unmapped}"
    )
    log_func(
        f"INFO | Field_ids with at least one count: "
        f"{len(counts)}"
    )

    # Convert defaultdicts to plain dicts, sort by month
    result = {}
    for field_id, month_data in counts.items():
        result[field_id] = {}
        for month, data in sorted(month_data.items()):
            result[field_id][month] = {
                "total": data["total"],
                "by_specialisation": dict(data["by_specialisation"])
            }

    return result


# ---------------------------------------------------------------------------
# STEP 5 — Write to lag_model function
# ---------------------------------------------------------------------------

def write_to_lag_model(lag_model, counts, log_func) -> list:
    """
    Write monthly_postings_history into each lag_model entry's raw block.

    Rules:
    - Only touches raw["monthly_postings_history"]
    - Never modifies computed block or future_value
    - field_ids in lag_model with no counts get {}
    - field_ids in counts but not in lag_model: warn + skip
    - Returns the updated lag_model list
    """
    lag_field_ids = {entry["field_id"] for entry in lag_model}

    # Warn about counts for field_ids not in lag_model
    extra_field_ids = set(counts.keys()) - lag_field_ids
    for fid in sorted(extra_field_ids):
        total = sum(m["total"] for m in counts[fid].values())
        log_func(
            f"WARN | field_id '{fid}' has {total:.1f} "
            f"job credits but is NOT in lag_model.json "
            f"— skipped. Inform Fazal to add this entry."
        )

    updated_count = 0
    empty_count = 0

    for entry in lag_model:
        field_id = entry["field_id"]

        # Ensure raw block exists
        if "raw" not in entry or entry["raw"] is None:
            entry["raw"] = {}

        month_data = counts.get(field_id, {})

        if month_data:
            entry["raw"]["monthly_postings_history"] = month_data
            total = sum(m["total"] for m in month_data.values())
            log_func(
                f"INFO | {field_id}: "
                f"{len(month_data)} month(s), "
                f"{total:.1f} total job credits"
            )
            updated_count += 1
        else:
            entry["raw"]["monthly_postings_history"] = {}
            empty_count += 1

    log_func(
        f"INFO | Lag model update summary\n"
        f"  Entries with data:    {updated_count}\n"
        f"  Entries with no data: {empty_count}"
    )
    return lag_model


# ---------------------------------------------------------------------------
# STEP 6 — Save function
# ---------------------------------------------------------------------------

def save_lag_model(lag_model, log_func):
    """Atomic write to lag_model.json."""
    tmp = LAG_MODEL_FILE.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(lag_model, f, indent=2, ensure_ascii=False)
        tmp.replace(LAG_MODEL_FILE)
        log_func(
            f"INFO | lag_model.json saved — "
            f"{len(lag_model)} entries written"
        )
    except Exception as e:
        log_func(f"ERROR | Failed to save lag model: {e}")
        raise


# ---------------------------------------------------------------------------
# STEP 7 — Main execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    LOG_FILE.parent.mkdir(exist_ok=True)
    log_handle = open(LOG_FILE, "a", encoding="utf-8", buffering=1)

    def log_func(message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{ts}] {message}"
        print(line)
        log_handle.write(line + "\n")
        log_handle.flush()

    log_func(f"INFO | Script D starting — {datetime.now().isoformat()}")

    # Load all three files
    raw_jobs = load_raw_jobs(log_func)
    confirmed_mapping = load_mapping(log_func)
    lag_model = load_lag_model(log_func)

    # Aggregate counts
    counts = aggregate_counts(raw_jobs, confirmed_mapping, log_func)

    # Write to lag_model
    updated_lag_model = write_to_lag_model(lag_model, counts, log_func)

    # Save atomically
    save_lag_model(updated_lag_model, log_func)

    # Final summary
    total_credits = sum(
        sum(m["total"] for m in months.values())
        for months in counts.values()
    )
    log_func(
        f"INFO | Script D complete\n"
        f"  Total job credits distributed: {total_credits:.1f}\n"
        f"  Field_ids with data: {len(counts)}\n"
        f"  Output: {LAG_MODEL_FILE}"
    )
    log_func(
        f"INFO | NEXT STEPS:\n"
        f"  1. Run QUICK TEST to verify output\n"
        f"  2. Commit lag_model.json to main branch\n"
        f"  3. Render will redeploy automatically"
    )

    log_handle.close()
