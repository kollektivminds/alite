from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Boolean,
    DateTime,
    Text,
    create_engine,
    UniqueConstraint,
    JSON
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

# This is the base class which our ORM models will inherit from
Base = declarative_base()

# --- Word Primary Tables ---
class Lexeme(Base):
    """Represents a unique word string as it appears in a text."""

    __tablename__ = "lexicon"

    id = Column(Integer, primary_key=True)
    word_text = Column(String(50), nullable=False, unique=True)

    word_forms = relationship("WordForm", back_populates="lexicon_entry")


class Lemma(Base):
    """Represents a dictionary base form (lemma) of a word."""

    __tablename__ = "lemmas"

    id = Column(Integer, primary_key=True)
    # text of the lemma
    lemma_text = Column(String(50), nullable=False)
    # part of speech of the lemma
    part_of_speech = Column(Integer, nullable=False)

    # A single lemma has many inflected word forms
    word_forms = relationship("WordForm", back_populates="lemma")
    # Relationships for verb aspect pairs as keys in VerbPair
    imperfective_pairs = relationship(
        "VerbPair",
        foreign_keys="[VerbPair.imperfective_verb_id]",
        back_populates="imperfective_verb",
    )
    perfective_pairs = relationship(
        "VerbPair",
        foreign_keys="[VerbPair.perfective_verb_id]",
        back_populates="perfective_verb",
    )
    # Relationship for parent verbs of participles
    parent_verb = relationship("ParentVerb", back_populates="parent_verb")
    # Relationship for lemma defintion
    lemma_definition = relationship(
        "LemmaDefinition", back_populates="definition_lemma"
    )
    # Relationships for study results
    lemma_crws = relationship(
        "ConjugationResultWordStudied", back_populates="crws_lemma"
    )
    lemma_drws = relationship(
        "DeclensionResultWordStudied", back_populates="drws_lemma"
    )
    # Unique pair of "lemma_text" and "part_of_speech" to prevent duplicates
    __table_args__ = (
        UniqueConstraint("lemma_text", "part_of_speech", name="unique_lemma"),
    )
    in_list = relationship("WordInList", back_populates="word_in")
    in_lesson = relationship("WordInLesson", back_populates="word_in")


class GrammaticalProperty(Base):
    """Represents a unique combination of grammatical properties."""

    __tablename__ = "gram_props"

    id = Column(Integer, primary_key=True)

    # Various grammatical properties that can potentially apply,
    # though table will be largely sparse

    # Verbs
    verb_aspect = Column(Integer)
    verb_conj = Column(String(4))
    verb_conj_type = Column(String(50))
    verb_mood = Column(Integer)
    verb_trans_refl = Column(Integer)
    verb_reflexive = Column(Boolean)
    verb_transitive = Column(Boolean)
    verb_conj_person = Column(Integer)
    verb_conj_tense = Column(Integer)
    # Participles
    part_type = Column(Integer)
    part_voice = Column(Integer)
    part_parent_verb_id = Column(Integer, ForeignKey("lemmas.id"))
    # Substantives (nouns, adjectives, numerals, participles)
    adjv_short = Column(Boolean)
    subst_case = Column(Integer)
    subst_animacy = Column(Boolean)
    gram_gender = Column(Integer)
    gram_number = Column(Integer)
    # Relationship for lemma's parent verb as Lemma.id
    part_parent_verb = relationship(
        "Lemma", foreign_keys="[Lemma.id]", back_populates="parent_verb"
    )
    # Relationship for a word form's grammatical properties
    gram_word_form = relationship(
        "WordForm", foreign_keys="[WordForm.id]", back_populates="word_form_gram"
    )
    # Unique set of grammatical properties to prevent duplicates
    __table_args__ = (
        UniqueConstraint(
            "verb_aspect",
            "verb_conj",
            "verb_conj_type",
            "verb_conj_person",
            "verb_conj_tense",
            "verb_mood",
            "verb_reflexive",
            "verb_transitive",
            "part_type",
            "part_voice",
            "adjv_short",
            "subst_case",
            "subst_animacy",
            "gram_gender",
            "gram_number",
            name="unique_grammar",
        ),
    )


# TODO: go through everything after this to correspond with init_db.sql
class WordForm(Base):
    """The central junction table linking a lemma to a lexicon entry with specific properties."""

    __tablename__ = "word_forms"

    id = Column(Integer, primary_key=True)
    lemma_id = Column(Integer, ForeignKey("lemmas.id"), nullable=False)
    lexicon_id = Column(Integer, ForeignKey("lexicon.id"), nullable=False)
    grammar_id = Column(Integer, ForeignKey("gram_props.id"), nullable=False)

    word_form_lemma = relationship("Lemma", back_populates="lemma_word_form")
    word_form_lexicon = relationship("Lexicon", back_populates="lexicon_word_form")
    word_form_gram = relationship(
        "GrammaticalProperty", back_populates="gram_word_form"
    )


class Definition(Base):
    __tablename__ = "definitions"

    id = Column(Integer, primary_key=True)
    definition_text = Column(String, unique=True, nullable=False)

    definition_lemma = relationship(
        "LemmaDefinition", back_populates="lemma_definition"
    )


# --- Word Junction Tables ---


class VerbPair(Base):
    """Junction table for imperfective/perfective verb pairs."""

    __tablename__ = "verb_pairs"

    imperfective_verb_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    perfective_verb_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)

    imperfective_verb = relationship(
        "Lemma",
        foreign_keys=[imperfective_verb_id],
        back_populates="imperfective_pairs",
    )
    perfective_verb = relationship(
        "Lemma", foreign_keys=[perfective_verb_id], back_populates="perfective_pairs"
    )


class LemmaDefinition(Base):
    """Junction table for lemma definitions."""

    __tablename__ = "lemma_defs"

    lemma_id = Column(Integer, ForeignKey("lemmas.id"), primary_key=True)
    definition_id = Column(Integer, ForeignKey("definitions.id"), primary_key=True)

    lemma_definition = relationship("Lemma", back_populates="word_definition")
    definition_lemma = relationship("Definition", back_populates="definition_word")


# --- Lemma Container Organization Tables ---


class Module(Base):
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    module_name = Column(String(10), nullable=False)

    with_lesson = relationship("LessonInModule", back_populates="in_module")

class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    lesson_name = Column(String(50), nullable=False)
    lesson_topic = Column(String, nullable=False)

    has_word = relationship("ListInLesson", back_populates="in_lesson")
    in_module = relationship("LessonInModule", back_populate="lesson_in")

class WordList(Base):
    __tablename__ = "word_lists"

    id = Column(Integer, primary_key=True)
    list_name = Column(String(50), nullable=False)

    with_word = relationship("WordInList", back_populates="in_list")
    in_lesson = relationship("ListInLesson", back_populates="list_in")

# --- Secondary Organization Tables ---

class LessonInModule(Base):
    __table__ = "lessons_in_modules"

    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    module_id = Column(Integer, ForeignKey("modules.id"))

    lesson_in = relationship(
        "Lesson", foreign_keys="[lessons.id]", back_populates="in_module"
        )
    in_module = relationship(
        "Module", foreign_keys="[modules.id]", back_populates="with_lesson"
        )

class WordInLesson(Base):
    __tablename__ = "words_in_lessons"

    word_id = Column(Integer, ForeignKey("lemmas.id"))
    lesson_id = Column(Integer, ForeignKey("lessons.id"))

    word_in = relationship(
        "Lemma", foreign_keys="[lemmas.id]", back_populates="in_lesson"
    )
    in_lesson = relationship(
        "Lesson", foreign_keys="[lessons.id]", back_populates="has_word"
    )

class WordInList(Base):
    __tablename__ = "words_in_lists"

    word_id = Column(Integer, ForeignKey("lemmas.id"))
    list_id = Column(Integer, ForeignKey("word_lists.id"))

    word_in = relationship(
        "Lemma", foreign_keys="[lemmas.id]", back_populates="in_list"
    )
    in_list = relationship(
        "WordList", foreign_keys="[word_lists.id]", back_populates="with_word"
    )

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

    user_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("user_groups.id"))

    group_user = relationship("User", back_populates="in_group")
    user_group = relationship("UserGroup", back_populates="users")


# --- Questions, Sessions, and Responses ---

class Question(Base):
    __tablename__ = 'questions'

    id = Column(Integer, primary_key=True)
    question_type = Column(String(50), nullable=False)
    question_text = Column(Text, nullable=False)
    choices = Column(JSON) # Using JSONB for flexibility
    correct_answer = Column(Text, nullable=False)
    lemma_id = Column(Integer, ForeignKey('lemmas.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    lemma = relationship("Lemma")


class QuestionSession(Base):
    __tablename__ = 'question_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_start_time = Column(DateTime(timezone=True), server_default=func.now())
    session_end_time = Column(DateTime(timezone=True))

    user = relationship("User")
    responses = relationship("StudentResponse", back_populates="session")


class StudentResponse(Base):
    __tablename__ = 'student_responses'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('question_sessions.id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    student_answer = Column(Text)
    is_correct = Column(Boolean)
    response_time_ms = Column(Integer)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("QuestionSession", back_populates="responses")
    question = relationship("Question")


class StudentDecision(Base):
    __tablename__ = 'student_decisions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    decision_type = Column(String(100), nullable=False)
    decision_value = Column(Text, nullable=False)
    made_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    
class Skill(Base):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True)
    skill_name = Column(String(255), nullable=False, unique=True)
    skill_description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SkillInQuestion(Base):
    __tablename__ = 'question_skills'

    question_id = Column(Integer, ForeignKey('questions.id'), primary_key=True)
    skill_id = Column(Integer, ForeignKey('skills.id'), primary_key=True)

class StudentSkillMastery(Base):
    __tablename__ = 'student_skill_mastery'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    mastery_level = Column(Float, default=0.0)
    p_learn = Column(Float)
    p_guess = Column(Float)
    p_slip = Column(Float)
    last_seen_at = Column(DateTime(timezone=True))
    next_review_at = Column(DateTime(timezone=True))

    user = relationship("User")
    skill = relationship("Skill")
    
class UserExperiment(Base):
    __tablename__ = 'user_experiments'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    experiment_name = Column(String(255), nullable=False)
    variant_name = Column(String(255), nullable=False)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")