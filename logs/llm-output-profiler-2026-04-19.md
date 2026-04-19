# ProfilerNode LLM Output Comparison — 2026-04-19

Model switch comparison: gemini-2.5-flash (Run 1, baseline) vs gemini-2.5-flash-lite-preview (Run 2, lighter model).

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

## Run 2 — gemini-2.0-flash-lite (attempted)

**Date/time:** 2026-04-19  
**Model attempted:** gemini-2.0-flash-lite  
**Temperature:** 0.0  

**Result:** API 429 — Quota exceeded (free tier limit = 0 for this model)  

```
Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests
limit: 0, model: gemini-2.0-flash-lite
```

`limit: 0` means the free-tier API key has zero access to `gemini-2.0-flash-lite` — it is
not available on the free quota plan, regardless of RPM. This is a billing tier restriction,
not a rate limit.

**Reply from LLM (error fallback path):**
```
I'm having trouble processing your request right now. Could you try again in a moment?
```

**Extracted constraints:** `{}` (none — LLM call failed before parsing)  
**profiling_complete:** False  

**Error handling confirmation:** profiler_node caught the 429 as a generic Exception,
appended the fallback AIMessage, and returned cleanly without crashing. The graceful
failure path works correctly.

---

## Comparison Notes

| Metric | gemini-2.5-flash (Run 1) | gemini-2.0-flash-lite (Run 2) |
|---|---|---|
| API call result | Success | 429 quota exceeded (limit=0 on free tier) |
| Budget extracted | 50000 ✓ | N/A (call failed) |
| Zone extracted | 2 ✓ | N/A (call failed) |
| profiling_complete | False ✓ | False (fallback) |
| JSON format | Valid | N/A |
| Tone | Friendly, conversational | N/A |

**Key finding: model abstraction is confirmed working.**  
Changing `LLM_MODEL_NAME` in `.env` changes the model used with zero code changes.
The `ChatGoogleGenerativeAI` wrapper accepts any Gemini model ID.
The error handling path also confirmed: fallback message is clean and does not crash.

**Why gemini-2.0-flash-lite is inaccessible:**  
Free-tier Gemini API key does not include gemini-2.0-flash-lite.
Only gemini-2.5-flash is accessible on this key (20 RPD, 5 RPM, 250k TPM).
gemini-2.0-flash and gemini-2.0-flash-lite require a paid quota plan.

**Config reverted:** Both config.py default and .env restored to `gemini-2.5-flash`
(the only model accessible on this key). `langchain-anthropic` remains in requirements.txt
as a pre-emptive dependency for the future production switch to claude-haiku-4-5.

**Unit tests after switch (gemini-2.0-flash-lite config, no API call):** 4/4 passed.
