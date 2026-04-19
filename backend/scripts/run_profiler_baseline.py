"""
run_profiler_baseline.py — Single-turn profiler_node invocation for model comparison.
Prints model name, raw AI reply, extracted constraints, and profiling_complete flag.
Run from backend/ directory with venv active.
"""
import json
import sys
import os

# Allow import from backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage

from app.agents.nodes.profiler import profiler_node
from app.core.config import settings


def _make_state(user_message: str) -> dict:
    return {
        "student_profile": {
            "education_level": "inter_part2",
            "grade_system": "percentage",
            "stream": "Pre-Engineering",
            "subject_marks": {
                "mathematics": 82,
                "physics": 78,
                "chemistry": 71,
                "english": 80,
                "biology": 0,
            },
            "riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
            "capability_scores": {
                "mathematics": 65.0,
                "physics": 70.0,
                "chemistry": 58.3,
                "english": 75.0,
                "biology": 0.0,
            },
        },
        "active_constraints": {},
        "profiling_complete": False,
        "last_intent": "get_recommendation",
        "student_mode": "inter",
        "education_level": "inter_part2",
        "current_roadmap": [],
        "previous_roadmap": None,
        "thought_trace": [],
        "mismatch_notice": None,
        "conflict_detected": False,
        "messages": [HumanMessage(content=user_message)],
    }


if __name__ == "__main__":
    print(f"=== ProfilerNode Baseline Run ===")
    print(f"Model: {settings.LLM_MODEL_NAME}")
    print(f"Temperature: {settings.LLM_TEMPERATURE}")
    print()

    test_message = "My budget is 50,000 rupees per semester and I live in Gulshan-e-Iqbal."
    print(f"Input: {test_message!r}")
    print()

    state = _make_state(test_message)
    result = profiler_node(state)

    ai_messages = [m for m in result["messages"] if hasattr(m, "type") and m.type == "ai"]
    reply = ai_messages[-1].content if ai_messages else "(no reply)"

    print(f"Reply: {reply}")
    print()
    print(f"Extracted constraints: {json.dumps(result['active_constraints'], ensure_ascii=False, indent=2)}")
    print()
    print(f"profiling_complete: {result['profiling_complete']}")
