from typing import Optional

from fastapi import Header, HTTPException

from app.services.jwt_service import get_jwt_service


async def auth(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency: require a valid `Authorization: Bearer <token>`.

    Returns the decoded JWT claims, or raises 401.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        return get_jwt_service().decode(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
