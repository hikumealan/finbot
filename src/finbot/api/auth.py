"""PIN-based authentication with JWT tokens."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, Response, status
from jose import jwt
from pydantic import BaseModel

from finbot.api.deps import ALGORITHM, DbSession, _get_secret
from finbot.config import settings
from finbot.models.user_profile import UserProfile

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode("utf-8")).hexdigest()


class LoginRequest(BaseModel):
    pin: str


class AuthStatus(BaseModel):
    authenticated: bool
    require_pin: bool
    has_pin: bool


@router.post("/login")
def login(body: LoginRequest, response: Response, db: DbSession):
    profile = db.query(UserProfile).first()
    expires_at = (datetime.now(UTC) + timedelta(minutes=settings.session_timeout_minutes)).isoformat()

    if not profile or not profile.pin_hash:
        token = _create_token()
        _set_cookie(response, token)
        return {"status": "ok", "message": "No PIN required", "expires_at": expires_at}

    if _hash_pin(body.pin) != profile.pin_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect PIN")

    token = _create_token()
    _set_cookie(response, token)
    return {"status": "ok", "expires_at": expires_at}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("finbot_token")
    return {"status": "ok"}


@router.get("/status", response_model=AuthStatus)
def auth_status(db: DbSession):
    profile = db.query(UserProfile).first()
    return AuthStatus(
        authenticated=False,
        require_pin=settings.require_pin,
        has_pin=bool(profile and profile.pin_hash),
    )


def _create_token() -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.session_timeout_minutes)
    return jwt.encode({"sub": "finbot_user", "exp": expire}, _get_secret(), algorithm=ALGORITHM)


def _set_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="finbot_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_timeout_minutes * 60,
    )
