import logging
from typing import Optional
from starlette.requests import Request
from starlette.responses import RedirectResponse
from sqladmin.authentication import AuthenticationBackend
from alite_backend.config import settings
from alite_backend.db.crud import user_crud
from alite_backend.db.db_session import SessionLocal

logger = logging.getLogger(__name__)


class AdminAuthBackend(AuthenticationBackend):
    """
    Session-based authentication backend for the SQLAdmin interface.

    Inherits from SQLAdmin's AuthenticationBackend to enforce administrative
    access boundaries on all /admin endpoints independent of API JWT tokens.
    """

    async def login(self, request: Request) -> bool:
        """
        Validates administrator credentials from the HTML form payload.

        Args:
            request: Incoming HTTP request containing form data.

        Returns:
            bool: True if authentication succeeds and session cookie is set; False otherwise.
        """
        form = await request.form()
        username: Optional[str] = form.get("username")  # type: ignore
        password: Optional[str] = form.get("password")  # type: ignore

        if not username or not password:
            logger.warning("Admin login attempt failed: Missing username or password.")
            return False

        # open an isolated session to query the user record
        db = SessionLocal()
        try:
            # query user using existing CRUD layer
            user = user_crud.crud_user.get_by_username(db=db, username_input=username)

            # enforce role-based access control (RBAC): User must exist and hold INSTRUCTOR/ADMIN role
            if not user or not user_crud.verify_password(
                password, user.hashed_password
            ):
                logger.warning(
                    "Admin login failed for user: %s (Invalid credentials)", username
                )
                return False

            if user.user_role != "admin":  # Restrict panel to faculty/instructors
                logger.warning(
                    "Unauthorized admin access attempt by user: %s", username
                )
                return False

            # mutate session state to store authenticated user identity
            request.session.update(
                {
                    "admin_user_id": user.id,
                    "admin_username": user.username,
                }
            )
            logger.info("Admin session established for user: %s", username)
            return True
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        """
        Destroys the administrative session cookie upon logout.
        """
        logger.info("Admin user logged out.")
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        """
        Middleware verification executed on every request targeting /admin.

        Args:
            request: Incoming HTTP request containing session metadata.

        Returns:
            bool: True if the request carries a valid session key; False to trigger login redirect.
        """
        admin_user_id = request.session.get("admin_user_id")
        if not admin_user_id:
            return False

        # Optional: Add token freshness / session expiration checks here
        return True


# Instantiate backend with secret key derived from configuration settings
admin_auth = AdminAuthBackend(secret_key=settings.SECRET_KEY)
