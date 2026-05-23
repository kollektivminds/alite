import logging
from typing import List, Optional, Sequence
from uuid import UUID
from functools import wraps
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from sqlalchemy.exc import (
    SQLAlchemyError,
    IntegrityError,
    ProgrammingError,
    DBAPIError,
    NoResultFound,
    StatementError,
)
from fastapi import HTTPException, status
from alite_backend.db.models import (
    EnumAltAdjvType,
    EnumAltNounType,
    EnumGramGender,
    EnumConjPerson,
    EnumGramTense,
    EnumPartType,
    EnumPartVoice,
    EnumPartOfSpeech,
    EnumSubstCase,
    EnumVerbAspect,
    EnumVerbMood,
    EnumVerbTransRefl,
    EnumVerbType,
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
    LookupQueue,
    LessonList,
    LemmaInLessonList,
    LessonListInModule,
    Module,
)
from alite_backend.db.schemas import (
    LemmasRecord,
    LemmaCreate,
    LemmaUpdate,
    LemmaSearchParams,
    LexiconRecord,
    LexemeCreate,
    LexemeUpdate,
    LexemeReturn,
    GramPropsRecord,
    GramPropCreate,
    GramPropUpdate,
    GramPropReturn,
    WordFormCreate,
    WordFormUpdate,
    WordFormReturn,
    DefinitionsRecord,
    DefinitionCreate,
    DefinitionUpdate,
    DefinitionReturn,
    ExampleCreate,
    ExampleUpdate,
    ExampleReturn,
    PronunciationCreate,
    PronunciationUpdate,
    PronunciationReturn,
    LemRelCreate,
    LemRelUpdate,
    LemRelReturn,
    LookupQueueCreate,
    LookupQueueUpdate,
    LookupQueueReturn,
    LemDefCreate,
    LemDefUpdate,
    LemDefReturn,
    DefExCreate,
    DefExUpdate,
    DefExReturn,
    ModuleCreate,
    ModuleUpdate,
    ModuleReturn,
    LessonListCreate,
    LessonListUpdate,
    LessonListReturn,
    LessListInModCreate,
    LessListInModUpdate,
    LessListInModReturn,
    LemInLessListCreate,
    LemInLessListUpdate,
    LemInLessListReturn,
    DefExamplesRecord,
    PronunciationsRecord,
    RelatedLemmaRecord,
    ProcessedPayload,
)
from alite_backend.words.funcs import remove_accents
from alite_backend.db.crud.crud_base import CRUDBase

logger = logging.getLogger(__name__)

# O
# H

# complete_props = {
#     # gram props
#     "gram_tense": None,
#     "irregular": None,
#     "gram_num": None,
#     "gram_gender": None,
#     "conj_person": None,
#     "verb_mood": None,
#     "subst_case": None,
#     "alt_adjv_type": None,
#     "alt_noun_type": None,
#     "part_type": None,
#     "part_voice": None,
# }


# def _map_lemma(lemma_record: LemmasRecord):
#     """_map_lemma _summary_

#     Args:
#         lemma_record (LemmasRecord): _description_

#     Returns:
#         _type_: _description_
#     """
#     mapped_lemma = Lemma(
#         entry_key=lemma_record.entry_key,
#         lem_text=lemma_record.lem_text,
#         lem_canon=lemma_record.lem_canon,
#         pos=lemma_record.pos,
#     )
#     return mapped_lemma


def ensure_params(*required_args):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # check positional args
            if any(arg is None for arg in args):
                raise ValueError("You must provide at least one argument.")
            # check specific names in kwargs
            for name in required_args:
                if kwargs.get(name) is None:
                    raise ValueError("Parameter '{name}' is required.")
            return func(*args, **kwargs)

        return wrapper

    return decorator


def at_least_one_of(*search_keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # check if any of the search_keys exist and are defined
            if not any(kwargs.get(key) is not None for key in search_keys):
                raise ValueError(
                    f"Function '{func.__name__}' requires at least one of "
                    f"{search_keys} to be defined to query the database."
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


#
# LEMMAS
#


class CRUDLemmas(CRUDBase[Lemma, LemmaCreate, LemmaUpdate]):

    def search(self, db: Session, params: LemmaSearchParams) -> list[Lemma]:
        # convert to dictionary (and drop instances of None)
        search_kwargs = params.model_dump(exclude_none=True)

        # base query
        query = db.query(self.model)

        # dyanmically chained filter() statements
        for key, value in search_kwargs.items():
            query = query.filter(getattr(self.model, key) == value)

        return query.all()


crud_lemma = CRUDLemmas(Lemma)

#
# LEXEMES
#


class CRUDLexicon(CRUDBase[Lexeme, LexemeCreate, LexemeUpdate]):
    pass


crud_lexicon = CRUDLexicon(Lexeme)

#
# GRAM_PROPS
#


class CRUDGramProps(CRUDBase[GramProp, GramPropCreate, GramPropUpdate]):
    pass


crud_gram_prop = CRUDGramProps(GramProp)

#
# WORD_FORMS
#


class CRUDWordForm(CRUDBase[WordForm, WordFormCreate, WordFormUpdate]):
    pass


crud_word_form = CRUDWordForm(WordForm)

#
# DEFINITIONS
#


class CRUDDefinition(CRUDBase[Definition, DefinitionCreate, DefinitionUpdate]):
    pass


crud_definition = CRUDDefinition(Definition)

#
# EXAMPLES
#


class CRUDExample(CRUDBase[Example, ExampleCreate, ExampleUpdate]):
    pass


crud_example = CRUDExample(Example)

#
# PRONUNCIATIONS
#


class CRUDPronunciation(
    CRUDBase[Pronunciation, PronunciationCreate, PronunciationUpdate]
):
    pass


crud_pronunciation = CRUDPronunciation(Pronunciation)


#
# LEMMA-LEMMA RELATIONSHIPS
#


class CRUDLemRel(CRUDBase[LemmaRelation, LemRelCreate, LemRelUpdate]):
    pass


crud_lem_rel = CRUDLemRel(LemmaRelation)

#
# LOOKUP QUEUE
#


class CRUDLookupQueue(CRUDBase[LookupQueue, LookupQueueCreate, LookupQueueReturn]):
    pass


crud_lookup_queue = CRUDLookupQueue(LookupQueue)


#
# LEMMA-DEFINITION RELATIONSHIPS
#


class CRUDLemDef(CRUDBase[LemmaDefinition, LemDefCreate, LemDefUpdate]):
    pass


crud_lem_def = CRUDLemDef(LemmaDefinition)


#
# DEFINITION-EXAMPLE RELATIONSHIPS
#


class CRUDDefEx(CRUDBase[DefinitionExample, DefExCreate, DefExUpdate]):
    pass


crud_def_ex = CRUDDefEx(DefinitionExample)


#
# MODULES
#


class CRUDModule(CRUDBase[Module, ModuleCreate, ModuleUpdate]):
    pass


crud_module = CRUDModule(Module)


#
# LESSONS & LISTS
#


class CRUDLessList(CRUDBase[LessonList, LessonListCreate, LessonListUpdate]):
    pass


crud_less_list = CRUDLessList(LessonList)


#
# LESSONS & LISTS IN MODULES
#


class CRUDLessListInMod(
    CRUDBase[LessonListInModule, LessListInModCreate, LessListInModUpdate]
):
    pass


crud_less_list_in_mod = CRUDLessListInMod(LessonListInModule)

#
# LEMMAS IN LESSONS & LISTS
#


class CRUDLemInLessList(
    CRUDBase[LemmaInLessonList, LemInLessListCreate, LemInLessListUpdate]
):
    pass


crud_lem_in_less_list = CRUDLemInLessList(LemmaInLessonList)

#
# C
#

# goc = get or create


# def goc_lemma(db: Session, lemma_record: LemmasRecord) -> Lemma | List[Lemma] | None:
#     """create_lemma _summary_

#     Args:
#         db (Session): _description_
#         lemma_record (LemmasRecord): _description_

#     Returns:
#         _type_: _description_
#     """
#     try:
#         entry_key, lem_text, lem_canon, pos = (
#             lemma_record.entry_key,
#             lemma_record.lem_text,
#             lemma_record.lem_canon,
#             lemma_record.pos,
#         )
#         existing_lem = get_lemmas(
#             db=db,
#             entry_key=entry_key,
#             lem_text=lem_text,
#             lem_canon=lem_canon,
#             pos=pos,
#         )
#         if existing_lem:
#             return existing_lem
#     except:
#         pass
#     else:
#         try:
#             sql_lemma = _map_lemma(lemma_record=lemma_record)
#             db.add(sql_lemma)
#             db.flush()
#             db.refresh(sql_lemma)

#             return sql_lemma

#         except IntegrityError as e:
#             db.rollback()
#             logger.exception(f"IntegrityError creating lemma: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="That lemma already exists",
#             )

#         except SQLAlchemyError as e:
#             db.rollback()
#             logger.exception(f"IntegrityError creating lemma: {str(e)}")
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="An unexpected database error occurred",
#             )


# def goc_lexeme(db: Session, word_form: str) -> Lexeme:
#     """
#     Creates a new lexeme entry and links it to its lemma.
#     """
#     lex_search_stmt = select(Lexeme).where(Lexeme.lex_text == word_form)
#     existing_lex = db.scalars(statement=lex_search_stmt).one_or_none()
#     # logging.debug("lexeme search_results: %s", search_results)
#     if existing_lex:
#         return existing_lex
#     else:
#         # logging.debug("making LexemRecord for %s", word_form)
#         db_lexeme = Lexeme(lex_text=word_form, lex_text_clean=remove_accents(word_form))
#         db.add(db_lexeme)
#         db.flush()
#         db.refresh(db_lexeme)
#         return db_lexeme


# def goc_gramprop(db: Session, incoming_props: dict) -> GramProp:
#     existing_gramprop = get_gramprop(db, incoming_props)
#     if existing_gramprop:
#         # logging.debug("This prop exists")
#         return existing_gramprop
#     else:
#         # logging.debug("This prop doesn't exist")
#         these_props = complete_props | incoming_props
#         new_gram_prop = GramProp(**these_props)
#         db.add(new_gram_prop)
#         db.flush()
#         db.refresh(new_gram_prop)
#         return new_gram_prop


# def goc_wordform(db: Session, form_ids: dict[str, int]) -> WordForm:
#     logging.debug("goc_wordform form_ids: %s", form_ids)
#     existing_wordform = get_wordform(db, **form_ids)
#     if existing_wordform:
#         logging.debug("This wordform exists")
#         return existing_wordform
#     else:
#         new_word_form = WordForm(**form_ids)
#         db.add(new_word_form)
#         db.flush()
#         db.refresh(new_word_form)
#         return new_word_form


# def goc_definition(db: Session, definitions: List[DefinitionsRecord]):
#     logging.debug("goc_definition definitions: %s", definitions)
#     # existing_definition = get_definitions(db, def_text=)

#     # return new_definition


# #
# # R
# #


# @at_least_one_of(
#     "id",
#     "entry_key",
#     "lem_text",
#     "lem_canon",
#     "pos",
#     "verb_aspect",
#     "verb_conj",
#     "verb_type",
#     "verb_trans_refl",
# )
# def get_lemmas(
#     db: Session,
#     id: Optional[int] = None,
#     entry_key: Optional[UUID] = None,
#     lem_text: Optional[str] = None,
#     lem_canon: Optional[str] = None,
#     pos: Optional[EnumPartOfSpeech] = None,
#     verb_aspect: Optional[EnumVerbAspect] = None,
#     verb_conj: Optional[str] = None,
#     verb_type: Optional[EnumVerbType] = None,
#     verb_trans_refl: Optional[EnumVerbTransRefl] = None,
# ) -> List[Lemma]:  # type: ignore
#     # base statement
#     stmt = select(Lemma)

#     # get immediately by entry_key or id
#     if entry_key is not None:
#         stmt = stmt.where(Lemma.entry_key == entry_key)
#         return db.scalars(statement=stmt).one_or_none()

#     if id is not None:
#         stmt = stmt.where(Lemma.id == id)
#         return db.scalars(statement=stmt).one_or_none()

#     # dynamic chaining for casting a wider net
#     if lem_text is not None:
#         stmt = stmt.where(Lemma.lem_text == lem_text)
#     if lem_canon is not None:
#         stmt = stmt.where(Lemma.lem_canon == lem_canon)
#     if pos is not None:
#         stmt = stmt.where(Lemma.pos == pos)
#     # logging.debug(stmt)
#     return list(db.scalars(statement=stmt).all())


# def get_lexemes(db: Session, lex_text: str) -> List[Lexeme]:
#     stmt = select(Lexeme).where(Lexeme.lex_text == lex_text)
#     return list(db.scalars(statement=stmt).all())


# def get_gramprop(db: Session, incoming_props: dict) -> GramProp:
#     # logging.debug("get_gramprop complete_props: %s", complete_props)
#     these_props = complete_props | incoming_props
#     # logging.debug("get_gramprop these_props: %s", these_props)
#     stmt = select(GramProp).filter_by(**these_props)
#     existing_gramprop = db.scalars(stmt).first()
#     return existing_gramprop


# def get_wordform(
#     db: Session, lem_id: int, lex_id: int, gram_id: int
# ) -> WordForm | None:
#     stmt = select(WordForm)

#     if lem_id is not None:
#         stmt = stmt.where(WordForm.lem_id == lem_id)
#     if lex_id is not None:
#         stmt = stmt.where(WordForm.lex_id == lex_id)
#     if gram_id is not None:
#         stmt = stmt.where(WordForm.gram_id == gram_id)

#     existing_wordform = db.scalars(stmt).first()

#     return existing_wordform


# # creating definitions, gram_props and linking them together in join tables


# @at_least_one_of("def_id", "def_text")
# def get_definitions(
#     db: Session, def_id: Optional[int], def_text: Optional[str]
# ) -> Definition | Sequence[Definition] | None:
#     stmt = select(Definition)

#     # search precisely by id
#     if def_id is not None:
#         stmt = stmt.where(Definition.id == def_id)
#         existing_definition = db.scalars(stmt).first()
#         if existing_definition:
#             return existing_definition

#     # search all by text contents


#
# U
#

#
# D
#
