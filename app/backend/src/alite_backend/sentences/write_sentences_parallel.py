# app/backend/sentences/parallel_pipeline.py
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from alite_backend.db.db_session import SessionLocal
from alite_backend.sentences.parser import parse_tgt_file
from alite_backend.sentences.loader import load_parsed_data

logger = logging.getLogger(__name__)

# Type alias for readability
ParsedData = Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]


def _parsing_worker(file_path: Path) -> ParsedData | None:
    """
    ISOLATED WORKER FUNCTION: Executes in a separate CPU process.
    Reads the file, parses the XML, and returns the dictionaries.
    Strictly performs NO database operations to prevent connection pool corruption.
    """
    try:
        # Calls your existing, Pandas-free XML parser
        return parse_tgt_file(str(file_path))
    except Exception as e:
        logger.error(f"Worker failed to parse {file_path.name}: {e}")
        return None


def run_parallel_sentence_pipeline(
    db: Session, corpus_directory: str, max_workers: int = 4, batch_size: int = 50
):
    """
    Orchestrates the parallel extraction and batched database loading.

    Args:
        corpus_directory: Path to the SynTagRus XML files.
        max_workers: Number of CPU cores to utilize. Defaults to 4.
        batch_size: How many documents to accumulate before flushing to the DB.
    """
    base_path = Path(corpus_directory)
    tgt_files = list(base_path.rglob("*.tgt"))
    total_files = len(tgt_files)

    logger.info(
        f"Starting parallel ETL for {total_files} files using {max_workers} workers."
    )

    # We use a context manager for the executor to guarantee process cleanup
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Scatter: Submit all file paths to the process pool
        # future_to_file maps the Future object back to the file path for error logging
        future_to_file = {
            executor.submit(_parsing_worker, filepath): filepath
            for filepath in tgt_files
        }

        # initialize batch aggregators
        batch_docs: List[Dict[str, Any]] = []
        batch_sents: List[List[Dict[str, Any]]] = []
        batch_tokens: List[List[Dict[str, Any]]] = []
        files_processed = 0

        # gather: iterate over results exactly as they complete
        for future in as_completed(future_to_file):
            file_path = future_to_file[future]

            try:
                result = future.result()
                if result is None:
                    continue  # Skip files that failed the parsing phase

                doc_data, sents_data, tokens_data = result

                # Aggregate the data
                batch_docs.append(doc_data)
                batch_sents.append(sents_data)
                batch_tokens.append(tokens_data)

                files_processed += 1

                # If our batch has reached the target size, flush it to the DB
                if len(batch_docs) >= batch_size:
                    _flush_batch_to_db(db, batch_docs, batch_sents, batch_tokens)
                    logger.info(
                        f"Processed and loaded {files_processed}/{total_files} documents."
                    )

                    # Clear the batch aggregators to free up RAM
                    batch_docs, batch_sents, batch_tokens = [], [], []

            except Exception as e:
                logger.error(f"Fatal error retrieving result for {file_path.name}: {e}")

        # Flush any remaining documents in the final, partial batch
        if batch_docs:
            _flush_batch_to_db(db, batch_docs, batch_sents, batch_tokens)
            logger.info(
                f"Final batch processed. Total: {files_processed}/{total_files} documents."
            )


def _flush_batch_to_db(
    db: Session,
    docs: List[Dict[str, Any]],
    sents: List[Dict[str, Any]],
    tokens: List[Dict[str, Any]],
) -> None:
    """
    MAIN THREAD FUNCTION: Executes the database inserts.
    Takes a batch of aggregated document data and pushes it to PostgreSQL.
    """
    with db as session:
        try:
            # loop through the batch and load them.
            for doc, sent_list, token_list in zip(docs, sents, tokens):
                load_parsed_data(session, doc, sent_list, token_list)

            # Commit the entire batch as a single atomic transaction
            session.commit()

        except SQLAlchemyError as e:
            # If any document in the batch causes an integrity error,
            # the entire batch is rolled back to preserve DB cleanliness.
            session.rollback()
            logger.error(
                f"Database insertion failed for batch. Rolling back. Error: {e}"
            )
