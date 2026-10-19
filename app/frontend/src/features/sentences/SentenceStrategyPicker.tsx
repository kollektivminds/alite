// src/features/sentences/SentenceStrategyPicker.tsx
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EnumItemFormat } from "../../types";
import {
  EnumSentenceItemGroup,
  ORDERED_SENTENCE_GROUPS,
  SentenceStrategyDefinition,
  SentenceStrategyTooltips,
} from "./SentenceStrategyDefinitions";

interface SentenceStrategyPickerProps {
  /** Map of Strategy Identifier -> Allocated Item Count */
  typeCounts: Record<string, number>;
  /** Dispatches change for an individual strategy */
  onCountChange: (strategyId: string, newCount: number) => void;
  /** Dispatches batch updates (used by Randomize and Reset) */
  onBatchCountChange: (newCounts: Record<string, number>) => void;
  /** Overall target quota from SentenceExerciseConfigPanel */
  targetCount: number;
  /** Currently active session delivery formats (MCQ, FITB, Unscramble) */
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

  // 1. Accordion disclosure state: Initialize with all canonical groups expanded
  const [expandedGroups, setExpandedGroups] = useState<
    Set<EnumSentenceItemGroup>
  >(() => new Set<EnumSentenceItemGroup>(ORDERED_SENTENCE_GROUPS));

  const toggleGroupAccordion = (group: EnumSentenceItemGroup) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) {
        next.delete(group);
      } else {
        next.add(group);
      }
      return next;
    });
  };

  // 2. Partition strategies into pedagogical groups matching ORDERED_SENTENCE_GROUPS
  const groupedStrategies = useMemo(() => {
    const map = new Map<EnumSentenceItemGroup, SentenceStrategyDefinition[]>();
    ORDERED_SENTENCE_GROUPS.forEach((group) => map.set(group, []));

    SentenceStrategyTooltips.forEach((def) => {
      const groupList = map.get(def.group);
      if (groupList) {
        groupList.push(def);
      }
    });

    return map;
  }, []);

  // 3. Compute aggregate allocation telemetry
  const totalAllocatedItems = useMemo(() => {
    return Object.values(typeCounts || {}).reduce(
      (sum, count) => sum + (count || 0),
      0,
    );
  }, [typeCounts]);

  // 4. Identify strategies compatible with currently active session delivery formats
  const viableStrategies = useMemo(() => {
    const activeFormatSet = new Set(enabledFormats);
    return SentenceStrategyTooltips.filter((strat) =>
      strat.supportedFormats.some((fmt) => activeFormatSet.has(fmt)),
    );
  }, [enabledFormats]);

  // 5. Stochastic Distributor: Distribute quota across compatible strategies
  const handleRandomizeDistribution = () => {
    if (viableStrategies.length === 0 || targetCount <= 0) return;

    const randomized: Record<string, number> = {};
    SentenceStrategyTooltips.forEach((strat) => {
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
    SentenceStrategyTooltips.forEach((strat) => {
      cleared[strat.id] = 0;
    });
    onBatchCountChange(cleared);
  };

  const remainingHeadroom = Math.max(0, targetCount - totalAllocatedItems);

  return (
    <div className="flex flex-col gap-5">
      {/* =================================================================== */}
      {/* TELEMETRY & STOCHASTIC ALLOCATION BAR                               */}
      {/* =================================================================== */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-xs flex items-center justify-between transition-colors">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            {t("exercises.settings.questionTypes")}
          </h3>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            {t("exercises.settings.allocated")}:{" "}
            <strong
              className={
                totalAllocatedItems > targetCount
                  ? "text-rose-600 dark:text-rose-400 font-bold"
                  : "text-blue-600 dark:text-blue-400 font-bold"
              }
            >
              {totalAllocatedItems}
            </strong>{" "}
            / {targetCount} {t("exercises.settings.target")}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleResetDistribution}
            disabled={totalAllocatedItems === 0}
            className="rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {t("exercises.settings.reset") || "Reset"}
          </button>

          <button
            type="button"
            onClick={handleRandomizeDistribution}
            disabled={viableStrategies.length === 0 || targetCount <= 0}
            className="rounded bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/50 dark:hover:bg-blue-900/60 px-3 py-1 text-xs font-semibold text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-2xs flex items-center gap-1.5"
          >
            <span>{t("exercises.settings.randomize")}</span>
          </button>
        </div>
      </div>

      {/* =================================================================== */}
      {/* HIERARCHICAL STRATEGY ACCORDION LIST                                */}
      {/* =================================================================== */}
      <div className="space-y-4">
        {ORDERED_SENTENCE_GROUPS.map((groupName) => {
          const strategies = groupedStrategies.get(groupName) || [];
          if (strategies.length === 0) return null;

          const isExpanded = expandedGroups.has(groupName);

          // Calculate total items allocated within this specific category
          const groupAllocatedCount = strategies.reduce(
            (sum, s) => sum + (typeCounts[s.id] || 0),
            0,
          );

          return (
            <div
              key={groupName}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden shadow-xs transition-colors"
            >
              {/* Category Accordion Header */}
              <button
                type="button"
                onClick={() => toggleGroupAccordion(groupName)}
                aria-expanded={isExpanded}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-50/80 hover:bg-slate-100/90 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-left transition-colors select-none"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    {t(`exercises.sentencesMenu.groups.${groupName}`)}
                  </span>
                  <span className="text-[11px] text-slate-400 font-mono">
                    ({strategies.length})
                  </span>
                </div>

                <div className="flex items-center gap-2.5">
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
                  <span className="text-slate-400 text-xs font-mono">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>
              </button>

              {/* Accordion Content Area */}
              {isExpanded && (
                <div className="p-3.5 border-t border-slate-100 dark:border-slate-700/60 space-y-3 bg-slate-50/30 dark:bg-slate-900/20">
                  {strategies.map((def) => {
                    const currentCount = typeCounts[def.id] || 0;
                    const maxAllowedForThis = currentCount + remainingHeadroom;
                    const isViable = def.supportedFormats.some((fmt) =>
                      enabledFormats.includes(fmt),
                    );

                    return (
                      <div
                        key={def.id}
                        className={`rounded-lg border p-3.5 transition-all ${
                          !isViable
                            ? "border-slate-200/40 bg-slate-100/40 dark:border-slate-800/40 dark:bg-slate-900/40 opacity-50"
                            : currentCount > 0
                              ? "border-blue-300 bg-blue-50/30 dark:border-blue-900/60 dark:bg-blue-950/20 shadow-2xs"
                              : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 shadow-2xs hover:border-slate-300"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          {/* Left Column: Metadata & Linguistic Spec */}
                          <div className="space-y-1.5 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                                {def.label}
                              </span>
                              <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">
                                [{def.id}]
                              </span>
                              {!isViable && (
                                <span className="text-[10px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50 px-1.5 py-0.2 rounded border border-amber-200 dark:border-amber-800">
                                  Format Disabled
                                </span>
                              )}
                            </div>

                            <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                              {def.description}
                            </p>

                            {/* Linguistic Stem & Key Example Scaffolding */}
                            {def.stemExample && (
                              <div className="mt-2 rounded bg-slate-50 dark:bg-slate-900/60 p-2 border border-slate-200/70 dark:border-slate-700/70 text-[11px] font-mono text-slate-700 dark:text-slate-300 flex items-center justify-between gap-2">
                                <div className="truncate">
                                  <span className="text-slate-400 text-[10px] font-semibold uppercase mr-1.5">
                                    {t("exercises.settings.ex")}:
                                  </span>
                                  <span>{def.stemExample}</span>
                                </div>
                                {def.keyExample && (
                                  <span className="shrink-0 font-bold text-emerald-600 dark:text-emerald-400">
                                    → {def.keyExample}
                                  </span>
                                )}
                              </div>
                            )}

                            {/* Format Pill Tags */}
                            <div className="mt-2.5 flex items-center gap-1.5 pt-2 border-t border-slate-100 dark:border-slate-700/40">
                              <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold">
                                {t("exercises.settings.formats.format") ||
                                  "Formats"}
                                :
                              </span>
                              <div className="flex gap-1 flex-wrap">
                                {def.supportedFormats.map((fmt) => {
                                  const isFmtActive =
                                    enabledFormats.includes(fmt);
                                  return (
                                    <span
                                      key={fmt}
                                      className={`rounded px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wider ${
                                        isFmtActive
                                          ? "bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-200"
                                          : "bg-slate-100/50 dark:bg-slate-800 text-slate-400 dark:text-slate-600 line-through"
                                      }`}
                                    >
                                      {fmt}
                                    </span>
                                  );
                                })}
                              </div>
                            </div>
                          </div>

                          {/* Right Column: Numeric Counter Controls */}
                          <div className="flex items-center gap-1.5 select-none shrink-0 pt-0.5">
                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(
                                  def.id,
                                  Math.max(0, currentCount - 1),
                                )
                              }
                              disabled={currentCount === 0 || !isViable}
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                              aria-label={`Decrease count for ${def.label}`}
                            >
                              -
                            </button>

                            <input
                              type="number"
                              min={0}
                              max={maxAllowedForThis}
                              value={currentCount}
                              disabled={!isViable}
                              onChange={(e) =>
                                onCountChange(
                                  def.id,
                                  Math.max(
                                    0,
                                    Math.min(
                                      maxAllowedForThis,
                                      parseInt(e.target.value, 10) || 0,
                                    ),
                                  ),
                                )
                              }
                              className="w-12 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-1 py-1 text-center text-xs font-bold font-mono text-slate-800 dark:text-slate-100 focus:border-blue-500 focus:outline-none disabled:opacity-40 shadow-2xs"
                            />

                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(def.id, currentCount + 1)
                              }
                              disabled={
                                !isViable || totalAllocatedItems >= targetCount
                              }
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                              aria-label={`Increase count for ${def.label}`}
                            >
                              +
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
