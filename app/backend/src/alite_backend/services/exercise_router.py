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
from alite_backend.services.items.substantives import (
    NounFormToGramStrategy,
    NounGramToFormStrategy,
)

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
        self.STRATEGY_MAP = {
            EnumWordItemType.NOUN_FORM_TO_GRAM: NounFormToGramStrategy,
            EnumWordItemType.NOUN_GRAM_TO_FORM: NounGramToFormStrategy,
        }
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

        return StrategyClass(db_session=self.db, request_context=exercise_context)

    def generate_exercise(
        self, request: schemas.ExerciseRequest
    ) -> schemas.ExerciseResponse:
        exercise_payload = []

        if not request.exercise_context or not request.type_counts:
            raise ValueError("No targets or generation formats provided.")

        for item_strategy, requested_qty in request.type_counts.items():
            if requested_qty <= 0:
                continue
            # instantiate the class
            strategy_runner = self.get_exercise_generator(
                item_strategy, request.exercise_context
            )
            specific_config = None
            if request.grammar_focus.strategies:
                specific_config = request.grammar_focus
            # create blueprints for all items of a strategy
            blueprints = strategy_runner.generate_item_blueprints(
                num_items=requested_qty,
                max_keys=request.exercise_context.max_keys,
                max_distractors=request.exercise_context.max_distractors,
                config=specific_config,
            )
            # assign format and add to item list
            for bp in blueprints:
                exercise_payload.append(
                    {
                        "item_bp": bp,
                        "item_type": item_strategy,
                        "item_format": random.choice(
                            request.exercise_context.ex_formats
                        ),
                        "settings": specific_config,
                    }
                )
        # add to database
        db_exercise = models.Exercise(user_id=self.user_id)
        self.db.add(db_exercise)
        self.db.flush()

        response_items = []

        for idx, pl in enumerate(exercise_payload):
            item_format = pl["item_format"]
            item_prompt = pl["item_bp"]["prompt"]
            item_key = pl["item_bp"]["keys"]
            item_distractors = pl["item_bp"]["distractors"]
            item_settings = (
                pl["settings"].model_dump(mode="json") if pl["settings"] else None
            )
            db_item = models.Item(
                ex_id=db_exercise.id,
                order_in_ex=idx,
                item_type=pl["item_type"],
                item_format=item_format,
                prompt=item_prompt,
                key=item_key,
                distractors=item_distractors,
                settings=item_settings,
            )
            self.db.add(db_item)
            self.db.flush()

            options = item_key + item_distractors
            random.shuffle(options)

            if item_format == models.EnumItemFormat.MCQ:
                response_items.append(
                    schemas.MultipleChoiceResponse(
                        item_id=db_item.id, prompt=item_prompt, options=options
                    )
                )
            elif item_format == models.EnumItemFormat.FLASHCARD:
                response_items.append(
                    schemas.FlashcardResponse(
                        item_id=db_item.id, front_text=item_prompt, back_text=item_key
                    )
                )
            elif item_format == models.EnumItemFormat.CLOZE:
                response_items.append(
                    schemas.WordClozeResponse(
                        item_id=db_item.id,
                        prompt=item_prompt,
                        sentence_parts=options,  # TODO
                        target_lemma=item_key,
                    )
                )
            else:
                continue

        self.db.commit()  # Save transaction securely

        return schemas.ExerciseResponse(
            exercise_id=db_exercise.id,
            num_questions=len(response_items),
            response_data=response_items,
        )

    # Usage in API endpoint:
    # generator = get_exercise_generator(db, request.context, request.type)
    # exercise_data = generator.generate(request.criteria, request.context)
