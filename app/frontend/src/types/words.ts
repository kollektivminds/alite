// src/types/words.ts

// Represents a single Russian word in its dictionary form.
export interface Lemma {
  id: string;
  lem_canon: string;
  lem_text: string;
  pos: string;
}

// Represents a curated curriculum batch.
export interface LessonList {
  id: string;
  name: string; // e.g., "Lesson 4: City Navigation"
  has_lemma: Lemma[];
}

// The structural format of the final assessment item.
export type EnumItemFormat = "mcq" | "fitb" | "flashcard" | "unscramble";
export type EnumWordItemGroup =
  | "General"
  | "Adjectives"
  | "Nouns"
  | "Participles"
  | "Verbs";
export type EnumItemDifficulty = "easy" | "medium" | "hard";

export type EnumWordItemType =
  | "LEM_TO_POS"
  | "POS_TO_LEM"
  | "LEM_TO_DEF"
  | "DEF_TO_LEM"
  | "LEM_TO_PRON"
  | "PRON_TO_LEM"
  | "LEM_LEM_TO_REL"
  | "REL_TO_LEM_LEM"
  | "ADJV_FORM_TO_TYPE"
  | "ADJV_TYPE_TO_LEM"
  | "ADJV_FORM_TO_GRAM"
  | "ADJV_GRAM_TO_FORM"
  | "NOUN_TO_GEND"
  | "GEND_TO_NOUN"
  | "NOUN_TO_ANIM"
  | "ANIM_TO_NOUN"
  | "NOUN_FORM_TO_GRAM"
  | "NOUN_GRAM_TO_FORM"
  | "NOUN_TO_DMIN_FORM"
  | "PART_FORM_TO_TYPE"
  | "PART_TYPE_TO_FORM"
  | "VERB_TO_ASPT"
  | "ASPT_TO_VERB"
  | "VERB_PAIR_TO_REL"
  | "VERB_TO_ASPT_PAIR"
  | "VERB_TO_TYPE"
  | "TYPE_TO_VERB"
  | "VERB_TO_CONJ_FORM"
  | "VERB_TO_TNRF"
  | "TNRF_TO_VERB";
export type EnumSentenceItemType =
  | "FILL_IN_THE_FORM"
  | "TAG_METADATA"
  | "UNSCRAMBLE"
  | "FILL_IN_THE_LEMMA";

export type EnumGramExFocus =
  | "SUBST_CASE"
  | "SUBST_GENDER"
  | "SUBST_NUM"
  | "VERB_TENSE"
  | "VERB_PERSON"
  | "VERB_MOOD"
  | "PART_TYPE"
  | "PART_VOICE"
  | "PART_TENSE";

// The final configuration payload sent to the backend.
export interface ExerciseContext {
  lemIds: number[];
  itemFormats: EnumItemFormat[];
  difficulty: EnumItemDifficulty;
  allowOddOneOut: boolean;
  maxKeys: number;
  maxDistractors: number;
}

export interface UIConfigState {
  itemFormat: EnumItemFormat[];
  difficulty: EnumItemDifficulty;
  allowOddOneOut: boolean;
  maxKeys: number;
  maxDistractors: number;
  maxItems: number;
  typeCounts: Record<EnumWordItemType | EnumSentenceItemType, number> | null;
}

export type focusKey = "substantives" | "participles" | "verbs";

type GrammarFocus = Partial<Record<focusKey, EnumGramExFocus[]>>;

export interface ExerciseRequest {
  exerciseContext: ExerciseContext;
  typeCounts: Record<EnumWordItemType | EnumSentenceItemType, number>;
  grammarFocus?: GrammarFocus;
}

// The shape of our local UI state during the selection process.
export interface WordSelectionState {
  selectedLessonListIds: string[];
  manualLemmas: Lemma[];
  excludedLemmaIds: string[];
  qualities: UIConfigState;
}

interface ItemResponse {
  itemFormat: string;
  itemId: number;
  prompt: string;
}

interface FlashcardResponse extends ItemResponse {
  backText: string;
}

interface MCQResponse extends ItemResponse {
  options: string[];
}

interface FITBResponse extends ItemResponse {
  parts: string[];
}

export interface ExerciseResponse {
  exerciseId: number;
  numQuestions: number;
  responseData: Array<FlashcardResponse | MCQResponse | FITBResponse>;
}
