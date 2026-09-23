# app/backend/services/exercise_router.py
import logging
import random
import uuid
from typing import Any, Dict, Tuple

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.schemas import EnumSentItemType, EnumWordItemType
from alite_backend.services.items.lemma_base import LemmaItemBaseStrategy
from alite_backend.services.items.lemma_subclasses import (
    LemmaMorphologicalStrategy,
    LemmaRelationStrategy,
    LemmaSiblingAttributeStrategy,
    LemmaStandaloneAttributeStrategy,
)
from alite_backend.services.items.sentence_subclasses import (
    EnumDistractorMode,
    EnumGraphQueryMode,
    SentenceAnnotationStrategy,
    SentenceClozeStrategy,
    SentenceGraphStrategy,
    SentenceUnscrambleStrategy,
)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

EXERCISE_CONFIG = {
    # lemmas - zero-query types
    EnumWordItemType.LEM_TO_POS: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.POS_TO_LEM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_GEND: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.GEND_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_ANIM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ANIM_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_ASPT: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ASPT_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TYPE: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TYPE_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TNRF: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TNRF_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # lemmas - sibling-query types
    EnumWordItemType.LEM_TO_DEF: {
        "strategy_class": LemmaSiblingAttributeStrategy,
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
        "strategy_class": LemmaSiblingAttributeStrategy,
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
        "strategy_class": LemmaSiblingAttributeStrategy,
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
        "strategy_class": LemmaSiblingAttributeStrategy,
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
    # lemmas - morphology types
    EnumWordItemType.NOUN_FORM_TO_GRAM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_GRAM_TO_FORM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.ADJV_FORM_TO_GRAM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ADJV_GRAM_TO_FORM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    # lemmas - relation types
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
    # sentences - tokens
    EnumSentItemType.CLOZE_NOUN_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": "NOUN",
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumSentItemType.CLOZE_VERB_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": "VERB",
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumSentItemType.CLOZE_LEXICAL: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.FEATURE_MATCHED,
            "target_pos": None,
            "show_lemma_hint": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sentences - annotation items
    EnumSentItemType.LABEL_DEP_REL: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "dep_rel",
            "prompt_instruction": "Определите синтаксическую роль выделенного слова:",
            "target_pos_filter": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.LABEL_NOUN_CASE: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.subst_case",
            "prompt_instruction": "Определите падеж выделенного существительного в предложении:",
            "target_pos_filter": "NOUN",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.LABEL_VERB_ASPECT: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.verb_aspect",
            "prompt_instruction": "Определите вид выделенного глагола в предложении:",
            "target_pos_filter": "VERB",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sentences - syntax items
    EnumSentItemType.SYNTAX_FIND_HEAD: {
        "strategy_class": SentenceGraphStrategy,
        "kwargs": {
            "query_mode": EnumGraphQueryMode.FIND_GOVERNOR,
            "focus_dep_rel": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.SYNTAX_FIND_SUBJECT: {
        "strategy_class": SentenceGraphStrategy,
        "kwargs": {
            "query_mode": EnumGraphQueryMode.FIND_ROLE,
            "focus_dep_rel": "предик",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sentence - unscramble
    EnumSentItemType.UNSCRAMBLE: {
        "strategy_class": SentenceUnscrambleStrategy,
        "kwargs": {
            "min_tokens": 4,
            "max_tokens": 10,
        },
        "formats": [models.EnumItemFormat.UNSCRAMBLE],
    },
}


class ExerciseRouter:
    """_summary_"""

    def __init__(
        self,
        db: Session,
        user_id: int,  # from endpoint
    ):
        self.db = db
        self.user_id = user_id
        # create exercise record
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)
        self.db.flush()

    def get_exercise_generator(
        self, exercise_type: EnumWordItemType | EnumSentItemType
    ) -> Tuple[
        Any,
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No target items or generation configurations provided.",
            )

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
            # specific_config = (
            #     request.grammar_focus.strategies if request.grammar_focus else None  # type: ignore
            # )
            # create blueprints for all items of a strategy
            blueprints = strategy_instance.generate_item_blueprints(
                num_items=requested_qty,
                max_keys=request.exercise_context.max_keys,
                max_distractors=request.exercise_context.max_distractors,
                config=request.grammar_focus or None,
            )
            if not blueprints:
                continue

            # Format arbitration: intersect requested formats with strategy capabilities
            supported_formats = schemas.STRATEGY_FORMATS.get(
                item_strategy, EXERCISE_CONFIG[item_strategy]["formats"]
            )
            viable_formats = list(
                set(supported_formats) & set(request.exercise_context.ex_formats)
            )

            if not viable_formats:
                logger.warning(
                    "Skipping %s: requested formats %s incompatible with supported %s",
                    item_strategy,
                    request.exercise_context.ex_formats,
                    supported_formats,
                )
                continue

            # assign format and add to item list
            for bp in blueprints:
                chosen_format = random.choice(viable_formats)
                exercise_payload.append(
                    {
                        "item_bp": bp,
                        "item_type": item_strategy,
                        "item_format": chosen_format,
                        "settings": request.grammar_focus,
                    }
                )

        response_items = []

        for idx, pl in enumerate(exercise_payload):
            bp: schemas.ItemBlueprint = pl["item_bp"]
            item_format = pl["item_format"]

            item_settings = {}
            # item_prompt = pl["item_bp"].prompt
            # item_key = pl["item_bp"].keys
            # item_distractors = pl["item_bp"].distractors
            # item_settings = (
            #     pl["settings"].model_dump(mode="json") if pl["settings"] else None
            # )
            # TODO
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
