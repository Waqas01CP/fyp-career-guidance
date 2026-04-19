# LLM Output Log — SupervisorNode
## Run 1 — gemini-3.1-flash-lite-preview — 2026-04-19

Model: gemini-3.1-flash-lite-preview

### System prompt sent (full text):
```
You are an intent classifier for an academic career guidance system.
Classify the student's message into exactly one of these intents:
get_recommendation, profile_update, fee_query, market_query,
follow_up, clarification, out_of_scope

Rules:
- If the student mentions changing budget, marks, or preferences: profile_update
- If the student asks about a specific university's fees or costs: fee_query
- If the student asks about careers, jobs, or future scope: market_query
- If the student references their existing recommendations: follow_up or clarification
- If unclear between follow_up and clarification: use follow_up
- Never return anything except one of the seven intent strings above

Student message: {user_input}
Respond with only the intent string. No explanation.
```

Note: `{user_input}` is formatted before sending. The formatted prompt is passed as
SystemMessage. user_input is also passed as a separate HumanMessage — required by
Gemini 3.1 API constraint (rejects lone SystemMessage with no non-system messages).

### Raw terminal output:
```
Model: gemini-3.1-flash-lite-preview
  Input: 'What degrees should I study?'
  Intent: get_recommendation

  Input: 'Yaar mujhe CS ka scope batao Pakistan mein'
  Intent: market_query

  Input: 'My budget is now 80,000 rupees'
  Intent: profile_update

  Input: 'How much does FAST charge per semester?'
  Intent: fee_query

  Input: 'Why did NED rank higher than SZABIST?'
  Intent: clarification

  Input: 'What is my RIASEC match score for NED CS?'
  Intent: follow_up

  Input: 'Can you help me with my physics homework?'
  Intent: out_of_scope
```

### Assessment
All 7 test cases classified correctly:
- Roman Urdu correctly classified as market_query (key reason LLM used over keyword matching)
- Budget change → profile_update ✓
- Fee query → fee_query ✓
- Recommendation request → get_recommendation ✓
- Existing recommendation question → clarification ✓ (point 2 says use follow_up if unclear — but this was specific enough for clarification; both route to answer_node so no functional difference)
- Out of scope (homework) → out_of_scope ✓

### Note on follow_up vs clarification
"Why did NED rank higher than SZABIST?" → clarification
"What is my RIASEC match score for NED CS?" → follow_up

Both route to answer_node via route_by_intent. The distinction is cosmetic at the routing level. This is correct behaviour — the spec says "if unclear between follow_up and clarification: use follow_up."
