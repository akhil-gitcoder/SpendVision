import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Response
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuthSession, User


SESSION_COOKIE = "spendvision_session"

password_hasher = PasswordHash.recommended()

# Used so unknown accounts still perform password verification.
_dummy_hash = password_hasher.hash(
    secrets.token_urlsafe(32)
)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(
    password: str,
    user: User | None,
) -> bool:
    stored_hash = user.auth_identifier if user else ""

    # Existing demo accounts do not have valid password hashes.
    if not stored_hash.startswith("$argon2"):
        password_hasher.verify(password, _dummy_hash)
        return False

    try:
        return password_hasher.verify(
            password,
            stored_hash,
        )
    except (ValueError, TypeError, UnknownHashError):
        return False


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        httponly=True,
        secure=get_settings().secure_cookies,
        samesite="lax",
    )


def revoke_session(
    db: Session,
    token: str | None,
) -> None:
    if token:
        db.query(AuthSession).filter(
            AuthSession.token_hash == token_digest(token)
        ).delete()


def issue_session(
    db: Session,
    user: User,
    response: Response,
    previous_token: str | None,
) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)

    # Remove expired sessions belonging to this account.
    db.query(AuthSession).filter(
        AuthSession.user_id == user.id,
        AuthSession.expires_at <= now,
    ).delete()

    # Replace any session already held by this browser.
    revoke_session(db, previous_token)

    token = secrets.token_urlsafe(32)
    lifetime_seconds = (
        settings.session_lifetime_hours * 3600
    )

    session = AuthSession(
        user_id=user.id,
        token_hash=token_digest(token),
        expires_at=now + timedelta(
            seconds=lifetime_seconds
        ),
    )

    db.add(session)
    db.commit()

    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=lifetime_seconds,
        path="/",
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )

    response.headers["Cache-Control"] = "no-store"