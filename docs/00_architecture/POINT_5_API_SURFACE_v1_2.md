# Point 5 — API Surface Contract
## FYP: AI-Assisted Academic Career Guidance System
### Status: COMPLETE AND LOCKED
### Date: March 2026
### Change Log:
### v1.0 — Initial lock. Defines all 9 endpoints: exact URL, method, auth,
###         request schema, response schema, and HTTP status codes.
###         SSE protocol fully specified: all status state values, all three
###         event types, and full payload schemas for university_card and
###         roadmap_timeline rich_ui events.
###         Synthesizes from Points 1, 2, 3, BACKEND_CHAT_INSTRUCTIONS, and
###         FRONTEND_CHAT_INSTRUCTIONS. Nothing invented — every field traces
###         back to a locked decision.
### v1.1 — Post-audit fixes (8 issues resolved):
###         (1) RIASEC score range corrected throughout: averaged 1–5 → summed
###             10–50. Example values updated to valid range.
###         (2) Endpoint 4 description corrected: "averaged/1–5" → "summed/10–50".
###         (3) Endpoint 4 error table corrected: "outside 1–5" → "outside 10–50".
###         (4) Endpoint 9 seed count corrected: 960 → 1140
###             3 curriculum levels × 5 subjects × 76 questions per subject per level.
###         (5) Decisions table: university_card field count corrected 18 → 20.
###         (6) Decisions table: RIASEC quiz format and schema decisions added.

---

## PURPOSE

This document is the **interface contract** between Waqas (backend) and the Flutter
frontend. It answers precisely: for every endpoint, what does the frontend send and
what does the backend return?

Points 1, 2, and 3 each define pieces of the API surface. This document is the
single place that assembles them all into one reference. If there is a conflict
between this document and Points 1, 2, or 3, this document loses — the earlier
Points are authoritative. Flag the conflict and resolve against the earlier Point.

---

## ENDPOINT INDEX

| # | Method | Path | Auth | Description |
|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/register` | None | Create account |
| 2 | POST | `/api/v1/auth/login` | None | Get JWT token |
| 3 | GET | `/api/v1/profile/me` | JWT | Load profile + onboarding state |
| 4 | POST | `/api/v1/profile/quiz` | JWT | Submit RIASEC quiz answers |
| 5 | POST | `/api/v1/profile/grades` | JWT | Submit academic marks |
| 6 | POST | `/api/v1/profile/marksheet` | JWT | Upload marksheet image for OCR |
| 7 | POST | `/api/v1/profile/assessment` | JWT | Submit capability assessment answers |
| 8 | POST | `/api/v1/chat/stream` | JWT | SSE streaming chat |
| 9 | POST | `/api/v1/admin/seed-knowledge` | JWT (admin only) | Re-seed JSON knowledge base |

**Base URL prefix:** `/api/v1/` on all endpoints — never omit this. Rate limiting on
endpoint 8: 10 requests/minute per IP via `slowapi`.

---

## AUTH CONVENTION

JWT token format: `Authorization: Bearer <token>`

JWT payload:
```json
{"sub": "<user_uuid>", "role": "student", "exp": <unix_timestamp>}
```

Token expiry: 60 minutes. Frontend stores token in `flutter_secure_storage`.
Never accept `user_id` from request body — always extract from JWT `sub` field.

---

## STANDARD ERROR RESPONSE

All endpoints return this shape on any error (4xx or 5xx):

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "The provided marks exceed 100.",
  "details": ["academic.mathematics"]
}
```

`error_code` values used across all endpoints:

| `error_code` | HTTP status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body failed Pydantic validation |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password |
| `EMAIL_ALREADY_EXISTS` | 409 | Registration with existing email |
| `UNAUTHORIZED` | 401 | Missing or invalid JWT |
| `FORBIDDEN` | 403 | Valid JWT but insufficient role (e.g., student hitting admin endpoint) |
| `NOT_FOUND` | 404 | Resource does not exist for this user |
| `RATE_LIMITED` | 429 | Too many requests (chat/stream only) |
| `INTERNAL_ERROR` | 500 | Unhandled server error |

Frontend must handle all of these. Never assume a 200 response.

---

## ENDPOINT 1 — `POST /api/v1/auth/register`

**Auth required:** None
**File:** `api/v1/endpoints/auth.py`

### Request
```json
{
  "email": "student@example.com",
  "password": "minimum8chars"
}
```

| Field | Type | Rules |
|---|---|---|
| `email` | `EmailStr` | Must be valid email format. Unique. |
| `password` | `str` | Minimum 8 characters. Backend hashes with Bcrypt before storage. |

### Response — 201 Created
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Frontend receives the token immediately on registration — no separate login step needed.
Student is routed to onboarding (`onboarding_stage: "not_started"`).

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| Email already registered | `EMAIL_ALREADY_EXISTS` | 409 |
| Invalid email format | `VALIDATION_ERROR` | 422 |
| Password too short | `VALIDATION_ERROR` | 422 |

---

## ENDPOINT 2 — `POST /api/v1/auth/login`

**Auth required:** None
**File:** `api/v1/endpoints/auth.py`

### Request
```json
{
  "email": "student@example.com",
  "password": "minimum8chars"
}
```

### Response — 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| Email not found or wrong password | `INVALID_CREDENTIALS` | 401 |

Do NOT distinguish between "email not found" and "wrong password" in the error
message — both return `INVALID_CREDENTIALS`. Security: prevents user enumeration.

---

## ENDPOINT 3 — `GET /api/v1/profile/me`

**Auth required:** JWT
**File:** `api/v1/endpoints/profile.py`

### Request
No body. User identity comes from JWT `sub`.

### Response — 200 OK
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "onboarding_stage": "grades_complete",
  "education_level": "inter_part2",
  "student_mode": "inter",
  "grade_system": "percentage",
  "stream": "Pre-Engineering",
  "board": "Karachi Board",
  "riasec_scores": {"R": 32, "I": 45, "A": 28, "S": 31, "E": 38, "C": 42},
  "subject_marks": {"mathematics": 87, "physics": 72, "chemistry": 65, "english": 80, "biology": 0},
  "capability_scores": {"mathematics": 58.3, "physics": 61.0, "chemistry": 75.0, "biology": 80.0, "english": 66.7},
  "budget_per_semester": 60000,
  "transport_willing": true,
  "home_zone": 2,
  "stated_preferences": ["Computer Science", "Engineering"],
  "family_constraints": null,
  "career_goal": "work in tech",
  "student_notes": null,
  "updated_at": "2026-03-13T12:00:00Z"
}
```

All `ProfileOut` fields returned. `riasec_scores`, `subject_marks`, `capability_scores`,
`stated_preferences` are empty `{}` / `{}` / `{}` / `[]` if not yet filled — never null.

**Flutter uses `onboarding_stage` to route the student on every app launch:**

| `onboarding_stage` | Flutter routes to |
|---|---|
| `"not_started"` | RIASEC quiz screen |
| `"riasec_complete"` | Grades input screen |
| `"grades_complete"` | Capability assessment screen |
| `"assessment_complete"` | Chat / recommendation dashboard |

Frontend never determines navigation logic independently — it always follows this field.

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| No valid JWT | `UNAUTHORIZED` | 401 |
| Profile row does not exist (should never occur post-register) | `NOT_FOUND` | 404 |

---

## ENDPOINT 4 — `POST /api/v1/profile/quiz`

**Auth required:** JWT
**File:** `api/v1/endpoints/profile.py`

RIASEC quiz submission. Overwrites `riasec_scores` in `student_profiles`.
Advances `onboarding_stage` from `"not_started"` to `"riasec_complete"`.
Writes a `"quiz_update"` row to `profile_history` (pre-change snapshot captured before write).

### Request
```json
{
  "responses": {
    "R": 32,
    "I": 45,
    "A": 28,
    "S": 31,
    "E": 38,
    "C": 42
  }
}
```

`responses` contains summed scores per dimension, computed by the frontend from
10 Likert responses per dimension (each scored 1–5). Each value is an integer 10–50.
All six keys (`R`, `I`, `A`, `S`, `E`, `C`) must be present.

### Response — 200 OK
```json
{
  "onboarding_stage": "riasec_complete"
}
```

Minimal response — Flutter only needs to know the new stage to route forward.

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| Missing dimension key | `VALIDATION_ERROR` | 422 |
| Score outside 10–50 | `VALIDATION_ERROR` | 422 |

---

## ENDPOINT 5 — `POST /api/v1/profile/grades`

**Auth required:** JWT
**File:** `api/v1/endpoints/profile.py`

Academic marks submission. Runs IBCC conversion server-side if
`education_level` is `"o_level"` or `"a_level"`. Stores marks as percentages
regardless of input format. Advances `onboarding_stage` to `"grades_complete"`.
Writes a `"grade_update"` row to `profile_history`.

### Request
```json
{
  "education_level": "inter_part2",
  "stream": "Pre-Engineering",
  "subject_marks": {
    "mathematics": 87,
    "physics": 72,
    "chemistry": 65,
    "english": 80,
    "biology": 0
  },
  "board": "Karachi Board"
}
```

| Field | Type | Rules |
|---|---|---|
| `education_level` | `str` | One of: `"matric"`, `"inter_part1"`, `"inter_part2"`, `"completed_inter"`, `"o_level"`, `"a_level"` |
| `stream` | `str \| None` | Required for Pakistani board students. `null` for O/A Level — ProfilerNode will confirm conversationally. |
| `subject_marks` | `dict[str, float]` | Keys are lowercase subject names. Values are raw marks (percentage or O/A Level grade). |
| `board` | `str \| None` | One of: `"Karachi Board"`, `"Federal Board"`, `"AKU"`, `"Cambridge"`, `"Other"`. `null` for O/A Level students. |

**IBCC conversion is applied server-side in the service layer:**
When `education_level` is `"o_level"` or `"a_level"`, the endpoint converts raw
grade letters (A*, A, B, C, D, E) to percentage equivalents before storage.
After conversion, all stored marks are always percentage integers — FilterNode
and ScoringNode never see raw letter grades.

**Derived fields written server-side (never accepted from request body):**

| `education_level` received | `student_mode` stored | `grade_system` stored |
|---|---|---|
| `"matric"` | `"matric_planning"` | `"percentage"` |
| `"inter_part1"` | `"inter"` | `"percentage"` |
| `"inter_part2"` | `"inter"` | `"percentage"` |
| `"completed_inter"` | `"inter"` | `"percentage"` |
| `"o_level"` | `"matric_planning"` | `"olevel_alevel"` |
| `"a_level"` | `"inter"` | `"olevel_alevel"` |

### Response — 200 OK
```json
{
  "onboarding_stage": "grades_complete"
}
```

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| Invalid `education_level` value | `VALIDATION_ERROR` | 422 |
| Mark value outside 0–100 (after IBCC conversion) | `VALIDATION_ERROR` | 422 |

---

## ENDPOINT 6 — `POST /api/v1/profile/marksheet`

**Auth required:** JWT
**File:** `api/v1/endpoints/profile.py`

OCR marksheet upload. Accepts image, runs Gemini Vision extraction, returns parsed
marks with confidence score. Does **not** automatically update `subject_marks` in
the database — frontend must show OCR verification modal, allow user to correct, then
submit corrected marks via Endpoint 5 (`POST /profile/grades`).

### Request
`multipart/form-data` with field `file` containing the image.
Supported formats: JPEG, PNG. Max size: 10MB.
On web: use browser file picker (camera package does not work on Flutter Web).
On Android: use camera overlay or image_picker, compress before upload.

### Response — 200 OK
```json
{
  "status": "success",
  "extracted_marks": {
    "mathematics": 80,
    "physics": 75,
    "chemistry": 68,
    "english": 82,
    "biology": 0
  },
  "confidence_score": 0.92,
  "requires_manual_verification": false
}
```

| Field | Values |
|---|---|
| `status` | `"success"` \| `"partial"` \| `"failed"` |
| `extracted_marks` | Dict of lowercase subject → float percentage |
| `confidence_score` | Float 0.0–1.0 |
| `requires_manual_verification` | `true` when `confidence_score < 0.80` — always, regardless of any other condition |

**Rule:** If `confidence_score < 0.80`, `requires_manual_verification` is `true`
regardless. Flutter blocks chat entry and shows the OCR verification modal with
inline editable fields until the student confirms or corrects the extracted marks.
The modal never navigates away from the current screen.

When `status` is `"partial"`: some subjects were extracted, others could not be read.
`extracted_marks` contains only successfully extracted subjects.
When `status` is `"failed"`: extraction produced no usable data. `extracted_marks` is `{}`.

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| File too large or unsupported format | `VALIDATION_ERROR` | 422 |
| Gemini Vision API failure | `INTERNAL_ERROR` | 500 |

---

## ENDPOINT 7 — `POST /api/v1/profile/assessment`

**Auth required:** JWT
**File:** `api/v1/endpoints/profile.py`

Capability assessment submission. Scores answers deterministically, writes results to
`capability_scores`. Advances `onboarding_stage` to `"assessment_complete"`.
Writes an `"assessment_update"` row to `profile_history`.

### Request
```json
{
  "responses": {
    "mathematics": [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1],
    "physics":     [1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1],
    "chemistry":   [0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1],
    "biology":     [1, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0],
    "english":     [1, 0, 1, 1, 1, 0, 1, 1, 0, 1, 0, 1]
  }
}
```

`responses` is a dict of subject → list of `0` or `1` values.
Each list contains one entry per question answered, in the order they were presented.
`1` = correct, `0` = incorrect.
All five subjects must be present. List length must match
`ASSESSMENT_QUESTIONS_PER_SESSION.easy + medium + hard = 12` per subject.

**Scoring (deterministic — no LLM involved):**
```python
capability_score_per_subject = (sum(answers) / len(answers)) * 100
```

Result stored as float in `capability_scores` JSONB, keyed by lowercase subject name.

### Response — 200 OK
```json
{
  "onboarding_stage": "assessment_complete",
  "capability_scores": {
    "mathematics": 66.7,
    "physics": 58.3,
    "chemistry": 75.0,
    "biology": 66.7,
    "english": 66.7
  }
}
```

Scores are returned so the Flutter constraint chat screen can show a capability summary
before the student enters the main chat. Not shown as raw numbers to the student —
framed as relative strength indicators by the frontend.

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| Missing subject | `VALIDATION_ERROR` | 422 |
| List length ≠ 12 | `VALIDATION_ERROR` | 422 |
| Value outside 0 or 1 | `VALIDATION_ERROR` | 422 |

---

## ENDPOINT 8 — `POST /api/v1/chat/stream`

**Auth required:** JWT
**File:** `api/v1/endpoints/chat.py`
**Rate limit:** 10 requests/minute per IP (`slowapi`)

The core endpoint. Returns a Server-Sent Events (SSE) stream.
The frontend must use a streaming HTTP client — standard HTTP clients do not handle SSE.
Recommended Flutter package: `http` with streaming response parser. Do not use `dio`.

### Request
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440001",
  "user_input": "What CS programs suit my profile?",
  "context_overrides": {}
}
```

| Field | Type | Rules |
|---|---|---|
| `session_id` | `UUID` | Must be a valid UUID for this user's session. |
| `user_input` | `str` | The student's message. PII-scrubbed before any LLM call. |
| `context_overrides` | `dict` | Optional. Explicit constraint overrides: `{"budget": 80000}`. Frontend can send these alongside messages. Merged into `active_constraints` before the graph runs. |

**Tenant isolation:** The endpoint extracts `user_id` from the JWT `sub` field and
loads the correct `student_profile` into `AgentState`. It never accepts `user_id` from
the request body.

**Pre-graph setup (in endpoint, before graph runs):**
1. Decode JWT → extract `user_id`
2. Load `student_profile` from DB using `user_id`
3. Restore `AgentState` from `AsyncPostgresSaver` (chat history restored)
4. Load `previous_roadmap` from most recent `recommendations` row for this user
5. Apply `context_overrides` to `active_constraints` if present
6. If pipeline rerun: set `previous_roadmap = current_roadmap`, clear `current_roadmap = []`
7. Run LangGraph graph

### Response — `text/event-stream`

The response body is a stream of SSE events. Each event follows the standard SSE format:

```
event: <event_type>\n
data: <json_payload>\n
\n
```

**Three event types:**

---

### SSE Event: `status`

Emitted when a new pipeline node begins executing. Flutter uses this to update the
`ThinkingIndicator` label.

```
event: status
data: {"state": "profiling"}
```

**All valid `state` values:**

| `state` value | When emitted |
|---|---|
| `"profiling"` | ProfilerNode begins executing |
| `"filtering_degrees"` | FilterNode begins — "Checking your eligibility..." |
| `"scoring_degrees"` | ScoringNode begins — "Ranking your matches..." |
| `"generating_explanation"` | ExplanationNode begins — "Writing your recommendations..." |
| `"fetching_fees"` | AnswerNode calls `fetch_fees()` tool |
| `"fetching_market_data"` | AnswerNode calls `lag_calc()` tool |
| `"done"` | Stream is complete. No more events will follow. |

`"done"` is the terminal event. Flutter dismisses the `ThinkingIndicator` when this arrives.

Note: SupervisorNode emits no status event — it is internal routing only with no
visible UI state. AnswerNode handling `follow_up` or `clarification` intents (reading
`current_roadmap` directly without a tool call) also emits no status event.

---

### SSE Event: `chunk`

Streamed text from ExplanationNode or AnswerNode. Flutter appends each chunk to the
current assistant bubble as it arrives, creating a typewriter effect.

```
event: chunk
data: {"text": "Based on your profile, I'd recommend "}
```

```
event: chunk
data: {"text": "BS Computer Science at NED University as your top match."}
```

`text` is a UTF-8 string fragment. May be a partial word or sentence — Flutter must
append, not replace. Chunks arrive in order. Roman Urdu chunks are also plain UTF-8.

---

### SSE Event: `rich_ui`

Structured data for Flutter to render a rich widget inside the chat bubble.
Arrives after the text explanation has been streamed.

```
event: rich_ui
data: {"type": "university_card", "payload": {...}}
```

**Two `type` values:**

---

#### `university_card` Payload

One event per ranked degree. Up to 5 events emitted in rank order.

```json
{
  "type": "university_card",
  "payload": {
    "rank": 1,
    "degree_id": "neduet_bs_cs",
    "degree_name": "BS Computer Science",
    "university_id": "neduet",
    "university_name": "NED University of Engineering & Technology",
    "field_id": "computer_science",
    "total_score": 0.84,
    "match_score_normalised": 0.89,
    "future_score": 8.4,
    "merit_tier": "likely",
    "eligibility_tier": "confirmed",
    "eligibility_note": null,
    "fee_per_semester": 27500,
    "aggregate_used": 82.5,
    "soft_flags": [
      {
        "type": "commute_distance",
        "message": "NED is in Zone 3 — moderate commute from your Zone 2 area",
        "actionable": "Travel time approximately 30 minutes"
      }
    ],
    "lifecycle_status": "Emerging",
    "risk_factor": "Low",
    "rozee_live_count": 1240,
    "rozee_last_updated": "2026-03-10",
    "policy_pending_verification": false
  }
}
```

20 fields total. Source for each:

| Field | Source | Purpose |
|---|---|---|
| `rank` | ScoringNode sort order | Card display order |
| `degree_id` | `universities.json` | Cross-reference key |
| `degree_name` | `universities.json` | Display |
| `university_id` | `universities.json` | Cross-reference key |
| `university_name` | `universities.json` | Display |
| `field_id` | `universities.json` | Links to lag_model/affinity entries |
| `total_score` | ScoringNode | Match bar percentage |
| `match_score_normalised` | ScoringNode | RIASEC alignment component |
| `future_score` | `lag_model.json computed.future_value` | FutureValue badge |
| `merit_tier` | FilterNode | Marks-based merit tier badge |
| `eligibility_tier` | FilterNode | Stream eligibility banner colour |
| `eligibility_note` | FilterNode (reads from `universities.json`) | Amber banner when `eligibility_tier = "likely"` |
| `fee_per_semester` | `universities.json` | Fee display |
| `aggregate_used` | FilterNode | Raw student aggregate (shown in thought trace) |
| `soft_flags` | FilterNode | Array of `{type, message, actionable}` objects — each rendered as inline notice |
| `lifecycle_status` | `lag_model.json` | `LagScoreBadge` widget: `"Emerging"` \| `"Peak"` \| `"Saturated"` |
| `risk_factor` | `lag_model.json` | Risk indicator dot: `"Low"` \| `"Medium"` \| `"High"` |
| `rozee_live_count` | `lag_model.json employment_data` | "X active jobs" count |
| `rozee_last_updated` | `lag_model.json employment_data` | "Last updated X days ago" notice |
| `policy_pending_verification` | `universities.json` | Amber caution banner |

**`merit_tier` vs `eligibility_tier` distinction:**
- `eligibility_tier` — stream-based eligibility: `"confirmed"` (fully eligible stream) or `"likely"` (conditionally eligible stream requiring bridge course or subject waiver). Comes from which FilterNode output list the degree appeared in.
- `merit_tier` — marks-based tier: `"confirmed"` | `"likely"` | `"stretch"` | `"improvement_needed"`. Based on aggregate vs historical cutoff range.
These are independent. A degree can be `eligibility_tier: "confirmed"` and `merit_tier: "stretch"` simultaneously.

**`policy_pending_verification: true`** → Flutter renders amber banner:
*"Policy verification pending — confirm with university directly."*

**`eligibility_tier: "likely"` with non-null `eligibility_note`** → Flutter renders
amber banner with the note text (e.g., "Bridge course required for Pre-Medical students").

---

#### `roadmap_timeline` Payload

One event per recommendation run (not per degree). Summarises the student's journey
from current status to projected 2030 outcome for the top-ranked degree.

```json
{
  "type": "roadmap_timeline",
  "payload": {
    "steps": [
      {
        "label": "Current Status",
        "detail": "Inter Part 2, Pre-Engineering, 82% aggregate",
        "status": "complete"
      },
      {
        "label": "Recommended Degree",
        "detail": "BS Computer Science — NED University (4 years)",
        "status": "next"
      },
      {
        "label": "Industry Entry",
        "detail": "Junior Software Engineer or ML Engineer role",
        "status": "future"
      },
      {
        "label": "2030 Outlook",
        "detail": "CS graduates projected 45% demand growth. 1,240 active roles on Rozee today.",
        "status": "future"
      }
    ],
    "field_id": "computer_science",
    "degree_id": "neduet_bs_cs"
  }
}
```

| Field | Type | Purpose |
|---|---|---|
| `steps` | Array of 4 objects | Rendered as vertical timeline by `RoadmapTimeline` widget |
| `steps[].label` | str | Step heading |
| `steps[].detail` | str | One-line context |
| `steps[].status` | `"complete"` \| `"next"` \| `"future"` | Controls step icon and colour |
| `field_id` | str | Frontend can deep-link to market data view |
| `degree_id` | str | Frontend can deep-link to degree detail |

`status` values:
- `"complete"` — student's current position. Shown with filled circle, teal.
- `"next"` — the recommended degree. Shown with arrow/highlight, teal.
- `"future"` — post-graduation steps. Shown with outline circle, slate.

---

### Full SSE Stream Example

A complete `get_recommendation` pipeline run looks like this:

```
event: status
data: {"state": "filtering_degrees"}

event: status
data: {"state": "scoring_degrees"}

event: status
data: {"state": "generating_explanation"}

event: chunk
data: {"text": "Looking at your profile — 82% aggregate, strong Investigative "}

event: chunk
data: {"text": "and Conventional RIASEC scores, budget of Rs. 60,000/semester — "}

event: chunk
data: {"text": "here are your best matches:\n\n"}

event: rich_ui
data: {"type": "university_card", "payload": {"rank": 1, "degree_name": "BS Computer Science", "university_name": "NED University", ...}}

event: rich_ui
data: {"type": "university_card", "payload": {"rank": 2, "degree_name": "BS Computer Science", "university_name": "FAST-NUCES", ...}}

event: rich_ui
data: {"type": "roadmap_timeline", "payload": {"steps": [...], "field_id": "computer_science", "degree_id": "neduet_bs_cs"}}

event: chunk
data: {"text": "Your Physics assessment shows 61% — ECAT weights Physics at 30%. "}

event: chunk
data: {"text": "I'd focus there before the test. What else would you like to know?"}

event: status
data: {"state": "done"}
```

Status events precede the content they announce. Text chunks stream first, then
rich_ui events for cards. The `done` event is always last.

---

### SSE Flutter Parsing Pattern

```dart
final request = http.Request('POST', Uri.parse('$baseUrl/api/v1/chat/stream'));
request.headers['Authorization'] = 'Bearer $token';
request.headers['Content-Type'] = 'application/json';
request.body = jsonEncode({
  "session_id": sessionId,
  "user_input": userInput,
  "context_overrides": contextOverrides
});

final streamedResponse = await client.send(request);
String currentEvent = '';

streamedResponse.stream
  .transform(utf8.decoder)
  .transform(const LineSplitter())
  .listen((line) {
    if (line.startsWith('event:')) {
      currentEvent = line.substring(6).trim();
    } else if (line.startsWith('data:')) {
      final data = jsonDecode(line.substring(5).trim());
      switch (currentEvent) {
        case 'status':
          if (data['state'] == 'done') {
            dismissThinkingIndicator();
          } else {
            updateThinkingIndicator(data['state']);
          }
          break;
        case 'chunk':
          appendToCurrentBubble(data['text']);
          break;
        case 'rich_ui':
          renderRichComponent(data['type'], data['payload']);
          break;
      }
    }
  });
```

### Errors on Chat Endpoint
| Condition | `error_code` | HTTP |
|---|---|---|
| Rate limit exceeded | `RATE_LIMITED` | 429 |
| `session_id` does not belong to this user | `FORBIDDEN` | 403 |
| LangGraph internal failure | `INTERNAL_ERROR` | 500 |

On 500: Flutter shows a generic retry prompt. Never expose stack traces to the client.

---

## ENDPOINT 9 — `POST /api/v1/admin/seed-knowledge`

**Auth required:** JWT with `role: "admin"`
**File:** `api/v1/endpoints/profile.py` (or a dedicated `admin.py` — Waqas's call)

Re-reads the JSON files from `backend/app/data/` and reseeds the PostgreSQL database.
Used after Fazal updates a JSON file and the server needs to reflect the new data.

This endpoint is operational scaffolding — not student-facing. Must be idempotent:
running it twice with the same data must produce identical DB state (UPSERT, never
raw INSERT).

### Request
No body required. JWT must have `role: "admin"`.

### Response — 200 OK
```json
{
  "status": "success",
  "seeded": {
    "universities": 20,
    "lag_model_fields": 30,
    "affinity_matrix_fields": 30,
    "assessment_questions": 1140
  }
}
```

`assessment_questions: 1140` = 3 curriculum levels × 5 subjects × 76 questions
per subject per level. Point 1 specifies 76 per subject per curriculum level
(20 easy, 32 medium, 24 hard). 3 × 5 × 76 = 1140 total question records.

### Errors
| Condition | `error_code` | HTTP |
|---|---|---|
| JWT role is not `"admin"` | `FORBIDDEN` | 403 |
| JSON validation fails (invalid data file) | `VALIDATION_ERROR` | 422 |
| File not found on disk | `INTERNAL_ERROR` | 500 |

---

## HTTP STATUS CODES — COMPLETE REFERENCE

| Code | Used when |
|---|---|
| 200 | Successful GET or POST that returns data |
| 201 | Successful resource creation (register only) |
| 401 | Missing/invalid JWT, or wrong credentials |
| 403 | Valid JWT but insufficient permissions |
| 404 | Requested resource not found for this user |
| 409 | Conflict — email already registered |
| 422 | Request body failed Pydantic validation |
| 429 | Rate limit exceeded on `/chat/stream` |
| 500 | Unhandled server error |

204 (No Content) is NOT used — every successful endpoint returns a body.

---

## DECISIONS LOCKED IN POINT 5

| Decision | Choice |
|---|---|
| API prefix | `/api/v1/` on all endpoints — never omit |
| Auth method | JWT Bearer token, 60-minute expiry, `sub` = user UUID |
| user_id source | Always from JWT `sub` — never from request body |
| Error format | `{"error_code": ..., "message": ..., "details": [...]}` on all failures |
| `INVALID_CREDENTIALS` | Same error for "email not found" and "wrong password" — prevents user enumeration |
| Registration response | Returns JWT immediately — no separate login step needed |
| IBCC conversion location | Endpoint 5 service layer — before storage, never in agents |
| `student_mode` and `grade_system` derivation | Server-side from `education_level` — never accepted from request body |
| Marksheet OCR response | Does NOT write to DB — frontend must confirm via Endpoint 5 |
| `requires_manual_verification` rule | Always `true` when `confidence_score < 0.80` — no exceptions |
| Assessment response format | `{0, 1}` per-question list per subject — not raw answers |
| Assessment scoring | Deterministic: `(sum / count) * 100` per subject — no LLM |
| Onboarding stage progression | Endpoint 4 → `riasec_complete`, Endpoint 5 → `grades_complete`, Endpoint 7 → `assessment_complete` |
| RIASEC quiz format | 60 questions, 10 per dimension, 5-point Likert (1–5 per question), summed per dimension, range 10–50 |
| RIASEC request schema | `dict[str, int]` — keys R/I/A/S/E/C, values 10–50 (summed Likert) |
| SSE event types | Three exactly: `status`, `chunk`, `rich_ui` — no others |
| SSE `done` event | Terminal signal — always emitted last; Flutter dismisses ThinkingIndicator on receipt |
| SSE status state values | 7 exact strings: `profiling`, `filtering_degrees`, `scoring_degrees`, `generating_explanation`, `fetching_fees`, `fetching_market_data`, `done` |
| SupervisorNode status event | None emitted — internal routing only, no UI state |
| SSE `rich_ui` types | Two: `university_card`, `roadmap_timeline` |
| `university_card` payload | 20 fields as defined above — source for each field documented |
| `roadmap_timeline` payload | 4-step array + `field_id` + `degree_id` |
| `roadmap_timeline` step status values | `"complete"`, `"next"`, `"future"` |
| `merit_tier` vs `eligibility_tier` | Independent fields — merit is marks-based (4 values), eligibility is stream-based (2 values) |
| `assessment_questions` seed count | 1140 — 3 curriculum levels × 5 subjects × 76 per subject per level |
| 204 No Content | Not used — every endpoint returns a body |
| Rate limiting | `slowapi`, 10 req/min per IP on `/chat/stream` only |
| Flutter SSE package | `http` with streaming parser — not `dio` |

---

*Point 5 v1.0 — March 2026 (initial lock — complete API surface contract for all 9 endpoints)*
*Point 5 v1.1 — March 2026 (post-audit: RIASEC range 1–5 → 10–50; quiz count 30→60; assessment_questions 960→380; university_card field count 18→20; decisions table updated)*
*Point 5 v1.2 — March 2026 (assessment_questions corrected again: 380 → 1140; Point 1 specifies 76 per subject per curriculum level, 3 levels × 5 subjects × 76 = 1140)*