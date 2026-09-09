from alite_backend.db import schemas
from alite_backend.db.crud import user_crud
from alite_backend.db.db_session import SessionLocal
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session


# 1. Database Dependency
def get_db():
    """Yields a database session and safely closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 2. Institutional Authentication Dependency
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


# 3. Role-Based Authorization Dependency
def get_current_instructor(current_user=Depends(get_current_user)):
    """Ensures the authenticated user has instructor privileges."""
    if not current_user.is_instructor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint requires instructor privileges.",
        )
    return current_user
