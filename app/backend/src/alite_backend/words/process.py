"""Class to process scraped data before loading it into the SQL database.

This module provides tools for processing and analyzing scraped word data. It
includes functions for cleaning raw text, extracting specific word forms, and
preparing data payloads for database insertion. It is designed to be the
'transform' step in an ETL (Extract, Transform, Load) pipeline.

This module supports:
- RawScrapedData: A dataclass for holding unprocessed scraped data.
- Processor: A class that orchestrates the transformation logic.

Example:
    processor = Processor()
    raw_data = RawScrapedData(term="example", ...)
    payload = processor.transform(raw_data)
"""

#!/usr/bin/env python
# coding: utf-8
import logging
import uuid
import re
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError
from alite_backend.config import settings
from alite_backend.db.schemas import FDAPIreturn, ProcessedPayload
from alite_backend.db.models import (
    EnumPartOfSpeech,
    EnumGender,
    EnumVerbAspect,
    EnumVerbTransRefl,
    EnumGramNum,
    EnumPronType,
    EnumRelLemType,
)
from alite_backend.words.funcs import (
    pos_dict,
    sop_dict,
    remove_accents,
    is_cyrillic,
    zalizniak_to_type,
)
from alite_backend.db.schemas import Quote

logger = logging.getLogger(__name__)
fixed_tags = {"canonical", "romanization", "table-tags"}
APP_NAMESPACE = uuid.UUID(settings.NAMESPACE)


class ReturnedLemmaProcessor:
    """
    Functions to turn a WordClass object into a usable response
    """

    def __init__(self):

        self.result = None

    def _map_lem_chars(self, pos: EnumPartOfSpeech, chars: list[str]):
        lemma_chars_dict = {}
        noun_chars_map = {
            # noun_gender
            "masculine": {"noun_gender": EnumGender.MASCULINE},
            "neuter": {"noun_gender": EnumGender.NEUTER},
            "feminine": {"noun_gender": EnumGender.FEMININE},
            # gram_num
            "singular": {"gram_num": EnumGramNum.SINGULAR},
            "plural": {"gram_num": EnumGramNum.PLURAL},
            # subst_animacy
            "inanimate": {"subst_animacy": False},
            "animate": {"subst_animacy": True},
        }
        verb_chars_map = {
            # verb_aspect
            "perfective": {"verb_aspect": EnumVerbAspect.PERFECTIVE},
            "imperfective": {"verb_aspect": EnumVerbAspect.IMPERFECTVE},
            # verb_trans_refl
            "transitive": {"verb_trans_refl": EnumVerbTransRefl.TRANSITIVE},
            "intransitive": {"verb_trans_refl": EnumVerbTransRefl.INTRANSITIVE},
            "reflexive": {"verb_trans_refl": EnumVerbTransRefl.REFLEXIVE},
        }

        for char in chars:
            if pos == EnumPartOfSpeech.VERB:
                if char in verb_chars_map:
                    lemma_chars_dict.update(verb_chars_map[char])
            else:
                if char in noun_chars_map:
                    lemma_chars_dict.update(noun_chars_map[char])
        return lemma_chars_dict

    def _sort_entries(self, lem_text, entries):
        sorted_data = {
            "lemmas": [],
            "gram_props": [],
            "lexicon": [],
            "definitions": [],
            "def_examples": [],
            "pronunciations": [],
            "rel_lems": [],
        }
        lang_code = "ru"
        entry_index = 0
        for entry in entries:
            # gather basic data
            # logger.debug(entry)
            language = entry.language
            # logger.debug("entry senses tags: %s", [x.tags for x in entry.senses][0])
            if language.code != lang_code:
                logger.error("%s is %s!!!", lem_text, language.name)
                continue
            elif (
                len(entry.senses) == 1
                and "form of" in [x.tags for x in entry.senses][0]
            ):
                logger.error(
                    "This word form (%s) was found but is not canonical (a lemma)",
                    lem_text,
                )
                # TODO catch these to put back in the queue if not already
                continue

            pos = entry.partOfSpeech
            if not pos or pos not in EnumPartOfSpeech._value2member_map_:
                continue
            entry_name = f"{lem_text}_{pos}_{entry_index}"
            entry_key = uuid.uuid5(APP_NAMESPACE, entry_name)
            # logger.debug("entry: %s", entry_key)
            pos = EnumPartOfSpeech(pos)
            # make entry's lemma dict
            lemma_dict = {
                "lem_text": lem_text,
                "lem_canon": None,
                "pos": pos,
                "entry_key": entry_key,
                # TO BE FILLED IN AS NEEDED
                "noun_gender": None,
                "subst_animacy": None,
                "verb_aspect": None,
                "verb_conj": None,
                "verb_type": None,
                "verb_trans_refl": None,
            }
            lemma_dict_tags = []
            canonical_forms = ["canonical", "infinitive"]
            try:
                # logger.debug("forms items: %s", [x.word for x in entry.forms if x.tags[0] == 'canonical'][0])
                if pos == EnumPartOfSpeech.VERB:
                    verb_infin_form_object = [
                        x
                        for x in entry.forms
                        if any(item in canonical_forms for item in x.tags)
                    ][0]
                    # logger.debug("verb infin form obj: %s", verb_infin_form_object)
                    canonical_form = verb_infin_form_object.word
                    # logger.debug("verb canonical form: %s", canonical_form)
                    tags = verb_infin_form_object.tags
                    # logger.debug("tags: %s", form.tags)
                    # logger.debug("word: %s", form.word)
                    if len(tags) == 2:
                        for tag in tags:
                            # logger.debug("tag: %s", tag)
                            if tag in ["perfective", "imperfective"]:
                                logger.debug("verb_aspect: %s", tag)
                                verbal_aspect = tag
                                lemma_dict["verb_aspect"] = verbal_aspect  # type: ignore
                        # logger.debug("form word: %s", form.word)
                    # logger.debug("first can form: %s", canonical_form)
                    # logger.debug("verb_infin_lex_entry: %s", verb_infin_lex_entry)
                else:
                    canonical_object = [
                        x for x in entry.forms if "canonical" in x.tags
                    ][0]
                    # logger.debug("canonical object: %s", canonical_object)
                    canonical_form = canonical_object.word
                    if pos == EnumPartOfSpeech.NOUN:
                        # logger.debug("noun base form lex entry: %s", noun_base_lex_entry)
                        canon_tags = canonical_object.tags
                        if len(canon_tags) > 1:
                            for prop in canon_tags:
                                if prop != "canonical":
                                    # logger.debug(
                                    #     "other canonical noun gram prop: %s", prop
                                    # )
                                    lemma_dict_tags.append(prop)

                # logger.debug("canonical form: %s", canonical_form)
                lemma_dict["lem_canon"] = canonical_form
            except Exception as e:
                canonical_form = None
                logger.error(
                    "No canonical form found for %s because of %s", lem_text, e
                )

            # lexicon and gram_props
            for form in entry.forms:
                form_word = form.word
                if not form_word or form_word == "-":
                    continue
                form_tags = form.tags
                if set(form_tags).isdisjoint(canonical_forms):
                    if not is_cyrillic(form_word):
                        # logger.debug("non-cyrillic form: %s (%s)", form_word, form_tags)
                        if "romanization" in form.tags:
                            sorted_data["pronunciations"].append(
                                {
                                    "entry_key": entry_key,
                                    "pron_text": form_word,
                                    "pron_type": EnumPronType.ROMANIZATION,
                                    "pron_tags": [],
                                }
                            )
                        elif "class" in form.tags and pos == EnumPartOfSpeech.VERB:
                            # logger.debug("class & verb: %s", form_word)
                            re_pattern = r"(?P<verb_conj>.*?)\s(?P<verb_aspect>imperfective|perfective)\s(?P<verb_trans_refl>intransitive|transitive|reflexive)$"
                            match = re.search(re_pattern, form_word)
                            if match:
                                # logger.debug("verb match: %s", match)
                                for group_name, group_val in match.groupdict().items():
                                    # logger.debug(
                                    #     "verb class matching: %s = %s",
                                    #     group_name,
                                    #     group_val,
                                    # )
                                    lemma_dict[group_name] = group_val
                                lemma_dict["verb_type"] = zalizniak_to_type(
                                    match.group("verb_conj")
                                )
                            else:
                                logger.debug("no class found for %s", lem_text)
                        elif "table-tags" in form.tags and pos == EnumPartOfSpeech.VERB:
                            re_pattern = r"^(?P<verb_aspect>imperfective|perfective)\s(?P<verb_trans_refl>intransitive|transitive|reflexive)$"
                            match = re.search(re_pattern, form_word)
                            if match:
                                # logger.debug("verb match: %s", match)
                                for group_name, group_val in match.groupdict().items():
                                    # logger.debug(
                                    #     "verb class matching: %s = %s",
                                    #     group_name,
                                    #     group_val,
                                    # )
                                    lemma_dict[group_name] = group_val
                            else:
                                logger.debug("no table-tags found for %s", lem_text)

                    else:
                        # link all its tags as grammatical properties
                        tags_to_boot = [
                            "dated",
                            "alternative",
                            "dialectical",
                            "canonical",
                            "class",
                            "emphatic"
                        ]
                        related_lemma_tags = [
                            "relational",
                            "adjective",
                            "noun-from-verb",
                            "adverb",
                            "abstract-noun"
                        ]
                        # logger.debug("tags: %s", tags)
                        if set(form_tags).isdisjoint(tags_to_boot):
                            # logger.debug("acceptable tags: %s - %s", form_word, form_tags)
                            # related words
                            if set(form_tags).intersection(related_lemma_tags):
                                logger.debug(
                                    "related word tags %s: %s", form_word, form_tags
                                )
                                if (
                                    "relational" in form_tags
                                    and "adjective" in form_tags
                                ):
                                    rel_adj_dict = {
                                        "entry_key": entry_key,
                                        "rel_form": form_word,
                                        "rel_type": EnumRelLemType.ABSTRACT_NOUN_OF,
                                    }
                                    sorted_data["rel_lems"].append(rel_adj_dict)
                                elif (
                                    len(form_tags) == 1
                                    and form_tags[0] == "noun-from-verb"
                                ):
                                    deverb_noun_dict = {
                                        "entry_key": entry_key,
                                        "rel_form": form_word,
                                        "rel_type": EnumRelLemType.NOUN_FROM_VERB_OF,
                                    }
                                    sorted_data["rel_lems"].append(deverb_noun_dict)
                                elif len(form_tags) == 1 and form_tags[0] == "adverb":
                                    adverb_dict = {
                                        "entry_key": entry_key,
                                        "rel_form": form_word,
                                        "rel_type": EnumRelLemType.ADVERB_OF,
                                    }
                                    sorted_data["rel_lems"].append(adverb_dict)
                                elif (
                                    len(form_tags) == 1
                                    and form_tags[0] == "abstract-noun"
                                ):
                                    abstract_noun_dict = {
                                        "entry_key": entry_key,
                                        "rel_form": form_word,
                                        "rel_type": EnumRelLemType.ABSTRACT_NOUN_OF,
                                    }
                                    sorted_data["rel_lems"].append(abstract_noun_dict)
                            # verb pair
                            elif (
                                pos == EnumPartOfSpeech.VERB
                                and len(form_tags) == 1
                                and re.match(r"imperfective|perfective", form_tags[0])
                            ):
                                # logger.debug("verb pair tags: %s", form_tags)
                                verb_pair_dict = {
                                    "entry_key": entry_key,
                                    "rel_form": None,
                                    "rel_type": None,
                                }
                                if verbal_aspect == "perfective":  # type:ignore
                                    imperfective_form = [
                                        x.word
                                        for x in entry.forms
                                        if len(x.tags) == 1
                                        and x.tags[0] == "imperfective"
                                    ][0]
                                    verb_pair_dict["rel_form"] = imperfective_form
                                    verb_pair_dict["rel_type"] = (
                                        EnumRelLemType.IMPERFECTIVE_PAIR_OF
                                    )
                                    sorted_data["rel_lems"].append(verb_pair_dict)
                                elif verbal_aspect == "imperfective":  # type:ignore
                                    perfective_form = [
                                        x.word
                                        for x in entry.forms
                                        if len(x.tags) == 1
                                        and x.tags[0] == "perfective"
                                    ][0]
                                    verb_pair_dict["rel_form"] = perfective_form
                                    verb_pair_dict["rel_type"] = (
                                        EnumRelLemType.PERFECTIVE_PAIR_OF
                                    )
                                    sorted_data["rel_lems"].append(verb_pair_dict)
                                else:
                                    logger.info("No verb pair found for %s", lem_text)
                            else:
                                temp_form_id = str(uuid.uuid4())
                                # logger.debug("lexicon tfid, entry_key, form: %s, %s, %s", temp_form_id, entry_key, form_word)
                                sorted_data["lexicon"].append(
                                    {
                                        "temp_form_id": temp_form_id,
                                        "entry_key": entry_key,  # To link to the lexicon entry
                                        "lex_text": form_word,
                                    }
                                )
                                for tag in form_tags:
                                    sorted_data["gram_props"].append(
                                        {
                                            "temp_form_id": temp_form_id,  # For load.py to find word_form_id
                                            "prop_name": tag,  # load.py will get-or-create this property
                                        }
                                    )
                        else:
                            # logging.debug(
                            #     "kicking out form/tag: %s - %s", form_word, form_tags
                            # )
                            continue

            # pronunciations
            # these link directly to the lexicon entry
            for pron in entry.pronunciations:
                sorted_data["pronunciations"].append(
                    {
                        "entry_key": entry_key,  # For load.py to find lexicon_id
                        "pron_text": pron.text,
                        "pron_type": EnumPronType.IPA if pron.type == "ipa" else None,
                        "pron_tags": pron.tags if len(pron.tags) > 0 else None,
                    }
                )

            # senses (definitions) and example sentences
            for sense in entry.senses:
                # Create a temp ID for this definition
                temp_def_id = str(uuid.uuid4())

                # check for global noun gram props in tags
                if pos == EnumPartOfSpeech.NOUN and len(sense.tags) > 0:
                    # logger.debug("sense tags: %s", sense.tags)
                    noun_sense_tag_set = {
                        "masculine",
                        "neuter",
                        "feminine",
                        "plural",
                        "animate",
                        "inanimate",
                    }
                    sense_tags_isxn = noun_sense_tag_set & set(sense.tags)
                    if sense_tags_isxn:
                        for tag in sense_tags_isxn:
                            # logger.debug("Noun sense tag: %s", tag)
                            lemma_dict_tags.append(tag)

                sorted_data["definitions"].append(
                    {
                        "temp_def_id": temp_def_id,
                        "entry_key": entry_key,  # To link to the lexicon entry
                        "def_text": sense.definition,
                        "def_tags": sense.tags,
                    }
                )

                # Link examples and quotes to this definition
                all_examples = sense.examples + sense.quotes
                for ex in all_examples:
                    # 'text' is the key for quotes
                    # logger.debug(type(ex), ex)
                    ex_text = ex.text if isinstance(ex, Quote) else ex
                    if ex_text and ex_text != "":
                        sorted_data["def_examples"].append(
                            {
                                "temp_def_id": temp_def_id,  # For load.py to find definition_id
                                "ex_text": ex_text,
                            }
                        )

            # Get rest of related words
            synonyms = entry.synonyms
            antonyms = entry.antonyms
            # all_nyms = synonyms + antonyms
            # logger.debug("%d *nyms: %s", len(all_nyms), all_nyms)
            if len(synonyms) > 0:
                for s in synonyms:
                    sorted_data["rel_lems"].append(
                        {
                            "entry_key": entry_key,
                            "rel_form": s,
                            "rel_type": EnumRelLemType.SYNONYM_OF,
                        }
                    )
            if len(antonyms) > 0:
                for a in antonyms:
                    sorted_data["rel_lems"].append(
                        {
                            "entry_key": entry_key,
                            "rel_form": a,
                            "rel_type": EnumRelLemType.ANTONYM_OF,
                        }
                    )
            # load up everything collected into lemma_dict
            # logger.debug("lemma_dict_tags: %s", lemma_dict_tags)
            lemma_dict_chars = self._map_lem_chars(pos.value, lemma_dict_tags)  # type: ignore
            # logger.debug("lemma_dict_chars: %s", lemma_dict_chars)
            lemma_dict = lemma_dict | lemma_dict_chars
            logger.debug("lemma_dict: %s", lemma_dict)

            # add lemma_dict to the data
            sorted_data["lemmas"].append(lemma_dict)

            # aug entry_index assignment
            entry_index += 1
        # logger.debug("sorted_data: %s", sorted_data)
        return sorted_data

    def process(self, word_data):

        try:
            unprocessed_word = FDAPIreturn(**word_data)
            this_word = unprocessed_word.word
            logger.info("Successfully validated %s", this_word)
        except ValidationError as e:
            logger.error("Failed to validate %s: %s", word_data, e)
            raise e
        except Exception as e:
            logger.error(
                "And unexpected error has occured while processing %s: %s",
                word_data.word,
                e,
            )
            raise e
        if this_word:
            # TODO get lexeme to query in DB
            sorted_entries_dict = self._sort_entries(
                this_word, unprocessed_word.entries
            )
            # logger.debug("sorted_entries_dict: %s", sorted_entries_dict)
            sorted_entries_dict = ProcessedPayload(**sorted_entries_dict)

            return sorted_entries_dict
        else:
            return []

    def run(self, word_data):
        return self.process(word_data=word_data)
