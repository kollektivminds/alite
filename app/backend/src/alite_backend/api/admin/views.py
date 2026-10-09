from ast import Mod
from datetime import datetime
from pydoc import Doc
from tracemalloc import start
from typing import Any

from alite_backend.api.admin.formatters import (
    format_document_link,
    format_document_title,
    format_lemma_label,
    format_lemma_link,
    format_lexeme_label,
    format_lexeme_link,
    format_sentence_tokens,
    format_word_form_label,
    format_word_form_link,
)
from alite_backend.db.models import (
    Definition,
    DefinitionExample,
    Document,
    Example,
    Exercise,
    GramProp,
    Item,
    ItemOption,
    ItemResponse,
    Lemma,
    LemmaDefinition,
    LemmaPronunciation,
    LemmaRelation,
    LessonList,
    Lexeme,
    LookupQueue,
    Module,
    Pronunciation,
    Sentence,
    SentenceToken,
    User,
    UserGroup,
    UserInGroup,
    WordForm,
)
from alite_backend.services import exercise_router
from hypothesis import example
from markupsafe import Markup
from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request
from tomlkit import date, item


def calc_duration(view: Any, context: Any, model: Any, name: Any):

    start_time = getattr(model, "start_time", None)
    finish_time = getattr(model, "finish_time", None)

    if not start_time or not finish_time:
        return "-"

    if isinstance(start_time, datetime) and isinstance(finish_time, datetime):
        return finish_time - start_time

    if isinstance(start_time, str) and isinstance(finish_time, str):
        start_time = datetime.fromisoformat(start_time)
        finish_time = datetime.fromisoformat(finish_time)
        return finish_time - start_time


class LemmaAdminView(ModelView, model=Lemma):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Lemma"
    name_plural = "Lemmas"
    icon = "fa-solid fa-book"
    category = "Lemmas"

    column_list = [
        Lemma.id,  # type: ignore
        Lemma.lem_text,
        Lemma.pos,
    ]  # type: ignore
    column_searchable_list = [Lemma.lem_text, Lemma.lem_canon]  # type: ignore
    column_sortable_list = [Lemma.id, Lemma.pos, Lemma.verb_aspect]  # type: ignore

    # Default sorting alphabetical by lemma string
    column_default_sort = [(Lemma.id, False)]
    page_size = 50


class LexemeAdminView(ModelView, model=Lexeme):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Lexeme"
    name_plural = "Lexicon"
    icon = "fa-solid fa-book"
    category = "Lemmas - Morphological"

    column_list = [
        Lexeme.id,  # type: ignore
        Lexeme.lex_text,
        Lexeme.lex_text_clean,
    ]  # type: ignore
    column_searchable_list = [Lexeme.lex_text, Lexeme.lex_text_clean]  # type: ignore
    column_sortable_list = [Lexeme.id, Lexeme.lex_text_clean]  # type: ignore
    column_default_sort = [(Lexeme.id, False)]

    page_size = 50


class GramPropAdminView(ModelView, model=GramProp):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Grammatical Properties"
    name_plural = "Gram Props"
    icon = "fa-solid fa-book"
    category = "Lemmas - Morphological"

    column_list = [
        GramProp.id,
        GramProp.irregular,
        GramProp.gram_tense,
        GramProp.gram_num,
        GramProp.gram_gender,
        GramProp.conj_person,
        GramProp.verb_mood,
        GramProp.subst_case,
        GramProp.alt_adjv_type,
        GramProp.alt_noun_type,
        GramProp.part_type,
        GramProp.part_voice,
        GramProp.gram_word_form,
    ]  # type: ignore
    column_searchable_list = [
        GramProp.gram_tense,
        GramProp.gram_num,
        GramProp.gram_gender,
        GramProp.conj_person,
        GramProp.verb_mood,
        GramProp.subst_case,
        GramProp.alt_adjv_type,
        GramProp.alt_noun_type,
        GramProp.part_type,
        GramProp.part_voice,
    ]  # type: ignore
    column_sortable_list = [  # type: ignore
        GramProp.irregular,
        GramProp.gram_tense,
        GramProp.gram_num,
        GramProp.gram_gender,
        GramProp.conj_person,
        GramProp.verb_mood,
        GramProp.subst_case,
        GramProp.alt_adjv_type,
        GramProp.alt_noun_type,
        GramProp.part_type,
        GramProp.part_voice,
    ]
    # Default sorting alphabetical by lemma string
    column_default_sort = [(GramProp.id, False), (GramProp.irregular, True)]
    # column_formatters = {GramProp.gram_word_form: format_gram_prop}
    page_size = 50


class WordFormAdminView(ModelView, model=WordForm):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Word Forms"
    name_plural = "Word Forms"
    icon = "fa-solid fa-book"
    category = "Lemmas - Morphological"

    column_list = [
        WordForm.lem_id,
        WordForm.word_form_lemma,
        WordForm.lex_id,
        WordForm.word_form_lexicon,
        "lex_text",
        WordForm.gram_id,
        WordForm.word_form_gram,
    ]  # type: ignore
    # column_searchable_list = [Lexeme.lex_text, Lexeme.lex_text_clean]  # type: ignore
    column_sortable_list = [
        WordForm.lem_id,
        WordForm.lex_id,
        WordForm.gram_id,
    ]  # type: ignore
    # default sorting alphabetical by lemma string
    column_default_sort = [(WordForm.id, False)]

    page_size = 50

    # column_select_related_list = [
    #     WordForm.word_form_lexicon,
    # ]

    # Safely extract related attributes without triggering ad-hoc queries.
    # column_formatters = {
    #     "lex_text": lambda model, attr: (
    #         model.word_form_lexicon.lex_text if model.word_form_lexicon else "—"
    #     ),
    #     WordForm.lem_id: format_lemma_link,
    #     WordForm.lex_id: format_lexeme_link,
    #     # WordForm.gram_id: format_gram_prop_link,
    # }


class DefinitionAdminView(ModelView, model=Definition):

    name = "Definition"
    name_plural = "Definitions"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [Definition.id, Definition.def_text, Definition.def_tags, Definition.lemmas, Definition.example]  # type: ignore
    column_sortable_list = [Definition.id, Definition.def_text, Definition.def_tags]  # type: ignore
    column_searchable_list = [Definition.def_text]
    column_default_sort = [(Definition.id, False)]

    # column_formatters = {Definition.lemmas: format_lemma_link}

    page_size = 50


class LemmaDefinitionAdminView(ModelView, model=LemmaDefinition):

    name = "Lemma-Definition"
    name_plural = "Lemma-Definitions"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [LemmaDefinition.lemma, LemmaDefinition.definition]  # type: ignore
    # column_sortable_list = [Definition.id, Definition.def_text, Definition.def_tags]  # type: ignore
    # column_searchable_list = [Definition.def_text]
    # column_default_sort = [(LemmaDefinition.lem_id, False)]

    page_size = 50


class ExampleAdminView(ModelView, model=Example):

    name = "Example"
    name_plural = "Examples"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [Example.id, Example.ex_text]  # type: ignore
    column_sortable_list = [Example.id, Example.ex_text]  # type: ignore
    column_default_sort = [(Example.id, False)]

    page_size = 50


class PronunciationAdminView(ModelView, model=Pronunciation):

    name = "Pronunciation"
    name_plural = "Pronunciations"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [Pronunciation.id, Pronunciation.pron_tags, Pronunciation.pron_text, Pronunciation.pron_type]  # type: ignore
    column_searchable_list = [Pronunciation.pron_text]
    column_sortable_list = [Pronunciation.id, Pronunciation.pron_tags, Pronunciation.pron_text, Pronunciation.pron_type]  # type: ignore
    column_default_sort = [(Pronunciation.id, False)]

    page_size = 50


class LemmaPronunciationAdminView(ModelView, model=LemmaPronunciation):

    name = "Lemma-Pronunciation"
    name_plural = "Lemma-Pronunciations"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [LemmaPronunciation.lem_id, LemmaPronunciation.lemma, LemmaPronunciation.pron_id, LemmaPronunciation.pronunciation]  # type: ignore
    column_searchable_list = [LemmaPronunciation.pronunciation]  # type: ignore
    column_sortable_list = [LemmaPronunciation.lem_id, LemmaPronunciation.pron_id]  # type: ignore
    column_default_sort = [(LemmaPronunciation.lem_id, False)]

    # column_formatters = {LemmaPronunciation.lemma: format_lemma_link}

    page_size = 50


class LemmaRelationAdminView(ModelView, model=LemmaRelation):

    name = "Lemma Relation"
    name_plural = "Lemma Relations"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [LemmaRelation.id, LemmaRelation.rel_type, LemmaRelation.source_lemma, LemmaRelation.target_lemma]  # type: ignore
    column_sortable_list = [LemmaRelation.id, LemmaRelation.rel_type, LemmaRelation.source_lemma, LemmaRelation.target_lemma]  # type: ignore
    column_default_sort = [(LemmaRelation.id, False)]

    page_size = 50


class LookupQueueAdminView(ModelView, model=LookupQueue):

    name = "Lookup Queue"
    name_plural = "Lookup Queue"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [LookupQueue.id, LookupQueue.rel_type, LookupQueue.source_id, LookupQueue.target_lem, LookupQueue.status]  # type: ignore
    column_sortable_list = [LookupQueue.id, LookupQueue.rel_type, LookupQueue.source_id, LookupQueue.target_lem, LookupQueue.status]  # type: ignore
    column_default_sort = [(LookupQueue.id, False)]

    page_size = 50


class ModuleAdminView(ModelView, model=Module):

    name = "Module"
    name_plural = "Modules"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Organization"

    column_list = [Module.id, Module.module_name]  # type: ignore
    column_sortable_list = [Module.id, Module.module_name]  # type: ignore
    column_default_sort = [(Module.id, False)]
    page_size = 50


class LessListAdminView(ModelView, model=LessonList):

    name = "LessonList"
    name_plural = "Lessons / Lists"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Organization"

    column_list = [LessonList.id, LessonList.title, LessonList.topic, LessonList.owner_id, LessonList.has_lemma]  # type: ignore
    column_sortable_list = [LessonList.id, LessonList.title, LessonList.topic, LessonList.owner_id]  # type: ignore
    column_default_sort = [(LessonList.id, False)]
    page_size = 50


class DocumentAdminView(ModelView, model=Document):
    """
    Administrative UI mapping for Corpus Documents.
    """

    name = "Document"
    name_plural = "Documents"
    icon = "fa-solid fa-align-left"
    category = "Sentences"

    column_list = [Document.id, Document.title, Document.author, Document.source, Document.date]  # type: ignore
    column_searchable_list = [
        Document.title,
        Document.author,
        Document.source,
        Document.date,
    ]  # type: ignore
    column_default_sort = [(Document.id, False)]
    page_size = 25


class SentenceAdminView(ModelView, model=Sentence):
    """
    Administrative UI mapping for Corpus Sentences.
    """

    name = "Sentence"
    name_plural = "Corpus Sentences"
    icon = "fa-solid fa-align-left"
    category = "Sentences"

    column_list = [Sentence.id, Sentence.doc_id, Sentence.raw_text, Sentence.sent_idx, Sentence.tokens]  # type: ignore
    column_searchable_list = [Sentence.raw_text]
    column_default_sort = [(Sentence.id, False)]

    column_formatters = {
        Sentence.doc_id: format_document_link,
    }
    column_formatters_detail = column_formatters

    def list_query(self, request: Request):
        return (
            select(Sentence)
            .options(
                selectinload(Sentence.document),
                selectinload(Sentence.tokens),
            )
            .order_by(Sentence.id.desc())
        )

    page_size = 25


class SentenceTokenAdminView(ModelView, model=SentenceToken):
    name = "Sentence Token"
    name_plural = "Sentence Tokens"
    icon = "fa-solid fa-align-left"
    category = "Sentences"

    column_list = [
        SentenceToken.id,
        SentenceToken.sentence,
        SentenceToken.lex_raw,
        SentenceToken.lem_raw,
        SentenceToken.word_form,
        SentenceToken.features,
        SentenceToken.head_idx,
        SentenceToken.dep_rel,
        SentenceToken.semantic_tag,
        SentenceToken.is_capitalized,
        SentenceToken.punctuation_before,
        SentenceToken.punctuation_after,
        SentenceToken.status,
        SentenceToken.lemma,
        SentenceToken.lexeme,
    ]

    column_select_related_list = [
        SentenceToken.lemma,
        SentenceToken.lexeme,
        SentenceToken.word_form,
    ]

    column_formatters = {
        SentenceToken.wf_id: format_word_form_label,
        SentenceToken.word_form: format_word_form_label,
        SentenceToken.lem_id: format_lemma_label,
        SentenceToken.lemma: format_lemma_label,
        SentenceToken.lex_id: format_lexeme_label,
        SentenceToken.lexeme: format_lexeme_label,
    }
    column_formatters_detail = column_formatters

    def list_query(self, request: Request):
        return (
            select(SentenceToken)
            .options(
                selectinload(SentenceToken.lemma),
                selectinload(SentenceToken.lexeme),
                selectinload(SentenceToken.sentence),
                selectinload(SentenceToken.word_form).selectinload(
                    WordForm.word_form_lexicon
                ),
                selectinload(SentenceToken.word_form).selectinload(
                    WordForm.word_form_lemma
                ),
            )
            .order_by(SentenceToken.id.desc())
        )


class UserAdminView(ModelView, model=User):
    """
    Administrative UI mapping for User account records.
    """

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    category = "Users"

    # Explicitly list visible table columns to prevent exposing hashed passwords
    column_list = [User.id, User.username, User.alias, User.email, User.role, User.settings, User.created_at]  # type: ignore
    column_searchable_list = [User.username, User.email]  # type: ignore
    column_sortable_list = [User.role]

    # Exclude system-managed timestamps and sensitive security hashes from edit forms
    form_excluded_columns = [User.created_at, User.exercises, User.in_group]  # type: ignore


class ExerciseAdminView(ModelView, model=Exercise):
    """
    Administrative UI mapping for Generated Exercise Test Items.
    """

    name = "Exercise"
    name_plural = "Exercises"
    icon = "fa-solid fa-puzzle-piece"
    category = "Assessment"

    column_list = [Exercise.id, Exercise.user_id, "duration", Exercise.start_time, Exercise.finish_time, Exercise.has_item]  # type: ignore
    column_details_list = [Exercise.id, Exercise.user_id, "duration", Exercise.start_time, Exercise.finish_time, Exercise.has_item]  # type: ignore
    column_sortable_list = [
        Exercise.id,
        Exercise.user_id,
        "duration",
        Exercise.start_time,
        Exercise.finish_time,
    ]  # type: ignore

    column_searchable_list = []
    page_size = 50


class ItemAdminView(ModelView, model=Item):
    """
    Administrative UI mapping for Generated Exercise Test Items.
    """

    name = "Exercise Item"
    name_plural = "Exercise Items"
    icon = "fa-solid fa-puzzle-piece"
    category = "Assessment"

    column_list = [
        Item.id,
        Item.ex_id,
        Item.item_type,
        Item.item_format,
        "duration",
        Item.prompt,
        Item.options,
        Item.responses,
        Item.settings,
        Item.start_time,
        Item.finish_time,
        Item.ref_lems,
    ]  # type: ignore
    column_details_list = [
        Item.id,
        Item.ex_id,
        Item.item_type,
        Item.item_format,
        "duration",
        Item.prompt,
        Item.options,
        Item.responses,
        Item.settings,
        Item.start_time,
        Item.finish_time,
        Item.ref_lems,
    ]  # type: ignore
    column_sortable_list = [
        Item.id,
        Item.item_type,
        Item.item_format,
        "duration",
        Item.start_time,
        Item.finish_time,
    ]  # type: ignore
    column_searchable_list = [Item.item_type, Item.item_format, Item.prompt]  # type: ignore
    page_size = 50


class ItemOptionAdminView(ModelView, model=ItemOption):
    """
    Administrative UI mapping for Generated Exercise Test Items.
    """

    name = "Exercise Item Option"
    name_plural = "Exercise Item Options"
    icon = "fa-solid fa-puzzle-piece"
    category = "Assessment"

    column_list = [
        ItemOption.option_text,
        ItemOption.option_uuid,
        ItemOption.item_id,
        ItemOption.is_correct,
        ItemOption.explanation,
    ]  # type: ignore
    column_sortable_list = [ItemOption.item_id, ItemOption.is_correct]  # type: ignore
    column_searchable_list = [ItemOption.option_text, ItemOption.explanation]  # type: ignore
    page_size = 50


class ItemResponseAdminView(ModelView, model=ItemResponse):
    """
    Administrative UI mapping for Generated Exercise Test Items.
    """

    name = "Exercise Item Response"
    name_plural = "Exercise Item Responses"
    icon = "fa-solid fa-puzzle-piece"
    category = "Assessment"

    column_list = [
        ItemResponse.item_id,
        ItemResponse.response,
        ItemResponse.is_correct,
        ItemResponse.response_time_ms,
        ItemResponse.attempt_num,
    ]  # type: ignore
    column_sortable_list = [ItemResponse.item_id]  # type: ignore
    column_searchable_list = [ItemResponse.item_id, ItemResponse.response]  # type: ignore
    page_size = 50
