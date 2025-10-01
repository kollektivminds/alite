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

from db.schemas import FDAPIreturn, ProcessedPayload
from pydantic import ValidationError

logger = logging.getLogger(__name__)

class ReturnedLemmaProcessor:
    """
    Functions to turn a WordClass object into a usable response
    """

    def __init__(
            self
        ):

        self.result = None
        
    def _handle_entries(self, entries):
        return_dict = None
        for entry in entries:
            entry_dict = {}
            pos = entry.partOfSpeech
            print("this is a %s", pos)
            if entry.language.code != 'ru':
                logger.error("%s is %s!!!", entry['word'], entry.language.name)
                #TODO keep these?
                continue
            elif 'form of' in [x.tags for x in entry.senses]:
                logger.error("This word form was found but is not canonical (a lemma)")
                #TODO catch these to put back in the queue if not already
                continue
            # 
            # pronunciations = entry.pronunciations
            # forms = entry.forms
            # senses = entry.senses
            
            # make lemma table entry (lemma_text, part_of_speech)
            load_to_lemma = {"lemma_text": entry['word'], "part_of_speech": pos}
            
            
            
            entry_dict['lemma'] = load_to_lemma
            
        return return_dict

    def process(self, word_data):
        final_payloads = []
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
            pass
        #
        entries = unprocessed_word.entries
        logger.debug("%d entries", len(entries))
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

        return final_payloads

    def run(self, word_data):
        return self.process(word_data=word_data)
