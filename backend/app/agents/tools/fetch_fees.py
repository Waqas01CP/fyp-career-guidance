"""
fetch_fees.py — Read fee structure for a specific university from universities.json.
Called by AnswerNode for fee_query intent.
Pure data lookup — no LLM, no DB.
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def fetch_fees(university_id: str) -> dict:
    """
    Return fee structure for the given university_id.
    Returns all degrees with their fee_per_semester.
    Returns empty dict if university not found.
    """
    path = DATA_DIR / "universities.json"
    if not path.exists():
        return {}
    with open(path) as f:
        universities = json.load(f)
    for uni in universities:
        if uni.get("university_id") == university_id:
            return {
                "university_id": uni["university_id"],
                "university_name": uni.get("university_name", ""),
                "degrees": [
                    {
                        "degree_name": d.get("degree_name"),
                        "fee_per_semester": d.get("fee_per_semester"),
                    }
                    for d in uni.get("degrees", [])
                ],
            }
    return {}
