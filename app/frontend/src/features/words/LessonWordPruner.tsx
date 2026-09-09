import React, { useMemo } from "react";
import { Lemma } from "../../types/words";

interface PrunerProps {
  lessonLemmas: Lemma[];
  manualLemmas: Lemma[];
  excludedIds: string[];
  onToggleExclude: (id: string) => void;
  onRemoveManual: (id: string) => void;
}

// Canonical pedagogical categories for student reference
type PosCategory = "Nouns" | "Verbs" | "Adjectives" | "Participles" | "Other";

function normalizePos(rawPos?: string): PosCategory {
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
  onRemoveManual,
}) => {
  const excludedSet = useMemo(() => new Set(excludedIds), [excludedIds]);

  // Combine active pools and eliminate items currently excluded
  const activePool = useMemo(() => {
    const listActive = lessonLemmas.filter((item) => !excludedSet.has(item.id));
    return [...listActive, ...manualLemmas];
  }, [lessonLemmas, manualLemmas, excludedSet]);

  // Aggregate lexical counts by part of speech
  const posCounts = useMemo(() => {
    const counts: Record<PosCategory, number> = {
      Nouns: 0,
      Verbs: 0,
      Adjectives: 0,
      Participles: 0,
      Other: 0,
    };

    activePool.forEach((item) => {
      const category = normalizePos(item.pos);
      counts[category] = (counts[category] || 0) + 1;
    });

    return counts;
  }, [activePool]);

  if (lessonLemmas.length === 0 && manualLemmas.length === 0) {
    return null;
  }

  return (
    <section aria-labelledby="pruner-heading" className="space-y-4">
      {/* Header & Functional Subtext */}
      <div>
        <h3
          id="pruner-heading"
          className="text-lg font-semibold text-gray-900 dark:text-gray-100"
        >
          Refine Final Vocabulary Pool
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Click a curriculum item to exclude it, or a custom word to remove it.
        </p>

        {/* POS Metrics Strip */}
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-400 dark:text-gray-500">
            Active Distribution:
          </span>
          {Object.entries(posCounts).map(([pos, count]) => {
            if (count === 0) return null;
            return (
              <span
                key={pos}
                className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300"
              >
                <span>{pos}:</span>
                <span className="font-bold text-blue-600 dark:text-blue-400">
                  {count}
                </span>
              </span>
            );
          })}
          <span className="text-xs text-gray-400">
            ({activePool.length} total active)
          </span>
        </div>
      </div>

      {/* Lemma Chip Staging Canvas */}
      <div className="max-h-72 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-800/40">
        <div className="flex flex-wrap gap-2">
          {/* 1. Base Curriculum Lemmas */}
          {lessonLemmas.map((item) => {
            const isExcluded = excludedSet.has(item.id);
            const displayText = item.lem_canon ?? item.lem_text ?? "—";

            return (
              <button
                key={`list-${item.id}`}
                type="button"
                onClick={() => onToggleExclude(item.id)}
                aria-pressed={!isExcluded}
                className={`
                  inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
                  ${
                    isExcluded
                      ? "border border-dashed border-red-300 bg-red-50 text-red-700 hover:bg-red-100 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300"
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

          {/* 2. Individually Added Lemmas */}
          {manualLemmas.map((item) => {
            const displayText = item.lem_canon ?? item.lem_text ?? "—";

            return (
              <button
                key={`manual-${item.id}`}
                type="button"
                onClick={() => onRemoveManual(item.id)}
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
                  aria-label="Remove word"
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
