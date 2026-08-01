# the lookup-process-load (ETL) pipeline
# import sys
import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from alite_backend.words.funcs import validate_word_list

# from alite_backend.words.lookup import LookupFDAPI
from alite_backend.words.lookup_parallel import LookupFDAPI
from alite_backend.words.process import ReturnedLemmaProcessor
from alite_backend.words.load import Loader

#
# LOCATIONS AND SETTINGS
#

# load environmental variables
load_dotenv()

# home location of files
save_dir_loc = os.getenv("APP_DIR")
logger = logging.getLogger(__name__)
logger.info("Starting run")


# def load_words(db: Session, word_s: list[str]):
#     """_summary_

#     Args:
#         db (Session): The active SQLAlchemy session passed in from the router or script.
#         word_s (list[str]): The list of words to look up.
#     """
#     # logger.info("Starting session for %s", word_s)

#     validate_word_list(word_s)
#     # init lookup class
#     fetcher = lfa()
#     # init processor class
#     processor = rlp()
#     # init loader class
#     loader = Loader(db_session=db)
#     # logger.info("Starting pull of %s", word_s)
#     results_stream = fetcher.get(word_s)

#     # The API call for each word happens as this loop runs.
#     for raw_data_dict in results_stream:
#         try:
#             # GET: Grab the raw dictionary data
#             # word_lemma = raw_data_dict.get("word", "unknown")
#             # logger.debug("Successfully looked up data for '%s':\n%s\n", word_lemma, raw_data_dict)

#             # PROCESS: Pass the raw dictionary to the processor
#             processed_payload = processor.process(raw_data_dict)

#             if processed_payload:
#                 # logger.debug("Successfully processed data for '%s':\n%s\n", word_lemma, processed_payload)

#                 # LOAD: Pass the processed payload to the Loader
#                 loader.load_payload(payload=processed_payload)  # type: ignore

#         except Exception as e:
#             logger.error(
#                 "Failed to process an item from the lookup stream: %s", e, exc_info=True
#             )

#     logger.info("Pipeline run finished.")


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
    db: Session, word_s: List[str], max_threads: int = 4, batch_size: int = 50
):
    """
    Bifurcated ETL pipeline. Processes cached words instantly,
    and threads uncached words over the network.
    """
    validate_word_list(word_s)

    fetcher = LookupFDAPI()
    processor = ReturnedLemmaProcessor()
    loader = Loader(db_session=db)

    # 1. BIFURCATION: Separate the fast path from the slow path
    cached_words = [w for w in word_s if w in fetcher.cache_data]
    uncached_words = [w for w in word_s if w not in fetcher.cache_data]

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

            # Flush batch if threshold is met
            if len(batch_payloads) >= batch_size:
                _flush_vocab_batch(db, loader, batch_payloads)
                batch_payloads.clear()
        except Exception as e:
            logger.error(f"Processing failed: {e}", exc_info=True)

    # 2. THE FAST PATH (Cache)
    for word in cached_words:
        _process_and_batch(fetcher.cache_data[word])

    # 3. THE SLOW PATH (Network)
    if uncached_words:
        with ThreadPoolExecutor(max_threads=max_threads) as executor:
            # Submit uncached words to the thread pool
            future_to_word = {
                executor.submit(_network_worker, w, fetcher): w for w in uncached_words
            }

            for future in as_completed(future_to_word):
                word, raw_data = future.result()

                if raw_data:
                    # update in-memory cache (Dict assignment is thread-safe in CPython)
                    fetcher.cache_data[word] = raw_data
                    new_words_fetched += 1

                    # Process the newly fetched data
                    _process_and_batch(raw_data)

    # 4. FINAL CLEANUP
    if batch_payloads:
        _flush_vocab_batch(db, loader, batch_payloads)

    if new_words_fetched > 0:
        fetcher.save_cache_to_disk()

    logger.info("Vocabulary pipeline run finished.")


def _flush_vocab_batch(db: Session, loader: Loader, payloads: List[Any]):
    """Safely loads a batch of processed words into the database."""
    try:
        for payload in payloads:
            loader.load_payload(payload=payload)
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database batch insertion failed. Rolling back. Error: {e}")
