import logging
from typing import Any, Dict, Iterator, List

import requests
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

logger = logging.getLogger(__name__)

class LookupFDAPI:
    """
    A class to look up word definitions from the Free Dictionary API.
    """

    def __init__(self):
        # No need for self.result if the function is a generator
        pass

    def _make_request(self, word: str, lang: str = "ru") -> Dict[str, Any] | None:
        """
        Makes a single API request for a word and returns the JSON response
        as a dictionary.

        Args:
            word: The word to look up.
            lang: The language code for the lookup.

        Returns:
            A dictionary with the API response, or None if an error occurred.
        """
        try:
            r = requests.get(
                f"https://freedictionaryapi.com/api/v1/entries/{lang}/{word}",
                timeout=5
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching '%s': %s", word, e)
            return None

    def get(self, word_list: List[str]) -> Iterator[Dict[str, Any]]:
        """
        Looks up a list of words and yields the result for each one.
        This is a generator function.

        Args:
            word_list: A list of words to look up.

        Yields:
            A dictionary containing the API response for each successfully found word.
        """
        logger.info("Starting API lookup for %d words.", len(word_list))
        for word in word_list:
            # 1. Make the request for the current word.
            lemma_return = self._make_request(word)

            # 2. Check if the request was successful (i.e., not None).
            #    This replaces the _is_valid_json check.
            if lemma_return:
                # 3. If successful, yield the result to the pipeline.
                yield lemma_return
