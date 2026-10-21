# app/backend/services/items/sentence_base.py
from __future__ import annotations

import logging
import random
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from alite_backend.db import models, schemas
from alite_backend.db.models import Lexeme, Sentence, SentenceToken, WordForm
from alite_backend.words.funcs import remove_accents
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, selectinload

logger = logging.getLogger(__name__)


# Canonical Pedagogical Mapping for SynTagRus Syntactic Tags
SYNTAGRUS_DEP_REL_MAP: Dict[str, str] = {
    "предик": "Subject",
    "1-компл": "Direct Object",
    "2-компл": "Indirect Object",
    "3-компл": "Oblique Object",
    "4-компл": "Oblique Object",
    "5-компл": "Oblique Object",
    "обст": "Adverbial Modifier",
    "опред": "Adjectival Modifier (Attribute)",
    "атриб": "Non-agreeing Modifier",
    "квазиагент": "Agentive / Genitive Complement",
    "огранич": "Restrictive Particle / Modifier",
    "сочин": "Coordinated Element",
    "соч-союзн": "Coordinating Conjunction Clause",
    "сент-соч": "Sentential Coordination",
    "подч-союзн": "Subordinating Conjunction Clause",
    "присвяз": "Copular Predicative",
    "вводн": "Parenthetical",
    "предл": "Prepositional Dependent",
    "количест": "Quantitative Modifier",
    "длительн": "Duration Modifier",
    "кратн": "Multiplicative Modifier",
    "распред": "Distributive Modifier",
    "сравнит": "Comparative Modifier",
    "сравн-союзн": "Comparative Conjunction Clause",
    "электив": "Partitive Dependent",
    "аппоз": "Apposition",
    "пасс-анал": "Passive Auxiliary",
    "вспом": "Auxiliary",
    "инф-союзн": "Infinitive Conjunction Clause",
    "уточн": "Clarifying Modifier",
    "эксплет": "Expletive",
    "композ": "Compound Part",
}

CANONICAL_ASPECTS: list[str] = [
    "imperfective",
    "perfective",
]

CANONICAL_CASES: list[str] = [
    "nominative",
    "genitive",
    "dative",
    "accusative",
    "instrumental",
    "prepositional",
]


class SentenceItemBaseStrategy(ABC):
    """
    Abstract Base Class for sentence-level exercise strategies.
    Manages querying, token-graph hydration, distractor harvesting,
    and client-safe payload generation.
    """

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
    ) -> None:
        self.db = db_session
        self.request_context = request_context

        self.lem_ids: list[int] = request_context.lem_ids or []
        self.formats: list[schemas.EnumItemFormat] = request_context.ex_formats
        self.difficulty: schemas.EnumItemDifficulty = request_context.difficulty
        self.max_keys: int = request_context.max_keys
        self.max_distractors: int = request_context.max_distractors

    def _get_candidate_sentences(
        self,
        limit: int,
        min_tokens: int = 5,
        max_tokens: int = 50,
        doc_id: Optional[int] = None,
        required_dep_rel: Optional[str] = None,
        required_pos: Optional[Any] = None,
    ) -> list[Sentence]:
        """
        Samples candidate sentences from the corpus matching syntactic criteria.
        Eagerly loads tokens sorted by token_idx.
        """
        stmt = select(Sentence).options(selectinload(Sentence.tokens))

        if doc_id is not None:
            stmt = stmt.where(Sentence.doc_id == doc_id)

        if self.lem_ids:
            lem_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.lem_id.in_(self.lem_ids))
                .distinct()
                .subquery()
            )
            stmt = stmt.join(lem_subq, Sentence.id == lem_subq.c.sent_id)

        if required_dep_rel:
            dep_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.dep_rel == required_dep_rel)
                .distinct()
                .subquery()
            )
            stmt = stmt.join(dep_subq, Sentence.id == dep_subq.c.sent_id)

        if required_pos:
            pos_val = (
                required_pos.value
                if hasattr(required_pos, "value")
                else str(required_pos).lower()
            )
            pos_subq = (
                select(SentenceToken.sent_id)
                .where(SentenceToken.features.contains({"pos": pos_val}))
                .distinct()
                .subquery()
            )
            stmt = stmt.join(pos_subq, Sentence.id == pos_subq.c.sent_id)

        fetch_limit = max(limit * 3, 10)
        stmt = stmt.order_by(func.random()).limit(fetch_limit)
        raw_candidates = list(self.db.scalars(stmt).all())

        valid_sentences: list[Sentence] = []
        for s in raw_candidates:
            s.tokens.sort(key=lambda t: t.token_idx)
            if min_tokens <= len(s.tokens) <= max_tokens:
                valid_sentences.append(s)
            if len(valid_sentences) >= limit:
                break

        return valid_sentences

    @staticmethod
    def render_reconstructed_sentence(
        tokens: Sequence[SentenceToken],
        highlight_indices: Optional[Sequence[int]] = None,
    ) -> str:
        """
        Собирает предложение из токенов с учетом пунктуационных правил,
        экранирования символов и инлайн-выделения целевых слов.
        """
        output: list[str] = []
        highlight_set = set(highlight_indices or [])

        for i, tok in enumerate(tokens):
            # Очистка артефактов экранирования кавычек из корпуса SynTagRus
            prefix = (
                (tok.punctuation_before or "").replace('\\"', '"').replace('"', "«", 1)
            )
            suffix = (
                (tok.punctuation_after or "").replace('\\"', '"').replace('"', "»", 1)
            )
            word = tok.lex_raw.replace('\\"', '"')

            if tok.token_idx in highlight_set:
                tok_repr = f"{prefix}**{word}**{suffix}"
            else:
                tok_repr = f"{prefix}{word}{suffix}"

            if not output:
                output.append(tok_repr)
            else:
                prev_tok = tokens[i - 1]
                prev_suffix = prev_tok.punctuation_after or ""

                if prev_suffix and prev_suffix in "([«\"'":
                    output.append(tok_repr)
                elif prefix and prefix in ".,!?:;)»\"'":
                    output.append(tok_repr)
                else:
                    output.append(f" {tok_repr}")

        rendered = "".join(output).strip()
        rendered = re.sub(r"\s+([.,!?:;»])", r"\1", rendered)
        rendered = re.sub(r"([«])\s+", r"\1", rendered)
        return rendered

    @staticmethod
    def assemble_tokens_with_punctuation(
        tokens: Sequence[SentenceToken],
    ) -> List[str]:
        """
        Synthesizes movable lexical tokens with contextual punctuation attached.

        Handles both column-based punctuation (punctuation_before/after) and
        relational punctuation tokens (dep_rel == 'пункт'):
        - Left-attaching punctuation (.,!?:;)»"'-) binds to preceding word.
        - Right-attaching punctuation (([«"') binds to following word.
        """
        OPENING_PUNCT: Set[str] = set("([«\"'‘“")
        CLOSING_PUNCT: Set[str] = set(".,!?:;)»\"'’”…")

        assembled: List[str] = []
        pending_prefix = ""

        # Guarantee sequential evaluation by token index
        sorted_tokens = sorted(tokens, key=lambda t: t.token_idx)

        for tok in sorted_tokens:
            raw_text = (tok.lex_raw or "").strip().replace('\\"', '"')
            if not raw_text:
                continue

            # Check if this token is a dedicated punctuation record
            is_standalone_punct = tok.dep_rel == "пункт" or (
                len(raw_text) == 1 and raw_text in (OPENING_PUNCT | CLOSING_PUNCT)
            )

            if is_standalone_punct:
                if any(ch in OPENING_PUNCT for ch in raw_text):
                    pending_prefix += raw_text
                else:
                    # Closing punctuation attaches directly to preceding content token
                    if assembled:
                        assembled[-1] = f"{assembled[-1]}{raw_text}"
                    else:
                        pending_prefix += raw_text
                continue

            # Handle content word token
            prefix = (tok.punctuation_before or "").replace('\\"', '"')
            suffix = (tok.punctuation_after or "").replace('\\"', '"')

            full_prefix = f"{pending_prefix}{prefix}"
            pending_prefix = ""

            word_unit = f"{full_prefix}{raw_text}{suffix}".strip()
            if word_unit:
                assembled.append(word_unit)

        # Flush any trailing punctuation to the final word
        if pending_prefix and assembled:
            assembled[-1] = f"{assembled[-1]}{pending_prefix}"

        return assembled

    @staticmethod
    def get_token_governor(
        token: SentenceToken,
        all_tokens: Sequence[SentenceToken],
    ) -> Optional[SentenceToken]:
        if token.head_idx is None:
            return None
        for candidate in all_tokens:
            if candidate.token_idx == token.head_idx:
                return candidate
        return None

    def fetch_intra_lemma_distractors(
        self,
        target_token: SentenceToken,
        limit: int = 3,
    ) -> list[str]:
        """
        Extracts alternate inflected forms of the same lemma.
        Strips dictionary accents so distractors match the target token orthography.
        """
        unique_distractors: dict[str, str] = {}
        target_raw = target_token.lex_raw
        target_stripped = remove_accents(target_raw).lower()
        has_accents_originally = any(
            unicodedata.category(ch) == "Mn"
            for ch in unicodedata.normalize("NFD", target_raw)
        )

        effective_lem_id = target_token.lem_id
        if effective_lem_id is None and target_token.lem_raw:
            lemma_stmt = (
                select(models.Lemma.id)
                .where(
                    func.lower(models.Lemma.lem_text) == target_token.lem_raw.lower()
                )
                .limit(1)
            )
            effective_lem_id = self.db.scalar(lemma_stmt)

        # 1. Primary pass: Dictionary tables via WordForm + Lexeme
        if effective_lem_id:
            dict_stmt = (
                select(Lexeme.lex_text)
                .join(WordForm, WordForm.lex_id == Lexeme.id)
                .where(WordForm.lem_id == effective_lem_id)
                .distinct()
                .limit(limit * 4)
            )
            for form in self.db.scalars(dict_stmt).all():
                # Strip accents unless the corpus target originally had them
                cleaned_form = form if has_accents_originally else remove_accents(form)
                folded = cleaned_form.lower()

                if folded != target_stripped and folded not in unique_distractors:
                    final_text = (
                        cleaned_form.capitalize()
                        if target_token.is_capitalized
                        else cleaned_form.lower()
                    )
                    unique_distractors[folded] = final_text
                if len(unique_distractors) >= limit:
                    break

        # 2. Secondary pass: Sentence corpus fallback
        if len(unique_distractors) < limit and target_token.lem_raw:
            token_stmt = (
                select(SentenceToken.lex_raw)
                .where(
                    and_(
                        func.lower(SentenceToken.lem_raw)
                        == target_token.lem_raw.lower(),
                        func.lower(SentenceToken.lex_raw) != target_stripped,
                    )
                )
                .distinct()
                .limit(limit * 2)
            )
            for form in self.db.scalars(token_stmt).all():
                cleaned_form = form if has_accents_originally else remove_accents(form)
                folded = cleaned_form.lower()
                if folded != target_stripped and folded not in unique_distractors:
                    final_text = (
                        cleaned_form.capitalize()
                        if target_token.is_capitalized
                        else cleaned_form.lower()
                    )
                    unique_distractors[folded] = final_text

        results = list(unique_distractors.values())
        return results if len(results) <= limit else random.sample(results, limit)

    def fetch_feature_matched_distractors(
        self,
        target_token: SentenceToken,
        required_features: dict[str, Any],
        limit: int = 3,
    ) -> list[str]:
        """
        Samples wordforms sharing identical morphological properties.
        """
        buffer_size = max(limit * 5, 20)
        stmt = (
            select(SentenceToken.lex_raw, SentenceToken.lem_raw)
            .where(
                and_(
                    SentenceToken.lem_raw != target_token.lem_raw,
                    SentenceToken.features.contains(required_features),
                )
            )
            .limit(buffer_size)
        )
        sampled_rows = list(self.db.execute(stmt).all())
        random.shuffle(sampled_rows)

        unique_distractors: dict[str, str] = {}
        seen_lemmas: set[str] = {target_token.lem_raw}
        target_lower = target_token.lex_raw.lower()

        for lex_raw, lem_raw in sampled_rows:
            lex_lower = lex_raw.lower()
            if (
                lem_raw not in seen_lemmas
                and lex_lower != target_lower
                and lex_lower not in unique_distractors
            ):
                seen_lemmas.add(lem_raw)
                clean_word = (
                    lex_raw.capitalize()
                    if target_token.is_capitalized
                    else lex_raw.lower()
                )
                unique_distractors[lex_lower] = clean_word

            if len(unique_distractors) >= limit:
                break

        return list(unique_distractors.values())

    def build_sentence_blueprint_context(
        self,
        sentence: Sentence,
        target_indices: list[int],
        syntactic_focus: Optional[str] = None,
    ) -> schemas.SentenceBlueprintContext:
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
        sentence: models.Sentence,
        masked_token_indices: Sequence[int],
        placeholder: str = " [___] ",
    ) -> Tuple[str, List[schemas.DisplayToken], List[str]]:
        """
        Builds client-safe stimulus representations with zero solution leakage.

        Returns:
            Tuple[0]: Full prompt string containing placeholder markers.
            Tuple[1]: Ordered list of DisplayTokens with targets masked.
            Tuple[2]: Delimiting text parts for frontend input blank injection.
        """
        display_tokens: List[schemas.DisplayToken] = []
        parts: List[str] = []
        current_segment: List[str] = []
        masked_set = set(masked_token_indices)

        for tok in sentence.tokens:
            is_target = tok.token_idx in masked_set
            prefix = tok.punctuation_before or ""
            suffix = tok.punctuation_after or ""

            if is_target:
                # 1. Flush the preceding non-target text into the parts slice
                parts.append("".join(current_segment))
                current_segment = []

                # 2. Add client-safe DisplayToken omitting target orthography
                display_tokens.append(
                    schemas.DisplayToken(
                        tok_idx=tok.token_idx,
                        text=placeholder.strip(),
                        is_masked=True,
                        is_punctuation=False,
                    )
                )
            else:
                tok_str = f"{prefix}{tok.lex_raw}{suffix}"
                display_tokens.append(
                    schemas.DisplayToken(
                        tok_idx=tok.token_idx,
                        text=tok_str,
                        is_masked=False,
                        is_punctuation=bool(tok.dep_rel == "пункт"),
                    )
                )
                current_segment.append(f" {tok_str}" if current_segment else tok_str)

        # Invariant: Always append the final trailing segment (even if empty string "")
        # Guarantees len(parts) == len(masked_token_indices) + 1
        parts.append("".join(current_segment))

        # Reconstruct the string prompt using the placeholder
        masked_prompt = placeholder.join(parts).strip()

        return masked_prompt, display_tokens, parts

    @abstractmethod
    def generate_item_blueprints(
        self,
        num_items: int,
        max_keys: int,
        max_distractors: int,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> list[schemas.ItemBlueprint]:
        pass
