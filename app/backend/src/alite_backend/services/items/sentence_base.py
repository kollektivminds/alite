"""
app/backend/services/items/sentence_base.py

Abstract base strategy class for sentence-level item generation in ALITE.
Manages sentence querying, token-graph hydration, orthographic rendering,
distractor harvesting, and client-safe payload masking.
"""

from __future__ import annotations

import logging
import random
from abc import ABC, abstractmethod
from typing import Any, Optional, Sequence
from uuid import uuid4

from alite_backend.db import models, schemas
from alite_backend.db.models import Sentence, SentenceToken
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


class SentenceItemBaseStrategy(ABC):
    """
    Abstract Base Class for sentence-level exercise strategies.

    Provides utility methods for sentence fetching, syntactic dependency analysis,
    orthographic surface rendering, and candidate token selection.
    """

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
    ) -> None:
        self.db = db_session
        self.request_context = request_context

        # Context settings extracted from the parent payload
        self.lem_ids: list[int] = request_context.lem_ids or []
        self.formats: list[schemas.EnumItemFormat] = request_context.ex_formats
        self.difficulty: schemas.EnumItemDifficulty = request_context.difficulty
        self.max_keys: int = request_context.max_keys
        self.max_distractors: int = request_context.max_distractors

    # -------------------------------------------------------------------------
    # Database Scoping and Eager Hydration
    # -------------------------------------------------------------------------

    def _get_candidate_sentences(
        self,
        limit: int,
        min_tokens: int = 5,
        max_tokens: int = 30,
        doc_id: Optional[int] = None,
        required_dep_rel: Optional[str] = None,
        required_pos: Optional[str] = None,
    ) -> list[Sentence]:
        """
        Samples candidate sentences from the corpus matching syntactic and length criteria.
        Eagerly loads tokens sorted by `token_idx` to prevent DetachedInstanceError.
        """
        stmt = select(Sentence).options(selectinload(Sentence.tokens))

        if doc_id is not None:
            stmt = stmt.where(Sentence.doc_id == doc_id)

        # Token length boundaries via a grouped subquery
        token_count_subq = (
            select(
                SentenceToken.sent_id,
                func.count(SentenceToken.id).label("tok_count"),
            )
            .group_by(SentenceToken.sent_id)
            .having(
                and_(
                    func.count(SentenceToken.id) >= min_tokens,
                    func.count(SentenceToken.id) <= max_tokens,
                )
            )
            .subquery()
        )
        stmt = stmt.join(token_count_subq, Sentence.id == token_count_subq.c.sent_id)

        # Filter by targeted curriculum lemmas if provided in ExerciseContext
        if self.lem_ids:
            lem_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.lem_id.in_(self.lem_ids))
                .distinct()
                .subquery()
            )
            stmt = stmt.join(lem_subq, Sentence.id == lem_subq.c.sent_id)

        # Syntactic dependency filter (e.g. sentences with 'предик' or '1-компл')
        if required_dep_rel:
            dep_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.dep_rel == required_dep_rel)
                .distinct()
                .subquery()
            )
            stmt = stmt.join(dep_subq, Sentence.id == dep_subq.c.sent_id)

        # Part-of-speech presence constraint (e.g. requires a VERB or NOUN)
        if required_pos:
            pos_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.features["pos"].as_string() == required_pos)
                .distinct()
                .subquery()
            )
            stmt = stmt.join(pos_subq, Sentence.id == pos_subq.c.sent_id)

        # Randomize selection and fetch excess rows to allow in-memory filtering
        stmt = stmt.order_by(func.random()).limit(limit * 3)
        sentences = list(self.db.scalars(stmt).all())

        # Ensure in-memory ordering guarantees for tokens
        for s in sentences:
            s.tokens.sort(key=lambda t: t.token_idx)

        return sentences

    # -------------------------------------------------------------------------
    # Orthography and Reconstruction Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def render_reconstructed_sentence(tokens: Sequence[SentenceToken]) -> str:
        """
        Reconstructs a sentence string respecting punctuation markers and capitalization.
        Ensures correct typographical spacing (e.g., no space before commas or periods).
        """
        output: list[str] = []
        for tok in tokens:
            prefix = tok.punctuation_before or ""
            suffix = tok.punctuation_after or ""
            word = tok.lex_raw

            # If preceding punctuation exists, attach cleanly
            tok_repr = f"{prefix}{word}{suffix}"

            if not output:
                output.append(tok_repr)
            else:
                # Decide if a space is required between tokens
                prev_tok = tokens[tokens.index(tok) - 1]
                # Skip space if previous token has trailing punctuation like an open quote
                if prev_tok.punctuation_after and prev_tok.punctuation_after in '([«"':
                    output.append(tok_repr)
                # Skip space if current token has leading punctuation attaching leftward
                elif prefix and prefix in '.,!?:;)»"':
                    output.append(tok_repr)
                else:
                    output.append(f" {tok_repr}")

        return "".join(output).strip()

    # -------------------------------------------------------------------------
    # Syntactic Graph & Token Analysis
    # -------------------------------------------------------------------------

    @staticmethod
    def get_token_dependents(
        head_token: SentenceToken,
        all_tokens: Sequence[SentenceToken],
    ) -> list[SentenceToken]:
        """
        Retrieves all syntactic children pointing to the given head_token via `head_idx`.
        """
        return [t for t in all_tokens if t.head_idx == head_token.token_idx]

    @staticmethod
    def get_token_governor(
        token: SentenceToken,
        all_tokens: Sequence[SentenceToken],
    ) -> Optional[SentenceToken]:
        """
        Retrieves the syntactic parent/governor for a given token.
        """
        if token.head_idx is None:
            return None
        for candidate in all_tokens:
            if candidate.token_idx == token.head_idx:
                return candidate
        return None

    # -------------------------------------------------------------------------
    # Distractor Harvesting Engines
    # -------------------------------------------------------------------------

    def fetch_intra_lemma_distractors(
        self,
        target_token: SentenceToken,
        limit: int = 3,
    ) -> list[str]:
        """
        Collects alternative surface wordforms (`lex_raw`) for the same lemma from the DB.
        Useful for grammatical case/tense selection drills (e.g. книгу -> книга, книге).
        """
        stmt = (
            select(SentenceToken.lex_raw)
            .where(
                and_(
                    SentenceToken.lem_raw == target_token.lem_raw,
                    func.lower(SentenceToken.lex_raw) != target_token.lex_raw.lower(),
                )
            )
            .distinct()
            .order_by(func.random())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def fetch_feature_matched_distractors(
        self,
        target_token: SentenceToken,
        required_features: dict[str, Any],
        limit: int = 3,
    ) -> list[str]:
        """
        Collects surface wordforms from DIFFERENT lemmas that share the exact
        same morphosyntactic slot (e.g., Accusative Singular Masculine noun).
        """
        stmt = select(SentenceToken.lex_raw).where(
            and_(
                SentenceToken.lem_raw != target_token.lem_raw,
                SentenceToken.features.contains(required_features),
            )
        )
        stmt = stmt.distinct().order_by(func.random()).limit(limit)
        return list(self.db.scalars(stmt).all())

    # -------------------------------------------------------------------------
    # Sanitization & Blueprint Creation
    # -------------------------------------------------------------------------

    def build_sentence_blueprint_context(
        self,
        sentence: Sentence,
        target_indices: list[int],
        syntactic_focus: Optional[str] = None,
    ) -> schemas.SentenceBlueprintContext:
        """
        Converts SQLAlchemy ORM Sentence and Token rows into an internal
        SentenceBlueprintContext schema. Retains ground-truth data on the backend.
        """
        token_contexts = [
            schemas.SentenceTokenContext(
                tok_idx=t.token_idx,
                lex_raw=t.lex_raw,
                lem_raw=t.lem_raw,
                pos=t.features.get("pos") if t.features else None,
                feats=t.features or {},
                head_idx=t.head_idx,
                dep_rel=t.dep_rel,
            )
            for t in sentence.tokens
        ]

        full_text = sentence.raw_text or self.render_reconstructed_sentence(
            sentence.tokens
        )

        return schemas.SentenceBlueprintContext(
            doc_id=sentence.doc_id,
            sent_id=sentence.id,
            full_sentence=full_text,
            tokens=token_contexts,
            target_token_indices=target_indices,
            syntactic_focus=syntactic_focus,
        )

    def mask_sentence_for_cloze(
        self,
        sentence: Sentence,
        masked_token_indices: list[int],
        placeholder: str = "[___]",
    ) -> tuple[str, list[schemas.DisplayToken], list[str]]:
        """
        Produces client-safe cloze structures:
        1. String prompt containing masked placeholders.
        2. Sequence of DisplayTokens with masked words blanked.
        3. String split parts around the blanks for FITB rendering.
        """
        display_tokens: list[schemas.DisplayToken] = []
        parts: list[str] = []
        current_segment: list[str] = []

        for tok in sentence.tokens:
            is_target = tok.token_idx in masked_token_indices
            prefix = tok.punctuation_before or ""
            suffix = tok.punctuation_after or ""

            if is_target:
                # Blank the text and flush segment to parts
                display_tokens.append(
                    schemas.DisplayToken(
                        tok_idx=tok.token_idx,
                        text=placeholder,
                        is_masked=True,
                        is_punctuation=False,
                    )
                )
                parts.append("".join(current_segment))
                current_segment = []
            else:
                text_repr = f"{prefix}{tok.lex_raw}{suffix}"
                display_tokens.append(
                    schemas.DisplayToken(
                        tok_idx=tok.token_idx,
                        text=text_repr,
                        is_masked=False,
                        is_punctuation=bool(tok.dep_rel == "пункт"),
                    )
                )
                current_segment.append(
                    f" {text_repr}" if current_segment else text_repr
                )

        if current_segment:
            parts.append("".join(current_segment))

        masked_prompt = placeholder.join(parts)
        return masked_prompt, display_tokens, parts

    # -------------------------------------------------------------------------
    # Abstract Interface
    # -------------------------------------------------------------------------

    @abstractmethod
    def generate_item_blueprints(
        self,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> list[schemas.ItemBlueprint]:
        """
        Core contract for generating sentence blueprints.
        Must return ItemBlueprints populated with `SentenceBlueprintContext`.
        """
        pass
