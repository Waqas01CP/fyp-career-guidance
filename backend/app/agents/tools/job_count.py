"""
job_count.py — Live Rozee.pk job count scraper with fallback chain.
Layer 1 live data source for FutureValue calculation.
Called by compute_future_values.py (scripts/) — NOT at request time.

Fallback chain (one source per scrape cycle):
  1. Rozee.pk (primary)
  2. Mustakbil.com (fallback 1)
  3. Jobz.pk (fallback 2)
  4. Cached last known value (last resort)

Sprint 1: returns None (scraper not yet implemented).
Sprint 2: implement polite Rozee.pk scraper with 1-2 second delays.
"""
import httpx


async def get_job_count(field_keyword: str) -> int | None:
    """
    Return current active job posting count for the given field keyword.
    Returns None if all sources fail (caller falls back to cached value).

    Sprint 2 implementation plan:
    - Scrape https://www.rozee.pk/job/jsearch/q/{field_keyword}
    - Parse result count from response HTML
    - Use httpx with 1-2 second polite delays
    - Return integer count
    """
    # TODO Sprint 2: implement Rozee.pk scraper
    count = _scrape_rozee(field_keyword)
    if count is None:
        count = _scrape_mustakbil(field_keyword)
    if count is None:
        count = _scrape_jobz(field_keyword)
    return count


def _scrape_rozee(keyword: str) -> int | None:
    """Sprint 2: implement Rozee.pk scrape."""
    return None  # TODO


def _scrape_mustakbil(keyword: str) -> int | None:
    """Sprint 2: implement Mustakbil.com scrape (fallback 1)."""
    return None  # TODO


def _scrape_jobz(keyword: str) -> int | None:
    """Sprint 2: implement Jobz.pk scrape (fallback 2)."""
    return None  # TODO
