from datetime import datetime, timezone
from functools import lru_cache

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.ai.provider import (
    LLMProvider,
    get_llm_provider,
)
from app.config import get_settings
from app.database import get_db
from app.models import AuthSession, User
from app.services.auth import (
    SESSION_COOKIE,
    token_digest,
)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE)

    if not token or not (20 <= len(token) <= 128):
        raise HTTPException(
            status_code=401,
            detail="Please sign in to continue.",
        )

    session = db.query(AuthSession).filter(
        AuthSession.token_hash == token_digest(token),
        AuthSession.expires_at > datetime.now(timezone.utc),
    ).first()

    if session is None or session.user is None:
        raise HTTPException(
            status_code=401,
            detail=(
                "Your session has expired. "
                "Please sign in again."
            ),
        )

    return session.user


@lru_cache
def _provider_singleton() -> LLMProvider | None:
    return get_llm_provider(get_settings())


def get_provider() -> LLMProvider | None:
    return _provider_singleton()