# app/backend/src/alite_backend/services/items/nouns.py
from alite_backend.services.items.base import BaseExerciseStrategy

class NounCaseStrategy(BaseExerciseStrategy):
    
    def fetch_keys(self, prompt_criteria, prompt_context) -> dict:
        # Query: WordForms where Pos=Noun, Case IN (Inst, Dat), Lesson IN (10-15)
        keys_dict = {}
        
        db = 
        query = db.
        return keys_dict
        
    def fetch_distractors(self, keys, prompt_criteria, prompt_context):
        # The Distractor Logic:
        # For the specific Lemmas in our keys, fetch WordForms where 
        # Case is NOT IN (Inst, Dat). 
        # Example: Prompt asks for "книгой" (Inst). Distractor should be "книгу" (Acc).
        distractors_dict = {}
        
        return distractors_dict