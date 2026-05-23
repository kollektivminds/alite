# schemas.py
# Pydantic models for API data validation and response shaping.
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
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
    EnumRelLemType,
    EnumLookupStatus,
    EnumPronType,
    EnumUserRole,
    EnumItemFormat,
    EnumWordItemType,
    EnumItemDifficulty,
)
from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    UUID4,
    UUID5,
    ConfigDict,
    model_validator,
    JsonValue,
)

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
    subst_animacy: Optional[bool]
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
    This is the final output of your 'Processor' class.
    """

    lemmas: List[LemmasRecord]
    gram_props: List[GramPropsRecord]
    lexicon: List[LexiconRecord]
    # A word can have multiple definitions
    definitions: List[DefinitionsRecord]
    def_examples: List[DefExamplesRecord]
    pronunciations: List[PronunciationsRecord]
    rel_lems: List[RelatedLemmaRecord]


# --- Wiki Pre-Processing Schema ---


class UnprocessedWikiWord(BaseModel):
    """Pydantic model for validating raw scraped data."""

    # General fields
    pos: Optional[str] = None
    definitions: Optional[Dict] = None
    inflections: Dict[str, Dict] = Field(default_factory=dict)

    # Adjectives
    has_short: Optional[bool] = None
    hard_stem: Optional[bool] = None

    # Nouns
    subst_animacy: Optional[bool] = None
    subst_gender: Optional[str] = None
    subst_number: Optional[str] = None

    # Verbs
    verb_aspect: Optional[str] = None
    verb_conj: Optional[str] = None
    verb_conj_type: Optional[int] = None
    verb_pair: Optional[str | List[str]] = None
    verb_trans_refl: Optional[Tuple[Optional[bool], Optional[bool]]] = None

    class Config:
        """This helps prevent errors if your scraper passes extra,
        unexpected fields that are not defined in the model."""

        extra = "ignore"


class RawWikiLemma(BaseModel):
    """"""

    lemma: Optional[str] = None
    parts_of_speech: Dict[str, List[UnprocessedWikiWord]]


#
# --- CRUD Schema ---
#

# Lemmas


# shared properties
class LemmaBase(BaseModel):
    lem_text: str
    lem_canon: Optional[str] = None


# lemma shared grammar properties
class LemmaProps(BaseModel):
    pos: Optional[EnumPartOfSpeech] = None
    noun_gender: Optional[EnumGramGender] = None
    subst_animacy: Optional[bool] = None
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
    subst_animacy: Optional[bool] = None
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
    lookup_status: EnumLookupStatus


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


# Users


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    user_role: EnumUserRole
    email: str


class UserUpdate(UserBase):
    id: int
    alias: Optional[str]


class UserReturn(UserUpdate):
    created_at: datetime


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

# Sentences

# Sentences in Documents

# Words in Sentences

# Items


class ItemBase(BaseModel):
    item_type: EnumWordItemType
    prompt: str
    settings: JsonValue
    key: str
    distractors: Optional[List[str]]


class ItemCreate(ItemBase):
    pass


class ItemUpdate(ItemBase):
    id: int


class ItemReturn(ItemUpdate):
    start_time: datetime
    finish_time: datetime
    created_at: datetime


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
    less_list_ids: Optional[List[int]]
    mod_ids: Optional[List[int]]
    lem_ids: Optional[List[int]]
    ex_formats: List[EnumItemFormat]
    num_items: int = 10
    max_keys: int = 1
    max_distractors: int = 3


class ExerciseRequest(BaseModel):
    # Side-A + Side-B items = request
    exercise_context: ExerciseContext
    type_counts: Dict[EnumWordItemType, int]


# Raw Exercise Responses


class KeysReponse(BaseModel):
    item_id: int
    key_text: str | Dict[str, Any]


class DistractorsResponse(BaseModel):
    item_id: int
    dist_text: str | Dict[str, Any]
    

class ItemBlueprint(BaseModel):
    prompt: str
    key: str
    distractors: List[str]


# Processed Exercise Responses


class FlashcardResponse(BaseModel):
    item_format = EnumItemFormat.FLASHCARD
    item_id: int
    front_text: str
    back_text: str


class MultipleChoiceResponse(BaseModel):
    item_format = EnumItemFormat.MCQ
    item_id: int
    prompt: str
    options: List[str | int]


class WordClozeResponse(BaseModel):
    item_format = EnumItemFormat.CLOZE
    item_id: int
    prompt: str
    sentence_parts: List[str]
    # TODO: replace below with cheat-secure way to check cloze responses
    target_lemma: str


ExerciseItems = FlashcardResponse | MultipleChoiceResponse | WordClozeResponse


class ExerciseResponse(BaseModel):
    total_questions: int
    response_data: List[ExerciseItems]


# User Item Response & Result


class AnswerSubmission(BaseModel):
    user_id: int
    item_id: int
    selection: str
    response_time_ms: int


class AnswerResult(BaseModel):
    is_correct: bool
    attempts_remaining: int
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


# Item Type


class Item_FormLemToGnc(BaseModel):
    gender: bool = True
    number: bool = True
    case: bool = True
