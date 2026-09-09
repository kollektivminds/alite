// src/features/exercises/ExerciseContainer.tsx
import React, { useState } from "react";
import { ExerciseResponse } from "../../types/words";

// Define the shape of our tracking data based on your requirements
interface AttemptRecord {
  itemId: number;
  startTime: number;
  endTime: number | null;
  selectedDistractors: string[];
  isCorrect: boolean;
}

interface ExerciseContainerProps {
  exerciseData: ExerciseResponse;
  onExit: () => void;
}

export const ExerciseContainer: React.FC<ExerciseContainerProps> = ({
  exerciseData,
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

  // 3. Start Exercise Handler
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

  // 4. The Core Evaluation Handler (To be passed to MCQDisplay)
  const handleEvaluateOption = async (selectedOption: string) => {
    if (isItemResolved) return;

    const currentItem = exerciseData.response_data[currentIndex];
    // Access the current attempt record we established when the item loaded
    const currentAttempt = attempts[attempts.length - 1];

    // 1. Calculate the response time delta for your analytics
    const responseTimeMs = Date.now() - currentAttempt.startTime;

    // 2. Derive the attempt number based on previously failed tries
    const currentAttemptNum = currentAttempt.selectedDistractors.length + 1;

    try {
      // 3. Construct payload strictly matching AnswerSubmission
      const submissionPayload = {
        item_id: currentItem.item_id,
        selection: selectedOption,
        response_time_ms: responseTimeMs,
        attempt_num: currentAttemptNum,
      };

      const response = await fetch("/api/v1/exercises/evaluate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(submissionPayload),
      });

      if (!response.ok) throw new Error("Evaluation failed");

      // 4. Parse the response matching AnswerResult
      const result = await response.json();

      // 5. Update UI state based on result.is_correct
      setAttempts((prev) => {
        const newAttempts = [...prev];
        const attemptToUpdate = newAttempts[newAttempts.length - 1];

        if (result.is_correct) {
          attemptToUpdate.isCorrect = true;
          attemptToUpdate.endTime = Date.now();
          setIsItemResolved(true);
        } else {
          attemptToUpdate.selectedDistractors.push(selectedOption);
          // Check against max tries (e.g., 2)
          if (attemptToUpdate.selectedDistractors.length >= 2) {
            attemptToUpdate.endTime = Date.now();
            setIsItemResolved(true);
            // Optionally display result.correct_answer or result.explanation here
          }
        }
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

  // 6. Declarative Rendering
  return (
    <div className="exercise-shell relative w-full h-full flex flex-col items-center">
      {/* Top Progress Bar - Only in active phase */}
      {phase === "active" && (
        <div className="progress-bar-placeholder w-full h-4 bg-gray-200">
          {/* Render colored segments based on the `attempts` array */}
        </div>
      )}

      {/* Main Content Area */}
      <div className="exercise-content flex-grow flex items-center justify-center w-full max-w-4xl p-6">
        {phase === "intro" && (
          <div className="intro-screen">
            {/* Render SummaryGrid with initial gray boxes */}
            <button onClick={handleStartExercise}>Start Exercise</button>
          </div>
        )}

        {phase === "active" && (
          <div className="active-item-wrapper w-full">
            {/* Render MCQDisplay here, passing the current item,
                the handleEvaluateOption function, and the current attempts record
                so it knows what to color red/green and when to freeze */}

            {isItemResolved && (
              <button
                onClick={handleNextItem}
                className="mt-8 bg-blue-600 text-white"
              >
                Continue
              </button>
            )}
          </div>
        )}

        {phase === "conclusion" && (
          <div className="conclusion-screen">
            {/* Render SummaryGrid colored based on attempts, calculate total score */}
            <button onClick={onExit}>Return to Menu</button>
          </div>
        )}
      </div>
    </div>
  );
};
