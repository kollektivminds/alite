// src/features/words/ExerciseConfigPanel.tsx
import React, { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Tooltip } from "../../components/modals/Tooltip";
import {
  EnumItemDifficulty,
  EnumItemFormat,
  EnumWordItemGroup,
  Lemma,
} from "../../types";
import {
  WordStrategyDefinition,
  WordStrategyTooltips,
} from "./wordsStrategyDefinitions";

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
  const { t } = useTranslation();
  const [expandedGroups, setExpandedGroups] = useState<Set<EnumWordItemGroup>>(
    () => new Set<EnumWordItemGroup>(["General"]),
  );

  // 1. Defensive normalization: Guard against undefined/null nested config structures
  const safeTypeCounts = useMemo(
    () => config?.typeCounts ?? {},
    [config?.typeCounts],
  );
  const safeItemFormats = useMemo(
    () => config?.itemFormats ?? [],
    [config?.itemFormats],
  );
  const maxItems = config?.maxItems ?? 10;

  // 2. Identify available POS categories from currently active lemmas
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

  // 3. Filter strategy definitions matching active vocabulary POS
  const validStrategies = useMemo(() => {
    return WordStrategyTooltips.filter((def: WordStrategyDefinition) =>
      availableGroups.has(def.group),
    );
  }, [availableGroups]);

  // 4. Partition strategies into ordered groups for rendering
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

  // 5. Compute total allocated items using safeTypeCounts
  const totalAllocatedItems = useMemo(() => {
    return Object.values(safeTypeCounts).reduce(
      (acc, count) => acc + (count || 0),
      0,
    );
  }, [safeTypeCounts]);

  // 6. Compute allowed formats using safeTypeCounts[cite: 21]
  const allowedFormats = useMemo(() => {
    const formats = new Set<EnumItemFormat>();

    validStrategies.forEach((def) => {
      const mainCount = safeTypeCounts[def.id] || 0;
      const pairCount = def.pairId ? safeTypeCounts[def.pairId] || 0 : 0;

      if (mainCount > 0 && def.supportedFormats) {
        def.supportedFormats.forEach((fmt) => formats.add(fmt));
      }

      if (pairCount > 0) {
        const pairFormats = def.pairSupportedFormats ?? def.supportedFormats;
        pairFormats.forEach((fmt) => formats.add(fmt));
      }
    });

    return formats;
  }, [safeTypeCounts, validStrategies]);

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
        ...safeTypeCounts,
        [strategyId]: sanitizedCount,
      },
    });
  };

  const toggleFormat = (format: EnumItemFormat) => {
    if (!allowedFormats.has(format)) return;
    const current = new Set(safeItemFormats);
    if (current.has(format)) current.delete(format);
    else current.add(format);
    onChange({ itemFormats: Array.from(current) });
  };

  /**
   * Evaluates the capacity of the active lemma pool for each strategy.
   * Uses uppercase string matching to remain aligned with StrategyDefinitions.ts.
   */
  const strategyCapacities = useMemo(() => {
    const capacities: Record<string, number> = {};

    validStrategies.forEach((def) => {
      let count = 0;
      const upperId = def.id.toUpperCase();

      activeLemmas.forEach((lemma) => {
        const pos = (lemma.pos || "").toLowerCase();
        const hasDefs = Boolean(
          lemma.definitions && lemma.definitions.length > 0,
        );
        const hasProns = Boolean(
          lemma.pronunciations && lemma.pronunciations.length > 0,
        );

        // General Strategies[cite: 19]
        if (upperId === "LEM_TO_DEF" || upperId === "DEF_TO_LEM") {
          if (hasDefs) count++;
        } else if (upperId === "LEM_TO_PRON" || upperId === "PRON_TO_LEM") {
          if (hasProns) count++;
        } else if (upperId === "LEM_TO_POS" || upperId === "POS_TO_LEM") {
          if (lemma.pos) count++;
        } else if (
          upperId === "LEM_LEM_TO_REL" ||
          upperId === "REL_TO_LEM_LEM"
        ) {
          // Requires relationship entries[cite: 14]
          if (hasDefs) count++;
        }
        // Part of Speech Specific Strategies[cite: 19]
        else if (
          def.group === "Nouns" &&
          (pos.includes("noun") || pos === "s" || pos === "subst")
        ) {
          count++;
        } else if (
          def.group === "Verbs" &&
          (pos.includes("verb") || pos === "v")
        ) {
          count++;
        } else if (
          def.group === "Adjectives" &&
          (pos.includes("adj") || pos === "a")
        ) {
          count++;
        } else if (
          def.group === "Participles" &&
          (pos.includes("part") || pos.includes("prt"))
        ) {
          count++;
        }
      });

      capacities[def.id] = count;
      if (def.pairId) {
        capacities[def.pairId] = count;
      }
    });

    return capacities;
  }, [validStrategies, activeLemmas]);

  /**
   * Capacity-Weighted Stochastic Distributor.
   * Normalizes casing checks to ensure General strategies participate in allocation.
   */
  const handleRandomizeDistribution = () => {
    if (validStrategies.length === 0 || maxItems <= 0) return;

    // Isolate strategy tokens with available lemma candidates
    const viableTokens = Object.keys(strategyCapacities).filter(
      (token) => strategyCapacities[token] > 0,
    );

    if (viableTokens.length === 0) return;

    const randomized: Record<string, number> = {};
    viableTokens.forEach((t) => (randomized[t] = 0));

    let itemsRemaining = maxItems;
    let attempts = 0;
    const maxAttempts = maxItems * 10;

    while (itemsRemaining > 0 && attempts < maxAttempts) {
      attempts++;

      // Filter tokens with remaining capacity headroom
      const availableTokens = viableTokens.filter(
        (t) => randomized[t] < strategyCapacities[t],
      );

      if (availableTokens.length === 0) {
        // Pool capacity reached; allocate remaining items to general fallbacks
        const generalFallbacks = viableTokens.filter((t) => {
          const upper = t.toUpperCase();
          return (
            upper.includes("DEF") ||
            upper.includes("POS") ||
            upper.includes("PRON")
          );
        });

        const fallback =
          generalFallbacks.length > 0
            ? generalFallbacks[
                Math.floor(Math.random() * generalFallbacks.length)
              ]
            : viableTokens[Math.floor(Math.random() * viableTokens.length)];

        randomized[fallback] = (randomized[fallback] || 0) + 1;
        itemsRemaining--;
        continue;
      }

      // Weight selection by remaining capacity headroom
      const totalRemainingCapacity = availableTokens.reduce(
        (sum, t) => sum + (strategyCapacities[t] - randomized[t]),
        0,
      );

      let randomWeight = Math.random() * totalRemainingCapacity;
      let chosenToken = availableTokens[0];

      for (const token of availableTokens) {
        const tokenWeight = strategyCapacities[token] - randomized[token];
        if (randomWeight <= tokenWeight) {
          chosenToken = token;
          break;
        }
        randomWeight -= tokenWeight;
      }

      randomized[chosenToken] += 1;
      itemsRemaining--;
    }

    onChange({ typeCounts: randomized });
  };

  const remainingHeadroom = Math.max(0, maxItems - totalAllocatedItems);

  return (
    <aside
      aria-labelledby="config-heading"
      className="space-y-6 max-h-[85vh] overflow-y-auto pr-2"
    >
      {/* SECTION 1: Assessment Constraints[cite: 21] */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
          {t("exercises.settings.exerciseSettings")}
        </h4>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.targetItemQuant")}
              </label>
              <Tooltip
                title={t("exercises.settings.targetItemQuantTooltipName")}
                content={t("exercises.settings.targetItemQuantTooltipDesc")}
              />
            </div>
            <input
              type="number"
              min={1}
              max={100}
              value={maxItems}
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
                {t("exercises.settings.difficultyLevel")}
              </label>
              <Tooltip
                title={t("exercises.settings.difficultyLevelTooltipName")}
                content={t("exercises.settings.difficultyLevelTooltipDesc")}
              />
            </div>
            <select
              value={config?.difficulty ?? "medium"}
              onChange={(e) =>
                onChange({ difficulty: e.target.value as EnumItemDifficulty })
              }
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700"
            >
              <option value="easy">{t("modal.settings.easy")}</option>
              <option value="medium">{t("modal.settings.medium")}</option>
              <option value="hard">{t("modal.settings.hard")}</option>
            </select>
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.distractorsItem")}
              </label>
              <Tooltip
                title={t("exercises.settings.distractorsTooltipName")}
                content={t("exercises.settings.distractorsTooltipDesc")}
              />
            </div>
            <input
              type="number"
              min={1}
              max={3}
              disabled={true}
              value={config?.maxDistractors ?? 3}
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 disabled:opacity-60"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.keysItem")}
              </label>
              <Tooltip
                title={t("exercises.settings.keysItemTooltipName")}
                content={t("exercises.settings.keysItemTooltipDesc")}
              />
            </div>
            <input
              type="number"
              min={1}
              max={3}
              disabled={true}
              value={config?.maxKeys ?? 1}
              className="mt-1 w-full rounded border-slate-300 px-2 py-1 text-sm shadow-sm focus:border-blue-500 focus:outline-none dark:border-slate-600 dark:bg-slate-700 disabled:opacity-60"
            />
          </div>

          <div className="col-span-2 flex items-center justify-between pt-2 border-t border-slate-200/60 dark:border-slate-700/60">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="odd-one-out-toggle"
                disabled={true}
                checked={config?.allowOddOneOut ?? false}
                className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500 disabled:opacity-60"
              />
              <label
                htmlFor="odd-one-out-toggle"
                className="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300"
              >
                {t("exercises.settings.allowOoo")}
              </label>
            </div>
            <Tooltip
              title={t("exercises.settings.allowOooTooltipName")}
              content={t("exercises.settings.allowOooTooltipDesc")}
            />
          </div>
        </div>
      </section>

      {/* SECTION 2: Hierarchical Strategy Distribution by POS[cite: 21] */}
      <section className="rounded-lg border border-slate-200 bg-slate-50/50 p-3.5 dark:border-slate-700 dark:bg-slate-800/30">
        <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-700">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300">
              {t("exercises.settings.questionTypes")}
            </h4>
            <span className="text-[11px] text-slate-500">
              {t("exercises.settings.allocated")}:{" "}
              <strong
                className={
                  totalAllocatedItems > maxItems
                    ? "text-red-500"
                    : "text-blue-600 dark:text-blue-400"
                }
              >
                {totalAllocatedItems}
              </strong>{" "}
              / {maxItems}
            </span>
          </div>

          <button
            type="button"
            onClick={handleRandomizeDistribution}
            disabled={validStrategies.length === 0}
            className="rounded bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700 border border-blue-200 hover:bg-blue-100 disabled:opacity-50 dark:border-blue-800 dark:bg-blue-950/40 dark:text-blue-300 transition-colors"
          >
            {t("exercises.settings.randomize")}
          </button>
        </div>

        <div className="mt-3 space-y-2.5">
          {validStrategies.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-2">
              {t("exercises.settings.stageVocab")}
            </p>
          ) : (
            Array.from(groupedStrategies.entries()).map(
              ([groupName, strategies]) => {
                if (strategies.length === 0) return null;

                const isGroupExpanded = expandedGroups.has(groupName);

                const groupAllocatedCount = strategies.reduce((sum, s) => {
                  const fCount = safeTypeCounts[s.id] || 0;
                  const rCount = s.pairId ? safeTypeCounts[s.pairId] || 0 : 0;
                  return sum + fCount + rCount;
                }, 0);

                return (
                  <div
                    key={groupName}
                    className="rounded-md border border-slate-200 bg-white overflow-hidden dark:border-slate-700 dark:bg-slate-800 shadow-sm"
                  >
                    <button
                      type="button"
                      onClick={() => toggleGroupAccordion(groupName)}
                      className="w-full flex items-center justify-between px-3 py-2 bg-slate-100/70 hover:bg-slate-100 dark:bg-slate-800/80 dark:hover:bg-slate-800 text-left transition-colors"
                      aria-expanded={isGroupExpanded}
                    >
                      <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                        {t(`exercises.wordsMenu.strategies.${groupName}`)}
                      </span>

                      <div className="flex items-center gap-2">
                        <span
                          className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full font-bold ${
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
                          {isGroupExpanded ? "▲" : "▼"}
                        </span>
                      </div>
                    </button>

                    {isGroupExpanded && (
                      <div className="p-2.5 space-y-3 border-t border-slate-200 dark:border-slate-700/60">
                        {strategies.map((def) => {
                          const forwardCount = safeTypeCounts[def.id] || 0;
                          const forwardMax = forwardCount + remainingHeadroom;

                          const hasReverse = Boolean(def.pairId);
                          const reverseCount = def.pairId
                            ? safeTypeCounts[def.pairId] || 0
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
                              <div className="flex items-center justify-between border-b border-slate-200/60 pb-1 dark:border-slate-700/40">
                                <span className="text-[10px] font-mono text-slate-400">
                                  {def.id} {hasReverse && `⇄ ${def.pairId}`}
                                </span>
                              </div>

                              <div
                                className={`grid gap-2.5 ${
                                  hasReverse
                                    ? "grid-cols-1 md:grid-cols-2"
                                    : "grid-cols-1"
                                }`}
                              >
                                {/* Forward Direction[cite: 21] */}
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
                                          {t("exercises.settings.ex")}:
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
                                      {t("exercises.settings.formats.format")}:
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

                                {/* Reverse Direction[cite: 21] */}
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
                                            {t("exercises.settings.ex")}:
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
                                        {t("exercises.settings.formats.format")}
                                        :
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

      {/* SECTION 3: Output Formats[cite: 21] */}
      <section>
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500">
          {t("exercises.settings.enabledSessionFormats")}
        </h4>
        <div className="flex flex-wrap gap-2">
          {(["mcq", "fitb", "flashcard"] as EnumItemFormat[]).map((fmt) => {
            const isSupported = allowedFormats.has(fmt);
            const isSelected = safeItemFormats.includes(fmt);

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
                {t(`exercises.settings.formats.${fmt}`)} {isSelected && "✓"}
              </button>
            );
          })}
        </div>
        {totalAllocatedItems > 0 && allowedFormats.size === 0 && (
          <p className="mt-2 text-xs text-red-500">
            {t("exercises.settings.formats.noFormat")}
          </p>
        )}
      </section>

      {/* SECTION 4: Submission CTA[cite: 21] */}
      <div className="sticky bottom-0 bg-white pt-4 pb-2 dark:bg-slate-800 border-t border-slate-100 dark:border-slate-700">
        <button
          type="button"
          disabled={
            activeLemmas.length === 0 ||
            totalAllocatedItems === 0 ||
            safeItemFormats.length === 0 ||
            totalAllocatedItems > maxItems
          }
          onClick={onSubmit}
          className="w-full rounded-md bg-blue-600 py-3 text-sm font-bold text-white shadow hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {totalAllocatedItems > maxItems
            ? `Allocated (${totalAllocatedItems}) exceeds Target (${maxItems})`
            : `${t("exercises.startExercise", { count: totalAllocatedItems })} ${t("exercises.numWords", { count: activeLemmas.length })}`}
        </button>
      </div>
    </aside>
  );
};
