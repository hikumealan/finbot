"""FastAPI dependency injection."""
from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from finbot.db.database import get_session, init_db
from finbot.security.encryption import get_or_create_key

ALGORITHM = "HS256"


def _get_secret() -> str:
    return get_or_create_key()


def get_db() -> Generator[Session, None, None]:
    init_db()
    session = get_session()
    try:
        yield session
    finally:
        session.close()


def get_current_user(request: Request) -> dict:
    """Validate JWT from cookie or Authorization header."""
    from finbot.config import settings

    if not settings.require_pin:
        return {"authenticated": True}

    token = request.cookies.get("finbot_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[ALGORITHM])
        return {"authenticated": True, "sub": payload.get("sub")}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[dict, Depends(get_current_user)]
