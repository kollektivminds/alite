// /frontend/src/types/exercise.ts
// controlled vocabulary for exercise maker
// aligned with /backend/src/alite_backend/db/models.py
import { EnumSentenceItemType } from "./sentences";
import { EnumWordItemType } from "./words";

export type EnumItemFormat = "mcq" | "fitb" | "flashcard" | "unscramble";
export type EnumItemDifficulty = "easy" | "medium" | "hard";

// Define what settings change based on difficulty
export interface DifficultySettings {
  maxTries: number;
  allowHints: boolean;
  timerMultiplier: number;
}

// The Configuration Map
export const DIFFICULTY_MAP: Record<EnumItemDifficulty, DifficultySettings> = {
  easy: { maxTries: 3, allowHints: true, timerMultiplier: 3 },
  medium: { maxTries: 2, allowHints: true, timerMultiplier: 2 },
  hard: { maxTries: 1, allowHints: false, timerMultiplier: 1 },
};

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

export interface ExerciseRequest {
  exerciseContext: ExerciseContext;
  typeCounts: Record<EnumWordItemType | EnumSentenceItemType, number>;
  grammarFocus?: GrammarFocus;
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
  exercise_id: number;
  num_questions: number;
  response_data: Array<FlashcardResponse | MCQResponse | FITBResponse>;
}

export interface DisplayToken {
  tok_idx: number;
  text: string;
  is_masked: boolean;
  is_punctuation: boolean;
}

export interface UnscrambleToken {
  token_handle: string;
  text: string;
}

// --- Item Deliverable Payloads ---

export interface BaseItemResponse {
  item_id: number;
  prompt: string;
  item_format: EnumItemFormat;
}

export interface FlashcardResponseItem extends BaseItemResponse {
  item_format: "flashcard";
  back_text: string;
}

export interface MCQResponseItem extends BaseItemResponse {
  item_format: "mcq";
  options: (string | number)[];
  sentence_tokens?: DisplayToken[] | null;
}

export interface FITBResponseItem extends BaseItemResponse {
  item_format: "fitb";
  parts: string[];
  sentence_tokens?: DisplayToken[] | null;
}

export interface UnscrambleResponseItem extends BaseItemResponse {
  item_format: "unscramble";
  shuffled_tokens: UnscrambleToken[];
}

export type ExerciseItem =
  | FlashcardResponseItem
  | MCQResponseItem
  | FITBResponseItem
  | UnscrambleResponseItem;

export interface ExerciseResponse {
  exercise_id: number;
  num_questions: number;
  response_data: ExerciseItem[];
}

export interface AttemptRecord {
  itemId: number;
  format: string;
  startTime: number;
  endTime: number | null;
  selectedDistractors: string[];
  isCorrect: boolean;
  finalRating?: string;
  revealedAnswer?: string;
}
