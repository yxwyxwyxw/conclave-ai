from __future__ import annotations

from base64 import urlsafe_b64decode, urlsafe_b64encode
import hashlib
import hmac
import os
from typing import Optional

from fastapi import HTTPException, Request, status


COOKIE_NAME = "divination_admin_session"


def admin_password() -> str:
    return os.getenv("DIVINATION_ADMIN_PASSWORD", "changeme")


def signing_secret() -> str:
    explicit = os.getenv("DIVINATION_APP_SECRET")
    if explicit:
        return explicit
    digest = hashlib.sha256(admin_password().encode("utf-8")).hexdigest()
    return f"divination-{digest}"


def sign_session(value: str) -> str:
    payload = value.encode("utf-8")
    signature = hmac.new(
        signing_secret().encode("utf-8"),
        payload,
        hashlib.sha256,
    ).digest()
    return (
        urlsafe_b64encode(payload).decode("ascii").rstrip("=")
        + "."
        + urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    )


def verify_session(token: str) -> Optional[str]:
    try:
        encoded_payload, encoded_signature = token.split(".", 1)
        payload = urlsafe_b64decode(_pad(encoded_payload))
        signature = urlsafe_b64decode(_pad(encoded_signature))
    except Exception:
        return None
    expected = hmac.new(
        signing_secret().encode("utf-8"),
        payload,
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(signature, expected):
        return None
    return payload.decode("utf-8")


def require_admin(request: Request) -> str:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth_required")
    identity = verify_session(token)
    if identity is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="auth_invalid")
    return identity


def _pad(value: str) -> bytes:
    return (value + "=" * (-len(value) % 4)).encode("ascii")
