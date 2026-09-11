// src/features/exercises/FlashcardDisplay.tsx
import React, { useEffect, useState } from "react";

// Matches backend polymorphic flashcard payload
export interface FlashcardItem {
  item_id: number;
  item_format: "flashcard";
  prompt: string; // e.g., Target Russian word or English gloss
  back_text: string; // e.g., Definition, inflectional table, or translation
  notes?: string; // Optional grammatical nuance or stress note
}

// 4-tier ordinal feedback mapping to BKT and Spaced Repetition
export type RecallRating = "forgot" | "struggled" | "remembered" | "mastered";

interface FlashcardDisplayProps {
  item: FlashcardItem;
  onEvaluate: (ratingToken: RecallRating) => void;
  isResolved: boolean;
}

interface RatingOption {
  key: RecallRating;
  label: string;
  description: string;
  colorClass: string;
  numericKey: string; // Shortcut key (1-4)
}

const RATING_OPTIONS: RatingOption[] = [
  {
    key: "forgot",
    label: "Forgot",
    description: "No recall",
    colorClass:
      "bg-red-50 text-red-700 border-red-200 hover:bg-red-100 hover:border-red-300",
    numericKey: "1",
  },
  {
    key: "struggled",
    label: "Struggled",
    description: "Partial/Slow",
    colorClass:
      "bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100 hover:border-amber-300",
    numericKey: "2",
  },
  {
    key: "remembered",
    label: "Remembered",
    description: "Recalled with effort",
    colorClass:
      "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 hover:border-blue-300",
    numericKey: "3",
  },
  {
    key: "mastered",
    label: "Mastered",
    description: "Immediate recall",
    colorClass:
      "bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100 hover:border-emerald-300",
    numericKey: "4",
  },
];

export const FlashcardDisplay: React.FC<FlashcardDisplayProps> = ({
  item,
  onEvaluate,
  isResolved,
}) => {
  const [isFlipped, setIsFlipped] = useState<boolean>(false);

  // Reset rotation state on question change
  useEffect(() => {
    setIsFlipped(false);
  }, [item.item_id]);

  // Keyboard accessibility: Space to flip, 1-4 to rate (only when flipped)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (isResolved) return;

      if (e.code === "Space") {
        e.preventDefault();
        setIsFlipped((prev) => !prev);
      } else if (isFlipped) {
        const selected = RATING_OPTIONS.find((opt) => opt.numericKey === e.key);
        if (selected) {
          e.preventDefault();
          onEvaluate(selected.key);
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isFlipped, isResolved, onEvaluate]);

  return (
    <div className="flex flex-col items-center justify-center w-full max-w-2xl mx-auto py-8">
      {/* Instructions header for reduced extraneous cognitive load */}
      <div className="mb-4 text-xs tracking-wider uppercase text-slate-400 font-semibold">
        {!isFlipped
          ? "Click card or press Space to reveal"
          : "Evaluate your mental retrieval"}
      </div>

      {/* 3D Perspective Container */}
      <div
        className="w-full h-80 [perspective:1000px] cursor-pointer select-none"
        onClick={() => !isResolved && setIsFlipped((prev) => !prev)}
      >
        {/* Animated Inner Card Shell */}
        <div
          className={`
            relative w-full h-full rounded-2xl shadow-sm border border-slate-200
            transition-transform duration-500 [transform-style:preserve-3d]
            ${isFlipped ? "[transform:rotateY(180deg)]" : ""}
          `}
        >
          {/* ================= CARD FRONT ================= */}
          <div className="absolute inset-0 w-full h-full rounded-2xl bg-white p-8 flex flex-col justify-between items-center [backface-visibility:hidden]">
            <span className="text-xs font-semibold tracking-wider text-slate-400 uppercase">
              Prompt
            </span>

            <div className="text-center px-4">
              <h2 className="text-3xl md:text-4xl font-semibold text-slate-900 leading-snug tracking-tight">
                {item.prompt}
              </h2>
            </div>

            <div className="text-xs text-blue-600 font-medium hover:underline">
              Reveal Answer ⟲
            </div>
          </div>

          {/* ================= CARD BACK ================= */}
          <div className="absolute inset-0 w-full h-full rounded-2xl bg-slate-50 p-8 flex flex-col justify-between items-center border-2 border-blue-500/20 [transform:rotateY(180deg)] [backface-visibility:hidden]">
            <span className="text-xs font-semibold tracking-wider text-blue-600 uppercase">
              Answer Key
            </span>

            <div className="text-center px-4 space-y-3">
              <h2 className="text-3xl md:text-4xl font-semibold text-slate-900 leading-snug tracking-tight">
                {item.back_text}
              </h2>
              {item.notes && (
                <p className="text-sm text-slate-500 italic max-w-md mx-auto">
                  {item.notes}
                </p>
              )}
            </div>

            <span className="text-xs text-slate-400">Card flipped</span>
          </div>
        </div>
      </div>

      {/* Action / Evaluation Area */}
      <div className="w-full mt-8 min-h-[5rem] flex items-center justify-center">
        {isFlipped && !isResolved ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 w-full animate-fadeIn">
            {RATING_OPTIONS.map((opt) => (
              <button
                key={opt.key}
                type="button"
                onClick={() => onEvaluate(opt.key)}
                className={`
                  flex flex-col items-center justify-center p-3 rounded-xl border
                  transition-all duration-150 transform active:scale-95 text-center
                  ${opt.colorClass}
                `}
              >
                <div className="flex items-center gap-1.5 font-semibold text-sm">
                  <span>{opt.label}</span>
                  <span className="text-[10px] opacity-60 border border-current rounded px-1">
                    {opt.numericKey}
                  </span>
                </div>
                <span className="text-[11px] opacity-80 mt-0.5">
                  {opt.description}
                </span>
              </button>
            ))}
          </div>
        ) : (
          <div className="text-sm text-slate-400 italic">
            {isResolved
              ? "Telemetry captured. Ready to continue."
              : "Inspect card before scoring"}
          </div>
        )}
      </div>
    </div>
  );
};
