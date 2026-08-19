from ast import Mod
from pydoc import Doc

from alite_backend.db.models import (
    Definition,
    DefinitionExample,
    Document,
    Example,
    Exercise,
    GramProp,
    Item,
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
from hypothesis import example
from sqladmin import ModelView


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

    # 3. Column Formatters:
    # Safely extract related attributes without triggering ad-hoc queries.
    column_formatters = {
        "lex_text": lambda model, attr: (
            model.word_form_lexicon.lex_text if model.word_form_lexicon else "—"
        )
    }


class DefinitionAdminView(ModelView, model=Definition):

    name = "Definition"
    name_plural = "Definitions"
    icon = "fa-solid" "fa-book"
    category = "Lemmas - Auxiliary"

    column_list = [Definition.id, Definition.def_text, Definition.def_tags]  # type: ignore
    column_sortable_list = [Definition.id, Definition.def_text, Definition.def_tags]  # type: ignore
    column_default_sort = [(Definition.id, False)]

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
    column_sortable_list = [Pronunciation.id, Pronunciation.pron_tags, Pronunciation.pron_text, Pronunciation.pron_type]  # type: ignore
    column_default_sort = [(Pronunciation.id, False)]

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

    column_list = [LessonList.id, LessonList.title, LessonList.topic, LessonList.owner_id]  # type: ignore
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

    column_list = [Sentence.id, Sentence.doc_id, Sentence.raw_text, Sentence.sent_idx]  # type: ignore
    column_searchable_list = [Sentence.raw_text]
    column_default_sort = [(Sentence.id, False)]
    page_size = 25


class SentenceTokenAdminView(ModelView, model=SentenceToken):
    """
    Administrative UI mapping for Corpus Sentence Tokens.
    """

    name = "Sentence Token"
    name_plural = "Sentence Tokens"
    icon = "fa-solid fa-align-left"
    category = "Sentences"

    column_list = [SentenceToken.id, SentenceToken.lex_raw, SentenceToken.lem_raw, SentenceToken.features, SentenceToken.head_idx, SentenceToken.dep_rel, SentenceToken.semantic_tag, SentenceToken.is_capitalized, SentenceToken.punctuation_before, SentenceToken.punctuation_after, SentenceToken.status, SentenceToken.lem_id, SentenceToken.lex_id, SentenceToken.wf_id]  # type: ignore
    column_searchable_list = [Sentence.raw_text]
    page_size = 25


class UserAdminView(ModelView, model=User):
    """
    Administrative UI mapping for User account records.
    """

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    category = "Users"

    # Explicitly list visible table columns to prevent exposing hashed passwords
    column_list = [User.id, User.username, User.email, User.user_role, User.created_at]  # type: ignore
    column_searchable_list = [User.username, User.email]  # type: ignore
    column_sortable_list = [User.user_role]

    # Exclude system-managed timestamps and sensitive security hashes from edit forms
    form_excluded_columns = [User.created_at, User.exercises, User.in_group]  # type: ignore


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
        Item.prompt,
    ]  # type: ignore
    column_sortable_list = [Item.item_type, Item.item_format]
    page_size = 50
