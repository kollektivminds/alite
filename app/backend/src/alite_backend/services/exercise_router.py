# app/backend/services/exercise_router.py
import logging
import random
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from alite_backend.db import schemas, models
from alite_backend.api import deps
from alite_backend.db.schemas import EnumWordItemType
from alite_backend.services.items.base import BaseExerciseStrategy

# from alite_backend.services.items.lemmas import
from alite_backend.services.items.substantives import NounFormToGramStrategy

# from alite_backend.services.items.lemmas import

# from .items.verbs import
# from .items.participles import

logger = logging.getLogger(__name__)


class ExerciseRouter:
    """_summary_"""

    def __init__(
        self,
        db: Session,
        user_id: int,  # from endpoint
        # exercise_request: schemas.ExerciseRequest,
    ):
        self.db = db
        # self.exercise_request = exercise_request
        # self.context = exercise_request.exercise_context
        self.user_id = user_id
        self.STRATEGY_MAP = {EnumWordItemType.NOUN_FORM_TO_GRAM: NounFormToGramStrategy}
        # create exercise record
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)
        self.db.flush()

    def get_exercise_generator(
        self, exercise_type: EnumWordItemType, exercise_context: schemas.ExerciseContext
    ) -> BaseExerciseStrategy:

        StrategyClass = self.STRATEGY_MAP.get(exercise_type)
        if not StrategyClass:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

        return StrategyClass(
            db_session=self.db, request_context=exercise_context
        )

    def generate_exercise(
        self, request: schemas.ExerciseRequest
    ) -> schemas.ExerciseResponse:
        collated_items_payload = []

        if not request.exercise_context or not request.type_counts:
            raise ValueError("No targets or generation formats provided.")

        for item_strategy, requested_qty in request.type_counts.items():
            if requested_qty <= 0:
                continue

            strategy_runner = self.get_exercise_generator(item_strategy, request.exercise_context)
            specific_config = None
            if request.grammar_focus and hasattr(request.grammar_focus, item_strategy.value):
                specific_config = getattr(request.grammar_focus, item_strategy.value)
                
            blueprints = strategy_runner.generate_item_blueprints(
                num_items=requested_qty,
                max_keys=request.exercise_context.max_keys,
                max_distractors=request.exercise_context.max_distractors,
                config=specific_config
            )
            # # Shape frontend response structures
            # if chosen_format == models.EnumItemFormat.MCQ:
            #     item_payload = schemas.MultipleChoiceResponse(
            #         item_id=db_item.id, prompt=prompt_text, options=options
            #     )
            # elif chosen_format == models.EnumItemFormat.FLASHCARD:
            #     item_payload = schemas.FlashcardResponse(
            #         item_id=db_item.id,
            #         front_text=prompt_text,
            #         back_text=correct_key,
            #     )
            # else:
            #     continue

            # collated_items_payload.append(item_payload)

        random.shuffle(collated_items_payload)
        self.db.commit()  # Save transaction securely

        return schemas.ExerciseResponse(
            # total_questions=len(collated_items_payload),
            response_data=collated_items_payload,
        )

    # Usage in API endpoint:
    # generator = get_exercise_generator(db, request.context, request.type)
    # exercise_data = generator.generate(request.criteria, request.context)
