"""
compute_future_values.py — Recompute FutureValue scores in lag_model.json.
Run by Fazal once per semester after updating Layer 1/2/3 raw data.
NOT run by the server at request time.
Run: python scripts/compute_future_values.py
Must be run from the backend/ directory.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"


def compute_future_value(entry: dict) -> float:
    """
    Compute FutureValue for a single degree field entry.
    FutureValue = weighted_sum(Layer1, Layer2, Layer3) × lag_confidence_multiplier
    All layers normalised to 0-10 scale before weighting.
    """
    lag_type = entry.get("lag_type", "LOCAL")
    weights = settings.FUTURE_VALUE_WEIGHTS.get(lag_type, settings.FUTURE_VALUE_WEIGHTS["LOCAL"])
    confidence = settings.LAG_CONFIDENCE.get(lag_type, 1.0)

    raw = entry.get("raw", {})
    l1 = float(raw.get("layer1_normalised", 0))
    l2 = float(raw.get("layer2_normalised", 0))
    l3 = float(raw.get("layer3_normalised", 0))

    fv = ((weights["layer1"] * l1) + (weights["layer2"] * l2) + (weights["layer3"] * l3)) * confidence
    return round(min(max(fv, 0.0), 10.0), 2)


def main():
    path = DATA_DIR / "lag_model.json"
    if not path.exists():
        print("lag_model.json not found. Create it first.")
        return

    with open(path) as f:
        lag_model = json.load(f)

    updated = 0
    for entry in lag_model:
        fv = compute_future_value(entry)
        if "computed" not in entry:
            entry["computed"] = {}
        entry["computed"]["future_value"] = fv
        updated += 1

    with open(path, "w") as f:
        json.dump(lag_model, f, indent=2)

    print(f"Recomputed FutureValue for {updated} fields. lag_model.json updated.")


if __name__ == "__main__":
    main()
