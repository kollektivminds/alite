/**
 * src/features/exercises/FITBDisplay.tsx
 */

import React, { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { AttemptRecord, FITBResponseItem } from "../../types/exercise";
import { renderFormattedPrompt } from "../../utils/formatPrompt";

interface FITBDisplayProps {
  item: FITBResponseItem;
  attemptsRecord: AttemptRecord;
  onEvaluate: (response: string) => void;
  isResolved: boolean;
}

export const FITBDisplay: React.FC<FITBDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  const [inputValue, setInputValue] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);
  const { t } = useTranslation();

  useEffect(() => {
    setInputValue("");
    const timer = setTimeout(() => inputRef.current?.focus(), 50);
    return () => clearTimeout(timer);
  }, [item.item_id]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (trimmed && !isResolved) {
      onEvaluate(trimmed);
    }
  };

  const getInputStyle = () => {
    const isFailed = attemptsRecord.selectedDistractors.includes(
      inputValue.trim(),
    );

    if (isResolved && attemptsRecord.isCorrect) {
      return "bg-emerald-50 border-emerald-500 text-emerald-800 focus:ring-emerald-500";
    }
    if (isFailed) {
      return "bg-red-50 border-red-500 text-red-700 focus:ring-red-500";
    }
    return "bg-white border-slate-300 text-slate-900 focus:ring-blue-500 focus:border-blue-500";
  };

  return (
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Sentence / Cloze Context Prompt */}
      <div className="mb-10 px-4 text-center max-w-2xl text-xl md:text-2xl font-medium text-slate-900 leading-relaxed tracking-tight">
        {renderFormattedPrompt(item.prompt)}
      </div>

      <form
        onSubmit={handleSubmit}
        className="flex flex-col items-center w-full max-w-md gap-6"
      >
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isResolved}
          placeholder={t("exercises.navigation.fitb.typeWord")}
          autoComplete="off"
          spellCheck="false"
          className={`
            w-full px-6 py-4 text-center text-xl rounded-xl border-2 transition-all duration-150 outline-hidden
            ${getInputStyle()}
          `}
        />

        <div className="h-16 flex items-center justify-center w-full">
          {isResolved && attemptsRecord.revealedAnswer && (
            <div className="text-red-600 font-medium text-center">
              {t("exercises.navigation.correctAnswer")}:{" "}
              {attemptsRecord.revealedAnswer}
            </div>
          )}
          <br />
          {!isResolved ? (
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-8 py-3 rounded-xl font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              {t("exercises.navigation.check")}
            </button>
          ) : (
            <div className="text-slate-500 italic text-sm">
              {t("exercises.navigation.exComplete")}.
            </div>
          )}
        </div>
      </form>
    </div>
  );
};
