# app/backend/src/alite_backend/services/items/subclasses.py
from typing import List
import random
from collections import defaultdict
import logging
from sqlalchemy import select, func
from alite_backend.db import models, schemas
from alite_backend.db.crud.item_crud import crud_item, crud_exercise
from alite_backend.services.items.base import BaseExerciseStrategy

logger = logging.getLogger(__name__)

# --- Distractor Formulae ---
# ZQ = zero-query (Enum-based)
# SQ = sibling quiery (multitable-based)
# GQ = grammar query (gram_props-based)


class StandaloneAttributeStrategy(BaseExerciseStrategy):

    def __init__(
        self,
        target_pos: models.EnumPartOfSpeech,
        target_column: str,
        drill_direction: str,
    ):
        self.target_pos = target_pos
        self.target_column = target_column
        self.target_direction = drill_direction

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
            drill_direction=self.target_direction
        )

class RelationalAttributeStrategy(BaseExerciseStrategy):
    
    def __init__(
        self,
        target_pos: models.EnumPartOfSpeech,
        target_column: str,
        drill_direction: str,
    ):
        self.target_pos = target_pos
        self.target_column = target_column
        self.target_direction = drill_direction

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_sibling_query_drill(
            pos_target=self.target_pos,
            target_attr=self.target_column,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction=self.target_direction
        )

class MorphologicalStrategy(BaseExerciseStrategy):
    
    def __init__(
        self,
        target_pos: models.EnumPartOfSpeech,
        target_column: str,
        drill_direction: str,
    ):
        self.target_pos = target_pos
        self.target_column = target_column
        self.target_direction = drill_direction

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False
        
        if self.target_pos in ["noun", "adjective"]:
            focus = "substantives"
        elif self.target_pos == "verb":
            focus = "verbs"
        elif self.target_pos == "participle":
            focus = "participles"
        
        foci = (
            config.strategies.get(
                focus, "all"
            )
            if config and config.strategies
            else "all"
        )
        
        return self._build_paradigm_drill(
            pos_target=self.target_pos,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allowed_foci=foci, # type: ignore
            allow_odd_one_out=allow_ooo,
            drill_direction=self.target_direction
        )

class LemmaRelationStrategy(BaseExerciseStrategy):
    
    def __init__(
        self,
        target_pos: models.EnumPartOfSpeech,
        target_column: str,
        drill_direction: str,
    ):
        self.target_pos = target_pos
        self.target_column = target_column
        self.target_direction = drill_direction

    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self.(
            pos_target=self.target_pos,
            target_attr=self.target_column,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction=self.target_direction
        )
