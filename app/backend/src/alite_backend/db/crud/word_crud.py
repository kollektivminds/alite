import logging
from typing import List, Optional, Sequence
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from alite_backend.db.models import (
    Lemma,
    Lexeme,
    GramProp,
    WordForm,
    Definition,
    Example,
    DefinitionExample,
    Pronunciation,
    LemmaDefinition,
    LemmaRelation,
    LessonList,
    LemmaInLessonList,
    LessonListInModule,
    Module,
)
from alite_backend.db.schemas import (
    LemmasRecord,
    GramPropsRecord,
    LexiconRecord,
    DefinitionsRecord,
    DefExamplesRecord,
    PronunciationsRecord,
    RelatedLemmaRecord,
    ProcessedPayload,
)
from alite_backend.words.funcs import remove_accents

# O
# H

complete_props = {
    "verb_aspect": None,
    "verb_conj": None,
    "verb_type": None,
    "verb_mood": None,
    "verb_trans_refl": None,
    "conj_person": None,
    "verb_infinitive": None,
    "part_type": None,
    "subst_case": None,
    "subst_animacy": None,
    "adjv_comp_type": None,
    "adjv_short": None,
    "diminutive": None,
    "conj_gender": None,
    "gram_number": None,
    "gram_tense": None,
    "irregular": None,
}


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


#
# C
#

# goc = get or create


def goc_lemma(db: Session, lemma_record: LemmasRecord) -> Lemma | List[Lemma]:
    """create_lemma _summary_

    Args:
        db (Session): _description_
        lemma_record (LemmasRecord): _description_

    Returns:
        _type_: _description_
    """
    entry_key, clean_lemma, accent_lemma, pos = (
        lemma_record.entry_key,
        lemma_record.clean_lemma,
        lemma_record.accent_lemma,
        lemma_record.pos,
    )
    existing_lem = get_lemmas(
        db=db,
        entry_key=entry_key,
        clean_lemma=clean_lemma,
        accent_lemma=accent_lemma,
        pos=pos,
    )
    if existing_lem:
        return existing_lem
    else:
        sql_lemma = _map_lemma(lemma_record=lemma_record)
        db.add(sql_lemma)
        db.flush()
        db.refresh(sql_lemma)

        return sql_lemma


def goc_lexeme(db: Session, word_form: str) -> Lexeme:
    """
    Creates a new lexeme entry and links it to its lemma.
    """
    lex_search_stmt = select(Lexeme).where(Lexeme.lex_text == word_form)
    existing_lex = db.scalars(statement=lex_search_stmt).one_or_none()
    # logging.debug("lexeme search_results: %s", search_results)
    if existing_lex:
        return existing_lex
    else:
        # logging.debug("making LexemRecord for %s", word_form)
        db_lexeme = Lexeme(lex_text=word_form, lex_text_clean=remove_accents(word_form))
        db.add(db_lexeme)
        db.flush()
        db.refresh(db_lexeme)
        return db_lexeme


def goc_gramprop(db: Session, incoming_props: dict) -> GramProp:
    existing_gramprop = get_gramprop(db, incoming_props)
    if existing_gramprop:
        # logging.debug("This prop exists")
        return existing_gramprop
    else:
        # logging.debug("This prop doesn't exist")
        these_props = complete_props | incoming_props
        new_gram_prop = GramProp(**these_props)
        db.add(new_gram_prop)
        db.flush()
        db.refresh(new_gram_prop)
        return new_gram_prop


def goc_wordform(db: Session, form_ids: dict[str, int]) -> WordForm:
    logging.debug("goc_wordform form_ids: %s", form_ids)
    existing_wordform = get_wordform(db, **form_ids)
    if existing_wordform:
        logging.debug("This wordform exists")
        return existing_wordform
    else:
        new_word_form = WordForm(**form_ids)
        db.add(new_word_form)
        db.flush()
        db.refresh(new_word_form)
        return new_word_form


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
) -> List[Lemma]:  # type: ignore
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
        return db.scalars(statement=stmt).one_or_none()

    if id is not None:
        stmt = stmt.where(Lemma.id == id)
        return db.scalars(statement=stmt).one_or_none()

    # dynamic chaining for casting a wider net
    if clean_lemma is not None:
        stmt = stmt.where(Lemma.lem_text == clean_lemma)
    if accent_lemma is not None:
        stmt = stmt.where(Lemma.lem_canon == accent_lemma)
    if pos is not None:
        stmt = stmt.where(Lemma.pos == pos)
    # logging.debug(stmt)
    return list(db.scalars(statement=stmt).all())


def get_lexemes(db: Session, lex_text: str) -> List[Lexeme]:
    stmt = select(Lexeme).where(Lexeme.lex_text == lex_text)
    return list(db.scalars(statement=stmt).all())


def get_gramprop(db: Session, incoming_props: dict) -> GramProp:
    # logging.debug("get_gramprop complete_props: %s", complete_props)
    these_props = complete_props | incoming_props
    # logging.debug("get_gramprop these_props: %s", these_props)
    stmt = select(GramProp).filter_by(**these_props)
    existing_gramprop = db.scalars(stmt).first()
    return existing_gramprop


def get_wordform(db: Session, lem_id: int, lex_id: int, gram_id: int) -> WordForm:
    stmt = select(WordForm)

    if lem_id is not None:
        stmt = stmt.where(WordForm.lem_id == lem_id)
    if lex_id is not None:
        stmt = stmt.where(WordForm.lex_id == lex_id)
    if gram_id is not None:
        stmt = stmt.where(WordForm.gram_id == gram_id)

    existing_wordform = db.scalars(stmt).first()

    return existing_wordform


# creating definitions, gram_props and linking them together in join tables


def get_definitions(db: Session, def_id: Optional[int], def_text: Optional[str]) -> Definition | Sequence[Definition]:
    stmt = select(Definition)
    
    existing_definition = db.scalars(stmt).all()
    
    return existing_definition

#
# U
#

#
# D
#
