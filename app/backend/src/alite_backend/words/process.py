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
from .funcs import pos_dict, sop_dict, remove_accents, is_cyrillic
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

    def _sort_forms(
        forms: List[Dict[str, Any]], lemma_id: str
    ) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
        """
        Separates fixed words from inflectional forms and assigns a UUID to the remaining forms.

        Returns:
            A tuple: (fixed_words_dict, inflectional_forms_list)
        """
        fixed_words = {}
        inflectional_forms = []

        for f in forms:
            # Check if any of the f's tags intersect with the FIXED_TAGS set
            # We assume the fixed tags are unique identifiers for these specific words
            f_tags = set(f["tags"])
            intersection = fixed_tags.intersection(f_tags)

            if intersection:
                # Use the first fixed tag found as the key (e.g., 'canonical')
                tag_name = intersection.pop()
                fixed_words[tag_name] = f["word"]
            else:
                # Create a new dictionary structure for the rest of the forms
                new_form = {
                    "lemma_id": lemma_id,  # The UUID to tie this form back to the lemma
                    "form_word": f["word"],  # The actual word
                    "form_tags": f[
                        "tags"
                    ],  # The remaining tags (e.g., 'genitive', 'plural')
                    "form_id": str(
                        uuid.uuid4()
                    ),  # A unique ID for this specific form f
                }
                inflectional_forms.append(new_form)

        return fixed_words, inflectional_forms

    def _sort_entries(self, clean_lemma, entries):
        sorted_data = {
            "lemmas": [],
            "gram_props": [],
            "lexicon": [],
            "definitions": [],
            "def_examples": [],
            "pronunciations": [],
            "verb_pairs": [],
        }
        lang_code = "ru"
        entry_index = 0
        for entry in entries:
            # gather basic data
            # logger.debug(entry)
            language = entry.language
            #logger.debug("entry senses tags: %s", [x.tags for x in entry.senses][0])
            if language.code != lang_code:
                logger.error("%s is %s!!!", clean_lemma, language.name)
                # TODO keep these?
                continue
            elif "form of" in [x.tags for x in entry.senses][0]:
                logger.error("This word form (%s) was found but is not canonical (a lemma)", clean_lemma)
                # TODO catch these to put back in the queue if not already
                continue

            # lemma + pos make the entry key tuple
            pos = entry.partOfSpeech
            if not pos:
                continue
            entry_name = f"{clean_lemma}_{pos}_{entry_index}"
            entry_key = uuid.uuid5(APP_NAMESPACE, entry_name)
            # logger.debug("entry: %s", entry_key)
            
            try:
                # logger.debug("forms items: %s", [x.word for x in entry.forms if x.tags[0] == 'canonical'][0])
                canonical_form = None
                verbal_aspect = None
                canonical_forms = ["canonical", "infinitive"]
                if pos == "verb":                    
                        verb_infin_temp_id = str(uuid.uuid4())
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
                            "temp_form_id": verb_infin_temp_id,
                            "entry_key": entry_key,
                        }
                        logger.debug("verb_infin_lex_entry: %s", verb_infin_lex_entry)
                        sorted_data["lexicon"].append(verb_infin_lex_entry)
                        sorted_data["gram_props"].append(
                            {
                                "temp_form_id": verb_infin_temp_id,
                                "verb_aspect": verbal_aspect
                            }
                        )
                        #if not canonical_form:
                        #    canonical_form = [
                        #        x.word for x in entry.forms if x.tags[0] == "canonical"
                        #    ][0]
                        # if verbal_aspect:
                        # logger.debug("verbal aspect: %s", verbal_aspect)
                        # pass
                        # logger.debug("verb canonical: %s", canonical_form)
                else:
                    canonical_form = [
                        x.word for x in entry.forms if "canonical" in x.tags
                    ][0]
                logger.debug("canonical form: %s", canonical_form)
            except:
                canonical_form = None
                logger.error("No canonical form found for %s", clean_lemma)

            # make entry's lemma dict
            lemma_dict = {
                "clean_lemma": clean_lemma,
                "accent_lemma": canonical_form,
                "pos": sop_dict.get(pos),
                "entry_key": entry_key
            }
            sorted_data["lemmas"].append(lemma_dict)
            
            # lexicon and gram_props
            for form in entry.forms:
                form_word = form.word
                if not form_word or form_word == "-":
                    continue
                else:
                    if not is_cyrillic(form_word):
                        logger.debug("non-cyrillic form: %s (%s)", form_word, form.tags)
                        if "romanization" in form.tags:
                            sorted_data["pronunciations"].append(
                                {
                                "entry_key": entry_key,
                                "pron_text": form_word,
                                "pron_type": 1,
                                "pron_tags": ""                             
                                }
                            )
                        elif "class" in form.tags and pos == "verb":
                            logger.debug("class & verb: %s", form_word)
                            re_pattern = r"(?P<verb_conj>.*)\s(?P<verb_aspect>i?m?perfective)\s(?P<verb_trans_refl>i?n?transitive)"
                            match = re.search(re_pattern, form_word)
                            logger.debug("verb match: %s", match)
                            #verb_info = match.group(0)
                            #verb_conj = match.group(1)
                            #verb_aspect = match.group(2)
                            #verb_trans_refl = match.group(3)
                            for group_name, group_val in match.groupdict().items():
                                logger.debug("verb class matching: %s = %s", group_name, group_val)
                                sorted_data["gram_props"].append(
                                    {
                                        "temp_form_id": verb_infin_temp_id,
                                        group_name: group_val
                                    }
                            )
                    else:
                        # link all its tags as grammatical properties
                        tags = form.tags
                        tags_to_boot = [
                            "dated", "alternative", "dialectical"
                        ]
                        # logger.debug("tags: %s", tags)
                        if set(tags).isdisjoint(tags_to_boot):
                            logger.debug("acceptable tags: %s - %s", form_word, tags)
                            temp_form_id = str(uuid.uuid4())
                            #logger.debug("lexicon tfid, entry_key, form: %s, %s, %s", temp_form_id, entry_key, form_word)
                            sorted_data["lexicon"].append(
                                {
                                    "temp_form_id": temp_form_id,
                                    "entry_key": entry_key,  # To link to the lexicon entry
                                    "form": form_word,
                                }
                            )
                            
                            for tag in tags:
                                sorted_data["gram_props"].append(
                                    {
                                        "temp_form_id": temp_form_id,  # For load.py to find word_form_id
                                        "prop_name": tag,  # load.py will get-or-create this property
                                    }
                                )
                        else:
                            logging.debug("kicking out form/tag: %s - %s", form_word, tags)
                            continue

            # 6. Verb Pairs (Special case while looping forms)
            if pos == "verb":
                verb_pair_dict = {
                    "entry_key": entry_key,
                    "pair_form": None,
                    "pair_aspect": None
                }
                if verbal_aspect == "perfective":  # type:ignore
                    imperfective_form = [
                        x.word
                        for x in entry.forms
                        if len(x.tags) == 1 and x.tags[0] == "imperfective"
                    ][0]
                    verb_pair_dict['pair_form'] = imperfective_form
                    verb_pair_dict['pair_aspect'] = 0
                    sorted_data["verb_pairs"].append(verb_pair_dict)
                elif verbal_aspect == "imperfective":  # type:ignore
                    perfective_form = [
                        x.word
                        for x in entry.forms
                        if len(x.tags) == 1 and x.tags[0] == "perfective"
                    ][0]
                    verb_pair_dict['pair_form'] = perfective_form
                    verb_pair_dict['pair_aspect'] = 1
                    sorted_data["verb_pairs"].append(verb_pair_dict)
                else:
                    logger.info("No verb pair found for %s", canonical_form)

            # pronunciations
            # these link directly to the lexicon entry
            for pron in entry.pronunciations:
                sorted_data["pronunciations"].append(
                    {
                        "entry_key": entry_key,  # For load.py to find lexicon_id
                        "pron_text": pron.text,
                        "pron_type": 0 if pron.type == 'ipa' else None,
                        "pron_tags": pron.tags if len(pron.tags) > 0 else None,
                    }
                )

            # senses (definitions) and example sentences
            for sense in entry.senses:
                # Create a temp ID for this definition
                temp_def_id = str(uuid.uuid4())

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
                    #logger.debug(type(ex), ex)
                    ex_text = ex.text if isinstance(ex, Quote) else ex
                    if ex_text and ex_text != '':
                        sorted_data["def_examples"].append(
                            {
                                "temp_def_id": temp_def_id,  # For load.py to find definition_id
                                "def_example": ex_text,
                            }
                        )
            entry_index += 1
        logger.debug("sorted_data: %s", sorted_data)
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
            #logger.debug("sorted_entries_dict: %s", sorted_entries_dict)
            sorted_entries_dict = ProcessedPayload(**sorted_entries_dict)

            return sorted_entries_dict
        else:
            return []
        #
        # entries = unprocessed_word.entries
        # logger.debug("%d entries", len(entries))
        # verify the lang is Russian

        # pronunciations (type='ipa', text=?)

        # forms
        # lemma = tags: ['canonical']
        # romanization = tags: ['romanization']
        # other interesting tags: dimunitive, class (stem, accent), adjective
        # noun-from-verb, table-tags, inflection-template
        # if 'dated' in tags: remove(word)
        # table-tags unique in tags per general form?
        # lemma = tags: ['canonical']
        # transitivity, reflexivity in forms.tags=table-tags
        # verb conj, transitivity, reflexivity in forms.tags=class (but not unique)
        # participles searched as is must be specified as 'adjectives'

    def run(self, word_data):
        return self.process(word_data=word_data)
