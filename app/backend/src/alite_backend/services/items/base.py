# app/backend/src/alite_backend/services/items/base.py
from abc import ABC, abstractmethod
import logging
import json
import random
from sqlalchemy.orm import Session
import logging
from typing import List, Optional
from alite_backend.db import schemas, models

logger = logging.getLogger(__name__)


class BaseExerciseStrategy(ABC):

    def __init__(self, db_session: Session, user_context: dict):
        self.db = db_session
        self.context = user_context

    # --- ABSTRACT METHODS ---

    @abstractmethod
    def fetch_keys(self, prompt_criteria: dict, num_keys: int, limit: int):
        """Fetch the database objects that act as the foundation for the correct answer."""
        pass

    @abstractmethod
    def fetch_distractors(self, target, num_distractors: int) -> list[str]:
        """Fetch incorrect text options for a specific target."""
        pass

    @abstractmethod
    def format_prompt(self, target) -> str:
        """Create the actual question text (e.g., 'Select the dative form of...')."""
        pass

    @abstractmethod
    def get_correct_answer_text(self, target) -> str:
        """Extract the correct answer string from the target object."""
        pass

    # --- CONCRETE METHOD ---

    def generate_exercise(
        self,
        user_id: int,
        prompt_criteria: dict,
        question_count: int = 10,
        key_count: int = 1,
        distractor_count: int = 3,
    ):
        """
        Orchestrates question generation, saves them to the database,
        and returns the safe, cheat-proof payload for React.
        """
        # create a new Study Session in the database
        exercise_record = models.Exercise(user_id=user_id)
        self.db.add(exercise_record)
        self.db.flush()

        # get the targets using the child's specific logic
        keys = self.fetch_keys(prompt_criteria=prompt_criteria, num_keys=key_count, limit=question_count)

        safe_frontend_items = []

        for key in keys: # type: ignore
            # generate the specific distractors and prompt
            distractor_texts = self.fetch_distractors(key, num_distractors=distractor_count)
            correct_text = self.get_correct_answer_text(key)
            prompt_text = self.format_prompt(key)

            # combine and shuffle the options
            all_options = distractor_texts + [correct_text]
            random.shuffle(all_options)

            # save the actual question (Item) to the database
            item_record = models.Item(
                item_type=prompt_criteria.get("exercise_type", "multiple_choice"),
                prompt=prompt_text,
                options=all_options,
                key=correct_text, 
                lemma_id=key.lem_id if hasattr(key, "lem_id") else None,
            )
            self.db.add(item_record)
            self.db.flush()

            # build the safe payload
            safe_frontend_items.append(
                {
                    "interaction_type": "multiple_choice",
                    "question_id": item_record.id,
                    "prompt": prompt_text,
                    "options": all_options,
                }
            )

        self.db.commit()

        return {
            "session_id": exercise_record.id,
            "total_questions": len(safe_frontend_items),
            "items": safe_frontend_items,
        }
