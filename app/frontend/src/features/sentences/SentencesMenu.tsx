// src/features/sentences/SentencesMenu.tsx
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { DifficultyLevel, ExerciseResponse } from "../../types/exercise";
import { ExerciseContainer } from "../exercises/exerciseContainer";
import { SentenceExerciseConfigPanel } from "./SentenceExerciseConfigPanel";
import { SentenceStrategyPicker } from "./SentenceStrategyPicker";
import type {
  ExerciseRequestPayload,
  SentenceExerciseConfigState,
} from "./types";

interface Props {
  onBack: () => void;
}

export function SentencesMenu({ onBack }: Props) {
  const { t } = useTranslation();

  // 1. STANDARD: Starts with 0 strategies selected
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({});

  // 2. STANDARD: Formats start unselected ([]), maxItems defaults to 10
  const [config, setConfig] = useState<SentenceExerciseConfigState>({
    difficulty: "medium",
    maxDistractors: 3,
    maxKeys: 1,
    allowOddOneOut: false,
    itemFormats: [],
    maxItems: 10,
  });

  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [activeExercise, setActiveExercise] = useState<ExerciseResponse | null>(
    null,
  );
  const [activeDifficulty, setActiveDifficulty] =
    useState<DifficultyLevel | null>(null);

  const handleConfigChange = (
    updated: Partial<SentenceExerciseConfigState>,
  ) => {
    setConfig((prev) => ({ ...prev, ...updated }));
  };

  const handleCountChange = (strategyId: string, newCount: number) => {
    setTypeCounts((prev) => ({
      ...prev,
      [strategyId]: Math.max(0, newCount),
    }));
  };

  // 3. Reset Button Handler: Clears allocations and formats back to initial state
  const handleResetAll = () => {
    setTypeCounts({});
    setConfig((prev) => ({
      ...prev,
      itemFormats: [],
    }));
    setErrorMsg(null);
  };

  const totalQuestions = Object.values(typeCounts).reduce(
    (acc, count) => acc + (count || 0),
    0,
  );

  const handleGenerate = async () => {
    if (totalQuestions === 0 || config.itemFormats.length === 0) return;

    setIsLoading(true);
    setErrorMsg(null);

    const payload: ExerciseRequestPayload = {
      exercise_context: {
        lem_ids: null, // Corpus-wide sentence search
        ex_formats: config.itemFormats,
        difficulty: config.difficulty,
        allow_odd_one_out: config.allowOddOneOut,
        max_keys: config.maxKeys,
        max_distractors: config.maxDistractors,
      },
      type_counts: Object.fromEntries(
        Object.entries(typeCounts).filter(([_, count]) => count > 0),
      ),
      grammar_focus: null,
    };

    try {
      const response = await fetch("/api/v1/exercises/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Server error: ${response.status}`);
      }

      const data: ExerciseResponse = await response.json();
      setActiveDifficulty(config.difficulty as DifficultyLevel);
      setActiveExercise(data);
    } catch (err: any) {
      console.error("Exercise generation failed:", err);
      setErrorMsg(err.message || "Failed to generate exercise session.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full relative">
      {activeExercise ? (
        <ExerciseContainer
          exerciseData={activeExercise}
          difficulty={activeDifficulty || "medium"}
          onExit={() => {
            setActiveExercise(null);
            setActiveDifficulty(null);
          }}
        />
      ) : (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8 relative pb-24">
          {/* Header Bar */}
          <div className="mb-8 flex justify-between items-center border-b border-gray-200 pb-5 dark:border-gray-700">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
                {t("exercises.sentencesMenu.title") || "Sentence-Level Drills"}
              </h1>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                {t("exercises.sentencesMenu.instructions") ||
                  "Configure syntactic, morphological, and word-order exercises in authentic context."}
              </p>
            </div>

            <button
              type="button"
              onClick={onBack}
              className="text-sm font-semibold bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 px-4 py-2 rounded-lg transition-colors"
            >
              ← {t("back") || "Back"}
            </button>
          </div>

          {errorMsg && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm rounded-lg">
              {errorMsg}
            </div>
          )}

          {/* Standard 12-Column Responsive Workspace */}
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
            {/* Left Column: Strategy Category Selectors */}
            <div className="space-y-8 lg:col-span-7">
              <SentenceStrategyPicker
                typeCounts={typeCounts}
                onCountChange={handleCountChange}
                onBatchCountChange={setTypeCounts}
                targetCount={config.maxItems}
                onResetAll={handleResetAll}
              />
            </div>

            {/* Right Column: Sticky Parameter Sidebar */}
            <div className="lg:col-span-5">
              <SentenceExerciseConfigPanel
                config={config}
                typeCounts={typeCounts}
                totalAllocated={totalQuestions}
                onChange={handleConfigChange}
                onSubmit={handleGenerate}
                isLoading={isLoading}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default SentencesMenu;
