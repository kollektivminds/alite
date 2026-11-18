# generate class for users
import logging

from pydantic import EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.db.crud.crud_base import CRUDBase
from alite_backend.db.models import User, UserGroup, UserInGroup
from alite_backend.db.schemas import (
    UserCreate,
    UserGroupCreate,
    UserGroupUpdate,
    UserInGroupCreate,
    UserInGroupUpdate,
    UserUpdate,
)
from alite_backend.services.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)

#
# USERS
#


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """
        Intercepts creation payload, hashes the raw password, and saves the User instance.
        """
        # 1. Convert Pydantic payload to dictionary
        db_obj_data = obj_in.model_dump(exclude={"password"})

        # 2. Hash the raw password and assign to hashed_password column
        db_obj_data["hashed_password"] = get_password_hash(obj_in.password)

        # 3. Instantiate model and commit
        db_obj = User(**db_obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(
        self, db: Session, *, username_or_email: str, password: str
    ) -> User | None:
        """
        Retrieves user by username/email and verifies password match.
        """
        user = self.get_by_username(
            db, username_input=username_or_email
        ) or self.get_by_email(db, email_input=username_or_email)

        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None

        return user

    def get_by_email(self, db: Session, email_input: EmailStr) -> User | None:

        stmt = select(User).where(User.email == email_input)  # type: ignore

        with db as session:
            return session.scalars(stmt).first()

    def get_by_username(self, db: Session, username_input: str) -> User | None:

        stmt = select(User).where(User.username == username_input)  # type: ignore

        with db as session:
            return session.scalars(stmt).first()


crud_user = CRUDUser(User)

#
# USER GROUPS
#


class CRUDUserGroup(CRUDBase[UserGroup, UserGroupCreate, UserGroupUpdate]):
    pass


crud_user_group = CRUDUserGroup(UserGroup)

#
# USER_IN_GROUP
#


class CRUDUserInGroup(CRUDBase[UserInGroup, UserInGroupCreate, UserInGroupUpdate]):
    pass


crud_user_in_group = CRUDUserInGroup(UserInGroup)
