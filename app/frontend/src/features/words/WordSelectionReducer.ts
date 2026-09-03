// src/features/words/wordSelectionReducer.ts

// Importing the core domain entities we defined for ALITE.
// Ensure this path points to your central types file (e.g., src/types/index.ts)[cite: 3]
import { Lemma, QualityConfig, WordSelectionState } from "../../types";

// 1. Action Definitions
export type WordSelectionAction =
  | { type: "TOGGLE_LESSON_LIST"; payload: string }
  | { type: "TOGGLE_EXCLUDE_LEMMA"; payload: string }
  | { type: "ADD_MANUAL_LEMMA"; payload: Lemma }
  | { type: "REMOVE_MANUAL_LEMMA"; payload: string }
  // Added UPDATE_QUALITIES to handle the psychometric distractor settings.
  // Using Partial<QualityConfig> allows us to update a single setting
  // (like distractorCount) without passing the entire object every time.
  | { type: "UPDATE_QUALITIES"; payload: Partial<QualityConfig> };

// 2. Default Configuration
// Establishing baseline parameters for item generation[cite: 3].
const defaultQualities: QualityConfig = {
  itemFormat: "MULTIPLE_CHOICE",
  strategy: "MORPHOLOGICAL_PARITY",
  distractorCount: 3,
  targetInflectionsOnly: true,
};

// 3. Initial State
export const initialState: WordSelectionState = {
  selectedLessonListIds: [],
  excludedLemmaIds: [],
  manualLemmas: [],
  qualities: defaultQualities, // Hooked up the default qualities
};

// 4. The Pure Reducer Function
export function wordSelectionReducer(
  state: WordSelectionState,
  action: WordSelectionAction,
): WordSelectionState {
  switch (action.type) {
    case "TOGGLE_LESSON_LIST": {
      const isSelected = state.selectedLessonListIds.includes(action.payload);
      return {
        ...state,
        selectedLessonListIds: isSelected
          ? state.selectedLessonListIds.filter((id) => id !== action.payload)
          : [...state.selectedLessonListIds, action.payload],
      };
    }

    case "TOGGLE_EXCLUDE_LEMMA": {
      const isExcluded = state.excludedLemmaIds.includes(action.payload);
      return {
        ...state,
        excludedLemmaIds: isExcluded
          ? state.excludedLemmaIds.filter((id) => id !== action.payload)
          : [...state.excludedLemmaIds, action.payload],
      };
    }

    case "ADD_MANUAL_LEMMA": {
      // Prevent duplicate dictionary forms from skewing the generation pipeline
      if (state.manualLemmas.some((l) => l.id === action.payload.id)) {
        return state;
      }
      return {
        ...state,
        manualLemmas: [...state.manualLemmas, action.payload],
        // Seamlessly clear previous exclusions for the same lemma
        excludedLemmaIds: state.excludedLemmaIds.filter(
          (id) => id !== action.payload.id,
        ),
      };
    }

    case "REMOVE_MANUAL_LEMMA": {
      return {
        ...state,
        manualLemmas: state.manualLemmas.filter((l) => l.id !== action.payload),
      };
    }

    case "UPDATE_QUALITIES": {
      // Merges the existing qualities state with the incoming payload changes
      return {
        ...state,
        qualities: {
          ...state.qualities,
          ...action.payload,
        },
      };
    }

    default:
      return state;
  }
}
