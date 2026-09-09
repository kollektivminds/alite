// src/features/words/WordsSubLandingPage.tsx
import React, { useMemo, useReducer } from "react";
import { ExerciseContext, Lemma, LessonList } from "../../types/words"; //[cite: 3]

import { ExerciseConfigPanel } from "./ExerciseConfigPanel";
import { LessonListPicker } from "./LessonListPicker";
import { LessonWordPruner } from "./LessonWordPruner";
import { SingleWordAdder } from "./SingleWordAdder";
import { initialState, wordSelectionReducer } from "./WordSelectionReducer";

interface WordsSubLandingPageProps {
  availableLessonLists: LessonList[]; //[cite: 2]
  searchLemmasApi: (query: string) => Promise<Lemma[]>; //[cite: 2]
  onSubmitGeneration: (payload: {
    lemmaIds: string[];
    qualities: ExerciseContext;
  }) => void; //[cite: 2]
}

export const WordsSubLandingPage: React.FC<WordsSubLandingPageProps> = ({
  availableLessonLists,
  searchLemmasApi,
  onSubmitGeneration,
}) => {
  const [state, dispatch] = useReducer(wordSelectionReducer, initialState);

  // extract active lemmas from toggled curriculum lists
  const activeLessonLemmas = useMemo(() => {
    const map = new Map<string, Lemma>();
    availableLessonLists
      .filter((list) => state.selectedLessonListIds.includes(String(list.id)))
      .forEach((list: any) =>
        (list.has_lemma || []).forEach((lemma: any) => {
          // guarantee the Lemma ID is stored as a string
          const safeLemmaId = String(lemma.id);
          map.set(safeLemmaId, lemma);
        }),
      );

    return Array.from(map.values());
  }, [availableLessonLists, state.selectedLessonListIds]);

  // 2. Derive the final pool for pipeline submission
  const finalActiveLemmas = useMemo(() => {
    const combined = new Map<string, Lemma>();
    activeLessonLemmas.forEach((l: Lemma) => combined.set(l.id, l));
    state.manualLemmas.forEach((l: Lemma) => combined.set(l.id, l));

    const exclusionSet = new Set(state.excludedLemmaIds);
    return Array.from(combined.values()).filter((l) => !exclusionSet.has(l.id));
  }, [activeLessonLemmas, state.manualLemmas, state.excludedLemmaIds]);

  const handleGenerate = () => {
    onSubmitGeneration({
      lemmaIds: finalActiveLemmas.map((l: { id: any }) => l.id),
      qualities: state.qualities,
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 border-b border-gray-200 pb-5 dark:border-gray-700">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Target Lemma Assessment Configuration
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Assemble target vocabulary and configure psychometric distractor
          strategies.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: Vocabulary Construction Inputs & Staging */}
        <div className="space-y-8 lg:col-span-7">
          {/* Input 1: Batch Selection */}
          <LessonListPicker
            lessonLists={availableLessonLists}
            selectedIds={state.selectedLessonListIds}
            onToggleList={(id: string) =>
              dispatch({ type: "TOGGLE_LESSON_LIST", payload: id })
            }
            onClearAll={() => dispatch({ type: "CLEAR_LESSON_LISTS" })}
          />

          {/* Input 2: Manual Search */}
          <SingleWordAdder
            onSearch={searchLemmasApi}
            onSelectLemma={(lemma: any) =>
              dispatch({ type: "ADD_MANUAL_LEMMA", payload: lemma })
            }
          />

          {/* Master Staging Area: Replaces both the old pruner and the summary */}
          <LessonWordPruner
            lessonLemmas={activeLessonLemmas}
            manualLemmas={state.manualLemmas}
            excludedIds={state.excludedLemmaIds}
            onToggleExclude={(id: any) =>
              dispatch({ type: "TOGGLE_EXCLUDE_LEMMA", payload: id })
            }
            onRemoveManual={(id: any) =>
              dispatch({ type: "REMOVE_MANUAL_LEMMA", payload: id })
            }
          />
        </div>

        {/* Right Column: Generation Qualities Sidebar */}
        <div className="lg:col-span-5">
          <div className="sticky top-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <ExerciseConfigPanel
              config={state.qualities} // Ensure this maps to ExerciseConfigState defined above
              activeLemmas={finalActiveLemmas} // Pass the array to evaluate POS
              onChange={(updated: any) =>
                dispatch({ type: "UPDATE_QUALITIES", payload: updated })
              }
              onSubmit={handleGenerate}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
