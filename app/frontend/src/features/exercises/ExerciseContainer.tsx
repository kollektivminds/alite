// src/features/exercises/ExerciseContainer.tsx
import React, { useState } from "react";
import { DIFFICULTY_MAP, DifficultyLevel } from "../../types/exercise";
import { ExerciseResponse } from "../../types/words";
import { ExerciseSummary } from "./ExerciseSummary";
import { ItemFormatRouter } from "./ItemFormatRouter";
import { ProgressBar } from "./ProgressBar";

interface AttemptRecord {
  itemId: number;
  format: string;
  startTime: number;
  endTime: number | null;
  selectedDistractors: string[];
  isCorrect: boolean;
  finalRating?: string;
  revealedAnswer?: string;
}

interface ExerciseContainerProps {
  exerciseData: ExerciseResponse;
  difficulty: DifficultyLevel;
  onExit: () => void;
}

export const ExerciseContainer: React.FC<ExerciseContainerProps> = ({
  exerciseData,
  difficulty,
  onExit,
}) => {
  const [phase, setPhase] = useState<"intro" | "active" | "conclusion">(
    "intro",
  );
  const [currentIndex, setCurrentIndex] = useState<number>(0);
  const [attempts, setAttempts] = useState<AttemptRecord[]>([]);
  const [isItemResolved, setIsItemResolved] = useState<boolean>(false);

  // Helper strictly requires the complete Item object, preventing undefined properties
  const startNewItemRecord = (item: ExerciseResponse["response_data"][0]) => {
    setAttempts((prev) => [
      ...prev,
      {
        itemId: item.item_id,
        format: item.item_format,
        startTime: Date.now(),
        endTime: null,
        selectedDistractors: [],
        isCorrect: false,
      },
    ]);
  };

  const handleStartExercise = () => {
    setPhase("active");
    // Pass the full item object, NOT just item_id
    startNewItemRecord(exerciseData.response_data[0]);
  };

  const handleEvaluateOption = async (selectedOption: string) => {
    if (isItemResolved) return;

    const currentItem = exerciseData.response_data[currentIndex];
    const currentAttempt = attempts[attempts.length - 1];
    const responseTimeMs = Date.now() - currentAttempt.startTime;
    const currentAttemptNum = currentAttempt.selectedDistractors.length + 1;

    const maxTries = DIFFICULTY_MAP[difficulty]?.maxTries ?? 1;
    const isFlashcard = currentItem.item_format === "flashcard";
    const isFinalAttempt = isFlashcard || currentAttemptNum >= maxTries;

    try {
      const submissionPayload = {
        item_id: currentItem.item_id,
        response: selectedOption,
        response_time_ms: responseTimeMs,
        attempt_num: isFlashcard ? 1 : currentAttemptNum,
        is_final_attempt: isFinalAttempt,
      };

      const response = await fetch("/api/v1/exercises/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submissionPayload),
      });

      if (!response.ok) {
        throw new Error(
          `HTTP Error ${response.status}: ${await response.text()}`,
        );
      }

      const result = await response.json();

      setAttempts((prev) => {
        const next = [...prev];
        const targetIdx = next.length - 1;
        const updated = {
          ...next[targetIdx],
          selectedDistractors: [...next[targetIdx].selectedDistractors],
        };

        if (isFlashcard) {
          updated.isCorrect = result.is_correct;
          updated.finalRating = selectedOption;
          updated.endTime = Date.now();
          setIsItemResolved(true); // Resolve immediately on 1st interaction
        } else if (result.is_correct) {
          updated.isCorrect = true;
          updated.endTime = Date.now();
          setIsItemResolved(true); // Resolve on correct match
        } else {
          updated.selectedDistractors.push(selectedOption);
          if (isFinalAttempt) {
            updated.endTime = Date.now();
            updated.revealedAnswer = result.correct_answer;
            setIsItemResolved(true); // Resolve when tries expire
          }
        }

        next[targetIdx] = updated;
        return next;
      });
    } catch (error) {
      console.error("Evaluation pipeline failed:", error);
    }
  };

  const handleNextItem = () => {
    setIsItemResolved(false);

    if (currentIndex + 1 < exerciseData.num_questions) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      // Pass the full item object
      startNewItemRecord(exerciseData.response_data[nextIndex]);
    } else {
      setPhase("conclusion");
    }
  };

  return (
    <div className="exercise-shell relative w-full min-h-[80vh] flex flex-col items-center">
      {phase === "active" && (
        <ProgressBar
          currentIndex={currentIndex}
          totalItems={exerciseData.num_questions}
        />
      )}

      <div className="exercise-content flex-grow flex items-center justify-center w-full max-w-4xl p-6">
        {phase === "intro" && (
          <ExerciseSummary
            phase={phase}
            exerciseData={exerciseData}
            attempts={attempts}
            onAction={handleStartExercise}
          />
        )}

        {phase === "active" && (
          <div className="active-item-wrapper w-full flex flex-col items-center">
            <ItemFormatRouter
              item={exerciseData.response_data[currentIndex]}
              attemptsRecord={attempts[attempts.length - 1]}
              onEvaluate={handleEvaluateOption}
              isResolved={isItemResolved}
            />

            {isItemResolved && (
              <button
                onClick={handleNextItem}
                className="mt-8 px-8 py-3 rounded-lg font-semibold bg-blue-600 text-white hover:bg-blue-700 transition-colors shadow-sm"
              >
                Continue
              </button>
            )}
          </div>
        )}

        {phase === "conclusion" && (
          <ExerciseSummary
            phase={phase}
            exerciseData={exerciseData}
            attempts={attempts}
            onAction={onExit}
          />
        )}
      </div>
    </div>
  );
};
