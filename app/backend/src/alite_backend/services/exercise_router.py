# app/backend/services/exercise_router.py
import logging
import random
import uuid
from typing import Any, Dict, Tuple

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.schemas import EnumSentItemType, EnumWordItemType
from alite_backend.services.items.base import BaseExerciseStrategy
from alite_backend.services.items.subclasses import (
    LemmaRelationStrategy,
    MorphologicalStrategy,
    SiblingAttributeStrategy,
    StandaloneAttributeStrategy,
)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

EXERCISE_CONFIG = {
    # zero-query types
    EnumWordItemType.LEM_TO_POS: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.POS_TO_LEM: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_GEND: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.GEND_TO_NOUN: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_ANIM: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ANIM_TO_NOUN: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_ASPT: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ASPT_TO_VERB: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TYPE: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TYPE_TO_VERB: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TNRF: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TNRF_TO_VERB: {
        "strategy_class": StandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sibling-query types
    EnumWordItemType.LEM_TO_DEF: {
        "strategy_class": SiblingAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_model": models.Definition,
            "target_column": "def_text",
            "junction_model": models.LemmaDefinition,
            "junction_column": "def_id",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.DEF_TO_LEM: {
        "strategy_class": SiblingAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_model": models.Definition,
            "target_column": "def_text",
            "junction_model": models.LemmaDefinition,
            "junction_column": "def_id",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.LEM_TO_PRON: {
        "strategy_class": SiblingAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_model": models.Pronunciation,
            "target_column": "pron_text",
            "junction_model": models.LemmaPronunciation,
            "junction_column": "pron_id",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.PRON_TO_LEM: {
        "strategy_class": SiblingAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_model": models.Pronunciation,
            "target_column": "pron_text",
            "junction_model": models.LemmaPronunciation,
            "junction_column": "pron_id",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    # morphology types
    EnumWordItemType.NOUN_FORM_TO_GRAM: {
        "strategy_class": MorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_GRAM_TO_FORM: {
        "strategy_class": MorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.ADJV_FORM_TO_GRAM: {
        "strategy_class": MorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ADJV_GRAM_TO_FORM: {
        "strategy_class": MorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    # lemma-relation types
    EnumWordItemType.VERB_PAIR_TO_REL: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_rel": models.EnumRelLemTypeGroup.ASPECTUAL_PAIR,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_ASPT_PAIR: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_rel": models.EnumRelLemTypeGroup.ASPECTUAL_PAIR,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.LEM_LEM_TO_REL: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.REL_TO_LEM_LEM: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
}


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
        # create exercise record
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)
        self.db.flush()

    def get_exercise_generator(
        self, exercise_type: EnumWordItemType | models.EnumSentItemType
    ) -> Tuple[
        StandaloneAttributeStrategy
        | SiblingAttributeStrategy
        | MorphologicalStrategy
        | LemmaRelationStrategy,
        Dict[str, Any],
    ]:

        StrategyClass = EXERCISE_CONFIG.get(exercise_type)
        if not StrategyClass:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

        return StrategyClass["strategy_class"], StrategyClass["kwargs"]

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
            strategy_class, strategy_kwargs = self.get_exercise_generator(item_strategy)
            strategy_instance = strategy_class(
                db_session=self.db,
                request_context=request.exercise_context,
                **strategy_kwargs,
            )  # type: ignore
            # specific_config = None
            specific_config = (
                request.grammar_focus.strategies if request.grammar_focus else None  # type: ignore
            )
            # create blueprints for all items of a strategy
            blueprints = strategy_instance.generate_item_blueprints(
                num_items=requested_qty,
                max_keys=request.exercise_context.max_keys,
                max_distractors=request.exercise_context.max_distractors,
                config=specific_config,
            )
            # assign format and add to item list
            for bp in blueprints:
                requested_formats = request.exercise_context.ex_formats
                supported_strategy_formats = schemas.STRATEGY_FORMATS.get(item_strategy)
                if supported_strategy_formats:
                    viable_formats = list(
                        supported_strategy_formats & set(requested_formats)
                    )
                    if not viable_formats:
                        logger.warning(
                            "Strategy '%s' cannot be scheduled: requested formats %s have zero "
                            "overlap with supported formats %s. Skipping %d blueprint(s).",
                            item_strategy,
                            requested_formats,
                            supported_strategy_formats,
                            len(blueprints),
                        )
                        continue
                    elif len(viable_formats) > 0:
                        chosen_format = random.choice(viable_formats)
                        exercise_payload.append(
                            {
                                "item_bp": bp,
                                "item_type": item_strategy,
                                "item_format": chosen_format,
                                "settings": specific_config,
                            }
                        )
                    else:
                        continue
                else:
                    continue

        response_items = []

        for idx, pl in enumerate(exercise_payload):
            item_format = pl["item_format"]
            item_prompt = pl["item_bp"].prompt
            item_key = pl["item_bp"].keys
            item_distractors = pl["item_bp"].distractors
            item_settings = (
                pl["settings"].model_dump(mode="json") if pl["settings"] else None
            )
            db_item = models.Item(
                ex_id=self.exercise_in.id,
                order_in_ex=idx,
                item_type=pl["item_type"],
                item_format=item_format,
                prompt=item_prompt,
                settings=item_settings,
                start_time=None,
                finish_time=None,
            )

            if db_item:
                self.db.add(db_item)
                self.db.flush()

                for opt in item_key + item_distractors:
                    db_option = models.ItemOption(
                        option_text=opt,
                        item_id=db_item.id,
                        option_uuid=uuid.uuid4(),
                        is_correct=True if opt in item_key else False,
                        # explanation=None,
                    )

                    self.db.add(db_option)
                    self.db.flush()

                db_lem_in_item = models.LemmaInItem(
                    item_id=db_item.id, lem_id=pl["item_bp"].lem_id
                )
                self.db.add(db_lem_in_item)
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
                            item_id=db_item.id,
                            prompt=item_prompt,
                            back_text=item_key[0],
                        )
                    )
                elif item_format == models.EnumItemFormat.FITB:
                    response_items.append(
                        schemas.FillInTheBlankResponse(
                            item_id=db_item.id,
                            prompt=item_prompt,
                            parts=item_key,
                        )
                    )
                else:
                    continue

        self.db.commit()  # Save transaction securely

        return schemas.ExerciseResponse(
            exercise_id=self.exercise_in.id,  # type: ignore
            num_questions=len(response_items),
            response_data=response_items,
        )
