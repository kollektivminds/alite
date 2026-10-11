// src/features/words/EditAddWordsModal.tsx
import React, { useEffect, useMemo, useState } from "react";
import { isLatin, latinToCyrillic } from "./Translit";

interface ParsedWordToken {
  original: string;
  cyrillic: string;
  wasConverted: boolean;
}

interface EditAddWordsModalProps {
  isOpen: boolean;
  initialQuery: string;
  isSubmitting: boolean;
  onConfirm: (tokens: string[]) => void;
  onCancel: () => void;
}

export const EditAddWordsModal: React.FC<EditAddWordsModalProps> = ({
  isOpen,
  initialQuery,
  isSubmitting,
  onConfirm,
  onCancel,
}) => {
  const [rawText, setRawText] = useState<string>("");

  // Sync state whenever modal is opened with a new search term
  useEffect(() => {
    if (isOpen) {
      setRawText(initialQuery);
    }
  }, [isOpen, initialQuery]);

  // Parse comma-, newline-, or space-separated tokens into clean Cyrillic words
  const parsedTokens = useMemo<ParsedWordToken[]>(() => {
    const rawTokens = rawText.split(/[,;\n\s]+/);
    const seen = new Set<string>();
    const tokens: ParsedWordToken[] = [];

    for (const raw of rawTokens) {
      const trimmed = raw.trim();
      if (!trimmed) continue;

      // Real-time orthographic projection
      const converted = isLatin(trimmed) ? latinToCyrillic(trimmed) : trimmed;
      const lowerKey = converted.toLowerCase();

      if (!seen.has(lowerKey)) {
        seen.add(lowerKey);
        tokens.push({
          original: trimmed,
          cyrillic: converted,
          wasConverted: isLatin(trimmed),
        });
      }
    }
    return tokens;
  }, [rawText]);

  if (!isOpen) return null;

  const handleRemoveToken = (indexToRemove: number) => {
    const updated = parsedTokens
      .filter((_, idx) => idx !== indexToRemove)
      .map((t) => t.cyrillic)
      .join(", ");
    setRawText(updated);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const finalTokens = parsedTokens.map((t) => t.cyrillic);
    if (finalTokens.length > 0) {
      onConfirm(finalTokens);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-150"
      role="dialog"
      aria-modal="true"
      aria-labelledby="batch-modal-title"
    >
      <div className="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-800">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-700">
          <h3
            id="batch-modal-title"
            className="text-base font-bold text-slate-900 dark:text-slate-100"
          >
            Edit & Batch Add Vocabulary
          </h3>
          <span className="text-xs font-mono text-slate-400">
            {parsedTokens.length} word{parsedTokens.length !== 1 ? "s" : ""}{" "}
            selected
          </span>
        </div>

        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          Review the Russian spelling or add multiple words separated by commas
          or newlines. Latin input is converted to Cyrillic automatically.
        </p>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
              Words to Fetch
            </label>
            <textarea
              rows={4}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="e.g. банан, vyuchit, собака, chitat"
              className="w-full rounded-lg border border-slate-300 p-3 text-sm font-mono text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
              autoFocus
            />
          </div>

          {/* Real-time Parsed Word Chips */}
          {parsedTokens.length > 0 && (
            <div>
              <span className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1.5">
                Queued Tokens Preview:
              </span>
              <div className="flex flex-wrap gap-1.5 max-h-32 overflow-y-auto p-1.5 rounded-lg border border-slate-100 bg-slate-50 dark:border-slate-700 dark:bg-slate-900/50">
                {parsedTokens.map((t, idx) => (
                  <span
                    key={`${t.cyrillic}-${idx}`}
                    className="inline-flex items-center gap-1.5 rounded-md bg-white px-2 py-1 text-xs font-medium text-slate-800 shadow-sm border border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <span>{t.cyrillic}</span>
                    {t.wasConverted && (
                      <span className="text-[10px] text-slate-400 font-mono">
                        ({t.original})
                      </span>
                    )}
                    <button
                      type="button"
                      onClick={() => handleRemoveToken(idx)}
                      className="text-slate-400 hover:text-red-500 transition-colors focus:outline-none"
                      title="Remove token"
                    >
                      ✕
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-700">
            <button
              type="button"
              disabled={isSubmitting}
              onClick={onCancel}
              className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={parsedTokens.length === 0 || isSubmitting}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? (
                <>
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>Queueing...</span>
                </>
              ) : (
                <span>
                  Queue {parsedTokens.length} Word
                  {parsedTokens.length !== 1 ? "s" : ""}
                </span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
