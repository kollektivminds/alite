// src/features/words/WordsSubLandingPage.tsx
import axios from "axios";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useState,
} from "react";
import { useTranslation } from "react-i18next";
import { ExerciseContext, Lemma, LessonList } from "../../types";
import { ExerciseConfigPanel } from "./ExerciseConfigPanel";
import { LessonListPicker } from "./LessonListPicker";
import { LessonWordPruner } from "./LessonWordPruner";
import { PipelineJobDrawer, TrackedPipelineJob } from "./PipelineJobDrawer";
import { PipelineResponse, SingleWordAdder } from "./SingleWordAdder";
import { initialState, wordSelectionReducer } from "./WordSelectionReducer";

interface LemmaReadinessItem {
  lemma_id: number;
  lem_text: string;
  is_usable: boolean;
  supported_item_types: string[];
  advisory_warnings: string[];
  critical_errors: string[];
}

interface PoolValidationResponse {
  can_start: boolean;
  total_requested: number;
  eligible_count: number;
  eligible_lemma_ids: number[];
  unusable_lemma_ids: number[];
  reports: LemmaReadinessItem[];
  summary_message: string;
}

interface WordsSubLandingPageProps {
  availableLessonLists: LessonList[];
  searchLemmasApi: (query: string) => Promise<Lemma[]>;
  requestPipelineApi?: (tokens: string[]) => Promise<PipelineResponse>;
  onSubmitGeneration: (payload: {
    lemmaIds: string[];
    qualities: ExerciseContext;
  }) => void;
}

export const WordsSubLandingPage: React.FC<WordsSubLandingPageProps> = ({
  availableLessonLists,
  searchLemmasApi,
  requestPipelineApi,
  onSubmitGeneration,
}) => {
  const { t } = useTranslation();
  const [state, dispatch] = useReducer(wordSelectionReducer, initialState);

  // Background pipeline job telemetry
  const [pipelineJobs, setPipelineJobs] = useState<TrackedPipelineJob[]>([]);

  // Validation feedback: fatal blockers vs advisory warnings
  const [fatalErrors, setFatalErrors] = useState<string[]>([]);
  const [advisoryWarnings, setAdvisoryWarnings] = useState<string[]>([]);
  const [isValidating, setIsValidating] = useState<boolean>(false);

  const handleRequestPipeline = useCallback(
    async (tokensInput: string[] | string): Promise<PipelineResponse> => {
      setFatalErrors([]);
      setAdvisoryWarnings([]);

      const tokenArray = Array.isArray(tokensInput)
        ? tokensInput
        : [tokensInput];
      const payload = {
        tokens: tokenArray,
        token: tokenArray[0] || "",
      };

      let data: PipelineResponse;
      if (requestPipelineApi) {
        data = await requestPipelineApi(tokenArray);
      } else {
        const response = await axios.post<PipelineResponse>(
          "/api/trainer/lemmas/pipeline-lookup",
          payload,
        );
        data = response.data;
      }

      if (data.results && data.results.length > 0) {
        const newJobs: TrackedPipelineJob[] = data.results.map((item) => ({
          token: item.token,
          status: item.status as TrackedPipelineJob["status"],
          message: item.message,
          timestamp: new Date(),
        }));

        setPipelineJobs((prev) => [...newJobs, ...prev]);
      }

      return data;
    },
    [requestPipelineApi],
  );

  // Background ETL Telemetry Polling Loop
  useEffect(() => {
    const hasPendingJobs = pipelineJobs.some(
      (j) => j.status === "queued" || j.status === "in_progress",
    );

    if (!hasPendingJobs) return;

    const intervalId = setInterval(async () => {
      try {
        const pendingTokens = pipelineJobs
          .filter((j) => j.status === "queued" || j.status === "in_progress")
          .map((j) => j.token);

        if (pendingTokens.length === 0) return;

        const response = await axios.post<any[]>(
          "/api/trainer/lemmas/queue-status",
          {
            tokens: pendingTokens,
          },
        );

        const outcomes = response.data;
        if (!outcomes || outcomes.length === 0) return;

        const outcomeMap = new Map(outcomes.map((o: any) => [o.token, o]));

        let stateChanged = false;
        const updatedJobs = pipelineJobs.map((job) => {
          const fresh = outcomeMap.get(job.token);
          if (fresh && fresh.status !== job.status) {
            stateChanged = true;

            // Auto-stage newly parsed lemmas upon completion
            if (fresh.status === "completed" && fresh.existing_lemma_id) {
              axios
                .get<Lemma>(`/api/trainer/lemmas/${fresh.existing_lemma_id}`)
                .then((res) => {
                  if (res.data) {
                    dispatch({ type: "ADD_MANUAL_LEMMA", payload: res.data });
                  }
                })
                .catch((err) =>
                  console.error("Error auto-staging completed lemma:", err),
                );
            }

            return {
              ...job,
              status: fresh.status as TrackedPipelineJob["status"],
              message: fresh.message || job.message,
            };
          }
          return job;
        });

        if (stateChanged) {
          setPipelineJobs(updatedJobs);
        }
      } catch (err) {
        console.error("Queue telemetry poll error:", err);
      }
    }, 2500);

    return () => clearInterval(intervalId);
  }, [pipelineJobs]);

  // Extract active curriculum lemmas based on selected list IDs
  const activeLessonLemmas = useMemo(() => {
    const map = new Map<string, Lemma>();
    availableLessonLists
      .filter((list) => state.selectedLessonListIds.includes(String(list.id)))
      .forEach((list) =>
        (list.has_lemma || []).forEach((lemma: Lemma) => {
          map.set(String(lemma.id), lemma);
        }),
      );
    return Array.from(map.values());
  }, [availableLessonLists, state.selectedLessonListIds]);

  // Combine curriculum and manual lemmas minus exclusion mask
  const finalActiveLemmas = useMemo(() => {
    const combined = new Map<string, Lemma>();
    activeLessonLemmas.forEach((l: Lemma) => combined.set(String(l.id), l));
    state.manualLemmas.forEach((l: Lemma) => combined.set(String(l.id), l));

    const exclusionSet = new Set(state.excludedLemmaIds.map(String));
    return Array.from(combined.values()).filter(
      (l) => !exclusionSet.has(String(l.id)),
    );
  }, [activeLessonLemmas, state.manualLemmas, state.excludedLemmaIds]);

  const handleSelectLemma = useCallback((lemma: Lemma) => {
    setFatalErrors([]);
    dispatch({ type: "ADD_MANUAL_LEMMA", payload: lemma });
  }, []);

  // Soft pre-flight check asserting quorum rather than strict homogeneity
  const handlePreFlightAndGenerate = async () => {
    if (isValidating) return;
    setFatalErrors([]);
    setAdvisoryWarnings([]);

    if (finalActiveLemmas.length === 0) {
      setFatalErrors([
        t("exercises.wordsMenu.noWordsSelected") ||
          "Please select a lesson list or search for vocabulary words before generating an exercise.",
      ]);
      return;
    }

    const inFlightJobs = pipelineJobs.filter(
      (j) => j.status === "queued" || j.status === "in_progress",
    );
    if (inFlightJobs.length > 0) {
      const names = inFlightJobs.map((j) => `"${j.token}"`).join(", ");
      setFatalErrors([
        `Dictionary extraction is currently processing: ${names}. Please wait for it to complete.`,
      ]);
      return;
    }

    setIsValidating(true);

    try {
      const numericIds = finalActiveLemmas
        .map((l) => Number(l.id))
        .filter((id) => !isNaN(id) && id > 0);

      const response = await axios.post<PoolValidationResponse>(
        "/api/v1/lemmas/validate-exercise-pool",
        {
          lemma_ids: numericIds,
          min_required_words: 1, // Require at least 1 viable word to build exercise
        },
      );

      const { can_start, eligible_lemma_ids, reports } = response.data;

      const advisories: string[] = [];
      reports.forEach((item) => {
        if (item.advisory_warnings.length > 0) {
          advisories.push(
            `${item.lem_text}: ${item.advisory_warnings.join(", ")}`,
          );
        }
      });
      setAdvisoryWarnings(advisories);

      if (!can_start) {
        const criticals: string[] = [];
        reports.forEach((item) => {
          if (item.critical_errors.length > 0) {
            criticals.push(
              `${item.lem_text}: ${item.critical_errors.join(", ")}`,
            );
          }
        });
        setFatalErrors(
          criticals.length > 0
            ? criticals
            : [
                "The selected vocabulary pool does not contain enough usable data to build an exercise.",
              ],
        );
        return;
      }

      onSubmitGeneration({
        lemmaIds: eligible_lemma_ids.map(String),
        qualities: state.qualities,
      });
    } catch (err: any) {
      console.error("Pool validation failed:", err);
      const detail =
        err.response?.data?.detail ||
        err.message ||
        "Could not verify vocabulary pool readiness. Please check server connectivity.";
      setFatalErrors([detail]);
    } finally {
      setIsValidating(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 relative pb-24">
      {/* Header */}
      <div className="mb-8 border-b border-gray-200 pb-5 dark:border-gray-700">
        <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
          {t("exercises.wordsMenu.title")}
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {t("exercises.wordsMenu.instructions")}
        </p>
      </div>

      {/* Fatal Error Notice (Blocks Generation) */}
      {fatalErrors.length > 0 && (
        <aside
          role="alert"
          aria-live="assertive"
          className="mb-6 rounded-xl border border-rose-200 bg-rose-50 p-4 shadow-sm dark:border-rose-900/60 dark:bg-rose-950/40"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="text-rose-600 dark:text-rose-400 font-bold text-base">
                ⚠
              </span>
              <h3 className="text-sm font-bold text-rose-900 dark:text-rose-200">
                Unable to Start Exercise
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setFatalErrors([])}
              className="text-xs font-semibold text-rose-600 hover:text-rose-800 dark:text-rose-400 focus:outline-none"
            >
              ✕
            </button>
          </div>
          <ul className="mt-2 list-disc list-inside space-y-1 text-xs text-rose-800 dark:text-rose-300">
            {fatalErrors.map((errMsg, idx) => (
              <li key={idx} className="leading-relaxed">
                {errMsg}
              </li>
            ))}
          </ul>
        </aside>
      )}

      {/* Advisory Warnings Notice (Non-Blocking) */}
      {advisoryWarnings.length > 0 && fatalErrors.length === 0 && (
        <aside
          role="status"
          className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 shadow-sm dark:border-amber-900/60 dark:bg-amber-950/40"
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <span className="text-amber-600 dark:text-amber-400 font-bold text-base">
                ℹ
              </span>
              <h3 className="text-sm font-bold text-amber-900 dark:text-amber-200">
                Lexical Coverage Advisory
              </h3>
            </div>
            <button
              type="button"
              onClick={() => setAdvisoryWarnings([])}
              className="text-xs font-semibold text-amber-600 hover:text-amber-800 dark:text-amber-400 focus:outline-none"
            >
              ✕
            </button>
          </div>
          <p className="mt-1 text-xs text-amber-700 dark:text-amber-300">
            Some lemmas have partial inflection tables. Questions will
            automatically adapt to available forms:
          </p>
          <ul className="mt-2 list-disc list-inside space-y-0.5 text-xs text-amber-800 dark:text-amber-300 max-h-32 overflow-y-auto">
            {advisoryWarnings.map((warnMsg, idx) => (
              <li key={idx}>{warnMsg}</li>
            ))}
          </ul>
        </aside>
      )}

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        {/* Left Column: LessonPicker, SingleWordAdder, LessonWordPruner */}
        <div className="space-y-8 lg:col-span-7">
          {/* Lesson List Curriculum Picker with Random Assortment Support */}
          <LessonListPicker
            lessonLists={availableLessonLists}
            selectedIds={state.selectedLessonListIds}
            onToggleList={(id: string) => {
              setFatalErrors([]);
              dispatch({ type: "TOGGLE_LESSON_LIST", payload: id });
            }}
            onSelectRandom={(randomIds: string[]) => {
              setFatalErrors([]);
              dispatch({ type: "SET_LESSON_LISTS", payload: randomIds });
            }}
            onClearAll={() => {
              setFatalErrors([]);
              dispatch({ type: "CLEAR_LESSON_LISTS" });
            }}
          />

          {/* Ad-Hoc Word Adder & Background ETL Trigger */}
          <SingleWordAdder
            onSearch={searchLemmasApi}
            onSelectLemma={handleSelectLemma}
            onRequestPipeline={handleRequestPipeline}
          />

          {/* Staged Pool Inspection with POS-Level Single-Click Filtering */}
          <LessonWordPruner
            lessonLemmas={activeLessonLemmas}
            manualLemmas={state.manualLemmas}
            excludedIds={state.excludedLemmaIds}
            onToggleExclude={(id: string) => {
              setFatalErrors([]);
              dispatch({ type: "TOGGLE_EXCLUDE_LEMMA", payload: id });
            }}
            onToggleBatchExclude={(ids: string[], shouldExclude: boolean) => {
              setFatalErrors([]);
              dispatch({
                type: "BATCH_EXCLUDE_LEMMAS",
                payload: { ids, shouldExclude },
              });
            }}
            onRemoveManual={(id: string) => {
              setFatalErrors([]);
              dispatch({ type: "REMOVE_MANUAL_LEMMA", payload: id });
            }}
          />
        </div>

        {/* Right Column: Exercise Parameters & Non-Blocking Launch */}
        <div className="lg:col-span-5">
          <div className="sticky top-6 rounded-xl border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-slate-800">
            <ExerciseConfigPanel
              config={state.qualities}
              activeLemmas={finalActiveLemmas}
              onChange={(updated) =>
                dispatch({ type: "UPDATE_QUALITIES", payload: updated })
              }
              onSubmit={handlePreFlightAndGenerate}
            />

            {isValidating && (
              <div className="mt-3 flex items-center justify-center gap-2 text-xs font-medium text-slate-500 dark:text-slate-400">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                <span>Checking lexical pool capability...</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Telemetry Drawer */}
      <PipelineJobDrawer jobs={pipelineJobs} />
    </div>
  );
};
