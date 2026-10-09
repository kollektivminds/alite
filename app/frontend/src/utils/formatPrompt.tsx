/**
 * src/utils/formatPrompt.tsx
 *
 * Lightweight string parser that converts ALITE instructional prompt conventions
 * (newlines and **highlighted target words**) into accessible React JSX nodes.
 */

import React from "react";

export function renderFormattedPrompt(promptText: string): React.ReactNode {
  if (!promptText) return null;

  // Split text into paragraphs based on newline boundaries
  const lines = promptText.split("\n\n");

  return (
    <div className="flex flex-col gap-2">
      {lines.map((line, lineIdx) => {
        // Parse **target_word** bold boundaries within each line
        const parts = line.split(/(\*\*[^*]+\*\*)/g);

        return (
          <p key={lineIdx} className="leading-relaxed">
            {parts.map((part, partIdx) => {
              if (part.startsWith("**") && part.endsWith("**")) {
                const innerWord = part.slice(2, -2);
                return (
                  <span
                    key={partIdx}
                    className="font-bold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded-md border border-indigo-200/60"
                  >
                    {innerWord}
                  </span>
                );
              }
              return part;
            })}
          </p>
        );
      })}
    </div>
  );
}
