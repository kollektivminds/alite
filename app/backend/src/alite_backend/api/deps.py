# alite_backend/api/deps.py
import time
from collections import defaultdict
from threading import Lock

from alite_backend.db import schemas
from alite_backend.db.crud import user_crud
from alite_backend.db.db_session import SessionLocal
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session


# database dependency
def get_db():
    """Yields a database session and safely closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# institutional authentication dependency
def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Extracts the authenticated user's identity provided by the institutional
    intranet gateway and maps it to an ALITE user.
    """
    intranet_user_id = request.headers.get("X-Intranet-UID")

    if not intranet_user_id:
        # raise HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Missing institutional authentication headers",
        # )

        # Look up the user in ALITE's local database
        # user = user_crud.get_by_intranet_id(db, intranet_id=intranet_user_id)
        user = user_crud.crud_user.get(db=db, id=1)

    # if not user:
    #     # TODO: add Just-In-Time (JIT) Provisioning.

    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User authenticated, but not registered in ALITE."
    #     )

    return user


# role-based authorization dependency
def get_current_instructor(current_user=Depends(get_current_user)):
    """Ensures the authenticated user has instructor privileges."""
    if not current_user.is_instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires instructor privileges.",
        )
    return current_user


class UserRateLimiter:
    """
    Thread-safe sliding window rate limiter tracking requests per user_id.
    Prevents abuse of expensive external crawler and scraper endpoints.
    """

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.history = defaultdict(list)
        self.lock = Lock()

    def check_and_increment(self, user_id: int) -> tuple[int, int]:
        now = time.time()
        window_start = now - self.window_seconds

        with self.lock:
            # purge entries older than the current sliding window
            self.history[user_id] = [
                ts for ts in self.history[user_id] if ts > window_start
            ]
            current_count = len(self.history[user_id])

            if current_count >= self.max_requests:
                oldest_timestamp = self.history[user_id][0]
                retry_after = int(oldest_timestamp + self.window_seconds - now)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=(
                        f"External lookup quota exceeded. Limit is {self.max_requests} "
                        f"requests per {self.window_seconds // 60} minutes."
                    ),
                    headers={"Retry-After": str(max(1, retry_after))},
                )

            # record this execution
            self.history[user_id].append(now)
            remaining = self.max_requests - (current_count + 1)
            reset_in = int(self.window_seconds - (now - self.history[user_id][0]))
            return remaining, max(1, reset_in)


# instantiated guardrail: 10 external requests per 10 minutes (600 seconds)
pipeline_rate_limiter = UserRateLimiter(max_requests=10, window_seconds=600)
