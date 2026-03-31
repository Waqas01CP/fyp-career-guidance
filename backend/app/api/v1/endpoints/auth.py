"""
auth.py — Authentication endpoints.
POST /api/v1/auth/register
POST /api/v1/auth/login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.models.profile import StudentProfile
from app.schemas.auth import UserCreate, UserLogin, TokenResponse
from app.models.session import ChatSession

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new student account. Returns JWT immediately — no separate login needed."""
    if len(payload.password) < 8:
        raise HTTPException(status_code=422, detail={"error_code": "VALIDATION_ERROR",
                                                      "message": "Password must be at least 8 characters.",
                                                      "details": ["password"]})
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"error_code": "EMAIL_ALREADY_EXISTS",
                                                      "message": "An account with this email already exists.",
                                                      "details": ["email"]})
    user = User(email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    await db.flush()  # get user.id before creating child rows

    # Create empty profile row immediately
    profile = StudentProfile(user_id=user.id)
    db.add(profile)
    await db.flush()

    # Create a ChatSession so Flutter can read session_id from GET /profile/me
    new_session = ChatSession(user_id=user.id)
    db.add(new_session)
    await db.flush()
    # No explicit commit — get_db() context manager commits on clean exit

    await db.refresh(user)

    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    """Authenticate with email + password. Returns JWT."""
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    # Same error for wrong email or wrong password — prevents user enumeration
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"error_code": "INVALID_CREDENTIALS",
                                                      "message": "Incorrect email or password.",
                                                      "details": []})
    token = create_access_token(str(user.id), user.role)
    return TokenResponse(access_token=token)
