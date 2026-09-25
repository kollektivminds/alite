// src/types/words.ts

export interface Pronunciation {
  id: number | string;
  pron_text: string;
  pron_type: string;
}

export interface DefinitionItem {
  id: number | string;
  def_text: string;
}

export interface Lemma {
  id: string;
  lem_canon: string;
  lem_text: string;
  pos: string;
  noun_gender?: string;
  noun_animacy?: string;
  verb_aspect?: string;
  pronunciations?: Pronunciation[];
  definitions?: DefinitionItem[];
}

// Represents a curated curriculum batch.
export interface LessonList {
  id: string;
  name: string;
  has_lemma: Lemma[];
}

// The structural format of the final assessment item.
export type EnumWordItemGroup =
  | "General"
  | "Adjectives"
  | "Nouns"
  | "Participles"
  | "Verbs";

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

export type focusKey = "substantives" | "participles" | "verbs";

type GrammarFocus = Partial<Record<focusKey, EnumGramExFocus[]>>;

// The shape of our local UI state during the selection process.
export interface WordSelectionState {
  selectedLessonListIds: string[];
  manualLemmas: Lemma[];
  excludedLemmaIds: string[];
  qualities: UIConfigState;
}

interface ItemResponse {
  item_format: string;
  item_id: number;
  prompt: string;
}

export interface Pronunciation {
  id: number | string;
  pron_text: string;
  pron_type: string;
}

export interface DefinitionItem {
  id: number | string;
  def_text: string;
}

export interface LemmaSearchReturn {
  id: string;
  lem_canon: string;
  lem_text: string;
  pos: string;
  noun_gender?: string;
  noun_animacy?: string;
  verb_aspect?: string;
  pronunciations?: Pronunciation[];
  definitions?: DefinitionItem[];
}
