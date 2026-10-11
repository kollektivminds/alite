// src/features/words/WordsSubLandingPage.tsx
import axios from "axios";
import React, { useCallback, useMemo, useReducer, useState } from "react";
import { useTranslation } from "react-i18next";
import { ExerciseContext, Lemma, LessonList } from "../../types";
import { ExerciseConfigPanel } from "./ExerciseConfigPanel";
import { LessonListPicker } from "./LessonListPicker";
import { LessonWordPruner } from "./LessonWordPruner";
import { PipelineJobDrawer, TrackedPipelineJob } from "./PipelineJobDrawer";
import { PipelineResponse, SingleWordAdder } from "./SingleWordAdder";
import { initialState, wordSelectionReducer } from "./WordSelectionReducer";

interface WordsSubLandingPageProps {
  availableLessonLists: LessonList[]; //[cite: 10]
  searchLemmasApi: (query: string) => Promise<Lemma[]>; //[cite: 10]
  requestPipelineApi?: (token: string) => Promise<PipelineResponse>; //[cite: 10]
  onSubmitGeneration: (payload: {
    lemmaIds: string[];
    qualities: ExerciseContext;
  }) => void; //[cite: 10]
}

export const WordsSubLandingPage: React.FC<WordsSubLandingPageProps> = ({
  availableLessonLists, //[cite: 10]
  searchLemmasApi, //[cite: 10]
  requestPipelineApi,
  onSubmitGeneration, //[cite: 10]
}) => {
  const { t } = useTranslation();
  const [state, dispatch] = useReducer(wordSelectionReducer, initialState); //[cite: 10]

  // Track background ETL jobs for the current session
  const [pipelineJobs, setPipelineJobs] = useState<TrackedPipelineJob[]>([]);

  const handleRequestPipeline = useCallback(
    async (tokens: string[]): Promise<PipelineResponse> => {
      // Submit array of tokens to match the updated Pydantic schema
      const response = await axios.post<PipelineResponse>(
        "/api/v1/lemmas/pipeline-lookup",
        { tokens },
      );

      const data = response.data;

      // Log all returned outcomes into the session job drawer
      if (data.results && data.results.length > 0) {
        const newJobs: TrackedPipelineJob[] = data.results.map((item) => ({
          token: item.token,
          status: item.status,
          message: item.message,
          timestamp: new Date(),
        }));

        setPipelineJobs((prev) => [...newJobs, ...prev]);
      }

      return data;
    },
    [],
  );

  const activeLessonLemmas = useMemo(() => {
    const map = new Map<string, Lemma>();
    availableLessonLists //[cite: 10]
      .filter((list) => state.selectedLessonListIds.includes(String(list.id))) //[cite: 10]
      .forEach((list) =>
        (list.has_lemma || []).forEach((lemma: Lemma) => {
          //[cite: 10]
          map.set(String(lemma.id), lemma);
        }),
      );
    return Array.from(map.values());
  }, [availableLessonLists, state.selectedLessonListIds]); //[cite: 10]

  const finalActiveLemmas = useMemo(() => {
    const combined = new Map<string, Lemma>();
    activeLessonLemmas.forEach((l: Lemma) => combined.set(String(l.id), l));
    state.manualLemmas.forEach((l: Lemma) => combined.set(String(l.id), l)); //[cite: 10]

    const exclusionSet = new Set(state.excludedLemmaIds); //[cite: 10]
    return Array.from(combined.values()).filter(
      (l) => !exclusionSet.has(String(l.id)),
    ); //[cite: 10]
  }, [activeLessonLemmas, state.manualLemmas, state.excludedLemmaIds]); //[cite: 10]

  const handleSelectLemma = useCallback((lemma: Lemma) => {
    dispatch({ type: "ADD_MANUAL_LEMMA", payload: lemma }); //[cite: 10]
  }, []);

  const handleGenerate = () => {
    onSubmitGeneration({
      //[cite: 10]
      lemmaIds: finalActiveLemmas.map((l) => String(l.id)), //[cite: 10]
      qualities: state.qualities, //[cite: 10]
    });
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 relative pb-20">
      <div className="mb-8 border-b border-gray-200 pb-5 dark:border-gray-700">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          {t("exercises.wordsMenu.title")}
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {t("exercises.wordsMenu.instructions")}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="space-y-8 lg:col-span-7">
          <LessonListPicker
            lessonLists={availableLessonLists} //[cite: 10]
            selectedIds={state.selectedLessonListIds} //[cite: 10]
            onToggleList={
              (id: string) =>
                dispatch({ type: "TOGGLE_LESSON_LIST", payload: id }) //[cite: 10]
            }
            onClearAll={() => dispatch({ type: "CLEAR_LESSON_LISTS" })} //[cite: 10]
          />

          {/* Bound with dropdown row action & Latin confirmation */}
          <SingleWordAdder
            onSearch={searchLemmasApi}
            onSelectLemma={handleSelectLemma}
            onRequestPipeline={handleRequestPipeline}
          />

          <LessonWordPruner
            lessonLemmas={activeLessonLemmas} //[cite: 10]
            manualLemmas={state.manualLemmas} //[cite: 10]
            excludedIds={state.excludedLemmaIds} //[cite: 10]
            onToggleExclude={
              (id: string) =>
                dispatch({ type: "TOGGLE_EXCLUDE_LEMMA", payload: id }) //[cite: 10]
            }
            onRemoveManual={
              (id: string) =>
                dispatch({ type: "REMOVE_MANUAL_LEMMA", payload: id }) //[cite: 10]
            }
          />
        </div>

        <div className="lg:col-span-5">
          <div className="sticky top-6 rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-800">
            <ExerciseConfigPanel
              config={state.qualities} //[cite: 10]
              activeLemmas={finalActiveLemmas}
              onChange={
                (updated) =>
                  dispatch({ type: "UPDATE_QUALITIES", payload: updated }) //[cite: 10]
              }
              onSubmit={handleGenerate} //[cite: 10]
            />
          </div>
        </div>
      </div>

      {/* Collapsible Session Ingestion Task Drawer */}
      <PipelineJobDrawer jobs={pipelineJobs} />
    </div>
  );
};
