# app/backend/src/alite_backend/services/items/base.py
from abc import ABC, abstractmethod
import logging
import json
import random
from sqlalchemy import select
from sqlalchemy.orm import Session, declarative_base
import logging
from typing import List, Any, Dict
from enum import Enum
from alite_backend.db import schemas, models

logger = logging.getLogger(__name__)


class BaseExerciseStrategy(ABC):
    """Base class for creating exercises"""

    def __init__(self, db_session: Session, request_context: schemas.ExerciseContext):
        self.db = db_session
        # self.type_counts = request.type_counts
        self.context_dict = request_context.model_dump()
        self.less_list_ids = self.context_dict.get("less_list_ids", [])
        self.mod_ids = self.context_dict.get("mod_ids", [])
        self.lem_ids = self.context_dict.get("lem_ids", [])
        self.formats = self.context_dict.get("ex_formats", [])
        self.num_items = self.context_dict.get("num_items", 10)
        self.max_keys = self.context_dict.get("max_keys", 1)
        self.max_distractors = self.context_dict.get("max_distractors", 3)

    # --- HELPER METHODS ---

    def get_scoped_stmt(self):

        stmt = select(models.Lemma)

        if self.less_list_ids:
            stmt = stmt.join(models.LemmaInLessonList).where(
                models.LemmaInLessonList.less_list_id.in_(self.less_list_ids)
            )

        if self.mod_ids:
            stmt = (
                stmt.join(models.LemmaInLessonList)
                .join(
                    models.LessonListInModule,
                    models.LessonListInModule.less_list_id
                    == models.LemmaInLessonList.less_list_id,
                )
                .where(models.LessonListInModule.mod_id.in_(self.mod_ids))
            )

        if self.lem_ids:
            stmt = stmt.where(models.Lemma.id.in_(self.lem_ids))

        return stmt

    def get_enum_distractors(self, correct_enum: Enum, num_distractors: int):
        """To get distractors with an enum class"""
        all_options = [
            e.value for e in correct_enum.__class__ if e != correct_enum.value
        ]
        return random.sample(all_options, min(num_distractors, len(all_options)))

    # --- ABSTRACT METHOD ---

    @abstractmethod
    def generate_item_blueprints(
        self, num_items: int, max_keys: int, max_distractors: int
    ) -> List[schemas.ItemBlueprint]:
        """generate_item_blueprints _summary_

        Args:
            limit (int): _description_
            max_distractors (int): _description_

        Returns:
            List[schemas.ItemBlueprint]: _description_
        """
        pass
