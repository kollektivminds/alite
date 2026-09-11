// src/features/exercises/ExerciseContainer.tsx
import React, { useState } from "react";
import { DIFFICULTY_MAP, DifficultyLevel } from "../../types/exercise";
import { ExerciseResponse } from "../../types/words";
import { ExerciseSummary } from "./ExerciseSummary";
import { ItemFormatRouter } from "./ItemFormatRouter";
import { ProgressBar } from "./ProgressBar";

// Define the shape of tracking data
interface AttemptRecord {
  itemId: number;
  startTime: number;
  endTime: number | null;
  selectedDistractors: string[];
  isCorrect: boolean;
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
  // 1. Phase Management
  const [phase, setPhase] = useState<"intro" | "active" | "conclusion">(
    "intro",
  );
  const [currentIndex, setCurrentIndex] = useState<number>(0);

  // 2. Telemetry and State Tracking
  const [exerciseStartTime, setExerciseStartTime] = useState<number | null>(
    null,
  );
  const [attempts, setAttempts] = useState<AttemptRecord[]>([]);

  // Local state to manage the UI freeze and 'Continue' button visibility for the current item
  const [isItemResolved, setIsItemResolved] = useState<boolean>(false);

  // start Exercise Handler
  const handleStartExercise = () => {
    setExerciseStartTime(Date.now());
    setPhase("active");
    // Initialize the first attempt record
    startNewItemRecord(exerciseData.response_data[0].item_id);
  };

  // Helper to push a fresh record into our attempts array when an item loads
  const startNewItemRecord = (itemId: number) => {
    setAttempts((prev) => [
      ...prev,
      {
        itemId,
        startTime: Date.now(),
        endTime: null,
        selectedDistractors: [],
        isCorrect: false,
      },
    ]);
  };

  // the Core Evaluation Handler
  const handleEvaluateOption = async (selectedOption: string) => {
    if (isItemResolved) return;

    const currentItem = exerciseData.response_data[currentIndex];
    // access the current attempt record established when the item loaded
    const currentAttempt = attempts[attempts.length - 1];

    // calculate the response time delta for analytics
    const responseTimeMs = Date.now() - currentAttempt.startTime;

    // derive the attempt number based on previously failed tries
    const currentAttemptNum = currentAttempt.selectedDistractors.length + 1;

    try {
      // construct payload strictly matching AnswerSubmission
      const submissionPayload = {
        item_id: currentItem.item_id,
        response: selectedOption,
        response_time_ms: responseTimeMs,
        attempt_num: currentAttemptNum,
      };

      const response = await fetch("/api/v1/exercises/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submissionPayload),
      });

      if (!response.ok) throw new Error("Evaluation failed");

      // parse the response matching AnswerResult
      const result = await response.json();

      setAttempts((prev) => {
        // 1. Shallow copy the main array
        const newAttempts = [...prev];

        // 2. IMMUTABLE CLONE of the target object and its nested array
        const targetIndex = newAttempts.length - 1;
        const attemptToUpdate = {
          ...newAttempts[targetIndex],
          selectedDistractors: [
            ...newAttempts[targetIndex].selectedDistractors,
          ],
        };

        if (result.is_correct) {
          attemptToUpdate.isCorrect = true;
          attemptToUpdate.endTime = Date.now();
          setIsItemResolved(true);
        } else {
          // Now safe to push because we cloned the array above
          attemptToUpdate.selectedDistractors.push(selectedOption);

          // Get max tries from the configuration map[cite: 10, 12]
          const maxTries = DIFFICULTY_MAP[difficulty].maxTries;

          if (attemptToUpdate.selectedDistractors.length >= maxTries) {
            attemptToUpdate.endTime = Date.now();
            setIsItemResolved(true);
          }
        }

        // 3. Replace the old object reference with our newly mutated clone
        newAttempts[targetIndex] = attemptToUpdate;
        return newAttempts;
      });
    } catch (error) {
      console.error("Network error during evaluation:", error);
    }
  };

  // 5. Navigation Handler
  const handleNextItem = () => {
    setIsItemResolved(false);

    if (currentIndex + 1 < exerciseData.num_questions) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      startNewItemRecord(exerciseData.response_data[nextIndex].item_id);
    } else {
      setPhase("conclusion");
    }
  };

  const currentAttemptRecord = attempts[attempts.length - 1];
  const maxTries = DIFFICULTY_MAP[difficulty].maxTries; //[cite: 12]
  const currentTryNumber = currentAttemptRecord
    ? currentAttemptRecord.selectedDistractors.length + 1
    : 1;
  const displayTry = Math.min(currentTryNumber, maxTries);

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
            {/* Visual Scaffolding Headers */}
            <div className="w-full flex justify-between items-center mb-8 px-4 max-w-3xl">
              <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Item {currentIndex + 1} of {exerciseData.num_questions}
              </span>
              <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">
                Attempt {displayTry} / {maxTries}
              </span>
            </div>

            <ItemFormatRouter
              item={exerciseData.response_data[currentIndex]}
              attemptsRecord={currentAttemptRecord}
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
