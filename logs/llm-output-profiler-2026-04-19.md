# ProfilerNode LLM Output Comparison — 2026-04-19

Model switch comparison: gemini-2.5-flash (Run 1, baseline) vs gemini-3.1-flash-lite-preview (Run 2, lighter model).

**Test input (same for both runs):**
```
"My budget is 50,000 rupees per semester and I live in Gulshan-e-Iqbal."
```

**Student context injected via system prompt:**
- Education: inter_part2 | Grade system: percentage | Stream: Pre-Engineering
- Marks: mathematics:82% | physics:78% | chemistry:71% | english:80%
- RIASEC: R:32 I:45 A:28 S:31 E:38 C:42
- active_constraints: {} (empty — first message)
- Missing required: [budget_per_semester, transport_willing, home_zone]

---

## Run 1 — gemini-2.5-flash (baseline)

**Date/time:** 2026-04-19  
**Model:** gemini-2.5-flash  
**Temperature:** 0.0  

**Reply from LLM:**
```
Great, so your budget is Rs. 50,000 per semester and you're located in Gulshan-e-Iqbal. Got it!
To help us find the best options, could you also tell me if you're open to traveling to any part
of Karachi for your studies, or if you'd prefer to stay closer to your area?
```

**Extracted constraints:**
```json
{
  "budget_per_semester": 50000,
  "home_zone": 2
}
```

**profiling_complete:** False  

**Observations:**
- Correctly extracted budget_per_semester=50000 (integer, not float)
- Correctly mapped "Gulshan-e-Iqbal" → home_zone=2 (Central zone)
- Both fields extracted from single message — correct behaviour
- Next question asks for transport_willing — correct (last missing required field)
- Friendly, conversational tone. Confirmed both extracted fields in one sentence before asking next.
- JSON output well-formed. No markdown wrapper.

---

## Run 2 — gemini-3.1-flash-lite-preview

**Date/time:** 2026-04-19  
**Model:** gemini-3.1-flash-lite-preview  
**Temperature:** 0.0  

**Note — content format fix required:**  
Gemini 3.1 returns `response.content` as a `list` of parts instead of a plain string.
The original `response.content.strip()` raised `AttributeError: 'list' object has no attribute 'strip'`.
Fix applied to `profiler.py`: content is flattened to string before `.strip()` when it is a list.

```python
content = response.content
if isinstance(content, list):
    content = "".join(
        p.get("text", "") if isinstance(p, dict) else str(p) for p in content
    )
raw_response = content.strip()
```

**Reply from LLM:**
```
That's great! I've noted your budget of 50,000 PKR per semester and that you live in the
Gulshan-e-Iqbal area, which falls under the Central zone. To help me find the best options
for you, are you willing to travel to universities across Karachi, or would you prefer to
stay closer to your home area?
```

**Extracted constraints:**
```json
{
  "budget_per_semester": 50000,
  "home_zone": 2
}
```

**profiling_complete:** False  

**Observations:**
- Correctly extracted budget_per_semester=50000 (integer)
- Correctly mapped "Gulshan-e-Iqbal" → home_zone=2 (Central zone)
- Both fields extracted from single message — correct
- Next question asks for transport_willing — correct (last missing required field)
- Named the zone explicitly ("Central zone") — slightly more verbose than Run 1
- JSON output well-formed after list-flatten fix.

---

## Comparison Notes

| Metric | gemini-2.5-flash (Run 1) | gemini-3.1-flash-lite-preview (Run 2) |
|---|---|---|
| API call result | Success | Success (after content list-flatten fix) |
| Budget extracted | 50000 ✓ | 50000 ✓ |
| Zone extracted | 2 ✓ | 2 ✓ |
| profiling_complete | False ✓ | False ✓ |
| JSON format | Valid | Valid |
| Tone | Friendly, brief | Friendly, slightly more verbose |
| Content format | String | List of parts (flattened) |
| Next question | transport_willing ✓ | transport_willing ✓ |

**Key finding: model abstraction confirmed — with one compatibility fix.**  
Changing `LLM_MODEL_NAME` in `.env` is the only config change needed. However,
`gemini-3.1-flash-lite-preview` returns `response.content` as a list of parts rather
than a plain string. A one-line flatten guard was added to `profiler.py` to handle both
formats. Both models extract the same fields, produce valid JSON, ask the correct next
question, and maintain a conversational tone.

**Config reverted:** Both `config.py` default and `.env` restored to `gemini-2.5-flash`
(dev model per CLAUDE.md). `langchain-anthropic` added to `requirements.txt` as a
pre-emptive dependency for the future production switch to `claude-haiku-4-5`.

**Unit tests after all changes:** 4/4 passed (no API calls).
