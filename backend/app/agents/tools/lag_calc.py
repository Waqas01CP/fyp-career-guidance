"""
lag_calc.py — Read FutureValue and market data for a degree field from lag_model.json.
Called by AnswerNode for market_query intent.
ScoringNode also reads computed.future_value directly — this tool returns richer data for answers.
Pure data lookup — no LLM, no DB.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def lag_calc(field_id: str) -> dict:
    """
    Return FutureValue and market data for the given field_id.
    Returns empty dict if field not found.
    """
    path = DATA_DIR / "lag_model.json"
    if not path.exists():
        return {}
    with open(path) as f:
        lag_model_list = json.load(f)
    lag_model = {entry["field_id"]: entry for entry in lag_model_list}
    return lag_model.get(field_id, {})
