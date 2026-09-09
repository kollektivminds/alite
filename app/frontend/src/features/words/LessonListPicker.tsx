import React from "react";
import { LessonList } from "../../types/words";

interface LessonListPickerProps {
  lessonLists: LessonList[];
  selectedIds: string[];
  onToggleList: (id: string) => void;
  onClearAll: () => void; // Declarative reset handler
}

export const LessonListPicker: React.FC<LessonListPickerProps> = ({
  lessonLists,
  selectedIds,
  onToggleList,
  onClearAll,
}) => {
  if (lessonLists.length === 0) {
    return (
      <div className="rounded-lg border-2 border-dashed border-gray-300 p-6 text-center text-gray-500">
        No curriculum lists available to load.
      </div>
    );
  }

  const hasSelections = selectedIds.length > 0;

  return (
    <section aria-labelledby="lesson-picker-heading">
      {/* Header bar with counter and reset trigger */}
      <div className="mb-4 flex items-center justify-between">
        <h2
          id="lesson-picker-heading"
          className="text-lg font-medium text-gray-900 dark:text-gray-100"
        >
          1. Base Curriculum Modules
        </h2>

        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">
            {selectedIds.length} list{selectedIds.length !== 1 ? "s" : ""}{" "}
            selected
          </span>

          {/* Render reset button only when active lists exist */}
          {hasSelections && (
            <button
              type="button"
              onClick={onClearAll}
              className="text-xs font-semibold text-red-600 hover:text-red-700 hover:underline focus:outline-none focus:ring-1 focus:ring-red-500 rounded px-1.5 py-0.5 dark:text-red-400 dark:hover:text-red-300"
              aria-label="Deselect all curriculum modules"
            >
              Deselect All
            </button>
          )}
        </div>
      </div>

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
                        : "border-gray-300 bg-transparent"
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
                  {list.has_lemma?.length || 0} lexical items
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
