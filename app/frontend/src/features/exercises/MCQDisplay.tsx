/**
 * src/features/exercises/MCQDisplay.tsx
 */

import React, { useEffect, useState } from "react";
import { AttemptRecord, MCQResponseItem } from "../../types/exercise";
import { renderFormattedPrompt } from "../../utils/formatPrompt";

interface MCQDisplayProps {
  item: MCQResponseItem;
  attemptsRecord: AttemptRecord;
  onEvaluate: (option: string) => void;
  isResolved: boolean;
}

export const MCQDisplay: React.FC<MCQDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  const [localSelection, setLocalSelection] = useState<string | null>(null);

  useEffect(() => {
    setLocalSelection(null);
  }, [item.item_id]);

  const handleSubmit = () => {
    if (localSelection && !isResolved) {
      onEvaluate(localSelection);
    }
  };

  const getOptionStyle = (optionStr: string) => {
    const isPreviouslyFailed =
      attemptsRecord.selectedDistractors.includes(optionStr);
    const isCurrentlySelected = localSelection === optionStr;

    if (isPreviouslyFailed) {
      return "bg-red-50 text-red-700 border-red-300 opacity-50 cursor-not-allowed";
    }
    if (isCurrentlySelected && !isResolved) {
      return "bg-blue-50 border-blue-500 text-blue-700 ring-2 ring-blue-200";
    }
    if (isResolved && isCurrentlySelected && attemptsRecord.isCorrect) {
      return "bg-emerald-50 border-emerald-500 text-emerald-800";
    }

    return "bg-white border-slate-200 text-slate-800 hover:bg-slate-50 hover:border-slate-300";
  };

  return (
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Formatted Prompt Area supporting sentence context & bold tokens */}
      <div className="mb-10 px-4 text-center max-w-2xl text-xl md:text-2xl font-medium text-slate-900 tracking-tight">
        {renderFormattedPrompt(item.prompt)}
      </div>

      {/* Options Grid */}
      <div className="flex flex-wrap justify-center gap-3.5 w-full max-w-3xl mb-8">
        {item.options.map((option, idx) => {
          const optionStr = String(option);
          return (
            <button
              key={`${item.item_id}-opt-${idx}`}
              type="button"
              onClick={() => setLocalSelection(optionStr)}
              disabled={
                isResolved ||
                attemptsRecord.selectedDistractors.includes(optionStr)
              }
              className={`
                px-6 py-3.5 rounded-xl border-2 text-lg font-medium transition-all duration-150 shadow-2xs
                ${getOptionStyle(optionStr)}
              `}
            >
              {optionStr}
            </button>
          );
        })}
      </div>

      {/* Action Controls */}
      <div className="h-16 flex items-center justify-center">
        {isResolved && attemptsRecord.revealedAnswer && (
          <div className="text-red-600 font-medium">
            Правильный ответ: {attemptsRecord.revealedAnswer}
          </div>
        )}
        {!isResolved ? (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!localSelection}
            className="px-8 py-3 rounded-xl font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            Ответить
          </button>
        ) : (
          <div className="text-slate-500 italic text-sm">
            Задание завершено.
          </div>
        )}
      </div>
    </div>
  );
};
