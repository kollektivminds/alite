# app/backend/services/exercise_router.py
import logging
import random
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from alite_backend.db import schemas, models
from alite_backend.api import deps
from alite_backend.db.schemas import EnumWordItemType
from .items.base import BaseExerciseStrategy
from .items.substantives import FormLemToGncStrategy

# from .items.nouns import NounCaseStrategy
# from .items.verbs import
# from .items.participles import

logger = logging.getLogger(__name__)


class ExerciseRouter:

    def __init__(
        self,
        db: Session,
        user_id: int,  # from endpoint
        exercise_context: schemas.ExerciseContext,
    ):
        self.db = db
        self.context = exercise_context
        self.user_id = user_id
        self.STRATEGY_MAP = {EnumWordItemType.FORM_LEM_TO_GNC: FormLemToGncStrategy}
        # create exercise record
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)
        self.db.flush()

    def get_exercise_generator(
        self,
        exercise_type: EnumWordItemType,
    ) -> BaseExerciseStrategy:

        StrategyClass = self.STRATEGY_MAP.get(exercise_type)
        if not StrategyClass:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

        return StrategyClass(db_session=self.db, context=self.context)

    def generate_exercise(
        self, exercise_target: schemas.ExerciseRequest
    ) -> schemas.ExerciseResponse:
        collated_items_payload = []

        if not exercise_target.exercise_context or not exercise_target.type_counts:
            raise ValueError("No targets or generation formats provided.")

        for item_type, requested_qty in exercise_target.type_counts.items():
            if requested_qty <= 0:
                continue

            strategy_runner = self.get_exercise_generator(item_type)
            targets = strategy_runner.fetch_keys(
                prompt_criteria=self.context.model_dump(),
                keys_per_item=exercise_target.exercise_context.max_keys,
                num_items=exercise_target.exercise_context.num_items,
            )

            for target in targets:
                prompt_text = strategy_runner.format_prompt(target)
                correct_key = strategy_runner.get_correct_answer_text(target)
                distractors = strategy_runner.fetch_distractors(
                    target,
                    distractors_per_item=exercise_target.exercise_context.max_distractors,
                )

                options = [correct_key] + distractors
                random.shuffle(options)

                chosen_format = strategy_runner.determine_format(
                    exercise_target.output.ex_formats
                )

                # Map attributes directly to columns in models.Item
                db_item = models.Item(
                    exercise_id=self.exercise_record.id,  # Link foreign key explicitly
                    item_type=item_type,
                    prompt=prompt_text,  # Column is named 'prompt'
                    key=correct_key,  # Column is named 'key'
                    distractors=distractors,
                    choices=options,  # Saved to JSON choices field
                    settings={"format": chosen_format.value},
                    difficulty=self.context.difficulty,
                )
                self.db.add(db_item)
                self.db.flush()  # Secure db_item.id

                # Shape frontend response structures
                if chosen_format == models.EnumItemFormat.MCQ:
                    item_payload = schemas.MultipleChoiceResponse(
                        item_id=db_item.id, prompt=prompt_text, options=options
                    )
                elif chosen_format == models.EnumItemFormat.FLASHCARD:
                    item_payload = schemas.FlashcardResponse(
                        item_id=db_item.id,
                        front_text=prompt_text,
                        back_text=correct_key,
                    )
                else:
                    continue

                collated_items_payload.append(item_payload)

        random.shuffle(collated_items_payload)
        self.db.commit()  # Save transaction securely

        return schemas.ExerciseResponse(
            total_questions=len(collated_items_payload),
            response_data=collated_items_payload,
        )

    # Usage in API endpoint:
    # generator = get_exercise_generator(db, request.context, request.type)
    # exercise_data = generator.generate(request.criteria, request.context)
