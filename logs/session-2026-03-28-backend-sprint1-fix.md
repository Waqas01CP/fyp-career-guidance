# Session Log — 2026-03-28 — Backend Sprint 1 Fix

## Task
Fix POST /api/v1/auth/register returning HTTP 500.

---

## Files Modified

### 1. `backend/app/main.py`
**Change:** Added one import line at the bottom of the imports block, immediately before the `lifespan` function definition:
```python
import app.models  # noqa: F401 — registers all 6 SQLAlchemy mappers at startup
```
**Why:** Ensures all 6 SQLAlchemy model classes are in the mapper registry before any request handler fires. Without this, the first query involving a relationship string (e.g. `relationship("ChatSession")` in user.py) would raise `InvalidRequestError: When initializing mapper... could not locate a name`.

### 2. `backend/app/models/__init__.py`
**Change:** No change required. File already contained the correct content (all 6 model imports + `__all__`) exactly as specified.

### 3. `backend/app/core/security.py`
**Change:** Replaced `passlib.context.CryptContext` with direct `bcrypt` library calls.

Before:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

After:
```python
import bcrypt as _bcrypt

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

**Why (third file justification):** After applying the mapper fix, the server still returned 500. The actual traceback revealed a second blocking bug: `passlib==1.7.4` (requirements.txt) is incompatible with `bcrypt==5.0.0` (installed). Two failure modes:
1. `bcrypt.__about__.__version__` — attribute removed in bcrypt 4.x; passlib uses it to detect version.
2. `passlib.handlers.bcrypt.detect_wrap_bug()` internally hashes a >72-byte test secret; bcrypt 4.x+ raises `ValueError` for secrets longer than 72 bytes.

passlib is unmaintained (last release 2017). The fix is to bypass passlib and call the bcrypt library directly, which is what passlib was wrapping anyway. This changes no behavior — same algorithm, same hash format (`$2b$...`), fully compatible with any hashes already stored.

---

## Root Causes Confirmed

1. **Mapper registry missing 4 of 6 models** — `main.py` did not import `app.models`, so ChatSession, Message, Recommendation, ProfileHistory were never registered. SQLAlchemy raises at first relationship resolution. **Fix: `import app.models` in main.py.**

2. **passlib 1.7.4 incompatible with bcrypt 5.0.0** — passlib's internal backend initialization crashes with `ValueError: password cannot be longer than 72 bytes` when probing the bcrypt backend. **Fix: replace passlib with direct bcrypt calls in security.py.**

---

## Verification Result

Server startup:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
No mapper warnings. No import errors.

Curl test:
```
HTTP STATUS: 201
Response: {"access_token":"eyJ...", "token_type":"bearer"}
Server log: 127.0.0.1 - "POST /api/v1/auth/register HTTP/1.1" 201 Created
```

---

## Sprint 1 Gate Status

**UNBLOCKED.** Register endpoint returns 201.

Remaining Sprint 1 gate checklist (to be done next session):
- [ ] POST /api/v1/auth/login → 200 + token
- [ ] GET /api/v1/profile/me → 200 (with valid JWT)
- [ ] POST /api/v1/profile/quiz → 200
- [ ] POST /api/v1/profile/grades → 200
- [ ] POST /api/v1/profile/marksheet → 200
- [ ] POST /api/v1/profile/assessment → 200
- [ ] POST /api/v1/chat/stream → mock SSE response
- [ ] POST /api/v1/admin/seed-knowledge → 200 (admin JWT)
- [ ] All 9 passing → Sprint 1 gate check passed

---

## What the Next Session Should Start With

1. Read CLAUDE.md, BACKEND_CHAT_INSTRUCTIONS.md, and team-updates/ as usual.
2. Test the remaining 8 endpoints in order using curl.
3. Fix any 500s found — read the uvicorn traceback before changing anything.
4. Once all 9 endpoints return expected status codes, run the Sprint 1 gate check with Architecture Chat.
5. Do not start Sprint 2 work until gate check is confirmed passed.
