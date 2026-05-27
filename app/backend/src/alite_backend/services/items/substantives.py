# app/backend/src/alite_backend/services/items/nouns.py
from typing import List
import logging
from alite_backend.db import models, schemas
from alite_backend.services.items.base import BaseExerciseStrategy

logger = logging.getLogger(__name__)

# --- Distractor Formulae ---
# ZQ = zero-query (Enum-based)
# SQ = sibling quiery (table-based)
# GQ = grammar query (gram_props-based)

#
# ADJECTIVES
#

# ADJECTIVE + FORM TO TYPE ("adjv_form_to_type")
# "What is the [comparative | superlative] form of [adjective]?" (ZQ: MCQ)


# ADJECTIVE TYPE TO LEMMA ("adjv_type_to_lem")
# "What is the base form of [adjective]?" (SQ: MCQ/Cloze)


# ADJECTIVE FORM TO GRAMMAR ("adjv_form_to_gram")
# "What is the [gender, number, case] of [adjective form]?" (GQ: MCQ)


# ADJECTIVE GRAMMAR TO FORM ("adjv_gram_to_form")
# "Which of the following adjectival forms is/are an example of [grammar]?" (GQ: MCQ)


#
# NOUNS
#

# NOUN TO GENDER ("noun_to_gender")
# "What gender is [noun]?" (ZQ: MCQ)


# GENDER TO NOUN ("gender_to_noun")
# "Which lemma(s) is/are [noun_gender]?" (ZQ: MCQ)


# NOUN TO ANIMACY ("noun_to_anim")
# "Is [noun] animate or inanimate?" (ZQ: MCQ)


# ANIMACY TO NOUN ("anim_to_noun")
# "Which lemma(s) is/are [subst_animacy]?" (ZQ: MCQ)


# NOUN FORM + LEMMA TO GENDER/NUMBER/CASE ("noun_form_to_gram")
# "What is the gender, number, case of [adjective form]?" (GQ: MCQ)


class NounFormToGramStrategy(BaseExerciseStrategy):

    gender_col = "conj_gender"
    number_col = "gram_num"
    case_col = "subst_case"

    def generate_item_blueprints(
        self, num_items: int = 10, max_keys: int = 1, max_distractors: int = 3
    ) -> List[schemas.ItemBlueprint]:
        blueprints = []

        stmt = (
            self.get_scoped_stmt()
            .add_columns(models.Lexeme, models.GramProp)
            .join(models.WordForm, models.WordForm.lem_id == models.Lemma.id)
            .join(models.Lexeme, models.WordForm.lex_id == models.Lexeme.id)
            .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)
            #
            .where(models.Lemma.pos == models.EnumPartOfSpeech.NOUN)
            .limit(num_items)
        )
        results = self.db.execute(stmt).all()

        for Lemma, WordForm, GramProp in results:
            logger.debug(
                "Lemma, WordForm, GramProp:" "%s, %s, %s", Lemma, WordForm, GramProp
            )
            # get distractors

            # add everything to blueprints

        return blueprints


# NOUN + GNC TO FORM ("noun_gram_to_form")
# "Which of the following noun forms is/are an example of [grammar]?" (GQ: MCQ)

#
# PARTICIPLES
#


# PARTICIPLE TYPE TO LEMMA ("part_type_to_lem")
# "What form is type X?" (SQ: MCQ)


# LEMMA TO PARTICIPLE TYPE ("lem_to_part_type")
# "What type of participle is [participle]?" (GQ: MCQ)
