/**
 * src/types/words.ts
 *
 * Pure TypeScript interfaces.
 * Do NOT include any runtime code (like initial variables or functions) in this file.
 */

// Represents a single Russian word in its dictionary form.
export interface Lemma {
  id: string;
  lemma: string; // e.g., "читать"
  pos: string; // Part of speech, e.g., "VERB"
  frequencyRank?: number; // Optional metadata for distractor generation weighting
}

// Represents a curated curriculum batch.
export interface LessonList {
  id: string;
  name: string; // e.g., "Lesson 4: City Navigation"
  lemmas: Lemma[];
}

// The structural format of the final assessment item.
export type ItemFormat =
  | "MULTIPLE_CHOICE"
  | "FILL_IN_BLANK"
  | "MATCHING"
  | "C_TEST";

// The algorithmic approach for generating incorrect answer options.
export type DistractorStrategy =
  | "MORPHOLOGICAL_PARITY"
  | "FREQUENCY_NEIGHBOR"
  | "SEMANTIC_SIMILARITY"
  | "RANDOM";

// The final configuration payload sent to the backend.
export interface QualityConfig {
  itemFormat: ItemFormat;
  strategy: DistractorStrategy;
  distractorCount: number;
  targetInflectionsOnly: boolean;
}

// The shape of our local UI state during the selection process.
export interface WordSelectionState {
  selectedLessonListIds: string[];
  manualLemmas: Lemma[];
  excludedLemmaIds: string[];
  //   qualities: QualityConfig;
}
