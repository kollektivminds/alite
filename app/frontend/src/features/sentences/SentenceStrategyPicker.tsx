// src/features/sentences/SentenceStrategyPicker.tsx
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  EnumSentenceItemGroup,
  ORDERED_SENTENCE_GROUPS,
  SentenceStrategyDefinition,
  SentenceStrategyTooltips,
} from "./SentenceStrategyDefinitions";

interface SentenceStrategyPickerProps {
  /** Map of strategy key to item count */
  typeCounts: Record<string, number>;
  /** Callback when an individual strategy count changes */
  onCountChange: (strategyId: string, newCount: number) => void;
  /** Callback for bulk state operations (Randomize / Reset) */
  onBatchCountChange: (newCounts: Record<string, number>) => void;
  /** Maximum items budget defined in the parent config */
  targetCount: number;
  /** Trigger to collapse all accordions on global reset */
  onResetAll?: () => void;
}

export const SentenceStrategyPicker: React.FC<SentenceStrategyPickerProps> = ({
  typeCounts,
  onCountChange,
  onBatchCountChange,
  targetCount,
  onResetAll,
}) => {
  const { t } = useTranslation();

  // 1. STANDARD: Accordions start completely collapsed
  const [expandedGroups, setExpandedGroups] = useState<
    Set<EnumSentenceItemGroup>
  >(() => new Set<EnumSentenceItemGroup>());

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

  // Group strategy definitions hierarchically
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

  // Compute total questions currently allocated
  const totalAllocatedItems = useMemo(() => {
    return Object.values(typeCounts || {}).reduce(
      (sum, count) => sum + (count || 0),
      0,
    );
  }, [typeCounts]);

  const remainingHeadroom = Math.max(0, targetCount - totalAllocatedItems);

  // 2. Uniform Randomization: Distribute across all valid strategies
  const handleRandomizeDistribution = () => {
    if (SentenceStrategyTooltips.length === 0 || targetCount <= 0) return;

    const randomized: Record<string, number> = {};
    SentenceStrategyTooltips.forEach((strat) => {
      randomized[strat.id] = 0;
    });

    for (let i = 0; i < targetCount; i++) {
      const randomIndex = Math.floor(
        Math.random() * SentenceStrategyTooltips.length,
      );
      const chosenStrategy = SentenceStrategyTooltips[randomIndex];
      randomized[chosenStrategy.id] = (randomized[chosenStrategy.id] || 0) + 1;
    }

    onBatchCountChange(randomized);
  };

  // 3. Clear strategies and collapse all groups
  const handleReset = () => {
    const cleared: Record<string, number> = {};
    SentenceStrategyTooltips.forEach((strat) => {
      cleared[strat.id] = 0;
    });
    onBatchCountChange(cleared);
    setExpandedGroups(new Set());
    if (onResetAll) onResetAll();
  };

  return (
    <div className="flex flex-col gap-4">
      {/* Telemetry and Control Header */}
      <div className="bg-white dark:bg-slate-800 p-4 rounded-xl border border-slate-200 dark:border-slate-700 shadow-xs flex items-center justify-between transition-colors">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
            {t("exercises.settings.questionTypes") || "Question Types"}
          </h3>
          <span className="text-[11px] text-slate-500 dark:text-slate-400">
            {t("exercises.settings.allocated") || "Allocated"}:{" "}
            <strong
              className={
                totalAllocatedItems > targetCount
                  ? "text-rose-600 dark:text-rose-400 font-bold"
                  : "text-blue-600 dark:text-blue-400 font-bold"
              }
            >
              {totalAllocatedItems}
            </strong>{" "}
            / {targetCount} {t("exercises.settings.target") || "Target"}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleReset}
            disabled={totalAllocatedItems === 0 && expandedGroups.size === 0}
            className="rounded bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {t("exercises.settings.reset") || "Reset"}
          </button>

          <button
            type="button"
            onClick={handleRandomizeDistribution}
            disabled={targetCount <= 0}
            className="rounded bg-blue-50 hover:bg-blue-100 dark:bg-blue-950/50 dark:hover:bg-blue-900/60 px-3 py-1 text-xs font-semibold text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-2xs flex items-center gap-1.5"
          >
            <span>{t("exercises.settings.randomize") || "Randomize"}</span>
          </button>
        </div>
      </div>

      {/* Accordion Group List */}
      <div className="space-y-3">
        {ORDERED_SENTENCE_GROUPS.map((groupName) => {
          const strategies = groupedStrategies.get(groupName) || [];
          if (strategies.length === 0) return null;

          const isExpanded = expandedGroups.has(groupName);
          const groupAllocatedCount = strategies.reduce(
            (sum, s) => sum + (typeCounts[s.id] || 0),
            0,
          );

          return (
            <div
              key={groupName}
              className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 overflow-hidden shadow-xs transition-colors"
            >
              <button
                type="button"
                onClick={() => toggleGroupAccordion(groupName)}
                aria-expanded={isExpanded}
                className="w-full flex items-center justify-between px-4 py-3 bg-slate-50/80 hover:bg-slate-100/90 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-left transition-colors select-none"
              >
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-slate-800 dark:text-slate-200">
                    {t(`exercises.sentencesMenu.strategies.${groupName}`) ||
                      groupName}
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
                    }) || "items"}
                  </span>
                  <span className="text-slate-400 text-xs font-mono">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </div>
              </button>

              {isExpanded && (
                <div className="p-3.5 border-t border-slate-100 dark:border-slate-700/60 space-y-3 bg-slate-50/30 dark:bg-slate-900/20">
                  {strategies.map((def) => {
                    const currentCount = typeCounts[def.id] || 0;
                    const maxAllowedForThis = currentCount + remainingHeadroom;

                    return (
                      <div
                        key={def.id}
                        className={`rounded-lg border p-3.5 transition-all ${
                          currentCount > 0
                            ? "border-blue-300 bg-blue-50/30 dark:border-blue-900/60 dark:bg-blue-950/20 shadow-2xs"
                            : "border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800 shadow-2xs hover:border-slate-300"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-4">
                          <div className="space-y-1.5 flex-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="text-xs font-bold text-slate-900 dark:text-slate-100">
                                {def.label}
                              </span>
                              <span className="text-[10px] font-mono text-slate-400 dark:text-slate-500">
                                [{def.id}]
                              </span>
                            </div>

                            <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-relaxed">
                              {def.description}
                            </p>

                            {def.stemExample && (
                              <div className="mt-2 rounded bg-slate-50 dark:bg-slate-900/60 p-2 border border-slate-200/70 dark:border-slate-700/70 text-[11px] font-mono text-slate-700 dark:text-slate-300 flex items-center justify-between gap-2">
                                <div className="truncate">
                                  <span className="text-slate-400 text-[10px] font-semibold uppercase mr-1.5">
                                    {t("exercises.settings.ex") || "Ex"}:
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

                            {/* Format Pill Indicators */}
                            <div className="mt-2.5 flex items-center gap-1.5 pt-2 border-t border-slate-100 dark:border-slate-700/40">
                              <span className="text-[9px] uppercase tracking-wider text-slate-400 font-semibold">
                                {t("exercises.settings.formats.format") ||
                                  "Formats"}
                                :
                              </span>
                              <div className="flex gap-1 flex-wrap">
                                {def.supportedFormats.map((fmt) => (
                                  <span
                                    key={fmt}
                                    className="rounded px-1.5 py-0.2 text-[9px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                                  >
                                    {fmt}
                                  </span>
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* Stepper Input */}
                          <div className="flex items-center gap-1.5 select-none shrink-0 pt-0.5">
                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(
                                  def.id,
                                  Math.max(0, currentCount - 1),
                                )
                              }
                              disabled={currentCount === 0}
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                              aria-label={`Decrease ${def.label}`}
                            >
                              -
                            </button>

                            <input
                              type="number"
                              min={0}
                              max={maxAllowedForThis}
                              value={currentCount}
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
                              className="w-12 rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-1 py-1 text-center text-xs font-bold font-mono text-slate-800 dark:text-slate-100 focus:border-blue-500 focus:outline-none shadow-2xs"
                            />

                            <button
                              type="button"
                              onClick={() =>
                                onCountChange(def.id, currentCount + 1)
                              }
                              disabled={totalAllocatedItems >= targetCount}
                              className="w-7 h-7 flex items-center justify-center rounded-md bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-200 font-bold hover:bg-slate-100 dark:hover:bg-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors shadow-2xs"
                              aria-label={`Increase ${def.label}`}
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
