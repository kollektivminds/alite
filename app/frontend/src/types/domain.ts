/**
 *
 * core domain entities for ALITE
 *
 **/

/**
 * api read responses
 */

// types.ts
export interface Lemma {
  id: string;
  lemma: string; // Russian dictionary form (e.g., "читать")
  pos: string; // Part of speech (e.g., "VERB")
  frequencyRank?: number;
}

export interface LessonList {
  id: string;
  name: string;
  lemmas: Lemma[];
}

export type ItemFormat =
  | "MULTIPLE_CHOICE"
  | "FILL_IN_BLANK"
  | "MATCHING"
  | "FLASHCARD";
export type DistractorStrategy =
  | "MORPHOLOGICAL_PARITY"
  | "FREQUENCY_NEIGHBOR"
  | "RANDOM";

export interface QualityConfig {
  itemFormat: ItemFormat;
  strategy: DistractorStrategy;
  distractorCount: number;
  targetInflectionsOnly: boolean;
}

export interface WordSelectionState {
  selectedLessonListIds: string[];
  manualLemmas: Lemma[];
  excludedLemmaIds: string[];
  qualities: QualityConfig;
}

export interface LemmaDetailsReturn {
  id: number;
  lemText: string;
  lemCanon?: string;
  pos: PartOfSpeech;
  nounGender?: GramGender;
  nounAnimacy?: boolean;
  verbAspect?: VerbAspect;
  verbConj?: string;
  verbType?: VerbType;
  verbTransRefl?: VerbTransRefl;
  createdAt: string;
}

export interface LexemeReturn {
  id: number;
  lexText: string;
  lexTextClean: string;
  createdAt: string;
}

export interface GramPropReturn {
  id: number;
  gramTense?: GramTense;
  gramNum?: GramNum;
  gramGender?: GramGender;
  conjPerson?: string;
  verbMood?: VerbMood;
  substCase?: SubstCase;
  altAdjvType?: AltAdjvType;
  altBounType?: AltNounType;
  partType?: PartType;
  partVoice?: PartVoice;
  createdAt: string;
}

export interface WordFormReturn {
  id: number;
  lem: LemmaDetailsReturn;
  lex: LexemeReturn;
  gram: GramPropReturn;
}

export interface DefinitionReturn {
  id: number;
  defText: string;
  defTags: string[];
  createdAt: string;
}

export interface ExampleReturn {
  id: number;
  exText: string;
  createdAt: string;
}

export interface PronunciationReturn {
  id: number;
  pronText: string;
  pronTags?: string[];
  createdAt: string;
}

export interface LemRelReturn {
  id: number;
  target: string;
  source: string[];
  relType: RelType;
  createdAt: string;
}

export interface UserReturn {
  id: number;
  username: string;
  email: string;
  alias?: string;
  createdAt: string;
}

export interface UserGroupReturn {
  id: number;
  group_name: string;
  createdAt: string;
}

export interface ModuleReturn {
  id: number;
  module_name: string;
  createdAt: string;
}

export interface LessonListReturn {
  id: number;
  title: string;
  topic?: string;
  owner: UserReturn;
  createdAt: string;
}

export interface DocumentReturn {
  id: number;
  title: string;
  author?: string;
  source?: string;
  date?: string;
  createdAt: string;
}

export interface SentenceReturn {
  id: number;
  rawText: string;
  sentIdx: number;
  createdAt: string;
}

/**
 * api request payloads
 */

/**
 * frontend ui state
 */

/**
 * supporting data types
 */

export const ALT_ADJV_TYPE = ["comparative", "superlative", "short"] as const;

export type AltAdjvType = (typeof ALT_ADJV_TYPE)[number];

export const ALT_NOUN_TYPE = [
  "diminutive",
  "augmentative",
  "collective",
  "paucal",
  "pejorative",
] as const;

export type AltNounType = (typeof ALT_NOUN_TYPE)[number];

export const CONJ_PERSON = ["first", "second", "third"] as const;

export type ConjPerson = (typeof CONJ_PERSON)[number];

export const GRAM_NUM = ["singular", "plural"] as const;

export type GramNum = (typeof GRAM_NUM)[number];

export const GRAM_TENSE = ["past", "present", "future"] as const;

export type GramTense = (typeof GRAM_TENSE)[number];

export const GRAM_GENDER = ["masculine", "neuter", "feminine", "dual"] as const;

export type GramGender = (typeof GRAM_GENDER)[number];

export const ITEM_DIFFICULTY = ["easy", "medium", "hard"] as const;

export type ItemDifficulty = (typeof ITEM_DIFFICULTY)[number];

export const PART_OF_SPEECH = [
  "adjective",
  "adverb",
  "conjunction",
  "interjection",
  "noun",
  "numeral",
  "participle",
  "particle",
  "preposition",
  "pronoun",
  "verb",
  "unknown",
] as const;

export type PartOfSpeech = (typeof PART_OF_SPEECH)[number];

export const PART_TYPE = ["adjectival", "adverbial"] as const;

export type PartType = (typeof PART_TYPE)[number];

export const PART_VOICE = ["active", "passive"] as const;

export type PartVoice = (typeof PART_VOICE)[number];

export const SUBST_CASE = [
  "nominative",
  "genitive",
  "accusative",
  "dative",
  "instrumental",
  "prepositional",
  "vocative",
  "locative",
  "partitive",
] as const;

export type SubstCase = (typeof SUBST_CASE)[number];

export const PRON_TYPE = ["romanization", "ipa"] as const;

export type PronType = (typeof PRON_TYPE)[number];

export const REL_TYPE = [
  "adjective_of",
  "abstract-noun_of",
  "adverb_of",
  "relational-adjective_of",
  "noun-from-verb_of",
  "perfective-pair_of",
  "imperfective-pair_of",
  "synonym_of",
  "antonym_of",
];

export type RelType = (typeof REL_TYPE)[number];

export const REL_LEM_TYPE_GROUP = [
  "shared root",
  "semantic",
  "aspectual pair",
] as const;

export type RelLemTypeGroup = (typeof REL_LEM_TYPE_GROUP)[number];

export const VERB_ASPECT = ["imperfective", "perfective", "dual"] as const;

export type VerbAspect = (typeof VERB_ASPECT)[number];

export type VerbTransRefl = (typeof VERB_TRANS_REFL)[number];

export const VERB_TYPE = ["type I", "type II"] as const;

export type VerbType = (typeof VERB_TYPE)[number];

export const VERB_TRANS_REFL = [
  "intransitive",
  "transitive",
  "reflexive",
] as const;

export const VERB_MOOD = ["indicative", "imperative"] as const;

export type VerbMood = (typeof VERB_MOOD)[number];

/**
 * db tables
 */

// lemmas
export interface Lemma {
  id: string;
  entryKey: string;
  lemText: string;
  lemCanon?: string;
  pos: string;
  nounGender: GramGender;
  nounAnimacy: boolean;
  verbAspect: VerbAspect;
  verbConj: string;
  verbType: VerbType;
  verbTrans_refl: VerbTransRefl;
  createdAt: string;
}

// lexicon
export interface Lexeme {
  id: number;
  lexText: string;
  lexTextClean: string;
  createdAt: string;
}

// gram_props
export interface GramProp {
  id: number;
  irregular: boolean;
  gramTense: GramTense;
  gramNum: GramNum;
  gramGender: GramGender;
  conjPerson: ConjPerson;
  verbMood: VerbMood;
  substCase: SubstCase;
  altAdjvType: AltAdjvType;
  altNounType: AltNounType;
  partType: PartType;
  partVoice: PartVoice;
  createdAt: string;
}

// word_forms
export interface WordForm {
  id: number;
  wordFormLemma: Lemma;
  wordFormLexicon: Lexeme;
  wordFormGram: GramProp;
  createdAt: string;
}

// definition
export interface Definition {
  id: number;
  defText: string;
  defTags?: string;
  createdAt: string;
}

// example
export interface Example {
  id: number;
  exText: string;
  createdAt: string;
}

// pronunciation
export interface Pronunciation {
  id: number;
  pronText: string;
  pronTags?: string;
  pronType: PronType;
  createdAt: string;
}

// lem_rels
export interface LemRel {
  id: number;
  sourceLemma: string;
  targetLemma: string;
  relType: RelType;
  createdAt: string;
}

// modules
export interface Module {
  id: number;
  moduleName: string;
  createdAt: string;
}

// lesson_lists
export interface LessonList {
  id: string;
  title: string;
  topic?: string;
  createdAt: string;
}

// sentences
export interface Sentence {
  id: number;
  rawText: string;
  sentIdx: number;
  document: Document;
  tokens: SentenceToken[];
  createdAt: string;
}

// sentence_tokens
export interface SentenceToken {
  id: number;
  sentId: number;
  tokenIdx: number;
  lexRaw: string;
  lemRaw: string;
  features: Record<string, unknown>;
  createdAt: string;
}

// documents
export interface Document {
  id: number;
  title: string;
  author?: string;
  source?: string;
  date?: string;
  createdAt: string;
}
