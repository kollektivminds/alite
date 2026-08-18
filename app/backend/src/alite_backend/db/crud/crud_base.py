import logging
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Define TypeVars for SQLAlchemy Model, Pydantic Create Schema, and Pydantic Update Schema
ModelType = TypeVar("ModelType", bound=Any)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        **Parameters**
        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        # return db.query(self.model).filter(self.model.id == id).first()
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        # return db.query(self.model).offset(skip).limit(limit).all()
        stmt = select(self.model).offset(skip).limit(limit)

        return list(db.scalars(stmt).all())

    def params_search(
        self, db: Session, filter_kwargs: dict[str, Any], find_one: bool = True
    ) -> ModelType | Sequence[ModelType] | None:

        stmt = select(self.model)

        for key, value in filter_kwargs.items():
            # getattr(self.model, 'lem_text') behaves exactly like self.model.lem_text
            stmt = stmt.where(getattr(self.model, key) == value)

        if find_one:
            return db.scalars(stmt).first()
        else:
            return db.scalars(stmt).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        try:
            # Convert Pydantic model to dict and unpack into SQLAlchemy model
            # obj_in_data = obj_in.model_dump()
            # obj_in_data = jsonable_encoder(obj=obj_in)
            if isinstance(obj_in, BaseModel):
                obj_in_data = obj_in.model_dump()
            else:
                obj_in_data = dict(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.flush()
            db.refresh(db_obj)
            return db_obj

        except IntegrityError as e:
            db.rollback()
            logger.exception(f"IntegrityError creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This {self.model.__name__} already exists or violates constraints.",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(f"Database error creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred",
            )

    def get_or_create(
        self,
        db: Session,
        obj_in: CreateSchemaType | Dict[str, Any],
        filter_kwargs: Optional[Dict[str, Any]] = None,
    ) -> ModelType:
        """
        Idempotent fetch-or-insert with PostgreSQL savepoint recovery.
        Guarantees concurrency safety against unique constraint violations.
        """
        # prepare query parameters from filter_kwargs or raw schema data
        if filter_kwargs is None:
            if isinstance(obj_in, dict):
                filter_kwargs = obj_in
            else:
                filter_kwargs = obj_in.model_dump(exclude_unset=True)

        # attempt clean lookup first
        stmt = select(self.model).filter_by(**filter_kwargs)
        existing = db.scalars(stmt).first()
        if existing:
            return existing

        # handle insert within a nested savepoint
        db_obj_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump()
        db_obj = self.model(**db_obj_data)

        try:
            # begin_nested creates a SAVEPOINT in PostgreSQL
            with db.begin_nested():
                db.add(db_obj)
                db.flush()
            return db_obj
        except IntegrityError:
            # savepoint automatically rolled back on exception; query existing row
            existing_after_collision = db.scalars(stmt).first()
            if existing_after_collision:
                return existing_after_collision

            # fallback: if collision occurred on a primary unique constraint not in filter_kwargs
            raise

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        try:
            # check that type is dict
            if isinstance(obj_in, BaseModel):
                obj_in_data = db_obj.model_dump()
            else:
                obj_in_data = dict(db_obj)

            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            for field in obj_in_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])

            # save changes
            db.add(db_obj)
            db.flush()
            db.refresh(db_obj)
            return db_obj

        except IntegrityError as e:
            db.rollback()
            logger.exception(f"IntegrityError updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Update violates database constraints (e.g., duplicate name).",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(f"Database error updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred during update.",
            )

    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        Deletes a record from the database by its ID.
        """
        try:
            # 1. Fetch the object
            # obj = db.query(self.model).filter(self.model.id == id).first()
            obj = db.get(self.model, id)

            # 2. If it doesn't exist, raise a clean 404 error
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found.",
                )

            # 3. Delete and flush
            db.delete(obj)
            db.flush()
            return obj

        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(f"Database error deleting {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred during deletion.",
            )
