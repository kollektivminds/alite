import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Boolean,
    DateTime,
    Text,
    UniqueConstraint,
    JSON,
    UUID,
    Enum
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# This is the base class which our ORM models will inherit from
Base = declarative_base()

class EnumAltNounType(str, enum.Enum):
    DIMINUTIVE = "diminutive"
    AUGMENTATIVE = "augmentative"
    COLLECTIVE = "collective"
    PAUCAL = "paucal"
    PEJORATIVE = "pejorative"

class EnumAltAdjvType(str, enum.Enum):
    COMPARATIVE = "comparative"
    SUPERLATIVE = "superlative"
    SHORT = "short"
    
class EnumGender(str, enum.Enum):
    MASCULINE = "masculine"
    NEUTER = "neuter"
    FEMININE = "feminine"
    
class EnumGramNum(str, enum.Enum):
    SINGULAR = "singular"
    PLURAL = "plural"

class EnumConjPerson(str, enum.Enum):
    FIRST = "first-person"
    SECOND = "second-person"
    THIRD = "third-person"
    
class EnumGramTense(str, enum.Enum):
    PAST = "past"
    PRESENT = "present"
    FUTURE = "future"

class EnumPartOfSpeech(str, enum.Enum):
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    COM = "com"
    INTERJECTION = "interjection"
    NOUN = "noun"
    NUMERAL = "numeral"
    PARTICIPLE = "participle"
    PARTICLE = "particle"
    PREPOSITION = "preposition"
    PRONOUN = "pronoun"
    VERB = "verb"
    UNKNOWN = "unknown"
    
class EnumParticipleType(str, enum.Enum):
    ADJECTIVAL = "adjectival"
    ADVERBIAL = "adverbial"
    
class EnumParticipleVoice(str, enum.Enum):
    ACTIVE = "active"
    PASSIVE = "passive"

class EnumSubstCase(str, enum.Enum):
    NOMINATIVE = "nominative"
    GENITIVE = "genitive"
    ACCUSATIVE = "accusative"
    DATIVE = "dative"
    INSTRUMENTAL = "instrumental"
    PREPOSITIONAL = "prepositional"
    VOCATIVE = "vocative"
    LOCATIVE = "locative"
    PARTITIVE = "partitive"
    
class EnumVerbType(str, enum.Enum):
    TYPE_I = "type-I"
    TYPE_II = "type-II"
    
class EnumVerbMood(str, enum.Enum):
    INDICATIVE = "indicative"
    IMPERATIVE = "imperative"
    
class EnumVerbAspect(str, enum.Enum):
    IMPERFECTVE = "imperfective"
    PERFECTIVE = "perfective"
    DUAL = "dual"
    
class EnumVerbTransRefl(str, enum.Enum):
    INTRANSITIVE = "intransitive"    
    TRANSITIVE = "transitive"
    REFLEXIVE = "reflexive"
    
class EnumPronType(str, enum.Enum):
    ADJECTIVE = "adjective"
    ABSTRACT_NOUN = "abstract-noun"
    ADVERB = "adverb"
    REL_ADJV = "relational-adjective"
    NOUN_FROM_VERB = "noun-from-verb"

# --- Word Primary Tables ---
class Lemma(Base):
    """Represents a dictionary base form (lemma) of a word."""

    __tablename__ = "lemmas"

    id = Column(Integer, primary_key=True)
    # UUID5 entry key
    entry_key = Column(UUID, nullable=False)
    # text of the lemma
    lem_text = Column(String(50), nullable=False)
    # canonical of the lemma
    lem_canon = Column(String(50), nullable=True)
    # part of speech of the lemma
    pos = Column(Enum(EnumPartOfSpeech), nullable=False)
    # nominal gender
    noun_gender = Column(Enum(EnumGender), nullable=True)
    # substantive animacy
    subst_animacy = Column(Boolean, nullable=True)
    # verb aspect
    verb_aspect = Column(Enum(EnumVerbAspect), nullable=True)
    # verb conj (Zalizniak's)
    verb_conj = Column(String(8), nullable=True)
    # verb type
    verb_type = Column(Enum(EnumVerbType), nullable=True)
    # verb transivity/reflexivity
    verb_trans_refl = Column(Enum(EnumVerbTransRefl), nullable=True)

    # A single lemma has many inflected word forms
    lemma_word_form = relationship("WordForm", back_populates="word_form_lemma")
    # Relationship for lemma defintion
    lemma_definition = relationship(
        "LemmaDefinition", back_populates="lemma_definition"
    )
    # Relationship to other lemmas
    related_to = relationship(
        "LemmaRelation",
        foreign_keys="[LemmaRelation.source_id]",
        back_populates="source_lemma",
    )
    related_from = relationship(
        "LemmaRelation",
        foreign_keys="[LemmaRelation.target_id]",
        back_populates="target_lemma",
    )
    in_lesslist = relationship("LemmaInLessonList", back_populates="lemma_in")
    # Relationships for study results
    # lemma_crws = relationship(
    #     "ConjugationResultWordStudied", back_populates="crws_lemma"
    # )
    # lemma_drws = relationship(
    #     "DeclensionResultWordStudied", back_populates="drws_lemma"
    # )
    # Unique pair of "lem_text" and "pos" to prevent duplicates
    __table_args__ = (UniqueConstraint("id", "entry_key", name="unique_lemma"),)


class Lexeme(Base):
    """Represents a unique word string as it appears in a text."""

    __tablename__ = "lexicon"

    id = Column(Integer, primary_key=True)
    lex_text = Column(String(50), nullable=False, unique=True)
    lex_text_clean = Column(String(50), nullable=False)

    lexeme_word_form = relationship("WordForm", back_populates="word_form_lexicon")


class GramProp(Base):
    """Represents a unique combination of grammatical properties."""

    __tablename__ = "gram_props"

    id = Column(Integer, primary_key=True)

    # Various grammatical properties that can potentially apply,
    # though table will be largely sparse

    # non-specific grammar
    gram_tense = Column(Enum(EnumGramTense), nullable=True)
    irregular = Column(Boolean, default=False)
    gram_num = Column(Enum(EnumGramNum), nullable=True)
    # Verbs
    conj_gender = Column(Enum(EnumGender), nullable=True)
    conj_person = Column(Enum(EnumConjPerson), nullable=True)
    verb_mood = Column(Enum(EnumVerbMood), nullable=True)
    # Substantives (nouns, adjectives, numerals, participles)
    subst_case = Column(Enum(EnumSubstCase), nullable=True)
    alt_adjv_type = Column(Enum(EnumAltAdjvType), nullable=True)
    alt_noun_type = Column(Enum(EnumAltNounType), nullable=True)
    # Participles
    part_type = Column(Enum(EnumParticipleType), nullable=True)
    part_voice = Column(Enum(EnumParticipleVoice), nullable=True)
    # Relationship for a word form's grammatical properties
    gram_word_form = relationship("WordForm", back_populates="word_form_gram")
    # Unique set of grammatical properties to prevent duplicates
    __table_args__ = (
        UniqueConstraint(
            "gram_tense",
            "gram_num",
            "conj_gender",
            "conj_person",
            "verb_mood",
            "subst_case",
            "alt_adjv_type",
            "alt_noun_type",
            "part_type",
            "part_voice",
            name="unique_grammar",
        ),
    )


# TODO: go through everything after this to correspond with init_db.sql
class WordForm(Base):
    """The central junction table linking a lemma to a lexicon entry with specific properties."""

    __tablename__ = "word_forms"

    id = Column(Integer, primary_key=True)
    lem_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    lex_id = Column(Integer, ForeignKey("lexicon.id"), nullable=False)
    gram_id = Column(Integer, ForeignKey("gram_props.id"), nullable=False)

    word_form_lemma = relationship("Lemma", back_populates="lemma_word_form")
    word_form_lexicon = relationship("Lexeme", back_populates="lexeme_word_form")
    word_form_gram = relationship(
        "GramProp", back_populates="gram_word_form"
    )


class Definition(Base):
    __tablename__ = "definitions"

    id = Column(Integer, primary_key=True)
    def_text = Column(String, unique=True, nullable=False)

    definition_lemma = relationship(
        "LemmaDefinition", back_populates="definition_lemma"
    )
    
    definition_example = relationship(
        "DefinitionExample", back_populates="definition_example"
    )


class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True)
    ex_text = Column(String, unique=True, nullable=False)
    
    example_definition = relationship(
        "DefinitionExample", back_populates="example_definition"
    )


class Pronunciation(Base):
    __tablename__ = "pronunciations"

    id = Column(Integer, primary_key=True)
    pron_text = Column(String, unique=True, nullable=False)
    pron_tags = Column(String, nullable=True)
    pron_type = Column(Enum(EnumPronType), nullable=False)


# --- Word Junction Tables ---


class LemmaRelation(Base):
    """Junction table for relating lemmas to each other"""

    __tablename__ = "lem_rels"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)

    rel_type = Column(Integer, nullable=False)

    source_lemma = relationship(
        "Lemma", foreign_keys=[source_id], back_populates="related_to"
    )
    target_lemma = relationship(
        "Lemma", foreign_keys=[target_id], back_populates="related_from"
    )


class LemmaDefinition(Base):
    """Junction table for lemma definitions."""

    __tablename__ = "lem_defs"

    lem_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    def_id = Column(Integer, ForeignKey("definitions.id"), primary_key=True)

    lemma_definition = relationship(
        "Lemma", foreign_keys=[lem_id], back_populates="lemma_definition"
    )
    definition_lemma = relationship(
        "Definition", foreign_keys=[def_id], back_populates="definition_lemma"
    )


class DefinitionExample(Base):
    """Junction table for lemma definitions."""

    __tablename__ = "def_exs"

    def_id = Column(Integer, ForeignKey("definitions.id"), primary_key=True)
    ex_id = Column(Integer, ForeignKey("examples.id"), primary_key=True)

    definition_example = relationship(
        "Definition", foreign_keys=[def_id], back_populates="definition_example"
    )
    example_definition = relationship(
        "Example", foreign_keys=[ex_id], back_populates="example_definition"
    )


# --- Lemma Container Organization Tables ---


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    module_name = Column(String(10), nullable=False)

    has_lesslist = relationship("LessonListInModule", back_populates="in_module")


class LessonList(Base):
    __tablename__ = "lessons_lists"

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    topic = Column(String, nullable=False)
    is_type = Column(Integer, nullable=False)

    in_module = relationship("LessonListInModule", back_populates="lesslist_in")
    has_lemma = relationship("LemmaInLessonList", back_populates="in_lesslist")


# --- Secondary Organization Tables ---


class LessonListInModule(Base):
    """Junction table for lessons and modules"""

    __tablename__ = "lesslists_in_modules"

    lesslist_id = Column(Integer, ForeignKey("lessons_lists.id"), primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), primary_key=True)

    lesslist_in = relationship("LessonList", back_populates="in_module")
    in_module = relationship("Module", back_populates="has_lesslist")


class LemmaInLessonList(Base):
    __tablename__ = "lems_in_lesslists"

    lem_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    lesslist_id = Column(Integer, ForeignKey("lessons_lists.id"), primary_key=True)

    lemma_in = relationship("Lemma", back_populates="in_lesslist")
    in_lesslist = relationship("LessonList", back_populates="has_lemma")


# --- Users ---


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=True)  # Added username
    privileged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    in_group = relationship("UserInGroup", back_populates="group_user")


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True)
    group_name = Column(String(50), unique=True, nullable=True)

    users = relationship("UserInGroup", back_populates="user_group")


class UserInGroup(Base):
    __tablename__ = "users_in_groups"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("user_groups.id"), primary_key=True)

    group_user = relationship("User", back_populates="in_group")
    user_group = relationship("UserGroup", back_populates="users")


# --- Questions, Sessions, and Responses ---
""" 

class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    item_type = Column(String(50), nullable=False)
    item_text = Column(Text, nullable=False)
    choices = Column(JSON)  # Using JSONB for flexibility
    correct_answer = Column(Text, nullable=False)
    lemma_id = Column(Integer, ForeignKey("lemmas.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class QuestionSession(Base):
    __tablename__ = "question_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_start_time = Column(DateTime(timezone=True), server_default=func.now())
    session_end_time = Column(DateTime(timezone=True))

    user = relationship("User")
    responses = relationship("StudentResponse", back_populates="session")


class StudentResponse(Base):
    __tablename__ = "student_responses"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    student_answer = Column(Text)
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("QuestionSession", back_populates="responses")
    question = relationship("Question")


class StudentDecision(Base):
    __tablename__ = "student_decisions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    decision_type = Column(String(100), nullable=False)
    decision_value = Column(Text, nullable=False)
    made_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True)
    skill_name = Column(String(255), nullable=False, unique=True)
    skill_description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SkillInQuestion(Base):
    __tablename__ = "question_skills"

    question_id = Column(Integer, ForeignKey("questions.id"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id"), primary_key=True)


class StudentSkillMastery(Base):
    __tablename__ = "student_skill_mastery"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id"), nullable=False)
    mastery_level = Column(Float, default=0.0)
    p_learn = Column(Float)
    p_guess = Column(Float)
    p_slip = Column(Float)
    last_seen_at = Column(DateTime(timezone=True))
    next_review_at = Column(DateTime(timezone=True))

    user = relationship("User")
    skill = relationship("Skill")


class UserExperiment(Base):
    __tablename__ = "user_experiments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    experiment_name = Column(String(255), nullable=False)
    variant_name = Column(String(255), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
 """