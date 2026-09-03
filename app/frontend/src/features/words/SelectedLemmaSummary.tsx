// src/components/words/SelectedLemmaSummary.tsx
import React, { useMemo } from "react";
import { Lemma } from "../../types";

interface SelectedLemmaSummaryProps {
  activeLemmas: Lemma[];
  manualLemmas: Lemma[];
  onRemoveManual: (id: string) => void;
  onExcludeLemma: (id: string) => void;
}

export const SelectedLemmaSummary: React.FC<SelectedLemmaSummaryProps> = ({
  activeLemmas,
  manualLemmas,
  onRemoveManual,
  onExcludeLemma,
}) => {
  // O(1) membership lookup for origin routing
  const manualIdSet = useMemo(
    () => new Set(manualLemmas.map((l) => l.id)),
    [manualLemmas],
  );

  return (
    <div className="rounded-lg border border-gray-200 bg-gray-50/60 p-4 dark:border-gray-700 dark:bg-gray-800/40">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300">
          Selected Target Pool
        </h3>
        <span className="inline-flex items-center rounded-full bg-indigo-100 px-2.5 py-0.5 text-xs font-semibold text-indigo-800 dark:bg-indigo-900/50 dark:text-indigo-300">
          Count: {activeLemmas.length}
        </span>
      </div>

      {activeLemmas.length === 0 ? (
        <p className="text-xs italic text-gray-500 dark:text-gray-400">
          No lemmas selected. Pick a curriculum list or search for individual
          items above.
        </p>
      ) : (
        <div className="flex flex-wrap gap-1.5">
          {activeLemmas.map((lemma) => {
            const isManual = manualIdSet.has(lemma.id);

            return (
              <span
                key={lemma.id}
                className={`
                  inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-xs font-medium
                  ${
                    isManual
                      ? "border-emerald-300 bg-emerald-50 text-emerald-900 dark:border-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-200"
                      : "border-gray-200 bg-white text-gray-800 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200"
                  }
                `}
              >
                <span>{lemma.lemma}</span>
                <span className="opacity-60">({lemma.pos})</span>

                <button
                  type="button"
                  onClick={() =>
                    isManual
                      ? onRemoveManual(lemma.id)
                      : onExcludeLemma(lemma.id)
                  }
                  className="ml-0.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full hover:bg-black/10 focus:outline-none dark:hover:bg-white/20"
                  aria-label={`Remove ${lemma.lemma}`}
                >
                  <svg
                    className="h-2.5 w-2.5"
                    viewBox="0 0 12 12"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      d="M2 2L10 10M10 2L2 10"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                    />
                  </svg>
                </button>
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
};
