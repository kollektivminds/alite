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
from ..db.schemas import FDAPIreturn, ProcessedPayload
from .funcs import pos_dict, sop_dict, remove_accents, is_cyrillic, pos_list
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

    def _sort_entries(self, clean_lemma, entries):
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
                logger.error("%s is %s!!!", clean_lemma, language.name)
                continue
            elif "form of" in [x.tags for x in entry.senses][0]:
                logger.error(
                    "This word form (%s) was found but is not canonical (a lemma)",
                    clean_lemma,
                )
                # TODO catch these to put back in the queue if not already
                continue

            # lemma + pos make the entry key tuple
            pos = entry.partOfSpeech
            if not pos or pos not in pos_list:
                continue
            entry_name = f"{clean_lemma}_{pos}_{entry_index}"
            entry_key = uuid.uuid5(APP_NAMESPACE, entry_name)
            # logger.debug("entry: %s", entry_key)
            base_form_temp_id = str(uuid.uuid4())

            try:
                # logger.debug("forms items: %s", [x.word for x in entry.forms if x.tags[0] == 'canonical'][0])
                canonical_form = None
                if pos == "verb":
                    verbal_aspect = None
                    canonical_forms = ["canonical", "infinitive"]
                    verb_infin_form_object = [
                        x
                        for x in entry.forms
                        if any(item == "infinitive" for item in x.tags)
                    ]
                    logger.debug("verb infin form obj: %s", verb_infin_form_object)
                    for form in verb_infin_form_object:
                        tags = form.tags
                        # logger.debug("tags: %s", form.tags)
                        # logger.debug("word: %s", form.word)
                        if len(tags) == 2:
                            for tag in tags:
                                # logger.debug("tag: %s", tag)
                                if tag != "infinitive":
                                    verbal_aspect = tag
                            # logger.debug("form word: %s", form.word)
                        canonical_form = form.word
                        # logger.debug("first can form: %s", canonical_form)
                    verb_infin_lex_entry = {
                        "temp_form_id": base_form_temp_id,
                        "entry_key": entry_key,
                        "form": canonical_form,
                    }
                    # logger.debug("verb_infin_lex_entry: %s", verb_infin_lex_entry)
                    sorted_data["lexicon"].append(verb_infin_lex_entry)
                    sorted_data["gram_props"].append(
                        {
                            "temp_form_id": base_form_temp_id,
                            "prop_name": verbal_aspect,
                        }
                    )
                else:
                    canonical_object = [
                        x.word for x in entry.forms if "canonical" in x.tags
                    ]
                    logger.debug("canonical object: %s", canonical_object)
                    canonical_form = canonical_object[0]
                    if pos == "noun":
                        noun_base_lex_entry = {
                            "temp_form_id": base_form_temp_id,
                            "entry_key": entry_key,
                            "form": canonical_form,
                        }
                        logger.debug("noun base form lex entry: %s", noun_base_lex_entry)
                        sorted_data["lexicon"].append(noun_base_lex_entry)
                        if len(canonical_object) > 1:
                            for prop in canonical_object:
                                if prop != "canonical":
                                    logger.debug("other canonical noun gram prop: %s", prop)
                                    sorted_data["gram_props"].append(
                                        {
                                            "temp_form_id": base_form_temp_id,
                                            "prop_name": prop,
                                        }
                                    )

                logger.debug("canonical form: %s", canonical_form)
            except:
                canonical_form = None
                logger.error("No canonical form found for %s", clean_lemma)

            # make entry's lemma dict
            lemma_dict = {
                "clean_lemma": clean_lemma,
                "accent_lemma": canonical_form,
                "pos": pos,
                "entry_key": entry_key,
            }
            sorted_data["lemmas"].append(lemma_dict)

            # lexicon and gram_props
            for form in entry.forms:
                form_word = form.word
                if not form_word or form_word == "-":
                    continue
                form_tags = form.tags
                if not is_cyrillic(form_word):
                    # logger.debug("non-cyrillic form: %s (%s)", form_word, form_tags)
                    if "romanization" in form.tags:
                        sorted_data["pronunciations"].append(
                            {
                                "entry_key": entry_key,
                                "pron_text": form_word,
                                "pron_type": 1,
                                "pron_tags": "",
                            }
                        )
                    elif "class" in form.tags and pos == "verb":
                        # logger.debug("class & verb: %s", form_word)
                        re_pattern = r"(?P<verb_conj>.*?)\s(?P<verb_aspect>imperfective|perfective)\s(?P<verb_trans_refl>intransitive|transitive|reflexive)$"
                        match = re.search(re_pattern, form_word)
                        if match and base_form_temp_id:
                            # logger.debug("verb match: %s", match)
                            # verb_info = match.group(0)
                            # verb_conj = match.group(1)
                            # verb_aspect = match.group(2)
                            # verb_trans_refl = match.group(3)
                            for group_name, group_val in match.groupdict().items():
                                # logger.debug(
                                #     "verb class matching: %s = %s",
                                #     group_name,
                                #     group_val,
                                # )
                                sorted_data["gram_props"].append(
                                    {
                                        "temp_form_id": base_form_temp_id,
                                        "prop_name": group_val,
                                    }
                                )
                        else:
                            logger.debug("no class found for %s", clean_lemma)
                else:
                    # link all its tags as grammatical properties
                    tags_to_boot = ["dated", "alternative", "dialectical", "canonical"]
                    related_lemma_tags = [
                        "relational",
                        "adjective",
                        "noun-from-verb",
                        "adverb",
                        "abstract-noun",
                    ]
                    # logger.debug("tags: %s", tags)
                    if set(form_tags).isdisjoint(tags_to_boot):
                        # logger.debug("acceptable tags: %s - %s", form_word, form_tags)
                        # related words
                        if set(form_tags).intersection(related_lemma_tags):
                            logger.debug(
                                "related word tags %s: %s", form_word, form_tags
                            )
                            if "relational" in form_tags and "adjective" in form_tags:
                                rel_adj_dict = {
                                    "entry_key": entry_key,
                                    "pair_form": form_word,
                                    "rel_type": 2,
                                }
                                sorted_data["rel_lems"].append(rel_adj_dict)
                            elif (
                                len(form_tags) == 1 and form_tags[0] == "noun-from-verb"
                            ):
                                deverb_noun_dict = {
                                    "entry_key": entry_key,
                                    "pair_form": form_word,
                                    "rel_type": 3,
                                }
                                sorted_data["rel_lems"].append(deverb_noun_dict)
                            elif len(form_tags) == 1 and form_tags[0] == "adverb":
                                adverb_dict = {
                                    "entry_key": entry_key,
                                    "pair_form": form_word,
                                    "rel_type": 4,
                                }
                                sorted_data["rel_lems"].append(adverb_dict)
                            elif (
                                len(form_tags) == 1 and form_tags[0] == "abstract-noun"
                            ):
                                abstract_noun_dict = {
                                    "entry_key": entry_key,
                                    "pair_form": form_word,
                                    "rel_type": 5,
                                }
                                sorted_data["rel_lems"].append(abstract_noun_dict)
                        # verb pair
                        elif (
                            pos == "verb"
                            and len(form_tags) == 1
                            and re.match(r"imperfective|perfective", form_tags[0])
                        ):
                            # logger.debug("verb pair tags: %s", form_tags)
                            verb_pair_dict = {
                                "entry_key": entry_key,
                                "pair_form": None,
                                "rel_type": None,
                                "pair_aspect": None,
                            }
                            if verbal_aspect == "perfective":  # type:ignore
                                imperfective_form = [
                                    x.word
                                    for x in entry.forms
                                    if len(x.tags) == 1 and x.tags[0] == "imperfective"
                                ][0]
                                verb_pair_dict["pair_form"] = imperfective_form
                                verb_pair_dict["rel_type"] = 0
                                verb_pair_dict["pair_aspect"] = 0
                                sorted_data["rel_lems"].append(verb_pair_dict)
                            elif verbal_aspect == "imperfective":  # type:ignore
                                perfective_form = [
                                    x.word
                                    for x in entry.forms
                                    if len(x.tags) == 1 and x.tags[0] == "perfective"
                                ][0]
                                verb_pair_dict["pair_form"] = perfective_form
                                verb_pair_dict["rel_type"] = 1
                                verb_pair_dict["pair_aspect"] = 1
                                sorted_data["rel_lems"].append(verb_pair_dict)
                            else:
                                logger.info("No verb pair found for %s", clean_lemma)
                        else:
                            temp_form_id = str(uuid.uuid4())
                            # logger.debug("lexicon tfid, entry_key, form: %s, %s, %s", temp_form_id, entry_key, form_word)
                            sorted_data["lexicon"].append(
                                {
                                    "temp_form_id": temp_form_id,
                                    "entry_key": entry_key,  # To link to the lexicon entry
                                    "form": form_word,
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
                        "pron_type": 0 if pron.type == "ipa" else None,
                        "pron_tags": pron.tags if len(pron.tags) > 0 else None,
                    }
                )

            # senses (definitions) and example sentences
            for sense in entry.senses:
                # Create a temp ID for this definition
                temp_def_id = str(uuid.uuid4())
                
                # check for global noun gram props in tags
                if pos == "noun" and len(sense.tags) > 0:
                    logger.debug("sense tags: %s", sense.tags)
                    noun_sense_tag_set = {'masculine', 'neuter', 'feminine', 'plural', 'animate', 'inanimate'}
                    sense_tags_set = set(sense.tags)
                    sense_tags_isxn = noun_sense_tag_set & sense_tags_set
                    if sense_tags_isxn:
                        for tag in sense_tags_isxn:
                            sorted_data["gram_props"].append(
                                {
                                    "temp_form_id": base_form_temp_id,
                                    "prop_name": tag
                                }
                            )
                    
                sorted_data["definitions"].append(
                    {
                        "temp_def_id": temp_def_id,
                        "entry_key": entry_key,  # To link to the lexicon entry
                        "def_text": sense.definition,
                        "tags": sense.tags,
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
                                "def_example": ex_text,
                            }
                        )
                        
            # Get rest of related words
            synonyms = entry.synonyms
            antonyms = entry.antonyms
            all_nyms = synonyms + antonyms
            # logger.debug("%d *nyms: %s", len(all_nyms), all_nyms)
            if len(synonyms) > 0:
                for s in synonyms:
                    sorted_data["rel_lems"].append(
                        {
                            "entry_key": entry_key,
                            "pair_form": s,
                            "rel_type": 6
                        }
                    )
            if len(antonyms) > 0:
                for a in antonyms:
                    sorted_data["rel_lems"].append(
                        {
                            "entry_key": entry_key,
                            "pair_form": a,
                            "rel_type": 7
                        }
                    )
            
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
