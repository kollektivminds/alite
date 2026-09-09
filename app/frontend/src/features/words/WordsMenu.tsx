import React, { useEffect, useState } from "react";
import { ExerciseResponse, Lemma, LessonList } from "../../types/words";
import { ExerciseContainer } from "../exercises/ExerciseContainer";
import { WordsSubLandingPage } from "./WordSubLandingPage";

interface WordsMenuProps {
  onBack: () => void;
}

export const WordsMenu: React.FC<WordsMenuProps> = ({ onBack }) => {
  const [availableLessonLists, setAvailableLessonLists] = useState<
    LessonList[]
  >([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeExercise, setActiveExercise] = useState<ExerciseResponse | null>(
    null,
  );

  // Execute the network request on component mount
  useEffect(() => {
    const fetchInitialData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // In production, use an environment variable (e.g., import.meta.env.VITE_API_URL).
        const response = await fetch(
          "http://0.0.0.0:8000/api/v1/lesslists/all",
        );

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: LessonList[] = await response.json();
        setAvailableLessonLists(data);
      } catch (err) {
        console.error("Failed to fetch lesson lists:", err);
        setError(
          "Failed to load curriculum data. Please check your connection.",
        );
      } finally {
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  // 1. Search Dictionary Forms
  const handleSearchLemmasApi = async (query: string): Promise<Lemma[]> => {
    try {
      // URL encode the query to safely handle Cyrillic characters
      const response = await fetch(
        `/api/v1/lemmas/search?q=${encodeURIComponent(query)}`,
      );

      if (!response.ok) {
        throw new Error(`Search failed with status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Database search error:", error);
      // Return an empty array so the UI dropdown smoothly renders "No results"
      // instead of crashing the React tree.
      return [];
    }
  };

  // 2. Submit Generation Payload
  const handleSubmitGeneration = async (payload: {
    lemmaIds: string[];
    qualities: any;
  }) => {
    try {
      // A. Transform string IDs from the UI into integers for PostgreSQL/SQLAlchemy
      const numericLemIds = payload.lemmaIds
        .map((id) => parseInt(id, 10))
        .filter((id) => !isNaN(id));

      // B. Filter out strategies with 0 counts to prevent backend iteration over empty requests
      const activeTypeCounts = Object.entries(
        payload.qualities.typeCounts || {},
      )
        .filter(([_, count]) => Number(count) > 0)
        .reduce(
          (acc, [key, count]) => {
            const normalizedKey = key.toLowerCase();
            acc[normalizedKey] = Number(count);
            return acc;
          },
          {} as Record<string, number>,
        );

      // C. Construct the exact schema expected by schemas.ExerciseRequest
      const requestPayload = {
        exercise_context: {
          lem_ids: numericLemIds,
          ex_formats: payload.qualities.itemFormats,
          difficulty: payload.qualities.difficulty,
          allow_odd_one_out: payload.qualities.allowOddOneOut,
          max_keys: payload.qualities.maxKeys,
          max_distractors: payload.qualities.maxDistractors,
        },
        type_counts: activeTypeCounts,
        // D. Optional: Explicitly send null or an empty object to satisfy the Optional[StrategyConfigs]
        grammar_focus: null,
      };

      const response = await fetch("/api/v1/exercises/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        // Log the exact validation error returned by FastAPI if it fails again
        const errDetail = await response.text();
        throw new Error(
          `Pipeline submission failed: ${response.status} - ${errDetail}`,
        );
      }

      const result = await response.json();
      // console.log("Psychometric items generated:", result);
      setActiveExercise(result);

      // Future implementation: Dispatch an action here to navigate the user
      // to a "Review Items" interface, passing the 'result' data.
    } catch (error) {
      console.error("Generation pipeline error:", error);
    }
  };

  const handleExitExercise = () => {
    setActiveExercise(null);
  };

  if (isLoading)
    return (
      <div className="p-8 text-center text-gray-500">
        Loading curriculum modules...
      </div>
    );
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="w-full relative">
      {/* Conditionally hide the back button if they are in an active exercise */}
      {!activeExercise && (
        <button
          onClick={onBack}
          className="absolute -top-12 left-0 mb-4 text-sm font-semibold text-blue-600 hover:underline"
        >
          ← Back
        </button>
      )}

      {/* D. Declaratively swap the UI based on activeExercise state */}
      {activeExercise ? (
        <ExerciseContainer
          exerciseData={activeExercise}
          onExit={handleExitExercise}
        />
      ) : (
        <WordsSubLandingPage
          availableLessonLists={availableLessonLists}
          searchLemmasApi={handleSearchLemmasApi}
          onSubmitGeneration={handleSubmitGeneration}
        />
      )}
    </div>
  );
};
