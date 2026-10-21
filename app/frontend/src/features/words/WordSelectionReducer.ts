// src/features/words/WordSelectionReducer.ts
import { Lemma } from "../../types";
import { ExerciseConfigState } from "./wordsExerciseConfigPanel";

export interface WordSelectionState {
  selectedLessonListIds: string[];
  manualLemmas: Lemma[];
  excludedLemmaIds: string[];
  // qualities holds the full configuration state for exercise generation
  qualities: ExerciseConfigState;
}

export type WordSelectionAction =
  | { type: "TOGGLE_LESSON_LIST"; payload: string }
  | { type: "CLEAR_LESSON_LISTS" }
  | { type: "RESET_ALL" }
  | { type: "SET_LESSON_LISTS"; payload: string[] }
  | { type: "ADD_MANUAL_LEMMA"; payload: Lemma }
  | { type: "REMOVE_MANUAL_LEMMA"; payload: string }
  | { type: "TOGGLE_EXCLUDE_LEMMA"; payload: string }
  | {
      type: "BATCH_EXCLUDE_LEMMAS";
      payload: { ids: string[]; shouldExclude: boolean };
    }
  | { type: "UPDATE_QUALITIES"; payload: Partial<ExerciseConfigState> };

export const initialState: WordSelectionState = {
  selectedLessonListIds: [],
  manualLemmas: [],
  excludedLemmaIds: [],
  qualities: {
    difficulty: "medium",
    maxKeys: 1,
    maxDistractors: 3,
    allowOddOneOut: false,
    itemFormats: [], // STANDARD: Unselected at start
    typeCounts: {},
    maxItems: 10,
  },
};

export function wordSelectionReducer(
  state: WordSelectionState,
  action: WordSelectionAction,
): WordSelectionState {
  switch (action.type) {
    case "TOGGLE_LESSON_LIST": {
      const exists = state.selectedLessonListIds.includes(action.payload);
      return {
        ...state,
        selectedLessonListIds: exists
          ? state.selectedLessonListIds.filter((id) => id !== action.payload)
          : [...state.selectedLessonListIds, action.payload],
      };
    }

    case "CLEAR_LESSON_LISTS":
      return {
        ...state,
        selectedLessonListIds: [],
        excludedLemmaIds: [],
      };

    case "SET_LESSON_LISTS":
      return {
        ...state,
        selectedLessonListIds: action.payload,
        excludedLemmaIds: [],
      };

    case "ADD_MANUAL_LEMMA": {
      const exists = state.manualLemmas.some(
        (l) => String(l.id) === String(action.payload.id),
      );
      if (exists) return state;
      return {
        ...state,
        manualLemmas: [...state.manualLemmas, action.payload],
      };
    }

    case "REMOVE_MANUAL_LEMMA":
      return {
        ...state,
        manualLemmas: state.manualLemmas.filter(
          (l) => String(l.id) !== String(action.payload),
        ),
        excludedLemmaIds: state.excludedLemmaIds.filter(
          (id) => id !== String(action.payload),
        ),
      };

    case "TOGGLE_EXCLUDE_LEMMA": {
      const targetId = String(action.payload);
      const isExcluded = state.excludedLemmaIds.includes(targetId);
      return {
        ...state,
        excludedLemmaIds: isExcluded
          ? state.excludedLemmaIds.filter((id) => id !== targetId)
          : [...state.excludedLemmaIds, targetId],
      };
    }

    case "BATCH_EXCLUDE_LEMMAS": {
      const { ids, shouldExclude } = action.payload;
      const targetSet = new Set(ids.map(String));
      const currentSet = new Set(state.excludedLemmaIds.map(String));

      if (shouldExclude) {
        targetSet.forEach((id) => currentSet.add(id));
      } else {
        targetSet.forEach((id) => currentSet.delete(id));
      }

      return {
        ...state,
        excludedLemmaIds: Array.from(currentSet),
      };
    }

    case "UPDATE_QUALITIES":
      return {
        ...state,
        qualities: {
          ...state.qualities,
          ...action.payload,
        },
      };

    case "RESET_ALL":
      return {
        ...initialState,
        qualities: {
          ...initialState.qualities,
          maxItems: state.qualities.maxItems, // preserve quota preference
          difficulty: state.qualities.difficulty,
        },
      };

    default:
      return state;
  }
}
