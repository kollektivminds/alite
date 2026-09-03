import React, { useMemo, useReducer } from "react";
import { Lemma, LessonList, QualityConfig } from "../../types"; //[cite: 3]

// These child components will be built in subsequent steps.
// Importing them now establishes the declarative layout contract.
import { LessonListPicker } from "./LessonListPicker";
import { LessonWordPruner } from "./LessonWordPruner";
import { QualitiesConfigPanel } from "./QualitiesConfigPanel";
import { SelectedLemmaSummary } from "./SelectedLemmaSummary";
import { SingleWordAdder } from "./SingleWordAdder";

// The reducer will handle the interconnected state transitions.
import { initialState, wordSelectionReducer } from "./WordSelectionReducer";

interface WordsSubLandingPageProps {
  availableLessonLists: LessonList[]; //[cite: 2]
  searchLemmasApi: (query: string) => Promise<Lemma[]>; //[cite: 2]
  onSubmitGeneration: (payload: {
    lemmaIds: string[];
    qualities: QualityConfig;
  }) => void; //[cite: 2]
}

export const WordsSubLandingPage: React.FC<WordsSubLandingPageProps> = ({
  availableLessonLists,
  searchLemmasApi,
  onSubmitGeneration,
}) => {
  // 1. Centralized State Management
  // We use useReducer here because selecting a lesson list, manually adding a word,
  // and pruning distractors are highly interrelated actions that shouldn't be split
  // across multiple disjointed useState hooks.
  const [state, dispatch] = useReducer(wordSelectionReducer, initialState);

  // 2. Deterministic Data Derivation (Memoization)
  // useMemo prevents expensive recalculations. If a user is typing a search query,
  // we do not want React to rebuild this entire array of dictionary forms on every keystroke.
  const activeLessonLemmas = useMemo(() => {
    const map = new Map<string, Lemma>();

    // Extract unique lemmas only from the lesson lists the user has toggled "on"
    availableLessonLists
      .filter((list) => state.selectedLessonListIds.includes(list.id))
      .forEach((list) =>
        list.has_lemma.forEach((lemma) => map.set(lemma.id, lemma)),
      );

    return Array.from(map.values());
  }, [availableLessonLists, state.selectedLessonListIds]);

  // Derive the final pool: (LessonBatches + ManualWords) - ExcludedSet[cite: 2]
  const finalActiveLemmas = useMemo(() => {
    const combined = new Map<string, Lemma>();

    activeLessonLemmas.forEach((l) => combined.set(l.id, l));
    state.manualLemmas.forEach((l) => combined.set(l.id, l));

    const exclusionSet = new Set(state.excludedLemmaIds);
    return Array.from(combined.values()).filter((l) => !exclusionSet.has(l.id));
  }, [activeLessonLemmas, state.manualLemmas, state.excludedLemmaIds]);

  // 3. Pipeline Submission
  const handleGenerate = () => {
    onSubmitGeneration({
      lemmaIds: finalActiveLemmas.map((l) => l.id),
      qualities: state.qualities,
    });
  };

  // 4. Declarative Layout
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 border-b border-gray-200 pb-5 dark:border-gray-700">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          Target Lemma Assessment Configuration
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Assemble target vocabulary and configure psychometric distractor
          strategies.
        </p>
      </div>

      {/* 12-Column Grid Layout */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: Vocabulary Construction (7 columns) */}
        <div className="space-y-6 lg:col-span-7">
          <LessonListPicker
            lessonLists={availableLessonLists}
            selectedIds={state.selectedLessonListIds}
            onToggleList={(id) =>
              dispatch({ type: "TOGGLE_LESSON_LIST", payload: id })
            }
          />

          <SingleWordAdder
            onSearch={searchLemmasApi}
            onSelectLemma={(lemma) =>
              dispatch({ type: "ADD_MANUAL_LEMMA", payload: lemma })
            }
          />

          {/* Only render the pruner if there are actually list lemmas to prune */}
          {activeLessonLemmas.length > 0 && (
            <LessonWordPruner
              lessonLemmas={activeLessonLemmas}
              excludedIds={state.excludedLemmaIds}
              onToggleExclude={(id) =>
                dispatch({ type: "TOGGLE_EXCLUDE_LEMMA", payload: id })
              }
            />
          )}

          <SelectedLemmaSummary
            activeLemmas={finalActiveLemmas}
            manualLemmas={state.manualLemmas}
            onRemoveManual={(id) =>
              dispatch({ type: "REMOVE_MANUAL_LEMMA", payload: id })
            }
            onExcludeLemma={(id) =>
              dispatch({ type: "TOGGLE_EXCLUDE_LEMMA", payload: id })
            }
          />
        </div>

        {/* Right Column: Generation Qualities Sticky Sidebar (5 columns) */}
        <div className="lg:col-span-5">
          <div className="sticky top-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
            <QualitiesConfigPanel
              config={state.qualities}
              lemmaCount={finalActiveLemmas.length}
              onChange={(updated) =>
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
