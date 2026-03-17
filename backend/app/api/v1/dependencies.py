"""
dependencies.py — FastAPI dependency injectors.
get_db, get_current_user, require_admin.
All endpoints that touch protected resources use these.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID as PyUUID
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Decode JWT, load user from DB. Raises 401 if invalid."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error_code": "UNAUTHORIZED",
                                    "message": "Invalid or expired token.",
                                    "details": []})
    user_id_str = payload.get("sub")
    try:
        user_uuid = PyUUID(user_id_str)
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error_code": "UNAUTHORIZED",
                                    "message": "Invalid token subject.",
                                    "details": []})
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail={"error_code": "UNAUTHORIZED",
                                    "message": "User not found.",
                                    "details": []})
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raises 403 if user role is not admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail={"error_code": "FORBIDDEN",
                                    "message": "Admin access required.",
                                    "details": []})
    return current_user
