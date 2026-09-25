/**
 * src/features/sentences/SentenceExerciseConfigPanel.tsx
 *
 * Controls assessment context options:
 * - Allowed item formats: MCQ, FITB, Unscramble (Flashcard omitted for sentences)
 * - Difficulty rating
 * - Max distractor count
 */

import React from "react";
import { useTranslation } from "react-i18next";
import { ItemDifficulty, ItemFormat } from "./types";

interface Props {
  selectedFormats: ItemFormat[];
  onToggleFormat: (format: ItemFormat) => void;
  difficulty: ItemDifficulty;
  onDifficultyChange: (difficulty: ItemDifficulty) => void;
  maxDistractors: number;
  onDistractorsChange: (val: number) => void;
  totalQuestions: number;
  onGenerate: () => void;
  isLoading: boolean;
}

export const SentenceExerciseConfigPanel: React.FC<Props> = ({
  selectedFormats,
  onToggleFormat,
  difficulty,
  onDifficultyChange,
  maxDistractors,
  onDistractorsChange,
  totalQuestions,
  onGenerate,
  isLoading,
}) => {
  const { t } = useTranslation();

  const availableFormats: { id: ItemFormat; label: string }[] = [
    { id: "mcq", label: t("formats.mcq", "Выбор варианта (MCQ)") },
    { id: "fitb", label: t("formats.fitb", "Заполнение пропусков (FITB)") },
    {
      id: "unscramble",
      label: t("formats.unscramble", "Расстановка слов (Unscramble)"),
    },
  ];

  return (
    <div className="bg-white p-6 rounded-xl border border-stone-200 shadow-xs flex flex-col gap-6 sticky top-6">
      <h3 className="text-lg font-semibold text-stone-800 border-b border-stone-100 pb-3">
        {t("exerciseConfig.parameters", "Параметры тренировки")}
      </h3>

      {/* Allowed Formats */}
      <div>
        <label className="text-xs font-semibold uppercase tracking-wider text-stone-500 block mb-2">
          {t("exerciseConfig.formats", "Доступные форматы")}
        </label>
        <div className="flex flex-col gap-2">
          {availableFormats.map((fmt) => (
            <label
              key={fmt.id}
              className="flex items-center gap-3 text-sm text-stone-700 cursor-pointer select-none"
            >
              <input
                type="checkbox"
                checked={selectedFormats.includes(fmt.id)}
                onChange={() => onToggleFormat(fmt.id)}
                className="w-4 h-4 rounded border-stone-300 text-blue-600 focus:ring-blue-500"
              />
              {fmt.label}
            </label>
          ))}
        </div>
      </div>

      {/* Difficulty Setting */}
      <div>
        <label className="text-xs font-semibold uppercase tracking-wider text-stone-500 block mb-2">
          {t("exerciseConfig.difficulty", "Уровень сложности")}
        </label>
        <select
          value={difficulty}
          onChange={(e) => onDifficultyChange(e.target.value as ItemDifficulty)}
          className="w-full bg-stone-50 border border-stone-300 rounded-lg p-2 text-sm text-stone-800 focus:outline-hidden focus:ring-2 focus:ring-blue-500"
        >
          <option value="easy">
            {t("difficulty.easy", "Начальный (с подсказкой леммы)")}
          </option>
          <option value="medium">
            {t("difficulty.medium", "Средний (стандартный)")}
          </option>
          <option value="hard">{t("difficulty.hard", "Продвинутый")}</option>
        </select>
      </div>

      {/* Distractor Count */}
      <div>
        <label className="text-xs font-semibold uppercase tracking-wider text-stone-500 block mb-2">
          {t("exerciseConfig.max_distractors", "Количество дистракторов")}:{" "}
          {maxDistractors}
        </label>
        <input
          type="range"
          min={2}
          max={4}
          value={maxDistractors}
          onChange={(e) => onDistractorsChange(Number(e.target.value))}
          className="w-full accent-blue-600"
        />
        <div className="flex justify-between text-xs text-stone-400 mt-1">
          <span>2</span>
          <span>3</span>
          <span>4</span>
        </div>
      </div>

      {/* Execution Call to Action */}
      <div className="pt-2 border-t border-stone-100">
        <button
          type="button"
          onClick={onGenerate}
          disabled={
            totalQuestions === 0 || selectedFormats.length === 0 || isLoading
          }
          className="w-full py-3 px-4 rounded-xl bg-green-600 hover:bg-green-700 text-white font-semibold text-sm shadow-sm transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <span>{t("loading", "Генерация...")}</span>
          ) : (
            <span>
              {t("sentencesMenu.start_exercise", "Начать упражнение")} (
              {totalQuestions})
            </span>
          )}
        </button>
      </div>
    </div>
  );
};
