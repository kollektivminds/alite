// /frontend/src/types/exercise.ts
// controlled vocabulary for exercise maker
// aligned with /backend/src/alite_backend/db/models.py

export const ITEM_FORMAT = [
  "fill-in-the-blank",
  "multiple choice",
  "flashcard",
] as const;

export type ItemFormat = (typeof ITEM_FORMAT)[number];

export type StrategyCategory = 'general' | 'adjectives' | 'nouns' | 'participles' | 'verbs';

export interface StrategyMetadata {
  id: WordItemStrategy;
  label: string;
  description: string; // Used for the Tooltip
  category: StrategyCategory;
  reversible: boolean;
}

export const ITEM_STRATEGY_REGISTRY: Record<WordItemStrategy, StrategyMetadata> = {
  lem_to_pos: {
    id: 'lem_to_pos',
    label: 'word ↔ part of speech',
    description: 'Tests identification of part of speech of a given word.',
    category: 'general',
    reversible: true,
  },
  lem_to_def: {
    id: 'lem_to_def',
    label: 'word ↔ definition',
    description: 'Tests identification of definition of a given word.',
    category: 'general',
    reversible: true,
  },
  lem_to_pron: {
    id: 'lem_to_pron',
    label: 'word ↔ pronunciation',
    description: 'Tests identification of part of speech of a given word.',
    category: 'general',
    reversible: true,
  },
  lem_lem_to_rel: {
    id: 'lem_lem_to_rel',
    label: '2 words ↔ relationship',
    description: 'Tests identification of part of speech of a given word.',
    category: 'general',
    reversible: true,
  },
  adjv_form_to_type: {
    id: 'adjv_form_to_type',
    label: 'adjective form ↔ comparative / superlative',
    description: 'Tests identification of part of speech of a given word.',
    category: 'adjectives',
    reversible: true,
  },
  adjv_form_to_gram: {
    id: 'adjv_form_to_gram',
    label: 'adjective form ↔ grammar type',
    description: 'Tests identification of part of speech of a given word.',
    category: 'adjectives',
    reversible: true,
  },
  noun_to_gend: {
    id: 'noun_to_gend',
    label: 'noun ↔ gender',
    description: 'Tests identification of gender of a given noun.',
    category: 'nouns',
    reversible: true,
  },
}

export const WORD_ITEM_STRATEGIES = [
  // lemmas
  "lem_to_pos",
  "pos_to_lem",
  "lem_to_def",
  "def_to_lem",
  "lem_to_pron",
  "pron_to_lem",
  "lem_lem_to_rel",
  "rel_to_lem_lem",
  // adjectives
  "adjv_form_to_type",
  "adjv_type_to_form",
  "adjv_form_to_gram",
  "adjv_gram_to_form",
  // nouns
  "noun_to_gend",
  "gend_to_noun",
  "noun_to_anim",
  "anim_to_noun",
  "noun_form_to_gram",
  "noun_gram_to_form",
  "noun_to_dmin_form",
  // participles
  "part_type_to_form",
  "part_form_to_type",
  // verbs
  "verb_to_aspt",
  "aspt_to_verb",
  "verb_to_conj_form",
  "verb_to_tnrf",
  "tnrf_to_verb",
] as const;

export type WordItemStrategy = (typeof WORD_ITEM_STRATEGIES)[number];

export const SENT_ITEM_STRATEGIES = [
  "fill_in_the_form",
  "tag_metadata",
  "unscramble",
  "fill_in_the_lemma",
] as const;

export type SentItemStrategy = (typeof SENT_ITEM_STRATEGIES)[number];
