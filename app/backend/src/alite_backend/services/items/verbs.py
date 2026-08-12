# app/backend/src/alite_backend/services/items/verbs.py
from typing import List

from alite_backend.db import models, schemas
from alite_backend.services.items.base import BaseExerciseStrategy

# verb to aspect
# "What is the aspect of [lemma_verb]?" (ZQ: MCQ)


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
            is_reverse=False,
        )


# aspect to verb
# "Choose a verb that is [aspect]." (ZQ: MCQ)


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
            is_reverse=True,
        )


# verb pair to relation
# "Which of the pair [lemma_verb0] - [lemma_verb1] is [verb_aspect]?"


class VerbPairToRelationStrategy(BaseExerciseStrategy):
    pass


# verb relation to pair
# "What is the [relation_verb_aspect] partner of [lemma_verb]?" (MCQ/Cloze)


class VerbRelationToPairStrategy(BaseExerciseStrategy):
    pass


# verb to type
# "What is the conjugation type of [lemma_verb]?" (ZQ: MCQ)


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
            is_reverse=False,
        )


# type to verb
# "Pick the [verb_type] verb." (ZQ: MCQ)


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
            is_reverse=True,
        )


# pronoun + verb to conjugated form
# "Conjugate [pronoun] [verb_lemma]:" (GQ: MCQ/Cloze)


class VerbToConjFormStrategy(BaseExerciseStrategy):
    pass


# verb to transitivity / reflexivity
# "What is the transitivity / reflexivity of [lemma_verb]?" (ZQ: MCQ)


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
            is_reverse=False,
        )


# transitivity / reflexivity to verb
# "Choose the [transitivity / reflexivity] verb." (ZQ: MCQ)


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
            is_reverse=True,
        )
