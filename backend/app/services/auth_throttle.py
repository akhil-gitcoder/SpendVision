from collections import deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException


_lock = Lock()

_attempts: dict[str, deque] = {}
_global_attempts: deque = deque()


def check_auth_attempt(email: str) -> None:
    now = monotonic()

    with _lock:
        # Track total attempts during the last minute.
        while (
            _global_attempts
            and _global_attempts[0] <= now - 60
        ):
            _global_attempts.popleft()

        # Track attempts per email during the last 5 minutes.
        for key in list(_attempts):
            history = _attempts[key]

            while history and history[0] <= now - 300:
                history.popleft()

            if not history:
                del _attempts[key]

        history = _attempts.get(email, deque())

        if (
            len(history) >= 10
            or len(_global_attempts) >= 120
        ):
            raise HTTPException(
                status_code=429,
                detail=(
                    "Too many sign-in attempts. "
                    "Please try again in a few minutes."
                ),
                headers={"Retry-After": "300"},
            )

        history.append(now)
        _attempts[email] = history
        _global_attempts.append(now)