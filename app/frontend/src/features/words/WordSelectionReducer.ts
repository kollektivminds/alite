// src/features/words/wordSelectionReducer.ts

// importing the core domain entities for ALITE.
import { Lemma, UIConfigState, WordSelectionState } from "../../types";

// action Definitions
export type WordSelectionAction =
  | { type: "TOGGLE_LESSON_LIST"; payload: string }
  | { type: "CLEAR_LESSON_LISTS" }
  | { type: "TOGGLE_EXCLUDE_LEMMA"; payload: string }
  | { type: "ADD_MANUAL_LEMMA"; payload: Lemma }
  | { type: "REMOVE_MANUAL_LEMMA"; payload: string }
  | { type: "UPDATE_QUALITIES"; payload: Partial<UIConfigState> };

// default configuration
export const defaultPanelConfig: UIConfigState = {
  itemFormats: [],
  difficulty: "medium",
  maxKeys: 1,
  maxDistractors: 3,
  maxItems: 10,
  allowOddOneOut: true,
  typeCounts: {},
};

// initial state
export const initialState: WordSelectionState = {
  selectedLessonListIds: [],
  excludedLemmaIds: [],
  manualLemmas: [],
  qualities: defaultPanelConfig,
};

// the pure reducer function
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

    case "CLEAR_LESSON_LISTS": {
      return {
        ...state,
        selectedLessonListIds: [],
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
