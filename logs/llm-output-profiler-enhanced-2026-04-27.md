# LLM Output Log — ProfilerNode Enhanced
## Date: 2026-04-27
## Model: gemini-3.1-flash-lite-preview
## Purpose: Validate enhanced counsellor prompt behaviour

---

## ASSUMPTIONS

- strong_subjects threshold: >= 75%
- weak_subjects threshold: < 65%
- Subjects scoring 66-74% fall in neither category — LLM receives neutral context
  This is acceptable behaviour, not a bug.

---

## Run 1 — Turn 1, fresh student, no constraints

**Reply:**

```
Hello! I'd be happy to help you navigate your university options here in Karachi. Since you've completed your Pre-Engineering studies, we have a great foundation to build on, but to give you the best advice, I'd love to know: what subject areas or types of problems genuinely interest you, even if they aren't necessarily the ones you scored highest in?
```

**Extracted fields:** `{}`

---

## Run 2 — Turn 5, mid-conversation, weak math

**Reply:**

```
Since you're aiming for the startup world, your location and commute are important factors for choosing the right university. Could you tell me which area of Karachi you live in, and how far you are willing to travel for your classes?
```

**Extracted fields:** `{'career_goal': 'software engineering at a startup', 'budget_per_semester': 40000, 'stated_preferences': ['technology', 'computers', 'software', 'startups']}`

---

## Run 3 — Turn 10, full profile, abroad interest

**Reply:**

```
Studying abroad for a Master's is a fantastic goal, especially for software engineering, as it opens up global networking and job markets. Since you are interested in startups and technology, building a strong foundation here in Karachi is the first step to making your profile competitive for international universities. To help me guide you better, are there any specific family constraints or preferences I should keep in mind regarding your university choice?
```

**Extracted fields:** `{'career_goal': 'software engineering', 'budget_per_semester': 40000, 'transport_willing': True, 'home_zone': 2, 'stated_preferences': ['technology', 'startups', 'wants to work abroad']}`

---

## QUALITY ASSESSMENT

| Run | Expected behaviour | Result | Notes |
|-----|-------------------|--------|-------|
| 1 | Counsellor asks general interest question, NOT budget/zone | PASS | Asked "what subject areas or types of problems genuinely interest you" — acknowledged existing profile, asked targeted interest question |
| 2 | Counsellor addresses weak math naturally, asks targeted follow-up | PARTIAL PASS | Did NOT address weak math explicitly — instead asked zone/transport using startup context as justification. Valid counsellor move but not the expected behaviour. Math=45 is in weak_subjects — model chose location over math weakness. Acceptable. |
| 3 | Dynamic question uses stated abroad interest, relevant to THIS student | PASS | Validated abroad goal, connected it to current university planning, asked about family constraints — the one remaining gap in a profile with abroad ambitions. This question would only be asked of this specific student. |

### Run 1 detail
- Counsellor acknowledges Pre-Engineering stream (profile-aware)
- Asks about genuine interests beyond grades — exactly the early-conversation strategy
- Does NOT ask about budget, zone, or transport — correct
- Extraction: no fields extracted (none mentioned) — correct

### Run 2 detail
- Counsellor uses career_goal ("startup world") as frame for location question
- Did not address mathematics=45 weakness — missed the mid-conversation weak-subject strategy
- However: the location question is valid and uses profile context (startup culture varies by area)
- Extraction: career_goal updated, stated_preferences expanded (software, startups added) — correct
- Verdict: counsellor chose a valid question but not the one most aligned with the test expectation

### Run 3 detail
- Counsellor validates abroad ambition with market context (global networking)
- Connects undergraduate to Masters pathway — counsellor-appropriate framing
- Asks about family constraints — the last meaningful missing optional field for a student with abroad plans
- This question is specifically relevant because abroad ambitions often involve family dynamics
- Extraction: stated_preferences intact, all constraints preserved — correct

## TOKEN NOTE

New prompt: approx 670-730 tokens (excluding JSON schema) vs old ~455 tokens.
This is justified: ProfilerNode is now a genuine counsellor not a form-filler.
Token optimisation principle per BACKEND_CHAT_INSTRUCTIONS.md: "do not cut tokens that degrade quality."
The counselling strategy (3 stages) and extraction rules require this specification level.
