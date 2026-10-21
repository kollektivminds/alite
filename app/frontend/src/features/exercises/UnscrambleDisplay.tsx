/**
 * src/features/exercises/UnscrambleDisplay.tsx
 *
 * Interactive word-reordering assessment component for ALITE.
 *
 * Features:
 * - Immediate formative feedback on intermediate failed attempts without answer leakage.
 * - Robust Russian typography engine (converts straight quotes to «ёлочки»,
 *   cleans escaped corpus artifacts, fixes attachment boundaries).
 * - Dual-layer feedback resolution (inspects onEvaluate return and attemptsRecord prop).
 * - Comprehensive Dark Mode styling aligned with ALITE's design system.
 */

import React, { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  AttemptRecord,
  UnscrambleResponseItem,
  UnscrambleToken,
} from "../../types/exercise";

// ============================================================================
// Russian Typographical Normalization Engine
// ============================================================================

/**
 * Normalizes quotation marks and punctuation spacing according to
 * standard Russian typography (кавычки-ёлочки: «...»).
 *
 * Rules handled:
 * 1. Strips corpus escaping artifacts (\").
 * 2. Normalizes comma/period placement outside quotes (слово," -> слово»,).
 * 3. Corrects inverted opening guillemets attached to prepositions (о»слово -> о «слово).
 * 4. Resolves quote pairs into opening « and closing » marks.
 * 5. Eliminates internal whitespace padding inside guillemets (« слово » -> «слово»).
 */
export const formatRussianTypography = (text: string): string => {
  if (!text) return "";

  let clean = text
    // 1. Strip raw backslash escapes from NLP/corpus serialization
    .replace(/\\"/g, '"')
    .replace(/\\'/g, "'");

  // 2. Fix corpus artifact where comma/period was inside or right before the quote
  clean = clean
    .replace(/([а-яА-ЯёЁa-zA-Z0-9]),"/g, '$1",')
    .replace(/([а-яА-ЯёЁa-zA-Z0-9])\."/g, '$1".');

  // 3. Fix inverted opening quote attached to prepositions: e.g. "о»европейском" -> "о «европейском"
  clean = clean.replace(
    /([а-яА-ЯёЁa-zA-Z0-9])»([а-яА-ЯёЁa-zA-Z0-9])/g,
    "$1 «$2",
  );
  clean = clean.replace(
    /([а-яА-ЯёЁa-zA-Z0-9])"([а-яА-ЯёЁa-zA-Z0-9])/g,
    "$1 «$2",
  );

  // 4. Fix space-shifted opening quote: e.g. 'своих" заблуждений"' -> 'своих «заблуждений»'
  clean = clean.replace(
    /([а-яА-ЯёЁa-zA-Z0-9])"\s+([а-яА-ЯёЁa-zA-Z0-9])/g,
    "$1 «$2",
  );

  // 5. Transform paired quotes across balanced segments
  clean = clean.replace(/"([^"]+)"/g, "«$1»");

  // 6. Contextual replacement for single tokens or remaining quotes:
  // Opening quote: at start of string or preceded by whitespace / brackets / dashes
  clean = clean.replace(/(^|[\s(\[{<—–-])"/g, "$1«");
  // Closing quote: preceded by word characters or sentence punctuation
  clean = clean.replace(/([^\s])"/g, "$1»");
  // Default fallback for any remaining straight quote
  clean = clean.replace(/"/g, "»");

  // 7. Fix inverted guillemets on single token chips (e.g. chip starting with closing guillemet)
  clean = clean.replace(/^»([а-яА-ЯёЁa-zA-Z0-9])/g, "«$1");
  clean = clean.replace(/([а-яА-ЯёЁa-zA-Z0-9])«([,.?!:;]*)$/g, "$1»$2");

  // 8. Eliminate extraneous whitespace directly inside guillemet boundaries
  clean = clean.replace(/«\s+/g, "«").replace(/\s+»/g, "»");

  return clean;
};

// ============================================================================
// Extended Component Interfaces
// ============================================================================

interface ExtendedAttemptRecord extends Partial<AttemptRecord> {
  isCorrect?: boolean;
  is_correct?: boolean;
  revealedAnswer?: string;
  correct_answer?: string;
  feedback?: string;
  feedbackMessage?: string;
  feedback_message?: string;
  banner?: string;
  bannerText?: string;
  banner_text?: string;
  message?: string;
  attemptCount?: number;
  attemptNum?: number;
  attempt_num?: number;
  attemptsCount?: number;
  attempts?: unknown[];
}

interface UnscrambleDisplayProps {
  item: UnscrambleResponseItem;
  attemptsRecord: ExtendedAttemptRecord;
  onEvaluate: (serializedResponse: string) => void | Promise<unknown>;
  isResolved: boolean;
}

// ============================================================================
// UnscrambleDisplay Component
// ============================================================================

export const UnscrambleDisplay: React.FC<UnscrambleDisplayProps> = ({
  item,
  attemptsRecord,
  onEvaluate,
  isResolved,
}) => {
  const { t } = useTranslation();

  // 1. Token banks (unplaced tokens vs assembled sentence tokens)
  const [bankTokens, setBankTokens] = useState<UnscrambleToken[]>([]);
  const [placedTokens, setPlacedTokens] = useState<UnscrambleToken[]>([]);

  // 2. Evaluation state tracking
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false);
  const [hasSubmittedAttempt, setHasSubmittedAttempt] =
    useState<boolean>(false);
  const [hasInteractedSinceSubmit, setHasInteractedSinceSubmit] =
    useState<boolean>(false);
  const [localFeedback, setLocalFeedback] = useState<string | null>(null);

  // 3. Reset state on item transition
  useEffect(() => {
    const sanitizedBank = (item.shuffled_tokens || []).map((tok) => ({
      ...tok,
      text: formatRussianTypography(tok.text),
    }));

    setBankTokens(sanitizedBank);
    setPlacedTokens([]);
    setLocalFeedback(null);
    setHasSubmittedAttempt(false);
    setHasInteractedSinceSubmit(false);
  }, [item.item_id, item.shuffled_tokens]);

  // 4. Resolve feedback message across local state and props
  const activeFeedback = useMemo(() => {
    return (
      localFeedback ||
      attemptsRecord?.feedback ||
      attemptsRecord?.feedbackMessage ||
      attemptsRecord?.feedback_message ||
      attemptsRecord?.banner ||
      attemptsRecord?.bannerText ||
      attemptsRecord?.banner_text ||
      attemptsRecord?.message ||
      null
    );
  }, [localFeedback, attemptsRecord]);

  // 5. Resolve attempt verdict defensively across camelCase and snake_case
  const isCorrect = useMemo(() => {
    return (
      attemptsRecord?.isCorrect === true || attemptsRecord?.is_correct === true
    );
  }, [attemptsRecord]);

  // 6. Resolve attempt counter defensively
  const attemptCount = useMemo(() => {
    return (
      attemptsRecord?.attemptCount ??
      attemptsRecord?.attemptNum ??
      attemptsRecord?.attempt_num ??
      attemptsRecord?.attemptsCount ??
      attemptsRecord?.attempts?.length ??
      (hasSubmittedAttempt ? 1 : 0)
    );
  }, [attemptsRecord, hasSubmittedAttempt]);

  // 7. Resolve canonical answer text for final attempt reveal
  const revealedAnswer = useMemo(() => {
    return (
      attemptsRecord?.revealedAnswer || attemptsRecord?.correct_answer || null
    );
  }, [attemptsRecord]);

  // 8. Identify whether the current state represents an intermediate incorrect attempt
  const isIntermediateFailure = useMemo(() => {
    if (isResolved || isCorrect) return false;
    return hasSubmittedAttempt || attemptCount > 0 || Boolean(activeFeedback);
  }, [
    isResolved,
    isCorrect,
    hasSubmittedAttempt,
    attemptCount,
    activeFeedback,
  ]);

  // 9. Interaction Handlers
  const handleSelectToken = (token: UnscrambleToken) => {
    if (isResolved) return;
    setHasInteractedSinceSubmit(true);
    setBankTokens((prev) =>
      prev.filter((t) => t.token_handle !== token.token_handle),
    );
    setPlacedTokens((prev) => [...prev, token]);
  };

  const handleReturnToken = (token: UnscrambleToken) => {
    if (isResolved) return;
    setHasInteractedSinceSubmit(true);
    setPlacedTokens((prev) =>
      prev.filter((t) => t.token_handle !== token.token_handle),
    );
    setBankTokens((prev) => [...prev, token]);
  };

  const handleReset = () => {
    if (isResolved) return;
    setHasInteractedSinceSubmit(true);
    const sanitizedBank = (item.shuffled_tokens || []).map((tok) => ({
      ...tok,
      text: formatRussianTypography(tok.text),
    }));
    setBankTokens(sanitizedBank);
    setPlacedTokens([]);
  };

  const handleSubmit = async () => {
    if (placedTokens.length === 0 || isResolved || isEvaluating) return;

    setHasSubmittedAttempt(true);
    setHasInteractedSinceSubmit(false);
    setIsEvaluating(true);

    const reconstructedSentence = placedTokens.map((t) => t.text).join(" ");

    try {
      // Capture response if onEvaluate returns a Promise from the parent runner
      const result = await Promise.resolve(onEvaluate(reconstructedSentence));
      if (result && typeof result === "object") {
        const res = result as Record<string, unknown>;
        const msg =
          res.feedback ||
          res.feedbackMessage ||
          res.feedback_message ||
          res.banner ||
          res.bannerText ||
          res.banner_text ||
          res.message;
        if (typeof msg === "string") {
          setLocalFeedback(msg);
        }
      }
    } catch (err) {
      console.error("Unscramble evaluation dispatch error:", err);
    } finally {
      setIsEvaluating(false);
    }
  };

  // 10. Rail styling reflecting pedagogical feedback state[cite: 26]
  const getRailBorderClass = () => {
    if (isResolved && isCorrect) {
      return "border-emerald-500 bg-emerald-50/50 dark:border-emerald-600 dark:bg-emerald-950/20";
    }
    if (isResolved && !isCorrect) {
      return "border-rose-500 bg-rose-50/50 dark:border-rose-700 dark:bg-rose-950/20";
    }
    // Intermediate failure: Amber warning state until the learner re-arranges chips
    if (isIntermediateFailure) {
      return hasInteractedSinceSubmit
        ? "border-blue-400 bg-blue-50/30 dark:border-blue-600 dark:bg-blue-950/20"
        : "border-amber-400 bg-amber-50/50 dark:border-amber-600 dark:bg-amber-950/30";
    }
    return "border-slate-300 bg-slate-50/60 dark:border-slate-700 dark:bg-slate-900/40";
  };

  return (
    <div className="flex flex-col w-full flex-grow justify-center items-center pb-16">
      {/* Prompt Area with Normalized Typography */}
      <div className="mb-6 px-4 text-center max-w-2xl">
        <span className="text-xs font-bold tracking-widest text-indigo-600 dark:text-indigo-400 uppercase">
          {t("exercises.settings.formats.unscramble") ||
            "Sentence Construction"}
        </span>
        <h2 className="text-xl md:text-2xl font-medium text-slate-900 dark:text-slate-100 mt-2 leading-relaxed tracking-tight">
          {formatRussianTypography(item.prompt)}
        </h2>
      </div>

      <div className="w-full max-w-3xl flex flex-col gap-5">
        {/* Construction Rail (Active Sentence Workspace)[cite: 26] */}
        <div
          className={`min-h-[88px] p-4 rounded-xl border-2 border-dashed transition-all duration-200 flex flex-wrap gap-2.5 items-center justify-center ${getRailBorderClass()}`}
        >
          {placedTokens.length === 0 ? (
            <span className="text-sm font-medium text-slate-400 dark:text-slate-500 select-none text-center">
              {t("exercises.unscramble.placeholder") ||
                "Click on the words below in order to assemble the sentence..."}
            </span>
          ) : (
            placedTokens.map((tok) => (
              <button
                key={tok.token_handle}
                type="button"
                onClick={() => handleReturnToken(tok)}
                disabled={isResolved}
                className={`
                  px-3.5 py-2 text-sm md:text-base font-medium rounded-lg shadow-xs transition-all duration-150 select-none
                  ${
                    isResolved && isCorrect
                      ? "bg-emerald-600 text-white cursor-default"
                      : isResolved && !isCorrect
                        ? "bg-rose-600 text-white cursor-default"
                        : isIntermediateFailure && !hasInteractedSinceSubmit
                          ? "bg-amber-600 hover:bg-amber-700 text-white active:scale-95"
                          : "bg-blue-600 hover:bg-blue-700 text-white active:scale-95"
                  }
                `}
                aria-label={`Remove ${tok.text} from sentence`}
              >
                {tok.text}
              </button>
            ))
          )}
        </div>

        {/* Word Token Bank (Unplaced Scrambled Chips)[cite: 26] */}
        <div className="min-h-[68px] flex flex-wrap justify-center gap-2.5 p-4 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-xs">
          {bankTokens.length === 0 && !isResolved ? (
            <span className="text-xs text-slate-400 dark:text-slate-500 italic py-2 select-none">
              {t("exercises.navigation.unscramble.allWordsChosen") ||
                "All words have been placed. Click 'Check' to verify."}
            </span>
          ) : (
            bankTokens.map((tok) => (
              <button
                key={tok.token_handle}
                type="button"
                onClick={() => handleSelectToken(tok)}
                disabled={isResolved}
                className="px-3.5 py-2 text-sm md:text-base font-medium bg-slate-100 hover:bg-slate-200 dark:bg-slate-700 dark:hover:bg-slate-600 text-slate-800 dark:text-slate-100 rounded-lg border border-slate-300 dark:border-slate-600 shadow-2xs transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed select-none"
                aria-label={`Add ${tok.text} to sentence`}
              >
                {tok.text}
              </button>
            ))
          )}
        </div>

        {/* ================================================================= */}
        {/* Formative Diagnostic Feedback Banners                             */}
        {/* ================================================================= */}

        {/* 1. Intermediate Failed Attempt Banner (Non-Final) */}
        {isIntermediateFailure && (
          <aside
            role="status"
            aria-live="polite"
            className="w-full p-3.5 rounded-xl border border-amber-300 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 text-sm shadow-xs flex items-center justify-between gap-3 animate-fade-in"
          >
            <div className="flex items-center gap-2.5">
              <span
                className="text-amber-600 dark:text-amber-400 font-bold text-base select-none"
                aria-hidden="true"
              >
                ⚠
              </span>
              <span className="leading-snug">
                {activeFeedback ||
                  t(
                    "exercises.unscramble.incorrectTryAgain",
                    "Not quite right. Check the word order and try rearranging the chips.",
                  )}
              </span>
            </div>

            {attemptCount > 0 && (
              <span className="text-xs font-semibold font-mono text-amber-700 dark:text-amber-300 bg-amber-100 dark:bg-amber-900/60 px-2 py-0.5 rounded-full shrink-0 select-none">
                {t("exercises.attempt", { count: attemptCount }) ||
                  `Attempt ${attemptCount}`}
              </span>
            )}
          </aside>
        )}

        {/* 2. Final Attempt Failed Resolution: Solution Reveal[cite: 26] */}
        {isResolved && !isCorrect && revealedAnswer && (
          <aside
            role="alert"
            aria-live="assertive"
            className="w-full p-4 rounded-xl border border-rose-300 bg-rose-50 dark:border-rose-900/60 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200 text-sm shadow-xs space-y-1.5"
          >
            <div className="flex items-center gap-2 font-bold text-rose-800 dark:text-rose-300">
              <span aria-hidden="true">✕</span>
              <span>
                {t("exercises.unscramble.incorrectFinal") || "Incorrect"}
              </span>
            </div>
            <p className="font-mono text-xs md:text-sm leading-relaxed text-slate-800 dark:text-slate-200">
              <strong className="text-rose-700 dark:text-rose-400 font-sans font-semibold">
                {t("exercises.settings.formats.canonicalAnswer") ||
                  "Correct sentence"}
                :{" "}
              </strong>
              {formatRussianTypography(revealedAnswer)}
            </p>
          </aside>
        )}

        {/* 3. Successful Resolution Banner */}
        {isResolved && isCorrect && (
          <aside
            role="status"
            aria-live="polite"
            className="w-full p-3.5 rounded-xl border border-emerald-300 bg-emerald-50 dark:border-emerald-900/60 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200 text-sm shadow-xs flex items-center gap-2"
          >
            <span
              className="text-emerald-600 dark:text-emerald-400 font-bold text-base select-none"
              aria-hidden="true"
            >
              ✓
            </span>
            <span className="font-medium">
              {activeFeedback ||
                t(
                  "exercises.unscramble.success",
                  "Correct! You assembled the sentence in the proper order.",
                )}
            </span>
          </aside>
        )}

        {/* Action Controls Area[cite: 26] */}
        <div className="flex flex-col items-center justify-center gap-4 mt-2">
          {!isResolved ? (
            <div className="flex items-center gap-4">
              <button
                type="button"
                onClick={handleReset}
                disabled={placedTokens.length === 0 || isEvaluating}
                className="px-5 py-2.5 text-sm font-semibold text-slate-600 hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                {t("exercises.navigation.reset") || "Reset"}
              </button>

              <button
                type="button"
                onClick={handleSubmit}
                disabled={bankTokens.length > 0 || isEvaluating}
                className="px-8 py-3 rounded-xl font-semibold bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors shadow-sm"
              >
                {isEvaluating
                  ? t("exercises.navigation.checking", "Checking...")
                  : t("exercises.navigation.check") || "Check"}
              </button>
            </div>
          ) : (
            <div className="text-slate-500 dark:text-slate-400 italic text-sm select-none">
              {t("exercises.navigation.exComplete") || "Item Completed"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
