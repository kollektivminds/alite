#
import logging
from pathlib import Path
from sqlalchemy.orm import Session
from alite_backend.db.db_session import SessionLocal
from alite_backend.sentences.loader import load_parsed_data
from alite_backend.sentences.parser import parse_tgt_file

logger = logging.getLogger(__name__)

# file_list = list_files_recursive(corpus_location, ff=True, sort=True)


def run_syntagrus_pipeline(db: Session, corpus_directory: str):
    """
    Orchestrates the extraction, transformation, and loading of SynTagRus files.
    """
    base_path = Path(corpus_directory)

    # find all .tgt files recursively using rglob
    tgt_files = list(base_path.rglob("*.tgt"))
    total_files = len(tgt_files)

    logger.info(f"Found {total_files} .tgt files. Beginning ETL pipeline.")

    # context manager ensures DB connections are gracefully closed
    with db as session:
        for idx, file_path in enumerate(tgt_files):
            logger.info(f"Processing [{idx+1}/{total_files}]: {file_path.name}")

            try:
                # extract & transform
                doc_data, sentences_data, tokens_data = parse_tgt_file(str(file_path))

                # load
                load_parsed_data(session, doc_data, sentences_data, tokens_data)

                # commit
                session.commit()

            except Exception as e:
                session.rollback()
                logger.error(f"Failed to process {file_path.name}. Error: {str(e)}")
                # optional: log the failed filepath to a text file for later review

    logger.info("SynTagRus ETL Pipeline Complete.")


if __name__ == "__main__":
    # Configure logging to see output in console
    logging.basicConfig(level=logging.INFO)

    # Run the pipeline
    corpus_location = "./raw/SynTagRus2022/"
    run_syntagrus_pipeline(corpus_location)
