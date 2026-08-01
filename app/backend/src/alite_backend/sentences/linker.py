import logging
from typing import List
from sqlalchemy import select, update, and_, distinct
from sqlalchemy.orm import Session
from alite_backend.db.models import (
    SentenceToken,
    Lemma,
    WordForm,
    Lexeme,
    EnumLookupStatus,
)

logger = logging.getLogger(__name__)


def resolve_unlinked_tokens(session: Session, batch_size: int = 5000):
    """
    Sweeps the database for UNLINKED sentence tokens and attempts to
    connect them to the ALITE dictionary using unaccented text columns.
    """

    # fetch a batch of UNLINKED tokens
    unlinked_stmt = (
        select(SentenceToken)
        .where(SentenceToken.status == EnumLookupStatus.UNLINKED)
        .limit(batch_size)
    )

    tokens = session.scalars(unlinked_stmt).all()

    if not tokens:
        return

    for token in tokens:
        # skip purely non-lexical tokens if needed
        if not token.lem_raw or not token.lex_raw:
            token.status = EnumLookupStatus.IGNORED
            continue

        raw_lem_lower = token.lem_raw.lower()
        raw_lex_lower = token.lex_raw.lower()
        pos = token.features.get("pos") if token.features else None

        # search for the Lemma using the UNACCENTED lem_text
        lemma = session.scalars(
            select(Lemma).where(and_(Lemma.lem_text == raw_lem_lower, Lemma.pos == pos))
        ).first()

        if lemma:
            token.lem_id = lemma.id

            # search for the WordForm using the UNACCENTED lex_text_clean
            # also ensure it belongs to the Lemma we just found
            word_form = session.scalars(
                select(WordForm)
                .join(Lexeme)
                .where(
                    and_(
                        Lexeme.lex_text_clean == raw_lex_lower,
                        WordForm.lem_id == lemma.id,
                    )
                )
            ).first()

            if word_form:
                token.wf_id = word_form.id

            token.status = EnumLookupStatus.LINKED
        else:
            # not in ALITE yet
            token.status = EnumLookupStatus.NOT_IN_DICT

    session.commit()


def get_missing_lemmas_for_pipeline(
    session: Session, batch_limit: int = 50
) -> List[str]:
    """
    Extracts a unique list of missing lemmas from the corpus to feed
    into the dictionary API pipeline.

    Args:
        session: Active SQLAlchemy session.
        batch_limit: Maximum number of unique words to extract at once
                     to prevent API rate-limiting.

    Returns:
        A list of unique lemma strings (e.g., ['собака', 'бегать']).
    """
    try:
        # construct the query using SQLAlchemy Core
        stmt = (
            select(distinct(SentenceToken.lem_raw))
            .where(SentenceToken.status == EnumLookupStatus.NOT_IN_DICT)
            .where(SentenceToken.lem_raw.is_not(None))
            .where(SentenceToken.lem_raw != "")
            .limit(batch_limit)
        )

        # execute the query
        missing_lemmas = session.scalars(stmt).all()

        logger.info(
            f"Extracted {len(missing_lemmas)} unique missing lemmas for processing."
        )

        return list(missing_lemmas)

    except Exception as e:
        logger.error(f"Failed to extract missing lemmas: {e}")
        return []
