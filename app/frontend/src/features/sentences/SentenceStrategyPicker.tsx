/**
 * src/features/sentences/SentenceStrategyPicker.tsx
 *
 * Displays linguistic target strategies grouped into pedagogical buckets:
 * 1. Слово в контексте (Cloze / In-sentence Morphology)
 * 2. Синтаксические связи (Dependency & Grammar Analysis)
 * 3. Порядок слов (Word Reordering)
 */

import React from "react";
import { useTranslation } from "react-i18next";
import { StrategyGroup } from "../../types/sentences";

export const SENTENCE_STRATEGY_GROUPS: StrategyGroup[] = [
  {
    groupKey: "sentencesMenu.group_cloze",
    strategies: [
      {
        id: "cloze_noun_morph",
        labelKey: "sentencesMenu.strat_cloze_noun",
        descriptionKey: "sentencesMenu.desc_cloze_noun",
        defaultFormat: "mcq",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "cloze_verb_morph",
        labelKey: "sentencesMenu.strat_cloze_verb",
        descriptionKey: "sentencesMenu.desc_cloze_verb",
        defaultFormat: "mcq",
        supportedFormats: ["mcq", "fitb"],
      },
      {
        id: "cloze_lexical",
        labelKey: "sentencesMenu.strat_cloze_lex",
        descriptionKey: "sentencesMenu.desc_cloze_lex",
        defaultFormat: "mcq",
        supportedFormats: ["mcq"],
      },
    ],
  },
  {
    groupKey: "sentencesMenu.group_word_order",
    strategies: [
      {
        id: "unscramble",
        labelKey: "sentencesMenu.strat_unscramble",
        descriptionKey: "sentencesMenu.desc_unscramble",
        defaultFormat: "unscramble",
        supportedFormats: ["unscramble"],
      },
    ],
  },
  {
    groupKey: "sentencesMenu.group_syntax",
    strategies: [
      {
        id: "label_dep_rel",
        labelKey: "sentencesMenu.strat_dep_rel",
        descriptionKey: "sentencesMenu.desc_dep_rel",
        defaultFormat: "mcq",
        supportedFormats: ["mcq"],
      },
      {
        id: "syntax_find_head",
        labelKey: "sentencesMenu.strat_find_head",
        descriptionKey: "sentencesMenu.desc_find_head",
        defaultFormat: "mcq",
        supportedFormats: ["mcq"],
      },
    ],
  },
];

interface Props {
  typeCounts: Record<string, number>;
  onCountChange: (strategyId: string, newCount: number) => void;
}

export const SentenceStrategyPicker: React.FC<Props> = ({
  typeCounts,
  onCountChange,
}) => {
  const { t } = useTranslation();

  return (
    <div className="flex flex-col gap-6">
      {SENTENCE_STRATEGY_GROUPS.map((group) => (
        <div
          key={group.groupKey}
          className="bg-white p-5 rounded-xl border border-stone-200 shadow-xs"
        >
          <h3 className="text-base font-semibold text-stone-800 mb-3 border-b border-stone-100 pb-2">
            {t(group.groupKey, group.groupKey.split(".").pop())}
          </h3>

          <div className="grid grid-cols-1 gap-3">
            {group.strategies.map((strat) => {
              const currentCount = typeCounts[strat.id] || 0;
              return (
                <div
                  key={strat.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-stone-50 border border-stone-200/60 hover:border-stone-300 transition-colors"
                >
                  <div className="flex flex-col pr-4">
                    <span className="text-sm font-medium text-stone-900">
                      {t(strat.labelKey, strat.id)}
                    </span>
                    <span className="text-xs text-stone-500">
                      {t(strat.descriptionKey, "")}
                    </span>
                  </div>

                  {/* Quantity Stepper */}
                  <div className="flex items-center gap-2 select-none">
                    <button
                      type="button"
                      onClick={() =>
                        onCountChange(strat.id, Math.max(0, currentCount - 1))
                      }
                      disabled={currentCount === 0}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-white border border-stone-300 text-stone-700 font-bold hover:bg-stone-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                    >
                      -
                    </button>
                    <span className="w-6 text-center text-sm font-semibold text-stone-800">
                      {currentCount}
                    </span>
                    <button
                      type="button"
                      onClick={() => onCountChange(strat.id, currentCount + 1)}
                      className="w-7 h-7 flex items-center justify-center rounded-md bg-white border border-stone-300 text-stone-700 font-bold hover:bg-stone-100 transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
};
