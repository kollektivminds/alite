import argparse
import logging
import sys
from typing import Optional

from alite_backend.db import models
from alite_backend.db.db_session import SessionLocal
from alite_backend.words.funcs import remove_accents
from alite_backend.words.pipeline import load_words
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

print(f"--> EXECUTING QUEUE FROM: {__file__}")

logger = logging.getLogger(__name__)


def process_lookup_queue(
    db: Session,
    batch_limit: Optional[int] = 4,
    target_item_id: Optional[int] = None,
) -> int:
    """
    Processes items from the lookup_queue.

    Args:
        db: Active SQLAlchemy database session.
        batch_limit: Max number of items to process in this execution run.
        target_item_id: Optional specific LookupQueue ID to run in isolation.

    Returns:
        int: Number of items successfully processed.
    """
    attempted_ids = set()
    processed_count = 0

    while True:
        # enforce batch limits to prevent unintended full-table processing
        if batch_limit is not None and processed_count >= batch_limit:
            logger.info(
                f"Reached batch limit of {batch_limit} item(s). Stopping execution."
            )
            break

        # build query based on whether we are targeting one item or pulling pending items
        query = db.query(models.LookupQueue)

        if target_item_id is not None:
            # Single-item target mode: query explicitly for the requested ID
            query = query.filter(models.LookupQueue.id == target_item_id)  # type: ignore
        else:
            # Batch mode: filter for UNLINKED/FAILED items not yet tried in this run
            query = query.filter(
                models.LookupQueue.status.in_(  # type: ignore
                    [
                        models.EnumLookupStatus.UNLINKED,
                        models.EnumLookupStatus.FAILED,
                    ]
                ),
                models.LookupQueue.id.notin_(attempted_ids),  # type: ignore
            )

        queue_item = query.first()

        # Stop if no matching items remain
        if not queue_item:
            if target_item_id:
                logger.warning(
                    f"Target LookupQueue item ID {target_item_id} not found."
                )
            break

        item_id = queue_item.id
        attempted_ids.add(item_id)

        try:
            target_lem_accented = str(queue_item.target_lem).strip()
            target_lem_clean = remove_accents(target_lem_accented)

            new_lemma = None

            # 3. Cache Check: Check local DB before invoking external pipeline
            existing_lemma = (
                db.query(models.Lemma)
                .filter(
                    (models.Lemma.lem_text == target_lem_clean)  # type: ignore
                    | (models.Lemma.lem_canon == target_lem_accented)  # type: ignore
                )
                .first()
            )
            # breakpoint()
            if existing_lemma:
                logger.info(
                    f"Found '{target_lem_clean}' in local DB. Bypassing pipeline."
                )
                new_lemma = existing_lemma
            else:
                logger.info(
                    f"'{target_lem_clean}' not found locally. Executing pipeline..."
                )
                loaded_lemmas = load_words(db, [target_lem_clean])

                new_lemma = loaded_lemmas[0] if loaded_lemmas else None

            # 4. Create LemmaRelation mapping and update status
            if new_lemma:
                new_relation = models.LemmaRelation(
                    source_id=queue_item.source_id,  # type: ignore
                    target_id=new_lemma.id,  # type: ignore
                    rel_type=queue_item.rel_type,
                )
                db.add(new_relation)
                db.flush()

                queue_item.target_id = new_relation.id
                queue_item.status = models.EnumLookupStatus.LINKED
                db.commit()

                processed_count += 1
                logger.info(
                    f"Linked '{target_lem_clean}' (Queue ID: {item_id}) -> Lemma ID {new_lemma.id}"
                )
            else:
                logger.warning(f"Pipeline returned None for word '{target_lem_clean}'")
                queue_item.status = models.EnumLookupStatus.FAILED
                db.commit()

        except ObjectDeletedError:
            db.rollback()
            continue
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing LookupQueue ID {item_id}: {e}")

            # Mark as failed safely
            try:
                failed_item = db.get(models.LookupQueue, item_id)
                if failed_item:
                    failed_item.status = models.EnumLookupStatus.FAILED
                    db.commit()
            except Exception as nested_e:
                db.rollback()
                logger.error(
                    f"Could not set failure status for ID {item_id}: {nested_e}"
                )

        # If running in single-item mode, exit the loop immediately after 1 attempt
        if target_item_id is not None:
            break

    logger.info(
        f"Lookup queue batch complete. Total items processed: {processed_count}"
    )
    return processed_count


def clean_lookup_queue(limit: Optional[int] = 50, item_id: Optional[int] = None) -> int:
    """Wrapper function managing session lifecycle."""
    with SessionLocal() as db:
        return process_lookup_queue(db, batch_limit=limit, target_item_id=item_id)


if __name__ == "__main__":
    # Configure CLI interface for local testing & ops scripts
    parser = argparse.ArgumentParser(description="ALITE Lookup Queue Processor")
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=1,
        help="Maximum number of queue items to process (default: 50)",
    )
    parser.add_argument(
        "-i",
        "--item-id",
        type=int,
        default=None,
        help="Target a specific LookupQueue item ID for single-row testing",
    )

    args = parser.parse_args()

    # Execute with parsed CLI options
    clean_lookup_queue(limit=args.limit, item_id=args.item_id)
