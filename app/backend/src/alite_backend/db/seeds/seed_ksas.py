# app/backend/db/seeds/seed_ksas.py
import logging
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from alite_backend.db.models import KSA

logger = logging.getLogger(__name__)


def seed_ksa_ontology(session: Session) -> None:
    """
    Idempotently seeds and updates the hierarchical KSA ontology tree.
    Supports variable depths (e.g., Words -> Grammar -> Noun Morphology -> Noun Case).
    """
    ksa_tree: Dict[str, Any] = {
        "Words": {
            "description": "Core lexical, morphological, and phonological knowledge domains for isolated words.",  # noqa: E501
            "children": {
                "Semantics": {
                    "description": "Lexical meaning, semantic equivalence, opposition, and derivational roots.",  # noqa: E501
                    "children": {
                        "Definitions": "Mapping lemmas to their core dictionary meanings.",  # noqa: E501
                        "Synonyms & Antonyms": "Identifying lemmas with similar and opposite meanings.",  # noqa: E501
                        "Shared Roots": "Recognizing etymological and derivational root connections across lemmas.",  # noqa: E501
                    },
                },
                "Grammar": {
                    "description": "Lexical categories, inherent grammatical traits, and inflectional paradigms.",  # noqa: E501
                    "children": {
                        "Parts of Speech": "Identifying the grammatical category of a lemma.",  # noqa: E501
                        "Noun Gender": "Identifying inherent grammatical gender (masculine, feminine, neuter).",  # noqa: E501
                        "Noun Animacy": "Distinguishing animate from inanimate nouns for accusative agreement.",  # noqa: E501
                        "Noun Morphology": {
                            "description": "Inflecting and parsing noun forms across nominal paradigms.",  # noqa: E501
                            "children": {
                                "Noun Case": "Declining and identifying nouns across grammatical cases.",  # noqa: E501
                                "Noun Number": "Distinguishing and forming singular and plural noun forms.",  # noqa: E501
                            },
                        },
                        "Adjective Morphology": {
                            "description": "Inflecting and parsing adjectives across agreement and degree paradigms.",  # noqa: E501
                            "children": {
                                "Adjective Case": "Declining and identifying adjectives across grammatical cases.",  # noqa: E501
                                "Adjective Number": "Forming and identifying singular and plural adjective agreement.",  # noqa: E501
                                "Adjective Gender": "Forming and identifying masculine, feminine, and neuter adjective agreement.",  # noqa: E501
                                "Adjective Degree & Form": "Forming and recognizing short-form, comparative, and superlative adjectives.",  # noqa: E501
                            },
                        },
                        "Verb Aspect": "Distinguishing imperfective, perfective, and biaspectual verbs.",  # noqa: E501
                        "Verb Pairs": "Mapping imperfective and perfective verbs to their aspectual partners.",  # noqa: E501
                        "Verb Type": "Identifying verb conjugation classes (Type I vs. Type II).",  # noqa: E501
                        "Verb TNRF": "Identifying verbal transitivity, intransitivity, and reflexivity.",  # noqa: E501
                        "Verb Morphology": {
                            "description": "Conjugating and parsing finite verb forms across verbal paradigms.",  # noqa: E501
                            "children": {
                                "Verb Tense": "Forming and identifying past, present, and future verb tenses.",  # noqa: E501
                                "Verb Person": "Conjugating and identifying first-, second-, and third-person forms.",  # noqa: E501
                                "Verb Number": "Forming and identifying singular and plural verb conjugations.",  # noqa: E501
                                "Verb Gender": "Forming and identifying past-tense gender agreement on singular verbs.",  # noqa: E501
                                "Verb Mood": "Forming and identifying indicative and imperative verb moods.",  # noqa: E501
                            },
                        },
                    },
                },
                "Phonology": {
                    "description": "Orthographic accuracy, stress placement, and phonetic realization.",  # noqa: E501
                    "children": {
                        "Spelling": "Producing accurate orthographic character sequences.",  # noqa: E501
                        "Pronunciation": "Identifying stress placement and phonetic/IPA realization.",  # noqa: E501
                    },
                },
            },
        },
        "Sentences": {
            "description": "Syntactic parsing, dependency relations, and contextualized lexicogrammar.",  # noqa: E501
            "children": {
                "Syntax": {
                    "description": "Structural dependency relations, constituency, and word order.",  # noqa: E501
                    "children": {
                        "Sentence Dependency": "Identifying the syntactic dependency role of a token within a clause.",  # noqa: E501
                        "Find Sentence Head": "Identifying the syntactic governor (head) of a target word.",  # noqa: E501
                        "Find Sentence Subject": "Identifying the grammatical subject (predicate anchor) of a sentence.",  # noqa: E501
                        "Unscramble Sentence": "Reconstructing grammatically and pragmatically valid Russian word order.",  # noqa: E501
                    },
                },
                "Contextual Lexicogrammar": {
                    "description": "Applying lexical meaning and morphological inflection within authentic sentence contexts.",  # noqa: E501
                    "children": {
                        "Adjectives in Context": "Selecting or producing correctly inflected adjective forms in a sentence.",  # noqa: E501
                        "Aspect in Context": "Identifying or selecting the appropriate verbal aspect given discourse context.",  # noqa: E501
                        "Case in Context": "Identifying the grammatical case required by syntactic governors in context.",  # noqa: E501
                        "Meaning in Context": "Selecting the semantically appropriate lemma to fit a sentence context.",  # noqa: E501
                        "Nouns in Context": "Selecting or producing correctly inflected noun forms in a sentence.",  # noqa: E501
                        "Verbs in Context": "Selecting or producing correctly conjugated verb forms in a sentence.",  # noqa: E501
                    },
                },
            },
        },
    }

    def insert_node(
        name: str,
        description: Optional[str],
        parent_id: Optional[int],
        children_dict: Optional[Dict[str, Any]],
    ) -> None:
        # Use SQLAlchemy 2.0 select() style rather than legacy session.query()
        stmt = select(KSA).where(KSA.name == name, KSA.parent_id == parent_id)  # type: ignore
        existing = session.scalars(stmt).first()

        if not existing:
            node = KSA(name=name, description=description, parent_id=parent_id)
            session.add(node)
            session.flush()  # Mint surrogate PK for child parent_id references
            current_id = node.id
        else:
            # Keep descriptions synchronized if they were previously blank or updated
            if description and existing.description != description:
                existing.description = description
                session.add(existing)
            current_id = existing.id

        if children_dict:
            for child_name, child_data in children_dict.items():
                if isinstance(child_data, dict):
                    insert_node(
                        name=child_name,
                        description=child_data.get("description"),
                        parent_id=current_id,
                        children_dict=child_data.get("children"),
                    )
                else:
                    # Leaf node: child_data is the description string
                    insert_node(
                        name=child_name,
                        description=child_data,
                        parent_id=current_id,
                        children_dict=None,
                    )

    for root_name, root_data in ksa_tree.items():
        insert_node(
            name=root_name,
            description=root_data["description"],
            parent_id=None,
            children_dict=root_data["children"],
        )


if __name__ == "__main__":
    # deferred imports keep SessionLocal and logging setup out of module import scope,
    # matching the migration-safe pattern used in init_db.py.
    from alite_backend.db.db_session import SessionLocal
    from alite_backend.logging_config import setup_logging

    setup_logging()

    # Context manager guarantees the session closes cleanly even if an exception occurs.
    with SessionLocal() as db:
        try:
            seed_ksa_ontology(session=db)
            db.commit()
            logger.info("KSA ontology seeded and committed successfully.")
        except Exception as exc:
            db.rollback()
            logger.exception("Failed to seed KSA ontology: %s", exc)
            raise
