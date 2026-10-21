# app/backend/services/exercise_router.py
import logging
import random
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from alite_backend.api import deps
from alite_backend.db import models, schemas
from alite_backend.db.schemas import EnumItemFormat, EnumSentItemType, EnumWordItemType
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
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumWordItemType.POS_TO_LEM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_GEND: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.GEND_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.NOUN_TO_ANIM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ANIM_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_ASPT: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.ASPT_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TYPE: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TYPE_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_TNRF: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.TNRF_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": False,
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
    EnumWordItemType.VERB_GRAM_TO_FORM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "is_reverse": True,
        },
        "formats": [
            models.EnumItemFormat.MCQ,
            models.EnumItemFormat.FITB,
            models.EnumItemFormat.FLASHCARD,
        ],
    },
    EnumWordItemType.VERB_FORM_TO_GRAM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "is_reverse": False,
        },
        "formats": [
            models.EnumItemFormat.MCQ,
            models.EnumItemFormat.FLASHCARD,
        ],
    },
    # lemmas - relation types
    EnumWordItemType.VERB_PAIR_TO_REL: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_rel": models.EnumRelLemTypeGroup.ASPECTUAL_PAIR,
            "drill_mode": "find_target",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.VERB_TO_ASPT_PAIR: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_rel": models.EnumRelLemTypeGroup.ASPECTUAL_PAIR,
            "drill_mode": "find_source",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.LEM_LEM_TO_REL: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "drill_mode": "find_relation",
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumWordItemType.REL_TO_LEM_LEM: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "drill_mode": "find_pair",
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    # sentences - tokens
    EnumSentItemType.NOUN_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumSentItemType.ADJECTIVE_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumSentItemType.VERB_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": models.EnumPartOfSpeech.VERB,
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
    },
    EnumSentItemType.LEXICAL: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.FEATURE_MATCHED,
            "target_pos": None,
            "show_lemma_hint": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sentences - annotation items
    EnumSentItemType.DEP_REL: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "dep_rel",
            "prompt_instruction": "What is the syntactical role of the highlighted word?",
            "target_pos_filter": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.NOUN_CASE: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.subst_case",
            "prompt_instruction": "What is the case of the highlighted noun?",
            "target_pos_filter": models.EnumPartOfSpeech.NOUN,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.VERB_ASPECT: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.verb_aspect",
            "prompt_instruction": "What is the aspect of the highlighted verb?",
            "target_pos_filter": models.EnumPartOfSpeech.VERB,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    # sentences - syntax items
    EnumSentItemType.FIND_HEAD: {
        "strategy_class": SentenceGraphStrategy,
        "kwargs": {
            "query_mode": EnumGraphQueryMode.FIND_GOVERNOR,
            "focus_dep_rel": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
    },
    EnumSentItemType.FIND_SUBJECT: {
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
            "max_tokens": 15,
        },
        "formats": [models.EnumItemFormat.UNSCRAMBLE],
    },
}


class ExerciseRouter:
    """
    Orchestrates pedagogical item generation, rolling deficit mitigation,
    and relational persistence for word- and sentence-level exercise sessions.
    """

    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
        # Stage the parent session header; flush is deferred until deliverables compile
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)

    def get_exercise_generator(
        self, exercise_type: Union[EnumWordItemType, EnumSentItemType, str]
    ) -> Tuple[Any, Dict[str, Any]]:
        resolved_enum = schemas.resolve_strategy_identifier(exercise_type)
        if not resolved_enum:
            raise ValueError(f"Unknown exercise type: {exercise_type}")

        strategy_config = EXERCISE_CONFIG.get(resolved_enum)
        if not strategy_config:
            raise ValueError(f"No generator registered for: {resolved_enum}")

        return strategy_config["strategy_class"], strategy_config["kwargs"]

    def generate_exercise(
        self, request: schemas.ExerciseRequest
    ) -> schemas.ExerciseResponse:
        """
        Executes item generation across requested strategies.
        Accumulates deficits dynamically and triggers domain fallbacks when quotas fall short.
        """
        exercise_payload: List[Dict[str, Any]] = []

        if not request.exercise_context or not request.type_counts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No target items or generation configurations provided.",
            )

        session_requested_formats = set(request.exercise_context.ex_formats)
        rolling_deficit = 0
        strategies_to_process = list(request.type_counts.items())
        is_sentence_session = request.exercise_context.lem_ids is None

        # ---------------------------------------------------------------------
        # 1. Primary Strategy Generation Pass
        # ---------------------------------------------------------------------
        for item_strategy_raw, base_qty in strategies_to_process:
            if base_qty <= 0 and rolling_deficit <= 0:
                continue

            item_strategy = schemas.resolve_strategy_identifier(item_strategy_raw)
            if not item_strategy:
                continue

            requested_qty = base_qty + rolling_deficit
            rolling_deficit = 0

            strategy_class, strategy_kwargs = self.get_exercise_generator(item_strategy)
            strategy_instance = strategy_class(
                db_session=self.db,
                request_context=request.exercise_context,
                **strategy_kwargs,
            )

            blueprints = strategy_instance.generate_item_blueprints(
                num_items=requested_qty,
                max_keys=request.exercise_context.max_keys,
                max_distractors=request.exercise_context.max_distractors,
                config=request.grammar_focus or None,
            )

            actual_yield = len(blueprints) if blueprints else 0
            if actual_yield < requested_qty:
                rolling_deficit = requested_qty - actual_yield

            if not blueprints:
                continue

            # Intersect strategy capabilities with session formats
            supported_formats = schemas.STRATEGY_FORMAT_COMPATIBILITY.get(
                item_strategy,
                frozenset(EXERCISE_CONFIG[item_strategy]["formats"]),
            )
            viable_formats = list(set(supported_formats) & session_requested_formats)

            if not viable_formats:
                rolling_deficit += actual_yield
                continue

            for bp in blueprints:
                chosen_format = random.choice(viable_formats)

                # Quality Guard: Never format as MCQ if distractor count is 0
                distractor_count = len(bp.distractors or [])
                if chosen_format == EnumItemFormat.MCQ and distractor_count < 1:
                    if EnumItemFormat.FITB in viable_formats:
                        chosen_format = EnumItemFormat.FITB
                    else:
                        rolling_deficit += 1
                        continue

                exercise_payload.append(
                    {
                        "item_bp": bp,
                        "item_type": item_strategy,
                        "item_format": chosen_format,
                        "settings": request.grammar_focus,
                    }
                )

        # ---------------------------------------------------------------------
        # 2. Deficit Compensation Pass (High-Capacity Domain Fallbacks)
        # ---------------------------------------------------------------------
        if rolling_deficit > 0:
            domain_fallbacks: List[schemas.AnyItemType] = (
                [
                    EnumSentItemType.NOUN_MORPH,
                    EnumSentItemType.VERB_MORPH,
                    EnumSentItemType.UNSCRAMBLE,
                    EnumSentItemType.LEXICAL,
                ]
                if is_sentence_session
                else [
                    EnumWordItemType.LEM_TO_DEF,
                    EnumWordItemType.LEM_TO_POS,
                ]
            )

            for fallback_strategy in domain_fallbacks:
                if rolling_deficit <= 0:
                    break

                supported_formats = schemas.STRATEGY_FORMAT_COMPATIBILITY.get(
                    fallback_strategy, frozenset()
                )
                viable_formats = list(
                    set(supported_formats) & session_requested_formats
                )
                if not viable_formats:
                    continue

                strategy_class, strategy_kwargs = self.get_exercise_generator(
                    fallback_strategy
                )
                fallback_instance = strategy_class(
                    db_session=self.db,
                    request_context=request.exercise_context,
                    **strategy_kwargs,
                )
                fallback_bps = fallback_instance.generate_item_blueprints(
                    num_items=rolling_deficit,
                    max_keys=request.exercise_context.max_keys,
                    max_distractors=request.exercise_context.max_distractors,
                    config=request.grammar_focus or None,
                )

                if fallback_bps:
                    for bp in fallback_bps:
                        fmt = random.choice(viable_formats)
                        if fmt == EnumItemFormat.MCQ and len(bp.distractors or []) < 1:
                            if EnumItemFormat.FITB in viable_formats:
                                fmt = EnumItemFormat.FITB
                            else:
                                continue

                        exercise_payload.append(
                            {
                                "item_bp": bp,
                                "item_type": fallback_strategy,
                                "item_format": fmt,
                                "settings": request.grammar_focus,
                            }
                        )
                        rolling_deficit -= 1

        # ---------------------------------------------------------------------
        # 3. Assemble and Commit Deliverables
        # ---------------------------------------------------------------------
        response_items = self._compile_deliverables(exercise_payload)

        return schemas.ExerciseResponse(
            exercise_id=self.exercise_in.id,
            num_questions=len(response_items),
            response_data=response_items,
        )

    def _compile_deliverables(
        self,
        exercise_payload: List[Dict[str, Any]],
    ) -> List[schemas.ExerciseItems]:
        """
        Transforms internal blueprints into client deliverables while persisting
        ground-truth keys exclusively to database records (Zero-Knowledge delivery).
        """
        # Hydrate self.exercise_in.id for child item foreign keys
        self.db.flush()
        response_items: List[schemas.ExerciseItems] = []

        for idx, pl in enumerate(exercise_payload):
            bp: schemas.ItemBlueprint = pl["item_bp"]
            raw_item_format: models.EnumItemFormat = pl["item_format"]
            raw_item_type = pl["item_type"]

            item_type_str = (
                raw_item_type.value
                if hasattr(raw_item_type, "value")
                else str(raw_item_type)
            )

            canonical_keys: List[str] = (
                bp.keys if isinstance(bp.keys, list) else [str(bp.keys)]
            )
            full_solution_text = " ".join(canonical_keys).strip()

            item_settings: dict = {}
            if pl["settings"]:
                item_settings["grammar_focus"] = pl["settings"].model_dump(mode="json")
            if bp.sentence_context:
                item_settings["sent_id"] = bp.sentence_context.sent_id
                item_settings["target_indices"] = (
                    bp.sentence_context.target_token_indices
                )
                item_settings["full_sentence"] = bp.sentence_context.full_sentence
                if bp.sentence_context.syntactic_focus:
                    item_settings["syntactic_focus"] = (
                        bp.sentence_context.syntactic_focus
                    )

            # Persist master string in database settings for grading lookups
            item_settings["solution"] = full_solution_text

            raw_prompt = bp.prompt or ""
            interactive_tokens: Optional[List[schemas.DisplayToken]] = None

            if bp.sentence_context and bp.sentence_context.tokens:
                interactive_tokens = [
                    schemas.DisplayToken(
                        tok_idx=t.tok_idx,
                        text=t.lex_raw,
                        is_masked=False,
                        is_punctuation=bool(t.dep_rel == "пункт"),
                    )
                    for t in bp.sentence_context.tokens
                ]

            # -------------------------------------------------------------
            # FORMAT: Fill-in-the-Blank (FITB) - In-Situ Lemma Injection
            # -------------------------------------------------------------
            if raw_item_format == models.EnumItemFormat.FITB:
                if "[___]" in raw_prompt and not bp.hint:
                    # Если пропуск есть, а подсказки нет, проверяем возможность переключения в MCQ
                    if bp.distractors and len(bp.distractors) >= 1:
                        logger.warning(
                            "FITB blueprint for item %s lacks lemma hint. Degrading to MCQ.",
                            item_type_str,
                        )
                        raw_item_format = models.EnumItemFormat.MCQ

            # -------------------------------------------------------------
            # ФОРМАТИРОВАНИЕ FITB С ИНЛАЙН-ПОДСКАЗКОЙ
            # -------------------------------------------------------------
            if raw_item_format == models.EnumItemFormat.FITB:
                # 1. Формирование частей и инлайн-подсказки [**лемма**]
                if "[___]" in raw_prompt:
                    split_parts = raw_prompt.split("[___]")
                    part_0 = split_parts[0]
                    part_1 = split_parts[1]

                    if bp.hint:
                        # Инъекция выделенной леммы сразу за пропуском
                        lemma_tag = f" [**{bp.hint}**]"
                        part_1 = f"{lemma_tag}{part_1}"

                    clean_parts = [part_0, part_1]
                    final_prompt = "[___]".join(clean_parts).strip()
                else:
                    clean_parts = [raw_prompt, ""]
                    final_prompt = raw_prompt

                # 2. Создание родительского Item с валидным prompt
                db_item = models.Item(
                    ex_id=self.exercise_in.id,
                    order_in_ex=idx,
                    item_type=item_type_str,
                    item_format=raw_item_format,
                    prompt=final_prompt,
                    settings=item_settings,
                    start_time=None,
                    finish_time=None,
                )
                self.db.add(db_item)
                self.db.flush()

                if bp.lem_id is not None:
                    self.db.add(
                        models.LemmaInItem(item_id=db_item.id, lem_id=bp.lem_id)
                    )

                # 3. Сохранение эталонного ключа в ItemOption
                for key in canonical_keys:
                    self.db.add(
                        models.ItemOption(
                            item_id=db_item.id,
                            option_text=key,
                            option_uuid=uuid.uuid4(),
                            is_correct=True,
                            explanation="target_key",
                        )
                    )
                self.db.flush()

                response_items.append(
                    schemas.FillInTheBlankResponse(
                        item_id=db_item.id,
                        prompt=final_prompt,
                        parts=clean_parts,
                        sentence_tokens=interactive_tokens,
                    )
                )

            # -------------------------------------------------------------
            # FORMAT: Multiple Choice (MCQ) - Options Only, Clean Prompt
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.MCQ:
                db_item = models.Item(
                    ex_id=self.exercise_in.id,
                    order_in_ex=idx,
                    item_type=item_type_str,
                    item_format=raw_item_format,
                    prompt=raw_prompt,
                    settings=item_settings,
                    start_time=None,
                    finish_time=None,
                )
                self.db.add(db_item)
                self.db.flush()

                if bp.lem_id is not None:
                    self.db.add(
                        models.LemmaInItem(item_id=db_item.id, lem_id=bp.lem_id)
                    )

                all_options = canonical_keys + (bp.distractors or [])
                for opt in all_options:
                    self.db.add(
                        models.ItemOption(
                            item_id=db_item.id,
                            option_text=opt,
                            option_uuid=uuid.uuid4(),
                            is_correct=(opt in canonical_keys),
                            explanation=None,
                        )
                    )
                self.db.flush()

                shuffled_options = list(all_options)
                random.shuffle(shuffled_options)

                response_items.append(
                    schemas.MultipleChoiceResponse(
                        item_id=db_item.id,
                        prompt=raw_prompt,
                        options=shuffled_options,
                        sentence_tokens=interactive_tokens,
                    )
                )

            # -------------------------------------------------------------
            # FORMAT: Unscramble - Token Shuffle & Master Solution Storage
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.UNSCRAMBLE:
                db_item = models.Item(
                    ex_id=self.exercise_in.id,
                    order_in_ex=idx,
                    item_type=item_type_str,
                    item_format=raw_item_format,
                    prompt=raw_prompt,
                    settings=item_settings,
                    start_time=None,
                    finish_time=None,
                )
                self.db.add(db_item)
                self.db.flush()

                # 1. Эталонное полное предложение для проверки
                self.db.add(
                    models.ItemOption(
                        item_id=db_item.id,
                        option_text=full_solution_text,
                        option_uuid=uuid.uuid4(),
                        is_correct=True,
                        explanation="complete_sentence",
                    )
                )

                # 2. Токены с сохранением единого UUID для хэндла и базы данных
                token_strings = canonical_keys
                handle_pairs: List[Tuple[str, str]] = []
                token_options: List[models.ItemOption] = []

                for pos, word in enumerate(token_strings):
                    # Генерируем один UUID и используем его и в базе, и в ответе
                    token_uuid = uuid.uuid4()
                    token_handle = token_uuid.hex[:8]
                    handle_pairs.append((token_handle, word))

                    token_options.append(
                        models.ItemOption(
                            item_id=db_item.id,
                            option_text=word,
                            option_uuid=token_uuid,
                            is_correct=False,
                            explanation=f"position:{pos}",
                        )
                    )

                self.db.add_all(token_options)
                self.db.flush()

                # Перемешивание токенов с гарантией нетождественности
                shuffled_pairs = list(handle_pairs)
                if len(shuffled_pairs) > 1:
                    attempts = 0
                    while [
                        p[1] for p in shuffled_pairs
                    ] == token_strings and attempts < 10:
                        random.shuffle(shuffled_pairs)
                        attempts += 1

                response_items.append(
                    schemas.UnscrambleResponse(
                        item_id=db_item.id,
                        prompt=raw_prompt,
                        shuffled_tokens=[
                            schemas.UnscrambleToken(token_handle=h, text=w)
                            for h, w in shuffled_pairs
                        ],
                    )
                )

            # -------------------------------------------------------------
            # FORMAT: Flashcard
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.FLASHCARD:
                db_item = models.Item(
                    ex_id=self.exercise_in.id,
                    order_in_ex=idx,
                    item_type=item_type_str,
                    item_format=raw_item_format,
                    prompt=raw_prompt,
                    settings=item_settings,
                    start_time=None,
                    finish_time=None,
                )
                self.db.add(db_item)
                self.db.flush()

                response_items.append(
                    schemas.FlashcardResponse(
                        item_id=db_item.id,
                        prompt=raw_prompt,
                        back_text=canonical_keys[0],
                    )
                )

        self.db.commit()
        return response_items
