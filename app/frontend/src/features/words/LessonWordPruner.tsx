// src/features/words/LessonWordPruner.tsx
import React, { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Lemma } from "../../types/words";

export type PosCategory =
  | "Nouns"
  | "Verbs"
  | "Adjectives"
  | "Participles"
  | "Other";

interface PrunerProps {
  lessonLemmas: Lemma[];
  manualLemmas: Lemma[];
  excludedIds: string[];
  onToggleExclude: (id: string) => void;
  onToggleBatchExclude?: (ids: string[], shouldExclude: boolean) => void; // Dispatches bulk POS toggle
  onRemoveManual: (id: string) => void;
}

export function normalizePos(rawPos?: string): PosCategory {
  if (!rawPos) return "Other";
  const tag = rawPos.toUpperCase();
  if (tag.includes("NOUN") || tag === "S" || tag === "SUBST") return "Nouns";
  if (tag.includes("VERB") || tag === "V") return "Verbs";
  if (tag.includes("ADJ") || tag === "A") return "Adjectives";
  if (tag.includes("PART") || tag.includes("PRT")) return "Participles";
  return "Other";
}

export const LessonWordPruner: React.FC<PrunerProps> = ({
  lessonLemmas,
  manualLemmas,
  excludedIds,
  onToggleExclude,
  onToggleBatchExclude,
  onRemoveManual,
}) => {
  const { t } = useTranslation();
  const excludedSet = useMemo(
    () => new Set(excludedIds.map(String)),
    [excludedIds],
  );

  // Combine curriculum items (which respect exclusions) with manual items
  const activePool = useMemo(() => {
    const listActive = lessonLemmas.filter(
      (item) => !excludedSet.has(String(item.id)),
    );
    return [...listActive, ...manualLemmas];
  }, [lessonLemmas, manualLemmas, excludedSet]);

  /**
   * Evaluates category metrics across the curriculum pool:
   * Tracks total available vs active count so buttons persist even at count 0.
   */
  const posMetrics = useMemo(() => {
    const categories: PosCategory[] = [
      "Nouns",
      "Verbs",
      "Adjectives",
      "Participles",
      "Other",
    ];
    const metrics: Record<
      PosCategory,
      { total: number; active: number; ids: string[] }
    > = {
      Nouns: { total: 0, active: 0, ids: [] },
      Verbs: { total: 0, active: 0, ids: [] },
      Adjectives: { total: 0, active: 0, ids: [] },
      Participles: { total: 0, active: 0, ids: [] },
      Other: { total: 0, active: 0, ids: [] },
    };

    lessonLemmas.forEach((item) => {
      const cat = normalizePos(item.pos);
      const idStr = String(item.id);
      metrics[cat].total += 1;
      metrics[cat].ids.push(idStr);
      if (!excludedSet.has(idStr)) {
        metrics[cat].active += 1;
      }
    });

    return metrics;
  }, [lessonLemmas, excludedSet]);

  /**
   * Toggles an entire POS category in a single click:
   * If any members are active -> exclude all of them.
   * If all members are already excluded -> re-include all of them.
   */
  const handleTogglePosCategory = useCallback(
    (category: PosCategory) => {
      if (!onToggleBatchExclude) return;

      const { ids, active } = posMetrics[category];
      if (ids.length === 0) return;

      // If at least one word in this category is currently active, exclude all of them
      const shouldExclude = active > 0;
      onToggleBatchExclude(ids, shouldExclude);
    },
    [posMetrics, onToggleBatchExclude],
  );

  if (lessonLemmas.length === 0 && manualLemmas.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="pruner-heading" className="space-y-4">
      {/* Header & Subtext */}
      <div>
        <h3
          id="pruner-heading"
          className="text-lg font-semibold text-gray-900 dark:text-gray-100"
        >
          {t("exercises.wordsMenu.refinePool")}
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {t("exercises.wordsMenu.clickToExclude")}
        </p>

        {/* Interactive POS Filter Buttons */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
            {t("exercises.wordsMenu.activeDist")}:
          </span>

          {(Object.keys(posMetrics) as PosCategory[]).map((pos) => {
            const { total, active } = posMetrics[pos];
            if (total === 0) return null; // Only show parts of speech present in current lists

            const isFullyExcluded = active === 0;
            const isPartiallyExcluded = active > 0 && active < total;

            return (
              <button
                key={pos}
                type="button"
                onClick={() => handleTogglePosCategory(pos)}
                aria-pressed={!isFullyExcluded}
                title={`Click to ${isFullyExcluded ? "include" : "exclude"} all ${pos}`}
                className={`
                  inline-flex items-center gap-1.5 rounded-md px-2.5 py-1 text-xs font-medium transition-all
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1
                  ${
                    isFullyExcluded
                      ? "border border-dashed border-red-300 bg-red-50 text-red-600 opacity-60 hover:opacity-100 dark:border-red-800 dark:bg-red-950/20 dark:text-red-400"
                      : isPartiallyExcluded
                        ? "border border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-200"
                        : "border border-gray-200 bg-white text-gray-700 shadow-sm hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
                  }
                `}
              >
                <span>
                  {t(`exercises.wordsMenu.strategies.${pos}`) || pos}:
                </span>
                <span
                  className={`font-bold ${
                    isFullyExcluded
                      ? "text-red-500 line-through"
                      : isPartiallyExcluded
                        ? "text-amber-600 dark:text-amber-400"
                        : "text-blue-600 dark:text-blue-400"
                  }`}
                >
                  {active}/{total}
                </span>
                <span className="text-[10px]" aria-hidden="true">
                  {isFullyExcluded ? "✕" : "✓"}
                </span>
              </button>
            );
          })}

          <span className="text-xs text-gray-400 dark:text-gray-500 font-mono">
            ({activePool.length}{" "}
            {t("exercises.wordsMenu.totalActive", { count: activePool.length })}
            )
          </span>
        </div>
      </div>

      {/* Lemma Chip Staging Canvas */}
      <div className="max-h-72 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/40">
        <div className="flex flex-wrap gap-2">
          {/* Curriculum Lemmas (Toggled via Individual Chip or POS Category Button) */}
          {lessonLemmas.map((item) => {
            const isExcluded = excludedSet.has(String(item.id));
            const displayText = item.lem_canon ?? item.lem_text ?? "—";

            return (
              <button
                key={`list-${item.id}`}
                type="button"
                onClick={() => onToggleExclude(String(item.id))}
                aria-pressed={!isExcluded}
                className={`
                  inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  ${
                    isExcluded
                      ? "border border-dashed border-red-300 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300 opacity-60"
                      : "border border-gray-200 bg-white text-gray-800 shadow-sm hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
                  }
                `}
              >
                <span className="font-semibold tracking-wide">
                  {displayText}
                </span>
                <span className="text-[10px] text-gray-400 uppercase tracking-tight">
                  ({item.pos})
                </span>
                <span
                  className={`text-[11px] font-bold ${
                    isExcluded
                      ? "text-red-500"
                      : "text-emerald-600 dark:text-emerald-400"
                  }`}
                  aria-hidden="true"
                >
                  {isExcluded ? "✕" : "✓"}
                </span>
              </button>
            );
          })}

          {/* Ad-Hoc Individually Added Lemmas */}
          {manualLemmas.map((item) => {
            const displayText = item.lem_canon ?? item.lem_text ?? "—";

            return (
              <button
                key={`manual-${item.id}`}
                type="button"
                onClick={() => onRemoveManual(String(item.id))}
                className="
                  inline-flex items-center gap-1.5 rounded-full border border-blue-300 bg-blue-50 px-3 py-1 text-xs font-medium text-blue-900 shadow-sm transition-colors
                  hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  dark:border-blue-700 dark:bg-blue-900/40 dark:text-blue-100 dark:hover:bg-blue-900/60
                "
              >
                <span className="font-semibold tracking-wide">
                  {displayText}
                </span>
                <span className="text-[10px] text-blue-400 uppercase tracking-tight">
                  ({item.pos})
                </span>
                <span
                  className="text-[11px] font-bold text-blue-500"
                  aria-label={t("exercises.wordsMenu.removeWord")}
                >
                  ✕
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </section>
  );
};
