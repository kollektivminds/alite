// src/features/words/ExerciseConfigPanel.tsx
import React, { useMemo, useState } from "react";
import { Tooltip } from "../../components/modals/Tooltip";
import {
  EnumItemDifficulty,
  EnumItemFormat,
  EnumWordItemGroup,
  Lemma,
} from "../../types/words";
import {
  WordStrategyDefinition,
  WordStrategyTooltips,
} from "./StrategyDefinitions";

export interface ExerciseConfigState {
  difficulty: EnumItemDifficulty;
  maxKeys: number;
  maxDistractors: number;
  allowOddOneOut: boolean;
  itemFormats: EnumItemFormat[];
  typeCounts: Record<string, number>;
  maxItems: number;
}

interface ExerciseConfigPanelProps {
  config: ExerciseConfigState;
  activeLemmas: Lemma[];
  onChange: (updated: Partial<ExerciseConfigState>) => void;
  onSubmit: () => void;
}

// Canonical pedagogical order for linguistic categories
const ORDERED_GROUPS: EnumWordItemGroup[] = [
  "General",
  "Nouns",
  "Verbs",
  "Adjectives",
  "Participles",
];

export const ExerciseConfigPanel: React.FC<ExerciseConfigPanelProps> = ({
  config,
  activeLemmas,
  onChange,
  onSubmit,
}) => {
  // 1. Independent Accordion State: Tracks which category groups are currently open
  const [expandedGroups, setExpandedGroups] = useState<Set<EnumWordItemGroup>>(
    () => new Set<EnumWordItemGroup>(["General"]),
  );

  // identify available groups based on staged vocabulary POS tags
  const availableGroups = useMemo(() => {
    const groups = new Set<EnumWordItemGroup>(["General"]);
    activeLemmas.forEach((lemma) => {
      const pos = (lemma.pos || "").toLowerCase();
      if (pos.includes("noun") || pos === "s" || pos === "subst")
        groups.add("Nouns");
      else if (pos.includes("verb") || pos === "v") groups.add("Verbs");
      else if (pos.includes("adj") || pos === "a") groups.add("Adjectives");
      else if (pos.includes("part") || pos.includes("prt"))
        groups.add("Participles");
    });
    return groups;
  }, [activeLemmas]);

  // filter strategy definitions matching active vocabulary POS
  const validStrategies = useMemo(() => {
    return WordStrategyTooltips.filter((def: WordStrategyDefinition) =>
      availableGroups.has(def.group),
    );
  }, [availableGroups]);

  // partition strategies into ordered groups for hierarchical rendering
  const groupedStrategies = useMemo(() => {
    const map = new Map<EnumWordItemGroup, WordStrategyDefinition[]>();

    ORDERED_GROUPS.forEach((group) => {
      if (availableGroups.has(group)) {
        map.set(group, []);
      }
    });

    validStrategies.forEach((def) => {
      const groupList = map.get(def.group);
      if (groupList) {
        groupList.push(def);
      }
    });

    return map;
  }, [availableGroups, validStrategies]);

  // compute total allocated items across all strategy directions
  const totalAllocatedItems = useMemo(() => {
    return Object.values(config.typeCounts || {}).reduce(
      (acc, count) => acc + (count || 0),
      0,
    );
  }, [config.typeCounts]);

  // compute allowed formats based on strategies with count > 0
  const allowedFormats = useMemo(() => {
    const formats = new Set<EnumItemFormat>();

    validStrategies.forEach((def) => {
      const mainCount = config.typeCounts[def.id] || 0;
      const pairCount = def.pairId ? config.typeCounts[def.pairId] || 0 : 0;

      if (mainCount > 0 && def.supportedFormats) {
        def.supportedFormats.forEach((fmt) => formats.add(fmt));
      }

      if (pairCount > 0) {
        const pairFormats = def.pairSupportedFormats ?? def.supportedFormats;
        pairFormats.forEach((fmt) => formats.add(fmt));
      }
    });

    return formats;
  }, [config.typeCounts, validStrategies]);

  // 7. Action Handlers
  const toggleGroupAccordion = (group: EnumWordItemGroup) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(group)) next.delete(group);
      else next.add(group);
      return next;
    });
  };

  const handleStrategyCount = (strategyId: string, count: number) => {
    const sanitizedCount = Math.max(0, count);
    onChange({
      typeCounts: {
        ...config.typeCounts,
        [strategyId]: sanitizedCount,
      },
    });
  };

  const toggleFormat = (format: EnumItemFormat) => {
    if (!allowedFormats.has(format)) return;
    const current = new Set(config.itemFormats || []);
    if (current.has(format)) current.delete(format);
    else current.add(format);
    onChange({ itemFormats: Array.from(current) });
  };

  // Uniform stochastic distributor across all available strategy tokens
  const handleRandomizeDistribution = () => {
    if (validStrategies.length === 0 || config.maxItems <= 0) return;

    const activeTokens: string[] = [];
    const randomized: Record<string, number> = {};

    validStrategies.forEach((def) => {
      randomized[def.id] = 0;
      activeTokens.push(def.id);

      if (def.pairId) {
        randomized[def.pairId] = 0;
        activeTokens.push(def.pairId);
      }
    });

    for (let i = 0; i < config.maxItems; i++) {
      const chosenToken =
        activeTokens[Math.floor(Math.random() * activeTokens.length)];
      randomized[chosenToken] = (randomized[chosenToken] || 0) + 1;
    }

    onChange({ typeCounts: randomized });
  };

  const remainingHeadroom = Math.max(0, config.maxItems - totalAllocatedItems);

  return (
    <aside
      aria-labelledby="config-heading"
      className="space-y-6 max-h-[85vh] overflow-y-auto pr-2"
    >
      {/* SECTION 1: Assessment Constraints */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
          Assessment Parameters
        </h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Target Question Count
              </label>
              <Tooltip
                title="Question Quota"
                content="The maximum number of questions requested (due to algorithmic processing, total number of questions produced may be fewer)."
              />
            </div>
            <input
              type="number"
              min={1}
              max={100}
              value={config.maxItems}
              onChange={(e) =>
                onChange({
                  maxItems: Math.min(
                    100,
                    Math.max(1, parseInt(e.target.value, 10) || 1),
                  ),
                })
              }
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Difficulty Tier
              </label>
              <Tooltip
                title="Exercise Difficulty"
                content="Set of options to more or less rigorously test knowledge. Default difficulty available in user settings."
              />
            </div>
            <select
              value={config.difficulty}
              onChange={(e) =>
                onChange({ difficulty: e.target.value as EnumItemDifficulty })
              }
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Distractors / Item
              </label>
              <Tooltip
                title="Distractor Quota"
                content="The number of syntactically plausible, incorrect options generated per multiple-choice item."
              />
            </div>
            <input
              type="number"
              min={1}
              max={3}
              disabled={true}
              value={config.maxDistractors}
              onChange={(e) =>
                onChange({ maxDistractors: parseInt(e.target.value, 10) || 3 })
              }
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                Keys / Item
              </label>
              <Tooltip
                title="Multiple True Keys"
                content="Allows generating items with multiple correct options to test comprehensive category recognition."
              />
            </div>
            <input
              type="number"
              min={1}
              max={3}
              disabled={true}
              value={config.maxKeys}
              onChange={(e) =>
                onChange({ maxKeys: parseInt(e.target.value, 10) || 1 })
              }
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700"
            />
          </div>

          <div className="col-span-2 flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-slate-700/60">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="odd-one-out-toggle"
                checked={config.allowOddOneOut}
                defaultChecked={false}
                onChange={(e) => onChange({ allowOddOneOut: e.target.checked })}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
              />
              <label
                htmlFor="odd-one-out-toggle"
                className="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300"
              >
                Allow Odd-One-Out Synthesis
              </label>
            </div>
            <Tooltip
              title="Odd-One-Out Generation"
              content="Generates questions with the usual multiple-choice format flipped: identify the one incorrect answer."
            />
          </div>
        </div>
      </section>

      {/* SECTION 2: Hierarchical Strategy Distribution by POS */}
      <section className="rounded-lg border border-slate-200 bg-slate-50/50 p-3.5 dark:border-slate-700 dark:bg-slate-800/30">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              Question Types
            </h4>
            <span className="text-[11px] text-slate-500">
              Allocated:{" "}
              <strong
                className={
                  totalAllocatedItems > config.maxItems
                    ? "text-red-500"
                    : "text-blue-600 dark:text-blue-400"
                }
              >
                {totalAllocatedItems}
              </strong>{" "}
              / {config.maxItems} Target
            </span>
          </div>

          <button
            type="button"
            onClick={handleRandomizeDistribution}
            disabled={validStrategies.length === 0}
            className="rounded bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 border border-blue-200 hover:bg-blue-100 disabled:opacity-50 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300 transition-colors"
          >
            Randomize
          </button>
        </div>

        {/* Group Sub-Lists */}
        <div className="mt-3 space-y-2.5">
          {validStrategies.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-2">
              Stage vocabulary lemmas on the left to unlock strategies.
            </p>
          ) : (
            Array.from(groupedStrategies.entries()).map(
              ([groupName, strategies]) => {
                if (strategies.length === 0) return null;

                const isGroupExpanded = expandedGroups.has(groupName);

                // calculate aggregate items allocated strictly within this POS group
                const groupAllocatedCount = strategies.reduce((sum, s) => {
                  const fCount = config.typeCounts[s.id] || 0;
                  const rCount = s.pairId
                    ? config.typeCounts[s.pairId] || 0
                    : 0;
                  return sum + fCount + rCount;
                }, 0);

                return (
                  <div
                    key={groupName}
                    className="rounded-md border border-slate-200 bg-white overflow-hidden dark:border-slate-700 dark:bg-slate-800 shadow-sm"
                  >
                    {/* Category Sub-Header Accordion Button */}
                    <button
                      type="button"
                      onClick={() => toggleGroupAccordion(groupName)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-slate-100/70 hover:bg-slate-100 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-left transition-colors"
                      aria-expanded={isGroupExpanded}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                          {groupName}
                        </span>
                        {/* <span className="text-[10px] text-slate-400">
                          ({strategies.length} pair
                          {strategies.length > 1 ? "s" : ""})
                        </span> */}
                      </div>

                      <div className="flex items-center gap-2">
                        {/* Telemetry Badge: Items Allocated in this group */}
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full font-bold ${
                            groupAllocatedCount > 0
                              ? "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300"
                              : "bg-slate-200/60 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
                          }`}
                        >
                          {groupAllocatedCount} items
                        </span>
                        <span className="text-slate-400 text-xs font-mono">
                          {isGroupExpanded ? "▲" : "▼"}
                        </span>
                      </div>
                    </button>

                    {/* Collapsible Content Area */}
                    {isGroupExpanded && (
                      <div className="p-2.5 space-y-3 border-t border-slate-200 dark:border-slate-700/60">
                        {strategies.map((def) => {
                          const forwardCount = config.typeCounts[def.id] || 0;
                          const forwardMax = forwardCount + remainingHeadroom;

                          const hasReverse = Boolean(def.pairId);
                          const reverseCount = def.pairId
                            ? config.typeCounts[def.pairId] || 0
                            : 0;
                          const reverseMax = reverseCount + remainingHeadroom;
                          const reverseName =
                            def.pairName && def.pairName.trim().length > 0
                              ? def.pairName
                              : `${def.name} (Reverse)`;

                          const forwardFormats = def.supportedFormats || [];
                          const reverseFormats =
                            def.pairSupportedFormats ?? forwardFormats;

                          return (
                            <div
                              key={def.id}
                              className="rounded-lg border border-slate-100 bg-slate-50/40 p-2.5 dark:border-slate-700/60 dark:bg-slate-900/20 space-y-2.5"
                            >
                              {/* Strategy Token Metadata Bar */}
                              <div className="flex items-center justify-between border-b border-slate-200/60 pb-1 dark:border-slate-700/40">
                                <span className="text-[10px] font-mono text-slate-400">
                                  {def.id} {hasReverse && `⇄ ${def.pairId}`}
                                </span>
                              </div>

                              {/* Dual-Lane Grid Layout */}
                              <div
                                className={`grid gap-2.5 ${
                                  hasReverse
                                    ? "grid-cols-1 md:grid-cols-2"
                                    : "grid-cols-1"
                                }`}
                              >
                                {/* LANE 1: Forward Direction */}
                                <div className="flex flex-col justify-between rounded border border-slate-200 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800">
                                  <div className="space-y-1.5">
                                    <div className="flex items-start justify-between gap-1.5">
                                      <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-tight">
                                        {def.name}
                                      </span>
                                      <input
                                        type="number"
                                        min={0}
                                        max={forwardMax}
                                        value={forwardCount}
                                        onChange={(e) =>
                                          handleStrategyCount(
                                            def.id,
                                            parseInt(e.target.value, 10) || 0,
                                          )
                                        }
                                        className="w-13 rounded border border-slate-300 bg-white px-1.5 py-0.5 text-right text-xs font-bold text-slate-800 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 shadow-sm"
                                      />
                                    </div>

                                    <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                                      {def.description}
                                    </p>

                                    {def.stemExample && (
                                      <div className="rounded bg-slate-50 p-1.5 border border-slate-200/60 dark:bg-slate-900/40 dark:border-slate-700/60 font-mono text-[10px] text-slate-700 dark:text-slate-300">
                                        <span className="text-slate-400">
                                          Ex:
                                        </span>{" "}
                                        {def.stemExample}
                                        {def.keyExample && (
                                          <span className="font-bold text-emerald-600 dark:text-emerald-400">
                                            {" "}
                                            → {def.keyExample}
                                          </span>
                                        )}
                                      </div>
                                    )}
                                  </div>

                                  <div className="mt-2.5 flex items-center gap-1 pt-1.5 border-t border-slate-100 dark:border-slate-700/40">
                                    <span className="text-[9px] uppercase tracking-wider text-slate-400">
                                      Formats:
                                    </span>
                                    <div className="flex gap-1 flex-wrap">
                                      {forwardFormats.map((fmt) => (
                                        <span
                                          key={fmt}
                                          className="rounded bg-slate-100 px-1 py-0.2 text-[9px] font-semibold text-slate-600 dark:bg-slate-700 dark:text-slate-300 uppercase"
                                        >
                                          {fmt}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                </div>

                                {/* LANE 2: Reverse Direction */}
                                {hasReverse && (
                                  <div className="flex flex-col justify-between rounded border border-slate-200 bg-white p-2.5 dark:border-slate-700 dark:bg-slate-800">
                                    <div className="space-y-1.5">
                                      <div className="flex items-start justify-between gap-1.5">
                                        <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 leading-tight">
                                          {reverseName}
                                        </span>
                                        <input
                                          type="number"
                                          min={0}
                                          max={reverseMax}
                                          value={reverseCount}
                                          onChange={(e) =>
                                            handleStrategyCount(
                                              def.pairId!,
                                              parseInt(e.target.value, 10) || 0,
                                            )
                                          }
                                          className="w-13 rounded border border-slate-300 bg-white px-1.5 py-0.5 text-right text-xs font-bold text-slate-800 focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 shadow-sm"
                                        />
                                      </div>

                                      <p className="text-[11px] text-slate-600 dark:text-slate-400 leading-snug">
                                        {def.pairDescription ||
                                          "Reverse operational assessment direction."}
                                      </p>

                                      {def.pairStemExample && (
                                        <div className="rounded bg-slate-50 p-1.5 border border-slate-200/60 dark:bg-slate-900/40 dark:border-slate-700/60 font-mono text-[10px] text-slate-700 dark:text-slate-300">
                                          <span className="text-slate-400">
                                            Ex:
                                          </span>{" "}
                                          {def.pairStemExample}
                                          {def.pairKeyExample && (
                                            <span className="font-bold text-emerald-600 dark:text-emerald-400">
                                              {" "}
                                              → {def.pairKeyExample}
                                            </span>
                                          )}
                                        </div>
                                      )}
                                    </div>

                                    <div className="mt-2.5 flex items-center gap-1 pt-1.5 border-t border-slate-100 dark:border-slate-700/40">
                                      <span className="text-[9px] uppercase tracking-wider text-slate-400">
                                        Formats:
                                      </span>
                                      <div className="flex gap-1 flex-wrap">
                                        {reverseFormats.map((fmt) => (
                                          <span
                                            key={fmt}
                                            className="rounded bg-slate-100 px-1 py-0.2 text-[9px] font-semibold text-slate-600 dark:bg-slate-700 dark:text-slate-300 uppercase"
                                          >
                                            {fmt}
                                          </span>
                                        ))}
                                      </div>
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              },
            )
          )}
        </div>
      </section>

      {/* SECTION 3: Session Output Formats */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
          Enabled Session Formats
        </h4>
        <div className="flex flex-wrap gap-2">
          {(["mcq", "fitb", "flashcard"] as EnumItemFormat[]).map((fmt) => {
            const isSupported = allowedFormats.has(fmt);
            const isSelected = (config.itemFormats || []).includes(fmt);

            return (
              <button
                key={fmt}
                type="button"
                disabled={!isSupported}
                onClick={() => toggleFormat(fmt)}
                className={`rounded px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors ${
                  !isSupported
                    ? "cursor-not-allowed border border-slate-200 bg-slate-100 text-slate-400 opacity-60 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-600"
                    : isSelected
                      ? "border border-blue-600 bg-blue-600 text-white shadow-sm"
                      : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200"
                }`}
              >
                {fmt} {isSelected && "✓"}
              </button>
            );
          })}
        </div>
        {totalAllocatedItems > 0 && allowedFormats.size === 0 && (
          <p className="mt-2 text-xs text-red-500">
            Selected strategies do not support any generator output formats.
          </p>
        )}
      </section>

      {/* SECTION 4: Submission CTA */}
      <div className="sticky bottom-0 bg-white pt-4 pb-2 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700">
        <button
          type="button"
          disabled={
            activeLemmas.length === 0 ||
            totalAllocatedItems === 0 ||
            (config.itemFormats || []).length === 0 ||
            totalAllocatedItems > config.maxItems
          }
          onClick={onSubmit}
          className="w-full rounded-md bg-blue-600 py-3 text-sm font-bold text-white shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {totalAllocatedItems > config.maxItems
            ? `Allocated (${totalAllocatedItems}) exceeds Target (${config.maxItems})`
            : `Generate ${totalAllocatedItems} Questions (${activeLemmas.length} Words)`}
        </button>
      </div>
    </aside>
  );
};
