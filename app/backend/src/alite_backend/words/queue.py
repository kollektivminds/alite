import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from alite_backend.db.db_session import SessionLocal
from alite_backend.db.models import LookupQueue, LemmaRelation, Lemma, EnumLookupStatus
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
        # fetch from db
        pending_items_query = (
            db.query(LookupQueue)
            .filter(LookupQueue.status == EnumLookupStatus.UNLINKED)
            .limit(batch_size)
            .all()
        )
        
        if not pending_items_query:
            logger.info("No more items remaining in lookup queue.")
            break

        for queue_item in pending_items_query:
            try:
                target_lem = str(queue_item.target_lem)
                clean_lem = [remove_accents(target_lem)]
                # re-use existing pipeline
                new_lemma = load_words(db, clean_lem)

                if new_lemma:
                    # create the new lemma relation
                    new_relation = LemmaRelation(
                        source_id=queue_item.source_id,
                        target_id=new_lemma.id,
                        rel_type=queue_item.rel_type,
                    )
                    db.add(new_relation)
                    db.flush()

                    # mark as completed in queue
                    queue_item.target_id = new_relation.id
                    queue_item.status = EnumLookupStatus.LINKED
                    db.commit()

                    logger.info(
                        f"Successfully processed and linked '{new_lemma}' to source ID {queue_item.source_id}"
                    )

                else:
                    # handle cases where the lookup pipeline couldn't find the word
                    logger.warning(f"Pipeline returned None for word '{new_lemma}'")
                    queue_item.status = EnumLookupStatus.FAILED
                    db.commit()

            except SQLAlchemyError as e:
                # database-level errors (e.g., unique constraint violations)
                db.rollback()
                logger.error(
                    f"Database error processing queue item ID {queue_item.id}: {e}"
                )

                # optionally mark as failed so it doesn't get stuck in a permanent loop
                queue_item.status = EnumLookupStatus.FAILED
                db.commit()

            except Exception as e:
                # broad catch for unexpected pipeline errors (e.g., JSON parsing errors)
                db.rollback()
                logger.error(
                    f"Unexpected error processing queue item ID {queue_item.id}: {e}"
                )

                queue_item.status = EnumLookupStatus.FAILED
                db.commit()

        logger.info("Lookup queue processing completed.")
    
    
def clean_lookup_queue():
    with SessionLocal() as db:
        process_lookup_queue(db)
        
if __name__ == "__main__":
    clean_lookup_queue()