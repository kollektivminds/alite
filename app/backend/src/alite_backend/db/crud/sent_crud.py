import logging
import random
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
    """Token-level persistence and distractor harvesting."""

    def get_tokens_by_sentence(self, db: Session, sent_id: int) -> list[SentenceToken]:
        stmt = (
            select(SentenceToken)
            .where(SentenceToken.sent_id == sent_id)
            .order_by(SentenceToken.token_idx.asc())
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
        """Fetch distinct wordforms without SQL ORDER BY random()."""
        stmt = (
            select(SentenceToken.lex_raw)
            .where(
                and_(
                    SentenceToken.lem_raw == lem_raw,
                    func.lower(SentenceToken.lex_raw) != func.lower(exclude_lex_raw),
                )
            )
            .distinct()
        )
        raw_candidates = list(db.scalars(stmt).all())

        # In-memory case deduplication
        deduped: dict[str, str] = {c.lower(): c for c in raw_candidates}
        forms = list(deduped.values())

        if len(forms) <= limit:
            return forms
        return random.sample(forms, limit)

    def get_feature_matched_distractors(
        self,
        db: Session,
        *,
        pos: str,
        feats: dict[str, Any],
        exclude_lem_raw: str,
        limit: int = 5,
    ) -> list[str]:
        """Fetch random buffer without SQL DISTINCT, then deduplicate in memory."""
        stmt = select(SentenceToken.lex_raw, SentenceToken.lem_raw).where(
            and_(
                SentenceToken.features["pos"].as_string() == pos,
                SentenceToken.lem_raw != exclude_lem_raw,
            )
        )
        if feats:
            stmt = stmt.where(SentenceToken.features.contains(feats))

        stmt = stmt.order_by(func.random()).limit(limit * 5)
        rows = db.execute(stmt).all()

        unique: dict[str, str] = {}
        for lex, lem in rows:
            lower_lex = lex.lower()
            if lower_lex not in unique:
                unique[lower_lex] = lex
            if len(unique) == limit:
                break

        return list(unique.values())

    def get_syntactic_relation_pool(
        self,
        db: Session,
        *,
        exclude_rel: Optional[str] = None,
        limit: int = 10,
    ) -> list[str]:
        """Fetch distinct relations and sample in memory."""
        stmt = select(SentenceToken.dep_rel).where(SentenceToken.dep_rel.is_not(None))
        if exclude_rel:
            stmt = stmt.where(SentenceToken.dep_rel != exclude_rel)

        stmt = stmt.distinct()
        relations = [r for r in db.scalars(stmt).all() if r and r != "пункт"]

        if len(relations) <= limit:
            return relations
        return random.sample(relations, limit)


crud_document = CRUDDocument(Document)
crud_sentence = CRUDSentence(Sentence)
crud_sentence_token = CRUDSentenceToken(SentenceToken)
