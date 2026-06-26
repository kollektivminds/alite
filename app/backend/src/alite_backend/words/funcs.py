"""Functions to support database fetching, processing, loading, etc.

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
import json
import logging
import os
import unicodedata
import re
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text
import alite_backend.db.schemas as schemas
from alite_backend.db.schemas import EnumVerbType

load_dotenv()

VOCAB_LIST_LOC = os.getenv("VOCAB_LIST_LOC")

# instantiate logger
logger = logging.getLogger(__name__)

pos_list = [
    "adjective",
    "adverb",
    "com",
    "conjunction",
    "interjection",
    "noun",
    "numeral",
    "participle",
    "particle",
    "preposition",
    "pronoun",
    "verb",
    "unknown",
]

pos_dict = dict(enumerate(pos_list))

sop_dict = {v: k for k, v in pos_dict.items()}

cases = [
    "nominative",
    "genitive",
    "dative",
    "accusative",
    "instrumental",
    "prepositional",
]

numbers = ["singular", "plural"]

genders = ["masculine", "neuter", "feminine"]

#
# AUXILIARY FUNCTIONS
#


# save_json function
def save_json(json_object, file_path):
    """
    Saves Python Dict object as serialized JSON object
    """
    with open(file_path, "w") as file:
        json.dump(json_object, file, indent=4)


# load_json function
def load_json(file_path):
    """
    Loads JSON data from a file.

    Args:
        file_path (str): The path to the JSON file.

    Returns:
        dict or list: The deserialized JSON data as a Python object, or None if an error occurs.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        logger.error("Error: File not found: %s", file_path)
        return None
    except json.JSONDecodeError:
        logger.error("Error: Invalid JSON format in file: %s", file_path)
        return None
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)
        return None


def remove_accents(input_str: str) -> str:
    """
    Removes ONLY the acute accent mark (stress mark) from a string,
    while preserving essential diacritics on letters like 'й' and 'ё'.
    e.g., "восстанови́ть" -> "восстановить"
    """
    if not isinstance(input_str, str):
        return input_str  # Return non-strings as they are

    # The specific Unicode character for the combining acute accent
    COMBINING_ACUTE_ACCENT = "\u0301"

    # Normalize to NFD to separate all combining marks
    nfd_form = unicodedata.normalize("NFD", input_str)

    # Filter out ONLY the acute accent mark and rejoin
    return "".join([c for c in nfd_form if c != COMBINING_ACUTE_ACCENT])


def map_words_in_cell(cell_text, word_map):
    if pd.isna(cell_text):  # Handle potential NaN values
        return np.nan
    words = str(cell_text).split(" or ")  # Split the string into words
    mapped_words = []
    missing_words = []
    for word in words:
        if word in word_map:
            mapped_words.append(word_map[word])  # Convert index to string
        else:
            mapped_words.append(word)  # Keep the original word if not found
            missing_words.append(word)
    return " ".join(
        [str(x) for x in mapped_words]
    )  # Join the mapped words back into a string


def assign_verb_pair(cell_string, pairMappingDict):
    if isinstance(cell_string, str):
        new_string = cell_string.split(" or ")
        new_string = [pairMappingDict.get(x) for x in new_string]

        return new_string

    else:
        return None


def strip_non_alpha_start(text):
    for i, char in enumerate(text):
        if char.isalpha():
            return text[i:]
    return ""


def clean_dict_values(d):
    """Applies the clean_string function to each value in a dictionary."""
    if isinstance(d, dict):
        return {k: strip_non_alpha_start(v) for k, v in d.items()}
    return d


def validate_word_list(word_list):
    # check if word_list is indeed a list of words
    # or at least a single word that can be recognized
    # TODO add some logic to pull out problematic words instead of stopping things
    if not isinstance(word_list, list) and all(
        isinstance(word, str) and word.isalpha() for word in word_list
    ):
        try:
            word_list.isalpha()
        except:
            raise TypeError("not alpha")


def is_cyrillic(text: str) -> bool:
    return bool(re.search(r"[А-Яа-яËё]", text))


def zalizniak_to_type(z_type: str) -> EnumVerbType:
    t2_pattern = r"^4"
    match = re.match(t2_pattern, z_type)
    if match:
        return EnumVerbType.TYPE_II
    else:
        return EnumVerbType.TYPE_I
