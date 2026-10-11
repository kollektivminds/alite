// src/features/words/SingleWordAdder.tsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Lemma } from "../../types/words";
import { EditAddWordsModal } from "./EditAddWordsModal";
import { isLatin, latinToCyrillic } from "./Translit";

export interface PipelineItemOutcome {
  token: string;
  status: "queued" | "already_exists" | "in_progress" | "rate_limited";
  message: string;
}

export interface PipelineResponse {
  results: PipelineItemOutcome[];
  total_requested: number;
  total_queued: number;
  remaining_attempts: number;
  reset_seconds: number;
  message?: string;
}

interface SingleWordAdderProps {
  onSearch: (query: string) => Promise<Lemma[]>;
  onSelectLemma: (lemma: Lemma) => void;
  onRequestPipeline?: (tokens: string[]) => Promise<PipelineResponse>;
}

export const SingleWordAdder: React.FC<SingleWordAdderProps> = ({
  onSearch,
  onSelectLemma,
  onRequestPipeline,
}) => {
  const { t } = useTranslation();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Lemma[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hoveredLemma, setHoveredLemma] = useState<Lemma | null>(null);

  // Pipeline execution & modal state
  const [isPipelineRequesting, setIsPipelineRequesting] =
    useState<boolean>(false);
  const [pipelineFeedback, setPipelineFeedback] = useState<{
    msg: string;
    isError: boolean;
  } | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Stabilize onSearch across renders to prevent timer invalidation
  const onSearchRef = useRef(onSearch);
  useEffect(() => {
    onSearchRef.current = onSearch;
  }, [onSearch]);

  // Compute live Cyrillic equivalent for immediate rendering
  const cyrillicConversion = useMemo(() => {
    const trimmed = query.trim();
    if (!trimmed) return "";
    return isLatin(trimmed) ? latinToCyrillic(trimmed) : trimmed;
  }, [query]);

  // Debounced search on input change
  useEffect(() => {
    setPipelineFeedback(null);
    const trimmed = query.trim();

    if (trimmed.length < 2) {
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
        const data = await onSearchRef.current(trimmed);
        setResults(data);
      } catch (err: unknown) {
        console.error("Dictionary lookup error:", err);
        setResults([]);
        setError("Failed to query the database. Check server connection.");
      } finally {
        setIsSearching(false);
        setHasSearched(true);
      }
    }, 250);

    return () => clearTimeout(debounceTimer);
  }, [query]);

  // Check if an exact match exists locally in Cyrillic or Latin
  const exactMatchExists = useMemo(() => {
    const cleanLower = query.trim().toLowerCase();
    const cyrillicLower = cyrillicConversion.toLowerCase();

    return results.some((item) => {
      const textMatch = item.lem_text.toLowerCase();
      const canonMatch = item.lem_canon ? item.lem_canon.toLowerCase() : "";
      return (
        textMatch === cleanLower ||
        textMatch === cyrillicLower ||
        canonMatch === cleanLower ||
        canonMatch === cyrillicLower
      );
    });
  }, [query, cyrillicConversion, results]);

  const handleSelection = (lemma: Lemma) => {
    onSelectLemma(lemma);
    setQuery("");
    setResults([]);
    setHasSearched(false);
    setHoveredLemma(null);
  };

  // Dispatch single or batch requests to the parent pipeline handler
  const executePipelineDispatch = async (tokensToFetch: string[]) => {
    if (!onRequestPipeline || tokensToFetch.length === 0) return;

    setIsPipelineRequesting(true);
    setPipelineFeedback(null);

    try {
      const response = await onRequestPipeline(tokensToFetch);
      const isSuccess = response.total_queued > 0;

      setPipelineFeedback({
        msg: response.message || `Queued ${response.total_queued} item(s).`,
        isError: !isSuccess,
      });

      // Clear input and modal on success
      setIsModalOpen(false);
      setQuery("");
      setResults([]);
      setHasSearched(false);
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        err.message ||
        "Failed to dispatch pipeline lookup.";
      setPipelineFeedback({ msg: detail, isError: true });
    } finally {
      setIsPipelineRequesting(false);
    }
  };

  return (
    <section aria-labelledby="manual-add-heading" className="space-y-4">
      <div>
        <h3
          id="manual-add-heading"
          className="text-lg font-semibold text-slate-900 dark:text-slate-100"
        >
          {t("exercises.wordsMenu.targetVocabStaging")}
        </h3>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          {t("exercises.wordsMenu.vocabStagingInstructions")}
        </p>
      </div>

      <div className="relative w-full max-w-md">
        <label htmlFor="lemma-search" className="sr-only">
          {t("exercises.wordsMenu.searchDictForm")}
        </label>

        <input
          id="lemma-search"
          type="text"
          role="combobox"
          aria-expanded={results.length > 0 || (hasSearched && !isSearching)}
          aria-controls="search-results-listbox"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={`${t("exercises.wordsMenu.eg")} солдат, soldat, выучить, vyuchit'`}
          className="w-full rounded-md border border-slate-300 px-4 py-2 text-sm shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
          autoComplete="off"
          spellCheck="false"
        />

        {isSearching && (
          <div className="absolute right-3 top-2.5 text-xs text-slate-400 animate-pulse">
            {t("exercises.searching")}...
          </div>
        )}

        {error && (
          <div className="mt-2 rounded-md bg-red-50 p-2 text-xs text-red-600 dark:bg-red-900/30 dark:text-red-400">
            {error}
          </div>
        )}

        {/* Dropdown Menu */}
        {!error && (results.length > 0 || (hasSearched && !isSearching)) && (
          <div
            className="absolute z-20 mt-1 max-h-72 w-full overflow-y-auto rounded-md border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-800"
            onMouseLeave={() => setHoveredLemma(null)}
          >
            <ul
              id="search-results-listbox"
              role="listbox"
              className="divide-y divide-slate-100 dark:divide-slate-700/60"
            >
              {/* Existing Lemma Rows */}
              {results.map((lemma) => {
                const displayText = lemma.lem_canon ?? lemma.lem_text ?? "—";
                const romanization = lemma.pronunciations?.find(
                  (p) => p.pron_type?.toUpperCase() === "ROMANIZATION",
                )?.pron_text;
                const ipa = lemma.pronunciations?.find(
                  (p) => p.pron_type?.toUpperCase() === "IPA",
                )?.pron_text;
                const phoneticGuide = romanization || ipa;

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

                      {definitionsSummary && (
                        <div className="relative mt-0.5 w-full overflow-hidden whitespace-nowrap text-xs text-slate-500 dark:text-slate-400">
                          <span>{definitionsSummary}</span>
                          <div className="pointer-events-none absolute right-0 top-0 h-full w-12 bg-gradient-to-l from-white group-hover:from-slate-50 dark:from-slate-800 dark:group-hover:from-slate-700/50 to-transparent transition-colors" />
                        </div>
                      )}
                    </button>
                  </li>
                );
              })}

              {/* Bottom Pipeline Dispatch Row */}
              {!exactMatchExists &&
                hasSearched &&
                !isSearching &&
                onRequestPipeline && (
                  <li role="option" aria-selected="false">
                    <div className="flex items-center justify-between border-t border-dashed border-blue-200 dark:border-blue-800/80 bg-blue-50/40 dark:bg-blue-950/20 px-3 py-2.5">
                      {/* Left: Instant single-click submission */}
                      <button
                        type="button"
                        disabled={isPipelineRequesting}
                        onClick={() =>
                          executePipelineDispatch([cyrillicConversion])
                        }
                        className="flex flex-1 items-center gap-2 text-left hover:opacity-80 transition-opacity disabled:opacity-50"
                      >
                        <span className="text-blue-600 dark:text-blue-400 text-sm">
                          {isPipelineRequesting ? "⏳" : "🔍"}
                        </span>
                        <div className="flex flex-col">
                          <span className="text-xs font-semibold text-blue-700 dark:text-blue-300">
                            Search online dictionary for "{cyrillicConversion}"
                          </span>
                          {isLatin(query.trim()) && (
                            <span className="text-[10px] text-slate-400 font-mono">
                              auto-converted from "{query.trim()}"
                            </span>
                          )}
                        </div>
                      </button>

                      {/* Right: Open Edit / Batch modal */}
                      <button
                        type="button"
                        onClick={() => setIsModalOpen(true)}
                        className="ml-2 shrink-0 rounded border border-blue-300 bg-white px-2 py-1 text-[11px] font-semibold text-blue-700 shadow-sm hover:bg-blue-50 dark:border-blue-700 dark:bg-slate-800 dark:text-blue-300 dark:hover:bg-slate-700 transition-colors"
                        title="Edit spelling or add multiple words"
                      >
                        Edit / Add Multiple
                      </button>
                    </div>

                    {pipelineFeedback && (
                      <div
                        className={`px-3 py-1.5 text-[11px] font-medium ${
                          pipelineFeedback.isError
                            ? "bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-400"
                            : "bg-emerald-50 text-emerald-600 dark:bg-emerald-950/40 dark:text-emerald-400"
                        }`}
                      >
                        {pipelineFeedback.msg}
                      </div>
                    )}
                  </li>
                )}
            </ul>
          </div>
        )}

        {/* Hover Inspector Flyout */}
        {hoveredLemma && (
          <aside className="hidden lg:block absolute left-[calc(100%+0.75rem)] top-1 z-30 w-80 rounded-xl border border-slate-200 bg-white p-4 shadow-xl dark:border-slate-700 dark:bg-slate-800 animate-in fade-in zoom-in-95 duration-150 pointer-events-none">
            <div className="flex items-start justify-between border-b border-slate-100 pb-2.5 dark:border-slate-700">
              <div>
                <h4 className="text-xl font-bold text-slate-900 dark:text-slate-100 leading-tight">
                  {hoveredLemma.lem_canon || hoveredLemma.lem_text}
                </h4>
              </div>
              <span className="rounded bg-blue-50 px-2 py-0.5 text-xs font-bold uppercase tracking-wider text-blue-700 dark:bg-blue-950/60 dark:text-blue-300">
                {hoveredLemma.pos}
              </span>
            </div>

            <div className="mt-3 space-y-1.5 border-t border-slate-100 pt-2.5 dark:border-slate-700">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                Definitions
              </span>
              <ol className="list-decimal list-inside space-y-1 text-xs text-slate-700 dark:text-slate-200">
                {(hoveredLemma.definitions || []).map((d, i) => (
                  <li key={d.id || i}>
                    <span className="text-slate-800 dark:text-slate-100">
                      {d.def_text}
                    </span>
                  </li>
                ))}
              </ol>
            </div>
          </aside>
        )}
      </div>

      {/* Multi-Word Batch & Edit Modal */}
      <EditAddWordsModal
        isOpen={isModalOpen}
        initialQuery={query.trim()}
        isSubmitting={isPipelineRequesting}
        onConfirm={executePipelineDispatch}
        onCancel={() => setIsModalOpen(false)}
      />
    </section>
  );
};
