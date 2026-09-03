import React from "react";
import { DistractorStrategy, ItemFormat, QualityConfig } from "../../types";

interface QualitiesProps {
  config: QualityConfig;
  lemmaCount: number;
  onChange: (updated: Partial<QualityConfig>) => void;
  onSubmit: () => void;
}

export const QualitiesConfigPanel: React.FC<QualitiesProps> = ({
  config,
  lemmaCount,
  onChange,
  onSubmit,
}) => {
  return (
    <div className="qualities-menu">
      {/* 1. Item Format Selection */}
      <div className="form-group">
        <label htmlFor="item-format">Item Format</label>
        <select
          id="item-format"
          value={config.itemFormat}
          onChange={(e) =>
            onChange({ itemFormat: e.target.value as ItemFormat })
          }
        >
          <option value="MULTIPLE_CHOICE">Multiple Choice Question</option>
          <option value="FILL_IN_BLANK">Fill-in-the-Blank (Cloze)</option>
          <option value="MATCHING">Form-to-Lemma Matching</option>
          <option value="C_TEST">C-Test / Partial Deletion</option>
        </select>
      </div>

      {/* 2. Generation Strategy Selection */}
      <div className="form-group">
        <label htmlFor="strategy">Distractor Strategy</label>
        <select
          id="strategy"
          value={config.strategy}
          onChange={(e) =>
            onChange({ strategy: e.target.value as DistractorStrategy })
          }
        >
          <option value="MORPHOLOGICAL_PARITY">
            Morphological Parity (Target inflection matching)
          </option>
          <option value="FREQUENCY_NEIGHBOR">Frequency Tier Cohort</option>
          <option value="RANDOM">Random Lexical Sample</option>
        </select>
      </div>

      {/* 3. Dynamic Strategy Submenu Options */}
      <div className="strategy-submenu">
        <h4>Strategy Parameters</h4>
        {config.itemFormat === "MULTIPLE_CHOICE" && (
          <div className="form-group">
            <label htmlFor="distractor-count">Number of Distractors:</label>
            <input
              id="distractor-count"
              type="number"
              min={2}
              max={5}
              value={config.distractorCount}
              onChange={(e) =>
                onChange({ distractorCount: Number(e.target.value) })
              }
            />
          </div>
        )}

        {config.strategy === "MORPHOLOGICAL_PARITY" && (
          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                checked={config.targetInflectionsOnly}
                onChange={(e) =>
                  onChange({ targetInflectionsOnly: e.target.checked })
                }
              />
              Strict grammatical feature matching (Case/Number/Aspect)
            </label>
          </div>
        )}
      </div>

      {/* Generation CTA with reactive guard */}
      <button
        type="button"
        className="generate-button"
        disabled={lemmaCount === 0}
        onClick={onSubmit}
      >
        Generate Items for {lemmaCount} {lemmaCount === 1 ? "Lemma" : "Lemmas"}
      </button>
    </div>
  );
};
