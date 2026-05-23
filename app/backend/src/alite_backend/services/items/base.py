# app/backend/src/alite_backend/services/items/base.py
from abc import ABC, abstractmethod
import logging
import json
import random
from sqlalchemy import select
from sqlalchemy.orm import Session, declarative_base
import logging
from typing import List, Any, Dict
from alite_backend.db import schemas, models

logger = logging.getLogger(__name__)


class BaseExerciseStrategy(ABC):

    def __init__(self, db_session: Session, context: schemas.ExerciseContext):
        self.db = db_session
        self.context_dict = context.model_dump()
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
        elif self.mod_ids:
            stmt = (
                stmt.join(models.LemmaInLessonList)
                .join(models.LessonList)
                .where(models.LessonList.in_module.in_(self.mod_ids))
            )

        return stmt

    # --- ABSTRACT METHODS ---

    @abstractmethod
    def generate_item_blueprints(
        self, limit: int, max_distractors: int
    ) -> List[schemas.ItemBlueprint]:
        """
        Must return a list of dictionaries:
        [{"prompt": "...", "key": "...", "distractors": [...]}]
        """
        pass

    # @abstractmethod
    # def fetch_keys(self, prompt_criteria, keys_per_item: int, num_items: int) -> Any:
    #     """Fetch the database objects that act as the foundation for the correct answer."""
    #     pass

    # @abstractmethod
    # def fetch_distractors(self, target, distractors_per_item: int) -> Any:
    #     """Fetch incorrect text options for a specific target."""
    #     pass

    # @abstractmethod
    # def format_prompt(self, target) -> str:
    #     """Create the actual question text (e.g., 'Select the dative form of...')."""
    #     pass

    # @abstractmethod
    # def get_correct_answer_text(self, target) -> str:
    #     """Extract the correct answer string from the target object."""
    #     pass

    # --- CONCRETE METHOD ---

    # def generate_exercise(self, prompt_criteria: schemas.ExerciseRequest):
    #     """
    #     Orchestrates question generation, saves them to the database,
    #     and returns the safe, cheat-proof payload for React.
    #     """
    #     # create a new Study Session in the database
    #     exercise_record = models.Exercise(user_id=self.context.user_id)
    #     self.db.add(exercise_record)
    #     self.db.flush()

    #     # get the targets using the child's specific logic
    #     keys = self.fetch_keys(
    #         prompt_criteria=prompt_criteria.output,
    #         keys_per_item=prompt_criteria.max_keys,
    #         num_items=prompt_criteria.num_items,
    #     )

    #     safe_frontend_items = []

    #     for key in keys:  # type: ignore
    #         # generate the specific distractors and prompt
    #         distractor_texts = self.fetch_distractors(
    #             key, distractors_per_item=distractor_count
    #         )
    #         correct_text = self.get_correct_answer_text(key)
    #         prompt_text = self.format_prompt(key)

    #         # combine and shuffle the options
    #         all_options = distractor_texts + [correct_text]
    #         random.shuffle(all_options)

    #         # save the actual question (Item) to the database
    #         item_record = models.Item(
    #             item_type=prompt_criteria.get("exercise_type", "multiple_choice"),
    #             prompt=prompt_text,
    #             options=all_options,
    #             key=correct_text,
    #             lemma_id=key.lem_id if hasattr(key, "lem_id") else None,
    #         )
    #         self.db.add(item_record)
    #         self.db.flush()

    #         # build the safe payload
    #         safe_frontend_items.append(
    #             {
    #                 "interaction_type": "multiple_choice",
    #                 "question_id": item_record.id,
    #                 "prompt": prompt_text,
    #                 "options": all_options,
    #             }
    #         )

    #     self.db.commit()

    #     return {
    #         "session_id": exercise_record.id,
    #         "total_questions": len(safe_frontend_items),
    #         "items": safe_frontend_items,
    #     }
