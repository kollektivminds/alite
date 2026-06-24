# app/backend/src/alite_backend/services/items/base.py
from abc import ABC, abstractmethod
import logging
import re
import json
import random
from collections import defaultdict
from sqlalchemy import select, func
from sqlalchemy.orm import Session, declarative_base
import logging
from typing import List, Any, Dict, Tuple, Optional
from enum import Enum
from alite_backend.db import schemas, models

logger = logging.getLogger(__name__)


class BaseExerciseStrategy(ABC):
    """Base class for creating exercises"""

    def __init__(self, db_session: Session, request_context: schemas.ExerciseContext):
        self.db = db_session
        # self.type_counts = request.type_counts
        self.context_dict = request_context.model_dump()
        self.less_list_ids = self.context_dict.get("less_list_ids", [])
        self.mod_ids = self.context_dict.get("mod_ids", [])
        self.lem_ids = self.context_dict.get("lem_ids", [])
        self.formats = self.context_dict.get("ex_formats", [])
        # self.num_items = self.context_dict.get("num_items", 10)
        self.max_keys = self.context_dict.get("max_keys", 1)
        self.max_distractors = self.context_dict.get("max_distractors", 3)

    # --- HELPER METHODS ---

    def _get_scoped_stmt(self):

        stmt = select(models.Lemma)

        if self.less_list_ids:
            stmt = stmt.join(models.LemmaInLessonList).where(
                models.LemmaInLessonList.less_list_id.in_(self.less_list_ids)
            )

        if self.mod_ids:
            stmt = (
                stmt.join(models.LemmaInLessonList)
                .join(
                    models.LessonListInModule,
                    models.LessonListInModule.less_list_id
                    == models.LemmaInLessonList.less_list_id,
                )
                .where(models.LessonListInModule.mod_id.in_(self.mod_ids))
            )

        if self.lem_ids:
            stmt = stmt.where(models.Lemma.id.in_(self.lem_ids))

        return stmt

    def _get_enum_distractors(
        self, correct_enum: Enum | bool, num_distractors: int = 3
    ) -> List:
        """to get distractors from within an enum class"""
        if isinstance(correct_enum, bool):
            return [str(not correct_enum)]
        elif isinstance(correct_enum, Enum):

            target_val = getattr(correct_enum, "value", correct_enum)

            all_options = [
                e.value for e in correct_enum.__class__ if e.value != target_val
            ]
            return random.sample(all_options, min(num_distractors, len(all_options)))

    def _format_attribute_name(self, target_attr: str) -> str:
        """_format_attribute_name translates db column names into human-readable strings

        Args:
            target_attr (str): _description_

        Returns:
            str: _description_
        """
        attribute_map = {
            "pos": "part of speech",
            "noun_gender": "grammatical gender",
            "subst_animacy": "animacy",
            "verb_aspect": "verbal aspect",
            "verb_type": "conjugation type",
            "verb_person": "person",
            "verb_trans_refl": "transitivity or reflexivity",
        }

        return attribute_map.get(
            target_attr,
            target_attr.replace("gram_", "")
            .replace("verb_", "")
            .replace("subst_", "")
            .replace("_", " "),
        )

    def _fetch_grouped_paradigms(
        self, pos_target: models.EnumPartOfSpeech, num_lemmas: int, *gram_filters
    ) -> Dict[int, List[Tuple]]:
        """
        Fetches fully joined morphological paradigms for a set of random lemmas.
        Returns a dictionary grouped by lemma.id.
        """
        # subquery: get distinct base words
        lemma_stmt = (
            self._get_scoped_stmt()
            .with_only_columns(models.Lemma.id)
            .where(models.Lemma.pos == pos_target)
            .order_by(func.random())
            .limit(num_lemmas)
        )

        # main query: the relational pathway
        stmt = (
            select(models.Lemma, models.WordForm, models.Lexeme, models.GramProp)
            .join(models.WordForm, models.WordForm.lem_id == models.Lemma.id)
            .join(models.Lexeme, models.WordForm.lex_id == models.Lexeme.id)
            .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)
            .where(models.Lemma.id.in_(lemma_stmt.scalar_subquery()))
        )

        # apply any specific grammatical filters passed by the child strategy
        if gram_filters:
            stmt = stmt.where(*gram_filters)

        results = self.db.execute(stmt).all()

        # organize by lemma.id for easy distractor picking
        grouped_results = defaultdict(list)
        for lemma, word_form, lexeme, gram_prop in results:
            grouped_results[lemma.id].append((lemma, word_form, lexeme, gram_prop))

        return grouped_results

    def _get_trait_mapping(
        self, pos_target: models.EnumPartOfSpeech, focus: schemas.EnumSubstGramExFocus
    ) -> Tuple[str, List[str]] | None:
        """
        UNIVERSAL MAPPING ENGINE: Translates an API focus selection into structural database column sets.
        Returns: (target_column_name, [list_of_static_column_names])
        """
        # Group definitions by major structural domains
        noun_cols: List[str] = ["subst_case", "gram_num"]
        adjective_cols: List[str] = noun_cols + ["gram_gender"]
        verb_cols: List[str] = [
            "gram_tense",
            "conj_person",
            "gram_num",
            "verb_mood",
            "gram_gender",
        ]
        participle_cols: List[str] = ["gram_tense", "part_type", "part_voice"]

        if pos_target == models.EnumPartOfSpeech.NOUN:
            return focus, [c for c in noun_cols if c != focus.value]
        elif pos_target == models.EnumPartOfSpeech.ADJECTIVE:
            return focus, [c for c in adjective_cols if c != focus.value]
        elif pos_target == models.EnumPartOfSpeech.VERB:
            return focus, [c for c in verb_cols if c != focus.value]
        elif pos_target == models.EnumPartOfSpeech.PARTICIPLE:
            return focus, [c for c in participle_cols if c != focus.value]

        # strat_id = r"(\w{4,5}_)(.*)$"
        # groups = re.findall(strat_id, focus.value)
        # if groups:
        #     type_cols = groups[0][0]
        #     focus_gram = groups[0][1]

        #     # 1. SUBSTANTIVES' FOCI
        #     if type_cols == "subst_":
        #         return focus, [c for c in substantive_cols if focus_gram not in c]
        #     # 2. VERBS' FOCI
        #     elif type_cols == "verb_":
        #         return focus, [c for c in verb_cols if focus_gram not in c]
        #     # 3. PARTICIPLES' FOCI
        #     elif type_cols == "part_":
        #         return focus, [c for c in participle_cols if focus_gram not in c]
        # 4. FALLBACK / MIXED GENERAL STUDY ("ALL")
        # Returning "all" signals the child generator loop to bypass variable isolation
        else:
            return "all", []

    def _format_grammar_label(
        self, gp: models.GramProp, target_attr: str, static_attrs: list
    ) -> str:
        if target_attr == "all":
            c_val = getattr(gp.subst_case, "value", "") if gp.subst_case else ""
            n_val = getattr(gp.gram_num, "value", "") if gp.gram_num else ""
            g_val = getattr(gp.gram_gender, "value", "") if gp.gram_gender else ""
            return f"{g_val} {c_val} {n_val}".strip()
        else:
            target_val = getattr(gp, target_attr)
            return getattr(target_val, "value", str(target_val))

    def _build_zero_query_drill(
        self,
        pos_target: models.EnumPartOfSpeech | None,
        target_attr: str,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        allow_odd_one_out: bool,
        drill_direction: str,  # "word_to_trait" OR "trait_to_word"
    ) -> list:
        """
        engine for creating exercises based on the lemma table
        """
        blueprints = []
        attr_name = self._format_attribute_name(target_attr)
        # fetch a buffered pool of valid lemmas
        stmt = self._get_scoped_stmt()
        
        if pos_target is not None:
            stmt = stmt.where(models.Lemma.pos == pos_target)
            
        stmt = (
            stmt.where(getattr(models.Lemma, target_attr).isnot(None))  # Ignore nulls
            .order_by(func.random())
            .limit(num_items * 4)  # heavy buffer for deduplication
        )
        lemmas = self.db.execute(stmt).scalars().all()

        # group by the target attribute
        buckets = defaultdict(list)
        for lem in lemmas:
            buckets[getattr(lem, target_attr)].append(lem)

        # a flat list of traits to pull distractors from
        all_traits = list(buckets.keys())
        if len(all_traits) < 2:
            return blueprints  # not enough variance in the database to form a question

        for baseline_lem in lemmas:
            if len(blueprints) == num_items:
                break
            lemma_id = baseline_lem.id
            baseline_trait = getattr(baseline_lem, target_attr)
            trait_str = getattr(baseline_trait, "value", str(baseline_trait))
            base_word = baseline_lem.lem_canon or baseline_lem.lem_text

            keys, distractors, prompt_text = [], [], ""

            # -----------------------------------------------------------------
            # scenario a: lemma -> trait (buttons are grammar qualities)
            # e.g., "What is the gender of 'книга'?" -> [Feminine, Masculine, Neuter]
            # -----------------------------------------------------------------
            if drill_direction == "lemma_to_trait":
                keys = [trait_str]

                # distractors are other enum traits available
                distractors = self._get_enum_distractors(
                    baseline_trait, num_distractors=max_distractors
                )

                # if len(distractors) < max_distractors:
                #     continue

                # dynamic prompt based on the attribute we are testing
                # attr_name = self._format_attribute_name(target_attr)
                prompt_text = f"Identify the {attr_name} of '{base_word}':"

            # -----------------------------------------------------------------
            # scenario b: trait -> lemma (buttons are Russian words)
            # e.g., "Which of these nouns is Feminine?" -> [книга, дом, окно]
            # -----------------------------------------------------------------
            elif drill_direction == "trait_to_lemma":
                item_is_ooo = (
                    random.choice([True, False]) if allow_odd_one_out else False
                )

                if item_is_ooo or max_keys > 1:
                    majority_trait, minority_trait = None, None
                    for trait, items in buckets.items():
                        if len(items) >= 3:
                            majority_trait = trait
                            other_traits = [t for t in buckets.keys() if t != trait]
                            if other_traits:
                                minority_trait = other_traits[0]
                            break

                    if not majority_trait or not minority_trait:
                        continue
                    maj_str = getattr(majority_trait, "value", str(majority_trait))

                    if item_is_ooo:
                        # the key is the anomaly
                        keys = [
                            getattr(k, "lem_canon", k.lem_text)
                            for k in random.sample(buckets[minority_trait], 1)
                        ]

                        pool = list(buckets[majority_trait])
                        random.shuffle(pool)
                        seen_texts = set(keys)

                        for lem in pool:
                            text = lem.lem_canon or lem.lem_text
                            if text not in seen_texts:
                                seen_texts.add(text)
                                distractors.append(text)
                            if len(distractors) == 3:
                                break

                        # if len(distractors) < 3:
                        #     continue
                        prompt_text = f"Which of these is NOT {maj_str} ({attr_name})?"

                    else:
                        # multi-select
                        keys = [
                            getattr(k, "lem_canon", k.lem_text)
                            for k in random.sample(buckets[majority_trait], max_keys)
                        ]

                        pool = list(buckets[minority_trait])
                        random.shuffle(pool)
                        seen_texts = set(keys)

                        for lem in pool:
                            text = lem.lem_canon or lem.lem_text
                            if text not in seen_texts:
                                seen_texts.add(text)
                                distractors.append(text)
                            if len(distractors) == max_distractors:
                                break

                        # if len(distractors) < max_distractors:
                        #     continue
                        prompt_text = f"Select all {maj_str} {pos_target}s:"

                else:
                    # single key: "Which word is feminine?"
                    keys = [base_word]

                    distractor_pool = []
                    for trait, items in buckets.items():
                        if trait != baseline_trait:
                            distractor_pool.extend(items)

                    random.shuffle(distractor_pool)
                    seen_texts = {base_word}

                    for lem in distractor_pool:
                        text = lem.lem_canon or lem.lem_text
                        if text not in seen_texts:
                            seen_texts.add(text)
                            distractors.append(text)
                        if len(distractors) == max_distractors:
                            break

                    # if len(distractors) < max_distractors:
                    #     continue
                    attr_name = self._format_attribute_name(target_attr)
                    prompt_text = f"Which of these words has the attribute: {trait_str} ({attr_name})?"

            if keys and distractors:
                blueprints.append(
                    {
                        "prompt": prompt_text,
                        "keys": keys,
                        "distractors": distractors,
                        "lem_id": lemma_id,
                    }
                )

        return blueprints

    def _build_paradigm_drill(
        self,
        pos_target: models.EnumPartOfSpeech,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        allowed_foci: list,
        allow_odd_one_out: bool,
        drill_direction: str = "form_to_gram",
    ) -> List[schemas.ItemBlueprint]:

        blueprints = []
        # get list of relational word objects for potential keys and distractors
        paradigms = self._fetch_grouped_paradigms(
            pos_target=pos_target, num_lemmas=num_items * 3
        )
        # loop list to analyze, filter, and arrange for list of blueprints
        for lemma_id, forms in paradigms.items():

            if len(blueprints) == num_items:
                break

            # skip word if forms are insufficient
            if not forms or len(forms) < (max_keys + max_distractors):
                continue

            # TODO: candidate for bkt
            item_focus = random.choice(allowed_foci)
            target_attr, static_attrs = self._get_trait_mapping(pos_target=pos_target, focus=item_focus)  # type: ignore

            # defective form filtering
            valid_forms = []
            for f in forms:
                gp = f[3]
                if target_attr != "all" and getattr(gp, target_attr) is None:
                    continue
                if not all(getattr(gp, attr) is not None for attr in static_attrs):
                    continue
                valid_forms.append(f)

            if not valid_forms or len(valid_forms) < (max_keys + max_distractors):
                continue

            baseline_form = random.choice(forms)
            baseline_gp = baseline_form[3]
            lemma_form = forms[0][0].lem_canon or forms[0][0].lem_text

            # dynamic inversion switch
            if drill_direction == "form_to_gram":
                # buttons show Russian words, prompt shows grammar rules.
                def get_option_text(f):  # type: ignore
                    return f[2].lex_text

                drill_prompt_target = lemma_form  # prompt asks about the base lemma
            else:
                # buttons show grammar, prompt shows Russian words.
                def get_option_text(f):
                    return self._format_grammar_label(f[3], target_attr, static_attrs)

                drill_prompt_target = baseline_form[2].lex_text

            # create pool for key and distractor selection
            if target_attr == "all":
                clean_pool = valid_forms
            else:
                clean_pool = [
                    f
                    for f in forms
                    if all(
                        getattr(f[3], attr) == getattr(baseline_gp, attr)
                        for attr in static_attrs
                    )
                ]

            # TODO: candidate for bkt
            item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False

            if drill_direction == "gram_to_form":
                item_is_ooo = False

            # odd-one-out or multi-key items
            if item_is_ooo or max_keys > 1:
                grouping_attr = target_attr
                if grouping_attr == "all":
                    # TODO: bkt candidate
                    grouping_attr = random.choice(
                        [
                            e.value
                            for e in schemas.EnumSubstGramExFocus
                            if e.value != "all"
                        ]
                    )
                # buckets to organize candidate words by attr
                buckets = defaultdict(list)
                for f in clean_pool:
                    trait_val = getattr(f[3], grouping_attr)
                    buckets[trait_val].append(f)

                # declare which trait will be key(s) /
                # distractor(s) based on item format
                majority_trait, minority_trait = None, None
                for trait, trait_forms in buckets.items():
                    if len(trait_forms) >= 3:
                        majority_trait = trait
                        other_traits = [t for t in buckets.keys() if t != trait]
                        if other_traits:
                            minority_trait = other_traits[0]
                        break

                if not majority_trait or not minority_trait:
                    continue

                maj_trait_name = getattr(majority_trait, "value", str(majority_trait))

                # ooo-specific settings
                if item_is_ooo:
                    keys = random.sample(buckets[minority_trait], 1)
                    key_strings = {get_option_text(k) for k in keys}

                    pool = list(buckets[majority_trait])
                    random.shuffle(pool)
                    distractors, seen_texts = [], set(key_strings)

                    for f in pool:
                        text = get_option_text(f)
                        if text not in seen_texts:
                            seen_texts.add(text)
                            distractors.append(f)
                        if len(distractors) == 3:
                            break

                    if len(distractors) < 3:
                        continue

                    # dynamic prompt
                    if drill_direction == "form_to_gram":
                        prompt_text = f"Which of these is NOT a {maj_trait_name} form of '{drill_prompt_target}'?"
                    else:
                        prompt_text = f"Which of these grammatical tags does NOT describe the form '{drill_prompt_target}'?"
                else:
                    # multi-select
                    keys = random.sample(buckets[majority_trait], max_keys)
                    key_strings = {get_option_text(k) for k in keys}
                    distractors = []

                    # get rid of duplicates
                    pool = list(buckets[minority_trait])
                    random.shuffle(pool)
                    seen_texts = set(key_strings)

                    for f in pool:
                        text = get_option_text(f)
                        if text not in seen_texts:
                            seen_texts.add(text)
                            distractors.append(f)
                        if len(distractors) == max_distractors:
                            break

                    if len(distractors) < max_distractors:
                        continue

                    if drill_direction == "form_to_gram":
                        prompt_text = f"Select all {maj_trait_name} forms of '{drill_prompt_target}':"
                    else:
                        # e.g., "Select all grammatical tags that apply to 'книги'" (Requires advanced logic, safe fallback)
                        prompt_text = f"Select the grammatical tags for the form '{drill_prompt_target}':"

            # scenario b: traditional single-key items
            else:
                keys = [baseline_form]
                key_text = baseline_form[2].lex_text
                distractors = []
                if target_attr == "all":
                    short_pool = [f for f in clean_pool if f[3].id != baseline_gp.id]
                else:
                    baseline_trait_val = getattr(baseline_gp, target_attr)
                    short_pool = [
                        f
                        for f in clean_pool
                        if getattr(f[3], target_attr) != baseline_trait_val
                    ]

                random.shuffle(short_pool)
                seen_texts = {key_text}

                for f in short_pool:
                    text = f[2].lex_text
                    if text not in seen_texts:
                        seen_texts.add(text)
                        distractors.append(f)
                    if len(distractors) == max_distractors:
                        break

                if len(distractors) < max_distractors:
                    continue

                if drill_direction == "gram_to_form":
                    # Buttons = Grammar Tags (Nominative, Plural). Prompt asks about the word form.
                    if target_attr == "all":
                        prompt_text = f"Identify the complete grammatical parsing for the form '{drill_prompt_target}':"
                    else:
                        clean_attr = self._format_attribute_name(target_attr)
                        prompt_text = f"What is the {clean_attr} of the form '{drill_prompt_target}'?"

                else:
                    # Buttons = Russian Words. Prompt asks about the grammar.
                    if target_attr == "all":
                        # safe extraction for GramProp values in case they are None
                        c_val = (
                            getattr(baseline_gp.subst_case, "value", "")
                            if baseline_gp.subst_case
                            else ""
                        )
                        n_val = (
                            getattr(baseline_gp.gram_num, "value", "")
                            if baseline_gp.gram_num
                            else ""
                        )

                        # trim extra spaces if one is missing
                        desc = f"{c_val} {n_val}".strip()
                        prompt_text = f"Identify the {desc} form of '{lemma_form}':"
                    else:
                        baseline_trait_val = getattr(baseline_gp, target_attr)
                        target_str = getattr(
                            baseline_trait_val, "value", str(baseline_trait_val)
                        )

                        # safe extraction for static traits
                        static_descriptions = ", ".join(
                            [
                                getattr(getattr(baseline_gp, attr), "value", "")
                                for attr in static_attrs
                                if getattr(baseline_gp, attr)
                            ]
                        )
                        prompt_text = f"Identify the ({static_descriptions}) {target_str} of '{lemma_form}':"

            if keys and distractors:
                blueprints.append(
                    {
                        "prompt": prompt_text,
                        "keys": [get_option_text(k) for k in keys],
                        "distractors": [get_option_text(d) for d in distractors],
                        "lem_id": lemma_id,
                    }
                )

        return blueprints

    # --- ABSTRACT METHOD ---

    @abstractmethod
    def generate_item_blueprints(
        self,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        config: schemas.StrategyConfigs | None = None,
    ) -> List[schemas.ItemBlueprint]:
        """generate_item_blueprints _summary_

        Args:
            limit (int): _description_
            max_distractors (int): _description_

        Returns:
            List[schemas.ItemBlueprint]: _description_
        """
        pass
