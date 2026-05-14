# app/backend/src/alite_backend/services/item_strategies/base.py
from abc import ABC, abstractmethod

class BaseExerciseStrategy(ABC):
    
    def __init__(self, db_session, user_context):
        self.db = db_session
        self.context = user_context # Contains lesson limits, user limits, etc.

    @abstractmethod
    def fetch_keys(self, prompt_criteria) -> dict:
        """Logic to fetch the correct answers based on the user's prompt."""
        pass

    @abstractmethod
    def fetch_distractors(self, keys) -> dict:
        """Logic to fetch the specific distractors for these keys."""
        pass

    def generate(self, prompt_criteria):
        """The main method that runs the strategy."""
        keys = self.fetch_keys(prompt_criteria)
        distractors = self.fetch_distractors(keys)
        return self._format_response(keys, distractors)