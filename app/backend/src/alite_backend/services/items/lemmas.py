# app/backend/src/alite_backend/services/items/lemmas.py
from typing import List, Dict
from alite_backend.services.items.base import BaseExerciseStrategy
from alite_backend.db import models, schemas

# LEMMA TO POS


# POS TO LEMMA


# LEMMA TO DEFINITION


class LemmaToDefinitionStrategy(BaseExerciseStrategy):

    def generate_item_blueprints(
        self, num_items: int, max_keys: int, max_distractors: int
    ) -> List[schemas.ItemBlueprint]:
        blueprints = []

        # 1. Fetch lemmas and their definitions in one go
        stmt = (
            self.get_scoped_stmt()
            .add_columns(models.Definition)
            .join(
                models.LemmaDefinition, models.LemmaDefinition.lem_id == models.Lemma.id
            )
            .join(
                models.Definition, models.LemmaDefinition.def_id == models.Definition.id
            )
            .limit(num_items)
        )
        results = self.db.execute(stmt).all()

        # 2. Build the package
        for lemma, definition in results:
            distractors = self._get_random_definitions(
                max_distractors, exclude_id=definition.id
            )

            blueprints.append(
                {
                    "prompt": f"What is the definition of '{lemma.lem_text}'?",
                    "key": definition.def_text,
                    "distractors": distractors,
                }
            )

        return blueprints

    def _get_random_definitions(self, limit: int, exclude_id: int):
        """A private helper method, living ONLY in this child class!"""
        # Logic to pull random distractors...
        pass


# DEFINITION TO LEMMA


# LEMMA TO PRONUNCIATION


# PRONUNCIATION TO LEMMA


# LEMMA + LEMMA TO RELATION


# RELATION TO LEMMA + LEMMA
