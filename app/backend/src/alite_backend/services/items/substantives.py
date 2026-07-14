# app/backend/src/alite_backend/services/items/nouns.py
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
# SQ = sibling query (lemmas+pronunciations/definitions-based)
# GQ = grammar query (gram_props-based)
# RQ = (lemma) relationship query (lem_rels-based)

#
# ADJECTIVES
#

# adjective + type to form ("adjv_type_to_form")
# "What is the [comparative | superlative] form of [lemma_adjective]?" (SQ: MCQ/Cloze)


class AdjvTypeToFormStrategy(BaseExerciseStrategy):
    pass


# adjective form to type ("type_form_to_adjv")
# "What is the base form of [adjective type form]?" (GQ: Cloze)


class AdjvFormToTypeStrategy(BaseExerciseStrategy):
    pass


# adjective form to grammar ("adjv_form_to_gram")
# "What is the [gender, number, case] of [adjective form]?" (GQ: MCQ)


class AdjvFormToGramStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        foci = (
            config.strategies.get(
                "substantives", [e.value for e in schemas.EnumGramExFocus]
            )
            if config and config.strategies
            else [e.value for e in schemas.EnumGramExFocus]
        )

        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_paradigm_drill(
            pos_target=models.EnumPartOfSpeech.ADJECTIVE,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allowed_foci=foci,
            allow_odd_one_out=allow_ooo,
            drill_direction="form_to_gram",
        )


# adjective grammar to form ("adjv_gram_to_form")
# "Which of the following adjectival forms is/are an example of [grammar]?" (GQ: MCQ)


class AdjvGramToFormStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        foci = (
            config.strategies.get(
                "substantives", [e.value for e in schemas.EnumGramExFocus]
            )
            if config and config.strategies
            else [e.value for e in schemas.EnumGramExFocus]
        )

        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_paradigm_drill(
            pos_target=models.EnumPartOfSpeech.ADJECTIVE,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allowed_foci=foci,
            allow_odd_one_out=allow_ooo,
            drill_direction="gram_to_form",
        )


#
# NOUNS
#

# noun to gender ("noun_to_gender")
# "What is the gender of [lemma_noun]?" (ZQ: MCQ)


class NounToGenderStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            target_attr="noun_gender",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",  # Prompts: "Identify the gender of 'книга'"
        )


# gender to noun ("gender_to_noun")
# "Which lemma(s) is/are [noun_gender]?" (ZQ: MCQ)


class GenderToNounStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            target_attr="noun_gender",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",  # Prompts: "Which of the following is feminine?"
        )


# noun to animacy ("noun_to_anim")
# "Is [noun] animate or inanimate?" (ZQ: MCQ)


class NounToAnimacyStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            target_attr="noun_animacy",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="lemma_to_trait",  # Prompts: "Identify the gender of 'книга'"
        )


# animacy to noun ("anim_to_noun")
# "Which lemma(s) is/are [noun_animacy]?" (ZQ: MCQ)


class AnimacyToNounStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_zero_query_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            target_attr="noun_animacy",
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allow_odd_one_out=allow_ooo,
            drill_direction="trait_to_lemma",  # Prompts: "Identify the gender of 'книга'"
        )


# NOUN FORM + LEMMA TO GENDER/NUMBER/CASE ("noun_form_to_gram")
# "What is the gender, number, case of [adjective form]?" (GQ: MCQ)


class NounFormToGramStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        foci = (
            config.strategies.get(
                "substantives", [e.value for e in schemas.EnumGramExFocus]
            )
            if config and config.strategies
            else [e.value for e in schemas.EnumGramExFocus]
        )
        foci = [f for f in foci if f != "subst_gender"]

        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_paradigm_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allowed_foci=foci,
            allow_odd_one_out=allow_ooo,
            drill_direction="form_to_gram",
        )


# class NounFormToGramStrategy(BaseExerciseStrategy):

#     def generate_item_blueprints(
#         self,
#         num_items: int = 10,
#         max_keys: int = 1,
#         max_distractors: int = 3,
#         config: schemas.StrategyConfigs | None = None,
#     ) -> List[schemas.ItemBlueprint]:
#         blueprints = []
#         allowed_foci = (
#             config.strategies["substantives"]
#             if config and config.strategies and "substantives" in config.strategies
#             else [e.value for e in schemas.EnumGramExFocus]
#         )
#         allow_odd_one_out = config.allow_odd_one_out if config else False

#         # target lemma/grammar data
#         paradigms = self._fetch_grouped_paradigms(
#             pos_target=models.EnumPartOfSpeech.NOUN, num_lemmas=num_items * 3
#         )
#         # for each lemma+grammar: identify key, fetch distractors, make prompt, add to master list
#         for lemma_id, forms in paradigms.items():
#             if len(blueprints) == num_items:
#                 break

#             if not forms or len(forms) < (max_keys + max_distractors):
#                 continue

#             item_focus = random.choice(allowed_foci)
#             target_attr, static_attrs = self._get_trait_mapping(item_focus)

#             keys = []
#             distractors = []
#             prompt_text = ""
#             lemma_form = (
#                 forms[0][0].lem_text
#                 if forms[0][0].lem_canon is None
#                 else forms[0][0].lem_canon
#             )

#             # pedagogical control
#             baseline_form = random.choice(forms)
#             baseline_gp = baseline_form[3]

#             if target_attr == "all":
#                 clean_pool = forms
#             else:
#                 clean_pool = [
#                     f
#                     for f in forms
#                     if all(
#                         getattr(f[3], attr) == getattr(baseline_gp, attr)
#                         for attr in static_attrs
#                     )
#                 ]

#             item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False

#             # # SCENARIO A: ODD-ONE-OUT OR MULTI-SELECT BLUEPRINTS
#             if item_is_ooo or max_keys > 1:
#                 grouping_attr = target_attr
#                 if grouping_attr == "all":
#                     grouping_attr = random.choice(
#                         [
#                             e.value
#                             for e in schemas.EnumSubstGramExFocus
#                             if e.value != "all"
#                         ]
#                     )
#                 buckets = defaultdict(list)
#                 for f in clean_pool:
#                     trait_val = getattr(f[3], grouping_attr)
#                     buckets[trait_val].append(f)

#                 majority_trait, minority_trait = None, None
#                 for trait, trait_forms in buckets.items():
#                     if len(trait_forms) >= 3:
#                         majority_trait = trait
#                         other_traits = [t for t in buckets.keys() if t != trait]
#                         if other_traits:
#                             minority_trait = other_traits[0]
#                         break

#                 if not majority_trait or not minority_trait:
#                     continue

#                 maj_trait_name = getattr(majority_trait, "value", str(majority_trait))

#                 if item_is_ooo:
#                     keys = random.sample(buckets[minority_trait], 1)
#                     key_strings = {k[2].lex_text for k in keys}

#                     # get rid of duplicates
#                     pool = list(buckets[majority_trait])
#                     random.shuffle(pool)
#                     seen_texts = set(
#                         key_strings
#                     )  # seed with key spellings to prevent overlap

#                     for f in pool:
#                         text = f[2].lex_text
#                         if text not in seen_texts:
#                             seen_texts.add(text)
#                             distractors.append(f)
#                         if len(distractors) == 3:
#                             break

#                     if len(distractors) < 3:
#                         continue  # Drained by syncretism, skip word safely

#                     prompt_text = f"Which of these is NOT a {majority_trait} form of '{lemma_form}'?"

#                 else:
#                     # Multi-select
#                     keys = random.sample(buckets[majority_trait], max_keys)
#                     key_strings = {k[2].lex_text for k in keys}

#                     # get rid of duplicates
#                     pool = list(buckets[minority_trait])
#                     random.shuffle(pool)
#                     seen_texts = set(key_strings)

#                     for f in pool:
#                         text = f[2].lex_text
#                         if text not in seen_texts:
#                             seen_texts.add(text)
#                             distractors.append(f)
#                         if len(distractors) == max_distractors:
#                             break

#                     if len(distractors) < max_distractors:
#                         continue

#                     prompt_text = (
#                         f"Select all {maj_trait_name} forms of '{lemma_form}':"
#                     )

#             # # SCENARIO B: TRADITIONAL SINGLE-KEY BLUEPRINTS
#             else:
#                 keys = [baseline_form]
#                 key_text = baseline_form[2].lex_text

#                 if target_attr == "all":
#                     raw_pool = [f for f in clean_pool if f[3].id != baseline_gp.id]
#                 else:
#                     baseline_trait_val = getattr(baseline_gp, target_attr)
#                     raw_pool = [
#                         f
#                         for f in clean_pool
#                         if getattr(f[3], target_attr) != baseline_trait_val
#                     ]

#                 random.shuffle(raw_pool)
#                 seen_texts = {key_text}

#                 for f in raw_pool:
#                     text = f[2].lex_text
#                     if text not in seen_texts:
#                         seen_texts.add(text)
#                         distractors.append(f)
#                     if len(distractors) == max_distractors:
#                         break

#                 if len(distractors) < max_distractors:
#                     continue

#                 if target_attr == "all":
#                     # safe extraction for GramProp values in case they are None
#                     c_val = (
#                         getattr(baseline_gp.subst_case, "value", "")
#                         if baseline_gp.subst_case
#                         else ""
#                     )
#                     n_val = (
#                         getattr(baseline_gp.gram_num, "value", "")
#                         if baseline_gp.gram_num
#                         else ""
#                     )

#                     # trim extra spaces if one is missing
#                     desc = f"{c_val} {n_val}".strip()
#                     prompt_text = f"Identify the {desc} form of '{lemma_form}':"
#                 else:
#                     baseline_trait_val = getattr(baseline_gp, target_attr)
#                     target_str = getattr(
#                         baseline_trait_val, "value", str(baseline_trait_val)
#                     )

#                     # safe extraction for static traits
#                     static_descriptions = ", ".join(
#                         [
#                             getattr(getattr(baseline_gp, attr), "value", "")
#                             for attr in static_attrs
#                             if getattr(baseline_gp, attr)
#                         ]
#                     )
#                     prompt_text = f"Identify the {target_str} of '{lemma_form}' ({static_descriptions}):"

#             # build and append blueprint
#             if keys and distractors:
#                 blueprints.append(
#                     {
#                         "prompt": prompt_text,
#                         # Map the tuples back to their Lexeme text values
#                         "keys": [k[2].lex_text for k in keys],
#                         "distractors": [d[2].lex_text for d in distractors],
#                     }
#                 )

#         return blueprints


# NOUN + GNC TO FORM ("noun_gram_to_form")
# "Which of the following noun forms is/are an example of [grammar]?" (GQ: MCQ)


class NounGramToFormStrategy(BaseExerciseStrategy):
    def generate_item_blueprints(
        self, num_items=10, max_keys=1, max_distractors=3, config=None
    ):
        foci = (
            config.strategies.get(
                "substantives", [e.value for e in schemas.EnumGramExFocus]
            )
            if config and config.strategies
            else [e.value for e in schemas.EnumGramExFocus]
        )
        foci = [f for f in foci if f != "subst_gender"]

        allow_ooo = config.allow_odd_one_out if config else False

        return self._build_paradigm_drill(
            pos_target=models.EnumPartOfSpeech.NOUN,
            num_items=num_items,
            max_keys=max_keys,
            max_distractors=max_distractors,
            allowed_foci=foci,
            allow_odd_one_out=allow_ooo,
            drill_direction="gram_to_form",
        )


# NOUN TO DIMINUTIVE FORM ("noun_to_dmun_form")
# "What is the diminutive form of [lemma_noun]?" (GQ: MCQ/Cloze)


class NounToDiminutiveStrategy(BaseExerciseStrategy):
    pass


#
# PARTICIPLES
#


# PARTICIPLE TYPE TO FORM ("part_type_to_form")
# "Which of the following is [participle type] of [verb_lemma]" (GQ: MCQ/Cloze)


class ParticpleTypeToForm(BaseExerciseStrategy):
    pass


# FORM TO PARTICIPLE TYPE ("form_to_part_type")
# "What type of participle is [participle form]?" (GQ: MCQ)


class ParticipleFormToType(BaseExerciseStrategy):
    pass
