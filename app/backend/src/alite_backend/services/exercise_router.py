# app/backend/services/exercise_router.py
import logging
import random
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.db import models, schemas
from alite_backend.db.models import (
    KSA,
    EnumDirectionality,
    EnumItemFormat,
    EnumSentItemType,
    EnumWordItemType,
    ItemTarget,
    LemmaInItem,
)
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

logger = logging.getLogger(__name__)

EXERCISE_CONFIG: Dict[
    Union[EnumWordItemType, EnumSentItemType], schemas.StrategyConfigEntry
] = {
    # lemmas - zero-query types
    EnumWordItemType.LEM_TO_POS: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Parts of Speech", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.POS_TO_LEM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": None,
            "target_column": "pos",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Parts of Speech", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.NOUN_TO_GEND: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Noun Gender", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.GEND_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_gender",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Noun Gender", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.NOUN_TO_ANIM: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Noun Animacy", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.ANIM_TO_NOUN: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "target_column": "noun_animacy",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Noun Animacy", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.VERB_TO_ASPT: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb Aspect", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.ASPT_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_aspect",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb Aspect", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.VERB_TO_TYPE: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb Type", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.TYPE_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_type",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb Type", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.VERB_TO_TNRF: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb TNRF", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.TNRF_TO_VERB: {
        "strategy_class": LemmaStandaloneAttributeStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_column": "verb_trans_refl",
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb TNRF", EnumDirectionality.SYNTHESIS),
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
        "ksa": ("Definitions", EnumDirectionality.ANALYSIS),
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
        "ksa": ("Definitions", EnumDirectionality.SYNTHESIS),
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
        "ksa": ("Pronunciation", EnumDirectionality.NEUTRAL),
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
        "ksa": ("Spelling", EnumDirectionality.NEUTRAL),
    },
    # lemmas - morphology types
    EnumWordItemType.NOUN_FORM_TO_GRAM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Noun Morphology", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.NOUN_GRAM_TO_FORM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.NOUN,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Noun Morphology", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.ADJV_FORM_TO_GRAM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Adjective Morphology", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.ADJV_GRAM_TO_FORM: {
        "strategy_class": LemmaMorphologicalStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "is_reverse": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Adjective Morphology", EnumDirectionality.SYNTHESIS),
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
        "ksa": ("Verb Morphology", EnumDirectionality.ANALYSIS),
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
        "ksa": ("Verb Morphology", EnumDirectionality.SYNTHESIS),
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
        "ksa": ("Verb Pairs", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.VERB_TO_ASPT_PAIR: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": models.EnumPartOfSpeech.VERB,
            "target_rel": models.EnumRelLemTypeGroup.ASPECTUAL_PAIR,
            "drill_mode": "find_source",
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Verb Pairs", EnumDirectionality.SYNTHESIS),
    },
    EnumWordItemType.LEM_LEM_TO_REL: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "drill_mode": "find_relation",
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Semantics", EnumDirectionality.ANALYSIS),
    },
    EnumWordItemType.REL_TO_LEM_LEM: {
        "strategy_class": LemmaRelationStrategy,
        "kwargs": {
            "target_pos": None,
            "target_rel": None,
            "drill_mode": "find_pair",
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Semantics", EnumDirectionality.SYNTHESIS),
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
        "ksa": ("Nouns in Context", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.ADJECTIVE_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": models.EnumPartOfSpeech.ADJECTIVE,
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Adjectives in Context", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.VERB_MORPH: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.INTRA_LEMMA,
            "target_pos": models.EnumPartOfSpeech.VERB,
            "show_lemma_hint": True,
        },
        "formats": [models.EnumItemFormat.MCQ, models.EnumItemFormat.FITB],
        "ksa": ("Verbs in Context", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.LEXICAL: {
        "strategy_class": SentenceClozeStrategy,
        "kwargs": {
            "distractor_mode": EnumDistractorMode.FEATURE_MATCHED,
            "target_pos": None,
            "show_lemma_hint": False,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Meaning in Context", EnumDirectionality.SYNTHESIS),
    },
    # sentences - annotation items
    EnumSentItemType.DEP_REL: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "dep_rel",
            "prompt_instruction": "What is the syntactical role of the highlighted word?",  # noqa: E501
            "target_pos_filter": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Sentence Dependency", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.NOUN_CASE: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.subst_case",
            "prompt_instruction": "What is the case of the highlighted noun?",
            "target_pos_filter": models.EnumPartOfSpeech.NOUN,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Case in Context", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.VERB_ASPECT: {
        "strategy_class": SentenceAnnotationStrategy,
        "kwargs": {
            "target_property": "features.verb_aspect",
            "prompt_instruction": "What is the aspect of the highlighted verb?",
            "target_pos_filter": models.EnumPartOfSpeech.VERB,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Aspect in Context", EnumDirectionality.SYNTHESIS),
    },
    # sentences - syntax items
    EnumSentItemType.FIND_HEAD: {
        "strategy_class": SentenceGraphStrategy,
        "kwargs": {
            "query_mode": EnumGraphQueryMode.FIND_GOVERNOR,
            "focus_dep_rel": None,
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Find Sentence Head", EnumDirectionality.SYNTHESIS),
    },
    EnumSentItemType.FIND_SUBJECT: {
        "strategy_class": SentenceGraphStrategy,
        "kwargs": {
            "query_mode": EnumGraphQueryMode.FIND_ROLE,
            "focus_dep_rel": "предик",
        },
        "formats": [models.EnumItemFormat.MCQ],
        "ksa": ("Find Sentence Subject", EnumDirectionality.SYNTHESIS),
    },
    # sentence - unscramble
    EnumSentItemType.UNSCRAMBLE: {
        "strategy_class": SentenceUnscrambleStrategy,
        "kwargs": {
            "min_tokens": 4,
            "max_tokens": 15,
        },
        "formats": [models.EnumItemFormat.UNSCRAMBLE],
        "ksa": ("Unscramble Sentence", EnumDirectionality.SYNTHESIS),
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

        # stage parent exercise session header
        self.exercise_in = models.Exercise(user_id=self.user_id)
        self.db.add(self.exercise_in)

        # pre-load KSA cache to ensure O(1) resolution during item compilation
        self._ksa_cache: Dict[str, int] = {}
        self._load_ksa_cache()

    def _load_ksa_cache(self) -> None:
        """Loads all KSA names and primary keys into memory at router instantiation."""
        try:
            ksas = self.db.scalars(select(KSA)).all()
            self._ksa_cache = {ksa.name: ksa.id for ksa in ksas if ksa.id is not None}
        except Exception as e:
            logger.warning(f"Could not load KSA cache during ExerciseRouter init: {e}")

    def _resolve_item_ksas(
        self,
        strategy: Union[EnumWordItemType, EnumSentItemType],
        override_names: Optional[List[str]] = None,
    ) -> Tuple[List[int], EnumDirectionality]:
        """
        Resolves a list of KSA IDs and the cognitive directionality for an item.
        Prioritizes blueprint-level leaf KSA overrides; falls back to EXERCISE_CONFIG.
        """
        config_entry = EXERCISE_CONFIG.get(strategy)
        if not config_entry or "ksa" not in config_entry:
            default_id = self._ksa_cache.get("Semantics")
            return ([default_id] if default_id else []), EnumDirectionality.NEUTRAL

        default_ksa_name, directionality = config_entry["ksa"]

        # Use dynamic leaf KSAs if the strategy provided them; otherwise use the static default  # noqa: E501
        target_names = override_names if override_names else [default_ksa_name]
        ksa_ids = [
            self._ksa_cache[name] for name in target_names if name in self._ksa_cache
        ]

        if not ksa_ids:
            logger.warning(
                "No KSA IDs resolved for strategy=%s, target_names=%s",
                strategy,
                target_names,
            )

        return ksa_ids, directionality

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
        """  # noqa: E501
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
        # 1. primary strategy generation pass
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
                chosen_format = random.choice(viable_formats)  # noqa: S311

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
        # 2. deficit compensation pass (high-capacity domain fallbacks)
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
                        fmt = random.choice(viable_formats)  # noqa: S311
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
        # 3. assemble and commit deliverables
        # ---------------------------------------------------------------------
        response_items = self._compile_deliverables(exercise_payload)

        return schemas.ExerciseResponse(
            exercise_id=self.exercise_in.id,  # type: ignore
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

            # persist master string in database settings for grading lookups
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
            # format: fill-in-the-blank (fitb) - in-situ lemma injection
            # -------------------------------------------------------------
            if raw_item_format == models.EnumItemFormat.FITB:
                if "[___]" in raw_prompt and not bp.hint:
                    if bp.distractors and len(bp.distractors) >= 1:
                        logger.warning(
                            "FITB blueprint for item %s lacks lemma hint. Degrading to MCQ.",  # noqa: E501
                            item_type_str,
                        )
                        raw_item_format = models.EnumItemFormat.MCQ

            def seed_item_irt(
                db_item: models.Item,
                item_format: models.EnumItemFormat,
                num_options: int = 0,
            ) -> None:
                """
                Seeds cold-start Item Response Theory (IRT) parameters for a newly created Item.
                Prevents empty item_irt rows and provides a baseline before batch calibration runs.
                """  # noqa: E501
                # guessing floor c is 1/k for multi-option mcq and 0.0 for recall/open/unscramble formats.  # noqa: e501
                if item_format == models.EnumItemFormat.MCQ and num_options > 1:
                    guessing_c = round(1.0 / num_options, 4)
                else:
                    guessing_c = 0.0

                self.db.add(
                    models.ItemIRT(
                        item_id=db_item.id,  # type: ignore
                        difficulty_b=0.0,
                        discrimination_a=1.0,
                        guessing_c=guessing_c,
                    )
                )

            def persist_base_item(
                prompt_text: str, num_options: int = 0
            ) -> models.Item:  # noqa: E501
                db_item = models.Item(
                    ex_id=self.exercise_in.id,  # type: ignore
                    order_in_ex=idx,  # noqa: B023
                    item_type=raw_item_type.value  # noqa: B023
                    if hasattr(raw_item_type, "value")  # noqa: B023
                    else str(raw_item_type),  # noqa: B023, E501
                    item_format=raw_item_format,  # noqa: B023
                    prompt=prompt_text,
                    settings=item_settings,  # noqa: B023
                )
                self.db.add(db_item)
                self.db.flush()

                # seed cold-start irt params for new item
                seed_item_irt(
                    db_item=db_item,
                    item_format=raw_item_format,  # noqa: B023
                    num_options=num_options,
                )  # noqa: B023, E501

                # resolve ksa and directionality from unified exercise_config
                ksa_ids, directionality = self._resolve_item_ksas(
                    strategy=raw_item_type,  # noqa: B023
                    override_names=bp.ksa_names,  # noqa: B023
                )

                if bp.lem_id is not None:  # noqa: B023
                    self.db.add(LemmaInItem(item_id=db_item.id, lem_id=bp.lem_id))  # type: ignore # noqa: B023

                    for ksa_id in ksa_ids:
                        self.db.add(
                            ItemTarget(
                                item_id=db_item.id,  # type: ignore
                                lemma_id=bp.lem_id,  # noqa: B023
                                ksa_id=ksa_id,
                                directionality=directionality,
                            )
                        )

                # optional branch if ItemTarget.lemma_id is nullable and you want non-lemma KSA tracking:  # noqa: E501
                elif ksa_ids:
                    for ksa_id in ksa_ids:
                        self.db.add(
                            ItemTarget(
                                item_id=db_item.id,  # type: ignore
                                lemma_id=None,  # type: ignore
                                ksa_id=ksa_id,
                                directionality=directionality,
                            )
                        )

                return db_item

            # -------------------------------------------------------------
            # formatting fitb with inline hint
            # -------------------------------------------------------------
            if raw_item_format == models.EnumItemFormat.FITB:
                # 1. Формирование частей и инлайн-подсказки [**лемма**]
                if "[___]" in raw_prompt:
                    split_parts = raw_prompt.split("[___]")
                    part_0 = split_parts[0]
                    part_1 = split_parts[1]

                    if bp.hint:
                        lemma_tag = f" [**{bp.hint}**]"
                        part_1 = f"{lemma_tag}{part_1}"

                    clean_parts = [part_0, part_1]
                    final_prompt = "[___]".join(clean_parts).strip()
                else:
                    clean_parts = [raw_prompt, ""]
                    final_prompt = raw_prompt

                # create parent item
                db_item = persist_base_item(final_prompt, num_options=0)

                for key in canonical_keys:
                    self.db.add(
                        models.ItemOption(
                            item_id=db_item.id,  # type: ignore
                            option_text=key,
                            option_uuid=uuid.uuid4(),
                            is_correct=True,
                            explanation="target_key",
                        )
                    )
                self.db.flush()

                response_items.append(
                    schemas.FillInTheBlankResponse(
                        item_id=db_item.id,  # type: ignore
                        prompt=final_prompt,
                        parts=clean_parts,
                        sentence_tokens=interactive_tokens,
                    )
                )

            # -------------------------------------------------------------
            # format: multiple choice (mcq) - options only, clean prompt
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.MCQ:
                all_options = canonical_keys + (bp.distractors or [])
                db_item = persist_base_item(
                    prompt_text=raw_prompt, num_options=len(all_options)
                )  # noqa: E501

                for opt in all_options:
                    self.db.add(
                        models.ItemOption(
                            item_id=db_item.id,  # type: ignore
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
                        item_id=db_item.id,  # type: ignore
                        prompt=raw_prompt,
                        options=shuffled_options,  # type: ignore
                        sentence_tokens=interactive_tokens,
                    )
                )

            # -------------------------------------------------------------
            # format: unscramble - token shuffle & master solution storage
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.UNSCRAMBLE:
                db_item = persist_base_item(prompt_text=raw_prompt)

                self.db.add(
                    models.ItemOption(
                        item_id=db_item.id,  # type: ignore
                        option_text=full_solution_text,
                        option_uuid=uuid.uuid4(),
                        is_correct=True,
                        explanation="complete_sentence",
                    )
                )

                token_strings = canonical_keys
                handle_pairs: List[Tuple[str, str]] = []
                token_options: List[models.ItemOption] = []

                for pos, word in enumerate(token_strings):
                    # 1 uuid for base and options
                    token_uuid = uuid.uuid4()
                    token_handle = token_uuid.hex[:8]
                    handle_pairs.append((token_handle, word))

                    token_options.append(
                        models.ItemOption(
                            item_id=db_item.id,  # type: ignore
                            option_text=word,
                            option_uuid=token_uuid,
                            is_correct=False,
                            explanation=f"position:{pos}",
                        )
                    )

                self.db.add_all(token_options)
                self.db.flush()

                # shuffle tokens
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
                        item_id=db_item.id,  # type: ignore
                        prompt=raw_prompt,
                        shuffled_tokens=[
                            schemas.UnscrambleToken(token_handle=h, text=w)
                            for h, w in shuffled_pairs
                        ],
                    )
                )

            # -------------------------------------------------------------
            # format: flashcard
            # -------------------------------------------------------------
            elif raw_item_format == models.EnumItemFormat.FLASHCARD:
                db_item = persist_base_item(prompt_text=raw_prompt)

                response_items.append(
                    schemas.FlashcardResponse(
                        item_id=db_item.id,  # type: ignore
                        prompt=raw_prompt,
                        back_text=canonical_keys[0],
                    )
                )

        self.db.commit()
        return response_items
