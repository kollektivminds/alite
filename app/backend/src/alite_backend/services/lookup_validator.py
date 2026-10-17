# app/backend/services/lemma_validator.py
from typing import Dict, List, Set

from alite_backend.db.models import EnumPartOfSpeech, Lemma
from alite_backend.db.schemas import LemmaCapabilityReport
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload


class LemmaReadinessValidator:
    """
    Validates that a newly scraped or existing Lemma has sufficient
    relational nodes to be used safely in question generation algorithms.
    """

    @classmethod
    def evaluate_lemma(cls, db: Session, lemma_id: int) -> LemmaCapabilityReport:
        stmt = (
            select(Lemma)
            .where(Lemma.id == lemma_id)  # type: ignore
            .options(
                selectinload(Lemma.definitions),  # type: ignore
                selectinload(Lemma.pronunciations),  # type: ignore
                selectinload(Lemma.lemma_word_form),  # type: ignore
                selectinload(Lemma.related_to),  # type: ignore
            )
        )
        lemma = db.scalars(stmt).first()

        if not lemma:
            return LemmaCapabilityReport(
                lemma_id=lemma_id,
                lem_text="UNKNOWN",
                is_exercise_ready=False,
                missing_critical_data=["Record not found in database"],
                supported_item_types=[],
            )

        missing: List[str] = []
        capabilities: List[str] = []

        # 1. Base lexical check
        if not lemma.lem_canon:
            missing.append("Missing canonical stress-marked form (lem_canon)")

        # 2. Semantic check (Definitions required for flashcards, clozes, and MCQ)
        if not lemma.definitions:
            missing.append("No definitions attached")
        else:
            capabilities.extend(["lem_to_def", "def_to_lem"])

        # 3. Phonetic check
        if lemma.pronunciations:
            capabilities.extend(["lem_to_pron", "pron_to_lem"])

        # 4. Morphological inflection checks based on part of speech
        pos = lemma.pos
        form_count = len(lemma.lemma_word_form) if lemma.lemma_word_form else 0

        if pos == EnumPartOfSpeech.VERB:
            if not lemma.verb_aspect:
                missing.append(
                    "Verb missing aspect classification (imperfective/perfective)"
                )
            else:
                capabilities.append("verb_to_aspt")

            # Aspectual pairs
            if lemma.related_to and any(
                r.rel_type in ("perfective_pair_of", "imperfective_pair_of")
                for r in lemma.related_to
            ):
                capabilities.append("verb_to_aspt_pair")

            # Verbs require conjugated forms in word_forms
            if form_count < 3:
                missing.append(
                    f"Insufficient conjugated forms (found {form_count}, minimum 3 required)"
                )
            else:
                capabilities.append("verb_to_conj_form")

        elif pos == EnumPartOfSpeech.NOUN:
            if not lemma.noun_gender:
                missing.append("Noun missing grammatical gender")
            else:
                capabilities.append("noun_to_gend")

            if form_count < 2:
                missing.append(f"Insufficient declined noun forms (found {form_count})")
            else:
                capabilities.append("noun_form_to_gram")

        # Readiness verdict: Must have canonical form, at least 1 definition, and no blocking gaps
        is_ready = len(missing) == 0 and len(capabilities) > 0

        return LemmaCapabilityReport(
            lemma_id=lemma.id,  # type: ignore
            lem_text=lemma.lem_text,
            is_exercise_ready=is_ready,
            missing_critical_data=missing,
            supported_item_types=capabilities,
        )
