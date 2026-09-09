import React, { useMemo, useState } from "react";
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
  maxItems: number; // Assessment length ceiling
}

interface ExerciseConfigPanelProps {
  config: ExerciseConfigState;
  activeLemmas: Lemma[];
  onChange: (updated: Partial<ExerciseConfigState>) => void;
  onSubmit: () => void;
}

export const ExerciseConfigPanel: React.FC<ExerciseConfigPanelProps> = ({
  config,
  activeLemmas,
  onChange,
  onSubmit,
}) => {
  // 1. Collapsible state for progressive disclosure
  const [isStrategiesExpanded, setIsStrategiesExpanded] =
    useState<boolean>(false);

  // 2. Derive available pedagogical groups based on staged vocabulary POS
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

  // 3. Filter strategy definitions to only those matching current vocabulary
  const validStrategies = useMemo(() => {
    return WordStrategyTooltips.filter((def: WordStrategyDefinition) =>
      availableGroups.has(def.group),
    );
  }, [availableGroups]);

  // 4. Calculate total allocated items across all strategy directions
  const totalAllocatedItems = useMemo(() => {
    return Object.values(config.typeCounts || {}).reduce(
      (acc, count) => acc + (count || 0),
      0,
    );
  }, [config.typeCounts]);

  // 5. Derive formats enabled by actively selected strategies
  const allowedFormats = useMemo(() => {
    const formats = new Set<EnumItemFormat>();
    validStrategies.forEach((def) => {
      const mainCount = config.typeCounts[def.id] || 0;
      const pairCount = def.pairId ? config.typeCounts[def.pairId] || 0 : 0;
      if (mainCount > 0 || pairCount > 0) {
        def.supportedFormats.forEach((fmt) => formats.add(fmt));
      }
    });
    return formats;
  }, [config.typeCounts, validStrategies]);

  // 6. Action Handlers
  const handleStrategyCount = (strategyId: string, count: number) => {
    const sanitizedCount = Math.max(0, count);
    onChange({
      typeCounts: {
        ...config.typeCounts,
        [strategyId]: sanitizedCount,
      },
    });
  };

  const handleReverseToggle = (
    mainId: string,
    pairId: string,
    isEnabled: boolean,
  ) => {
    const currentRemaining = Math.max(0, config.maxItems - totalAllocatedItems);
    const mainCount = config.typeCounts[mainId] || 1;
    // Allocate up to remaining ceiling space
    const targetCount = isEnabled
      ? Math.min(mainCount, currentRemaining + (config.typeCounts[pairId] || 0))
      : 0;
    handleStrategyCount(pairId, targetCount);
  };

  const toggleFormat = (format: EnumItemFormat) => {
    if (!allowedFormats.has(format)) return;
    const current = new Set(config.itemFormats || []);
    if (current.has(format)) current.delete(format);
    else current.add(format);
    onChange({ itemFormats: Array.from(current) });
  };

  // 7. Uniform stochastic distributor across active strategies
  const handleRandomizeDistribution = () => {
    if (validStrategies.length === 0 || config.maxItems <= 0) return;

    // Reset counts for all valid keys
    const randomized: Record<string, number> = {};
    validStrategies.forEach((def) => {
      randomized[def.id] = 0;
      if (def.pairId) randomized[def.pairId] = 0;
    });

    // Uniformly distribute exactly maxItems tokens
    for (let i = 0; i < config.maxItems; i++) {
      const selectedDef =
        validStrategies[Math.floor(Math.random() * validStrategies.length)];

      // If pair strategy exists, allocate between base and reverse stochastically
      if (selectedDef.pairId && Math.random() > 0.5) {
        randomized[selectedDef.pairId] =
          (randomized[selectedDef.pairId] || 0) + 1;
      } else {
        randomized[selectedDef.id] = (randomized[selectedDef.id] || 0) + 1;
      }
    }

    onChange({ typeCounts: randomized });
  };

  return (
    <aside
      aria-labelledby="config-heading"
      className="space-y-6 max-h-[85vh] overflow-y-auto pr-2"
    >
      {/* SECTION 1: Assessment Constraints */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-500">
          Assessment Parameters
        </h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
              Target Item Count
            </label>
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
              className="mt-1 w-full rounded border-gray-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
              Difficulty
            </label>
            <select
              value={config.difficulty}
              onChange={(e) =>
                onChange({ difficulty: e.target.value as EnumItemDifficulty })
              }
              className="mt-1 w-full rounded border-gray-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
              Distractors / Item
            </label>
            <input
              type="number"
              min={1}
              max={5}
              value={config.maxDistractors}
              onChange={(e) =>
                onChange({ maxDistractors: parseInt(e.target.value, 10) || 3 })
              }
              className="mt-1 w-full rounded border-gray-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300">
              Keys / Item
            </label>
            <input
              type="number"
              min={1}
              max={3}
              value={config.maxKeys}
              onChange={(e) =>
                onChange({ maxKeys: parseInt(e.target.value, 10) || 1 })
              }
              className="mt-1 w-full rounded border-gray-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
            />
          </div>

          <div className="col-span-2 flex items-center pt-1">
            <input
              type="checkbox"
              id="odd-one-out-toggle"
              checked={config.allowOddOneOut}
              onChange={(e) => onChange({ allowOddOneOut: e.target.checked })}
              className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <label
              htmlFor="odd-one-out-toggle"
              className="ml-2 text-xs text-gray-700 dark:text-gray-300"
            >
              Allow Odd-One-Out Generation
            </label>
          </div>
        </div>
      </section>

      {/* SECTION 2: Psychometric Strategy Allocation */}
      <section className="rounded-lg border border-gray-200 bg-gray-50/50 p-3 dark:border-gray-700 dark:bg-gray-800/30">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-gray-600 dark:text-gray-400">
              Strategy Distribution
            </h4>
            <span className="text-[11px] text-gray-500">
              Allocated:{" "}
              <strong
                className={
                  totalAllocatedItems > config.maxItems
                    ? "text-red-500"
                    : "text-blue-600"
                }
              >
                {totalAllocatedItems}
              </strong>{" "}
              / {config.maxItems}
            </span>
          </div>

          <div className="flex items-center gap-2">
            {/* Always Visible Random Distributor */}
            <button
              type="button"
              onClick={handleRandomizeDistribution}
              disabled={validStrategies.length === 0}
              className="rounded bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 border border-blue-200 hover:bg-blue-100 disabled:opacity-50 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300"
            >
              Randomize
            </button>

            {/* Disclosure Accordion Toggle */}
            <button
              type="button"
              onClick={() => setIsStrategiesExpanded(!isStrategiesExpanded)}
              className="flex items-center gap-1 rounded border border-gray-300 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
              aria-expanded={isStrategiesExpanded}
              aria-label="Toggle strategy list view"
            >
              {isStrategiesExpanded ? "Hide Details ▲" : "Configure ▼"}
            </button>
          </div>
        </div>

        {/* Collapsible Strategy List Container */}
        {isStrategiesExpanded && (
          <div className="mt-4 space-y-3 border-t border-gray-200 pt-3 dark:border-gray-700">
            {validStrategies.length === 0 ? (
              <p className="text-xs text-gray-500">
                Stage vocabulary words to unlock strategies.
              </p>
            ) : (
              validStrategies.map((def) => {
                const count = config.typeCounts[def.id] || 0;
                const pairCount = def.pairId
                  ? config.typeCounts[def.pairId] || 0
                  : 0;
                const remainingHeadroom = Math.max(
                  0,
                  config.maxItems - totalAllocatedItems,
                );

                return (
                  <div
                    key={def.id}
                    className="group relative rounded border border-gray-200 bg-white p-2.5 shadow-sm hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800"
                  >
                    {/* Tooltip Overlay */}
                    <div className="pointer-events-none absolute bottom-full left-0 z-20 mb-2 hidden w-72 rounded bg-gray-900 p-3 text-xs text-white shadow-xl group-hover:block">
                      <strong className="block pb-1 text-blue-300">
                        {def.name}
                      </strong>
                      <p className="pb-2 text-gray-200">{def.description}</p>
                      <p className="border-t border-gray-700 pt-1.5 font-mono text-[10px] text-emerald-300">
                        Ex: {def.stemExample} → {def.keyExample}
                      </p>
                      {def.pairDescription && (
                        <div className="mt-2 border-t border-gray-700 pt-1.5">
                          <p className="text-gray-300">
                            <span className="font-semibold text-blue-300">
                              Reverse:
                            </span>{" "}
                            {def.pairDescription}
                          </p>
                          {def.pairStemExample && (
                            <p className="mt-1 font-mono text-[10px] text-emerald-300">
                              Ex: {def.pairStemExample} → {def.pairKeyExample}
                            </p>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center justify-between">
                      <label className="cursor-help border-b border-dotted border-gray-400 text-xs font-medium text-gray-800 dark:text-gray-200">
                        {def.name}
                      </label>
                      <input
                        type="number"
                        min={0}
                        max={count + remainingHeadroom}
                        value={count}
                        onChange={(e) =>
                          handleStrategyCount(
                            def.id,
                            parseInt(e.target.value, 10) || 0,
                          )
                        }
                        className="w-16 rounded border border-gray-300 px-1.5 py-0.5 text-right text-xs focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-700"
                      />
                    </div>

                    {/* Granular Reverse Direction Sub-Toggle */}
                    {def.pairId && count > 0 && (
                      <div className="mt-2 flex items-center justify-between border-t border-gray-100 pt-2 dark:border-gray-700/60">
                        <label className="flex items-center text-[11px] text-gray-600 dark:text-gray-400">
                          <input
                            type="checkbox"
                            checked={pairCount > 0}
                            onChange={(e) =>
                              handleReverseToggle(
                                def.id,
                                def.pairId!,
                                e.target.checked,
                              )
                            }
                            className="mr-1.5 h-3.5 w-3.5 rounded border-gray-300 text-blue-600"
                          />
                          Include reverse direction
                        </label>
                        {pairCount > 0 && (
                          <input
                            type="number"
                            min={0}
                            max={pairCount + remainingHeadroom}
                            value={pairCount}
                            onChange={(e) =>
                              handleStrategyCount(
                                def.pairId!,
                                parseInt(e.target.value, 10) || 0,
                              )
                            }
                            className="w-14 rounded border border-gray-300 bg-gray-50 px-1 py-0.5 text-right text-xs dark:border-gray-600 dark:bg-gray-900"
                          />
                        )}
                      </div>
                    )}
                  </div>
                );
              })
            )}
          </div>
        )}
      </section>

      {/* SECTION 3: Output Formats */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-gray-500">
          Target Formats (Multi-Choice)
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
                    ? "cursor-not-allowed border border-gray-200 bg-gray-100 text-gray-400 opacity-60 dark:border-gray-800 dark:bg-gray-800 dark:text-gray-600"
                    : isSelected
                      ? "border border-blue-600 bg-blue-600 text-white shadow-sm"
                      : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-200"
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

      {/* CTA Trigger */}
      <div className="sticky bottom-0 bg-white pt-4 pb-2 dark:bg-gray-800">
        <button
          type="button"
          disabled={
            activeLemmas.length === 0 ||
            totalAllocatedItems === 0 ||
            (config.itemFormats || []).length === 0 ||
            totalAllocatedItems > config.maxItems
          }
          onClick={onSubmit}
          className="w-full rounded-md bg-blue-600 py-3 text-sm font-bold text-white shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {totalAllocatedItems > config.maxItems
            ? `Allocated (${totalAllocatedItems}) exceeds Target (${config.maxItems})`
            : `Generate ${totalAllocatedItems} Items (${activeLemmas.length} Lemmas)`}
        </button>
      </div>
    </aside>
  );
};
