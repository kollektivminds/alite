// src/features/words/TranslitGuidePopover.tsx
import React from "react";
import { useTranslation } from "react-i18next";
import { TRANSLIT_GUIDE_GROUPS } from "./Translit";

export const TranslitGuidePopover: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="w-72 p-1 space-y-3 text-left">
      {/* Instructional Overview */}
      <div className="border-b border-slate-200 dark:border-slate-700 pb-2">
        <h4 className="text-xs font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider">
          {t("exercises.wordsMenu.translitGuide.title")}
        </h4>
        <p className="mt-0.5 text-[11px] text-slate-500 dark:text-slate-400 leading-snug">
          {t("exercises.wordsMenu.translitGuide.subtitle")}
        </p>
      </div>

      {/* Orthographic Categories Grid */}
      <div className="space-y-2.5">
        {TRANSLIT_GUIDE_GROUPS.map((group) => (
          <div key={group.categoryKey}>
            <span className="block text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1">
              {t(group.categoryKey) || group.categoryKey.split(".").pop()}
            </span>
            <div className="grid grid-cols-3 gap-1">
              {group.pairs.map(({ latin, cyrillic }) => (
                <div
                  key={latin}
                  className="flex items-center justify-between rounded bg-slate-50 dark:bg-slate-900/60 px-1.5 py-0.5 border border-slate-200/80 dark:border-slate-700/80 text-[11px]"
                >
                  <code className="font-mono text-blue-600 dark:text-blue-400 font-semibold">
                    {latin}
                  </code>
                  <span className="text-slate-400 text-[10px]">→</span>
                  <span className="font-medium text-slate-800 dark:text-slate-200">
                    {cyrillic}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Example Scaffolding */}
      <div className="rounded bg-blue-50/60 dark:bg-blue-950/30 p-2 border border-blue-100 dark:border-blue-900/40 text-[11px] leading-tight text-blue-900 dark:text-blue-200">
        <span className="font-semibold">{t("exercises.wordsMenu.eg")}: </span>
        <code className="font-mono text-blue-700 dark:text-blue-300">
          vyuchit&apos;
        </code>
        {" → "}
        <span className="font-bold">выучить</span>
      </div>
    </div>
  );
};
