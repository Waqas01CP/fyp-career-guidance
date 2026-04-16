"""
compute_future_values.py — Recompute FutureValue scores in lag_model.json.
Run by Fazal once per semester after updating Layer 1/2/3 raw data.
NOT run by the server at request time.
Run: python scripts/compute_future_values.py
Must be run from the backend/ directory.
"""
import json
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"


# ---------------------------------------------------------------------------
# Signal extractors — return float or None if field is absent / null
# ---------------------------------------------------------------------------

def _pak_now(entry: dict):
    """Layer 1: Pakistan current YoY job posting growth."""
    try:
        v = entry["pakistan_now"]["yoy_growth_rate"]
        return float(v) if v is not None else None
    except (KeyError, TypeError):
        return None


def _pak_fut(entry: dict):
    """Layer 2: Pakistan projected 4-year growth."""
    try:
        v = entry["pakistan_future"]["projected_4yr_growth"]
        return float(v) if v is not None else None
    except (KeyError, TypeError):
        return None


def _world_now(entry: dict):
    """Layer 3a: Composite mean of US/UK/UAE YoY growth rates."""
    try:
        wn = entry["world_now"]
        vals = [
            wn.get("us_yoy_growth_rate"),
            wn.get("uk_yoy_growth_rate"),
            wn.get("uae_yoy_growth_rate"),
        ]
        available = [float(v) for v in vals if v is not None]
        return mean(available) if available else None
    except (KeyError, TypeError):
        return None


def _world_fut(entry: dict):
    """Layer 3b: US BLS 4-year projected growth."""
    try:
        v = entry["world_future"]["us_bls_4yr_projected_growth"]
        return float(v) if v is not None else None
    except (KeyError, TypeError):
        return None


# Ordered list of (weight_key, extractor) pairs — order matters for iteration
SIGNAL_EXTRACTORS = [
    ("layer1",  _pak_now),
    ("layer2",  _pak_fut),
    ("layer3a", _world_now),
    ("layer3b", _world_fut),
]


# ---------------------------------------------------------------------------
# Min-max normalisation
# ---------------------------------------------------------------------------

def _minmax_normalise(values: list) -> list:
    """
    Min-max normalise a list that may contain None values.
    None entries are preserved as None in the output.
    If all non-None values are identical (max == min), every non-None
    entry normalises to 0.5 (uniform signal — no field dominates).
    """
    non_null = [v for v in values if v is not None]
    if not non_null:
        return list(values)
    lo = min(non_null)
    hi = max(non_null)
    result = []
    for v in values:
        if v is None:
            result.append(None)
        elif hi == lo:
            result.append(0.5)
        else:
            result.append((v - lo) / (hi - lo))
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    path = DATA_DIR / "lag_model.json"
    if not path.exists():
        print("lag_model.json not found. Create it first.")
        return

    with open(path) as f:
        lag_model = json.load(f)

    # STEP 1 — Extract raw signal values per entry (one pass over all entries)
    raw_signals = {layer_key: [] for layer_key, _ in SIGNAL_EXTRACTORS}
    for entry in lag_model:
        for layer_key, extractor in SIGNAL_EXTRACTORS:
            raw_signals[layer_key].append(extractor(entry))

    # STEP 2 — Min-max normalise each signal independently across all fields
    normalised_signals = {
        layer_key: _minmax_normalise(raw_signals[layer_key])
        for layer_key, _ in SIGNAL_EXTRACTORS
    }

    now_str = datetime.now().strftime("%Y-%m")
    updated = 0

    for i, entry in enumerate(lag_model):
        # STEP 3 — Handle missing signals: redistribute weight proportionally
        lag_cat = entry.get("lag_category", "LOCAL")
        weights = settings.FUTURE_VALUE_WEIGHTS.get(
            lag_cat, settings.FUTURE_VALUE_WEIGHTS["LOCAL"]
        )
        confidence = settings.LAG_CONFIDENCE.get(lag_cat, 1.0)

        available_weight_sum = 0.0
        any_missing = False

        for layer_key, _ in SIGNAL_EXTRACTORS:
            norm_val = normalised_signals[layer_key][i]
            if norm_val is not None:
                available_weight_sum += weights[layer_key]
            else:
                any_missing = True

        # STEP 4 — Compute FutureValue
        if available_weight_sum == 0.0:
            # No signals available at all — future_value is 0
            raw = 0.0
        else:
            raw = 0.0
            for layer_key, _ in SIGNAL_EXTRACTORS:
                norm_val = normalised_signals[layer_key][i]
                if norm_val is None:
                    continue
                # Redistribute missing weight proportionally to available signals
                adjusted_w = weights[layer_key] / available_weight_sum
                raw += norm_val * adjusted_w

        future_value = round(raw * 10 * confidence, 2)
        future_value = min(max(future_value, 0.0), 10.0)

        # STEP 5 — Write back to entry
        if "computed" not in entry:
            entry["computed"] = {}
        entry["computed"]["future_value"] = future_value
        entry["computed"]["last_computed"] = now_str

        if any_missing and "employment_data" in entry:
            entry["employment_data"]["data_status"] = "partial"

        updated += 1

    with open(path, "w") as f:
        json.dump(lag_model, f, indent=2)

    print(f"Recomputed FutureValue for {updated} fields. lag_model.json updated.")


if __name__ == "__main__":
    main()
