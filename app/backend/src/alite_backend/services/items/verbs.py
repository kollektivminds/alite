# app/backend/src/alite_backend/services/items/verbs.py
from typing import List
from alite_backend.db import models, schemas
from alite_backend.services.items.base import BaseExerciseStrategy

# verb to aspect


class VerbToAspectStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self,
        num_items: int = 10,
        max_keys: int = 1,
        max_distractors: int = 3,
        config=None,
    ) -> List[schemas.ItemBlueprint]:
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_aspect",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",  # Prompts: "Identify the gender of 'книга'"
        )


# aspect to verb


class AspectToVerbStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_aspect",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",  # Prompts: "Identify the gender of 'книга'"
        )


# VERB PAIR TO RELATION


# VERB ASPECT TO PAIR


# LEMMA TO VERB TYPE


class VerbToTypeStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_type",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",  # Prompts: "Identify the gender of 'книга'"
        )


# VERB TYPE TO LEMMA


class TypeToVerbStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_type",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",  # Prompts: "Identify the gender of 'книга'"
        )


# PRONOUN + INFINITIVE TO VERB CONJUGATION


# VERB CONJUGATION TO PRONOUN + INFINITIVE


# VERB TO TRANSITIVITY/REFLEXIVITY


class VerbToTransReflStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_trans_refl",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",  # Prompts: "Identify the gender of 'книга'"
        )


# TRANSITIVITY/REFLEXIVITY TO VERB


class TransReflToVerbStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.VERB,
            target_attr="verb_trans_refl",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",  # Prompts: "Identify the gender of 'книга'"
        )
