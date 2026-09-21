// src/features/words/SingleWordAdder.tsx
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
    // Guard clause: skip search if input is shorter than 2 characters
    if (query.trim().length < 2) {
      setResults([]);
      setHasSearched(false);
      setError(null);
      return;
    }

    setIsSearching(true);
    setHasSearched(false);
    setError(null);

    // Debounce timer: delays execution until typing pauses for 250ms
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
    }, 250);

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
          Word Lookup
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Search lexical dictionary forms using Cyrillic or Latin romanization.
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
          placeholder="e.g., собака, sobaka, читать, chitat'..."
          className="w-full rounded-md border border-gray-300 px-4 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100"
          autoComplete="off"
          spellCheck="false"
        />

        {isSearching && (
          <div className="absolute right-3 top-2.5 text-xs text-gray-400 animate-pulse">
            Searching...
          </div>
        )}

        {error && (
          <div className="mt-2 rounded-md bg-red-50 p-2 text-xs text-red-600 dark:bg-red-900/30 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Dropdown Container */}
        {!error && (results.length > 0 || (hasSearched && !isSearching)) && (
          <div className="absolute z-10 mt-1 max-h-60 w-full overflow-y-auto rounded-md border border-gray-200 bg-white shadow-lg dark:border-gray-700 dark:bg-gray-800">
            {results.length > 0 ? (
              <ul
                id="search-results-listbox"
                role="listbox"
                className="divide-y divide-gray-100 dark:divide-gray-700"
              >
                {results.map((lemma) => {
                  const displayText = lemma.lem_canon ?? lemma.lem_text ?? "—";

                  // Safely find the Latin transliteration from the unpacked array
                  const romanization = lemma.pronunciations?.find(
                    (p) => p.pron_type?.toUpperCase() === "ROMANIZATION",
                  )?.pron_text;

                  return (
                    <li key={lemma.id} role="option" aria-selected="false">
                      <button
                        type="button"
                        onClick={() => handleSelection(lemma)}
                        className="flex w-full items-center justify-between px-4 py-2.5 text-left hover:bg-slate-50 focus:bg-slate-50 focus:outline-none dark:hover:bg-slate-700/50 dark:focus:bg-slate-700/50 transition-colors"
                      >
                        <div className="flex items-baseline gap-2">
                          <span className="font-medium text-slate-900 dark:text-slate-100 text-sm">
                            {displayText}
                          </span>
                          {romanization && (
                            <span className="font-mono text-xs text-slate-400 dark:text-slate-500">
                              [{romanization}]
                            </span>
                          )}
                        </div>
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-slate-500 dark:bg-slate-700 dark:text-slate-300">
                          {lemma.pos}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="px-4 py-3 text-xs text-gray-500 text-center">
                No matches found for '{query}'.
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
};
