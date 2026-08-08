# alite_backend/scripts/create_admin.py

import sys
import getpass
import logging
from sqlalchemy.orm import Session
from alite_backend.db.db_session import SessionLocal
from alite_backend.db.crud import user_crud
from alite_backend.db.models import EnumUserRole
from alite_backend.db.schemas import UserCreate

# Configure terminal logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_account(db: Session) -> None:
    """
    Interactive CLI utility for provisioning administrative user accounts.
    Executes within the application context, enforcing password hashing and validation.
    """
    print("\n--- ALITE Administrative Account Provisioning ---\n")

    # prompt for user details interactively
    username = input("Enter username: ").strip()
    email = input("Enter email address: ").strip()

    # getpass prevents echo masking of plain-text passwords in terminal
    password = getpass.getpass("Enter password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    # input validation
    if password != password_confirm:
        logger.error("Passwords do not match. Aborting operation.")
        sys.exit(1)

    if len(password) < 8:
        logger.error("Password must be at least 8 characters long.")
        sys.exit(1)

    # check for existing username or email collisions
    existing_user = user_crud.crud_user.get_by_email(db=db, email_input=email)
    if existing_user:
        logger.error("User with email '%s' already exists.", email)
        sys.exit(1)

    # construct creation schema and persist to database
    try:
        user_in = UserCreate(
            username=username,
            email=email,
            password=password,
            user_role=EnumUserRole.ADMIN,
            alias="admin",
        )
        new_admin = user_crud.crud_user.create(db=db, obj_in=user_in)
        logger.info(
            "Successfully created administrative user: %s (ID: %s)",
            new_admin.username,
            new_admin.id,
        )
    except Exception as e:
        logger.exception("Failed to create admin user: %s", str(e))
        db.rollback()
        sys.exit(1)


def main() -> None:
    """Session lifecycle wrapper for the CLI script."""
    db = SessionLocal()
    try:
        create_admin_account(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
