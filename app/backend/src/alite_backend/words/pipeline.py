# the lookup-process-load (ETL) pipeline
# import sys
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from alite_backend.db import models
from alite_backend.words.funcs import validate_word_list
from alite_backend.words.load import Loader

# from alite_backend.words.lookup import LookupFDAPI
from alite_backend.words.lookup_parallel import LookupFDAPI
from alite_backend.words.process import ReturnedLemmaProcessor
from bleach import clean
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

#
# LOCATIONS AND SETTINGS
#

# load environmental variables
load_dotenv()

# home location of files
save_dir_loc = os.getenv("APP_DIR")
logger = logging.getLogger(__name__)
logger.info("Starting run")


def _network_worker(
    word: str, fetcher: LookupFDAPI
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Executes in a separate thread. Sleeps to respect rate limits, then fetches.
    """
    time.sleep(0.5)
    raw_data = fetcher.fetch_from_api(word)
    return word, raw_data


def load_words(
    db: Session, word_s: List[str], max_workers: int = 4, batch_size: int = 50
):
    """
    Bifurcated ETL pipeline. Processes cached words instantly,
    and threads uncached words over the network.
    """
    validate_word_list(word_s)

    fetcher = LookupFDAPI()
    processor = ReturnedLemmaProcessor()
    loader = Loader(db_session=db)

    clean_words = [w.strip().lower() for w in word_s]

    # separate cache and uncached words
    cached_words = [w for w in clean_words if w in fetcher.cache_data]
    uncached_words = [w for w in clean_words if w not in fetcher.cache_data]

    logger.info(
        f"Pipeline started. {len(cached_words)} cached, {len(uncached_words)} uncached."
    )

    batch_payloads = []
    new_words_fetched = 0

    def _process_and_batch(raw_data: Dict[str, Any]):
        """Helper to process JSON and queue it for DB insertion."""
        try:
            processed_payload = processor.process(raw_data)
            if processed_payload:
                batch_payloads.append(processed_payload)

            # flush batch if threshold is met
            if len(batch_payloads) >= batch_size:
                _flush_vocab_batch(db, loader, batch_payloads)
                batch_payloads.clear()
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)

    # get cached words
    for word in cached_words:
        _process_and_batch(fetcher.cache_data[word])

    # get uncached words from the internet
    if uncached_words:
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # type: ignore
            # submit uncached words to the thread pool
            future_to_word = {
                executor.submit(_network_worker, w, fetcher): w for w in uncached_words
            }

            for future in as_completed(future_to_word):
                word, raw_data = future.result()

                if raw_data:
                    # update in-memory cache (Dict assignment is thread-safe in CPython)
                    fetcher.cache_data[word] = raw_data
                    new_words_fetched += 1

                    # process the newly fetched data
                    _process_and_batch(raw_data)
                else:
                    logger.warning(f"API returned no data for '{word}'")

    # cleanup
    if batch_payloads:
        _flush_vocab_batch(db, loader, batch_payloads)

    if new_words_fetched > 0:
        fetcher.save_cache_to_disk()

    logger.info("Vocabulary pipeline run finished.")

    stmt = select(models.Lemma).where(models.Lemma.lem_text.in_(clean_words))  # type: ignore
    return list(db.scalars(stmt).all())


def _flush_vocab_batch(db: Session, loader: Loader, payloads: List[Any]):
    """Safely loads a batch of processed words into the database."""
    try:
        for payload in payloads:
            loader.load_payload(payload=payload)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database batch insertion failed. Rolling back. Error: {e}")
