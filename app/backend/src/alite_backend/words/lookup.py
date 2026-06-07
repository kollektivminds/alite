import logging
from typing import Any, Dict, Iterator, List
import os
import json
import time
from alite_backend.db.schemas import FDAPIreturn
import requests
from dotenv import load_dotenv

# Load environmental variables
load_dotenv()

logger = logging.getLogger(__name__)
app_dir = os.getenv("APP_DIR")
cache_loc = os.getenv("VOCAB_CACHE_LOC")


class LookupFDAPI:
    """
    A class to look up word definitions from the Free Dictionary API.
    """

    def __init__(self):
        # NB: no need for self.result if the function is a generator
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
                f"https://freedictionaryapi.com/api/v1/entries/{lang}/{word}", timeout=5
            )
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException as e:
            logger.error("Error fetching '%s': %s", word, e)
            return None

    def _check_local(
        self, word: str, cache_loc: str | None = cache_loc
    ) -> Dict[str, Any] | None:
        # check if the cache file exists and is not empty
        # cache file for init vocab to reduce API calls
        # logger.debug("Cache loc: %s", cache_loc)
        if os.path.exists(cache_loc):
            if os.path.getsize(cache_loc) > 0:
                with open(cache_loc, "r") as f:
                    data = json.load(f)
                logger.debug("words in cache: %d", len(data))
                if word in data:
                    # print(f"'{word}' found in cache.")
                    return data[word]

    def _update_cache(self, word: str, data: FDAPIreturn, cache_loc: str = cache_loc):
        # Read existing data
        if os.path.exists(cache_loc):
            with open(cache_loc, "r") as f:
                cache_data = json.load(f)
        else:
            raise KeyError

        # Add new data and write back to the file
        cache_data[word] = data
        with open(cache_loc, "w") as f:
            json.dump(cache_data, f, indent=4)

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
            try:
                # 1. Check for word in local cache
                addendum = self._check_local(word)
                # 2. Check if the request was successful (i.e., not None).
                if addendum:
                    # 3. If successful, yield the result to the pipeline.
                    logger.debug("%s was found in the database", word)
                    yield addendum
                else:
                    # 3. If unsuccessful, make the request for the current word.
                    logger.debug("need to fetch %s from FDAPI", word)
                    lemma_return = self._make_request(word)
                    # 4. Check if the request was successful (i.e., not None).
                    if lemma_return:
                        # 5. If successful, add to local cache
                        self._update_cache(word, lemma_return)
                        # 6. If successful, yield the result to the pipeline.
                        yield lemma_return
                    else:
                        logger.error("failed to get %s", word)
                time.sleep(0.5)
            except Exception as e:
                logger.error("There was an error looking up %s: %s", word, e)
                continue
