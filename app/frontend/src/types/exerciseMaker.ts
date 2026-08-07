// /frontend/src/types/exerciseMaker.ts
// controlled vocabulary for exercise maker
// aligned with /backend/src/alite_backend/db/models.py

export enum ItemFormat {
  CLOZE = "cloze",
  MCQ = "mcq",
  FLASHCARD = "flashcard",
}

export enum ItemDifficulty {
  EASY = "easy",
  MEDIUM = "medium",
  HARD = "hard",
}

export enum AltAdjvType {
  COMPARATIVE = "comparative",
  SUPERLATIVE = "superlative",
  SHORT = "short",
}

export enum GramGender {
  MASCULINE = "masculine",
  NEUTER = "neuter",
  FEMININE = "feminine",
  DUAL = "dual",
}

export enum GramNum {
  SINGULAR = "singular",
  PLURAL = "plural",
}

export enum GramTense {
  PAST = "past",
  PRESENT = "present",
  FUTURE = "future",
}

export enum PartOfSpeech {
  ADJECTIVE = "adjective",
  ADVERB = "adverb",
  CONJUNCTION = "conjunction",
  INTERJECTION = "interjection",
  NOUN = "noun",
  NUMERAL = "numeral",
  PARTICIPLE = "participle",
  PARTICLE = "particle",
  PREPOSITION = "preposition",
  PRONOUN = "pronoun",
  VERB = "verb",
  UNKNOWN = "unknown",
}

export enum PartType {
  ADJECTIVAL = "adjectival",
  ADVERBIAL = "adverbial",
}

export enum SubstCase {
  NOMINATIVE = "nominative",
  GENITIVE = "genitive",
  ACCUSATIVE = "accusative",
  DATIVE = "dative",
  INSTRUMENTAL = "instrumental",
  PREPOSITIONAL = "prepositional",
  VOCATIVE = "vocative",
  LOCATIVE = "locative",
  PARTITIVE = "partitive",
}

export enum VerbType {
  TYPE_I = "type I",
  TYPE_II = "type II",
}

export enum VerbMood {
  INDICATIVE = "indicative",
  IMPERATIVE = "imperative",
}

export enum VerbAspect {
  IMPERFECTIVE = "imperfective",
  PERFECTIVE = "perfective",
  DUAL = "dual",
}

export enum VerbTransRefl {
  INTRANSITIVE = "intransitive",
  TRANSITIVE = "transitive",
  REFLEXIVE = "reflexive",
}

export enum RelLemTypeGroup {
  SHARED_ROOT = "shared root",
  SEMANTIC = "semantic",
  ASPECTUAL_PAIR = "aspectual pair",
}

export enum PronType {
  ROMANIZATION = "romanization",
  IPA = "ipa",
}

export enum WordItemType {
  // lemmas
  LEM_TO_POS = "lemma -> part of speech",
  POS_TO_LEM = "part of speech -> lemma",
  LEM_TO_DEF = "lemma -> definition",
  DEF_TO_LEM = "definition -> lemma",
  LEM_TO_PRON = "lemma -> pronunciation",
  PRON_TO_LEM = "pronunciation -> lemma",
  LEM_LEM_TO_REL = "lemma + lemma -> relation",
  REL_TO_LEM_LEM = "relation -> lemma + lemma",
  // adjectives
  ADJV_FORM_TO_TYPE = "adjectival form -> type",
  ADJV_TYPE_TO_FORM = "adjectival type -> form",
  ADJV_FORM_TO_GRAM = "adjectival form -> grammar",
  ADJV_GRAM_TO_FORM = "adjectival grammar -> form",
  // nouns
  NOUN_TO_GEND = "noun -> gender",
  GEND_TO_NOUN = "gender -> noun",
  NOUN_TO_ANIM = "noun -> animacy",
  ANIM_TO_NOUN = "animacy -> noun",
  NOUN_FORM_TO_GRAM = "noun form -> grammar",
  NOUN_GRAM_TO_FORM = "noun grammar -> form",
  NOUN_TO_DMIN_FORM = "noun -> diminitive form",
  // participles
  PART_TYPE_TO_FORM = "participle type -> form",
  PART_FORM_TO_TYPE = "participle form -> type",
  // verbs
  VERB_TO_ASPT = "verb -> aspect",
  ASPT_TO_VERB = "aspect -> verb",
  VERB_TO_CONJ_FORM = "verb -> conjugated form",
  VERB_TO_TNRF = "verb -> transitivity / reflexivity",
  TNRF_TO_VERB = "transitivity / reflexivity -> verb",
}

export enum SentItemType {
  FILL_IN_THE_FORM = "fill-in-the-form",
  TAG_METADATA = "tag metadata",
  UNSCRAMBLE = "unscramble",
  FILL_IN_THE_LEMMA = "fill-in-the-lemma",
}
