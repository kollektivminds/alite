from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from alite_backend.db.models import Lemma, Lexeme, GramProp, WordForm
from alite_backend.db.schemas import (
    LemmasRecord,
    GramPropsRecord,
    LexiconRecord,
    DefinitionsRecord,
    DefExamplesRecord,
    PronunciationsRecord,
    VerbPairsRecord,
    ProcessedPayload,
)
import logging

# O
# H


def _map_lemma(lemma_record: LemmasRecord):
    """_map_lemma _summary_

    Args:
        lemma_record (LemmasRecord): _description_

    Returns:
        _type_: _description_
    """
    mapped_lemma = Lemma(
        entry_key=lemma_record.entry_key,
        lem_text=lemma_record.clean_lemma,
        lem_canon=lemma_record.accent_lemma,
        pos=lemma_record.pos,
    )
    return mapped_lemma


grammar_tag_map = {
    # verb_aspect
    "imperfective": {"verb_aspect": 0},
    "perfective": {"verb_aspect": 0},
    "imperfective": {"verb_aspect": 0},
    # verb_conj
    # verb_type
    # verb_mood
    # verb_trans_refl
    # verb_person
    "first-person": {"verb_person": 1},
    "second-person": {"verb_person": 2},
    "third-person": {"verb_person": 3},
    # part_type
    # part_voice
    "active": {"part_voice": 0},
    "passive": {"part_voice": 1},
    # subst_case
    "nominative": {"subst_case": 0},
    "genitive": {"subst_case": 1},
    "accusative": {"subst_case": 2},
    "dative": {"subst_case": 3},
    "instrumental": {"subst_case": 4},
    "prepositional": {"subst_case": 5},
    "vocative": {"subst_case": 6},
    "locative": {"subst_case": 7},
    "partitive": {"subst_case": 8},
    # subst_animacy
    "animate": {"subst_animacy": True},
    "inanimate": {"subst_animacy": False},
    # adjv_short
    "short-form": {"adjv_short": True},
    # diminutive
    # gram_gender
    "masculine": {"gram_gender": 0},
    "neuter": {"gram_gender": 1},
    "feminine": {"gram_gender": 2},
    "dual": {"gram_gender": 3},
    # gram_number
    "singular": {"gram_gender": 0},
    "plural": {"gram_gender": 1},
    "dual": {"gram_gender": 2},
    # gram_tense
    "past": {"gram_tense": 0},
    "present": {"gram_tense": 1},
    "future": {"gram_tense": 2},
}


def _parse_grammar_tags(payload_tags: list[str]) -> dict:

    props = {}

    for tag in payload_tags:
        # tag = tag.lower()

        if tag in grammar_tag_map:
            props.update(grammar_tag_map[tag])

    return props


#
# C
#

# cog = create or get


def cog_lemma(db: Session, lemma_record: LemmasRecord) -> Lemma:
    """create_lemma _summary_

    Args:
        db (Session): _description_
        lemma_record (LemmasRecord): _description_

    Returns:
        _type_: _description_
    """
    sql_lemma = _map_lemma(lemma_record=lemma_record)

    db.add(sql_lemma)
    db.flush()
    db.refresh(sql_lemma)

    return sql_lemma


def cog_lexeme(db: Session, word_form: str) -> Lexeme:
    """
    Creates a new lexeme entry and links it to its lemma.
    """
    db_lexeme = Lexeme(word_text=word_form)
    db.add(db_lexeme)
    db.flush()
    db.refresh(db_lexeme)
    return db_lexeme


def cog_gram_prop(
    db: Session,
    verb_aspect: Optional[int] = None,
    verb_conj: Optional[str] = None,
    verb_type: Optional[int] = None,
    verb_mood: Optional[int] = None,
    verb_trans_refl: Optional[int] = None,
    verb_person: Optional[int] = None,
    part_type: Optional[int] = None,
    subst_case: Optional[int] = None,
    subst_animacy: Optional[bool] = None,
    adjv_short: Optional[bool] = None,
    diminutive: Optional[bool] = None,
    gram_gender: Optional[int] = None,
    gram_number: Optional[int] = None,
    gram_tense: Optional[int] = None,
    irregular: Optional[bool] = None,
) -> GramProp:
    prop_cols = locals()
    prop_cols = prop_cols.pop("db", None)
    db_gram_prop = GramProp(prop_cols)
    db.add(db_gram_prop)
    db.flush()
    db.refresh(db_gram_prop)
    return db_gram_prop


def cog_word_form(db: Session, lem_id: int, lex_id: int, gram_id: int) -> WordForm:
    form_cols = locals()
    form_cols = form_cols.pop("db", None)
    db_word_form = WordForm(form_cols)
    db.add(db_word_form)
    db.flush()
    db.refresh(db_word_form)
    return db_word_form


#
# R
#


def get_lemmas(
    db: Session,
    id: Optional[int] = None,
    entry_key: Optional[UUID] = None,
    clean_lemma: Optional[str] = None,
    accent_lemma: Optional[str] = None,
    pos: Optional[int] = None,
) -> List[Lemma] | Lemma:  # type: ignore
    """get_lemmas _summary_

    Args:
        db (Session): _description_
        id (Optional[int], optional): _description_. Defaults to None.
        entry_key (Optional[UUID], optional): _description_. Defaults to None.
        clean_lemma (Optional[str], optional): _description_. Defaults to None.
        accent_lemma (Optional[str], optional): _description_. Defaults to None.
        pos (Optional[int], optional): _description_. Defaults to None.

    Returns:
        List[Lemma]: _description_
    """
    # base statement
    stmt = select(Lemma)

    # get immediately by entry_key or id
    if entry_key is not None:
        stmt = stmt.where(Lemma.entry_key == entry_key)
        return db.scalar(statement=stmt)

    if id is not None:
        stmt = stmt.where(Lemma.id == id)
        return db.scalar(statement=stmt)

    # dynamic chaining for casting a wider net
    if clean_lemma is not None:
        stmt = stmt.where(Lemma.lem_text == clean_lemma)
    if accent_lemma is not None:
        stmt = stmt.where(Lemma.lem_canon == accent_lemma)
    if pos is not None:
        stmt = stmt.where(Lemma.pos == pos)
    logging.debug(stmt)
    return list(db.scalars(statement=stmt).all())


# creating definitions, gram_props and linking them together in join tables

#
# U
#

#
# D
#
