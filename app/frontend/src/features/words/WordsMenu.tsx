import React, { useEffect, useState } from "react";
import { Lemma, LessonList, QualityConfig } from "../../types";
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
        `/api/lemmas/search?q=${encodeURIComponent(query)}`,
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
    qualities: QualityConfig;
  }) => {
    try {
      const response = await fetch("/api/assessments/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`Pipeline submission failed: ${response.status}`);
      }

      const result = await response.json();
      console.log("Psychometric items generated:", result);

      // Future implementation: Dispatch an action here to navigate the user
      // to a "Review Items" interface, passing the 'result' data.
    } catch (error) {
      console.error("Generation pipeline error:", error);
    }
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
      <button
        onClick={onBack}
        className="absolute -top-12 left-0 mb-4 text-sm font-semibold text-blue-600 hover:underline"
      >
        ← Back
      </button>
      {/* Pass the populated database records into the UI shell */}
      <WordsSubLandingPage
        availableLessonLists={availableLessonLists}
        searchLemmasApi={handleSearchLemmasApi}
        onSubmitGeneration={handleSubmitGeneration}
      />
    </div>
  );
};
