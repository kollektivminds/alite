import React from "react";
import { Lemma } from "../../types";

interface PrunerProps {
  lessonLemmas: Lemma[];
  excludedIds: string[];
  onToggleExclude: (id: string) => void;
}

export const LessonWordPruner: React.FC<PrunerProps> = ({
  lessonLemmas,
  excludedIds,
  onToggleExclude,
}) => {
  const excludedSet = new Set(excludedIds);

  return (
    <div className="pruner-container">
      <h3>Refine Lesson List Words</h3>
      <p className="hint-text">
        Click a lemma to exclude/re-include it from generation.
      </p>
      <div className="chip-grid">
        {lessonLemmas.map((item) => {
          const isExcluded = excludedSet.has(item.id);
          return (
            <button
              key={item.id}
              type="button"
              className={`lemma-chip ${isExcluded ? "chip-excluded" : "chip-active"}`}
              onClick={() => onToggleExclude(item.id)}
            >
              <span>{item.lemma}</span>
              <small>({item.pos})</small>
              <span className="badge-status">
                {isExcluded ? "✕ Excluded" : "✓ Included"}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
};
