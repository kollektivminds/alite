/**
 * src/features/exercises/UnscrambleDisplay.tsx
 *
 * Interactive word-reordering display component.
 * Allows students to reconstruct the canonical sentence sequence
 * by moving word chips between a source bank and a target construction rail.
 */

import React, { useEffect, useState } from "react";
import {
  AttemptRecord,
  UnscrambleResponseItem,
  UnscrambleToken,
} from "../../types/exercise";

interface UnscrambleDisplayProps {
  item: UnscrambleResponseItem;
  attemptsRecord: AttemptRecord;
  onEvaluate: (serializedResponse: string) => void;
  isResolved: boolean;
}

export const UnscrambleDisplay: React.FC<UnscrambleDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  // 1. Local state separating unplaced word tokens from assembled tokens
  const [bankTokens, setBankTokens] = useState<UnscrambleToken[]>(
    item.shuffled_tokens,
  );
  const [placedTokens, setPlacedTokens] = useState<UnscrambleToken[]>([]);

  // 2. Reset component state whenever transitioning to a new item
  useEffect(() => {
    setBankTokens(item.shuffled_tokens);
    setPlacedTokens([]);
  }, [item.item_id, item.shuffled_tokens]);

  // 3. Move token from Available Bank -> Construction Rail
  const handleSelectToken = (token: UnscrambleToken) => {
    if (isResolved) return;
    setBankTokens((prev) =>
      prev.filter((t) => t.token_handle !== token.token_handle),
    );
    setPlacedTokens((prev) => [...prev, token]);
  };

  // 4. Move token from Construction Rail -> Available Bank
  const handleReturnToken = (token: UnscrambleToken) => {
    if (isResolved) return;
    setPlacedTokens((prev) =>
      prev.filter((t) => t.token_handle !== token.token_handle),
    );
    setBankTokens((prev) => [...prev, token]);
  };

  // 5. Reset all tokens back to the initial scrambled state
  const handleReset = () => {
    if (isResolved) return;
    setBankTokens(item.shuffled_tokens);
    setPlacedTokens([]);
  };

  // 6. Formulate serialized answer string and dispatch to container
  const handleSubmit = () => {
    if (placedTokens.length === 0 || isResolved) return;

    // Serialize as reconstructed sentence text to match backend grading
    const reconstructedSentence = placedTokens.map((t) => t.text).join(" ");
    onEvaluate(reconstructedSentence);
  };

  // 7. Dynamic status styling for the target assembly line
  const getRailBorderClass = () => {
    if (isResolved && attemptsRecord.isCorrect) {
      return "border-emerald-500 bg-emerald-50/50";
    }
    if (isResolved && !attemptsRecord.isCorrect) {
      return "border-red-400 bg-red-50/40";
    }
    return "border-slate-300 bg-slate-50/60";
  };

  return (
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Prompt Instruction Area */}
      <div className="mb-8 px-4 text-center max-w-2xl">
        <span className="text-xs font-bold tracking-widest text-indigo-600 uppercase">
          Порядок слов
        </span>
        <h2 className="text-2xl md:text-3xl font-medium text-slate-900 mt-2 leading-relaxed tracking-tight">
          {item.prompt}
        </h2>
      </div>

      <div className="w-full max-w-3xl flex flex-col gap-6">
        {/* Construction Rail (Active Sentence Line) */}
        <div
          className={`min-h-[80px] p-4 rounded-xl border-2 border-dashed transition-colors flex flex-wrap gap-2.5 items-center justify-center ${getRailBorderClass()}`}
        >
          {placedTokens.length === 0 ? (
            <span className="text-sm font-medium text-slate-400 select-none">
              Нажимайте на слова внизу, чтобы составить предложение...
            </span>
          ) : (
            placedTokens.map((tok) => (
              <button
                key={tok.token_handle}
                type="button"
                onClick={() => handleReturnToken(tok)}
                disabled={isResolved}
                className={`
                  px-4 py-2 text-base font-medium rounded-lg shadow-xs transition-all duration-150
                  ${
                    isResolved && attemptsRecord.isCorrect
                      ? "bg-emerald-600 text-white cursor-default"
                      : isResolved && !attemptsRecord.isCorrect
                        ? "bg-red-600 text-white cursor-default"
                        : "bg-blue-600 text-white hover:bg-blue-700 active:scale-95"
                  }
                `}
              >
                {tok.text}
              </button>
            ))
          )}
        </div>

        {/* Word Token Bank (Remaining Scrambled Words) */}
        <div className="min-h-[64px] flex flex-wrap justify-center gap-2.5 p-4 rounded-xl bg-white border border-slate-200">
          {bankTokens.length === 0 && !isResolved ? (
            <span className="text-xs text-slate-400 italic py-2">
              Все слова размещены. Нажмите «Проверить», чтобы отправить ответ.
            </span>
          ) : (
            bankTokens.map((tok) => (
              <button
                key={tok.token_handle}
                type="button"
                onClick={() => handleSelectToken(tok)}
                disabled={isResolved}
                className="px-4 py-2 text-base font-medium bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg border border-slate-300 shadow-2xs transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {tok.text}
              </button>
            ))
          )}
        </div>

        {/* Action Controls & Feedback Area */}
        <div className="flex flex-col items-center justify-center gap-4 mt-2">
          {isResolved && attemptsRecord.revealedAnswer && (
            <div className="text-red-600 font-medium text-center">
              Правильный порядок:{" "}
              <span className="font-bold">{attemptsRecord.revealedAnswer}</span>
            </div>
          )}

          {!isResolved ? (
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleReset}
                disabled={placedTokens.length === 0}
                className="px-5 py-2.5 text-sm font-semibold text-slate-600 hover:text-slate-800 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                Сбросить
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={bankTokens.length > 0}
                className="px-8 py-3 rounded-xl font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                Проверить
              </button>
            </div>
          ) : (
            <div className="text-slate-500 italic text-sm">
              Задание завершено.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
