import React, { useEffect, useState } from "react";
import { Lemma } from "../../types/words";

interface SingleWordAdderProps {
  onSearch: (query: string) => Promise<Lemma[]>;
  onSelectLemma: (lemma: Lemma) => void;
}

export const SingleWordAdder: React.FC<SingleWordAdderProps> = ({
  onSearch,
  onSelectLemma,
}) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Lemma[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // 1. Guard Clause: Skip search if input is too short
    if (query.trim().length < 2) {
      setResults([]);
      setHasSearched(false);
      setError(null);
      return;
    }

    setIsSearching(true);
    setHasSearched(false);
    setError(null);

    // 2. Debounce Timer: Delays execution until typing pauses
    const debounceTimer = setTimeout(async () => {
      try {
        const data = await onSearch(query);
        setResults(data);
      } catch (err) {
        console.error("Dictionary lookup failed:", err);
        setResults([]);
        setError("Failed to query the database. Please try again.");
      } finally {
        setIsSearching(false);
        setHasSearched(true);
      }
    }, 300);

    // 3. Cleanup: Clears the timer if the query changes before 300ms
    return () => clearTimeout(debounceTimer);
  }, [query, onSearch]);

  const handleSelection = (lemma: Lemma) => {
    onSelectLemma(lemma);
    setQuery("");
    setResults([]);
    setHasSearched(false);
  };

  return (
    <section aria-labelledby="manual-add-heading" className="space-y-4">
      <div>
        <h3
          id="manual-add-heading"
          className="text-lg font-semibold text-gray-900 dark:text-gray-100"
        >
          Individual Lemma Lookup
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Search the database for specific dictionary forms to include.
        </p>
      </div>

      <div className="relative w-full max-w-md">
        <label htmlFor="lemma-search" className="sr-only">
          Search dictionary form
        </label>
        <input
          id="lemma-search"
          type="text"
          role="combobox"
          aria-expanded={results.length > 0}
          aria-controls="search-results-listbox"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g., собака, читать..."
          className="w-full rounded-md border border-gray-300 px-4 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          autoComplete="off"
        />

        {isSearching && (
          <div className="absolute right-3 top-2.5 text-sm text-gray-400">
            Searching...
          </div>
        )}

        {/* Error State Rendering */}
        {error && (
          <div className="mt-2 rounded-md bg-red-50 p-2 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Dropdown Container */}
        {!error && (results.length > 0 || (hasSearched && !isSearching)) && (
          <div className="absolute z-10 mt-1 max-h-60 w-full overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {results.length > 0 ? (
              <ul id="search-results-listbox" role="listbox">
                {results.map((lemma) => {
                  const displayText = lemma.lem_canon ?? lemma.lem_text ?? "—";
                  return (
                    <li key={lemma.id} role="option" aria-selected="false">
                      <button
                        type="button"
                        onClick={() => handleSelection(lemma)}
                        className="flex w-full items-center justify-between px-4 py-2 text-left hover:bg-gray-100 focus:bg-gray-100 focus:outline-none dark:hover:bg-gray-700 dark:focus:bg-gray-700"
                      >
                        <span className="font-medium text-gray-900 dark:text-gray-100">
                          {displayText}
                        </span>
                        <span className="text-xs text-gray-500 uppercase tracking-wider">
                          {lemma.pos}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="px-4 py-3 text-sm text-gray-500">
                <p>No matches found for "{query}".</p>
                <button
                  type="button"
                  disabled
                  className="mt-2 inline-flex items-center rounded border border-transparent bg-blue-100 px-2.5 py-1.5 text-xs font-medium text-blue-700 opacity-50 cursor-not-allowed"
                >
                  Request Pipeline Generation (Coming Soon)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
