# alite_backend/db/crud/crud_base.py
import logging
from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar, Union

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Any)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        Args:
            model: A SQLAlchemy model class
        """
        self.model = model

    def _extract_model_data(
        self,
        obj_in: Union[CreateSchemaType, UpdateSchemaType, Dict[str, Any]],
        exclude_unset: bool = False,
    ) -> Dict[str, Any]:
        """
        Extracts a plain dictionary from a Pydantic schema or mapping, filtering
        out keys that do not correspond to mapped SQLAlchemy model columns.
        """
        if isinstance(obj_in, BaseModel):
            raw_data = obj_in.model_dump(exclude_unset=exclude_unset)
        elif isinstance(obj_in, dict):
            raw_data = obj_in.copy()
        else:
            raise ValueError(f"Expected BaseModel or dict, received {type(obj_in)}")

        valid_columns = set(self.model.__mapper__.column_attrs.keys())
        return {k: v for k, v in raw_data.items() if k in valid_columns}

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Fetch multiple records with offset pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def params_search(
        self, db: Session, filter_kwargs: dict[str, Any], find_one: bool = True
    ) -> Union[ModelType, Sequence[ModelType], None]:
        """Search entities based on key-value equality filters."""
        stmt = select(self.model)
        for key, value in filter_kwargs.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)

        if find_one:
            return db.scalars(stmt).first()
        return db.scalars(stmt).all()

    def get_or_create(
        self,
        db: Session,
        *,
        obj_in: Union[CreateSchemaType, Dict[str, Any]],
        filter_kwargs: Optional[Dict[str, Any]] = None,
    ) -> ModelType:
        """
        Fetches an existing entity matching filter_kwargs or creates a new one idempotently.

        Engineering Safeguards:
        1. Whitelists search criteria against self.model column attributes to prevent
           AttributeError when schemas contain transient metadata (e.g. temp_form_id).
        2. Supports explicit filter dictionaries or falls back to extracted obj_in data.
        3. Isolates creation inside a transaction SAVEPOINT (db.begin_nested()). If a
           unique constraint collision occurs during flush, only the sub-transaction
           rolls back, preventing PostgreSQL from aborting the entire ETL session.
        """
        # 1. Resolve search criteria
        if filter_kwargs is not None:
            raw_filters = filter_kwargs
        elif isinstance(obj_in, BaseModel):
            raw_filters = obj_in.model_dump(exclude_unset=True)
        elif isinstance(obj_in, dict):
            raw_filters = obj_in
        else:
            raise ValueError(
                f"Expected BaseModel or dict for obj_in, received {type(obj_in)}"
            )

        # Intersect filter keys with mapped columns to discard transient payload fields
        valid_columns = set(self.model.__mapper__.column_attrs.keys())
        search_filters = {k: v for k, v in raw_filters.items() if k in valid_columns}

        # 2. Check if the entity already exists
        stmt = select(self.model)
        for key, value in search_filters.items():
            column = getattr(self.model, key)
            stmt = stmt.where(column == value)

        existing_obj = db.scalars(stmt).first()
        if existing_obj is not None:
            return existing_obj

        # 3. Create the entity within an isolated SAVEPOINT
        try:
            with db.begin_nested():
                create_data = self._extract_model_data(obj_in, exclude_unset=False)
                db_obj = self.model(**create_data)
                db.add(db_obj)
                db.flush()
                db.refresh(db_obj)
                return db_obj
        except IntegrityError:
            # Re-query the conflicting row that caused the unique violation
            existing_obj = db.scalars(stmt).first()
            if existing_obj is not None:
                return existing_obj
            raise
        except SQLAlchemyError as e:
            logger.exception(
                f"Database error during get_or_create for {self.model.__name__}: {str(e)}"
            )
            raise

    def create(
        self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Creates an ORM instance safely. Filters out extra schema keys and relies
        on SQL transaction boundaries with clean error translation.
        """
        try:
            create_data = self._extract_model_data(obj_in, exclude_unset=False)
            db_obj = self.model(**create_data)
            db.add(db_obj)
            db.flush()
            db.refresh(db_obj)
            return db_obj

        except IntegrityError as e:
            db.rollback()
            logger.exception(f"IntegrityError creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Record creation violates database constraints for {self.model.__name__}.",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(f"Database error creating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred during persistence.",
            )

    def create_multi(
        self, db: Session, *, objs_in: Sequence[Union[CreateSchemaType, Dict[str, Any]]]
    ) -> List[ModelType]:
        """
        Bulk creates records in an atomic unit of work. Essential for ingesting
        sentence token sequences (sentence_tokens) to avoid N database flushes.
        """
        try:
            db_objs = [
                self.model(**self._extract_model_data(obj, exclude_unset=False))
                for obj in objs_in
            ]
            db.add_all(db_objs)
            db.flush()
            for obj in db_objs:
                db.refresh(obj)
            return db_objs

        except IntegrityError as e:
            db.rollback()
            logger.exception(
                f"IntegrityError in bulk create for {self.model.__name__}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bulk creation violates database constraints for {self.model.__name__}.",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(
                f"Database error in bulk create for {self.model.__name__}: {str(e)}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred during bulk persistence.",
            )

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """
        Updates an existing ORM entity from a schema or dictionary without invoking
        Pydantic methods on SQLAlchemy instances.
        """
        try:
            update_data = self._extract_model_data(obj_in, exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            db.add(db_obj)
            db.flush()
            db.refresh(db_obj)
            return db_obj

        except IntegrityError as e:
            db.rollback()
            logger.exception(f"IntegrityError updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update violates database constraints (e.g. duplicate unique key).",
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.exception(f"Database error updating {self.model.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected database error occurred during update.",
            )

    def remove(self, db: Session, *, id: int) -> ModelType:
        """Removes a record by ID and issues a 404 if not found."""
        try:
            obj = db.get(self.model, id)
            if not obj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"{self.model.__name__} not found.",
                )
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
