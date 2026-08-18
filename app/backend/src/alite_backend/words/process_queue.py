import argparse
import logging
import sys
import unicodedata
from collections import defaultdict
from typing import Dict, List, Optional, Set

from alite_backend.db import models
from alite_backend.db.db_session import SessionLocal
from alite_backend.words.funcs import remove_accents
from alite_backend.words.pipeline import load_words
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import ObjectDeletedError

print(f"--> EXECUTING QUEUE FROM: {__file__}")

logger = logging.getLogger(__name__)


def process_lookup_queue(
    db: Session,
    batch_limit: int = 50,
    target_item_id: Optional[int] = None,
    include_failed: bool = True,
) -> int:
    """
    Consumes pending records from models.LookupQueue in optimized batches.
    Resolves items against the local DB first, then delegates missing strings
    to the ETL pipeline.
    """
    attempted_ids: Set[int] = set()
    total_processed = 0

    target_statuses = [models.EnumLookupStatus.UNLINKED]
    if include_failed:
        target_statuses.append(models.EnumLookupStatus.FAILED)

    while True:
        # fetch a batch of queue items
        stmt = select(models.LookupQueue)
        if target_item_id is not None:
            stmt = stmt.where(models.LookupQueue.id == target_item_id)  # type: ignore
        else:
            stmt = stmt.where(
                models.LookupQueue.status.in_(target_statuses),  # type: ignore
                models.LookupQueue.id.notin_(attempted_ids),  # type: ignore
            ).limit(batch_limit)

        queue_batch = list(db.scalars(stmt).all())

        if not queue_batch:
            break

        # track ids to prevent infinite loops
        for item in queue_batch:
            attempted_ids.add(item.id)  # type: ignore

        # extract & normalize target strings
        # mapping: queue_item.id -> clean_string
        item_to_clean_str: Dict[int, str] = {}
        unique_clean_strings: Set[str] = set()

        for item in queue_batch:
            accented = unicodedata.normalize("NFC", str(item.target_lem).strip())
            clean = remove_accents(accented)
            item_to_clean_str[item.id] = clean  # type: ignore
            unique_clean_strings.add(clean)

        # batch db cache check (the n+1 fix)
        # fetch all existing lemmas that match any target strings in one query
        existing_lemmas_stmt = select(models.Lemma).where(
            models.Lemma.lem_text.in_(unique_clean_strings)  # type: ignore
        )
        existing_lemmas = list(db.scalars(existing_lemmas_stmt).all())

        # core tracking dictionary: maps 'clean_str' -> [Lemma1, Lemma2...]
        resolved_dict: Dict[str, List[models.Lemma]] = defaultdict(list)
        for lem in existing_lemmas:
            if lem.lem_text:
                resolved_dict[lem.lem_text].append(lem)

        # identify missing words & run pipeline
        missing_strings = [
            text for text in unique_clean_strings if text not in resolved_dict
        ]

        if missing_strings:
            logger.info(
                f"Batch dispatching {len(missing_strings)} unknown words to ETL pipeline..."
            )

            new_lemmas = load_words(db, missing_strings)

            if new_lemmas:
                for lem in new_lemmas:
                    if lem.lem_text:
                        resolved_dict[lem.lem_text].append(lem)

        # resolve queue items and link
        # now iterate through original queue items and link them using populated dictionary
        for item in queue_batch:
            target_str = item_to_clean_str[item.id]  # type: ignore
            matched_lemmas = resolved_dict.get(target_str, [])

            try:
                if matched_lemmas:
                    # ink all homographs
                    for lemma in matched_lemmas:
                        # idempotency check: don't create duplicate relationships
                        rel_exists = db.scalars(
                            select(models.LemmaRelation).where(
                                models.LemmaRelation.source_id == item.source_id,  # type: ignore
                                models.LemmaRelation.target_id == lemma.id,  # type: ignore
                                models.LemmaRelation.rel_type == item.rel_type,  # type: ignore
                            )
                        ).first()

                        if not rel_exists:
                            db.add(
                                models.LemmaRelation(
                                    source_id=item.source_id,  # type: ignore
                                    target_id=lemma.id,  # type: ignore
                                    rel_type=item.rel_type,
                                )
                            )

                    # successfully linked at least one relation
                    item.target_id = matched_lemmas[0].id
                    item.status = models.EnumLookupStatus.LINKED
                    total_processed += 1
                    logger.info(f"Linked '{target_str}' for Queue ID {item.id}.")

                else:
                    logger.warning(
                        f"Word '{target_str}' not resolved. Marking NOT_IN_DICT."
                    )
                    item.status = models.EnumLookupStatus.NOT_IN_DICT

                # commit per-item to ensure a failure on one item doesn't roll back the whole batch
                db.flush()
                db.commit()

            except Exception as e:
                db.rollback()
                logger.error(f"Failed linking Queue ID {item.id}: {e}")

                # safe failure fallback
                failed_item = db.get(models.LookupQueue, item.id)
                if failed_item:
                    failed_item.status = models.EnumLookupStatus.FAILED
                    db.commit()

        if target_item_id is not None:
            break  # exit after processing the specific item

    logger.info(f"Queue processing complete. Successfully linked: {total_processed}")
    return total_processed


def clean_lookup_queue(limit: Optional[int] = 50, item_id: Optional[int] = None) -> int:
    """Wrapper function managing session lifecycle."""
    with SessionLocal() as db:
        return process_lookup_queue(db, batch_limit=limit, target_item_id=item_id)  # type: ignore


if __name__ == "__main__":
    # configure CLI interface for local testing & ops scripts
    parser = argparse.ArgumentParser(description="ALITE Lookup Queue Processor")
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=5,
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

    # execute with parsed CLI options
    clean_lookup_queue(limit=args.limit, item_id=args.item_id)
