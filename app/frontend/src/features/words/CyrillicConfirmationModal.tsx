// src/features/words/CyrillicConfirmationModal.tsx
import React, { useEffect, useState } from "react";

interface CyrillicConfirmationModalProps {
  isOpen: boolean;
  originalInput: string;
  suggestedCyrillic: string;
  onConfirm: (confirmedCyrillic: string) => void;
  onCancel: () => void;
}

export const CyrillicConfirmationModal: React.FC<
  CyrillicConfirmationModalProps
> = ({ isOpen, originalInput, suggestedCyrillic, onConfirm, onCancel }) => {
  const [editableCyrillic, setEditableCyrillic] = useState(suggestedCyrillic);

  // Sync suggestion when the modal opens with a new query
  useEffect(() => {
    setEditableCyrillic(suggestedCyrillic);
  }, [suggestedCyrillic, isOpen]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-800">
        <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
          Confirm Cyrillic Spelling
        </h3>
        <p className="mt-2 text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
          You searched using Latin characters (
          <strong className="font-mono text-slate-800 dark:text-slate-200">
            {originalInput}
          </strong>
          ). Please verify the Russian Cyrillic spelling before initiating
          external dictionary extraction.
        </p>

        <div className="mt-4">
          <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
            Target Cyrillic Lemma
          </label>
          <input
            type="text"
            value={editableCyrillic}
            onChange={(e) => setEditableCyrillic(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-900 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100"
            autoFocus
          />
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!editableCyrillic.trim()}
            onClick={() => onConfirm(editableCyrillic.trim())}
            className="rounded-md bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white shadow hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            Confirm & Search Web
          </button>
        </div>
      </div>
    </div>
  );
};
