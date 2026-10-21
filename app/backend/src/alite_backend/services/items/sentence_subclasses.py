# app/backend/services/items/sentence_subclasses.py
from __future__ import annotations

import logging
import random
from enum import Enum
from typing import Any, List, Optional

from alite_backend.db import models, schemas
from alite_backend.db.models import EnumPartOfSpeech, Sentence, SentenceToken
from alite_backend.services.items.sentence_base import (
    CANONICAL_ASPECTS,
    CANONICAL_CASES,
    SYNTAGRUS_DEP_REL_MAP,
    SentenceItemBaseStrategy,
)
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EnumDistractorMode(str, Enum):
    INTRA_LEMMA = "intra_lemma"
    FEATURE_MATCHED = "feature_matched"


class EnumGraphQueryMode(str, Enum):
    FIND_GOVERNOR = "find_governor"
    FIND_DEPENDENT = "find_dependent"
    FIND_ROLE = "find_role"


class SentenceClozeStrategy(SentenceItemBaseStrategy):
    """
    Synthesizes sentence cloze items.
    Stores the lemma hint on the blueprint for downstream in-situ delivery.
    """

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        distractor_mode: EnumDistractorMode = EnumDistractorMode.INTRA_LEMMA,
        target_pos: Optional[EnumPartOfSpeech] = None,
        show_lemma_hint: bool = False,
    ) -> None:
        super().__init__(db_session, request_context)
        self.distractor_mode = distractor_mode
        self.target_pos = target_pos
        self.show_lemma_hint = show_lemma_hint

    def generate_item_blueprints(
        self,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 3,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> List[schemas.ItemBlueprint]:
        blueprints: List[schemas.ItemBlueprint] = []

        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            required_pos=self.target_pos,
        )

        target_pos_str = (
            self.target_pos.value
            if hasattr(self.target_pos, "value")
            else str(self.target_pos or "").lower()
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            # 1. Prune acronyms, numeric tokens, and punctuation
            eligible_tokens = [
                t
                for t in sentence.tokens
                if t.dep_rel != "пункт"
                and not t.lex_raw.isupper()  # Reject acronyms ('АПС')
                and not any(ch.isdigit() for ch in t.lex_raw)  # Reject numbers ('90-й')
                and len(t.lex_raw) > 1  # Reject single-character initials
                and (
                    not self.target_pos
                    or str(t.features.get("pos", "")).lower() == target_pos_str
                )
                and (not self.lem_ids or (t.lem_id and t.lem_id in self.lem_ids))
            ]

            if not eligible_tokens:
                continue

            # Prioritize tokens that inflect away from the base lemma
            inflected_tokens = [
                t
                for t in eligible_tokens
                if t.lem_raw and t.lex_raw.lower() != t.lem_raw.lower()
            ]
            chosen_pool = inflected_tokens if inflected_tokens else eligible_tokens
            target_token = random.choice(chosen_pool)

            # 2. Extract distractors for potential MCQ selection
            distractors: List[str] = []
            if self.distractor_mode == EnumDistractorMode.INTRA_LEMMA:
                distractors = self.fetch_intra_lemma_distractors(
                    target_token=target_token,
                    limit=max_distractors,
                )
            elif self.distractor_mode == EnumDistractorMode.FEATURE_MATCHED:
                required_feats = target_token.features or {}
                filter_feats = {
                    k: v
                    for k, v in required_feats.items()
                    if k
                    in {"pos", "subst_case", "gram_num", "gram_tense", "verb_aspect"}
                }
                distractors = self.fetch_feature_matched_distractors(
                    target_token=target_token,
                    required_features=filter_feats,
                    limit=max_distractors,
                )

            # 3. Create clean cloze masking (no tail-end appending)
            masked_prompt, _, _ = self.mask_sentence_for_cloze(
                sentence=sentence,
                masked_token_indices=[target_token.token_idx],
                placeholder=" [___] ",
            )

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_token.token_idx],
                syntactic_focus=f"Cloze:{self.distractor_mode.value}",
            )

            # Pass the dictionary base lemma as an explicit hint on the blueprint
            lemma_hint: Optional[str] = None
            if self.show_lemma_hint and target_token.lem_raw:
                raw_lemma = target_token.lem_raw.strip()
                if target_token.is_capitalized:
                    lemma_hint = raw_lemma.capitalize()
                else:
                    lemma_hint = raw_lemma.lower()

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=masked_prompt,
                    keys=[target_token.lex_raw],
                    distractors=distractors[:max_distractors],
                    lem_id=target_token.lem_id,
                    sentence_context=bp_context,
                    hint=lemma_hint,
                )
            )

        return blueprints


class SentenceAnnotationStrategy(SentenceItemBaseStrategy):
    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        target_property: str,
        prompt_instruction: str,
        target_pos_filter: Optional[str] = None,
    ) -> None:
        super().__init__(db_session, request_context)
        self.target_property = target_property
        self.prompt_instruction = prompt_instruction
        self.target_pos_filter = target_pos_filter

    def _extract_token_property(self, token: SentenceToken) -> Optional[str]:
        if self.target_property == "dep_rel":
            return token.dep_rel
        if self.target_property.startswith("features."):
            feature_key = self.target_property.split(".", 1)[1]
            return token.features.get(feature_key) if token.features else None
        return getattr(token, self.target_property, None)

    def generate_item_blueprints(
        self,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 3,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> list[schemas.ItemBlueprint]:
        blueprints: list[schemas.ItemBlueprint] = []

        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            min_tokens=5,
            max_tokens=25,
            required_pos=self.target_pos_filter,
        )

        target_pos_str = (
            self.target_pos_filter.value
            if hasattr(self.target_pos_filter, "value")
            else str(self.target_pos_filter or "").lower()
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            valid_tokens = [
                t
                for t in sentence.tokens
                if t.dep_rel != "пункт"
                and self._extract_token_property(t) is not None
                and (
                    not self.target_pos_filter
                    or str(t.features.get("pos", "")).lower() == target_pos_str
                )
            ]

            if not valid_tokens:
                continue

            target_tok = random.choice(valid_tokens)
            raw_val = str(self._extract_token_property(target_tok))

            # English Mapping Layer
            if self.target_property == "dep_rel":
                correct_display = SYNTAGRUS_DEP_REL_MAP.get(raw_val, raw_val)
                distractor_candidates = [
                    v
                    for k, v in SYNTAGRUS_DEP_REL_MAP.items()
                    if k != raw_val and v != correct_display
                ]
            elif "verb_aspect" in self.target_property:
                correct_display = raw_val.capitalize()
                distractor_candidates = [
                    a.capitalize()
                    for a in CANONICAL_ASPECTS
                    if a.lower() != raw_val.lower()
                ]
            elif "subst_case" in self.target_property:
                correct_display = raw_val.capitalize()
                distractor_candidates = [
                    c.capitalize()
                    for c in CANONICAL_CASES
                    if c.lower() != raw_val.lower()
                ]
            else:
                correct_display = raw_val
                distractor_candidates = []

            if not distractor_candidates:
                continue

            sample_count = min(len(distractor_candidates), max_distractors)
            distractors = random.sample(distractor_candidates, sample_count)

            # In-Situ Word Highlighting in sentence body
            rendered_sentence = self.render_reconstructed_sentence(
                sentence.tokens,
                highlight_indices=[target_tok.token_idx],
            )
            prompt = f"{self.prompt_instruction}\n\n«{rendered_sentence}»"

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_tok.token_idx],
                syntactic_focus=f"Annotation:{self.target_property}",
            )

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=prompt,
                    keys=[correct_display],
                    distractors=distractors,
                    lem_id=target_tok.lem_id,
                    sentence_context=bp_context,
                )
            )

        return blueprints


class SentenceGraphStrategy(SentenceItemBaseStrategy):
    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        query_mode: EnumGraphQueryMode = EnumGraphQueryMode.FIND_GOVERNOR,
        focus_dep_rel: Optional[str] = None,
    ) -> None:
        super().__init__(db_session, request_context)
        self.query_mode = query_mode
        self.focus_dep_rel = focus_dep_rel

    def generate_item_blueprints(
        self,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 3,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> List[schemas.ItemBlueprint]:
        blueprints: List[schemas.ItemBlueprint] = []
        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            min_tokens=5,
            max_tokens=25,
            required_dep_rel=self.focus_dep_rel,
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            target_token: Optional[SentenceToken] = None
            key_token: Optional[SentenceToken] = None
            prompt: str = ""

            if self.query_mode == EnumGraphQueryMode.FIND_GOVERNOR:
                eligible = [
                    t
                    for t in sentence.tokens
                    if t.head_idx is not None
                    and t.head_idx != 0
                    and t.dep_rel != "пункт"
                ]
                if not eligible:
                    continue
                target_token = random.choice(eligible)
                key_token = self.get_token_governor(target_token, sentence.tokens)
                if not key_token:
                    continue

                rendered = self.render_reconstructed_sentence(
                    sentence.tokens,
                    highlight_indices=[target_token.token_idx],
                )
                prompt = (
                    f"On which word does the highlighted word depend?\n\n«{rendered}»"
                )

            elif self.query_mode == EnumGraphQueryMode.FIND_ROLE and self.focus_dep_rel:
                role_tokens = [
                    t for t in sentence.tokens if t.dep_rel == self.focus_dep_rel
                ]
                if not role_tokens:
                    continue
                key_token = role_tokens[0]
                target_token = key_token
                role_label = SYNTAGRUS_DEP_REL_MAP.get(
                    self.focus_dep_rel, self.focus_dep_rel
                ).lower()
                rendered = self.render_reconstructed_sentence(sentence.tokens)
                prompt = f"Identify the {role_label} in the sentence:\n\n«{rendered}»"

            if not key_token or not target_token:
                continue

            # DEFECT FIX: Exclude both the head AND the dependent itself
            excluded_indices = {key_token.token_idx, target_token.token_idx}
            excluded_texts = {key_token.lex_raw.lower(), target_token.lex_raw.lower()}

            candidate_distractors = [
                t.lex_raw
                for t in sentence.tokens
                if t.token_idx not in excluded_indices
                and t.dep_rel != "пункт"
                and t.lex_raw.lower() not in excluded_texts
            ]
            distinct_distractors = list(set(candidate_distractors))

            sample_size = min(len(distinct_distractors), max_distractors)
            sampled = (
                random.sample(distinct_distractors, sample_size)
                if sample_size > 0
                else []
            )

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_token.token_idx],
                syntactic_focus=f"Graph:{self.query_mode.value}:{self.focus_dep_rel or 'head'}",
            )

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=prompt,
                    keys=[key_token.lex_raw],
                    distractors=sampled,
                    lem_id=key_token.lem_id,
                    sentence_context=bp_context,
                )
            )

        return blueprints


class SentenceUnscrambleStrategy(SentenceItemBaseStrategy):
    """
    Generates word-reordering items with punctuation preserved and attached.
    """

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        min_tokens: int,
        max_tokens: int,
    ) -> None:
        super().__init__(db_session, request_context)
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens

    def generate_item_blueprints(
        self,
        num_items: int = 5,
        max_keys: int = 1,
        max_distractors: int = 0,
        config: Optional[schemas.StrategyConfigs] = None,
    ) -> list[schemas.ItemBlueprint]:
        blueprints: list[schemas.ItemBlueprint] = []

        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            min_tokens=self.min_tokens,
            max_tokens=self.max_tokens,
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            # assemble words with attached punctuation
            original_words = self.assemble_tokens_with_punctuation(sentence.tokens)
            if len(original_words) < self.min_tokens:
                continue

            # enforce non-identity shuffling
            shuffled = list(original_words)
            attempts = 0
            while shuffled == original_words and attempts < 10:
                random.shuffle(shuffled)
                attempts += 1

            if shuffled == original_words:
                continue

            content_indices = [
                t.token_idx for t in sentence.tokens if t.dep_rel != "пункт"
            ]

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=content_indices,
                syntactic_focus="Unscramble:LinearOrder",
            )

            # store canonical array in keys, shuffled array in distractors
            blueprints.append(
                schemas.ItemBlueprint(
                    prompt="Put the words in the correct order:",
                    keys=original_words,
                    distractors=shuffled,
                    lem_id=None,
                    sentence_context=bp_context,
                )
            )

        return blueprints
