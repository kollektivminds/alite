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

    # --- ABSTRACT METHODS (Children MUST implement these) ---

    @abstractmethod
    def fetch_targets(self, prompt_criteria: dict, limit: int):
        """Fetch the database objects that act as the foundation for the correct answer."""
        pass

    @abstractmethod
    def fetch_distractors(self, target, limit: int) -> list[str]:
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

    # --- CONCRETE METHOD (The Orchestrator) ---

    def generate_exercise(
        self,
        user_id: int,
        prompt_criteria: dict,
        question_count: int = 10,
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
        targets = self.fetch_targets(prompt_criteria, limit=question_count)

        safe_frontend_items = []

        for target in targets:
            # generate the specific distractors and prompt
            distractor_texts = self.fetch_distractors(target, limit=distractor_count)
            correct_text = self.get_correct_answer_text(target)
            prompt_text = self.format_prompt(target)

            # combine and shuffle the options
            all_options = distractor_texts + [correct_text]
            random.shuffle(all_options)

            # save the actual question (Item) to the database
            item_record = models.Item(
                item_type=prompt_criteria.get("exercise_type", "multiple_choice"),
                prompt=prompt_text,
                options=all_options,  # Stored as JSON
                key=correct_text, 
                lemma_id=target.lem_id if hasattr(target, "lem_id") else None,
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
            "session_id": session_record.id,
            "total_questions": len(safe_frontend_items),
            "items": safe_frontend_items,
        }
