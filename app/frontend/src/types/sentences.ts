/**
 * src/types/sentences.ts
 *
 * Frontend domain types matching ALITE backend schemas for sentence-level generation.
 */

import { EnumItemDifficulty, EnumItemFormat } from "./exercise";

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
}

export interface StrategyDefinition {
  id: string;
  labelKey: string;
  descriptionKey: string;
  defaultFormat: EnumItemFormat;
  supportedFormats: EnumItemFormat[];
}

export interface StrategyGroup {
  groupKey: string;
  strategies: StrategyDefinition[];
}
