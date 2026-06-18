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

    def get_scoped_stmt(self):

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

    def get_enum_distractors(self, correct_enum: Enum, num_distractors: int):
        """To get distractors with an enum class"""
        all_options = [
            e.value for e in correct_enum.__class__ if e != correct_enum.value
        ]
        return random.sample(all_options, min(num_distractors, len(all_options)))

    def _fetch_grouped_paradigms(
        self, pos_target: models.EnumPartOfSpeech, num_lemmas: int, *gram_filters
    ) -> Dict[int, List[Tuple]]:
        """
        Fetches fully joined morphological paradigms for a set of random lemmas.
        Returns a dictionary grouped by lemma.id.
        """
        # subquery: get distinct base words
        lemma_stmt = (
            self.get_scoped_stmt()
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

    def _get_trait_mapping(self, focus: str) -> Tuple[str, List[str]] | None:
        """
        UNIVERSAL MAPPING ENGINE: Translates an API focus selection into structural database column sets.
        Returns: (target_column_name, [list_of_static_column_names])
        """
        # Group definitions by major structural domains
        substantive_cols: List[str] = ["subst_case", "gram_num", "gram_gender"]
        verb_cols: List[str] = [
            "gram_tense",
            "conj_person",
            "gram_num",
            "verb_mood",
            "gram_gender",
        ]
        participle_cols: List[str] = ["gram_tense", "part_type", "part_voice"]

        strat_id = r"(subst_)(.*)$"
        groups = re.findall(strat_id, focus)
        if groups:
            type_cols = groups[0][0]
            focus_gram = groups[0][1]

            # 1. SUBSTANTIVES' FOCI
            if type_cols == "subst_":
                return focus, [c for c in substantive_cols if focus_gram not in c]
            # 2. VERBS' FOCI
            elif type_cols == "verb_":
                return focus, [c for c in verb_cols if focus_gram not in c]
            # 3. PARTICIPLES' FOCI
            elif type_cols == "part_":
                return focus, [c for c in participle_cols if focus_gram not in c]
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
            # exit if enough blueprints have been made already
            if len(blueprints) == num_items:
                break
            # skip word if forms are insufficient
            # for an item's total options
            if not forms or len(forms) < (max_keys + max_distractors):
                continue
            # TODO: candidate for BKT algo
            item_focus = random.choice(allowed_foci)
            target_attr, static_attrs = self._get_trait_mapping(focus=item_focus)  # type: ignore

            baseline_form = random.choice(forms)
            baseline_gp = baseline_form[3]
            lemma_form = forms[0][0].lem_canon or forms[0][0].lem_text

            # -----------------------------------------------------------------
            # THE DYNAMIC INVERSION SWITCH
            # Justification: By defining these lambda-like extractors here,
            # the exact same collision logic works perfectly for BOTH strategies.
            # -----------------------------------------------------------------
            if drill_direction == "gram_to_form":
                # Buttons show Russian words. Prompt shows Grammar rules.
                def get_option_text(f):  # type: ignore
                    return f[2].lex_text

                drill_prompt_target = lemma_form  # Prompt asks about the base lemma
            else:
                # Buttons show Grammar rules. Prompt shows Russian words.
                def get_option_text(f):
                    return self._format_grammar_label(f[3], target_attr, static_attrs)

                drill_prompt_target = baseline_form[
                    2
                ].lex_text  # Prompt asks about the specific inflected text

            # pedagogical control for item creation
            baseline_form = random.choice(forms)
            baseline_gp = baseline_form[3]

            # create pool for key and distractor selection
            if target_attr == "all":
                clean_pool = forms
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
                    key_strings = {
                        get_option_text(k) for k in keys
                    }  # <-- USING DYNAMIC EXTRACTOR

                    pool = list(buckets[majority_trait])
                    random.shuffle(pool)
                    distractors, seen_texts = [], set(key_strings)

                    for f in pool:
                        text = get_option_text(f)  # <-- USING DYNAMIC EXTRACTOR
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
                    key_strings = {k[2].lex_text for k in keys}
                    distractors = []

                    # get rid of duplicates
                    pool = list(buckets[minority_trait])
                    random.shuffle(pool)
                    seen_texts = set(key_strings)

                    for f in pool:
                        text = f[2].lex_text
                        if text not in seen_texts:
                            seen_texts.add(text)
                            distractors.append(f)
                        if len(distractors) == max_distractors:
                            break

                    if len(distractors) < max_distractors:
                        continue

                    prompt_text = (
                        f"Select all {maj_trait_name} forms of '{lemma_form}':"
                    )

            # # SCENARIO B: TRADITIONAL SINGLE-KEY BLUEPRINTS
            else:
                keys = [baseline_form]
                key_text = baseline_form[2].lex_text
                distractors = []
                if target_attr == "all":
                    raw_pool = [f for f in clean_pool if f[3].id != baseline_gp.id]
                else:
                    baseline_trait_val = getattr(baseline_gp, target_attr)
                    raw_pool = [
                        f
                        for f in clean_pool
                        if getattr(f[3], target_attr) != baseline_trait_val
                    ]

                random.shuffle(raw_pool)
                seen_texts = {key_text}

                for f in raw_pool:
                    text = f[2].lex_text
                    if text not in seen_texts:
                        seen_texts.add(text)
                        distractors.append(f)
                    if len(distractors) == max_distractors:
                        break

                if len(distractors) < max_distractors:
                    continue

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
                    prompt_text = f"Identify the {target_str} of '{lemma_form}' ({static_descriptions}):"

            if keys and distractors:
                blueprints.append(
                    {
                        "prompt": prompt_text,
                        "keys": [get_option_text(k) for k in keys],
                        "distractors": [get_option_text(d) for d in distractors],
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
