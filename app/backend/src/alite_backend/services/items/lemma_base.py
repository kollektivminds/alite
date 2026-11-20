# app/backend/src/alite_backend/services/items/base.py
import logging
import random
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from alite_backend.db import models, schemas

logger = logging.getLogger(__name__)

# declarative mapping from (POS, GramProp column) -> exact leaf KSA.name in seed_ksas.py
MORPHOLOGY_KSA_MAP: Dict[Tuple[models.EnumPartOfSpeech, str], str] = {
    # nouns
    (models.EnumPartOfSpeech.NOUN, "subst_case"): "Noun Case",
    (models.EnumPartOfSpeech.NOUN, "gram_num"): "Noun Number",
    # adjectives
    (models.EnumPartOfSpeech.ADJECTIVE, "subst_case"): "Adjective Case",
    (models.EnumPartOfSpeech.ADJECTIVE, "gram_num"): "Adjective Number",
    (models.EnumPartOfSpeech.ADJECTIVE, "gram_gender"): "Adjective Gender",
    (models.EnumPartOfSpeech.ADJECTIVE, "alt_adjv_type"): "Adjective Degree & Form",
    # verbs
    (models.EnumPartOfSpeech.VERB, "gram_tense"): "Verb Tense",
    (models.EnumPartOfSpeech.VERB, "conj_person"): "Verb Person",
    (models.EnumPartOfSpeech.VERB, "gram_num"): "Verb Number",
    (models.EnumPartOfSpeech.VERB, "gram_gender"): "Verb Gender",
    (models.EnumPartOfSpeech.VERB, "verb_mood"): "Verb Mood",
}

REL_TYPE_DICT: Dict[models.EnumRelLemTypeGroup, List[models.EnumRelLemType]] = {
    models.EnumRelLemTypeGroup.ASPECTUAL_PAIR: [
        models.EnumRelLemType.PERFECTIVE_PAIR_OF,
        models.EnumRelLemType.IMPERFECTIVE_PAIR_OF,
    ],
    models.EnumRelLemTypeGroup.SEMANTIC: [
        models.EnumRelLemType.SYNONYM_OF,
        models.EnumRelLemType.ANTONYM_OF,
    ],
    models.EnumRelLemTypeGroup.SHARED_ROOT: [
        models.EnumRelLemType.ADJECTIVE_OF,
        models.EnumRelLemType.ABSTRACT_NOUN_OF,
        models.EnumRelLemType.ADVERB_OF,
        models.EnumRelLemType.REL_ADJV_OF,
        models.EnumRelLemType.NOUN_FROM_VERB_OF,
    ],
}

REL_GROUP_KSA_MAP: Dict[models.EnumRelLemTypeGroup, str] = {
    models.EnumRelLemTypeGroup.ASPECTUAL_PAIR: "Verb Pairs",
    models.EnumRelLemTypeGroup.SEMANTIC: "Synonyms & Antonyms",
    models.EnumRelLemTypeGroup.SHARED_ROOT: "Shared Roots",
}

# precompute O(1) lookup: specific EnumRelLemType -> leaf KSA.name
REL_TYPE_TO_KSA: Dict[models.EnumRelLemType, str] = {
    rel_type: REL_GROUP_KSA_MAP[group]
    for group, rel_types in REL_TYPE_DICT.items()
    for rel_type in rel_types
}


class LemmaItemBaseStrategy(ABC):
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
                models.LemmaInLessonList.less_list_id.in_(self.less_list_ids)  # type: ignore
            )

        if self.mod_ids:
            stmt = (
                stmt.join(models.LemmaInLessonList)
                .join(
                    models.LessonListInModule,
                    models.LessonListInModule.less_list_id  # type: ignore
                    == models.LemmaInLessonList.less_list_id,
                )
                .where(models.LessonListInModule.mod_id.in_(self.mod_ids))  # type: ignore
            )

        if self.lem_ids:
            stmt = stmt.where(models.Lemma.id.in_(self.lem_ids))  # type: ignore

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
            self._get_scoped_stmt()  # type: ignore
            .with_only_columns(models.Lemma.id)  # type: ignore
            .where(models.Lemma.pos == pos_target)
            .order_by(func.random())
            .limit(num_lemmas)
        )

        # main query: the relational pathway
        stmt = (
            select(models.Lemma, models.WordForm, models.Lexeme, models.GramProp)
            .join(models.WordForm, models.WordForm.lem_id == models.Lemma.id)  # type: ignore
            .join(models.Lexeme, models.WordForm.lex_id == models.Lexeme.id)  # type: ignore
            .join(models.GramProp, models.WordForm.gram_id == models.GramProp.id)  # type: ignore
            .where(models.Lemma.id.in_(lemma_stmt.scalar_subquery()))  # type: ignore
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
        self,
        pos_target: models.EnumPartOfSpeech,
        focus: Union[Enum, str, None],
    ) -> Tuple[str, List[str]]:
        """
        Translates a pedagogical focus into column sets for SQL validation.

        Enhancements:
        1. Polymorphic Normalization: Coerces Enum members, raw strings, and None
           into a clean lowercase string, preventing AttributeError on '.value'.
        2. Universal Wildcard Handling: Immediately returns ('all', []) if focus
           is 'all', bypassing column subtraction.
        3. String Contract: Guarantees that target_attr is always a string column
           name suitable for getattr(gram_prop, target_attr).
        """
        FOCUS_TO_COLUMN = {
            "subst_gender": "gram_gender",
            "subst_num": "gram_num",
            "verb_tense": "gram_tense",
            "verb_person": "conj_person",
            "part_tense": "gram_tense",
        }

        # normalize focus to a string scalar
        if focus is None:
            focus_str = "all"
        elif hasattr(focus, "value"):
            focus_str = str(focus.value).lower()  # type: ignore
        else:
            focus_str = str(focus).lower()

        # early return for unconstrained paradigm tests
        if focus_str == "all":
            return "all", []

        focus_str = FOCUS_TO_COLUMN.get(focus_str, focus_str)  # type: ignore

        # column set definitions per morphological domain
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

        domain_map: Dict[models.EnumPartOfSpeech, List[str]] = {
            models.EnumPartOfSpeech.NOUN: noun_cols,
            models.EnumPartOfSpeech.ADJECTIVE: adjective_cols,
            models.EnumPartOfSpeech.VERB: verb_cols,
            models.EnumPartOfSpeech.PARTICIPLE: participle_cols,
        }

        active_cols = domain_map.get(pos_target, [])
        static_cols = [c for c in active_cols if c != focus_str]

        return focus_str, static_cols

    def _filter_valid_forms(
        self,
        forms: List[Tuple],
        pos_target: models.EnumPartOfSpeech,
        target_attr: str,
        static_attrs: List[str],
    ) -> List[Tuple]:
        """
        Filters out incomplete or defective inflectional records while respecting
        inherent asymmetries in Russian nominal and verbal paradigms.
        """

        def _is_valid(gram_prop: models.GramProp) -> bool:
            # target attribute invariant: form MUST exhibit the feature being tested
            if target_attr != "all":
                if getattr(gram_prop, target_attr, None) is None:
                    return False

            # russian adjective heuristic:
            # short-form adjectives lack case; plural adjectives lack gender.
            # only validate static attributes when static_attrs is non-empty.
            if pos_target == models.EnumPartOfSpeech.ADJECTIVE:
                if static_attrs:
                    # require at least one static agreement anchor (GNC)
                    if not any(
                        getattr(gram_prop, a, None) is not None for a in static_attrs
                    ):
                        return False

            # russian verb heuristic:
            # past tense has gender but no person; present/future has person but no gender.  # noqa: E501
            elif pos_target == models.EnumPartOfSpeech.VERB:
                tense = getattr(gram_prop, "gram_tense", None)
                # assert tense is not None  # noqa: S101
                tense_val = (
                    tense.value if hasattr(tense, "value") else str(tense or "").lower()  # type: ignore
                )

                # Number is an invariant across all finite Russian verb forms
                if getattr(gram_prop, "gram_num", None) is None:
                    return False

                if tense_val in ("present", "future"):
                    if getattr(gram_prop, "conj_person", None) is None:
                        return False
                elif tense_val == "past":
                    # Singular past requires gender; plural past has no gender in Russian  # noqa: E501
                    num = getattr(gram_prop, "gram_num", None)
                    # assert num is not None  # noqa: S101
                    num_val = (
                        num.value if hasattr(num, "value") else str(num or "").lower()  # type: ignore
                    )
                    if (
                        num_val in ("singular", "sg")
                        and getattr(gram_prop, "gram_gender", None) is None
                    ):
                        return False

            # 4. Standard Nominal (Noun) Heuristic:
            elif pos_target == models.EnumPartOfSpeech.NOUN:
                if static_attrs:
                    if not all(
                        getattr(gram_prop, a, None) is not None for a in static_attrs
                    ):
                        return False

            return True

        return [row for row in forms if _is_valid(gram_prop=row[3])]

    def _extract_option_text(self, item_tuple: Tuple, is_reverse: bool) -> str:
        """
        Extracts the user-facing string from the raw database tuple based on the drill type.
        """  # noqa: E501
        lemma, word_form, lexeme, gram_prop = item_tuple

        # if the drill shows words and asks for grammar, the options are the grammar tags.  # noqa: E501
        # if the drill asks for a word based on a grammar prompt, the options are the words.  # noqa: E501
        if is_reverse is False:
            return self._format_attribute_name(gram_prop)
        else:
            return lexeme.lex_text or lexeme.lex_text_clean

    def _get_paradigm_option_text(
        self,
        item_tuple: Tuple,
        is_reverse: bool,
        target_attr: str,
        static_attrs: List[str],
    ) -> str:
        """
        Extracts the user-facing option string from the raw database tuple.
        """
        # Unpack the standard paradigm tuple
        lemma, word_form, lexeme, gram_prop = item_tuple

        if is_reverse is False:
            return self._format_grammar_label(gram_prop, target_attr, static_attrs)
        else:
            return lexeme.lex_text or lexeme.lex_text_clean

    def _generate_paradigm_prompt(
        self, baseline_form: Tuple, is_reverse: bool, target_attr: str
    ) -> str:
        """
        Generates the instructional prompt for a paradigm-based item.
        """
        lemma, word_form, lexeme, gram_prop = baseline_form

        # Determine the base word to display (fallback to lem_text if canon is null)
        base_word = lemma.lem_canon or lemma.lem_text

        if is_reverse is False:
            # user sees a Russian word and must select its grammatical properties.
            if target_attr == "all":
                return f"Identify the complete grammatical parsing for the form '{lexeme.lex_text or lexeme.lex_text_clean}':"  # noqa: E501
            else:
                # E.g., "What is the subst_case of..." -> "What is the case of..."
                clean_attr = self._format_attribute_name(target_attr)
                return f"What is the {clean_attr} of the form '{lexeme.lex_text or lexeme.lex_text_clean}'?"  # noqa: E501

        else:
            # user sees a grammatical description and must select the matching Russian word.  # noqa: E501
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
        is_reverse: bool,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates a standard multiple-choice paradigm question with one correct answer."""  # noqa: E501

        # Unpack the baseline to access its grammatical properties
        _, _, _, base_gp = baseline_form

        # filter the pool for valid distractors.
        # a valid distractor matches all static attributes but differs on the target attribute.  # noqa: E501
        distractor_pool = []
        for form in valid_forms:
            _, _, _, gp = form

            # skip the baseline itself (and any identical syncretic forms)
            if form == baseline_form:
                continue

            # must match all static attributes (e.g., if baseline is plural, distractor must be plural)  # noqa: E501
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

        # graceful degradation: Ensure we have enough distractors to make a viable question  # noqa: E501
        if len(distractor_pool) < max_distractors:
            return None

        # sample exactly what we need
        distractors = random.sample(distractor_pool, max_distractors)

        # generate the localized prompt (e.g., "Find the Genitive Plural form of X")
        prompt_text = self._generate_paradigm_prompt(
            baseline_form, is_reverse, target_attr
        )

        # build and return the blueprint
        return schemas.ItemBlueprint(
            prompt=prompt_text,
            keys=[
                self._get_paradigm_option_text(
                    baseline_form, is_reverse, target_attr, static_attrs
                )
            ],
            distractors=[
                self._get_paradigm_option_text(d, is_reverse, target_attr, static_attrs)
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
        is_reverse: bool,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates a multi-select paradigm question with 1 to N correct answers."""

        _, _, _, base_gp = baseline_form

        key_pool = []
        distractor_pool = []

        # partition the valid forms into potential keys and distractors
        for form in valid_forms:
            _, _, _, gp = form

            # must match static attributes to belong in this specific question's universe  # noqa: E501
            if not all(
                getattr(gp, attr) == getattr(base_gp, attr) for attr in static_attrs
            ):
                continue

            # if it matches the target attribute, it's a key. otherwise, it's a distractor.  # noqa: E501
            if target_attr == "all" or getattr(gp, target_attr) == getattr(
                base_gp, target_attr
            ):
                key_pool.append(form)
            else:
                distractor_pool.append(form)

        # graceful degradation: check if we have enough total options to make the item
        # we need at least 1 key (the baseline is guaranteed, but let's be safe) and enough distractors  # noqa: E501
        if not key_pool or len(distractor_pool) < max_distractors:
            return None

        # sample the pools
        # cap the number of keys at max_keys, ensuring baseline is included if we want it guaranteed  # noqa: E501
        num_keys_to_pick = min(len(key_pool), max_keys)
        keys = random.sample(key_pool, num_keys_to_pick)
        distractors = random.sample(distractor_pool, max_distractors)

        prompt_text = self._generate_paradigm_prompt(
            baseline_form, is_reverse, target_attr
        )

        return schemas.ItemBlueprint(
            prompt=prompt_text,
            keys=[
                self._get_paradigm_option_text(k, is_reverse, target_attr, static_attrs)
                for k in keys
            ],
            distractors=[
                self._get_paradigm_option_text(d, is_reverse, target_attr, static_attrs)
                for d in distractors
            ],
            lem_id=baseline_form[0].id,
        )

    def _build_ooo_prompt(
        self, shared_forms: List[Tuple], target_attr: str, is_reverse: bool
    ) -> str:
        """
        Generates the instruction prompt for an odd-one-out question.
        """
        # to be explicit about what pattern they are looking for,
        # we grab the grammatical property of the shared forms to state the pattern.
        _, _, _, shared_gp = shared_forms[0]

        if target_attr == "all":
            return "Which of the following forms does not belong?"

        # if we are testing a specific attribute (like case), we can build a specific prompt.  # noqa: E501
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
        is_reverse: bool,
    ) -> Optional[schemas.ItemBlueprint]:
        """Generates an odd-one-out morphology question."""

        # determine the grouping attribute (bkt decision point for 'all')
        grouping_attr = target_attr
        if grouping_attr == "all":
            grouping_attr = random.choice(  # noqa: S311
                [e.value for e in schemas.EnumSubstGramExFocus if e.value != "all"]
            )

        # bucket the forms by the target grammatical trait
        buckets = defaultdict(list)
        for lemma, word_form, lexeme, gram_prop in valid_forms:
            trait_val = getattr(gram_prop, grouping_attr)
            buckets[trait_val].append((lemma, word_form, lexeme, gram_prop))

        # verify there is at least one trait with 3+ items (distractors) and one with 1 item (the key)  # noqa: E501
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
            is_reverse=is_reverse,
        )

        # pick the odd-one-out (the key)
        key_tuple = random.choice(buckets[minority_trait])  # noqa: S311

        _, _, key_lexeme, _ = key_tuple

        key_text = key_lexeme.lex_text or key_lexeme.lex_text_clean

        # distractor_texts = [
        #     self._get_paradigm_option_text(
        #         d, is_reverse, target_attr, static_attrs
        #     )
        #     for d in distractors
        # ]

        seen_texts = {key_text}
        distractor_texts = []

        # safely extract distractors
        # shuffle the majority bucket so we don't always grab the first N items
        pool = list(buckets[majority_trait])
        random.shuffle(pool)

        for form_tuple in pool:
            _, _, dist_lexeme, _ = form_tuple
            dist_text = dist_lexeme.lex_text or dist_lexeme.lex_text_clean

            # only add to our distractors if the surface string is entirely unique
            if dist_text not in seen_texts:
                seen_texts.add(dist_text)
                distractor_texts.append(dist_text)

            # break early once we hit the required number of distractors
            if len(distractor_texts) == max_distractors:
                break

        # graceful degradation check
        # because of deduplication, we might run out of unique words before hitting max_distractors  # noqa: E501
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
        is_reverse: bool,
    ) -> List[schemas.ItemBlueprint]:
        """
        engine for creating exercises based on the lemma table
        """
        blueprints = []
        attr_name = self._format_attribute_name(target_attr)
        # fetch a buffered pool of valid lemmas
        stmt = self._get_scoped_stmt()

        if pos_target is not None:
            stmt = stmt.where(models.Lemma.pos == pos_target)  # type: ignore

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
            if is_reverse is True:
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
            elif is_reverse is False:
                item_is_ooo = (
                    random.choice([True, False]) if allow_odd_one_out else False  # noqa: S311
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
                    prompt_text = f"Which of these words has the attribute: {trait_str} ({attr_name})?"  # noqa: E501

            if keys and distractors:
                bp = schemas.ItemBlueprint(
                    prompt=prompt_text,
                    keys=keys,
                    distractors=distractors,
                    lem_id=lemma_id,  # type: ignore
                )
                blueprints.append(bp)

        return blueprints

    def _build_paradigm_drill(
        self,
        pos_target: models.EnumPartOfSpeech,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        allowed_foci: Any,
        allow_odd_one_out: bool,
        is_reverse: bool,
    ) -> List[schemas.ItemBlueprint]:
        blueprints = []
        paradigms = self._fetch_grouped_paradigms(
            pos_target=pos_target, num_lemmas=num_items * 5
        )

        for _lemma_id, forms in paradigms.items():
            if len(blueprints) >= num_items:
                break

            if not forms or len(forms) < (max_keys + max_distractors):
                continue

            # Robust resolution of drill focus
            if not allowed_foci or allowed_foci == "all" or allowed_foci == ["all"]:
                item_focus = "all"
            elif isinstance(allowed_foci, (list, tuple, set)):
                item_focus = random.choice(list(allowed_foci))  # noqa: S311
            else:
                item_focus = allowed_foci

            target_attr, static_attrs = self._get_trait_mapping(
                pos_target=pos_target, focus=item_focus
            )

            valid_forms = self._filter_valid_forms(
                forms, pos_target, target_attr, static_attrs
            )

            if not valid_forms or len(valid_forms) < (max_keys + max_distractors):
                continue

            baseline_form = random.choice(valid_forms)  # noqa: S311
            item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False  # noqa: S311
            if is_reverse is False:
                item_is_ooo = False

            if item_is_ooo:
                bp = self._generate_ooo_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_keys,
                    max_distractors,
                    is_reverse,
                )
            elif max_keys > 1:
                bp = self._generate_multiselect_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_keys,
                    max_distractors,
                    is_reverse,
                )
            else:
                bp = self._generate_single_key_paradigm(
                    valid_forms,
                    baseline_form,
                    target_attr,
                    static_attrs,
                    max_distractors,
                    is_reverse,
                )

            if bp:
                # baseline_form is (lemma, word_form, lexeme, gram_prop)
                bp.ksa_names = self._resolve_ksas(
                    pos_target=pos_target,
                    target_attr=target_attr,
                    target=baseline_form[3],
                )
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
        is_reverse: bool = False,
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
            stmt = stmt.filter(models.Lemma.pos == target_pos)  # type: ignore

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
        #         f"\n--- SIBLING DRILL SQL ---\n{compiled_sql}\n-------------------------\n"  # noqa: E501
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
                pos_label = target_pos if target_pos is not None else "any"
                logger.warning(
                    f"Requested {num_items} items for {target_model.__name__}, "
                    f"but only found {len(candidates)} valid '{pos_label}' lemmas in DB."  # noqa: E501
                )
                num_items = len(candidates)
                if num_items == 0:
                    return []
            # raise ValueError(
            #     f"Not enough {target_pos} lemmas with {target_model.__name__} data to generate {num_items} items."  # noqa: E501
            # )

        for lemma in candidates:
            if len(blueprints) >= num_items:
                break
            # fetch the siblings (definitions / pronunciations) utilizing the scoped statement  # noqa: E501
            sibling_stmt = (
                select(target_model)
                .join(junction_model)
                .filter(junction_model.lem_id == lemma.id)
            )
            siblings = self.db.scalars(sibling_stmt).all()
            sibling_values = [getattr(s, target_column) for s in siblings]

            item_is_ooo = random.choice([True, False]) if allow_odd_one_out else False  # noqa: S311

            if is_reverse is True and not item_is_ooo:
                distractor_stmt = (
                    select(models.Lemma)
                    .join(
                        junction_model
                    )  # Ensure the distractor word actually has entries
                    .filter(models.Lemma.pos == lemma.pos, models.Lemma.id != lemma.id)  # type: ignore
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
                    .filter(models.Lemma.pos == lemma.pos, models.Lemma.id != lemma.id)  # type: ignore
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
                    prompt=f"Which of these is NOT a {target_model.__name__.lower()} for '{lemma.lem_text}'?",  # noqa: E501
                    keys=[distractor_val],
                    distractors=random.sample(
                        sibling_values, 3
                    ),  # valid siblings act as wrong answers
                    lem_id=lemma.id,  # type: ignore
                )

            elif is_reverse is False:
                bp = schemas.ItemBlueprint(
                    prompt=lemma.lem_text,
                    keys=random.sample(
                        sibling_values, min(max_keys, len(sibling_values))
                    ),
                    distractors=distractor_values,
                    lem_id=lemma.id,  # type: ignore
                )

            elif is_reverse is True:
                selected_sibling = random.choice(sibling_values)  # noqa: S311
                bp = schemas.ItemBlueprint(
                    prompt=selected_sibling,
                    keys=[lemma.lem_text],
                    distractors=distractor_values,
                    lem_id=lemma.id,  # type: ignore
                )

            blueprints.append(bp)  # type: ignore

        return blueprints

    def _generate_relation_prompt(
        self,
        prompt_word: str,
        rel_type: str | Enum,
        is_reverse: bool,
        is_ooo: bool = False,
    ) -> str:
        """
        Generates pedagogically sound prompts for relational items, handling
        asymmetry in derivational and aspectual relationships.
        """
        # extract string value if an Enum is passed
        rel_str = getattr(rel_type, "value", str(rel_type))

        # base mapping for forward relations (Source -> Target)
        forward_labels = {
            "perfective_pair_of": "perfective counterpart",
            "imperfective_pair_of": "imperfective counterpart",
            "synonym_of": "synonym",
            "antonym_of": "antonym",
            "adjective_of": "derived adjective",
            "abstract_noun_of": "abstract noun",
            "adverb_of": "derived adverb",
            "rel_adjv_of": "relational adjective",
            "noun_from_verb_of": "verbal noun",
        }

        # base mapping for reverse relations (target -> source)
        # resolves the asymmetry of derivational/aspectual roots
        reverse_labels = {
            "perfective_pair_of": "imperfective base",
            "imperfective_pair_of": "perfective base",
            "synonym_of": "synonym",  # Symmetric
            "antonym_of": "antonym",  # Symmetric
            "adjective_of": "base noun or verb",
            "abstract_noun_of": "base word",
            "adverb_of": "base adjective",
            "rel_adjv_of": "base noun",
            "noun_from_verb_of": "base verb",
        }

        if is_ooo:
            # for ooo, the prompt_word is always the central hub.
            label = forward_labels.get(rel_str, rel_str.replace("_", " "))
            return f"Which word is NOT a {label} for '{prompt_word}'?"

        if is_reverse:
            # showing the Target, asking for the Source
            label = reverse_labels.get(rel_str, f"base of {rel_str}")
            return f"Identify the {label} for '{prompt_word}':"
        else:
            # showing the Source, asking for the Target
            label = forward_labels.get(rel_str, rel_str.replace("_", " "))
            return f"Identify the {label} for '{prompt_word}':"

    def _build_lemma_relation_drill(
        self,
        rel_target_group: models.EnumRelLemTypeGroup | None,
        pos_target: models.EnumPartOfSpeech | None,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 3,
        allow_odd_one_out: bool = False,
        drill_mode: str = "find_target",  # "find_target", "find_source", "find_relation", "find_pair"  # noqa: E501
    ) -> List[schemas.ItemBlueprint]:
        """
        Builds an item by traversing the lemma_relations junction table.
        Adapts prompt and key generation based on the specified drill_mode.
        """
        blueprints = []
        target_rel_types = []
        if rel_target_group:
            target_rel_types = REL_TYPE_DICT.get(rel_target_group, [])

        # fetch distinct (source_id, specific_rel_type) pairs
        relations_query = (
            self._get_scoped_stmt()
            .join_from(
                models.Lemma,
                models.LemmaRelation,
                models.LemmaRelation.source_id == models.Lemma.id,  # type: ignore
            )
            .with_only_columns(
                models.LemmaRelation.source_id,  # type: ignore
                models.LemmaRelation.rel_type,  # type: ignore
            )
        )

        if target_rel_types:
            relations_query = relations_query.filter(
                models.LemmaRelation.rel_type.in_(target_rel_types)  # type: ignore
            )

        if pos_target is not None:
            relations_query = relations_query.filter(models.Lemma.pos == pos_target)

        relations_query = relations_query.order_by(func.random()).limit(num_items * 4)

        # execute and deduplicate to ensure unique pair combinations
        candidate_pairs = list(set(self.db.execute(relations_query).all()))

        if len(candidate_pairs) < num_items:
            num_items = len(candidate_pairs)
            if num_items == 0:
                return []

        for source_id, specific_rel_type in candidate_pairs:
            if len(blueprints) >= num_items:
                break

            source_lemma = self.db.get(models.Lemma, source_id)
            if not source_lemma:
                continue

            item_ksas = self._resolve_ksas(target=specific_rel_type)

            # Get targets matching this EXACT relation type
            target_stmt = (
                select(models.Lemma)
                .join_from(
                    models.LemmaRelation,
                    models.Lemma,
                    models.LemmaRelation.target_id == models.Lemma.id,  # type: ignore
                )
                .filter(
                    models.LemmaRelation.source_id == source_id,
                    models.LemmaRelation.rel_type == specific_rel_type,
                )
            )

            all_targets = self.db.scalars(target_stmt).all()
            if not all_targets:
                continue

            target_words = [
                t.lem_canon or t.lem_text
                for t in all_targets
                if t.lem_canon or t.lem_text
            ]
            first_target = all_targets[0]

            source_display = source_lemma.lem_canon or source_lemma.lem_text
            target_display = target_words[0]

            # mode 1: find relation (lem_lem_to_rel)
            # prompt: word a & word b -> key: relationship type
            if drill_mode == "find_relation":
                rel_label = specific_rel_type.value.replace("_", " ")
                prompt_text = f"'{target_display}' is what to '{source_display}'?"

                # Get wrong relationships as distractors
                distractors = self._get_enum_distractors(
                    specific_rel_type, max_distractors
                )
                distractors = [d.replace("_", " ") for d in distractors]

                blueprints.append(
                    schemas.ItemBlueprint(
                        prompt=prompt_text,
                        keys=[rel_label],
                        distractors=distractors,
                        lem_id=source_lemma.id,
                        ksa_names=item_ksas,
                    )
                )
                continue

            # mode 2: find pair (rel_to_lem_lem)
            # prompt: relationship type -> key: word a - word b
            if drill_mode == "find_pair":
                rel_label = specific_rel_type.value.replace("_", " ")
                prompt_text = f"Which of the following pairs represents a '{rel_label}' relationship?"  # noqa: E501
                correct_pair = f"{target_display} is the ... {source_display}"

                # fetch distractors: random pairs that are not this relationship
                # easiest way: pull random relations that don't match specific_rel_type
                distractor_pairs = []
                dist_stmt = (
                    select(models.LemmaRelation)
                    .filter(models.LemmaRelation.rel_type != specific_rel_type)
                    .order_by(func.random())
                    .limit(max_distractors + 2)
                    .options(
                        selectinload(models.LemmaRelation.source_lemma),  # type: ignore
                        selectinload(models.LemmaRelation.target_lemma),  # type: ignore
                    )
                )
                for d_rel in self.db.scalars(dist_stmt).all():
                    if d_rel.source_lemma and d_rel.target_lemma:
                        d_source = (
                            d_rel.source_lemma.lem_canon or d_rel.source_lemma.lem_text
                        )
                        d_target = (
                            d_rel.target_lemma.lem_canon or d_rel.target_lemma.lem_text
                        )
                        distractor_pairs.append(f"{d_target} is the ... {d_source}")
                        if len(distractor_pairs) == max_distractors:
                            break

                if len(distractor_pairs) < max_distractors:
                    continue  # graceful degradation

                blueprints.append(
                    schemas.ItemBlueprint(
                        prompt=prompt_text,
                        keys=[correct_pair],
                        distractors=distractor_pairs,
                        lem_id=source_lemma.id,
                        ksa_names=item_ksas,
                    )
                )
                continue

            # modes 3 & 4: find target or find source (standard drills)
            # fetch standard word distractors
            required_distractor_pos = (
                source_lemma.pos if drill_mode == "find_source" else first_target.pos
            )

            invalid_ids_subquery = select(models.LemmaRelation.target_id).filter(  # type: ignore
                models.LemmaRelation.source_id == source_id,
                models.LemmaRelation.rel_type == specific_rel_type,
            )

            distractor_stmt = (
                select(models.Lemma)
                .filter(
                    models.Lemma.id != source_id,
                    models.Lemma.pos == required_distractor_pos,  # type: ignore
                    ~models.Lemma.id.in_(invalid_ids_subquery),  # type: ignore
                )
                .order_by(func.random())
                .limit(max_distractors)
            )

            distractor_lemmas = self.db.scalars(distractor_stmt).all()
            distractor_words = [
                d.lem_canon or d.lem_text
                for d in distractor_lemmas
                if d.lem_canon or d.lem_text
            ]

            if not target_words or len(distractor_words) < max_distractors:
                continue

            item_is_ooo = allow_odd_one_out and len(target_words) >= 3

            # OOO logic applies primarily to finding targets where multiple exist (e.g. synonyms)  # noqa: E501
            if item_is_ooo:
                prompt_text = self._generate_relation_prompt(
                    prompt_word=source_display,
                    rel_type=specific_rel_type,
                    is_reverse=(drill_mode == "find_source"),
                    is_ooo=True,
                )
                blueprints.append(
                    schemas.ItemBlueprint(
                        prompt=prompt_text,
                        keys=[distractor_words[0]],
                        distractors=target_words[:3],
                        lem_id=source_lemma.id,
                        ksa_names=item_ksas,
                    )
                )
            elif drill_mode == "find_target":
                prompt_text = self._generate_relation_prompt(
                    prompt_word=source_display,
                    rel_type=specific_rel_type,
                    is_reverse=False,
                )
                blueprints.append(
                    schemas.ItemBlueprint(
                        prompt=prompt_text,
                        keys=random.sample(
                            target_words, min(max_keys, len(target_words))
                        ),
                        distractors=distractor_words,
                        lem_id=source_lemma.id,
                        ksa_names=item_ksas,
                    )
                )
            elif drill_mode == "find_source":
                target_hub = random.choice(target_words)  # noqa: S311
                prompt_text = self._generate_relation_prompt(
                    prompt_word=target_hub,
                    rel_type=specific_rel_type,
                    is_reverse=True,
                )
                blueprints.append(
                    schemas.ItemBlueprint(
                        prompt=prompt_text,
                        keys=[source_display],
                        distractors=distractor_words,
                        lem_id=source_lemma.id,
                        ksa_names=item_ksas,
                    )
                )

        return blueprints

    def _resolve_ksas(
        self,
        target: Union[models.GramProp, models.EnumRelLemType],
        pos_target: Optional[models.EnumPartOfSpeech] = None,
        target_attr: str = "all",
    ) -> List[str]:
        """
        Unified leaf-KSA resolver for dynamic lemma strategies.
        - EnumRelLemType -> resolves via REL_TYPE_TO_KSA (works even when rel_target_group is None).
        - GramProp -> resolves single focus or expands 'all' to non-null morphological traits.
        """
        # Branch A: Lemma Relation drills
        if isinstance(target, models.EnumRelLemType):
            ksa_name = REL_TYPE_TO_KSA.get(target)
            return [ksa_name] if ksa_name else []

        # Branch B: Morphological Paradigm drills
        if pos_target is None:
            return []

        if target_attr != "all":
            ksa_name = MORPHOLOGY_KSA_MAP.get((pos_target, target_attr))
            return [ksa_name] if ksa_name else []

        # Wildcard 'all': include only traits present on this specific inflected form
        return [
            ksa_name
            for (pos, col_name), ksa_name in MORPHOLOGY_KSA_MAP.items()
            if pos == pos_target and getattr(target, col_name, None) is not None
        ]

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
