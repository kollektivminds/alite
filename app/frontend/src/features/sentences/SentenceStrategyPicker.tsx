/**
 * src/features/sentences/SentenceStrategyPicker.tsx
 *
 * Categorized strategy selector for sentence-level drills.
 * Features:
 * - Independent collapsible category accordions mirroring Words ExerciseConfigPanel
 * - Telemetry header with aggregate allocation status
 * - Uniform stochastic distributor (Randomize) and bulk Reset
 * - WAI-ARIA compliant disclosure buttons
 */

import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import type { StrategyGroup } from "../../types";
import type { EnumItemFormat } from "../../types/exercise";

// ============================================================================
// Canonical Strategy Definitions (Aligned with EnumSentItemType in models.py)
// ============================================================================
export const SENTENCE_STRATEGY_GROUPS: StrategyGroup[] = [
  {
    groupKey: "sentencesMenu.group_cloze",
    strategies: [
      {
        id: "noun_morph",
        labelKey: "sentencesMenu.strategies.nounMorph",
        descriptionKey: "sentencesMenu.desc_noun_morph",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "adjective_morph",
        labelKey: "sentencesMenu.strategies.adjectiveMorph",
        descriptionKey: "sentencesMenu.desc_adj_morph",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "verb_morph",
        labelKey: "sentencesMenu.strategies.verbMorph",
        descriptionKey: "sentencesMenu.desc_verb_morph",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "lexical",
        labelKey: "sentencesMenu.strategies.lexical",
        descriptionKey: "sentencesMenu.desc_lexical",
        supportedFormats: ["mcq"],
      },
    ],
  },
  {
    groupKey: "sentencesMenu.group_word_order",
    strategies: [
      {
        id: "unscramble",
        labelKey: "sentencesMenu.strategies.unscramble",
        descriptionKey: "sentencesMenu.desc_unscramble",
        supportedFormats: ["unscramble"],
      },
    ],
  },
  {
    groupKey: "sentencesMenu.group_syntax",
    strategies: [
      {
        id: "dep_rel",
        labelKey: "sentencesMenu.strategies.depRel",
        descriptionKey: "sentencesMenu.desc_dep_rel",
        supportedFormats: ["mcq"],
      },
      {
        id: "find_head",
        labelKey: "sentencesMenu.strategies.findHead",
        descriptionKey: "sentencesMenu.desc_find_head",
        supportedFormats: ["mcq"],
      },
      {
        id: "find_subject",
        labelKey: "sentencesMenu.strategies.findSubject",
        descriptionKey: "sentencesMenu.desc_find_subject",
        supportedFormats: ["mcq"],
      },
      {
        id: "noun_case",
        labelKey: "sentencesMenu.strat_noun_case",
        descriptionKey: "sentencesMenu.desc_noun_case",
        supportedFormats: ["mcq"],
      },
      {
        id: "verb_aspect",
        labelKey: "sentencesMenu.strat_verb_aspect",
        descriptionKey: "sentencesMenu.desc_verb_aspect",
        supportedFormats: ["mcq"],
      },
    ],
  },
];

interface SentenceStrategyPickerProps {
  typeCounts: Record<string, number>;
  onCountChange: (strategyId: string, newCount: number) => void;
  onBatchCountChange: (newCounts: Record<string, number>) => void;
  targetCount: number;
  enabledFormats: EnumItemFormat[];
}

export const SentenceStrategyPicker: React.FC<SentenceStrategyPickerProps> = ({
  typeCounts,
  onCountChange,
  onBatchCountChange,
  targetCount,
  enabledFormats,
}) => {
  const { t } = useTranslation();

  // 1. Accordion Disclosure State: Initializes with all category groups expanded
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(
    () => new Set<string>(SENTENCE_STRATEGY_GROUPS.map((g) => g.groupKey)),
  );

  const toggleGroupAccordion = (groupKey: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(groupKey)) {
        next.delete(groupKey);
      } else {
        next.add(groupKey);
      }
      return next;
    });
  };

  // 2. Aggregate allocation telemetry
  const totalAllocatedItems = Object.values(typeCounts || {}).reduce(
    (sum, count) => sum + (count || 0),
    0,
  );

  const allStrategies = SENTENCE_STRATEGY_GROUPS.flatMap((g) => g.strategies);

  // Strategies compatible with currently enabled delivery formats
  const viableStrategies = allStrategies.filter((strat) =>
    strat.supportedFormats.some((fmt) => enabledFormats.includes(fmt)),
  );

  // 3. Stochastic distributor matching Words ExerciseConfigPanel
  const handleRandomizeDistribution = () => {
    if (viableStrategies.length === 0 || targetCount <= 0) return;

    const randomized: Record<string, number> = {};
    allStrategies.forEach((strat) => {
      randomized[strat.id] = 0;
    });

    for (let i = 0; i < targetCount; i++) {
      const randomIndex = Math.floor(Math.random() * viableStrategies.length);
      const chosenStrategy = viableStrategies[randomIndex];
      randomized[chosenStrategy.id] = (randomized[chosenStrategy.id] || 0) + 1;
    }

    onBatchCountChange(randomized);
  };

  const handleResetDistribution = () => {
    const cleared: Record<string, number> = {};
    allStrategies.forEach((strat) => {
      cleared[strat.id] = 0;
    });
    onBatchCountChange(cleared);
  };

  return (
    <div className="flex flex-col gap-4">
      {/* =================================================================== */}
      {/* TELEMETRY & STOCHASTIC ALLOCATION BAR                               */}
      {/* =================================================================== */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex items-center justify-between transition-colors">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            {t("exercises.formats.questionTypes")}
          </h3>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            {t("exercises.sentencesMenu.allocated")}:{" "}
            <strong
              className={
                totalAllocatedItems > targetCount
                  ? "text-red-500 font-bold"
                  : "text-blue-600 dark:text-blue-400 font-bold"
              }
            >
              {totalAllocatedItems}
            </strong>{" "}
            / {targetCount} {t("exercises.sentencesMenu.target")}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetDistribution}
            disabled={totalAllocatedItems === 0}
            className="rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {t("exercises.settings.reset")}
          </button>

          <button
            type="button"
            onClick={handleRandomizeDistribution}
            disabled={viableStrategies.length === 0 || targetCount <= 0}
            className="rounded bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/50 dark:hover:bg-blue-900/60 px-3 py-1 text-xs font-semibold text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-2xs flex items-center gap-1.5"
          >
            <span>🎲</span>
            <span>{t("exercises.settings.randomize")}</span>
          </button>
        </div>
      </div>

      {/* =================================================================== */}
      {/* HIERARCHICAL STRATEGY ACCORDION LIST                                */}
      {/* =================================================================== */}
      <div className="space-y-3">
        {SENTENCE_STRATEGY_GROUPS.map((group) => {
          const isExpanded = expandedGroups.has(group.groupKey);

          // Calculate total items allocated within this specific category
          const groupAllocatedCount = group.strategies.reduce(
            (sum, s) => sum + (typeCounts[s.id] || 0),
            0,
          );

          return (
            <div
              key={group.groupKey}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden shadow-sm transition-colors"
            >
              {/* Accordion Trigger Header */}
              <button
                type="button"
                onClick={() => toggleGroupAccordion(group.groupKey)}
                aria-expanded={isExpanded}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-50/70 hover:bg-slate-100/80 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-left transition-colors select-none"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    {t(group.groupKey, group.groupKey.split(".").pop())}
                  </span>
                  <span className="text-[11px] text-slate-400">
                    ({group.strategies.length})
                  </span>
                </div>

                <div className="flex items-center gap-2.5">
                  {/* Category Telemetry Badge */}
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                      groupAllocatedCount > 0
                        ? "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300"
                        : "bg-slate-200/60 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
                    }`}
                  >
                    {groupAllocatedCount}{" "}
                    {t("exercises.settings.item", {
                      count: groupAllocatedCount,
                    })}
                  </span>

                  {/* Collapse Chevron Indicator */}
                  <span className="text-slate-400 text-xs font-mono">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>
              </button>

              {/* Collapsible Content Area */}
              {isExpanded && (
                <div className="p-4 border-t border-slate-100 dark:border-slate-700/60 bg-white dark:bg-slate-800/50 space-y-3">
                  <div className="grid grid-cols-1 gap-2.5">
                    {group.strategies.map((strat) => {
                      const currentCount = typeCounts[strat.id] || 0;
                      const isViable = strat.supportedFormats.some((fmt) =>
                        enabledFormats.includes(fmt),
                      );

                      return (
                        <div
                          key={strat.id}
                          className={`flex items-center justify-between p-3 rounded-lg border transition-all ${
                            !isViable
                              ? "bg-slate-50/50 dark:bg-slate-900/20 border-slate-200/40 dark:border-slate-800/40 opacity-50"
                              : currentCount > 0
                                ? "bg-blue-50/40 dark:bg-blue-950/20 border-blue-200 dark:border-blue-900/60"
                                : "bg-slate-50/80 dark:bg-slate-900/40 border-slate-200/80 dark:border-slate-700/60 hover:border-slate-300 dark:hover:border-slate-600"
                          }`}
                        >
                          {/* Strategy Label, Description, and Formats */}
                          <div className="flex flex-col pr-4">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium text-slate-900 dark:text-slate-100">
                                {t(strat.labelKey, strat.id)}
                              </span>
                              {!isViable && (
                                <span className="text-[10px] text-amber-600 dark:text-amber-400 italic">
                                  (Формат выключен)
                                </span>
                              )}
                            </div>

                            <span className="text-xs text-slate-500 dark:text-slate-400 mt-0.5 leading-snug">
                              {t(strat.descriptionKey, "")}
                            </span>

                            {/* Format Pill Tags */}
                            <div className="flex items-center gap-1.5 mt-2">
                              <span className="text-[9px] uppercase tracking-wider text-slate-400">
                                Форматы:
                              </span>
                              {strat.supportedFormats.map((fmt) => (
                                <span
                                  key={fmt}
                                  className={`rounded px-1.5 py-0.2 text-[9px] font-semibold uppercase ${
                                    enabledFormats.includes(fmt)
                                      ? "bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200"
                                      : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-600 line-through"
                                  }`}
                                >
                                  {fmt}
                                </span>
                              ))}
                            </div>
                          </div>

                          {/* Stepper Controls */}
                          <div className="flex items-center gap-2 select-none shrink-0">
                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(
                                  strat.id,
                                  Math.max(0, currentCount - 1),
                                )
                              }
                              disabled={currentCount === 0 || !isViable}
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                            >
                              -
                            </button>

                            <span className="w-6 text-center text-sm font-semibold font-mono text-slate-800 dark:text-slate-200">
                              {currentCount}
                            </span>

                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(strat.id, currentCount + 1)
                              }
                              disabled={!isViable}
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
