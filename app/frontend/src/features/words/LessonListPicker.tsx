// src/features/words/LessonListPicker.tsx
import React, { useCallback } from "react";
import { useTranslation } from "react-i18next";
import { LessonList } from "../../types";

interface LessonListPickerProps {
  lessonLists: LessonList[];
  selectedIds: string[];
  onToggleList: (id: string) => void;
  onSelectRandom?: (ids: string[]) => void; // Dispatches randomly sampled list IDs
  onClearAll: () => void;
}

export const LessonListPicker: React.FC<LessonListPickerProps> = ({
  lessonLists,
  selectedIds,
  onToggleList,
  onSelectRandom,
  onClearAll,
}) => {
  const { t } = useTranslation();

  /**
   * Deterministic sampling utility:
   * Selects an assortment of 2 to 3 lists (or all available if total <= 2).
   */
  const handleRandomize = useCallback(() => {
    if (!onSelectRandom || lessonLists.length === 0) return;

    const totalLists = lessonLists.length;
    // Target sample size: between 2 and 3 lists, bounded by total list count
    const sampleSize =
      totalLists <= 2 ? totalLists : Math.floor(Math.random() * 2) + 2;

    // Fast Fisher-Yates array shuffle
    const shuffled = [...lessonLists];
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }

    const randomIds = shuffled
      .slice(0, sampleSize)
      .map((list) => String(list.id));
    onSelectRandom(randomIds);
  }, [lessonLists, onSelectRandom]);

  if (lessonLists.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center text-gray-500 dark:border-gray-700 dark:text-gray-400">
        {t("exercises.wordsMenu.noLists")}
      </div>
    );
  }

  const hasSelections = selectedIds.length > 0;

  return (
    <section aria-labelledby="lesson-picker-heading">
      {/* Header Bar with Counter, Randomize, and Deselect All */}
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <h2
          id="lesson-picker-heading"
          className="text-lg font-medium text-gray-900 dark:text-gray-100"
        >
          {t("exercises.wordsMenu.lessonLists")}
        </h2>

        <div className="flex items-center gap-2.5">
          <span className="text-xs text-gray-500 dark:text-gray-400 font-mono">
            {selectedIds.length}{" "}
            {t("exercises.wordsMenu.list", { count: selectedIds.length })}{" "}
            {t("exercises.wordsMenu.selected", { count: selectedIds.length })}
          </span>

          {/* Random Curriculum Selection Trigger */}
          {onSelectRandom && lessonLists.length > 1 && (
            <button
              type="button"
              onClick={handleRandomize}
              className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 shadow-sm hover:bg-blue-100 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300 dark:hover:bg-blue-900/50 transition-colors focus:outline-none focus:ring-1 focus:ring-blue-500"
              title="Select a random set of curriculum lists"
            >
              <span>{t("exercises.settings.randomize")}</span>
            </button>
          )}

          {/* Deselect All Action */}
          {hasSelections && (
            <button
              type="button"
              onClick={onClearAll}
              className="text-xs font-semibold text-red-600 hover:text-red-700 hover:underline focus:outline-none focus:ring-1 focus:ring-red-500 rounded px-1.5 py-0.5 dark:text-red-400 dark:hover:text-red-300 transition-colors"
              aria-label="Deselect all curriculum modules"
            >
              {t("exercises.wordsMenu.deselectAll")}
            </button>
          )}
        </div>
      </div>

      {/* Grid of Selectable Lists */}
      <div className="max-h-96 overflow-y-auto pr-2">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {lessonLists.map((list) => {
            const safeListId = String(list.id);
            const isSelected = selectedIds.includes(safeListId);

            return (
              <button
                key={safeListId}
                type="button"
                onClick={() => onToggleList(safeListId)}
                aria-pressed={isSelected}
                className={`
                  relative flex cursor-pointer flex-col rounded-lg border p-4 text-left shadow-sm
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  transition-all duration-200 ease-in-out
                  ${
                    isSelected
                      ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500 dark:bg-blue-900/20"
                      : "border-gray-300 bg-white hover:border-gray-400 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:hover:bg-gray-700"
                  }
                `}
              >
                <div className="flex w-full items-center justify-between">
                  <span
                    className={`block text-sm font-semibold ${
                      isSelected
                        ? "text-blue-900 dark:text-blue-100"
                        : "text-gray-900 dark:text-gray-100"
                    }`}
                  >
                    {list.title || "Untitled List"}
                  </span>

                  <div
                    className={`flex h-5 w-5 items-center justify-center rounded-full border ${
                      isSelected
                        ? "border-blue-600 bg-blue-600 text-white"
                        : "border-gray-300 bg-transparent dark:border-gray-600"
                    }`}
                  >
                    {isSelected && (
                      <svg
                        className="h-3 w-3"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>
                </div>

                <span className="mt-2 block text-xs text-gray-400 dark:text-gray-500">
                  {t("exercises.numWords", { count: list.has_lemma?.length })}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
