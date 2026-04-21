from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException, status
from pydantic import BaseModel
import logging

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
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        try:
            # Convert Pydantic model to dict and unpack into SQLAlchemy model
            obj_in_data = obj_in.model_dump()
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
        self, db: Session, obj_in: CreateSchemaType, filter_kwargs: Dict[str, Any]
    ) -> ModelType:
        """
        Tries to fetch the object based on filter_kwargs.
        If it doesn't exist, it creates it using obj_in.
        """
        existing_obj = db.query(self.model).filter_by(**filter_kwargs).first()

        if existing_obj:
            return existing_obj

        return self.create(db=db, obj_in=obj_in)

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        try:
            # check that type is dict
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.model_dump(exclude_unset=True)

            # iterate and update as relevant
            for field, value in update_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

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

    def remove(self, db: Session, *, id: Any) -> ModelType:
        """
        Deletes a record from the database by its ID.
        """
        try:
            # 1. Fetch the object
            obj = db.query(self.model).filter(self.model.id == id).first()

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
