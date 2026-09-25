/**
 * src/features/sentences/SentencesMenu.tsx
 *
 * Root view for configuring and generating sentence-level exercises.
 * Uses named exports to align with Vite's strict module resolution.
 */

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { SentenceExerciseConfigPanel } from "./SentenceExerciseConfigPanel";
import { SentenceStrategyPicker } from "./SentenceStrategyPicker";
import { ExerciseRequestPayload, ItemDifficulty, ItemFormat } from "./types";

interface Props {
  onBack: () => void;
  onExerciseGenerated?: (exerciseData: any) => void;
}

export function SentencesMenu({ onBack, onExerciseGenerated }: Props) {
  const { t } = useTranslation();

  // Strategy question distribution
  const [typeCounts, setTypeCounts] = useState<Record<string, number>>({
    cloze_noun_morph: 0,
    unscramble: 0,
  });

  // Global session constraints
  const [selectedFormats, setSelectedFormats] = useState<ItemFormat[]>([
    "mcq",
    "fitb",
    "unscramble",
  ]);
  const [difficulty, setDifficulty] = useState<ItemDifficulty>("medium");
  const [maxDistractors, setMaxDistractors] = useState<number>(3);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCountChange = (strategyId: string, newCount: number) => {
    setTypeCounts((prev) => ({
      ...prev,
      [strategyId]: newCount,
    }));
  };

  const handleToggleFormat = (fmt: ItemFormat) => {
    setSelectedFormats((prev) =>
      prev.includes(fmt) ? prev.filter((f) => f !== fmt) : [...prev, fmt],
    );
  };

  const totalQuestions = Object.values(typeCounts).reduce(
    (acc, c) => acc + c,
    0,
  );

  // Payload dispatch to backend
  const handleGenerate = async () => {
    if (totalQuestions === 0 || selectedFormats.length === 0) return;

    setIsLoading(true);
    setErrorMsg(null);

    const payload: ExerciseRequestPayload = {
      exercise_context: {
        lem_ids: null, // Corpus-wide sampling
        ex_formats: selectedFormats,
        difficulty: difficulty,
        allow_odd_one_out: false,
        max_keys: 1,
        max_distractors: maxDistractors,
      },
      type_counts: Object.fromEntries(
        Object.entries(typeCounts).filter(([_, count]) => count > 0),
      ),
    };

    try {
      const response = await fetch("/api/v1/exercises/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(
          errData.detail || "Failed to generate exercise session.",
        );
      }

      const data = await response.json();
      if (onExerciseGenerated) {
        onExerciseGenerated(data);
      }
    } catch (err: any) {
      setErrorMsg(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 w-full max-w-6xl mx-auto">
      {/* View Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-3xl font-bold text-stone-900">
            {t("sentencesMenu.title", "Тренировка предложений")}
          </h2>
          <p className="text-sm text-stone-500 mt-1">
            {t(
              "sentencesMenu.subtitle",
              "Выберите грамматические задачи и настройте формат тренировки",
            )}
          </p>
        </div>

        <button
          type="button"
          onClick={onBack}
          className="text-sm font-semibold bg-stone-200 hover:bg-stone-300 text-stone-700 px-4 py-2 rounded-lg transition-colors"
        >
          ← {t("back", "Назад")}
        </button>
      </div>

      {errorMsg && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg">
          {errorMsg}
        </div>
      )}

      {/* Main Layout Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2">
          <SentenceStrategyPicker
            typeCounts={typeCounts}
            onCountChange={handleCountChange}
          />
        </div>

        <div className="md:col-span-1">
          <SentenceExerciseConfigPanel
            selectedFormats={selectedFormats}
            onToggleFormat={handleToggleFormat}
            difficulty={difficulty}
            onDifficultyChange={setDifficulty}
            maxDistractors={maxDistractors}
            onDistractorsChange={setMaxDistractors}
            totalQuestions={totalQuestions}
            onGenerate={handleGenerate}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
}

export default SentencesMenu;
