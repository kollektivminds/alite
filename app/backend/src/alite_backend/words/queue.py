import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
from alite_backend.db.db_session import SessionLocal
from alite_backend.db import models
from alite_backend.words.funcs import remove_accents
from alite_backend.words.pipeline import load_words

logger = logging.getLogger(__name__)


def process_lookup_queue(db: Session, batch_size: int = 10):
    """
    Iterates over the lookup_queue table to process pending lemmas.

    This function streams pending queue items in batches. For each item,
    it delegates to the existing word pipeline to fetch and load the lemma,
    and then creates a relationship mapping in the related_lemmas table.
    """

    # while loop to fetch batches until empty
    while True:
        # fetch unprocessed item.
        queue_item = (
            db.query(models.LookupQueue)
            .filter(models.LookupQueue.status == models.EnumLookupStatus.UNLINKED)
            .first()
        )

        if not queue_item:
            break

        # extract primitive ID for safe error handling
        item_id = queue_item.id

        try:
            target_lem = str(queue_item.target_lem)
            clean_lem = [remove_accents(target_lem)]
            # re-use existing pipeline
            new_lemma = load_words(db, clean_lem)

            if new_lemma:
                # create the new lemma relation
                new_relation = models.LemmaRelation(
                    source_id=queue_item.source_id,
                    target_id=new_lemma.id,
                    rel_type=queue_item.rel_type,
                )
                db.add(new_relation)
                db.flush()

                # mark as completed in queue
                queue_item.target_id = new_relation.id
                queue_item.status = models.EnumLookupStatus.LINKED
                db.commit()

                logger.info(
                    f"Successfully processed and linked '{new_lemma}' to source ID {queue_item.source_id}"
                )

            else:
                # handle cases where the lookup pipeline couldn't find the word
                logger.warning(f"Pipeline returned None for word '{new_lemma}'")
                queue_item.status = models.EnumLookupStatus.FAILED
                db.commit()

        except ObjectDeletedError:
            # Another process happened to delete this row while we were looking at it.
            db.rollback()
            continue

        except Exception as e:
            # 4. Critical Safe Error Handling
            db.rollback()
            print(f"Pipeline error on queue item ID {item_id}: {e}")

            # THE INFINITE LOOP TRAP
            try:
                failed_item = db.query(models.LookupQueue).get(item_id)
                if failed_item:
                    failed_item.status = models.EnumLookupStatus.FAILED
                    db.commit()
            except Exception as nested_e:
                db.rollback()
                print(f"Failed to set error state for ID {item_id}: {nested_e}")
                break

            continue

        logger.info("Lookup queue processing completed.")


def clean_lookup_queue():
    with SessionLocal() as db:
        process_lookup_queue(db)


if __name__ == "__main__":
    clean_lookup_queue()
