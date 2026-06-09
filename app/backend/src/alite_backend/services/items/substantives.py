# app/backend/src/alite_backend/services/items/nouns.py
from typing import List
import random
from collections import defaultdict
import logging
from sqlalchemy import select, func
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

    def generate_item_blueprints(
        self,
        num_items: int = 10,
        max_keys: int = 1,
        max_distractors: int = 3,
        config: schemas.NounStrategyConfig | None = None,
    ) -> List[schemas.ItemBlueprint]:
        blueprints = []
        allowed_foci = (
            config.focus_props
            if config and config.focus_props
            else schemas.EnumGramExFocus.ALL
        )
        allow_odd_one_out = config.is_odd_one_out if config else False

        # target lemma/grammar data
        paradigms = self._fetch_grouped_paradigms(
            pos_target=models.EnumPartOfSpeech.NOUN, num_lemmas=num_items
        )
        # for each lemma/grammar: id key, fetch distractors, make prompt, add to master list
        for lemma_id, forms in paradigms.items():
            if not forms or len(forms) < (max_keys + max_distractors):
                continue
            
            item_focus = random.choice(allowed_foci)
            target_attr, static_attrs = self._get_trait_mapping(item_focus)
            
            
            
            keys = []
            distractors = []
            prompt_text = ""
            base_word = forms[0][0].lem_canon
            
            # SCENARIO A: ONE-OUT-OUT OR MULTI-SELECT BLUEPRINTS
            if (is_odd_one_out or max_keys > 1):
                if focus
            
            # SCENARIO B: TRADITIONAL SINGLE-KEY BLUEPRINTS
            else:
                key_tuple = random.choice(forms)
                keys = [key_tuple]
                
                if focus == schemas.EnumGramExFocus.SUBST_CASE:
                    # Drill Case: Distractors have different case, same number
                    pool = [f for f in forms if f[3].subst_case != key_tuple[3].subst_case and f[3].gram_num == key_tuple[3].gram_num]
                else:
                    pool = [f for f in forms if f[3].id != key_tuple[3].id]

                distractors = random.sample(pool, min(max_distractors, len(pool)))
                prompt_text = f"Identify the {key_tuple[3].subst_case} {key_tuple[3].gram_num} of '{base_word}':"


            # -----------------------------------------------------------------
            # BUILD AND APPEND THE BLUEPRINT
            # -----------------------------------------------------------------
            if keys and distractors:
                blueprints.append({
                    "prompt": prompt_text,
                    # Map the tuples back to their Lexeme text values
                    "keys": [k[2].lex_text for k in keys],
                    "distractors": [d[2].lex_text for d in distractors]
                })

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
