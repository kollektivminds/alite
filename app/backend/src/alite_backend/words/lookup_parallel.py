# alite_backend/words/lookup.py
import logging
import os
import json
import requests
from typing import Any, Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
cache_loc = os.getenv("VOCAB_CACHE_LOC")


class LookupFDAPI:
    """
    Manages API lookups and an in-memory cache to prevent disk I/O bottlenecks.
    """

    def __init__(self, cache_path: str = cache_loc):  # type: ignore
        self.cache_path = cache_path
        self.cache_data = self._initialize_cache()

    def _initialize_cache(self) -> Dict[str, Any]:
        """Loads the cache into memory exactly ONCE during initialization."""
        if self.cache_path and os.path.exists(self.cache_path):
            if os.path.getsize(self.cache_path) > 0:
                with open(self.cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    logger.debug(f"Loaded {len(data)} words into memory cache.")
                    return data
        return {}

    def save_cache_to_disk(self) -> None:
        """Flushes the in-memory cache back to disk at the end of the pipeline."""
        if not self.cache_path:
            return

        with open(self.cache_path, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, indent=4, ensure_ascii=False)
        logger.info("Vocabulary cache successfully synced to disk.")

    def fetch_from_api(self, word: str, lang: str = "ru") -> Optional[Dict[str, Any]]:
        """
        ISOLATED NETWORK WORKER: Makes a single API request.
        Safe to run concurrently in a ThreadPoolExecutor.
        """
        try:
            r = requests.get(
                f"https://freedictionaryapi.com/api/v1/entries/{lang}/{word}", timeout=5
            )
            r.raise_for_status()

            # The API returns a list; extract the first entry to match your schema
            response_data = r.json()
            return (
                response_data[0] if isinstance(response_data, list) else response_data
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching '{word}' from API: {e}")
            return None
