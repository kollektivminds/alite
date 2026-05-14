from alite_backend.services.item_strategies.base import BaseExerciseStrategy

class NounCaseStrategy(BaseExerciseStrategy):
    
    def fetch_keys(self, prompt_criteria) -> dict:
        # Query: WordForms where Pos=Noun, Case IN (Inst, Dat), Lesson IN (10-15)
        keys_dict = {}
        return keys_dict
        
    def fetch_distractors(self, keys):
        # The Distractor Logic:
        # For the specific Lemmas in our keys, fetch WordForms where 
        # Case is NOT IN (Inst, Dat). 
        # Example: Prompt asks for "книгой" (Inst). Distractor should be "книгу" (Acc).
        distractors_dict = {}
        
        return distractors_dict