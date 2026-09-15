// src/features/exercises/ExerciseSummary.tsx
import React from "react";
import { ExerciseResponse } from "../../types/words";

interface ExerciseSummaryProps {
  phase: "intro" | "conclusion";
  exerciseData: ExerciseResponse;
  attempts: any[];
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

  // Calculate score excluding flashcards (since they are subjective)
  const scoreAttempts = attempts.filter((a) => a.format !== "flashcard");
  const correctCount = scoreAttempts.filter((a) => a.isCorrect).length;

  return (
    <div className="flex flex-col items-center w-full max-w-3xl mx-auto py-12">
      <h2 className="text-3xl font-bold text-slate-900 mb-4">
        {isIntro ? "Exercise Overview" : "Exercise Complete!"}
      </h2>

      <p className="text-slate-600 mb-10 text-lg text-center">
        {isIntro
          ? `You are about to tackle ${totalCount} items.`
          : `You scored ${correctCount} out of ${scoreAttempts.length} objective items.`}
      </p>

      <div className="grid grid-cols-5 md:grid-cols-8 gap-4 mb-12 w-full place-items-center">
        {exerciseData.response_data.map((item, index) => {
          const finalAttempt = attempts
            .slice()
            .reverse()
            .find((a) => a.itemId === item.item_id);
          let boxStyle = "bg-slate-200 text-slate-500 border-slate-300";

          if (!isIntro && finalAttempt) {
            if (finalAttempt.format === "flashcard") {
              // Flashcard subjective colors
              const ratingColors: Record<string, string> = {
                forgot: "bg-red-100 border-red-500 text-red-800",
                struggled: "bg-amber-100 border-amber-500 text-amber-800",
                remembered: "bg-blue-100 border-blue-500 text-blue-800",
                mastered: "bg-emerald-100 border-emerald-500 text-emerald-800",
              };
              boxStyle = ratingColors[finalAttempt.finalRating] || boxStyle;
            } else {
              // Objective MCQ/FITB logic
              if (finalAttempt.isCorrect) {
                if (finalAttempt.selectedDistractors.length === 0) {
                  // right on 1st try: fully green
                  boxStyle =
                    "bg-emerald-100 border-emerald-500 text-emerald-800";
                } else {
                  // wrong then right: half red / half green (sharp diagonal split)
                  boxStyle =
                    "bg-gradient-to-r from-red-100 from-50% to-emerald-100 to-50% border-emerald-500 text-slate-800";
                }
              } else {
                // Wrong on all tries: Fully Red
                boxStyle = "bg-red-100 border-red-500 text-red-800";
              }
            }
          }

          return (
            <div
              key={`summary-box-${item.item_id}`}
              className={`flex items-center justify-center w-14 h-14 rounded-xl border-2 font-bold text-xl transition-all duration-300 ${boxStyle}`}
              title={!isIntro ? item.prompt : `Item ${index + 1}`}
            >
              {index + 1}
            </div>
          );
        })}
      </div>

      <button
        onClick={onAction}
        className="px-8 py-3 bg-blue-600 text-white rounded-lg"
      >
        {isIntro ? "Start Exercise" : "Return to Menu"}
      </button>
    </div>
  );
};
