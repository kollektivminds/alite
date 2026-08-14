# app/backend/src/alite_backend/services/items/subclasses.py
import logging
import random
from collections import defaultdict
from typing import Any, List

from alite_backend.db import models, schemas
from alite_backend.db.crud.item_crud import crud_exercise, crud_item
from alite_backend.services.items.base import BaseExerciseStrategy
from sqlalchemy import func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# --- Distractor Formulae ---
# ZQ = zero-query (Enum-based)
# SQ = sibling quiery (multitable-based)
# GQ = grammar query (gram_props-based)


class StandaloneAttributeStrategy(BaseExerciseStrategy):

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        target_pos: models.EnumPartOfSpeech | None,
        target_column: str,
        is_reverse: bool,
    ):
        # pass up to Base class
        super().__init__(db_session, request_context)

        # subclass attributes
        self.target_pos = target_pos
        self.target_column = target_column
        self.is_reverse = is_reverse

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=self.target_pos,
            target_attr=self.target_column,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            is_reverse=self.is_reverse,
        )


class SiblingAttributeStrategy(BaseExerciseStrategy):

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        target_pos: models.EnumPartOfSpeech,
        target_model: models.Base,
        target_column: str,
        junction_model: models.Base,
        junction_column: str,
        is_reverse: bool,
    ):
        # pass up to Base class
        super().__init__(db_session, request_context)

        self.target_pos = target_pos
        self.target_model = target_model
        self.junction_model = junction_model
        self.junction_column = junction_column
        self.target_column = target_column
        self.is_reverse = is_reverse

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_sibling_query_drill(
            target_model=self.target_model,
            target_column=self.target_column,
            junction_model=self.junction_model,
            junction_column=self.junction_column,
            target_pos=self.target_pos,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            is_reverse=self.is_reverse,
        )


class MorphologicalStrategy(BaseExerciseStrategy):

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        target_pos: models.EnumPartOfSpeech,
        is_reverse: bool,
    ):

        # pass up to Base class
        super().__init__(db_session, request_context)

        self.target_pos = target_pos
        self.is_reverse = is_reverse

    def generate_item_blueprints(
        self,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 3,
        config: schemas.StrategyConfigs | None = None,
    ) -> List[schemas.ItemBlueprint] | None:
        allow_ooo = config.allow_odd_one_out if config else False

        if self.target_pos in ["noun", "adjective"]:
            focus = "substantives"
        elif self.target_pos == "verb":
            focus = "verbs"
        elif self.target_pos == "participle":
            focus = "participles"
        else:
            raise KeyError

        if focus:
            foci = (
                config.strategies.get(focus, "all")
                if config and config.strategies
                else "all"
            )

            return self._build_paradigm_drill(
                pos_target=self.target_pos,
                num_items=num_items,
                max_keys=max_keys,
                max_distractors=max_distractors,
                allowed_foci=foci,  # type: ignore
                allow_odd_one_out=allow_ooo,
                is_reverse=self.is_reverse,
            )


class LemmaRelationStrategy(BaseExerciseStrategy):

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        target_pos: models.EnumPartOfSpeech | None,
        target_rel: models.EnumRelLemTypeGroup | None,
        is_reverse: bool,
    ):
        # pass up to Base class
        super().__init__(db_session, request_context)

        # subclass attributes
        self.target_pos = target_pos
        self.target_rel = target_rel
        self.is_reverse = is_reverse

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_lemma_relation_drill(
            rel_target_group=self.target_rel,
            pos_target=self.target_pos,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            is_reverse=self.is_reverse,
        )
