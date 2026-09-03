// src/components/words/SingleWordAdder.tsx
import React, { useEffect, useRef, useState } from "react";
import { Lemma } from "../../types";

interface SingleWordAdderProps {
  onSearch: (query: string) => Promise<Lemma[]>;
  onSelectLemma: (lemma: Lemma) => void;
}

export const SingleWordAdder: React.FC<SingleWordAdderProps> = ({
  onSearch,
  onSelectLemma,
}) => {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<Lemma[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  const [isOpen, setIsOpen] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  // Debounced API request to protect backend worker threads
  useEffect(() => {
    const trimmedQuery = query.trim();
    if (trimmedQuery.length < 2) {
      setResults([]);
      setIsOpen(false);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const debounceTimer = setTimeout(async () => {
      try {
        const payload = await onSearch(trimmedQuery);
        setResults(payload);
        setIsOpen(true);
      } catch (err) {
        console.error("Failed to retrieve lemma candidates:", err);
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [query, onSearch]);

  const handleSelect = (lemma: Lemma) => {
    onSelectLemma(lemma);
    setQuery("");
    setResults([]);
    setIsOpen(false);
  };

  return (
    <div ref={containerRef} className="relative mb-6 w-full max-w-lg">
      <label
        htmlFor="lemma-autocomplete-input"
        className="block text-xs font-semibold uppercase tracking-wider text-gray-700 dark:text-gray-300"
      >
        Individual Lemma Addition
      </label>

      <div className="relative mt-1.5">
        <input
          id="lemma-autocomplete-input"
          type="text"
          lang="ru"
          autoComplete="off"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search Russian lemma (e.g. говорить, стол)..."
          className="block w-full rounded-md border border-gray-300 bg-white py-2 pl-3 pr-10 text-sm placeholder-gray-400 shadow-sm transition focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 dark:placeholder-gray-500"
        />

        {isSearching && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
            <svg
              className="h-4 w-4 animate-spin text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
          </div>
        )}
      </div>

      {/* Floating suggestion list */}
      {isOpen && results.length > 0 && (
        <ul
          role="listbox"
          className="absolute z-20 mt-1 max-h-56 w-full overflow-y-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg ring-1 ring-black/5 dark:border-gray-700 dark:bg-gray-800"
        >
          {results.map((lemma) => (
            <li
              key={lemma.id}
              role="option"
              aria-selected={false}
              onClick={() => handleSelect(lemma)}
              className="flex cursor-pointer items-center justify-between px-3.5 py-2 text-sm text-gray-800 hover:bg-indigo-50 hover:text-indigo-900 dark:text-gray-200 dark:hover:bg-indigo-950 dark:hover:text-indigo-200"
            >
              <span className="font-medium">{lemma.lemma}</span>
              <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                {lemma.pos}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
