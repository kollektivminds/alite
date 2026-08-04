import logging
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError
from alite_backend.db.db_session import SessionLocal
from alite_backend.db import models
from alite_backend.words.funcs import remove_accents
from alite_backend.words.pipeline import load_words

logger = logging.getLogger(__name__)


def process_lookup_queue(db: Session, batch_size: int = 25):
    """
    Iterates over the lookup_queue table to process pending lemmas.

    This function streams pending queue items in batches. For each item,
    it delegates to the existing word pipeline to fetch and load the lemma,
    and then creates a relationship mapping in the related_lemmas table.
    """

    # track attempts
    attempted_ids = set()

    # while loop to fetch batches until empty
    while len(attempted_ids) < batch_size:
        # fetch unprocessed item.
        queue_item = (
            db.query(models.LookupQueue)
            .filter(
                models.LookupQueue.status == models.EnumLookupStatus.UNLINKED,
                # models.LookupQueue.status.in_(
                #     [models.EnumLookupStatus.UNLINKED, models.EnumLookupStatus.FAILED]
                # ),
                models.LookupQueue.id.notin_(attempted_ids),
            )
            .first()
        )

        if not queue_item:
            break

        # extract primitive ID for safe error handling
        item_id = queue_item.id
        attempted_ids.add(item_id)

        try:
            target_lem = str(queue_item.target_lem).strip()
            clean_lem = remove_accents(target_lem)

            new_lemma = None

            # check local db
            existing_lemma = (
                db.query(models.Lemma)
                .filter(
                    (models.Lemma.lem_canon == target_lem)
                    | (models.Lemma.lem_text == clean_lem)
                )
                .first()
            )

            if existing_lemma:
                logger.info(f"Found '{clean_lem}' in local DB. Skipping pipeline.")
                new_lemma = existing_lemma
            else:
                # fallback to the pipeline
                logger.info(f"'{clean_lem}' not found locally. Running pipeline...")
                new_lemma = load_words(db, [clean_lem])

            # re-use existing pipeline
            # new_lemma = load_words(db, clean_lem)

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
                logger.warning(f"Pipeline returned None for word '{clean_lem}'")
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
