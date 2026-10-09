/**
 * src/types/sentences.ts
 *
 * Frontend domain types matching ALITE backend schemas for sentence-level generation.
 */

import { EnumItemDifficulty, EnumItemFormat } from "./exercise";

export interface SentenceExerciseConfigState {
  difficulty: EnumItemDifficulty;
  maxDistractors: number;
  maxKeys: number;
  allowOddOneOut: boolean;
  itemFormats: EnumItemFormat[];
}

export interface ExerciseContextPayload {
  lem_ids: number[] | null;
  ex_formats: EnumItemFormat[];
  difficulty: EnumItemDifficulty;
  allow_odd_one_out: boolean;
  max_keys: number;
  max_distractors: number;
}

export interface ExerciseRequestPayload {
  exercise_context: ExerciseContextPayload;
  type_counts: Record<string, number>;
  grammar_focus: null;
}

export interface StrategyDefinition {
  id: string;
  labelKey: string;
  descriptionKey: string;
  supportedFormats: EnumItemFormat[];
}

export type EnumSentenceItemType =
  | "noun_morph"
  | "adjective_morph"
  | "verb_morph"
  | "lexical"
  | "dep_rel"
  | "noun_case"
  | "verb_aspect"
  | "find_head"
  | "find_subject"
  | "unscramble";

export interface StrategyDefinition {
  id: string;
  labelKey: string;
  descriptionKey: string;
  supportedFormats: EnumItemFormat[];
}

export interface StrategyGroup {
  groupKey: string;
  strategies: StrategyDefinition[];
}
