"""
app/backend/services/items/sentence_subclasses.py

Parameterized subclasses for sentence-level item generation in ALITE.
Consolidates Cloze, Grammatical Annotation, Syntactic Graph Traversal,
and Unscrambling into four reusable, language-independent engines.
"""

from __future__ import annotations

import logging
import random
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from alite_backend.db import models, schemas
from alite_backend.db.models import EnumPartOfSpeech, Sentence, SentenceToken
from alite_backend.services.items.sentence_base import SentenceItemBaseStrategy
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ============================================================================
# Strategy Configuration Enums
# ============================================================================


class EnumDistractorMode(str, Enum):
    INTRA_LEMMA = "intra_lemma"  # Other forms of the SAME lemma (morphology)
    FEATURE_MATCHED = "feature_matched"  # Different lemmas with SAME features (lexical)


class EnumGraphQueryMode(str, Enum):
    FIND_GOVERNOR = "find_governor"  # "Which word governs X?"
    FIND_DEPENDENT = "find_dependent"  # "Which word depends on X with relation R?"
    FIND_ROLE = "find_role"  # "Find the subject / direct object in this clause"


# sentence cloze strategy (fill-in-the-blank & word choice mcqs)
class SentenceClozeStrategy(SentenceItemBaseStrategy):
    """
    Generates items where a target token within a sentence is blanked out.
    Supports both morphological inflection drills (intra-lemma distractors)
    and contextual vocabulary drills (feature-matched inter-lemma distractors).
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
    ) -> list[schemas.ItemBlueprint]:
        blueprints: list[schemas.ItemBlueprint] = []

        # fetch candidate sentences satisfying token length & POS constraints
        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            required_pos=self.target_pos,
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            # filter candidate tokens inside the sentence eligible for masking
            eligible_tokens = [
                t
                for t in sentence.tokens
                if t.dep_rel != "пункт"  # Exclude punctuation tokens
                and (
                    not self.target_pos
                    or (t.features and t.features.get("pos") == self.target_pos)
                )
                and (not self.lem_ids or (t.lem_id and t.lem_id in self.lem_ids))
            ]

            if not eligible_tokens:
                continue

            target_token = random.choice(eligible_tokens)

            # harvest distractors according to configured mode
            distractors: list[str] = []
            if self.distractor_mode == EnumDistractorMode.INTRA_LEMMA:
                distractors = self.fetch_intra_lemma_distractors(
                    target_token=target_token,
                    limit=max_distractors,
                )
            elif self.distractor_mode == EnumDistractorMode.FEATURE_MATCHED:
                required_feats = target_token.features or {}
                # match pos and case/tense/number, stripping non-comparable keys
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

            # graceful degradation: ensure option pool sufficiency
            if len(distractors) < max_distractors:
                continue

            # construct client-safe cloze representation
            masked_prompt, display_tokens, _ = self.mask_sentence_for_cloze(
                sentence=sentence,
                masked_token_indices=[target_token.token_idx],
                placeholder="[___]",
            )

            # append hint if enabled (e.g. for beginner curriculum tracks)
            if self.show_lemma_hint and target_token.lem_raw:
                masked_prompt = f"{masked_prompt} ({target_token.lem_raw})"

            # build blueprint context preserving ground-truth validation data
            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_token.token_idx],
                syntactic_focus=f"Cloze:{self.distractor_mode.value}",
            )

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=masked_prompt,
                    keys=[target_token.lex_raw],
                    distractors=distractors[:max_distractors],
                    lem_id=target_token.lem_id,
                    sentence_context=bp_context,
                )
            )

        return blueprints


# sentence annotation strategy (categorical property mcqs)


class SentenceAnnotationStrategy(SentenceItemBaseStrategy):
    """
    Displays an intact sentence with a target token highlighted.
    Prompts the user to identify a categorical attribute (e.g. Case, Verb Aspect,
    Part of Speech, or SynTagRus Dependency Relation).
    """

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
                    or (t.features and t.features.get("pos") == self.target_pos_filter)
                )
            ]

            if not valid_tokens:
                continue

            target_tok = random.choice(valid_tokens)
            correct_val = str(self._extract_token_property(target_tok))

            # Mine categorical distractors safely without DISTINCT + ORDER BY random()
            if self.target_property == "dep_rel":
                stmt = (
                    select(SentenceToken.dep_rel)
                    .where(
                        and_(
                            SentenceToken.dep_rel.is_not(None),
                            SentenceToken.dep_rel != correct_val,
                            SentenceToken.dep_rel != "пункт",
                        )
                    )
                    .distinct()
                )
                pool = [r for r in self.db.scalars(stmt).all() if r]
            else:
                feature_key = self.target_property.split(".")[-1]
                stmt = (
                    select(SentenceToken.features[feature_key].as_string())
                    .where(
                        and_(
                            SentenceToken.features[feature_key].is_not(None),
                            SentenceToken.features[feature_key].as_string()
                            != correct_val,
                        )
                    )
                    .distinct()
                )
                pool = [d for d in self.db.scalars(stmt).all() if d]

            if len(pool) < max_distractors:
                continue

            # Randomize candidate options in Python
            distractors = random.sample(pool, max_distractors)

            rendered_sentence = self.render_reconstructed_sentence(sentence.tokens)
            prompt = (
                f"{self.prompt_instruction}\n\n"
                f"«{rendered_sentence}»\n"
                f"(Целевое слово: **{target_tok.lex_raw}**)"
            )

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_tok.token_idx],
                syntactic_focus=f"Annotation:{self.target_property}",
            )

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=prompt,
                    keys=[correct_val],
                    distractors=distractors,
                    lem_id=target_tok.lem_id,
                    sentence_context=bp_context,
                )
            )

        return blueprints


# sentence graph strategy (constituent search & dependency edge mcqs)


class SentenceGraphStrategy(SentenceItemBaseStrategy):
    """
    Generates syntactic dependency items where the words *within* the sentence
    form the multiple-choice options (interactive token selection).
    Learners click on tokens to identify governors, subjects, or arguments.
    """

    def __init__(
        self,
        db_session: Session,
        request_context: schemas.ExerciseContext,
        query_mode: EnumGraphQueryMode = EnumGraphQueryMode.FIND_GOVERNOR,
        focus_dep_rel: Optional[
            str
        ] = None,  # e.g. "предик" (subject), "1-компл" (object)
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
    ) -> list[schemas.ItemBlueprint]:
        blueprints: list[schemas.ItemBlueprint] = []

        candidates = self._get_candidate_sentences(
            limit=num_items * 3,
            min_tokens=5,
            max_tokens=20,
            required_dep_rel=self.focus_dep_rel,
        )

        for sentence in candidates:
            if len(blueprints) >= num_items:
                break

            target_token: Optional[SentenceToken] = None
            key_token: Optional[SentenceToken] = None
            prompt: str = ""

            # scenario a: find the governor/head of word x
            if self.query_mode == EnumGraphQueryMode.FIND_GOVERNOR:
                eligible_tokens = [
                    t
                    for t in sentence.tokens
                    if t.head_idx is not None
                    and t.head_idx != 0
                    and t.dep_rel != "пункт"
                ]
                if not eligible_tokens:
                    continue
                target_token = random.choice(eligible_tokens)
                key_token = self.get_token_governor(target_token, sentence.tokens)
                if not key_token:
                    continue
                prompt = (
                    f"On which word in the current sentence does the highlighted word depend?\n\n"
                    f"«{self.render_reconstructed_sentence(sentence.tokens)}»\n"
                    f"(dependent word: **{target_token.lex_raw}**)"
                )

            # scenario b: find by syntactic role (e.g., subject / 'предик')
            elif self.query_mode == EnumGraphQueryMode.FIND_ROLE and self.focus_dep_rel:
                role_tokens = [
                    t for t in sentence.tokens if t.dep_rel == self.focus_dep_rel
                ]
                if not role_tokens:
                    continue
                key_token = role_tokens[0]
                target_token = key_token
                role_label = (
                    "subject"
                    if self.focus_dep_rel == "предик"
                    else f"rel: '{self.focus_dep_rel}'"
                )
                prompt = (
                    f"Find the {role_label} in the sentence:\n\n"
                    f"«{self.render_reconstructed_sentence(sentence.tokens)}»"
                )

            if not key_token or not target_token:
                continue

            # distractors are sibling content words from the SAME sentence
            candidate_distractor_tokens = [
                t
                for t in sentence.tokens
                if t.token_idx != key_token.token_idx and t.dep_rel != "пункт"
            ]

            if len(candidate_distractor_tokens) < max_distractors:
                continue

            # pick distinct wordforms
            distractors = list(
                {
                    t.lex_raw
                    for t in candidate_distractor_tokens
                    if t.lex_raw != key_token.lex_raw
                }
            )
            if len(distractors) < max_distractors:
                continue

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[target_token.token_idx],
                syntactic_focus=f"Graph:{self.query_mode.value}:{self.focus_dep_rel or 'head'}",
            )

            blueprints.append(
                schemas.ItemBlueprint(
                    prompt=prompt,
                    keys=[key_token.lex_raw],
                    distractors=random.sample(distractors, max_distractors),
                    lem_id=key_token.lem_id,
                    sentence_context=bp_context,
                )
            )

        return blueprints


# sentence unscramble strategy (syntactic ordering & permutation)


class SentenceUnscrambleStrategy(SentenceItemBaseStrategy):
    """
    Generates word-reordering items. Ingests a syntactically verified sentence,
    packages words into moveable tokens, enforces non-identity shuffling,
    and assigns ephemeral UUID handles for client-side evaluation security.
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

            # filter out standalone punctuation for dragging ease:
            # attach to words or retain lexical tokens
            content_tokens = [t for t in sentence.tokens if t.dep_rel != "пункт"]
            if len(content_tokens) < self.min_tokens:
                continue

            # original sequential token strings
            original_words = [t.lex_raw for t in content_tokens]

            # enforce non-identity permutation
            shuffled_words = list(original_words)
            attempts = 0
            while shuffled_words == original_words and attempts < 10:
                random.shuffle(shuffled_words)
                attempts += 1

            if shuffled_words == original_words:
                continue

            bp_context = self.build_sentence_blueprint_context(
                sentence=sentence,
                target_indices=[t.token_idx for t in content_tokens],
                syntactic_focus="Unscramble:LinearOrder",
            )

            # in ItemBlueprint, keys holds the canonical ordered tokens;
            # distractors holds the permuted token sequence
            blueprints.append(
                schemas.ItemBlueprint(
                    prompt="Расставьте слова в правильном порядке, чтобы получилось предложение:",
                    keys=original_words,
                    distractors=shuffled_words,
                    lem_id=None,
                    sentence_context=bp_context,
                )
            )

        return blueprints
