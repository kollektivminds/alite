/**
 * src/features/sentences/SentencesMenu.tsx
 *
 * Root view for configuring and orchestrating sentence-level exercises.
 * Manages assessment configuration state and synchronizes stochastic allocation.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { DifficultyLevel, ExerciseResponse } from "../../types/exercise";
import { ExerciseContainer } from "../exercises/ExerciseContainer";
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

  // 1. Linguistic Strategy Allocations (Individual strategy question counts)
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({
    noun_morph: 3,
    unscramble: 2,
  });

  // 2. Harmonized Assessment Configuration State Container
  const [config, setConfig] = useState<SentenceExerciseConfigState>({
    difficulty: "medium",
    maxDistractors: 3,
    maxKeys: 1,
    allowOddOneOut: false,
    itemFormats: ["mcq", "fitb", "unscramble"],
    maxItems: 10, // Default target question quota
  });

  // 3. Telemetry and active assessment session state
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

  const totalQuestions = Object.values(typeCounts).reduce(
    (acc, count) => acc + (count || 0),
    0,
  );

  // 4. Exercise Generation Pipeline Dispatch
  const handleGenerate = async () => {
    if (totalQuestions === 0 || config.itemFormats.length === 0) return;

    setIsLoading(true);
    setErrorMsg(null);

    const payload: ExerciseRequestPayload = {
      exercise_context: {
        lem_ids: null, // Corpus-wide sentence sampling
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

  const handleExitExercise = () => {
    setActiveExercise(null);
    setActiveDifficulty(null);
  };

  return (
    <div className="w-full relative">
      {activeExercise ? (
        <ExerciseContainer
          exerciseData={activeExercise}
          difficulty={activeDifficulty || "medium"}
          onExit={handleExitExercise}
        />
      ) : (
        <div className="p-8 w-full max-w-6xl mx-auto">
          {/* Header Navigation Bar */}
          <div className="flex justify-between items-center mb-6">
            <div>
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100">
                {t("exercises.sentencesMenu.title")}
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                {t("exercises.sentencesMenu.instructions")}
              </p>
            </div>

            <button
              type="button"
              onClick={onBack}
              className="text-sm font-semibold bg-slate-200 hover:bg-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-700 dark:text-slate-200 px-4 py-2 rounded-lg transition-colors"
            >
              ← {t("back")}
            </button>
          </div>

          {errorMsg && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm rounded-lg">
              {errorMsg}
            </div>
          )}

          {/* Unified Assessment Workspace Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="md:col-span-2">
              <SentenceStrategyPicker
                typeCounts={typeCounts}
                onCountChange={handleCountChange}
                onBatchCountChange={setTypeCounts}
                targetCount={config.maxItems}
                enabledFormats={config.itemFormats}
              />
            </div>

            <div className="md:col-span-1">
              <SentenceExerciseConfigPanel
                config={config}
                onChange={handleConfigChange}
                totalQuestions={totalQuestions}
                onGenerate={handleGenerate}
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
