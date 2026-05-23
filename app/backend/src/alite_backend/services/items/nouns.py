# app/backend/src/alite_backend/services/items/nouns.py
from typing import List
from alite_backend.db import models, schemas
from alite_backend.services.items.base import BaseExerciseStrategy

# NOUN TO GENDER


# GENDER TO NOUN


# NOUN TO ANIMACY


# ANIMACY TO NOUN


# FORM + LEMMA TO GENDER/NUMBER/CASE


class FormLemToGncStrategy(BaseExerciseStrategy):

    gender_col = "conj_gender"
    number_col = "gram_num"
    case_col = "subst_case"

    def generate_item_blueprints(
        self, limit: int, max_distractors: int
    ) -> List[schemas.ItemBlueprint]:
        """
        Must return a list of dictionaries:
        [{"prompt": "...", "key": "...", "distractors": [...]}]
        """
        pass


# LEMMA + GNC TO FORM
