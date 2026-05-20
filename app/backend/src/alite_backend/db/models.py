from typing import Optional, List
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
    Enum,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import ARRAY

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


class EnumItemFormat(str, enum.Enum):
    CLOZE = "cloze"
    MCQ = "mcq"
    FLASHCARD = "flashcard"


class EnumWordItemType(str, enum.Enum):
    # --- LEMMAS ---
    # Part of Speech
    # lemmas.lem_canon <-> lemmas.pos
    LEM_TO_POS = "lem_to_pos"  # "What part of speech is X?" (FC/MCQ)
    POS_TO_LEM = "pos_to_lem"  # "Which lemma(s) is/are X?" (FC/MCQ)
    # Definitions
    # lemmas.lem_canon <-> definitions.def_text
    LEM_TO_DEF = "lem_to_def"  # "What is the definition of X?" (FC/MCQ)
    DEF_TO_LEM = "def_to_lem"  # "Which lemma(s) fit the following definition: X?" (MCQ)
    # Pronunciations
    # lemmas.lem_canon <-> pronunciations.pron_text
    LEM_TO_PRON = "lem_to_pron"  # "What is the pronunciation of X?" (MCQ)
    PRON_TO_LEM = "pron_to_lem"  # "What is the correct Russian spelling of the word pronounced 'X'?" (FC/MCQ/Cloze)
    # Lemma Relations
    # lem_rels.source_id(lemmas.lem_canon)
    # + lem_rels.target_id(lemmas.lem_canon)
    # <-> lem_rels.rel_type
    LEM2_TO_LREL = "lem2_to_lrel"  # "How does X relate to Y?" (MCQ)
    LREL_TO_LEM2 = (
        "lrel_to_lem2"
        # "Which of the following pairs is an example of X?" (MCQ)
    )

    # --- VERBS ----
    # Aspect
    # lemmas.filter(pos==verb).lem_canon <-> lemmas(id=lem_id).filter(pos==verb).verb_aspect
    VERB_TO_ASPT = "verb_to_aspt"  # "What is the aspect of [verb]?" (FC/MCQ)
    # lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[source_id, target_id].lem_canon
    # <-> lemmas(id=lem_id).verb_aspect
    VERB_PAIR_TO_REL = "verb_pair_to_rel"  # "Which of these verbs is [aspect]?" (MCQ)
    # lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[source_id].lem_canon
    # <-> lem_rels(rel_type=IMPERFECTIVE/PERFECTIVE).[target_id].lem_canon
    VERB_ASPT_TO_PAIR = (
        "verb_to_aspt_pair"  # "What is the aspectual partner of [verb]?" (FC/MCQ/Cloze)
    )
    # Conjugation Type
    # lemmas.filter(pos==verb).lem_canon <-> lemmas.filter(pos==verb).verb_type
    LEM_TO_VTYP = "lem_to_vtyp"  # "What type of verb is X?" (MCQ)
    VTYP_TO_LEM = "vtyp_to_lem"  # "Which lemma(s) is/are type X?" (MCQ)
    # Conjugation Forms (tense, number, gender, person, mood)
    # word_forms[gram_id=gram_props.[gram_tense, gram_num, gram_gender, conj_person, verb_mood]].lem_id[pos=PRONOUN].lem_canon
    # + lemmas.filter(pos==verb).lem_canon
    # <-> word_forms(lem_id=lem, gram_id=gram_prop).lex_id.lex_text
    PRON_INFV_TO_VERB_CONJ = (
        "pron_infv_to_verb_conj"  # "What is the X form of Y?" (MCQ/Cloze)
    )
    VERB_CONJ_TO_PRON_INFV = "verb_conj_to_pron_infv"  # "What form of what infinitive verb is [verb lexeme]?" (MCQ)
    # Transitivity & Reflexivity
    # lemmas.filter(pos==verb).lem_canon
    # <-> lemmas.filter(pos==verb).verb_trans_refl
    LEM_TO_VTR = "lem_to_vtr"  # "Is X transitive, reflexive, or neither?" (MCQ)
    VTR_TO_LEM = "vtr_to_lem"  # "Which lemma(s) is/are X?" (MCQ)

    # --- SUBSTANTIVES ---
    # Adjectival, Nominal, and Pronominal Inflections
    # word_forms(gram_props[])
    FORM_LEM_TO_GNC = "subst_to_gnc"  # "What is the [gender / number / case] of [noun / pronoun / adjective]?" (MCQ)
    LEM_GNC_TO_FORM = (
        "subst_to_form"  # "What is the [gnc] form of [lemma]?" (MCQ/Cloze)
    )

    # --- ADJECTIVES ---
    # lemma (adjective) <-> comparative / superlative form
    LEM_TO_ADJV_FORM = "lem_to_adjv_form"  # "What is the Y form of X?" (MCQ)
    ADJV_FORM_TO_LEM = "adjv_form_to_lem"  # "What is the base form of X?" (MCQ/Cloze)
    # adjective form <-> adjective type
    ADJV_FORM_TO_TYPE = "adjv_to_type"  # "What kind of adjective is X?" (MCQ)
    TYPE_TO_ADJV_FORM = "type_to_adjv"  # "Which of the following adjectives is/are an example of X?" (MCQ)

    # --- NOUNS ---
    # lemma (noun) <-> gender
    LEM_TO_GEND = "lem_to_gender"  # "What gender is X?" (MCQ)
    GEND_TO_LEM = "gender_to_lem"  # "Which lemma(s) is/are X?" (MCQ)
    # lemma (noun) <-> animacy (bool)
    LEM_TO_ANIM = "lem_to_anim"  # "Is X animate or inanimate?" (MCQ)
    ANIM_TO_LEM = "anim_to_lem"  # "Which lemma(s) is/are in/animate?" (MCQ)

    # --- PARTICIPLES ---
    # participle <-> type
    PART_TO_TYPE = "part_to_type"  # "What type of participle is X?" (MCQ)
    TYPE_TO_PART = "type_to_part"  # "What form is type X?" (MCQ)


class EnumSentItemType(str, enum.Enum):
    # how to organize these items?
    pass


class EnumItemDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    DIFFICULT = "difficult"


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    in_less_list = relationship(
        "LessonList", secondary="lems_in_less_lists", back_populates="has_lemma"
    )
    in_item = relationship("Item", secondary="lems_in_items", back_populates="ref_lems")
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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    gram_gender = Column(Enum(EnumGender), nullable=True)
    conj_person = Column(Enum(EnumConjPerson), nullable=True)
    verb_mood = Column(Enum(EnumVerbMood), nullable=True)
    # Substantives (nouns, adjectives, numerals, participles)
    subst_case = Column(Enum(EnumSubstCase), nullable=True)
    alt_adjv_type = Column(Enum(EnumAltAdjvType), nullable=True)
    alt_noun_type = Column(Enum(EnumAltNounType), nullable=True)
    # Participles
    part_type = Column(Enum(EnumParticipleType), nullable=True)
    part_voice = Column(Enum(EnumParticipleVoice), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationship for a word form's grammatical properties
    gram_word_form = relationship("WordForm", back_populates="word_form_gram")
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


# TODO: go through everything after this to correspond with init_db.sql
class WordForm(Base):
    """The central junction table linking a lemma to a lexicon entry with specific properties."""

    __tablename__ = "word_forms"

    id = Column(Integer, primary_key=True)
    lem_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    lex_id = Column(Integer, ForeignKey("lexicon.id"), nullable=False)
    gram_id = Column(Integer, ForeignKey("gram_props.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    word_form_lemma = relationship("Lemma", back_populates="lemma_word_form")
    word_form_lexicon = relationship("Lexeme", back_populates="lexeme_word_form")
    word_form_gram = relationship("GramProp", back_populates="gram_word_form")


class Definition(Base):
    __tablename__ = "definitions"

    id = Column(Integer, primary_key=True)
    def_text = Column(String, unique=True, nullable=False)
    def_tags = Column(ARRAY(String), nullable=True)

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    example_definition = relationship(
        "DefinitionExample", back_populates="example_definition"
    )


class Pronunciation(Base):
    __tablename__ = "pronunciations"

    id = Column(Integer, primary_key=True)
    pron_text = Column(String, unique=True, nullable=False)
    pron_tags = Column(ARRAY(String), nullable=True)
    pron_type = Column(Enum(EnumPronType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# --- Word Junction Tables ---


class LemmaRelation(Base):
    """Junction table for relating lemmas to each other"""

    __tablename__ = "lem_rels"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    rel_type = Column(Enum(EnumRelLemType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    source_lemma = relationship(
        "Lemma", foreign_keys=[source_id], back_populates="related_to"
    )
    target_lemma = relationship(
        "Lemma", foreign_keys=[target_id], back_populates="related_from"
    )


class LookupQueue(Base):

    __tablename__ = "lookup_queue"

    id = Column(Integer, primary_key=True, index=True)
    target_lem = Column(String(50), nullable=False)
    target_id = Column(Integer, ForeignKey("lemmas.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("lemmas.id"), nullable=True)
    rel_type = Column(Enum(EnumRelLemType), nullable=False)
    lookup_status = Column(
        Enum(EnumLookupStatus), nullable=False, default=EnumLookupStatus.UNLINKED
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class LemmaDefinition(Base):
    """Junction table for lemma definitions."""

    __tablename__ = "lem_defs"

    lem_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    def_id = Column(Integer, ForeignKey("definitions.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    definition_example = relationship(
        "Definition", foreign_keys=[def_id], back_populates="definition_example"
    )
    example_definition = relationship(
        "Example", foreign_keys=[ex_id], back_populates="example_definition"
    )


# --- Lemma Container Organization Tables ---


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String(10), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    has_less_list = relationship("LessonListInModule", back_populates="in_module")


class LessonList(Base):
    __tablename__ = "lessons_lists"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), nullable=False, unique=True)
    topic = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    in_module = relationship("LessonListInModule", back_populates="less_list_in")
    has_lemma = relationship(
        "Lemma", secondary="lems_in_less_lists", back_populates="in_less_list"
    )


# --- Secondary Organization Tables ---


class LemmaInLessonList(Base):
    __tablename__ = "lems_in_less_lists"

    lem_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    less_list_id = Column(Integer, ForeignKey("lessons_lists.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # lemma_in = relationship("Lemma", back_populates="in_less_list")
    # in_less_list = relationship("LessonList", back_populates="has_lemma")


class LessonListInModule(Base):
    """Junction table for lessons and modules"""

    __tablename__ = "less_lists_in_mods"

    less_list_id = Column(Integer, ForeignKey("lessons_lists.id"), primary_key=True)
    mod_id = Column(Integer, ForeignKey("modules.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    less_list_in = relationship("LessonList", back_populates="in_module")
    in_module = relationship("Module", back_populates="has_less_list")


# --- Sentence Tables ---


# class Sentence(Base):
#     ___tablename__ = "sentences"

#     id = Column(Integer, primary_key=True)
#     raw_text = Column(Text, nullable=False)

#     tokens = relationship(
#         "SentenceToken",
#         back_populates="sentence",
#         order_by="SentenceToken.position_index",  # Guarantees order when fetched!
#         cascade="all, delete-orphan",
#     )


# class WordFormInSentence(Base):
#     """Junction table mapping a WordForm to a specific position in a Sentence."""

#     __tablename__ = "word_forms_in_sentences"

#     id = Column(Integer, primary_key=True)
#     sentence_id = Column(
#         Integer, ForeignKey("sentences.id", ondelete="CASCADE"), nullable=False
#     )
#     word_form_id = Column(Integer, ForeignKey("word_forms.id"), nullable=False)

#     position_index = Column(Integer, nullable=False)

#     # context-specific lexeme orthography
#     is_capitalized = Column(Boolean, default=False)
#     punctuation_after = Column(String(5), nullable=True)
#     punctuation_before = Column(String(5), nullable=True)

#     # relationships
#     sentence = relationship("Sentence", back_populates="tokens")
#     word_form = relationship("WordForm")


# --- Sentence Organization Tables ---


# class Document(Base):
#     __tablename__ = "documents"

#     id = Column(Integer, primary_key=True)
#     author = Column(String(48), nullable=False)
#     date = Column(DateTime, nullable=True)
#     source = Column(Text, nullable=False)
#     title = Column(String(48), nullable=False)
#     created_at = Column(DateTime(timezone=True), server_default=func.now())

#     sentences = relationship("Sentence", back_populates="in_document")


# --- Users ---


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=True)
    alias = Column(String(25), unique=False, nullable=True)
    user_role = Column(Enum(EnumUserRole))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    in_group = relationship("UserInGroup", back_populates="group_user")
    exercises = relationship("Items", back_populates="user")


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    group_name = Column(String(50), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserInGroup", back_populates="user_group")


class UserInGroup(Base):
    __tablename__ = "users_in_groups"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("user_groups.id"), primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    group_user = relationship("User", back_populates="in_group")
    user_group = relationship("UserGroup", back_populates="users")


# --- Questions, Sessions, and Responses ---


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    item_type = Column(String(48), nullable=False)
    prompt = Column(Text, nullable=False)
    settings = Column(JSON, nullable=False)
    key = Column(Text, nullable=False)
    distractors = Column(ARRAY(String), nullable=True)
    difficulty = Column(Enum(EnumItemDifficulty), nullable=True)
    # TODO: set up to record times
    start_time = Column(DateTime(timezone=True))
    finish_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    reponses = relationship("ItemResponse", back_populates="item")
    ref_lems = relationship(
        "Lemma", secondary="lems_in_items", back_populates="in_item"
    )
    in_ex = relationship(
        "Exercise", secondary="items_in_exercises", back_populates="has_item"
    )


class LemmaInItem(Base):
    __tablename__ = "lems_in_items"

    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    lem_id = Column(
        Integer, ForeignKey("lemmas.id", ondelete="CASCADE"), primary_key=True
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # TODO: set this up to start at load
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    has_item = relationship
    user = relationship("User", back_populates="exercises")


class ItemInExercise(Base):
    __tablename__ = "items_in_exercises"

    item_id = Column(
        Integer, ForeignKey("items.id", ondelete="CASCADE"), primary_key=True
    )
    ex_id = Column(
        Integer, ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True
    )


class ItemResponse(Base):
    __tablename__ = "student_responses"

    id = Column(Integer, primary_key=True)
    ex_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("items.id"), nullable=False)
    student_answer = Column(Text, nullable=False)
    response_time_ms = Column(Integer)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    exercise = relationship("Exercise", back_populates="responses")
    item = relationship("Item", back_populates="responses")


"""
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
