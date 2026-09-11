// src/features/exercises/ExerciseSummary.tsx
import React from "react";
import { ExerciseResponse } from "../../types/words";

interface ExerciseSummaryProps {
  phase: "intro" | "conclusion";
  exerciseData: ExerciseResponse;
  attempts: any[]; // Type this strictly to your AttemptRecord array
  onAction: () => void;
}

export const ExerciseSummary: React.FC<ExerciseSummaryProps> = ({
  phase,
  exerciseData,
  attempts,
  onAction,
}) => {
  const isIntro = phase === "intro";
  const totalCount = exerciseData.num_questions;

  // Calculate the final score by filtering the attempts history
  const correctCount = attempts.filter((a) => a.isCorrect).length;

  return (
    <div className="flex flex-col items-center w-full max-w-3xl mx-auto py-12 animate-fadeIn">
      <h2 className="text-3xl font-bold text-slate-900 mb-4">
        {isIntro ? "Exercise Overview" : "Exercise Complete!"}
      </h2>

      <p className="text-slate-600 mb-10 text-lg text-center">
        {isIntro
          ? `You are about to tackle ${totalCount} items. Good luck!`
          : `You scored ${correctCount} out of ${totalCount}.`}
      </p>

      {/* Responsive Grid for Item Representation */}
      <div className="grid grid-cols-5 md:grid-cols-8 gap-4 mb-12 w-full place-items-center">
        {exerciseData.response_data.map((item, index) => {
          // Extract the final record for this specific item
          const finalAttempt = attempts
            .slice()
            .reverse()
            .find((a) => a.itemId === item.item_id);

          // Default styling for the intro screen (gray boxes)
          let boxStyle = "bg-slate-200 text-slate-500 border-slate-300";

          if (!isIntro && finalAttempt) {
            boxStyle = finalAttempt.isCorrect
              ? "bg-emerald-100 border-emerald-500 text-emerald-800"
              : "bg-red-100 border-red-500 text-red-800";
          }

          return (
            <div
              key={`summary-box-${item.item_id}`}
              className={`flex items-center justify-center w-14 h-14 rounded-xl border-2 font-bold text-xl transition-all duration-300 ${boxStyle}`}
              // Native browser tooltip displays the prompt on hover during conclusion
              title={!isIntro ? item.prompt : `Item ${index + 1}`}
            >
              {index + 1}
            </div>
          );
        })}
      </div>

      <button
        onClick={onAction}
        className="px-8 py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
      >
        {isIntro ? "Start Exercise" : "Return to Menu"}
      </button>
    </div>
  );
};
