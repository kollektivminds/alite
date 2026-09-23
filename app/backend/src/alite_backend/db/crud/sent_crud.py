import logging
from typing import Any, Optional, Sequence

from alite_backend.db.crud.crud_base import CRUDBase
from alite_backend.db.models import Document, Sentence, SentenceToken
from alite_backend.db.schemas import (
    DocumentCreate,
    DocumentUpdate,
    SentenceCreate,
    SentenceTokenCreate,
    SentenceTokenUpdate,
    SentenceUpdate,
)
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


class CRUDDocument(CRUDBase[Document, DocumentCreate, DocumentUpdate]):
    pass


class CRUDSentence(CRUDBase[Sentence, SentenceCreate, SentenceUpdate]):
    """
    Sentence-level persistence operations supporting dependency-tree hydration
    and pedagogically targeted sampling.
    """

    def get_with_tokens(self, db: Session, sent_id: int) -> Optional[Sentence]:
        """
        Fetches a sentence with all associated tokens eagerly loaded and
        strictly ordered by `tok_idx`. Prevents DetachedInstanceError.
        """
        stmt = (
            select(Sentence)
            .where(Sentence.id == sent_id)
            .options(selectinload(Sentence.tokens))
        )
        sentence = db.scalars(stmt).first()
        if sentence and sentence.tokens:
            # Ensure deterministic in-memory order by sequence index
            sentence.tokens.sort(key=lambda t: t.tok_idx)
        return sentence

    def sample_sentences(
        self,
        db: Session,
        *,
        doc_id: Optional[int] = None,
        min_token_count: int = 4,
        max_token_count: int = 30,
        required_lemmas: Optional[list[str]] = None,
        required_dep_rel: Optional[str] = None,
        limit: int = 10,
    ) -> Sequence[Sentence]:
        """
        Samples random sentences satisfying curriculum criteria.

        Uses SQL subqueries to enforce token constraints before fetching full entities,
        minimizing database transport overhead.
        """
        # Base statement selecting candidate sentences
        stmt = select(Sentence).options(selectinload(Sentence.tokens))

        if doc_id is not None:
            stmt = stmt.where(Sentence.doc_id == doc_id)

        # Apply token count bounds to filter out fragments or run-on paragraphs
        # Subquery counting tokens per sentence
        token_count_subq = (
            select(
                SentenceToken.sent_id, func.count(SentenceToken.id).label("tok_count")
            )
            .group_by(SentenceToken.sent_id)
            .having(
                and_(
                    func.count(SentenceToken.id) >= min_token_count,
                    func.count(SentenceToken.id) <= max_token_count,
                )
            )
            .subquery()
        )
        stmt = stmt.join(token_count_subq, Sentence.id == token_count_subq.c.sent_id)

        # Filter by presence of specific target lemma strings
        if required_lemmas:
            lemma_filter_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.lem_raw.in_(required_lemmas))
                .distinct()
                .subquery()
            )
            stmt = stmt.join(
                lemma_filter_subq, Sentence.id == lemma_filter_subq.c.sent_id
            )

        # Filter by specific syntactic dependency relation (e.g. 'предик', 'квазиагент')
        if required_dep_rel:
            dep_filter_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.dep_rel == required_dep_rel)
                .distinct()
                .subquery()
            )
            stmt = stmt.join(dep_filter_subq, Sentence.id == dep_filter_subq.c.sent_id)

        # Randomize selection using PostgreSQL random() and clamp limit
        stmt = stmt.order_by(func.random()).limit(limit)

        sentences = db.scalars(stmt).all()
        for sent in sentences:
            sent.tokens.sort(key=lambda t: t.tok_idx)

        return sentences


class CRUDSentenceToken(
    CRUDBase[SentenceToken, SentenceTokenCreate, SentenceTokenUpdate]
):
    """
    Token-level query operations for morphological harvesting and distractor generation.
    """

    def get_tokens_by_sentence(self, db: Session, sent_id: int) -> list[SentenceToken]:
        """
        Retrieves all tokens for a sentence ordered by their syntactic index.
        """
        stmt = (
            select(SentenceToken)
            .where(SentenceToken.sent_id == sent_id)
            .order_by(SentenceToken.tok_idx.asc())
        )
        return list(db.scalars(stmt).all())

    def get_intra_lemma_distractors(
        self,
        db: Session,
        *,
        lem_raw: str,
        exclude_lex_raw: str,
        limit: int = 5,
    ) -> list[str]:
        """
        Harvests alternative inflected forms of the same lemma from the database.
        Example: target is 'книгу', returns ['книга', 'книге', 'книгой'].
        """
        stmt = (
            select(SentenceToken.lex_raw)
            .where(
                and_(
                    SentenceToken.lem_raw == lem_raw,
                    func.lower(SentenceToken.lex_raw) != func.lower(exclude_lex_raw),
                )
            )
            .distinct()
            .order_by(func.random())
            .limit(limit)
        )
        return list(db.scalars(stmt).all())

    def get_feature_matched_distractors(
        self,
        db: Session,
        *,
        pos: str,
        feats: dict[str, Any],
        exclude_lem_raw: str,
        limit: int = 5,
    ) -> list[str]:
        """
        Samples word forms from different lemmas that match specified grammatical features.

        Utilizes PostgreSQL JSONB containment (@>) or text casting depending on column type.
        Assuming `feats` is stored as JSON/JSONB or structured mapping.
        """
        stmt = select(SentenceToken.lex_raw).where(
            and_(
                SentenceToken.pos == pos,
                SentenceToken.lem_raw != exclude_lem_raw,
            )
        )

        # If features column is JSONB, filter by key-value containment
        if feats and hasattr(SentenceToken, "feats"):
            # Matches tokens where feats contains the required subset (e.g. Case, Gender, Number)
            stmt = stmt.where(SentenceToken.feats.contains(feats))

        stmt = stmt.distinct().order_by(func.random()).limit(limit)
        return list(db.scalars(stmt).all())

    def get_syntactic_relation_pool(
        self,
        db: Session,
        *,
        exclude_rel: Optional[str] = None,
        limit: int = 10,
    ) -> list[str]:
        """
        Returns distinct dependency relation labels (e.g., 'предик', '1-компл', 'сочин')
        attested in the corpus for distractor generation in syntax annotation tasks.
        """
        stmt = select(SentenceToken.dep_rel).where(SentenceToken.dep_rel.is_not(None))

        if exclude_rel:
            stmt = stmt.where(SentenceToken.dep_rel != exclude_rel)

        stmt = stmt.distinct().order_by(func.random()).limit(limit)
        return list(db.scalars(stmt).all())


crud_document = CRUDDocument(Document)
crud_sentence = CRUDSentence(Sentence)
crud_sentence_token = CRUDSentenceToken(SentenceToken)
