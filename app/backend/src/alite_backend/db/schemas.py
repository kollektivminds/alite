# schemas.py
# Pydantic models for API data validation and response shaping.
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, EmailStr, Field, HttpUrl

#
# --- Data Processing Schmae ---
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
# These models define the clean, structured data that your
# 'Processor' will output, ready for the 'Loader'.

class LexiconRecord(BaseModel):
    """Schema for an entry in the Lexicon table."""
    word_text: str

class LemmasRecord(BaseModel):
    """Schema for an entry in the Lemmas table."""
    lemma_text: str
    part_of_speech: int

class GramPropsRecord(BaseModel):
    """Schema for the grammatical properties of a word form."""
    verb_aspect: Optional[int] = None
    verb_conj: Optional[str] = None
    verb_conj_type: Optional[str] = None
    verb_infinitive: Optional[bool] = None
    verb_mood: Optional[int] = None
    verb_trans_refl: Optional[int] = None
    verb_conj_person: Optional[int] = None
    part_type: Optional[int] = None
    part_voice: Optional[int] = None
    subst_case: Optional[int] = None
    subst_animacy: Optional[bool] = None
    adjv_short: Optional[bool] = None
    gram_gender: Optional[int] = None
    gram_number: Optional[int] = None
    gram_tense: Optional[int] = None
    noun_dimun: Optional[bool] = None

class DefinitionsRecord(BaseModel):
    """Schema for a single definition entry."""
    definition_text: str

class ProcessedPayload(BaseModel):
    """
    A container for the structured, processed data, ready for the Loader.
    This is the final output of your 'Processor' class.
    """
    lexicon: LexiconRecord
    lemma: LemmasRecord
    # A word can have multiple definitions
    definitions: List[DefinitionsRecord]
    gram_props: GramPropsRecord

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
# --- Database Schema ---
#

# --- User Schemas ---


class UserBase(BaseModel):
    """Base schema for user data, used for sharing common attributes."""

    username: str


class UserInDB(UserBase):
    """Schema for representing a user as stored in the database."""

    id: int
    privileged: bool
    created_at: datetime

    class Config:  # Pydantic v1 style config. For v2, use model_config
        from_attributes = True  # This is the v2 equivalent of orm_mode=True
        # For Pydantic v2:
        # model_config = {'from_attributes': True}
        # or just:
        # model_config = ConfigDict(from_attributes=True)


# --- Token Schemas for Authentication ---
# (Any token schemas would go here)
