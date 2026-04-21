# schemas.py
# Pydantic models for API data validation and response shaping.
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from .models import (
    EnumAltAdjvType,
    EnumAltNounType,
    EnumGender,
    EnumConjPerson,
    EnumGramTense,
    EnumParticipleType,
    EnumParticipleVoice,
    EnumPartOfSpeech,
    EnumSubstCase,
    EnumVerbAspect,
    EnumVerbMood,
    EnumVerbTransRefl,
    EnumVerbType
)
from pydantic import BaseModel, Field, HttpUrl, UUID4, UUID5, ConfigDict, model_validator

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
    examples: List[str] # The API sends a list of strings here.
    quotes: List[Quote] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    subsenses: List['Sense'] = Field(default_factory=list) # Self-referencing for nested senses

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
    clean_lemma: str
    accent_lemma: Optional[str] = None
    pos: EnumPartOfSpeech
    entry_key: UUID5
    noun_gender: Optional[EnumGender]
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
    form: str

class DefinitionsRecord(BaseModel):
    """Schema for a single definition entry."""
    temp_def_id: UUID4
    entry_key: UUID5
    def_text: str
    tags: List[str]

class DefExamplesRecord(BaseModel):
    """Schema for a single definition entry."""
    temp_def_id: UUID4
    def_example: str

class PronunciationsRecord(BaseModel):
    """Schema for a single definition entry."""
    entry_key: UUID5
    pron_text: str
    pron_type: int
    pron_tags: Optional[List[str]|str] = None

class RelatedLemmaRecord(BaseModel):
    """Schema for a single definition entry."""
    entry_key: UUID5
    pair_form: str
    rel_type: int
    pair_aspect: Optional[int] = None

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
    verb_pair: Optional[Union[str, List[str]]] = None
    verb_trans_refl: Optional[Tuple[Optional[bool], Optional[bool]]] = None

    class Config:
        """This helps prevent errors if your scraper passes extra,
        unexpected fields that are not defined in the model."""
        extra = 'ignore'

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
    clean_lemma: str
    accent_lemma: Optional[str] = None
    
# lemma shared grammar properties
class LemmaProps(BaseModel):
    pos: Optional[EnumPartOfSpeech] = None
    noun_gender: Optional[EnumGender] = None
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
    
    # read data even if it's not a dict
    model_config = ConfigDict(from_attributes=True)

# for pydantic validation of searches
class LemmaSearchParams(BaseModel):
    clean_lemma: Optional[str] = None
    accent_lemma: Optional[str] = None
    pos: Optional[EnumPartOfSpeech] = None
    entry_key: Optional[UUID5] = None
    noun_gender: Optional[EnumGender] = None
    subst_animacy: Optional[bool] = None
    verb_aspect: Optional[EnumVerbAspect] = None
    verb_conj: Optional[str] = None
    verb_type: Optional[EnumVerbType] = None
    verb_trans_refl: Optional[EnumVerbTransRefl] = None
    
    @model_validator(mode="after")
    def check_at_least_one_param(self):
        # check if all are None
        if not self.model_dump(exclude_unset=True):
            raise ValueError('You must provide at least one search parameter.')
        return self

# Lexicon

# shared properties
class LexiconBase(BaseModel):
    lex_text: str
    
# create lexeme
class LexemeCreate(LexiconBase):
    lex_text_clean: str
    
class LexemeUpdate(LexiconBase):
    id: int

# lexeme return
class LexemeReturn(LexiconBase):
    id: int
    
    # read data even if it's not a dict
    model_config = ConfigDict(from_attributes=True)

# Gram Props

class GramPropBase(BaseModel):
    irregular: bool
    
class GramPropCreate(GramPropBase):
    gram_tense: Optional[str] = None
    gram_num: Optional[str] = None
    conj_gender: Optional[str] = None
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
    model_config = ConfigDict(from_attributes=True)

# Definitions

class DefinitionBase(BaseModel):
    def_text: str
    
class DefinitionCreate(DefinitionBase):
    tags: List[str]

class DefinitionUpdate(DefinitionBase):
    id: int
    
class DefinitionReturn(DefinitionUpdate):
    pass

# Examples

class ExampleBase(BaseModel):
    def_text: str
    
class ExampleCreate(ExampleBase):
    pass

class ExampleUpdate(ExampleBase):
    id: int
    
class ExampleReturn(ExampleUpdate):
    pass

# Pronunciations

class PronunciationBase(BaseModel):
    pron_text: str
    
class PronunciationCreate(PronunciationBase):
    pron_tags: str
    pron_type: str

class PronunciationUpdate(PronunciationBase):
    id: int
    
class PronunciationReturn(PronunciationUpdate):
    pass


#
# --- Database Schema ---
#
