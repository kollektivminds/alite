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

  // Tracks the currently hovered lemma to populate the inspector flyout
  const [hoveredLemma, setHoveredLemma] = useState<Lemma | null>(null);

  useEffect(() => {
    if (query.trim().length < 2) {
      setResults([]);
      setHasSearched(false);
      setError(null);
      setHoveredLemma(null);
      return;
    }

    setIsSearching(true);
    setHasSearched(false);
    setError(null);

    const debounceTimer = setTimeout(async () => {
      try {
        const data = await onSearch(query);
        setResults(data);
      } catch (err) {
        console.error("Dictionary lookup failed:", err);
        setResults([]);
        setError("Failed to query the database. Please check connection.");
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
    setHoveredLemma(null);
  };

  return (
    <section aria-labelledby="manual-add-heading" className="space-y-4">
      <div>
        <h3
          id="manual-add-heading"
          className="text-lg font-semibold text-slate-900 dark:text-slate-100"
        >
          Target Vocabulary Staging
        </h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Search lexical dictionary forms in Cyrillic or Latin script.
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
          placeholder="e.g., солдат, soldat, выучить, vyuchit'..."
          className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          autoComplete="off"
          spellCheck="false"
        />

        {isSearching && (
          <div className="absolute right-3 top-2.5 text-xs text-slate-400 animate-pulse">
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
          <div
            className="absolute z-10 mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800"
            onMouseLeave={() => setHoveredLemma(null)}
          >
            {results.length > 0 ? (
              <ul
                id="search-results-listbox"
                role="listbox"
                className="divide-y divide-slate-100 dark:divide-slate-700/60"
              >
                {results.map((lemma) => {
                  const displayText = lemma.lem_canon ?? lemma.lem_text ?? "—";

                  // Extract existing ROMANIZATION record from the eager-loaded database array
                  const romanization = lemma.pronunciations?.find(
                    (p) => p.pron_type?.toUpperCase() === "ROMANIZATION",
                  )?.pron_text;

                  // Fallback to IPA if romanization record is absent
                  const ipa = lemma.pronunciations?.find(
                    (p) => p.pron_type?.toUpperCase() === "IPA",
                  )?.pron_text;

                  const phoneticGuide = romanization || ipa;

                  // Concatenate definitions into a single line
                  const definitionsSummary = (lemma.definitions || [])
                    .map((d) => d.def_text.trim())
                    .filter(Boolean)
                    .join("; ");

                  return (
                    <li
                      key={lemma.id}
                      role="option"
                      aria-selected="false"
                      onMouseEnter={() => setHoveredLemma(lemma)}
                    >
                      <button
                        type="button"
                        onClick={() => handleSelection(lemma)}
                        className="group flex w-full flex-col px-4 py-2 text-left hover:bg-slate-50 focus:bg-slate-50 focus:outline-none dark:hover:bg-slate-700/50 dark:focus:bg-slate-700/50 transition-colors"
                      >
                        {/* Primary Identity Row */}
                        <div className="flex w-full items-center justify-between">
                          <div className="flex items-baseline gap-2 overflow-hidden">
                            <span className="font-semibold text-slate-900 dark:text-slate-100 text-sm">
                              {displayText}
                            </span>
                            {phoneticGuide && (
                              <span className="font-mono text-xs text-slate-400 dark:text-slate-500">
                                [{phoneticGuide}]
                              </span>
                            )}
                          </div>
                          <span className="shrink-0 rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:bg-slate-700 dark:text-slate-300">
                            {lemma.pos}
                          </span>
                        </div>

                        {/* Secondary Semantic Row with Gradient Fade Mask */}
                        {definitionsSummary && (
                          <div className="relative mt-0.5 w-full overflow-hidden whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                            <span>{definitionsSummary}</span>
                            {/* Gradient Fade: Matches container background on hover */}
                            <div className="pointer-events-none absolute right-0 top-0 h-full w-12 bg-gradient-to-l from-white group-hover:from-slate-50 dark:from-slate-800 dark:group-hover:from-slate-700/50 to-transparent transition-colors" />
                          </div>
                        )}
                      </button>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <div className="px-4 py-3 text-xs text-slate-500 text-center">
                No matches found for "{query}".
              </div>
            )}
          </div>
        )}

        {/* Coordinated Hover Inspector Window */}
        {hoveredLemma && (
          <aside
            aria-label="Lemma Inspector"
            className="hidden lg:block absolute left-[calc(100%+0.75rem)] top-1 z-20 w-80 rounded-xl border border-slate-200 bg-white p-4 shadow-xl dark:border-slate-700 dark:bg-slate-800 animate-in fade-in zoom-in-95 duration-150 pointer-events-none"
          >
            {/* Header: Canonical Form & Part of Speech */}
            <div className="flex items-start justify-between border-b border-slate-100 pb-2.5 dark:border-slate-700">
              <div>
                <h4 className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-tight">
                  {hoveredLemma.lem_canon || hoveredLemma.lem_text}
                </h4>
                {hoveredLemma.lem_canon &&
                  hoveredLemma.lem_text !== hoveredLemma.lem_canon && (
                    <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
                      Plain: {hoveredLemma.lem_text}
                    </span>
                  )}
              </div>
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                {hoveredLemma.pos}
              </span>
            </div>

            {/* Metadata Badges (Pronunciations, Gender, Aspect) */}
            <div className="mt-2.5 flex flex-wrap gap-1.5 text-xs">
              {hoveredLemma.pronunciations?.map((p) => (
                <span
                  key={p.id}
                  className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[11px] font-mono text-slate-700 dark:bg-slate-700 dark:text-slate-300"
                >
                  <span className="text-[9px] uppercase font-bold text-slate-400">
                    {p.pron_type}:
                  </span>
                  {p.pron_text}
                </span>
              ))}

              {hoveredLemma.noun_gender && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                  Gender: {hoveredLemma.noun_gender}
                </span>
              )}
              {hoveredLemma.verb_aspect && (
                <span className="rounded bg-slate-100 px-2 py-0.5 text-[11px] text-slate-600 dark:bg-slate-700 dark:text-slate-300">
                  Aspect: {hoveredLemma.verb_aspect}
                </span>
              )}
            </div>

            {/* Full Definitions List */}
            <div className="mt-3 space-y-1.5 border-t border-slate-100 pt-2.5 dark:border-slate-700">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Definitions ({hoveredLemma.definitions?.length || 0})
              </span>
              {hoveredLemma.definitions &&
              hoveredLemma.definitions.length > 0 ? (
                <ol className="list-decimal list-inside space-y-1 text-xs text-slate-700 dark:text-slate-200 leading-snug">
                  {hoveredLemma.definitions.map((d, index) => (
                    <li key={d.id || index} className="pl-1">
                      <span className="text-slate-800 dark:text-slate-100">
                        {d.def_text}
                      </span>
                    </li>
                  ))}
                </ol>
              ) : (
                <p className="text-xs text-slate-400 italic">
                  No definitions recorded.
                </p>
              )}
            </div>
          </aside>
        )}
      </div>
    </section>
  );
};
