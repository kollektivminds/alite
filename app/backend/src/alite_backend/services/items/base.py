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
            "noun_animacy": "animacy",
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
        # group definitions by major structural domains
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

        else:
            return "all", []

    def _filter_valid_forms(
        self,
        forms: List[Tuple],
        pos_target: models.EnumPartOfSpeech,
        target_attr: str,
        static_attrs: List[str],
    ) -> List[Tuple]:
        def _is_valid(gram_prop: models.GramProp) -> bool:
            # if we are testing a specific attribute (not "all"),
            # the row MUST have a value for that attribute

            # the row MUST also have valid values for all contextual attributes
            if pos_target == "adjective":
                if not any(
                    getattr(gram_prop, attr) is not None for attr in static_attrs
                ):
                    return False
            else:
                if target_attr != "all" and getattr(gram_prop, target_attr) is None:
                    return False
                if not all(
                    getattr(gram_prop, attr) is not None for attr in static_attrs
                ):
                    return False

            return True

        # return a new list containing only the tuples where the 4th element (GramProp)
        return [row for row in forms if _is_valid(gram_prop=row[3])]

    def _extract_option_text(self, item_tuple: Tuple, drill_direction: str) -> str:
        """
        Extracts the user-facing string from the raw database tuple based on the drill type.
        """
        lemma, word_form, lexeme, gram_prop = item_tuple

        # if the drill shows words and asks for grammar, the options are the grammar tags.
        # if the drill asks for a word based on a grammar prompt, the options are the words.
        if drill_direction == "form_to_gram":
            return self._format_attribute_name(gram_prop)
        else:
            return lexeme.lex_text or lexeme.lex_text_clean

    def _get_paradigm_option_text(
        self,
        item_tuple: Tuple,
        drill_direction: str,
        target_attr: str,
        static_attrs: List[str],
    ) -> str:
        """
        Extracts the user-facing option string from the raw database tuple.
        """
        # Unpack the standard paradigm tuple
        lemma, word_form, lexeme, gram_prop = item_tuple

        if drill_direction == "form_to_gram":
            return self._format_grammar_label(gram_prop, target_attr, static_attrs)
        else:
            return lexeme.lex_text or lexeme.lex_text_clean

    def _generate_paradigm_prompt(
        self, baseline_form: Tuple, drill_direction: str, target_attr: str
    ) -> str:
        """
        Generates the instructional prompt for a paradigm-based item.
        """
        lemma, word_form, lexeme, gram_prop = baseline_form

        # Determine the base word to display (fallback to lem_text if canon is null)
        base_word = lemma.lem_canon or lemma.lem_text

        if drill_direction == "form_to_gram":
            # user sees a Russian word and must select its grammatical properties.
            if target_attr == "all":
                return f"Identify the complete grammatical parsing for the form '{word_form.text}':"
            else:
                # E.g., "What is the subst_case of..." -> "What is the case of..."
                clean_attr = self._format_attribute_name(target_attr)
                return f"What is the {clean_attr} of the form '{lexeme.lex_text or lexeme.lex_text_clean}'?"

        else:
            # user sees a grammatical description and must select the matching Russian word.
            if target_attr == "all":
                # e.g., "Identify the Feminine Accusative Singular form of 'книга':"
                desc = self._format_grammar_label(gram_prop, target_attr, [])
                return f"Identify the {desc} form of '{base_word}':"
            else:
                # testing a specific trait (e.g., Nominative)
                target_val = getattr(gram_prop, target_attr)
                target_str = getattr(target_val, "value", str(target_val))

                # loop through getattr(gram_prop, attr) to build a combined string.
                return f"Identify the {target_str} form of '{base_word}':"

    def _generate_single_key_paradigm(
        self,
        valid_forms: List[Tuple],
        baseline_form: Tuple,
        target_attr: str,
        static_attrs: List[str],
        max_distractors: int,
        drill_direction: str,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates a standard multiple-choice paradigm question with one correct answer."""

        # Unpack the baseline to access its grammatical properties
        _, _, _, base_gp = baseline_form

        # filter the pool for valid distractors.
        # a valid distractor matches all static attributes but differs on the target attribute.
        distractor_pool = []
        for form in valid_forms:
            _, _, _, gp = form

            # skip the baseline itself (and any identical syncretic forms)
            if form == baseline_form:
                continue

            # must match all static attributes (e.g., if baseline is plural, distractor must be plural)
            if not all(
                getattr(gp, attr) == getattr(base_gp, attr) for attr in static_attrs
            ):
                continue

            # must differ on the target attribute (e.g., nominative vs genitive)
            if target_attr != "all" and getattr(gp, target_attr) == getattr(
                base_gp, target_attr
            ):
                continue

            # If target_attr is 'all', it just needs to differ somewhere in the paradigm
            if target_attr == "all" and gp == base_gp:
                continue

            distractor_pool.append(form)

        # graceful degradation: Ensure we have enough distractors to make a viable question
        if len(distractor_pool) < max_distractors:
            return None

        # sample exactly what we need
        distractors = random.sample(distractor_pool, max_distractors)

        # generate the localized prompt (e.g., "Find the Genitive Plural form of X")
        prompt_text = self._generate_paradigm_prompt(
            baseline_form, drill_direction, target_attr
        )

        # build and return the blueprint
        return schemas.ItemBlueprint(
            prompt=prompt_text,
            keys=[
                self._get_paradigm_option_text(
                    baseline_form, drill_direction, target_attr, static_attrs
                )
            ],
            distractors=[
                self._get_paradigm_option_text(
                    d, drill_direction, target_attr, static_attrs
                )
                for d in distractors
            ],
            lem_id=baseline_form[0].id,
        )

    def _generate_multiselect_paradigm(
        self,
        valid_forms: List[Tuple],
        baseline_form: Tuple,
        target_attr: str,
        static_attrs: List[str],
        max_keys: int,
        max_distractors: int,
        drill_direction: str,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates a multi-select paradigm question with 1 to N correct answers."""

        _, _, _, base_gp = baseline_form

        key_pool = []
        distractor_pool = []

        # partition the valid forms into potential keys and distractors
        for form in valid_forms:
            _, _, _, gp = form

            # Must match static attributes to belong in this specific question's universe
            if not all(
                getattr(gp, attr) == getattr(base_gp, attr) for attr in static_attrs
            ):
                continue

            # If it matches the target attribute, it's a key. Otherwise, it's a distractor.
            if target_attr == "all" or getattr(gp, target_attr) == getattr(
                base_gp, target_attr
            ):
                key_pool.append(form)
            else:
                distractor_pool.append(form)

        # graceful degradation: Check if we have enough total options to make the item
        # we need at least 1 key (the baseline is guaranteed, but let's be safe) and enough distractors
        if not key_pool or len(distractor_pool) < max_distractors:
            return None

        # sample the pools
        # cap the number of keys at max_keys, ensuring baseline is included if we want it guaranteed
        num_keys_to_pick = min(len(key_pool), max_keys)
        keys = random.sample(key_pool, num_keys_to_pick)
        distractors = random.sample(distractor_pool, max_distractors)

        prompt_text = self._generate_paradigm_prompt(
            baseline_form, drill_direction, target_attr
        )

        return schemas.ItemBlueprint(
            prompt=prompt_text,
            keys=[
                self._get_paradigm_option_text(
                    k, drill_direction, target_attr, static_attrs
                )
                for k in keys
            ],
            distractors=[
                self._get_paradigm_option_text(
                    d, drill_direction, target_attr, static_attrs
                )
                for d in distractors
            ],
            lem_id=baseline_form[0].id,
        )

    def _build_ooo_prompt(
        self, shared_forms: List[Tuple], target_attr: str, drill_direction: str
    ) -> str:
        """
        Generates the instruction prompt for an odd-one-out question.
        """
        # to be explicit about what pattern they are looking for,
        # we grab the grammatical property of the shared forms to state the pattern.
        _, _, _, shared_gp = shared_forms[0]

        if target_attr == "all":
            return "Which of the following forms does not belong?"

        # if we are testing a specific attribute (like case), we can build a specific prompt.
        # e.g., getattr(shared_gp, 'subst_case') might return 'gen'
        target_value = getattr(shared_gp, target_attr)

        return f"Which word is NOT {target_value.value.lower()}?"

    def _generate_ooo_paradigm(
        self,
        valid_forms: List[Tuple],
        baseline_form: Tuple,
        target_attr: str,
        static_attrs: List[str],
        max_keys: int,
        max_distractors: int,
        drill_direction: str,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates an odd-one-out morphology question."""

        # determine the grouping attribute (bkt decision point for 'all')
        grouping_attr = target_attr
        if grouping_attr == "all":
            grouping_attr = random.choice(
                [e.value for e in schemas.EnumSubstGramExFocus if e.value != "all"]
            )

        # bucket the forms by the target grammatical trait
        buckets = defaultdict(list)
        for lemma, word_form, lexeme, gram_prop in valid_forms:
            trait_val = getattr(gram_prop, grouping_attr)
            buckets[trait_val].append((lemma, word_form, lexeme, gram_prop))

        # verify there is at least one trait with 3+ items (distractors) and one with 1 item (the key)
        majority_trait, minority_trait = None, None
        for trait, trait_forms in buckets.items():
            if len(trait_forms) >= 3:
                majority_trait = trait
                other_traits = [t for t in buckets.keys() if t != trait]
                if other_traits:
                    minority_trait = other_traits[0]
                break

        if not majority_trait or not minority_trait:
            return None

        # pick the distractors (the majority group)
        # pool = list(buckets[majority_trait])
        # random.shuffle(pool)
        # distractors = pool[: max_distractors + 1]

        # build prompt and text options based on direction
        prompt_text = self._build_ooo_prompt(
            shared_forms=buckets[majority_trait],
            target_attr=target_attr,
            drill_direction=drill_direction,
        )

        # pick the odd-one-out (the key)
        key_tuple = random.choice(buckets[minority_trait])

        _, _, key_lexeme, _ = key_tuple

        key_text = key_lexeme.lex_text or key_lexeme.lex_text_clean

        # distractor_texts = [
        #     self._get_paradigm_option_text(
        #         d, drill_direction, target_attr, static_attrs
        #     )
        #     for d in distractors
        # ]

        seen_texts = {key_text}
        distractor_texts = []

        # 4. Safely Extract Distractors
        # Shuffle the majority bucket so we don't always grab the first N items
        pool = list(buckets[majority_trait])
        random.shuffle(pool)

        for form_tuple in pool:
            _, _, dist_lexeme, _ = form_tuple
            dist_text = dist_lexeme.lex_text or dist_lexeme.lex_text_clean

            # Only add to our distractors if the surface string is entirely unique
            if dist_text not in seen_texts:
                seen_texts.add(dist_text)
                distractor_texts.append(dist_text)

            # Break early once we hit the required number of distractors
            if len(distractor_texts) == max_distractors:
                break

        # 5. Graceful Degradation Check
        # Because of deduplication, we might run out of unique words before hitting max_distractors
        if len(distractor_texts) < max_distractors:
            return None

        return schemas.ItemBlueprint(
            prompt=prompt_text,
            keys=[key_text],
            distractors=distractor_texts,
            lem_id=key_tuple[0].id,
        )

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
        drill_direction: str,  # "lemma_to_trait" OR "trait_to_lemma"
    ) -> List[schemas.ItemBlueprint]:
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
            if len(blueprints) >= num_items:
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
                bp = schemas.ItemBlueprint(
                    prompt=prompt_text,
                    keys=keys,
                    distractors=distractors,
                    lem_id=lemma_id,
                )
                blueprints.append(bp)

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
            pos_target=pos_target, num_lemmas=num_items * 5
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
            valid_forms = self._filter_valid_forms(
                forms, pos_target, target_attr, static_attrs
            )

            if not valid_forms or len(valid_forms) < (max_keys + max_distractors):
                continue

            baseline_form = random.choice(valid_forms)

            # TODO: candidate for bkt
            item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False

            if drill_direction == "gram_to_form":
                item_is_ooo = False

            if item_is_ooo:
                bp = self._generate_ooo_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_keys,
                    max_distractors,
                    drill_direction,
                )
            elif max_keys > 1:
                bp = self._generate_multiselect_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_keys,
                    max_distractors,
                    drill_direction,
                )
            else:
                bp = self._generate_single_key_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_distractors,
                    drill_direction,
                )

            if bp:
                blueprints.append(bp)

        return blueprints

    def _build_sibling_query_drill(
        self,
        target_model: Any,
        target_column: str,
        junction_model: Any,
        junction_column: str,
        target_pos: models.EnumPartOfSpeech | None,
        num_items: int = 10,
        max_keys: int = 1,
        max_distractors: int = 3,
        allow_odd_one_out: bool = False,
        drill_direction: str = "lemma_to_sibling",
    ) -> List[schemas.ItemBlueprint]:
        """
        Builds an item by joining the Lemma table to a related 'sibling' table
        (e.g., Definitions, Pronunciations) via a foreign key.
        """

        blueprints = []

        stmt = self._get_scoped_stmt()

        stmt = stmt.join(junction_model, models.Lemma.id == junction_model.lem_id).join(
            target_model, target_model.id == getattr(junction_model, junction_column)
        )

        if target_pos:
            stmt = stmt.filter(models.Lemma.pos == target_pos)

        stmt = stmt.order_by(func.random()).limit(num_items * 4)

        # ---------------------------------------------------------
        # DIAGNOSTIC TRIPWIRE: Expose the SQL and the DB state
        # ---------------------------------------------------------

        # 1. Compile the query to exact SQL with literal values bound
        # try:
        #     compiled_sql = stmt.compile(
        #         dialect=self.db.bind.dialect, compile_kwargs={"literal_binds": True}
        #     )
        #     logger.error(
        #         f"\n--- SIBLING DRILL SQL ---\n{compiled_sql}\n-------------------------\n"
        #     )
        # except Exception as e:
        #     logger.error(f"Could not compile SQL: {e}")

        # # 2. Verify the API's session can actually see the junction table data
        # raw_junction_count = self.db.execute(
        #     select(func.count()).select_from(junction_model)
        # ).scalar()

        # raw_target_count = self.db.execute(
        #     select(func.count()).select_from(target_model)
        # ).scalar()

        # logger.error(
        #     f"API DB SESSION SEES: "
        #     f"{raw_junction_count} rows in {junction_model.__name__}, "
        #     f"{raw_target_count} rows in {target_model.__name__}"
        # )
        # ---------------------------------------------------------

        candidates = self.db.scalars(stmt).unique().all()
        if len(candidates) < num_items:
            if len(candidates) < num_items:
                pos_label = target_pos if target_pos != None else "any"
                logger.warning(
                    f"Requested {num_items} items for {target_model.__name__}, "
                    f"but only found {len(candidates)} valid '{pos_label}' lemmas in DB."
                )
                num_items = len(candidates)
                if num_items == 0:
                    return []
            # raise ValueError(
            #     f"Not enough {target_pos} lemmas with {target_model.__name__} data to generate {num_items} items."
            # )

        for lemma in candidates:
            if len(blueprints) >= num_items:
                break
            # fetch the siblings (definitions / pronunciations) utilizing the scoped statement
            sibling_stmt = (
                select(target_model)
                .join(junction_model)
                .filter(junction_model.lem_id == lemma.id)
            )
            siblings = self.db.scalars(sibling_stmt).all()
            sibling_values = [getattr(s, target_column) for s in siblings]

            item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False

            if drill_direction == "sibling_to_lemma" and not item_is_ooo:
                distractor_stmt = (
                    select(models.Lemma)
                    .join(
                        junction_model
                    )  # Ensure the distractor word actually has entries
                    .filter(models.Lemma.pos == lemma.pos, models.Lemma.id != lemma.id)
                    .order_by(func.random())
                    .limit(max_distractors)
                )
                distractor_entries = self.db.scalars(distractor_stmt).all()
                distractor_values = [d.lem_text for d in distractor_entries]

            else:
                distractor_stmt = (
                    select(target_model)
                    .join(junction_model)
                    .join(models.Lemma)
                    .filter(models.Lemma.pos == lemma.pos, models.Lemma.id != lemma.id)
                    .order_by(func.random())
                    .limit(max_distractors)
                )
                distractor_entries = self.db.scalars(distractor_stmt).all()
                distractor_values = [
                    getattr(d, target_column) for d in distractor_entries
                ]

            if item_is_ooo and len(sibling_values) >= 3:
                # The "distractor" becomes the correct answer to select
                distractor_val = (
                    distractor_values[0] if distractor_values else "UNKNOWN"
                )

                bp = schemas.ItemBlueprint(
                    prompt=f"Which of these is NOT a {target_model.__name__.lower()} for '{lemma.lem_text}'?",
                    keys=[distractor_val],
                    distractors=random.sample(
                        sibling_values, 3
                    ),  # Valid siblings act as wrong answers
                    lem_id=lemma.id,
                )

            elif drill_direction == "lemma_to_sibling":
                bp = schemas.ItemBlueprint(
                    prompt=lemma.lem_text,
                    keys=random.sample(
                        sibling_values, min(max_keys, len(sibling_values))
                    ),
                    distractors=distractor_values,
                    lem_id=lemma.id,
                )

            elif drill_direction == "sibling_to_lemma":
                selected_sibling = random.choice(sibling_values)
                bp = schemas.ItemBlueprint(
                    prompt=selected_sibling,
                    keys=[lemma.lem_text],
                    distractors=distractor_values,  # We efficiently fetched exactly what we needed!
                    lem_id=lemma.id,
                )

            blueprints.append(bp)  # type: ignore

        return blueprints

    # def _build_lemma_relation_drill(
    #     self,
    #     relation_type: models.EnumRelLemTypeGroup,
    #     pos_target: schemas.EnumPartOfSpeech,
    #     num_items: int = 5,
    #     max_keys: int = 1,
    #     max_distractors: int = 3,
    #     allow_odd_one_out: bool = False,
    #     drill_direction: str = "forward",
    # ) -> Dict[str, Any]:
    #     """
    #     Builds an item by traversing the lemma_relations junction table
    #     (e.g., finding synonyms, antonyms, or aspect pairs).
    #     """
    #     blueprints = []

    #     # fetch valid relationships using scoped statement
    #     rel_stmt = self._get_scoped_stmt()
    #     relations_query = (
    #         rel_stmt.join(
    #             models.Lemma, models.LemmaRelation.source_id == models.Lemma.id
    #         )
    #         .filter(
    #             models.LemmaRelation.rel_type == relation_type,
    #             models.Lemma.pos == pos_target,
    #         )
    #         .order_by(func.random())
    #         .limit(num_items * 2)
    #     )

    #     # deduplicate sources
    #     unique_sources = list({rel.source_id: rel for rel in relations_query}.values())[
    #         :num_items
    #     ]

    #     for rel in unique_sources:
    #         lemma_stmt = self._get_scoped_stmt()
    #         source_lemma = lemma_stmt.get(rel.source_id)

    #         # Get all valid targets using scoped statement
    #         target_stmt = self._get_scoped_stmt()
    #         all_targets = (
    #             target_stmt.join(
    #                 models.LemmaRelation,
    #                 models.LemmaRelation.target_id == models.Lemma.id,
    #             )
    #             .filter(
    #                 models.LemmaRelation.source_id == source_lemma.id,
    #                 models.LemmaRelation.rel_type == relation_type,
    #             )
    #             .all()
    #         )

    #         target_words = [t.word for t in all_targets]

    #         # 2. Defensively fetch distractors using scoped statement
    #         # We still need the raw db.query for the subquery logic
    #         invalid_ids_subquery = db.query(models.LemmaRelation.target_id).filter(
    #             models.LemmaRelation.source_id == source_lemma.id,
    #             models.LemmaRelation.rel_type == relation_type,
    #         )

    #         distractor_stmt = self._get_scoped_stmt(db, models.Lemma)
    #         distractor_lemmas = (
    #             distractor_stmt.filter(
    #                 models.Lemma.pos == pos_target,
    #                 models.Lemma.id != source_lemma.id,
    #                 ~models.Lemma.id.in_(invalid_ids_subquery),
    #             )
    #             .order_by(func.random())
    #             .limit(max_distractors)
    #             .all()
    #         )

    #         distractor_words = [d.word for d in distractor_lemmas]

    #         # 3. Blueprint Formulation
    #         if allow_odd_one_out and len(target_words) >= 3:
    #             blueprint = schemas.ItemBlueprint(
    #                 prompt=f"Which word is NOT a {relation_type} for '{source_lemma.word}'?",
    #                 keys=[distractor_words[0]],
    #                 distractors=target_words[:3],
    #                 metadata={"type": "odd_one_out", "relation_type": relation_type},
    #             )

    #         elif drill_direction == "forward":
    #             blueprint = schemas.ItemBlueprint(
    #                 prompt=source_lemma.word,
    #                 keys=random.sample(target_words, min(max_keys, len(target_words))),
    #                 distractors=distractor_words,
    #                 metadata={"relation": relation_type, "direction": "forward"},
    #             )

    #         elif drill_direction == "reverse":
    #             blueprint = schemas.ItemBlueprint(
    #                 prompt=random.choice(target_words),
    #                 keys=[source_lemma.word],
    #                 distractors=distractor_words,
    #                 metadata={"relation": relation_type, "direction": "reverse"},
    #             )

    #         blueprints.append(blueprint)

    #     return blueprints

    # --- ABSTRACT METHOD ---

    @abstractmethod
    def generate_item_blueprints(
        self,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        config: schemas.StrategyConfigs | None = None,
    ) -> List[schemas.ItemBlueprint] | None:
        """generate_item_blueprints _summary_

        Args:
            limit (int): _description_
            max_distractors (int): _description_

        Returns:
            List[schemas.ItemBlueprint]: _description_
        """
        pass
