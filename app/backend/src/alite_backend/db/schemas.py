# schemas.py
# pydantic models for API data validation and response shaping
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import UUID

from alite_backend.db.models import (
    EnumGramGender,
    EnumItemDifficulty,
    EnumItemFormat,
    EnumLookupStatus,
    EnumPartOfSpeech,
    EnumPronType,
    EnumRelLemType,
    EnumSentItemType,
    EnumSystemTheme,
    EnumTargetLanguage,
    EnumUserRole,
    EnumVerbAspect,
    EnumVerbTransRefl,
    EnumVerbType,
    EnumWordItemType,
)
from click import Option
from pydantic import (
    UUID4,
    UUID5,
    AliasChoices,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    HttpUrl,
    JsonValue,
    field_validator,
    model_validator,
)
from pyparsing import Opt

#
# --- Data Processing Schemas ---
#

# --- FDAPI models ---


# --- Component models for Entry ---
class Language(BaseModel):
    code: str
    name: str


class Pronunciation(BaseModel):
    type: Optional[str] = None
    text: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class Form(BaseModel):
    word: str
    tags: List[str] = Field(default_factory=list)


class Quote(BaseModel):
    text: str
    reference: Optional[str] = None


class Example(BaseModel):
    text: str


class Sense(BaseModel):
    definition: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str]  # The API sends a list of strings here.
    quotes: List[Quote] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    subsenses: List["Sense"] = Field(
        default_factory=list
    )  # Self-referencing for nested senses


# --- Main Entry Structure ---


class Entry(BaseModel):
    language: Language
    partOfSpeech: str
    pronunciations: List[Pronunciation] = Field(default_factory=list)
    forms: List[Form] = Field(default_factory=list)
    senses: List[Sense] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)


# --- Source and License Information ---


class License(BaseModel):
    name: str
    url: HttpUrl


class Source(BaseModel):
    url: HttpUrl
    license: License


# --- The Top-Level FDAPI Container Model ---


class FDAPIreturn(BaseModel):
    """
    The main Pydantic model to validate the entire API response
    for a single word.
    """

    word: str
    entries: List[Entry]
    source: Source


# --- Post-Processing Schemas ---
# These models define the clean, structured data


class LemmasRecord(BaseModel):
    """Schema for an entry in the Lemmas table."""

    lem_text: str
    lem_canon: Optional[str] = None
    pos: EnumPartOfSpeech
    entry_key: UUID5
    noun_gender: Optional[EnumGramGender]
    noun_animacy: Optional[bool]
    verb_aspect: Optional[EnumVerbAspect]
    verb_conj: Optional[str]
    verb_type: Optional[EnumVerbType]
    verb_trans_refl: Optional[EnumVerbTransRefl]


class GramPropsRecord(BaseModel):
    temp_form_id: UUID4
    prop_name: str


class LexiconRecord(BaseModel):
    """Schema for an entry in the Lexicon table."""

    temp_form_id: UUID4
    entry_key: UUID5
    lex_text: str


class DefinitionsRecord(BaseModel):
    """Schema for a single definition entry."""

    temp_def_id: UUID4
    entry_key: UUID5
    def_text: str
    def_tags: Optional[List[str]]


class DefExamplesRecord(BaseModel):
    """Schema for a single definition entry."""

    temp_def_id: UUID4
    ex_text: str


class PronunciationsRecord(BaseModel):
    """Schema for a single definition entry."""

    entry_key: UUID5
    pron_text: str
    pron_type: EnumPronType | None
    pron_tags: Optional[List[str]] = None


class RelatedLemmaRecord(BaseModel):
    """Schema for a single definition entry."""

    entry_key: UUID5
    rel_form: str
    rel_type: EnumRelLemType


class ProcessedPayload(BaseModel):
    """
    A container for the structured, processed data, ready for the Loader.
    This is the final output of the 'Processor' class.
    """

    lemmas: List[LemmasRecord]
    gram_props: List[GramPropsRecord]
    lexicon: List[LexiconRecord]
    definitions: List[DefinitionsRecord]
    def_examples: List[DefExamplesRecord]
    pronunciations: List[PronunciationsRecord]
    rel_lems: List[RelatedLemmaRecord]


#
# --- CRUD Schema ---
#

# Lemmas


# shared properties
class LemmaBase(BaseModel):
    lem_text: str
    lem_canon: Optional[str] = None
    pos: Optional[EnumPartOfSpeech] = None


# lemma shared grammar properties
class LemmaProps(BaseModel):
    pos: Optional[EnumPartOfSpeech] = None
    noun_gender: Optional[EnumGramGender] = None
    noun_animacy: Optional[bool] = None
    verb_aspect: Optional[EnumVerbAspect] = None
    verb_conj: Optional[str] = None
    verb_type: Optional[EnumVerbType] = None
    verb_trans_refl: Optional[EnumVerbTransRefl] = None


# properties to receive on creation
class LemmaCreate(LemmaBase, LemmaProps):
    entry_key: UUID5


# properties to receive on update
class LemmaUpdate(LemmaBase, LemmaProps):
    pass


# properties to return to the frontend (API response) for general use
class LemmaExerciseReturn(LemmaBase):
    id: int

    # read data even if it's not a dict
    model_config = ConfigDict(from_attributes=True)


# properties to return to the frontend for detailed view
class LemmaDetailsReturn(LemmaBase, LemmaProps):
    id: int
    created_at: datetime

    # read data even if it's not a dict
    model_config = ConfigDict(from_attributes=True)


# for pydantic validation of searches
class LemmaSearchParams(BaseModel):
    lem_text: Optional[str] = None
    lem_canon: Optional[str] = None
    pos: Optional[EnumPartOfSpeech] = None
    entry_key: Optional[UUID5] = None
    noun_gender: Optional[EnumGramGender] = None
    noun_animacy: Optional[bool] = None
    verb_aspect: Optional[EnumVerbAspect] = None
    verb_conj: Optional[str] = None
    verb_type: Optional[EnumVerbType] = None
    verb_trans_refl: Optional[EnumVerbTransRefl] = None

    @model_validator(mode="after")
    def check_at_least_one_param(self):
        # check if all are None
        if not self.model_dump(exclude_unset=True):
            raise ValueError("You must provide at least one search parameter.")
        return self


# Lexicon


# shared properties
class LexemeBase(BaseModel):
    lex_text: str


# create lexeme
class LexemeCreate(LexemeBase):
    lex_text_clean: str


class LexemeUpdate(LexemeBase):
    id: int


# lexeme return
class LexemeReturn(LexemeUpdate):
    created_at: datetime

    # read data even if it's not a dict
    model_config = ConfigDict(from_attributes=True)


# Gram Props


class GramPropBase(BaseModel):
    irregular: bool = False


class GramPropCreate(GramPropBase):
    gram_tense: Optional[str] = None
    gram_num: Optional[str] = None
    gram_gender: Optional[str] = None
    conj_person: Optional[str] = None
    verb_mood: Optional[str] = None
    subst_case: Optional[str] = None
    alt_adjv_type: Optional[str] = None
    alt_noun_type: Optional[str] = None
    part_type: Optional[str] = None
    part_voice: Optional[str] = None


class GramPropUpdate(GramPropBase):
    id: int


class GramPropReturn(GramPropCreate, GramPropUpdate):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Word Forms


class WordFormBase(BaseModel):
    pass


class WordFormCreate(WordFormBase):
    lem_id: int
    lex_id: int
    gram_id: int


class WordFormUpdate(WordFormBase):
    id: int


class WordFormReturn(WordFormCreate, WordFormUpdate):
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Definitions


class DefinitionBase(BaseModel):
    def_text: str


class DefinitionCreate(DefinitionBase):
    def_tags: Optional[List[str]]


class DefinitionUpdate(DefinitionBase):
    id: int


class DefinitionReturn(DefinitionUpdate):
    created_at: datetime


# Examples


class ExampleBase(BaseModel):
    ex_text: str


class ExampleCreate(ExampleBase):
    pass


class ExampleUpdate(ExampleBase):
    id: int


class ExampleReturn(ExampleUpdate):
    created_at: datetime


# Pronunciations


class PronunciationBase(BaseModel):
    pron_text: str
    pron_type: str


class PronunciationCreate(PronunciationBase):
    pron_tags: Optional[List[str]]


class PronunciationUpdate(PronunciationBase):
    id: int


class PronunciationReturn(PronunciationUpdate):
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Lemma Rels


class LemRelBase(BaseModel):
    target_id: int
    rel_type: EnumRelLemType
    source_id: int


class LemRelCreate(LemRelBase):
    pass


class LemRelUpdate(LemRelBase):
    id: int


class LemRelReturn(LemRelUpdate):
    created_at: datetime


# Lookup Queue


class LookupQueueBase(BaseModel):
    target_lem: str
    rel_type: EnumRelLemType
    source_id: int


class LookupQueueCreate(LookupQueueBase):
    pass


class LookupQueueUpdate(LookupQueueBase):
    id: int
    target_id: int
    status: EnumLookupStatus


class LookupQueueReturn(LookupQueueUpdate):
    created_at: datetime


# Lemma-Definition Relationships


class LemDefBase(BaseModel):
    lem_id: int
    def_id: int


class LemDefCreate(LemDefBase):
    pass


class LemDefUpdate(LemDefBase):
    id: int


class LemDefReturn(LemDefUpdate):
    created_at: datetime


# Definition-Example Relationships


class DefExBase(BaseModel):
    def_id: int
    ex_id: int


class DefExCreate(DefExBase):
    pass


class DefExUpdate(DefExBase):
    id: int


class DefExReturn(DefExUpdate):
    created_at: datetime


# Lemma-Pronunciation Relationships


class LemPronBase(BaseModel):
    lem_id: int
    pron_id: int


class LemPronCreate(LemPronBase):
    pass


class LemPronUpdate(LemPronBase):
    id: int


class LemPronReturn(LemPronUpdate):
    created_at: datetime


# Users


class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: EnumUserRole


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        description="Plain text password submitted on creation. Will be hashed before DB save.",
    )
    alias: Optional[str]


class UserUpdate(BaseModel):
    id: Optional[int]
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str] = Field(default=None, min_length=8)


class UserReturn(UserBase):
    id: int
    created_at: datetime
    alias: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class UserSettings(BaseModel):
    difficulty: EnumItemDifficulty
    theme: EnumSystemTheme
    reduce_motion: bool
    language: EnumTargetLanguage


# User Groups


class UserGroupBase(BaseModel):
    group_name: str


class UserGroupCreate(UserGroupBase):
    pass


class UserGroupUpdate(UserGroupBase):
    id: int


class UserGroupReturn(UserGroupUpdate):
    created_at: datetime


# Users in User Groups


class UserInGroupBase(BaseModel):
    user_id: int
    group_id: int


class UserInGroupCreate(UserInGroupBase):
    pass


class UserInGroupUpdate(UserInGroupBase):
    pass


class UserInGroupReturn(UserInGroupUpdate):
    created_at: datetime


# Modules


class ModuleBase(BaseModel):
    module_name: str


class ModuleCreate(ModuleBase):
    pass


class ModuleUpdate(ModuleBase):
    id: int


class ModuleReturn(ModuleUpdate):
    created_at: datetime


# Lessons & Word Lists


class LessonListBase(BaseModel):
    title: str
    topic: Optional[str]
    owner_id: Optional[int]


class LessonListCreate(LessonListBase):
    pass


class LessonListUpdate(LessonListBase):
    id: int


class LessonListReturn(LessonListUpdate):
    created_at: datetime
    has_lemma: List[LemmaExerciseReturn] = []
    model_config = ConfigDict(from_attributes=True)


# Lessons & Lists in Modules


class LessListInModsBase(BaseModel):
    mod_id: int
    less_list_id: int


class LessListInModCreate(LessListInModsBase):
    pass


class LessListInModUpdate(LessListInModsBase):
    id: int


class LessListInModReturn(LessListInModUpdate):
    created_at: datetime


# Lemmas in Lessons & Lists


class LemInLessListBase(BaseModel):
    lem_id: int
    less_list_id: int


class LemInLessListCreate(LemInLessListBase):
    pass


class LemInLessListUpdate(LemInLessListBase):
    id: int


class LemInLessListReturn(LemInLessListUpdate):
    created_at: datetime


# Documents


class DocumentBase(BaseModel):
    pass


class DocumentCreate(DocumentBase):
    title: str
    author: str
    source: str
    date: Any


class DocumentUpdate(DocumentBase):
    id: int


class DocumentReturn(DocumentCreate, DocumentUpdate):
    created_at: datetime


# Sentences


class SentenceBase(BaseModel):
    pass


class SentenceCreate(SentenceBase):
    doc_id: int
    raw_text: str
    sent_idx: int


class SentenceUpdate(SentenceBase):
    id: int


class SentenceReturn(SentenceCreate, SentenceUpdate):
    created_at: datetime


# Sentence Tokens


class SentenceTokenBase(BaseModel):
    """
    Base schema for sentence token attributes shared across requests and responses.
    """

    sent_id: int = Field(description="Foreign key referencing the parent sentence")
    token_idx: int = Field(description="0-indexed position of token in the sentence")
    lex_raw: str = Field(description="Surface string as it appears in source text")
    lem_raw: str = Field(description="Raw dictionary lemma string")

    features: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Morphological and syntactic feature map from NLP pipeline",
    )

    is_capitalized: bool = Field(
        default=False, description="Orthographic capitalization flag"
    )

    punctuation_before: Optional[str] = Field(
        default=None, description="Punctuation attached before the token word boundary"
    )
    punctuation_after: Optional[str] = Field(
        default=None, description="Punctuation attached after the token word boundary"
    )

    status: EnumLookupStatus = Field(
        default=EnumLookupStatus.UNLINKED,
        description="Lookup status against dictionary tables",
    )
    lem_id: Optional[int] = Field(
        default=None, description="Linked Lemma surrogate key"
    )
    lex_id: Optional[int] = Field(
        default=None, description="Linked Lexeme surrogate key"
    )
    wf_id: Optional[int] = Field(
        default=None, description="Linked WordForm surrogate key"
    )


class SentenceTokenCreate(SentenceTokenBase):
    """Schema for creating a new SentenceToken entry."""

    pass


class SentenceTokenUpdate(SentenceTokenBase):
    """Schema for updating an existing SentenceToken entry."""

    id: int


class SentenceTokenReturn(SentenceTokenBase):
    """
    Schema for API response serialization of sentence tokens.
    Inherits field definitions from SentenceTokenBase to maintain DRY principles.
    """

    id: int
    created_at: datetime

    # Pydantic V2 configuration for ORM/SQLModel attribute extraction
    model_config = ConfigDict(from_attributes=True)


# Exercise


class ExerciseBase(BaseModel):
    user_id: int


class ExerciseCreate(ExerciseBase):
    pass


class ExerciseUpdate(ExerciseBase):
    id: int


class ExerciseReturn(ExerciseUpdate):
    start_time: datetime
    finish_time: datetime
    created_at: datetime


# Items


class ItemBase(BaseModel):
    item_type: EnumWordItemType


class ItemCreate(ItemBase):
    prompt: str
    settings: JsonValue
    options: List[str]


class ItemUpdate(ItemBase):
    id: int


class ItemReturn(ItemUpdate):
    start_time: datetime
    finish_time: datetime
    created_at: datetime


# Item Options


class ItemOptionBase(BaseModel):
    option_text: str
    item_id: int
    is_correct: bool


class ItemOptionCreate(ItemOptionBase):
    option_uuid: UUID


class ItemOptionUpdate(ItemOptionCreate):
    id: int


class ItemOptionReturn(ItemOptionUpdate):
    start_time: datetime
    finish_time: datetime
    created_at: datetime


# Item Response


class ItemResponseBase(BaseModel):
    user_id: int
    item_id: int


class ItemResponseCreate(ItemResponseBase):
    pass


class ItemResponseUpdate(ItemResponseBase):
    student_answer: str
    is_correct: bool
    id: int


class ItemResponseReturn(ItemResponseUpdate):
    response_time_ms: int
    submitted_at: datetime


#
# --- Services Schema ---
#

# Exercises

# Exercise Requests


class ExerciseContext(BaseModel):
    # Side-A menu items
    lem_ids: Optional[List[int]]
    ex_formats: List[EnumItemFormat]
    difficulty: EnumItemDifficulty = EnumItemDifficulty.MEDIUM
    allow_odd_one_out: bool = False
    max_keys: int = 1
    max_distractors: int = 3


class EnumSubstGramExFocus(str, Enum):
    ALL = "all"
    SUBST_CASE = "subst_case"
    GRAM_GENDER = "gram_gender"
    GRAM_NUM = "gram_num"


class EnumVerbGramExFocus(str, Enum):
    ALL = "all"
    GRAM_TENSE = "gram_tense"
    VERB_PERSON = "verb_person"
    VERB_MOOD = "verb_mood"


class EnumPartGramExFocus(str, Enum):
    ALL = "all"
    PART_TYPE = "part_type"
    PART_VOICE = "part_voice"
    GRAM_TENSE = "gram_tense"


class EnumGramExFocus(str, Enum):
    ALL = "all"
    SUBST_CASE = "subst_case"
    SUBST_GENDER = "subst_gender"
    SUBST_NUM = "subst_num"
    VERB_TENSE = "verb_tense"
    VERB_PERSON = "verb_person"
    VERB_MOOD = "verb_mood"
    PART_TYPE = "part_type"
    PART_VOICE = "part_voice"
    PART_TENSE = "part_tense"


STRATEGY_FORMATS: Dict[EnumWordItemType | EnumSentItemType, Set[EnumItemFormat]] = {
    # words - lemmas
    EnumWordItemType.LEM_TO_POS: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.POS_TO_LEM: {
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.LEM_TO_DEF: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.DEF_TO_LEM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.LEM_TO_PRON: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.PRON_TO_LEM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.LEM_LEM_TO_REL: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.REL_TO_LEM_LEM: {
        EnumItemFormat.MCQ,
    },
    # words - adjectives
    EnumWordItemType.ADJV_FORM_TO_TYPE: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.ADJV_TYPE_TO_LEM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.ADJV_FORM_TO_GRAM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.ADJV_GRAM_TO_FORM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    # words - nouns
    EnumWordItemType.NOUN_TO_GEND: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.GEND_TO_NOUN: {
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.NOUN_TO_ANIM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.ANIM_TO_NOUN: {
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.NOUN_FORM_TO_GRAM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.NOUN_GRAM_TO_FORM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.NOUN_TO_DMIN_FORM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    # words - participles
    EnumWordItemType.PART_FORM_TO_TYPE: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.PART_TYPE_TO_FORM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    # words - verbs
    EnumWordItemType.VERB_TO_ASPT: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.ASPT_TO_VERB: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.VERB_PAIR_TO_REL: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.VERB_TO_ASPT_PAIR: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.VERB_TO_TYPE: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.TYPE_TO_VERB: {
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.VERB_TO_TNRF: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.TNRF_TO_VERB: {
        EnumItemFormat.MCQ,
    },
    EnumWordItemType.VERB_TO_CONJ_FORM: {
        EnumItemFormat.FLASHCARD,
        EnumItemFormat.FITB,
        EnumItemFormat.MCQ,
    },
    # sentences
}


class LemmaSearchResults(BaseModel):
    id: int
    lem_text: str
    lem_canon: Optional[str] = None
    pos: Optional[str] = None
    noun_gender: Optional[Any] = None
    noun_animacy: Optional[Any] = None
    verb_aspect: Optional[Any] = None

    pronunciations: List[PronunciationReturn] = []

    definitions: List[DefinitionReturn] = Field(
        default=[], validation_alias=AliasChoices("definitions", "lem_defs")
    )
    model_config = ConfigDict(from_attributes=True)

    @field_validator("pronunciations", mode="before")
    @classmethod
    def extract_pronunciations(cls, raw_list: Any) -> list[Any]:
        """
        Intercepts the association table collection (LemmaPronunciation) and pulls
        the attached Pronunciation model prior to schema validation.
        """
        if not raw_list:
            return []

        resolved: list[Any] = []
        for entry in raw_list:
            # Case 1: Raw dictionary or direct Pronunciation instance
            if isinstance(entry, dict) or hasattr(entry, "pron_text"):
                resolved.append(entry)
            # Case 2: LemmaPronunciation association instance
            elif hasattr(entry, "pronunciation") and entry.pronunciation is not None:
                resolved.append(entry.pronunciation)
            elif hasattr(entry, "pron") and entry.pron is not None:
                resolved.append(entry.pron)

        return resolved

    @field_validator("definitions", mode="before")
    @classmethod
    def extract_definitions(cls, raw_collection: Any) -> list[Any]:
        """
        Unpacks target Definition instances from LemmaDefinition association rows,
        preventing missing-field ResponseValidationErrors.
        """
        if not raw_collection:
            return []
        resolved = []
        for item in raw_collection:
            # Direct model or dictionary
            if isinstance(item, dict) or hasattr(item, "def_text"):
                resolved.append(item)
            # Association row instance (e.g., LemmaDefinition.definition)
            elif hasattr(item, "definition") and item.definition is not None:
                resolved.append(item.definition)
            elif hasattr(item, "def_") and item.def_ is not None:
                resolved.append(item.def_)
        return resolved


class StrategyConfigs(BaseModel):
    # use optional attributes mapped directly to core strategy enums
    strategies: dict[
        str,
        List[EnumGramExFocus],
    ]


class ExerciseRequest(BaseModel):
    # Side-A + Side-B items = request
    exercise_context: ExerciseContext
    grammar_focus: Optional[StrategyConfigs] = None
    type_counts: dict[Union[EnumWordItemType, EnumSentItemType], int]


# sentence token requests


class SentenceTokenContext(BaseModel):
    """
    Internal schema representing a single token from the `sentence_tokens` table.
    Retains full grammatical and syntactic truth for generation and grading.
    Never sent directly to the client for masked/interactive items.
    """

    tok_idx: int = Field(
        ..., description="1-based index of the token within the sentence"
    )
    lex_raw: str = Field(..., description="Exact wordform as it appears in the text")
    lem_raw: str = Field(..., description="Dictionary lemma form")
    pos: Optional[str] = Field(None, description="Part of speech tag")
    feats: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Morphological features (case, number, tense, etc.)",
    )
    head_idx: Optional[int] = Field(
        None, description="tok_idx of the syntactic governor"
    )
    dep_rel: Optional[str] = Field(
        None, description="Syntactic dependency relation tag (e.g. предик, квазиагент)"
    )


class DisplayToken(BaseModel):
    """
    Client-safe token model for rendering interactive sentences.
    Allows frontend click-to-select, highlighting, and accessible blank rendering.
    """

    tok_idx: int = Field(..., description="Position index for UI layout")
    text: str = Field(
        ..., description="Display text (masked with placeholder if target)"
    )
    is_masked: bool = Field(
        False, description="Indicates whether this token represents an input blank"
    )
    is_punctuation: bool = Field(
        False, description="Helps frontend format spacing without leading spaces"
    )


class UnscrambleToken(BaseModel):
    """
    Client-safe token specifically for unscramble exercises.
    Uses an ephemeral, non-sequential handle to prevent students from inspecting
    the network payload or DOM to discover the correct word sequence.
    """

    token_handle: str = Field(
        default_factory=lambda: uuid4().hex[:8],
        description="Opaque unique identifier for client drag-and-drop state",
    )
    text: str = Field(
        ..., description="The word or punctuation fragment to display on the chip"
    )


# Raw Exercise Responses


class SentenceBlueprintContext(BaseModel):
    """
    Encapsulates sentence-specific metadata within an ItemBlueprint.
    Keeps the root ItemBlueprint clean while providing sentence generators
    with complete context for distractor validation and backend grading.
    """

    doc_id: Optional[int] = Field(None, description="Parent document ID")
    sent_id: int = Field(..., description="Sentence database ID")
    full_sentence: str = Field(..., description="Unmodified original sentence text")
    tokens: list[SentenceTokenContext] = Field(
        ..., description="Ordered raw tokens from the database"
    )
    target_token_indices: list[int] = Field(
        default_factory=list,
        description="Indices (tok_idx) of tokens targeted for blanking, MCQ options, or syntax labeling",
    )
    syntactic_focus: Optional[str] = Field(
        None,
        description="Target dependency relation or grammar quality (e.g., 'предик', 'Aspect=Perf')",
    )


class ItemBlueprint(BaseModel):
    prompt: str
    keys: str | List[str]
    distractors: Optional[List[str]] = None
    lem_id: Optional[int] = None
    sentence_context: Optional[SentenceBlueprintContext] = None


class ItemFormatBlueprints(BaseModel):
    item_format: EnumItemFormat
    item_bp: ItemBlueprint


# Processed Exercise Responses


class FlashcardResponse(BaseModel):
    item_format: EnumItemFormat = EnumItemFormat.FLASHCARD
    item_id: int
    prompt: str
    back_text: str


class MultipleChoiceResponse(BaseModel):
    item_format: EnumItemFormat = EnumItemFormat.MCQ
    item_id: int
    prompt: str
    options: List[str | int]
    sentence_tokens: Optional[list[DisplayToken]] = None


class FillInTheBlankResponse(BaseModel):
    item_format: EnumItemFormat = EnumItemFormat.FITB
    item_id: int
    prompt: str
    parts: list[str] = Field(
        default_factory=list,
        description="Text fragments surrounding blanks: ['Она читает ', ' в парке.']",
    )
    sentence_tokens: Optional[list[DisplayToken]] = None


class UnscrambleResponse(BaseModel):
    """
    Client deliverable for sentence unscrambling items.
    Tokens are scrambled using a seeded or verified permutation that ensures
    they do not match the original sequence. Keys and correct ordering are omitted.
    """

    item_format: EnumItemFormat = EnumItemFormat.UNSCRAMBLE
    item_id: int
    prompt: str = Field(
        "Расставьте слова в правильном порядке:", description="Instructional prompt"
    )
    shuffled_tokens: list[UnscrambleToken] = Field(
        ..., description="Permuted tokens with opaque identifiers for UI drag-and-drop"
    )


ExerciseItems = Union[
    FlashcardResponse,
    MultipleChoiceResponse,
    FillInTheBlankResponse,
    UnscrambleResponse,
]


class ExerciseResponse(BaseModel):
    exercise_id: int
    num_questions: int
    response_data: list[ExerciseItems]


# User Item Response & Result


class AnswerSubmission(BaseModel):
    item_id: int
    response: str
    response_time_ms: int
    attempt_num: int
    is_final_attempt: bool = False


class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
