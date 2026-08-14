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
from sqladmin import ModelView


class LemmaAdminView(ModelView, model=Lemma):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Lemma"
    name_plural = "Lemmas"
    icon = "fa-solid fa-book"
    category = "Linguistics"

    column_list = [
        Lemma.id,
        Lemma.lem_text,
        Lemma.pos,
        Lemma.noun_gender,
        Lemma.verb_aspect,
    ]  # type: ignore
    column_searchable_list = [Lemma.lem_text, Lemma.lem_canon]  # type: ignore
    column_filters = [Lemma.pos, Lemma.verb_aspect, Lemma.noun_gender]

    # Default sorting alphabetical by lemma string
    column_default_sort = [(Lemma.lem_text, False)]
    page_size = 50


class LexemeAdminView(ModelView, model=Lexeme):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Lexeme"
    name_plural = "Lexicon"
    icon = "fa-solid fa-book"
    category = "Linguistics"

    column_list = [
        Lexeme.id,
        Lexeme.lex_text,
        Lexeme.lex_text_clean,
    ]  # type: ignore
    column_searchable_list = [Lexeme.lex_text, Lexeme.lex_text_clean]  # type: ignore
    column_filters = [Lexeme.lex_text]

    # Default sorting alphabetical by lemma string
    column_default_sort = [(Lexeme.lex_text, False)]
    page_size = 50


class WordFormAdminView(ModelView, model=WordForm):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Word Forms"
    name_plural = "Word Forms"
    icon = "fa-solid fa-book"
    category = "Linguistics"

    column_list = [
        WordForm.lem_id,
        WordForm.lex_id,
        WordForm.gram_id,
    ]  # type: ignore
    # column_searchable_list = [Lexeme.lex_text, Lexeme.lex_text_clean]  # type: ignore
    # column_filters = [Lexeme.lex_text]

    # Default sorting alphabetical by lemma string
    # column_default_sort = [(Lexeme.lex_text, False)]
    page_size = 50


class GramPropAdminView(ModelView, model=GramProp):
    """
    Administrative UI mapping for Dictionary Base Forms (Lemmas).
    """

    name = "Grammatical Properties"
    name_plural = "Gram Props"
    icon = "fa-solid fa-book"
    category = "Linguistics"

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
    column_filters = [
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
    column_default_sort = [(GramProp.irregular, True)]
    page_size = 50


class UserAdminView(ModelView, model=User):
    """
    Administrative UI mapping for User account records.
    """

    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    category = "Access Control"

    # Explicitly list visible table columns to prevent exposing hashed passwords
    column_list = [User.id, User.username, User.email, User.user_role, User.created_at]  # type: ignore
    column_searchable_list = [User.username, User.email]  # type: ignore
    column_filters = [User.user_role]

    # Exclude system-managed timestamps and sensitive security hashes from edit forms
    form_excluded_columns = [User.created_at, User.exercises, User.in_group]  # type: ignore


class SentenceAdminView(ModelView, model=Sentence):
    """
    Administrative UI mapping for Corpus Sentences.
    """

    name = "Sentence"
    name_plural = "Corpus Sentences"
    icon = "fa-solid fa-align-left"
    category = "Corpus Management"

    column_list = [Sentence.id, Sentence.doc_id, Sentence.raw_text, Sentence.sent_idx]  # type: ignore
    column_searchable_list = [Sentence.raw_text]
    page_size = 25


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
    column_filters = [Item.item_type, Item.item_format]
    page_size = 50
