// src/features/sentences/SentenceExerciseConfigPanel.tsx
import React, { useCallback, useMemo } from "react";
import { useTranslation } from "react-i18next";
import { Tooltip } from "../../components/modals/Tooltip";
import { EnumItemFormat } from "../../types";
import { SentenceStrategyTooltips } from "./SentenceStrategyDefinitions";
import { SentenceExerciseConfigState } from "./types";

interface SentenceExerciseConfigPanelProps {
  config: SentenceExerciseConfigState;
  typeCounts: Record<string, number>;
  totalAllocated: number;
  onChange: (updated: Partial<SentenceExerciseConfigState>) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export const SentenceExerciseConfigPanel: React.FC<
  SentenceExerciseConfigPanelProps
> = ({ config, typeCounts, totalAllocated, onChange, onSubmit, isLoading }) => {
  const { t } = useTranslation();

  // ==========================================================================
  // INVERTED FORMAT CONTROL (Derived from Strategies)
  // ==========================================================================

  // 1. Calculate viable formats based on active strategies
  const allowedFormats = useMemo(() => {
    const formats = new Set<EnumItemFormat>();
    SentenceStrategyTooltips.forEach((def) => {
      const allocated = typeCounts[def.id] || 0;
      if (allocated > 0) {
        def.supportedFormats.forEach((fmt) => formats.add(fmt));
      }
    });
    return formats;
  }, [typeCounts]);

  // 2. Prune Invalid Formats & Auto-Select Defaults
  // Added logic to automatically activate allowed formats if none are currently selected.
  // This prevents the button from being permanently disabled when strategies are first chosen.
  React.useEffect(() => {
    const active = config.itemFormats || [];
    const pruned = active.filter((fmt) => allowedFormats.has(fmt));

    if (active.length === 0 && allowedFormats.size > 0) {
      // Auto-select all available formats to unblock the user immediately
      onChange({ itemFormats: Array.from(allowedFormats) });
    } else if (pruned.length !== active.length) {
      // Prune formats that are no longer supported by the remaining strategies
      onChange({ itemFormats: pruned });
    }
  }, [allowedFormats, config.itemFormats, onChange]);

  // 3. Format Toggle Handler
  const toggleFormat = useCallback(
    (format: EnumItemFormat) => {
      if (!allowedFormats.has(format)) return;

      const current = new Set(config.itemFormats || []);
      if (current.has(format)) {
        current.delete(format);
      } else {
        current.add(format);
      }
      onChange({ itemFormats: Array.from(current) });
    },
    [allowedFormats, config.itemFormats, onChange],
  );

  // ==========================================================================
  // EVENT HANDLERS
  // ==========================================================================

  // Prevent input locking by allowing NaN temporarily during user typing,
  // falling back to a safe default if the input is entirely cleared.
  const handleQuotaChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const rawValue = parseInt(e.target.value, 10);
    const safeValue = isNaN(rawValue)
      ? 1
      : Math.min(100, Math.max(1, rawValue));
    onChange({ maxItems: safeValue });
  };

  // Safely wrap onSubmit to prevent SyntheticEvent leakage into the parent handler,
  // and prevent default form submission if this panel is ever nested in a <form>.
  const handleGenerateClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.preventDefault();
    onSubmit();
  };

  // ==========================================================================
  // VALIDATION & SUBMISSION STATE
  // ==========================================================================

  const isSubmitDisabled =
    totalAllocated === 0 ||
    (config.itemFormats || []).length === 0 ||
    totalAllocated > config.maxItems ||
    isLoading;

  return (
    <aside
      aria-labelledby="sentence-config-heading"
      className="sticky top-6 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm space-y-6"
    >
      {/* EXERCISE SETTINGS */}
      <section>
        <h4
          id="sentence-config-heading"
          className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500"
        >
          {t("exercises.settings.exerciseSettings") || "Exercise Settings"}
        </h4>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.targetItemQuant") || "Question Quota"}
              </label>
              <Tooltip
                title={
                  t("exercises.settings.targetItemQuantTooltipName") ||
                  "Target Items"
                }
                content={
                  t("exercises.settings.targetItemQuantTooltipDesc") ||
                  "Target session length."
                }
              />
            </div>
            <input
              type="number"
              min={1}
              max={100}
              value={config.maxItems}
              onChange={handleQuotaChange}
              className="mt-1 w-full rounded border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-sm shadow-xs focus:border-blue-500 focus:outline-none dark:text-slate-100"
            />
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.difficultyLevel") || "Difficulty"}
              </label>
            </div>
            <select
              value={config.difficulty}
              onChange={(e) => onChange({ difficulty: e.target.value as any })}
              className="mt-1 w-full rounded border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1 text-sm shadow-xs focus:border-blue-500 focus:outline-none dark:text-slate-100"
            >
              <option value="easy">{t("modal.settings.easy") || "Easy"}</option>
              <option value="medium">
                {t("modal.settings.medium") || "Medium"}
              </option>
              <option value="hard">{t("modal.settings.hard") || "Hard"}</option>
            </select>
          </div>
        </div>
      </section>

      {/* DYNAMIC OUTPUT FORMATS */}
      <section>
        <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">
          {t("exercises.settings.enabledSessionFormats") || "Delivery Formats"}
        </h4>
        <p className="text-[11px] text-slate-400 dark:text-slate-500 mb-3">
          {allowedFormats.size === 0
            ? "Allocate questions above to activate supported formats."
            : "Select one or more active delivery formats:"}
        </p>

        <div className="flex flex-wrap gap-2">
          {(["mcq", "fitb", "unscramble"] as EnumItemFormat[]).map((fmt) => {
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
                    ? "cursor-not-allowed border border-slate-200 bg-slate-100 text-slate-400 opacity-50 dark:border-slate-800 dark:bg-slate-800/40 dark:text-slate-600"
                    : isSelected
                      ? "border border-blue-600 bg-blue-600 text-white shadow-xs"
                      : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-700 dark:text-slate-200"
                }`}
              >
                {t(`exercises.settings.formats.${fmt}`) || fmt}{" "}
                {isSelected && "✓"}
              </button>
            );
          })}
        </div>
      </section>

      {/* LAUNCH CTA BUTTON */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-700">
        <button
          type="button"
          disabled={isSubmitDisabled}
          onClick={handleGenerateClick}
          className="w-full rounded-md bg-blue-600 py-3 text-sm font-bold text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              Generating Exercises...
            </span>
          ) : totalAllocated === 0 ? (
            "Select Question Types"
          ) : (config.itemFormats || []).length === 0 ? (
            "Select a Format"
          ) : totalAllocated > config.maxItems ? (
            `Allocated (${totalAllocated}) exceeds Target (${config.maxItems})`
          ) : (
            t("exercises.startExercise", { count: totalAllocated }) ||
            `Start Exercise (${totalAllocated} Questions)`
          )}
        </button>
      </div>
    </aside>
  );
};
