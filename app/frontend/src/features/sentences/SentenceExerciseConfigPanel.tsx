/**
 * src/features/sentences/SentenceExerciseConfigPanel.tsx
 *
 * Harmonized configuration panel for sentence-level exercise parameters.
 * Aligns typography, color tokens, 2x2 layout grid, tooltips, format pill buttons,
 * and Odd-One-Out toggle with the words assessment configuration panel.
 */

import React from "react";
import { useTranslation } from "react-i18next";
import { Tooltip } from "../../components/modals/Tooltip";

import type { EnumItemDifficulty, EnumItemFormat } from "../../types/exercise";
import type { SentenceExerciseConfigState } from "./types";

interface SentenceExerciseConfigPanelProps {
  config: SentenceExerciseConfigState;
  onChange: (updated: Partial<SentenceExerciseConfigState>) => void;
  totalQuestions: number;
  onGenerate: () => void;
  isLoading: boolean;
}

export const SentenceExerciseConfigPanel: React.FC<
  SentenceExerciseConfigPanelProps
> = ({ config, onChange, totalQuestions, onGenerate, isLoading }) => {
  const { t } = useTranslation();

  // Valid delivery formats supported by the sentence generation strategies
  const supportedFormats: EnumItemFormat[] = ["mcq", "fitb", "unscramble"];

  // Toggle format selection with a minimum-selection guardrail (at least 1 active)
  const toggleFormat = (format: EnumItemFormat) => {
    const current = new Set(config.itemFormats || []);
    if (current.has(format)) {
      if (current.size > 1) {
        current.delete(format);
      }
    } else {
      current.add(format);
    }
    onChange({ itemFormats: Array.from(current) });
  };

  // Resolve target question count: prefers state-level maxItems, falls back to active totalQuestions
  const activeQuestionCount = config.maxItems ?? totalQuestions;

  return (
    <aside
      aria-labelledby="sentence-config-heading"
      className="space-y-6 bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm sticky top-6 transition-colors"
    >
      {/* =================================================================== */}
      {/* SECTION 1: Assessment Parameters (Balanced 2x2 Grid + OOO Toggle)   */}
      {/* =================================================================== */}
      <section>
        <h4
          id="sentence-config-heading"
          className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400"
        >
          {t("exercises.settings.exerciseSettings", "Assessment Parameters")}
        </h4>

        <div className="grid grid-cols-2 gap-4 text-sm">
          {/* Row 1, Col 1: Target Question Count */}
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.targetItemQuant", "Total Questions")}
              </label>
              <Tooltip
                title={t(
                  "exercises.settings.targetItemQuant",
                  "Question Quota",
                )}
                content={t(
                  "exercises.settings.quotaTooltip",
                  "The total number of sentence items generated across the allocated strategy categories.",
                )}
              />
            </div>
            <input
              type="number"
              min={1}
              max={50}
              value={activeQuestionCount}
              onChange={(e) => {
                const val = Math.min(
                  50,
                  Math.max(1, parseInt(e.target.value, 10) || 1),
                );
                onChange({ maxItems: val });
              }}
              className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 shadow-sm focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Row 1, Col 2: Difficulty Tier */}
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.difficultyLevel")}
              </label>
              <Tooltip
                title={t("modal.settings.difficulty")}
                content={t(
                  "exercises.settings.difficultyTooltip",
                  "Controls lexical assistance (e.g. showing base lemma hints for cloze items) and distractor complexity.",
                )}
              />
            </div>
            <select
              value={config.difficulty}
              onChange={(e) =>
                onChange({ difficulty: e.target.value as EnumItemDifficulty })
              }
              className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2 py-1.5 text-xs text-slate-800 dark:text-slate-100 shadow-sm focus:border-blue-500 focus:outline-none transition-colors"
            >
              <option value="easy">{t("modal.settings.easy", "Easy")}</option>
              <option value="medium">
                {t("modal.settings.medium", "Medium")}
              </option>
              <option value="hard">{t("modal.settings.hard", "Hard")}</option>
            </select>
          </div>

          {/* Row 2, Col 1: Distractors / Item */}
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.distractorsItem")}
              </label>
              <Tooltip
                title={t(
                  "exercises.settings.distractorsTitle",
                  "Distractor Quota",
                )}
                content={t(
                  "exercises.settings.distractorsTooltip",
                  "Number of syntactically and morphologically plausible incorrect options generated per MCQ item.",
                )}
              />
            </div>
            <input
              type="number"
              min={2}
              max={4}
              disabled={true}
              value={config.maxDistractors}
              onChange={(e) =>
                onChange({
                  maxDistractors: Math.min(
                    4,
                    Math.max(2, parseInt(e.target.value, 10) || 3),
                  ),
                })
              }
              className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 px-2.5 py-1.5 text-xs text-slate-800 dark:text-slate-100 shadow-sm focus:border-blue-500 focus:outline-none transition-colors"
            />
          </div>

          {/* Row 2, Col 2: Keys / Item */}
          <div>
            <div className="flex items-center gap-1.5">
              <label className="block text-xs font-medium text-slate-700 dark:text-slate-300">
                {t("exercises.settings.keysItem", "Keys / Item")}
              </label>
              <Tooltip
                title={t("exercises.settings.keysTitle", "Correct Keys")}
                content={t(
                  "exercises.settings.keysTooltip",
                  "Number of correct solution targets expected per item (fixed at 1 for standard sentence drills).",
                )}
              />
            </div>
            <input
              type="number"
              min={1}
              max={2}
              disabled={true}
              value={config.maxKeys}
              className="mt-1 w-full rounded border border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/50 px-2.5 py-1.5 text-xs text-slate-500 dark:text-slate-400 shadow-sm cursor-not-allowed"
            />
          </div>

          {/* Row 3 (Full Width): Odd-One-Out Synthesis Toggle */}
          <div className="col-span-2 flex items-center justify-between pt-3 border-t border-slate-200/60 dark:border-slate-700/60">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="sentence-odd-one-out"
                disabled={true}
                checked={config.allowOddOneOut}
                onChange={(e) => onChange({ allowOddOneOut: e.target.checked })}
                className="h-4 w-4 rounded border-slate-300 dark:border-slate-600 text-blue-600 focus:ring-blue-500"
              />
              <label
                htmlFor="sentence-odd-one-out"
                className="ml-2 text-xs font-medium text-slate-700 dark:text-slate-300 cursor-pointer select-none"
              >
                {t(
                  "exercises.settings.allowOoo",
                  "Allow Odd-One-Out Synthesis",
                )}
              </label>
            </div>
            <Tooltip
              title={t("exercises.settings.oooTitle", "Odd-One-Out")}
              content={t(
                "exercises.settings.oooTooltip",
                "Generates inverse items where learners identify the syntactically or morphologically anomalous option.",
              )}
            />
          </div>
        </div>
      </section>

      {/* =================================================================== */}
      {/* SECTION 2: Session Output Formats (Pill-Button Badges on Bottom)    */}
      {/* =================================================================== */}
      <section className="pt-2 border-t border-slate-200/60 dark:border-slate-700/60">
        <h4 className="mb-3 text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {t("exercises.formats.availableFormats", "Enabled Session Formats")}
        </h4>
        <div className="flex flex-wrap gap-2">
          {supportedFormats.map((fmt) => {
            const isSelected = (config.itemFormats || []).includes(fmt);

            return (
              <button
                key={fmt}
                type="button"
                onClick={() => toggleFormat(fmt)}
                className={`rounded px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors shadow-2xs ${
                  isSelected
                    ? "border border-blue-600 bg-blue-600 text-white shadow-xs"
                    : "border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-600"
                }`}
              >
                {fmt} {isSelected && "✓"}
              </button>
            );
          })}
        </div>
      </section>

      {/* =================================================================== */}
      {/* SECTION 3: Action / Generation CTA (Sticky Bottom Footer)           */}
      {/* =================================================================== */}
      <div className="pt-4 border-t border-slate-100 dark:border-slate-700">
        <button
          type="button"
          onClick={onGenerate}
          disabled={
            totalQuestions === 0 || config.itemFormats.length === 0 || isLoading
          }
          className="w-full rounded-md bg-blue-600 hover:bg-blue-700 py-3 text-sm font-bold text-white shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors"
        >
          {isLoading ? (
            <span>{t("exercises.loading", "Generating...")}</span>
          ) : (
            <span>
              {t("exercises.startExercise", { count: totalQuestions })}
            </span>
          )}
        </button>
      </div>
    </aside>
  );
};
