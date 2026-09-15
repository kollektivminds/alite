// src/features/exercises/MCQDisplay.tsx
import React, { useEffect, useState } from "react";
import { MCQResponse } from "../../types/words";

interface MCQDisplayProps {
  item: MCQResponse;
  attemptsRecord: any;
  onEvaluate: (option: string) => void;
  isResolved: boolean;
}

export const MCQDisplay: React.FC<MCQDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  // Local state to track what the user has clicked BEFORE hitting submit
  const [localSelection, setLocalSelection] = useState<string | null>(null);

  // Clear local selection if the item changes (e.g., moving to the next question)
  useEffect(() => {
    setLocalSelection(null);
  }, [item.item_id]);

  const handleSubmit = () => {
    if (localSelection && !isResolved) {
      onEvaluate(localSelection);
      // We do NOT clear localSelection here, so we can render it red/green based on the result
    }
  };

  // Helper to determine styling based on history AND current local selection
  const getOptionStyle = (option: string) => {
    const isPreviouslyFailed =
      attemptsRecord.selectedDistractors.includes(option);
    const isCurrentlySelected = localSelection === option;

    if (isPreviouslyFailed)
      return "bg-red-50 text-red-700 border-red-300 opacity-50 cursor-not-allowed";
    if (isCurrentlySelected && !isResolved)
      return "bg-blue-50 border-blue-500 text-blue-700 ring-2 ring-blue-200";
    if (isResolved && isCurrentlySelected && attemptsRecord.isCorrect)
      return "bg-emerald-50 border-emerald-500 text-emerald-800";

    return "bg-white border-slate-200 text-slate-800 hover:bg-slate-50 hover:border-slate-300";
  };

  return (
    // Flex container taking up full height to allow vertical centering
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Prompt: mb-12 pushes the options down, making the prompt sit slightly above true center */}
      <div className="mb-12 px-4 text-center max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-medium text-slate-900 leading-relaxed tracking-tight">
          {item.prompt}
        </h2>
      </div>

      {/* Options: Flex-wrap allows options to flow naturally based on text length */}
      <div className="flex flex-wrap justify-center gap-4 w-full max-w-3xl mb-8">
        {item.options.map((option, idx) => (
          <button
            key={`${item.item_id}-opt-${idx}`}
            onClick={() => setLocalSelection(option)}
            disabled={
              isResolved || attemptsRecord.selectedDistractors.includes(option)
            }
            className={`
              px-6 py-4 rounded-xl border-2 text-lg font-medium transition-all duration-200
              ${getOptionStyle(option)}
            `}
          >
            {option}
          </button>
        ))}
      </div>

      {/* Action Area: Submit or Continue */}
      <div className="h-16 flex items-center justify-center">
        {isResolved && attemptsRecord.revealedAnswer && (
          <div className="text-red-600 font-medium">
            Correct Answer: {attemptsRecord.revealedAnswer}
          </div>
        )}
        {!isResolved ? (
          <button
            onClick={handleSubmit}
            disabled={!localSelection}
            className="px-8 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Submit Answer
          </button>
        ) : (
          <div className="text-slate-500 italic">
            {/* The "Continue" button is currently handled in ExerciseContainer,
                but you could optionally render feedback text here! */}
            Item resolved.
          </div>
        )}
      </div>
    </div>
  );
};
