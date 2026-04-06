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
from alite_backend.db.crud import word_crud
#from .load import LoadDB as ldb

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

def feed_data(db: Session, word_s: list[str]):
    """_summary_

    Args:
        db (Session): The active SQLAlchemy session passed in from the router or script.
        word_s (list[str]): The list of words to look up.
    """
    logger.info("Starting session for %s", word_s)

    validate_word_list(word_s)
    # init lookup class
    fetcher = lfa()
    # init processor class
    processor = rlp()
    
    logger.info("Starting pull of %s", word_s)
    results_stream = fetcher.get(word_s)
    
    # The API call for each word happens as this loop runs.
    for raw_data_dict in results_stream:
        try:
            # GET: Grab the raw dictionary data
            word_lemma = raw_data_dict.get('word', 'unknown')
            #logger.debug("Successfully looked up data for '%s':\n%s\n", word_lemma, raw_data_dict)
            
            # PROCESS: Pass the raw dictionary to the processor
            processed_payload = processor.process(raw_data_dict)
            
            if processed_payload:
                logger.debug("Successfully processed data for '%s':\n%s\n", word_lemma, processed_payload)
                
                # LOAD: Pass the processed payload to the Loader
                

        except Exception as e:
            logger.error("Failed to process an item from the lookup stream: %s", e, exc_info=True)

    logger.info("Pipeline run finished.")
    
