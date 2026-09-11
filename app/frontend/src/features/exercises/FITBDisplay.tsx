// src/features/exercises/FITBDisplay.tsx
import React, { useEffect, useRef, useState } from "react";
import { FITBResponse } from "../../types/words";

interface FITBDisplayProps {
  item: FITBResponse;
  attemptsRecord: any; // Type strictly against your AttemptRecord
  onEvaluate: (response: string) => void;
  isResolved: boolean;
}

export const FITBDisplay: React.FC<FITBDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  // 1. Controlled Input State
  const [inputValue, setInputValue] = useState<string>("");
  const inputRef = useRef<HTMLInputElement>(null);

  // 2. Reset input and auto-focus when the item changes
  useEffect(() => {
    setInputValue("");
    // Delaying focus slightly ensures the DOM has painted the new item
    setTimeout(() => inputRef.current?.focus(), 50);
  }, [item.item_id]);

  // 3. Form Submission Handler
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault(); // Prevents the browser from refreshing the page
    const trimmedInput = inputValue.trim();

    if (trimmedInput && !isResolved) {
      onEvaluate(trimmedInput);
    }
  };

  // 4. Dynamic Feedback Styling
  const getInputStyle = () => {
    // If the exact string they currently have typed has already been submitted and failed
    const isPreviouslyFailed = attemptsRecord.selectedDistractors.includes(
      inputValue.trim(),
    );

    if (isResolved && attemptsRecord.isCorrect) {
      return "bg-emerald-50 border-emerald-500 text-emerald-800 focus:ring-emerald-500";
    }
    if (isPreviouslyFailed) {
      return "bg-red-50 border-red-500 text-red-700 focus:ring-red-500";
    }

    // Default interactive state
    return "bg-white border-slate-300 text-slate-900 focus:ring-blue-500 focus:border-blue-500";
  };

  return (
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Prompt Area */}
      <div className="mb-12 px-4 text-center max-w-2xl">
        <h2 className="text-2xl md:text-3xl font-medium text-slate-900 leading-relaxed tracking-tight">
          {item.prompt}
        </h2>
      </div>

      {/* Form Wrapper for native 'Enter' key submission */}
      <form
        onSubmit={handleSubmit}
        className="flex flex-col items-center w-full max-w-md gap-8"
      >
        <input
          ref={inputRef}
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={isResolved}
          placeholder="Type your answer in Russian..."
          autoComplete="off"
          spellCheck="false" // Prevents the browser from drawing red squiggles under Russian words
          className={`
            w-full px-6 py-4 text-center text-xl rounded-xl border-2 transition-all duration-200 outline-none
            ${getInputStyle()}
          `}
        />

        {/* Action Area */}
        <div className="h-16 flex items-center justify-center w-full">
          {!isResolved ? (
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="px-8 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Submit Answer
            </button>
          ) : (
            <div className="text-slate-500 italic">Item resolved.</div>
          )}
        </div>
      </form>
    </div>
  );
};
