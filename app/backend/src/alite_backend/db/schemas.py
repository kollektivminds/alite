# schemas.py
# pydantic models for API data validation and response shaping
import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set, Union
from uuid import UUID, uuid4

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

AnyItemType = Union[EnumWordItemType, EnumSentItemType]

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


STRATEGY_FORMATS: Dict[AnyItemType, FrozenSet[EnumItemFormat]] = {
    # words - lemmas
    EnumWordItemType.LEM_TO_POS: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.POS_TO_LEM: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_TO_DEF: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.DEF_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_TO_PRON: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.PRON_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_LEM_TO_REL: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.REL_TO_LEM_LEM: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    # words - adjectives
    EnumWordItemType.ADJV_FORM_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_TYPE_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # words - nouns
    EnumWordItemType.NOUN_TO_GEND: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.GEND_TO_NOUN: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_TO_ANIM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ANIM_TO_NOUN: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_TO_DMIN_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # words - participles
    EnumWordItemType.PART_FORM_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.PART_TYPE_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # words - verbs
    EnumWordItemType.VERB_TO_ASPT: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ASPT_TO_VERB: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_PAIR_TO_REL: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_ASPT_PAIR: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.TYPE_TO_VERB: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_TNRF: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.TNRF_TO_VERB: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # sentences
    EnumSentItemType.NOUN_MORPH: frozenset({EnumItemFormat.FITB, EnumItemFormat.MCQ}),
    EnumSentItemType.VERB_MORPH: frozenset({EnumItemFormat.FITB, EnumItemFormat.MCQ}),
    EnumSentItemType.ADJECTIVE_MORPH: frozenset(
        {EnumItemFormat.FITB, EnumItemFormat.MCQ}
    ),
    EnumSentItemType.LEXICAL: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.DEP_REL: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.FIND_HEAD: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.FIND_SUBJECT: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.NOUN_CASE: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.VERB_ASPECT: frozenset({EnumItemFormat.MCQ}),
    EnumSentItemType.UNSCRAMBLE: frozenset({EnumItemFormat.UNSCRAMBLE}),
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


# class ExerciseRequest(BaseModel):
#     # Side-A + Side-B items = request
#     exercise_context: ExerciseContext
#     grammar_focus: Optional[StrategyConfigs] = None
#     type_counts: dict[AnyItemType, int]


def resolve_strategy_identifier(key: Any) -> Optional[AnyItemType]:
    """
    Polymorphic strategy identifier resolver.

    Guarantees consistent resolution whether the caller provides:
    1. An already-materialized EnumWordItemType or EnumSentItemType instance.
    2. An uppercase member identifier ('VERB_MORPH', 'NOUN_CASE').
    3. A lowercase column value ('verb_morph', 'noun_case').

    Returns None if the key does not map to any recognized strategy domain.
    """
    # 1. Identity return if already an enum member
    if isinstance(key, (EnumWordItemType, EnumSentItemType)):
        return key

    if not isinstance(key, str):
        return None

    clean = key.strip()

    # 2. Fast-path lookup by Enum member name (case-insensitive)
    clean_upper = clean.upper()
    if clean_upper in EnumWordItemType.__members__:
        return EnumWordItemType[clean_upper]
    if clean_upper in EnumSentItemType.__members__:
        return EnumSentItemType[clean_upper]

    # 3. Fallback lookup by Enum value (case-insensitive)
    try:
        return EnumWordItemType(clean)
    except ValueError:
        pass

    try:
        return EnumSentItemType(clean)
    except ValueError:
        pass

    return None


class ExerciseRequest(BaseModel):
    """
    Inbound payload initiating exercise session item generation.
    Validates cross-field compatibility between requested strategies and formats.
    """

    exercise_context: ExerciseContext
    grammar_focus: Optional[StrategyConfigs] = None
    type_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Map of Strategy Identifier -> Requested Item Count",
    )

    @model_validator(mode="after")
    def validate_strategy_format_compatibility(self) -> "ExerciseRequest":
        """
        Validates strategy compatibility against enabled session formats.
        Uses resolve_strategy_identifier to accept both uppercase and lowercase keys.
        """
        session_formats: Set[EnumItemFormat] = set(self.exercise_context.ex_formats)
        if not session_formats:
            raise ValueError(
                "At least one session format (MCQ, FITB, etc.) must be enabled."
            )

        allocated_counts = {
            strat_key: count
            for strat_key, count in self.type_counts.items()
            if count > 0
        }

        if not allocated_counts:
            raise ValueError(
                "At least one strategy must have an allocated item count > 0."
            )

        incompatible_errors: List[str] = []

        for strat_key, count in allocated_counts.items():
            # Polymorphic resolution: handles 'VERB_MORPH' and 'verb_morph' cleanly
            target_strategy = resolve_strategy_identifier(strat_key)

            if target_strategy is None:
                incompatible_errors.append(
                    f"Unknown strategy identifier: '{strat_key}'."
                )
                continue

            # Lookup compatible formats from canonical matrix
            compatible_formats = STRATEGY_FORMAT_COMPATIBILITY.get(target_strategy)
            if not compatible_formats:
                incompatible_errors.append(
                    f"Strategy '{strat_key}' has no registered format compatibility matrix."
                )
                continue

            # Format intersection assertion
            viable_session_formats = compatible_formats.intersection(session_formats)
            if not viable_session_formats:
                allowed_str = ", ".join(f.value for f in compatible_formats)
                active_str = ", ".join(f.value for f in session_formats)
                incompatible_errors.append(
                    f"Strategy '{strat_key}' (count: {count}) requires one of [{allowed_str}], "
                    f"but active session formats only provide [{active_str}]."
                )

        if incompatible_errors:
            raise ValueError(" ; ".join(incompatible_errors))

        return self


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
    Client-safe representation of sentence tokens for interactive formatting.
    Guarantees the target token's surface string is masked prior to serialization.
    """

    tok_idx: int = Field(description="1-based index within the sentence sequence")
    text: str = Field(description="Display text or blank placeholder")
    is_masked: bool = Field(
        default=False, description="True if this token is the target blank"
    )
    is_punctuation: bool = Field(
        default=False, description="Spacing flag for typographical attachment"
    )

    model_config = ConfigDict(from_attributes=True)


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
    """
    Internal intermediate representation generated by strategy subclasses.
    Decoupled from client delivery format constraints.
    """

    prompt: str = Field(description="Normalized prompt containing [___] marker")
    keys: Union[str, List[str]] = Field(description="Canonical accepted answer(s)")
    distractors: Optional[List[str]] = Field(
        default=None, description="Plausible distractors for MCQ"
    )
    lem_id: Optional[int] = Field(
        default=None, description="Surrogate key of associated lemma"
    )
    sentence_context: Optional[SentenceBlueprintContext] = Field(
        default=None, description="Ground truth linguistic metadata"
    )
    # Expose explicit hint field for FITB inflection instructions
    hint: Optional[str] = Field(
        default=None,
        description="Base dictionary lemma to display in-situ for FITB items (e.g. 'человек')",
    )


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
    """
    Client deliverable for FITB items.

    Security Contract:
    The target answer key must NEVER be passed to this model.
    'parts' must contain strictly (N + 1) text fragments surrounding N blanks.
    For a single blank:
        parts[0] = Text preceding the blank
        parts[1] = Text succeeding the blank (can be empty string if terminal)
    """

    item_format: str = "fitb"
    item_id: int
    prompt: str
    parts: List[str] = Field(
        default_factory=list,
        description="Text slices flanking the target blanks. Must never contain the key.",
    )
    sentence_tokens: Optional[List[DisplayToken]] = Field(
        default=None,
        description="Sanitized token stream with target items masked.",
    )

    model_config = ConfigDict(from_attributes=True)

    @field_validator("parts")
    @classmethod
    def validate_parts_structure(cls, v: List[str]) -> List[str]:
        """Ensures parts provides valid text delimiters for input blanks."""
        if not v or len(v) < 2:
            # Fallback if a single prompt string was supplied without delimiters
            return ["", ""] if not v else [v[0], ""]
        return v


class UnscrambleResponse(BaseModel):
    """
    Client deliverable for sentence unscrambling items.
    Tokens are scrambled using a seeded or verified permutation that ensures
    they do not match the original sequence. Keys and correct ordering are omitted.
    """

    item_format: EnumItemFormat = EnumItemFormat.UNSCRAMBLE
    item_id: int
    prompt: str = Field(
        "Put the words in the correct order:", description="Instructional prompt"
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
    item_id: int = Field(..., description="ID of the item being evaluated")
    response: str = Field(
        ..., description="The learner's submitted answer token or string"
    )
    response_time_ms: int = Field(
        ..., description="Latency for this specific attempt in ms"
    )
    attempt_num: int = Field(..., description="1-based attempt index for this item")
    is_final_attempt: bool = Field(
        False, description="Flag indicating if the item is resolving"
    )

    client_item_start: Optional[datetime] = Field(
        None, description="Timestamp when the client mounted this item into view"
    )


class AnswerResult(BaseModel):
    """
    Outcome deliverable for student response evaluation.
    Provides immediate pedagogical feedback while protecting answer keys on intermediate attempts.
    """

    is_correct: bool = Field(description="Evaluation verdict for this submission")
    correct_answer: Optional[str] = Field(
        default=None,
        description="Revealed canonical answer when solved or attempts exhausted",
    )
    explanation: Optional[str] = Field(
        default=None,
        description="Linguistic explanation or grammatical focus descriptor",
    )
    feedback: Optional[str] = Field(
        default=None,
        description="User-facing feedback message explaining attempt outcome or retry status",
    )
    attempt_num: Optional[int] = Field(
        default=None,
        description="1-based index of the evaluated attempt",
    )

    model_config = ConfigDict(from_attributes=True)


# results display


class UserResultsSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exercise_id: int
    completed_at: datetime
    difficulty_level: str
    total_items: int
    correct_count: int
    accuracy_rate: float
    duration_seconds: int


class ExerciseAttemptsSummary(BaseModel):
    accuracy_rate: float


class UserResultsReturn(BaseModel):
    summary: dict
    details: dict


class PipelineLookupRequest(BaseModel):
    """
    Ingests single or batch tokens for external dictionary synthesis.

    Robustness Enhancements:
    - Accepts 'token' or 'tokens' as either a string or an array of strings.
    - Flattens comma-, space-, or newline-delimited inputs.
    - Guarantees downstream consumers receive both `self.tokens` (List[str])
      and `self.token` (str) without throwing 422 TypeErrors.
    """

    # Accept Union[str, List[str]] to prevent Pydantic string_type crashes
    token: Optional[Union[str, List[str]]] = Field(
        default=None, description="Single lemma or legacy token payload."
    )
    tokens: Optional[Union[str, List[str]]] = Field(
        default_factory=list,
        description="Array or delimited list of target lemmas to ingest.",
    )

    @model_validator(mode="after")
    def unify_and_sanitize_tokens(self) -> "PipelineLookupRequest":
        raw_items: List[str] = []

        def extract_items(source: Optional[Union[str, List[str]]]) -> None:
            if not source:
                return
            if isinstance(source, str):
                # Split comma-, semicolon-, space-, or newline-separated pasted strings
                splits = re.split(r"[,;\s\n]+", source.strip())
                raw_items.extend([t for t in splits if t])
            elif isinstance(source, list):
                for element in source:
                    if isinstance(element, str) and element.strip():
                        splits = re.split(r"[,;\s\n]+", element.strip())
                        raw_items.extend([t for t in splits if t])

        # Extract from both potential fields
        extract_items(self.token)
        extract_items(self.tokens)

        # De-duplicate while preserving order
        seen = set()
        sanitized: List[str] = []
        for t in raw_items:
            cleaned = t.strip().lower()
            if cleaned and cleaned not in seen:
                # Strictly require alphabetic Cyrillic or Latin characters with optional internal hyphen
                if re.fullmatch(r"^[а-яёa-z]+([-'`][а-яёa-z]+)?$", cleaned):
                    seen.add(cleaned)
                    sanitized.append(cleaned)

        if not sanitized:
            raise ValueError("At least one valid lexical word token must be provided.")

        # Ensure both attributes are populated with proper types for downstream routes
        self.tokens = sanitized
        self.token = sanitized[0]
        return self


class PipelineItemOutcome(BaseModel):
    token: str
    status: str  # "queued", "already_exists", "in_progress", "rate_limited"
    queue_id: Optional[int] = None
    existing_lemma_id: Optional[int] = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class PipelineLookupResponse(BaseModel):
    results: List[PipelineItemOutcome]
    total_requested: int
    total_queued: int
    remaining_attempts: int
    reset_seconds: int

    # Backward compatibility attributes for single-item responses
    token: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PipelineStatusRequest(BaseModel):
    tokens: List[str] = Field(default_factory=list)


class LemmaCapabilityReport(BaseModel):
    """
    Data transfer object detailing what drill strategies a lemma
    is structurally equipped to support.
    """

    lemma_id: int
    lem_text: str
    is_exercise_ready: bool
    missing_critical_data: List[str]
    supported_item_types: List[str]


class LemmaReadinessItem(BaseModel):
    lemma_id: int
    lem_text: str
    is_usable: bool
    supported_item_types: List[str]
    advisory_warnings: List[str]
    critical_errors: List[str]

    model_config = ConfigDict(from_attributes=True)


class PoolValidationRequest(BaseModel):
    lemma_ids: List[int]
    min_required_words: int = Field(
        default=1,
        ge=1,
        description="Minimum number of eligible lemmas required to build the exercise.",
    )


class PoolValidationResponse(BaseModel):
    can_start: bool
    total_requested: int
    eligible_count: int
    eligible_lemma_ids: List[int]
    unusable_lemma_ids: List[int]
    reports: List[LemmaReadinessItem]
    summary_message: str

    model_config = ConfigDict(from_attributes=True)


# Pedagogical Capability Matrix: Strategy -> Compatible Item Formats
STRATEGY_FORMAT_COMPATIBILITY: Dict[AnyItemType, FrozenSet[EnumItemFormat]] = {
    # --- Lemma-Level Strategies ---
    EnumWordItemType.LEM_TO_POS: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.POS_TO_LEM: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_TO_DEF: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.DEF_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_TO_PRON: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.PRON_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.LEM_LEM_TO_REL: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.REL_TO_LEM_LEM: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    # --- Noun Morphological Strategies ---
    EnumWordItemType.NOUN_TO_GEND: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.GEND_TO_NOUN: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_TO_ANIM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ANIM_TO_NOUN: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.NOUN_TO_DMIN_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # --- Verb Morphological Strategies ---
    EnumWordItemType.VERB_TO_ASPT: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ASPT_TO_VERB: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_PAIR_TO_REL: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_ASPT_PAIR: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.TYPE_TO_VERB: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_TO_TNRF: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.TNRF_TO_VERB: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.VERB_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    # --- Adjective & Participle Strategies ---
    EnumWordItemType.ADJV_FORM_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_TYPE_TO_LEM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_FORM_TO_GRAM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.ADJV_GRAM_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.PART_FORM_TO_TYPE: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.MCQ,
        }
    ),
    EnumWordItemType.PART_TYPE_TO_FORM: frozenset(
        {
            EnumItemFormat.FLASHCARD,
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    # --- Sentence Syntax / Cloze Strategies ---
    EnumSentItemType.NOUN_MORPH: frozenset(
        {
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.VERB_MORPH: frozenset(
        {
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.ADJECTIVE_MORPH: frozenset(
        {
            EnumItemFormat.FITB,
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.DEP_REL: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.UNSCRAMBLE: frozenset(
        {
            EnumItemFormat.UNSCRAMBLE,
        }
    ),
    EnumSentItemType.FIND_HEAD: frozenset(
        {
            EnumItemFormat.MCQ,
            EnumItemFormat.FITB,
        }
    ),
    EnumSentItemType.FIND_SUBJECT: frozenset(
        {
            EnumItemFormat.MCQ,
            EnumItemFormat.FITB,
        }
    ),
    EnumSentItemType.NOUN_CASE: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.VERB_ASPECT: frozenset(
        {
            EnumItemFormat.MCQ,
        }
    ),
    EnumSentItemType.LEXICAL: frozenset(
        {
            EnumItemFormat.MCQ,
            EnumItemFormat.FITB,
        }
    ),
}
