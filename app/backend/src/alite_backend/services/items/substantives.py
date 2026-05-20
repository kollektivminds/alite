# app/backend/src/alite_backend/services/items/substantives.py
from alite_backend.services.items.base import BaseExerciseStrategy
from alite_backend.db import models, schemas

class FormLemToGncStrategy(BaseExerciseStrategy):
    
    def fetch_keys(self, prompt_criteria: schemas.Item_FormLemToGnc, keys_per_item: int, num_items: int):
        return (
            self.db.query(models.GramProp)
        )