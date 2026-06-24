# app/backend/src/alite_backend/services/items/lemmas.py
from typing import List, Dict
from alite_backend.services.items.base import BaseExerciseStrategy
from alite_backend.db import models, schemas

# LEMMA TO POS


class LemmaToPosStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=None,
            target_attr="pos",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",
        )


# POS TO LEMMA


class PosToLemmaStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=None,
            target_attr="pos",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",
        )


# LEMMA TO DEFINITION


class LemmaToDefinitionStrategy(BaseExerciseStrategy):
    pass


# DEFINITION TO LEMMA


class DefinitionToLemmaStrategy(BaseExerciseStrategy):
    pass


# LEMMA TO PRONUNCIATION


class LemmaToPronunciationStrategy(BaseExerciseStrategy):
    pass


# PRONUNCIATION TO LEMMA


class PronunciationToLemmaStrategy(BaseExerciseStrategy):
    pass


# LEMMA + LEMMA TO RELATION


class LemLemToRelationStrategy(BaseExerciseStrategy):
    pass


# RELATION TO LEMMA + LEMMA


class RelationToLemLemStrategy(BaseExerciseStrategy):
    pass
