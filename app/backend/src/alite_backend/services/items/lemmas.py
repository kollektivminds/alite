# app/backend/src/alite_backend/services/items/lemmas.py
from typing import List, Dict
from alite_backend.services.items.base import BaseExerciseStrategy
from alite_backend.db import models, schemas

# lemam to part of speech ("lemma_to_pos")
# "What is the part of speech of [lemma]?" (ZQ: MCQ)


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


# part of speech to lemma ("pos_to_lemma")
# "Choose the [part_of_speech] from the following." (ZQ: MCQ)


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


# lemma to definition ("lem_to_def")
# "What is a definition of [lemma]?" (SQ: MCQ)


class LemmaToDefinitionStrategy(BaseExerciseStrategy):
    pass


# definition to lemma ("def_to_lem")
# "Choose a word with the following meaning: [definition]." (SQ: MCQ)


class DefinitionToLemmaStrategy(BaseExerciseStrategy):
    pass


# lemma to pronunciation ("lem_to_pron")
# "How do you pronounce [lemma] ([pron_type])?" (SQ: MCQ)


class LemmaToPronunciationStrategy(BaseExerciseStrategy):
    pass


# "Which lemma is pronounced [pronunciation] ([pron_type])?" (SQ: MCQ/Cloze)


class PronunciationToLemmaStrategy(BaseExerciseStrategy):
    pass


# lemma + lemma to relation ("lem_lem_to_rel")
# "[lemma_0] is what to [lemma_1]?" (MCQ)


class LemLemToRelationStrategy(BaseExerciseStrategy):
    pass


# relation to lemma + lemma ("rel_to_lem_lem")
# "Which of the following pairs is [lemma_relation]?" (MCQ)


class RelationToLemLemStrategy(BaseExerciseStrategy):
    pass
