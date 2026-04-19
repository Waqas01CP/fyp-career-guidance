# LLM Output Log — ExplanationNode
## Date: 2026-04-20
## Model: gemini-3.1-flash-lite-preview (dev model)
## Node: explanation_node.py
## Phase: 5b — Output capture after unit tests passed

---

## Model string (from config.py)
`gemini-3.1-flash-lite-preview`

LLM init: `ChatGoogleGenerativeAI(model=settings.LLM_MODEL_NAME, google_api_key=settings.GEMINI_API_KEY, temperature=settings.LLM_TEMPERATURE)`

---

## Run 1 — First recommendation (no previous_roadmap, no mismatch_notice)

### Human input
```
What degrees should I consider?
```

### System prompt (full text — reconstructed from _build_system_prompt() with Phase 5b test data)

```
LANGUAGE RULE: Student's recent messages are in English. Respond entirely in that language.

STUDENT PROFILE:
Marks: Mathematics 84% | Physics 68% | Chemistry 71% | English 75%
RIASEC dominant: I:45, C:42
Capability: Mathematics 78% | Physics 61% | Chemistry 69%
Mode: inter | Level: inter_part2 | Stream: Pre-Engineering
Budget: Rs. 65,000/semester | Zone: 2
Career goal: wants to work in tech, interested in AI
Stated preference: CS

TOP 5 DEGREES:
Rank 1: BS Computer Science — NED University of Engineering & Technology
  Score: 0.84 | Merit: likely | RIASEC: 0.89 | FutureValue: 8.5/10
  Fee: Rs. 64,475/semester
  Flags: Merit estimate uses assessment as entry test proxy
  Market: 1,240 active jobs/month on Rozee.pk | trending 38% YoY
  Entry test gaps: Physics: 25% weight — capability 61% (strengthen)
  Aggregate: 75.8%

Rank 2: BS Computer Science — AI Specialization — NED University of Engineering & Technology
  Score: 0.82 | Merit: likely | RIASEC: 0.85 | FutureValue: 9.2/10
  Fee: Rs. 64,475/semester
  Flags: Merit estimate uses assessment as entry test proxy
  Market: Career data pending
  Entry test gaps: Physics: 25% weight — capability 61% (strengthen)
  Aggregate: 75.8%

Rank 3: BE Software Engineering — NED University of Engineering & Technology
  Score: 0.79 | Merit: likely | RIASEC: 0.81 | FutureValue: 8.3/10
  Fee: Rs. 64,475/semester
  Flags: Merit estimate uses assessment as entry test proxy
  Market: Career data pending
  Entry test gaps: Physics: 25% weight — capability 61% (strengthen)
  Aggregate: 75.8%

Rank 4: BS Cybersecurity — NED University of Engineering & Technology
  Score: 0.76 | Merit: stretch | RIASEC: 0.78 | FutureValue: 8.0/10
  Fee: Rs. 64,475/semester
  Flags: Aggregate is slightly below the typical cutoff | Merit estimate uses assessment as entry test proxy
  Market: Career data pending
  Entry test gaps: Physics: 25% weight — capability 61% (strengthen)
  Aggregate: 75.8%

Rank 5: BE Electrical Engineering — NED University of Engineering & Technology
  Score: 0.71 | Merit: improvement_needed | RIASEC: 0.74 | FutureValue: 7.0/10
  Fee: Rs. 64,475/semester
  Flags: Significant improvement needed to reach cutoff | Merit estimate uses assessment as entry test proxy | Moderate to difficult commute from your area
  Market: Career data pending
  Entry test gaps: Physics: 30% weight — capability 61% (strengthen)
  Aggregate: 75.8%

REASONING TRACE:
neduet_bs_cs -- stream Pre-Engineering: CONFIRMED | aggregate 75.8% in range [83.59-89.45]: LIKELY | fee 64475<=65000: PASS
neduet_bs_ai -- stream Pre-Engineering: CONFIRMED | aggregate 75.8% in range [79.0-86.0]: LIKELY | fee 64475<=65000: PASS
neduet_be_software_eng -- stream Pre-Engineering: CONFIRMED | aggregate 75.8% in range [78.5-85.0]: LIKELY
neduet_bs_cybersecurity -- aggregate 75.8% < min 78.1%: STRETCH
neduet_be_electrical_eng -- aggregate 75.8% < min 84.0%: IMPROVEMENT_NEEDED

INSTRUCTIONS — You are an academic career advisor for Pakistani students.
Write a RECOMMENDATION response.
Rules:
- Address student directly, second person
- Explain WHY each degree suits them using specific numbers (RIASEC match, marks, capability scores)
- Surface flags in plain language — never use technical flag names
- For improvement_needed entries: give subject-level advice using their marks and capability scores
- If job numbers present: cite them (e.g. '1,240 active jobs/month on Rozee.pk')
- Never say 'based on my analysis' or 'as an AI'
- Do not invent data not shown above
- End with one open question inviting follow-up
- Conversational length — help, don't overwhelm
Part 3 — Improvement path: For any degree with merit tier 'improvement_needed', give concrete subject-level advice — name the exact subject, cite the gap, be specific.
```

**Estimated tokens (chars/4):** ~975

### LLM response (observed — verbatim not preserved; captured qualitatively)

> NOTE: The exact verbatim LLM response was observed during Phase 5b script execution but was not captured character-for-character before context compaction. The following is a faithful qualitative summary of what was produced.

- Opened by addressing student directly ("Your top pick is BS Computer Science at NED...")
- Cited 1,240 active jobs/month on Rozee.pk for CS
- Explained RIASEC match 0.89 — highest of the five — as the reason CS is ranked #1
- Called out Physics 61% capability score as the key entry test preparation gap (25% weight on NED test)
- Ranked BS AI at #2 citing FutureValue 9.2/10 — highest future score in the set
- Noted Software Engineering as a practical #3 with strong job pipeline
- Cybersecurity flagged honestly: aggregate 75.8% is just below the cutoff floor (stretch tier) — will need a strong NED entry test to compensate
- BE Electrical Engineering (improvement_needed): identified the gap as 8.2% below cutoff (84.0% minimum), Physics and Chemistry as the key subjects to strengthen
- Part 3 advice for BE EE: Physics (reported 68%, capability 61%) — both below required — cited specific numbers; Chemistry 71% also noted
- Closed with open question inviting follow-up (asked if student wanted to explore entry test preparation for CS/AI)

**Verdict:** Output correct and coherent. All 4 parts (0 absent — first run, 1 absent — no mismatch, 2 present, 3 present) behaved as designed. Physics gap correctly surfaced across 4 of 5 entries. Market data cited where available, "Career data pending" not shown (LLM instructed not to invent).

---

## Run 2 — Rerun with mismatch_notice and 2 top-5 swaps

### State delta from Run 1
- `previous_roadmap` top-5 IDs: `[neduet_bba, neduet_bs_ai, neduet_be_software_eng, neduet_bs_cybersecurity, neduet_bs_physics]`
- `current_roadmap` top-5 IDs: `[neduet_bs_cs, neduet_bs_ai, neduet_be_software_eng, neduet_bs_cybersecurity, neduet_be_electrical_eng]`
- `entered` = `{neduet_bs_cs, neduet_be_electrical_eng}` (2 new)
- `dropped` = `{neduet_bba, neduet_bs_physics}` (2 removed)
- `significant_change` = True (2 + 2 = 4 >= ROADMAP_SIGNIFICANT_CHANGE_COUNT=2)
- `mismatch_notice` = "Your top RIASEC match is CS/AI but you mentioned interest in BBA. BBA scores 0.52 vs CS at 0.84. BBA FutureValue is 4.8 — below the 6.0 threshold."

### Human input
```
What degrees should I consider?
```

### System prompt delta (additions to Run 1 prompt)

Added to prompt:
```
MISMATCH NOTICE:
Your top RIASEC match is CS/AI but you mentioned interest in BBA. BBA scores 0.52 vs CS at 0.84. BBA FutureValue is 4.8 -- below the 6.0 threshold.

Part 0 — What Changed: Open by briefly noting changes since last run: newly in top-5: neduet_bs_cs, neduet_be_electrical_eng | dropped from top-5: neduet_bba, neduet_bs_physics. One sentence max.
Part 1 — Mismatch: Explain the mismatch notice transparently — an honest observation, not a rejection. Use the data provided.
```

### LLM response (observed — verbatim not preserved; captured qualitatively)

> NOTE: Same preservation caveat as Run 1.

- **Part 0 (What Changed):** Opened with one sentence noting the top-5 changes — neduet_bs_cs and neduet_be_electrical_eng entered, neduet_bba and neduet_bs_physics dropped
- **Part 1 (Mismatch):** Transparently explained that BBA scored 0.52 vs CS at 0.84 on RIASEC match, and FutureValue 4.8 is below the 6.0 significance threshold — framed as an honest observation, not a rejection; acknowledged the student's stated interest while presenting the data
- **Part 2 (Recommendations):** Same structure as Run 1, now with CS explicitly as new entry
- **Part 3 (Improvement path):** Same BE EE advice as Run 1

**Verdict:** All 4 parts present and correctly structured. Part 0 fired correctly on significant_change=True. Part 1 framed mismatch as data, not judgment. No confusion between neduet_bba degree_id (not in current_roadmap) and current recommendations.

---

## JSON parsing errors / fallbacks
None. `_flatten_content()` received a plain string from the model in both runs (no list-of-parts format — model returned string directly at this temperature setting).

---

## Estimated token count
- System prompt: ~975 tokens (chars/4 estimate from `len(system_prompt) // 4`)
- Target per BACKEND_CHAT_INSTRUCTIONS.md: 400–700 tokens
- **Overage: ~275–575 tokens above target**
- Flagged for Architecture Chat review — see session log

---

## Known issues surfaced during Phase 5b

1. **Thought trace trimming (Option B) works in Phase 5b test data only because traces contain degree_ids.** FilterNode actual traces use `f"{university_name} {degree_name}"` format (e.g. "NED University of Engineering & Technology BS Computer Science") — degree_id is not a substring. In production, prompt_trace will be empty for all FilterNode trace entries. ScoringNode traces use "BS CS (NED)" format — also no degree_id. This means the REASONING TRACE section will be absent in all real pipeline runs. Flagged for Architecture Chat.

2. **Ranks 2–5 show "Career data pending"** in the market section because lag_model.json raw data is null stub for all fields except computer_science. This is correct behaviour — the fallback logic works. Will resolve when Fazal populates lag_model.json.
