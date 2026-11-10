from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _password_bytes(password: str) -> bytes:
    # bcrypt учитывает только первые 72 байта
    return password.encode()[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_password_bytes(password), password_hash.encode())


def _create_token(user_id: int, token_type: str, expires_in: timedelta, extra: dict | None = None) -> str:
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "exp": datetime.now(timezone.utc) + expires_in,
        **(extra or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    return _create_token(
        user_id=user_id,
        token_type="access",
        expires_in=timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
        extra={"role": role},
    )


def create_refresh_token(user_id: int, session_version: int) -> str:
    return _create_token(
        user_id=user_id,
        token_type="refresh",
        expires_in=timedelta(days=settings.REFRESH_TOKEN_DAYS),
        extra={"ver": session_version},
    )


def decode_token(token: str, token_type: str) -> dict | None:
    """Payload токена нужного типа или None, если токен неверный или просрочен."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != token_type or not str(payload.get("sub", "")).isdigit():
        return None
    return payload
