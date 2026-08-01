from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
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
    Enum,
    Index,
)
from sqlalchemy.orm import relationship, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB


class EnumTargetLanguage(str, enum.Enum):
    RU = "ru"


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


class EnumGramGender(str, enum.Enum):
    MASCULINE = "masculine"
    NEUTER = "neuter"
    FEMININE = "feminine"
    DUAL = "dual"


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
    CONJUNCTION = "conjunction"
    INTERJECTION = "interjection"
    NOUN = "noun"
    NUMERAL = "numeral"
    PARTICIPLE = "participle"
    PARTICLE = "particle"
    PREPOSITION = "preposition"
    PRONOUN = "pronoun"
    VERB = "verb"
    UNKNOWN = "unknown"


class EnumPartType(str, enum.Enum):
    ADJECTIVAL = "adjectival"
    ADVERBIAL = "adverbial"


class EnumPartVoice(str, enum.Enum):
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


class EnumRelLemType(str, enum.Enum):
    ADJECTIVE_OF = "adjective_of"
    ABSTRACT_NOUN_OF = "abstract-noun_of"
    ADVERB_OF = "adverb_of"
    REL_ADJV_OF = "relational-adjective_of"
    NOUN_FROM_VERB_OF = "noun-from-verb_of"
    PERFECTIVE_PAIR_OF = "perfective-pair_of"
    IMPERFECTIVE_PAIR_OF = "imperfective-pair_of"
    SYNONYM_OF = "synonym_of"
    ANTONYM_OF = "antonym_of"


class EnumRelLemTypeGroup(str, enum.Enum):
    SHARED_ROOT = "shared_root"
    SEMANTIC = "semantic"
    ASPECTUAL_PAIR = "aspectual_pair"


class EnumPronType(str, enum.Enum):
    IPA = "ipa"
    ROMANIZATION = "romanization"


class EnumLessListType(str, enum.Enum):
    COURSE = "course"
    USER = "user"


class EnumUserRole(str, enum.Enum):
    INSTRUCTOR = "instructor"
    STUDENT = "student"


class EnumLookupStatus(str, enum.Enum):
    UNLINKED = "unlinked"
    LINKED = "linked"
    FAILED = "failed"
    IGNORED = "ignored"
    NOT_IN_DICT = "not_in_dict"


class EnumItemFormat(str, enum.Enum):
    CLOZE = "cloze"
    MCQ = "mcq"
    FLASHCARD = "flashcard"


class EnumWordItemType(str, enum.Enum):
    # --- LEMMAS ---
    # Part of Speech
    # lemmas.lem_canon <-> lemmas.pos
    LEM_TO_POS = "lem_to_pos"
    POS_TO_LEM = "pos_to_lem"
    # Definitions
    # lemmas.lem_canon <-> definitions.def_text
    LEM_TO_DEF = "lem_to_def"
    DEF_TO_LEM = "def_to_lem"
    # Pronunciations
    # lemmas.lem_canon <-> pronunciations.pron_text
    LEM_TO_PRON = "lem_to_pron"
    PRON_TO_LEM = "pron_to_lem"
    # Lemma Relations
    # lem_rels.source_id(lemmas.lem_canon)
    # + lem_rels.target_id(lemmas.lem_canon)
    # <-> lem_rels.rel_type
    LEM_LEM_TO_REL = "lem_lem_to_rel"
    REL_TO_LEM_LEM = "rel_to_lem_lem"

    # --- SUBSTANTIVES ---
    # --- ADJECTIVES ---
    # lemma (adjective) <-> comparative / superlative form
    ADJV_FORM_TO_TYPE = "adjv_form_to_type"  # "What is the [comparative | superlative] form of X?" (MCQ)
    ADJV_TYPE_TO_LEM = (
        "adjv_type_to_lem"  # "What is the base form of [adjective]?" (MCQ/Cloze)
    )
    # adjective form <-> adjective type
    ADJV_FORM_TO_GRAM = "adjv_form_to_gram"  # "What is the gender, number, case of [adjective form]?" (MCQ)
    ADJV_GRAM_TO_FORM = "adjv_gram_to_form"  # "Which of the following adjectival forms is/are an example of [grammar]?" (MCQ)
    # --- NOUNS ---
    # lemma (noun) <-> gender
    NOUN_TO_GEND = "noun_to_gender"  # "What gender is [noun]?" (MCQ)
    GEND_TO_NOUN = "gender_to_noun"  # "Which lemma(s) is/are [noun_gender]?" (MCQ)
    # lemma (noun) <-> animacy (bool)
    NOUN_TO_ANIM = "noun_to_anim"  # "Is [noun] animate or inanimate?" (MCQ)
    ANIM_TO_NOUN = "anim_to_noun"  # "Which lemma(s) is/are ["verb_aspect"]?" (MCQ)
    # noun form <-> noun GNC
    NOUN_FORM_TO_GRAM = "noun_form_to_gram"  # "What is the gender, number, case of [adjective form]?" (MCQ)
    NOUN_GRAM_TO_FORM = "noun_gram_to_form"  # "Which of the following noun forms is/are an example of [grammar]?" (MCQ)
    # noun lemma -> diminutive form
    NOUN_TO_DMUN_FORM = (
        "noun_to_dmun_form"  # What is the diminutive form of [lemma]? (MCQ/Cloze)
    )
    # --- PARTICIPLES ---
    # participle <-> type (tense, mood)
    PART_TYPE_TO_FORM = "part_type_to_form"  # "What form is type X?" (MCQ)
    FORM_TO_PART_TYPE = "form_to_part_type"  # "What type of participle is X?" (MCQ)

    # --- VERBS ----
    # Aspect
    # lemmas.filter(pos==verb).lem_canon <-> lemmas(id=lem_id).filter(pos==verb).verb_aspect
    VERB_TO_ASPT = "verb_to_aspt"  # "What is the aspect of [verb]?" (FC/MCQ)
    # lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[source_id, target_id].lem_canon
    # <-> lemmas(id=lem_id).verb_aspect
    ASPT_TO_VERB = "aspt_to_verb"  # "Which of these verbs is [aspect]?" (MCQ)
    # Aspectual pairs
    VERB_PAIR_TO_REL = "verb_pair_to_rel"  # "Choose the [aspect] verb(s) of the aspectual group." (MCQ)
    # lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[source_id].lem_canon
    # <-> lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[target_id].lem_canon
    VERB_TO_ASPT_PAIR = (
        "verb_to_aspt_pair"  # "What is the [aspect] partner of [verb]?" (FC/MCQ/Cloze)
    )
    # Conjugation Type
    # lemmas.filter(pos==verb).lem_canon <-> lemmas.filter(pos==verb).verb_type
    VERB_TO_TYPE = "verb_to_type"  # "What type of verb is X?" (MCQ)
    TYPE_TO_VERB = "type_to_verb"  # "Which lemma(s) is/are type X?" (MCQ)
    # Conjugation Forms (tense, number, gender, person, mood)
    # word_forms[gram_id=gram_props.[gram_tense, gram_num, gram_gender, conj_person, verb_mood]].lem_id[pos=PRONOUN].lem_canon
    # + lemmas.filter(pos==verb).lem_canon
    # <-> word_forms(lem_id=lem, gram_id=gram_prop).lex_id.lex_text
    VERB_TO_CONJ_FORM = "verb_to_conj_form"  # "What is the X form of Y?" (MCQ/Cloze)
    # Transitivity & Reflexivity
    # lemmas.filter(pos==verb).lem_canon
    # <-> lemmas.filter(pos==verb).verb_trans_refl
    VERB_TO_TNRF = "verb_to_tnrf"  # "Is X transitive, reflexive, or neither?" (MCQ)
    TNRF_TO_VERB = "tnrf_to_verb"  # "Which lemma(s) is/are X?" (MCQ)


class EnumSentItemType(str, enum.Enum):
    # how to organize these items?
    pass


class EnumItemDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    DIFFICULT = "difficult"


#
# Declarative Base for Models
#

# Base = declarative_base()


class Base(DeclarativeBase):
    """
    All database models
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    pass


# --- Word Primary Tables ---


class Lemma(Base):
    """Represents a dictionary base form (lemma) of a word."""

    __tablename__ = "lemmas"

    id: Mapped[int] = mapped_column(primary_key=True)
    # UUID5 entry key
    entry_key: Mapped[UUID] = mapped_column()
    # text of the lemma
    lem_text: Mapped[str] = mapped_column(String(48), index=True)
    # canonical of the lemma
    lem_canon: Mapped[str | None] = mapped_column(String(48))
    # part of speech of the lemma
    pos: Mapped[EnumPartOfSpeech] = mapped_column(Enum(EnumPartOfSpeech))
    # nominal gender
    noun_gender: Mapped[EnumGramGender | None] = mapped_column(Enum(EnumGramGender))
    # substantive animacy
    noun_animacy: Mapped[bool | None] = mapped_column()
    # verb aspect
    verb_aspect: Mapped[EnumVerbAspect | None] = mapped_column(Enum(EnumVerbAspect))
    # verb conj (Zalizniak's)
    verb_conj: Mapped[str | None] = mapped_column(String(16))
    # verb type
    verb_type: Mapped[EnumVerbType | None] = mapped_column(Enum(EnumVerbType))
    # verb transivity/reflexivity
    verb_trans_refl: Mapped[EnumVerbTransRefl | None] = mapped_column(
        Enum(EnumVerbTransRefl)
    )

    # A single lemma has many inflected word forms
    lemma_word_form: Mapped[List["WordForm"]] = relationship(
        back_populates="word_form_lemma"
    )
    # Relationship for lemma definitions
    definitions: Mapped[List["LemmaDefinition"]] = relationship(back_populates="lemma")
    # Relationship for lemma pronunciations
    pronunciations: Mapped[List["LemmaPronunciation"]] = relationship(
        back_populates="lemma"
    )
    # Relationship to other lemmas as source
    related_to: Mapped[List["LemmaRelation"]] = relationship(
        foreign_keys="[LemmaRelation.source_id]",
        back_populates="source_lemma",
    )
    # Relationship to other lemmas as target
    related_from: Mapped[List["LemmaRelation"]] = relationship(
        foreign_keys="[LemmaRelation.target_id]",
        back_populates="target_lemma",
    )
    in_less_list: Mapped[List["LessonList"]] = relationship(
        secondary="lems_in_less_lists", back_populates="has_lemma"
    )
    in_item: Mapped[List["Item"]] = relationship(
        secondary="lems_in_items", back_populates="ref_lems"
    )
    # Unique pair of "lem_text" and "pos" to prevent duplicates
    __table_args__ = (UniqueConstraint("id", "entry_key", name="unique_lemma"),)


# Morphological Tables


class Lexeme(Base):
    """Represents a unique word string as it appears in a text."""

    __tablename__ = "lexicon"

    id: Mapped[int] = mapped_column(primary_key=True)
    lex_text: Mapped[str] = mapped_column(String(48), unique=True)
    lex_text_clean: Mapped[str] = mapped_column(String(48))

    lexeme_word_form: Mapped[List["WordForm"]] = relationship(
        back_populates="word_form_lexicon"
    )


class GramProp(Base):
    """Represents a unique combination of grammatical properties."""

    __tablename__ = "gram_props"

    id: Mapped[int] = mapped_column(primary_key=True)

    # non-pos-specific grammar
    irregular: Mapped[bool] = mapped_column(default=False)
    gram_tense: Mapped[EnumGramTense | None] = mapped_column(Enum(EnumGramTense))
    gram_num: Mapped[EnumGramNum | None] = mapped_column(Enum(EnumGramNum))
    # Verbs
    gram_gender: Mapped[EnumGramGender | None] = mapped_column(Enum(EnumGramGender))
    conj_person: Mapped[EnumConjPerson | None] = mapped_column(Enum(EnumConjPerson))
    verb_mood: Mapped[EnumVerbMood | None] = mapped_column(Enum(EnumVerbMood))
    # Substantives (nouns, adjectives, numerals, participles)
    subst_case: Mapped[EnumSubstCase | None] = mapped_column(Enum(EnumSubstCase))
    alt_adjv_type: Mapped[EnumAltAdjvType | None] = mapped_column(Enum(EnumAltAdjvType))
    alt_noun_type: Mapped[EnumAltNounType | None] = mapped_column(Enum(EnumAltNounType))
    # Participles
    part_type: Mapped[EnumPartType | None] = mapped_column(Enum(EnumPartType))
    part_voice: Mapped[EnumPartVoice | None] = mapped_column(Enum(EnumPartVoice))

    # Relationship for a word form's grammatical properties
    gram_word_form: Mapped[List["WordForm"]] = relationship(
        back_populates="word_form_gram"
    )
    # Unique set of grammatical properties to prevent duplicates
    __table_args__ = (
        UniqueConstraint(
            "gram_tense",
            "gram_num",
            "gram_gender",
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


class WordForm(Base):
    """The central junction table linking a lemma to a lexicon entry with specific properties."""

    __tablename__ = "word_forms"

    id: Mapped[int] = mapped_column(primary_key=True)
    lem_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), index=True)
    lex_id: Mapped[int] = mapped_column(ForeignKey("lexicon.id"), index=True)
    gram_id: Mapped[int] = mapped_column(ForeignKey("gram_props.id"), index=True)

    word_form_lemma: Mapped["Lemma"] = relationship(back_populates="lemma_word_form")
    word_form_lexicon: Mapped["Lexeme"] = relationship(
        back_populates="lexeme_word_form"
    )
    word_form_gram: Mapped["GramProp"] = relationship(back_populates="gram_word_form")


# Auxiliary Linguistic Tables


class Definition(Base):
    __tablename__ = "definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    def_text: Mapped[str] = mapped_column(unique=True)
    def_tags: Mapped[List[str] | None] = mapped_column(ARRAY(String))

    lemmas: Mapped[List["LemmaDefinition"]] = relationship(back_populates="definition")

    example: Mapped[List["DefinitionExample"]] = relationship(
        back_populates="definition_example"
    )


class Example(Base):
    __tablename__ = "examples"

    id: Mapped[int] = mapped_column(primary_key=True)
    ex_text: Mapped[str] = mapped_column(unique=True)

    definition: Mapped["DefinitionExample"] = relationship(
        back_populates="example_definition"
    )


class Pronunciation(Base):
    __tablename__ = "pronunciations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pron_text: Mapped[str] = mapped_column(unique=True)
    pron_tags: Mapped[List[str] | None] = mapped_column(ARRAY(String))
    pron_type: Mapped[EnumPronType] = mapped_column(Enum(EnumPronType))

    lemmas: Mapped["LemmaPronunciation"] = relationship(back_populates="pronunciation")


# --- Lemma Junction Tables ---


class LemmaRelation(Base):
    """Junction table for relating lemmas to each other"""

    __tablename__ = "lem_rels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), index=True)
    target_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), index=True)
    rel_type: Mapped[EnumRelLemType] = mapped_column(Enum(EnumRelLemType))

    source_lemma: Mapped["Lemma"] = relationship(
        foreign_keys=[source_id], back_populates="related_to"
    )
    target_lemma: Mapped["Lemma"] = relationship(
        foreign_keys=[target_id], back_populates="related_from"
    )


class LookupQueue(Base):

    __tablename__ = "lookup_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    target_lem: Mapped[int] = mapped_column(String(48))
    target_id: Mapped[int | None] = mapped_column(ForeignKey("lemmas.id"), index=True)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("lemmas.id"), index=True)
    rel_type: Mapped[EnumRelLemType] = mapped_column(Enum(EnumRelLemType))
    status: Mapped[EnumLookupStatus] = mapped_column(
        Enum(EnumLookupStatus), default=EnumLookupStatus.UNLINKED
    )


class LemmaDefinition(Base):
    """Junction table for lemmas and definitions."""

    __tablename__ = "lem_defs"

    lem_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), primary_key=True)
    def_id: Mapped[int] = mapped_column(ForeignKey("definitions.id"), primary_key=True)

    lemma: Mapped["Lemma"] = relationship(
        foreign_keys=[lem_id], back_populates="definitions"
    )
    definition: Mapped["Definition"] = relationship(
        foreign_keys=[def_id], back_populates="lemmas"
    )


class DefinitionExample(Base):
    """Junction table for definitions and examples."""

    __tablename__ = "def_exs"

    def_id: Mapped[int] = mapped_column(ForeignKey("definitions.id"), primary_key=True)
    ex_id: Mapped[int] = mapped_column(ForeignKey("examples.id"), primary_key=True)

    definition_example: Mapped["Definition"] = relationship(
        foreign_keys=[def_id], back_populates="example"
    )
    example_definition: Mapped["Example"] = relationship(
        foreign_keys=[ex_id], back_populates="definition"
    )


class LemmaPronunciation(Base):
    """Junction table for lemmas and pronunciations."""

    __tablename__ = "lem_prons"

    lem_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), primary_key=True)
    pron_id: Mapped[int] = mapped_column(
        ForeignKey("pronunciations.id"), primary_key=True
    )

    lemma: Mapped["Lemma"] = relationship(
        foreign_keys=[lem_id], back_populates="pronunciations"
    )
    pronunciation: Mapped["Pronunciation"] = relationship(
        foreign_keys=[pron_id], back_populates="lemmas"
    )


# --- Lemma Container Organization Tables ---


class Module(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(primary_key=True)
    module_name: Mapped[str] = mapped_column(String(10))

    has_less_list: Mapped[List["LessonListInModule"]] = relationship(
        back_populates="in_module"
    )


class LessonList(Base):
    __tablename__ = "lessons_lists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(48), unique=True)
    topic: Mapped[str | None] = mapped_column(String)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    in_module: Mapped[List["LessonListInModule"]] = relationship(
        back_populates="less_list_in"
    )
    has_lemma: Mapped[List["Lemma"]] = relationship(
        secondary="lems_in_less_lists", back_populates="in_less_list"
    )


# --- Secondary Organization Tables ---


class LemmaInLessonList(Base):
    __tablename__ = "lems_in_less_lists"

    lem_id: Mapped[int] = mapped_column(ForeignKey("lemmas.id"), primary_key=True)
    less_list_id: Mapped[int] = mapped_column(
        ForeignKey("lessons_lists.id"), primary_key=True
    )

    # lemma_in = relationship("Lemma", back_populates="in_less_list")
    # in_less_list = relationship("LessonList", back_populates="has_lemma")


class LessonListInModule(Base):
    """Junction table for lessons and modules"""

    __tablename__ = "less_lists_in_mods"

    less_list_id: Mapped[int] = mapped_column(
        ForeignKey("lessons_lists.id"), primary_key=True
    )
    mod_id: Mapped[int] = mapped_column(ForeignKey("modules.id"), primary_key=True)

    less_list_in: Mapped["LessonList"] = relationship(back_populates="in_module")
    in_module: Mapped["Module"] = relationship(back_populates="has_less_list")


# --- Sentence Tables ---


class Sentence(Base):
    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    sent_idx: Mapped[int] = mapped_column(Integer)
    document: Mapped["Document"] = relationship(back_populates="sentences")
    tokens: Mapped["SentenceToken"] = relationship(
        back_populates="sentence",
        order_by="SentenceToken.token_idx",
        cascade="all, delete-orphan",
    )


class SentenceToken(Base):
    """Junction table mapping a WordForm to a specific position in a Sentence."""

    __tablename__ = "sentence_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sent_id: Mapped[int] = mapped_column(
        ForeignKey("sentences.id", ondelete="CASCADE"), index=True
    )
    token_idx: Mapped[int] = mapped_column(Integer)

    lex_raw: Mapped[str] = mapped_column(String(48))
    lem_raw: Mapped[str] = mapped_column(String(48))
    features: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)

    head_idx: Mapped[int | None] = mapped_column(Integer)
    dep_rel: Mapped[str | None] = mapped_column(String(100))
    semantic_tag: Mapped[str | None] = mapped_column(String(100))

    # context-specific lexeme orthography
    is_capitalized: Mapped[bool] = mapped_column()
    punctuation_before: Mapped[str | None] = mapped_column(String(8))
    punctuation_after: Mapped[str | None] = mapped_column(String(8))

    # associated form(s)
    status: Mapped[EnumLookupStatus] = mapped_column(
        Enum(EnumLookupStatus), default=EnumLookupStatus.UNLINKED, index=True
    )
    lem_id: Mapped[int | None] = mapped_column(ForeignKey("lemmas.id"), index=True)
    lex_id: Mapped[int | None] = mapped_column(ForeignKey("lexicon.id"), index=True)
    wf_id: Mapped[int | None] = mapped_column(ForeignKey("word_forms.id"), index=True)

    # relationships
    sentence: Mapped["Sentence"] = relationship(back_populates="tokens")
    lemma: Mapped[Optional["Lemma"]] = relationship()
    word_form: Mapped[Optional["WordForm"]] = relationship()

    __table_args__ = (
        Index("ix_sentence_token_features_gin", "features", postgresql_using="gin"),
    )


# --- Sentence Organization Tables ---


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column()
    author: Mapped[str | None] = mapped_column()
    source: Mapped[str | None] = mapped_column()
    date: Mapped[datetime | None] = mapped_column(DateTime(timezone=False))

    sentences: Mapped[List["Sentence"]] = relationship(
        back_populates="document",
        order_by="Sentence.sent_idx",
        cascade="all, delete-orphan",
    )


# --- Users ---


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(String(48), unique=True)
    alias: Mapped[str | None] = mapped_column(String(25))
    user_role: Mapped[EnumUserRole] = mapped_column(Enum(EnumUserRole))
    settings: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    # target_lang: Mapped[EnumTargetLanguage] = mapped_column(Enum(EnumTargetLanguage))
    # email: Mapped[str] = mapped_column()
    in_group: Mapped["UserInGroup"] = relationship(back_populates="group_user")
    exercises: Mapped[List["Exercise"]] = relationship(back_populates="user")

    __table_args__ = (
        Index("ix_user_settings_gin", "settings", postgresql_using="gin"),
    )


class UserGroup(Base):
    __tablename__ = "user_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_name: Mapped[str | None] = mapped_column(String(48), unique=True)

    users: Mapped[List["UserInGroup"]] = relationship(back_populates="user_group")


class UserInGroup(Base):
    __tablename__ = "users_in_groups"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("user_groups.id"), primary_key=True
    )

    group_user: Mapped["User"] = relationship(back_populates="in_group")
    user_group: Mapped["UserGroup"] = relationship(back_populates="users")


# --- Questions, Sessions, and Responses ---


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), index=True)
    # TODO: set this up to start at load
    start_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    has_item: Mapped[List["Item"]] = relationship(
        back_populates="in_ex", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship(back_populates="exercises")


class Item(Base):
    __tablename__ = "items"
    # id, type
    id: Mapped[int] = mapped_column(primary_key=True)
    ex_id: Mapped[int] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    order_in_ex: Mapped[int] = mapped_column()
    item_type: Mapped[EnumWordItemType] = mapped_column(Enum(EnumWordItemType))
    item_format: Mapped[EnumItemFormat] = mapped_column(Enum(EnumItemFormat))
    # content
    prompt: Mapped[str | None] = mapped_column()
    settings: Mapped[dict | None] = mapped_column(JSON)
    key: Mapped[str | List[str]] = mapped_column(ARRAY(String))
    distractors: Mapped[List[str] | None] = mapped_column(ARRAY(String))
    difficulty: Mapped[EnumItemDifficulty | None] = mapped_column(
        Enum(EnumItemDifficulty)
    )
    responses: Mapped[List["ItemResponse"]] = relationship(back_populates="item")
    # meta
    # TODO: set up to record times
    start_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finish_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    ref_lems: Mapped[List["Lemma"]] = relationship(
        secondary="lems_in_items", back_populates="in_item"
    )
    in_ex: Mapped["Exercise"] = relationship(back_populates="has_item")


class LemmaInItem(Base):
    __tablename__ = "lems_in_items"

    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    lem_id: Mapped[int] = mapped_column(
        ForeignKey("lemmas.id", ondelete="CASCADE"), primary_key=True
    )


class ItemResponse(Base):
    __tablename__ = "student_responses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    selection: Mapped[str] = mapped_column()
    is_correct: Mapped[bool] = mapped_column()
    response_time_ms: Mapped[int] = mapped_column()

    item: Mapped["Item"] = relationship(back_populates="responses")


"""
class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    skill_name: Mapped[int] = mapped_column(String(255), nullable=False, unique=True)
    skill_description: Mapped[int] = mapped_column(Text)


class SkillInQuestion(Base):
    __tablename__ = "question_skills"

    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id"), primary_key=True)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id"), primary_key=True)


class StudentSkillMastery(Base):
    __tablename__ = "student_skill_mastery"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id: Mapped[int] = mapped_column(Integer, ForeignKey("skills.id"), nullable=False)
    mastery_level: Mapped[int] = mapped_column(Float, default=0.0)
    p_learn: Mapped[int] = mapped_column(Float)
    p_guess: Mapped[int] = mapped_column(Float)
    p_slip: Mapped[int] = mapped_column(Float)
    last_seen_at: Mapped[int] = mapped_column(DateTime(timezone=True))
    next_review_at: Mapped[int] = mapped_column(DateTime(timezone=True))

    user = relationship("User")
    skill = relationship("Skill")


class UserExperiment(Base):
    __tablename__ = "user_experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    experiment_name: Mapped[int] = mapped_column(String(255), nullable=False)
    variant_name: Mapped[int] = mapped_column(String(255), nullable=False)
    assigned_at: Mapped[int] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
"""
