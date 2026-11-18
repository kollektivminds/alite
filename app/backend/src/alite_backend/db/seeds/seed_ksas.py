# app/backend/db/seeds/seed_ksas.py
# Heavily commented outline for seeding the KSA ontology hierarchically.

from sqlalchemy.orm import Session

from alite_backend.db.models import KSA


def seed_ksa_ontology(session: Session) -> None:
    """
    Idempotently seeds the initial KSA ontology tree matching the site UI:
    Words (Semantics, Grammar, Spelling/Phonology) and Sentences.
    """
    # define root nodes dictionary structure
    ksa_tree = {
        "Words": {
            "description": "Core lexical and morphological knowledge domains for words.",
            "children": {
                "Semantics": {
                    "description": "Meaning, synonyms, antonyms, and shared root lemmas.",
                    "children": {
                        "Lemma Meaning": "Understanding core dictionary definitions.",
                        "Synonyms": "Identifying semantic equivalents.",
                        "Antonyms": "Identifying semantic opposites.",
                        "Shared Roots": "Recognizing etymological root connections.",
                    },
                },
                "Grammar": {
                    "description": "Morphological properties and syntactic behavior.",
                    "children": {
                        "Part of Speech": "Identifying lexical category.",
                        "Noun Morphology": "Declension, gender, and animacy.",
                        "Verb Morphology": "Conjugations, aspect, transitivity, and reflexivity.",
                        "Adjective Morphology": "Declension, short forms, and comparative/superlative types.",
                    },
                },
                "Phonology": {
                    "description": "Orthography, spelling, and pronunciation.",
                    "children": {
                        "Spelling": "Orthographic accuracy and character sequences.",
                        "Pronunciation": "Stress placement and phonetic realization.",
                    },
                },
            },
        },
        "Sentences": {
            "description": "Syntactic parsing, dependency relations, and sentence-level cloze constructs.",
            "children": {
                "Syntax": "Dependency relations, head identification, and subject-verb agreement.",
                "Sentence Morphology": "Contextual case assignment and verbal aspect in context.",
            },
        },
    }

    # 2. Recursive helper function to insert nodes safely
    def insert_node(
        name: str,
        description: str | None,
        parent_id: int | None,
        children_dict: dict | None,
    ):
        # Check if node already exists under this parent to maintain idempotency
        existing = session.query(KSA).filter_by(name=name, parent_id=parent_id).first()
        if not existing:
            node = KSA(name=name, description=description, parent_id=parent_id)
            session.add(node)
            session.flush()  # Flush to generate surrogate PK ID
            current_id = node.id
        else:
            current_id = existing.id

        if children_dict:
            for child_name, child_data in children_dict.items():
                if isinstance(child_data, dict):
                    desc = child_data.get("description")
                    sub_children = child_data.get("children")
                    insert_node(child_name, desc, current_id, sub_children)
                else:
                    # Leaf node string description
                    insert_node(child_name, child_data, current_id, None)

    # 3. Execute seeding
    for root_name, root_data in ksa_tree.items():
        insert_node(root_name, root_data["description"], None, root_data["children"])

    session.commit()
