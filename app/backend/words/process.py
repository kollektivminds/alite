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
from typing import List, Dict, Any, Tuple
from pydantic import ValidationError

from ..db.schemas import FDAPIreturn, ProcessedPayload
from .funcs import pos_dict, sop_dict, remove_accents

logger = logging.getLogger(__name__)
fixed_tags = {'canonical', 'romanization', 'table-tags'}

class ReturnedLemmaProcessor:
    """
    Functions to turn a WordClass object into a usable response
    """

    def __init__(
            self
        ):

        self.result = None

    def _sort_forms(forms: List[Dict[str, Any]], lemma_id: str) -> Tuple[Dict[str, str], List[Dict[str, Any]]]:
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
            f_tags = set(f['tags'])
            intersection = fixed_tags.intersection(f_tags)
            
            if intersection:
                # Use the first fixed tag found as the key (e.g., 'canonical')
                tag_name = intersection.pop()
                fixed_words[tag_name] = f['word']
            else:
                # Create a new dictionary structure for the rest of the forms
                new_form = {
                    'lemma_id': lemma_id,        # The UUID to tie this form back to the lemma
                    'form_word': f['word'],  # The actual word
                    'form_tags': f['tags'],  # The remaining tags (e.g., 'genitive', 'plural')
                    'form_id': str(uuid.uuid4()) # A unique ID for this specific form f
                }
                inflectional_forms.append(new_form)

        return fixed_words, inflectional_forms
        
    def _sort_entries(self, clean_lemma, entries):
        sorted_data = {
            "lemmas": [],
            "gram_props": [],
            "lexicon": [],
            "definitions": [],
            "def_sentences": [],
            "pronunciations": [],
            "verb_pairs": [],
        }
        lang_code = 'ru'
        for entry in entries:
            # gather basic data
            #logger.debug(entry)
            language = entry.language
            if language.code != lang_code:
                logger.error("%s is %s!!!", entry['word'], language.name)
                #TODO keep these?
                continue
            elif 'form of' in [x.tags for x in entry.senses]:
                logger.error("This word form was found but is not canonical (a lemma)")
                #TODO catch these to put back in the queue if not already
                continue
            
            # lemma + pos make the entry key tuple
            pos = entry.partOfSpeech
            if not pos:
                continue
            verbal_aspect = None
            try:
                #logger.debug("forms items: %s", [x.word for x in entry.forms if x.tags[0] == 'canonical'][0])
                canonical_form = None
                verbal_aspect = None
                canonical_forms = ['canonical', 'infinitive']
                if pos == 'verb':
                    canonical_form_object = [x for x in entry.forms if any(item in canonical_forms for item in x.tags)]
                    #logger.debug("can form obj: %s", canonical_form_object)
                    for form in canonical_form_object:
                        tags = form.tags
                        #logger.debug("tags: %s", form.tags)
                        #logger.debug("word: %s", form.word)
                        if (len(tags) == 2) & ("infinitive" in tags):
                            for tag in tags:
                                #logger.debug("tag: %s", tag)
                                if tag != "infinitive":
                                    verbal_aspect = tag
                            #logger.debug("form word: %s", form.word)
                            canonical_form = form.word
                            #logger.debug("first can form: %s", canonical_form)
                    if not canonical_form:
                        canonical_form = [x.word for x in entry.forms if x.tags[0] == 'canonical'][0]
                    if verbal_aspect:
                        #logger.debug("verbal aspect: %s", verbal_aspect)
                        pass
                    #logger.debug("verb canonical: %s", canonical_form)
                else:
                    canonical_form = [x.word for x in entry.forms if x.tags[0] == 'canonical'][0]
                logger.debug("canonical form: %s", canonical_form)
            except:
                canonical_form = None
                logger.error("No canonical form found for %s", clean_lemma)

            # make entry's lemma dict
            lemma_dict = {
                "clean_lemma": clean_lemma,
                "accent_lemma": canonical_form,
                "pos": sop_dict.get(pos)
            }
            sorted_data['lemmas'].append(lemma_dict)
            
            entry_key = (canonical_form, pos)
            #logger.debug("entry: %s", entry_key)

            # lexicon and gram_props
            for form in entry.forms:
                form_word = form.word
                if not form_word or form_word == '-':
                    continue

                # Create a temp ID for this specific word form
                temp_form_id = str(uuid.uuid4())
                
                sorted_data['lexicon'].append({
                    "temp_id": temp_form_id,
                    "temp_lexicon_id": entry_key, # To link to the lexicon entry
                    "form": form_word
                })

                # link all its tags as grammatical properties
                tags = form.tags
                #logger.debug("tags: %s", tags)
                for tag in tags:
                    sorted_data['gram_props'].append({
                        "temp_form_id": temp_form_id, # For load.py to find word_form_id
                        "prop_name": tag # load.py will get-or-create this property
                    })

            # 6. Verb Pairs (Special case while looping forms)
            if pos == 'verb' and verbal_aspect:
                if verbal_aspect == "perfective":
                    imperfective_form = [x.word for x in entry.forms if len(x.tags) == 1 and x.tags[0] == 'imperfective'][0]
                    sorted_data['verb_pairs'].append(imperfective_form)
                elif verbal_aspect == "imperfective":
                    perfective_form = [x.word for x in entry.forms if len(x.tags) == 1 and x.tags[0] == 'perfective'][0]
                    sorted_data['verb_pairs'].append(perfective_form)
            elif pos == 'verb' and not verbal_aspect:
                logger.info("No verb pair found for %s", canonical_form)

            # pronunciations
            # these link directly to the lexicon entry
            for pron in entry.pronunciations:
                sorted_data['pronunciations'].append({
                    "temp_lexicon_id": entry_key, # For load.py to find lexicon_id
                    "text": pron.text,
                    "type": pron.type,
                    "tags": pron.tags
                })

            # senses (definitions) and example sentences
            for sense in entry.senses:
                # Create a temp ID for this definition
                temp_def_id = str(uuid.uuid4())
                
                sorted_data['definitions'].append({
                    "temp_id": temp_def_id,
                    "temp_lexicon_id": entry_key, # To link to the lexicon entry
                    "definition_text": sense.definition,
                    "tags": sense.tags
                })
                
                # Link examples and quotes to this definition
                all_examples = sense.examples + sense.quotes
                for ex in all_examples:
                    # 'text' is the key for quotes
                    sentence_text = ex.text if 'text' in ex else ex
                    if sentence_text:
                        sorted_data['def_sentences'].append({
                            "temp_def_id": temp_def_id, # For load.py to find definition_id
                            "sentence": sentence_text
                        })
            
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
            logger.error("And unexpected error has occured while processing %s: %s", word_data.word, e)
            raise e
        if this_word:
            #TODO get lexeme to query in DB
            sorted_entries_dict = self._sort_entries(this_word, unprocessed_word.entries)
            #logger.debug(sorted_entries_dict)
            
            return sorted_entries_dict
        else:
            return []
        #
        #entries = unprocessed_word.entries
        #logger.debug("%d entries", len(entries))
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
