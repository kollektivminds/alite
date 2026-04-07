# schemas.py
# Pydantic models for API data validation and response shaping.
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, HttpUrl, UUID4, UUID5

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
# These models define the clean, structured data

class LemmasRecord(BaseModel):
    """Schema for an entry in the Lemmas table."""
    clean_lemma: str
    accent_lemma: Optional[str] = None
    pos: int
    entry_key: UUID5

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
    pron_tags: Optional[List[str]|str]

class VerbPairsRecord(BaseModel):
    """Schema for a single definition entry."""
    entry_key: UUID5
    pair_form: str
    pair_aspect: int

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
    verb_pairs: List[VerbPairsRecord]

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
