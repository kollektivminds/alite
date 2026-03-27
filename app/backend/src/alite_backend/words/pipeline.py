# the lookup-process-load pipeline
#import sys
import logging
import os

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .funcs import validate_word_list
from .logging_config import setup_logging
from .lookup import LookupFDAPI as lfa
from .process import ReturnedLemmaProcessor as rlp

#from load import LoadDB as ldb

setup_logging()

#
# LOCATIONS AND SETTINGS
#

# load environmental variables
load_dotenv()

# home location of files
save_dir_loc = os.getenv("APP_DIR")
logger = logging.getLogger(__name__)
logger.info("Starting run")

def feed_data(word_s: list[str]):
    """_summary_

    Args:
        word_s (list[str]): _description_

    Returns:
        _type_: _description_
    """
    logger.info("Starting session for %s", word_s)

    # TODO DB session loader
    #loader = ldb(db_session=db_session)
    #, db_session: Session

    validate_word_list(word_s)
    # init lookup class
    fetcher = lfa()
    # init processor class
    processor = rlp()
    # init loader class
    #loader = ldb()
    logger.info("Starting pull of %s", word_s)
    results_stream = fetcher.get(word_s)
    # The API call for each word happens as this loop runs.
    for raw_data_dict in results_stream:
        try:
            # a. PROCESS: Pass the raw dictionary to the processor
            word_lemma = raw_data_dict.get('word', 'unknown')
            logger.debug("Successfully looked up data for '%s':\n%s\n", word_lemma, raw_data_dict)
            
            # b. LOAD: Pass the clean, final payload to your loader
            processed_payload = processor.process(raw_data_dict)
            if processed_payload:
                logger.debug("Successfully processed data for '%s':\n%s\n", word_lemma, processed_payload)
                #loader.load_to_db(processed_payload)

        except Exception as e:
            logger.error("Failed to process an item from the lookup stream: %s", e, exc_info=True)

    logger.info("Pipeline run finished.")
    
