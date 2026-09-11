// src/features/exercises/ProgressBar.tsx
import React from "react";

interface ProgressBarProps {
  currentIndex: number;
  totalItems: number;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  currentIndex,
  totalItems,
}) => {
  // Calculate percentage. Math.min/max ensures it stays safely bounded between 0 and 100.
  const progressPercentage = Math.max(
    0,
    Math.min(100, (currentIndex / totalItems) * 100),
  );

  return (
    <div className="w-full h-3 bg-slate-200 overflow-hidden">
      <div
        className="h-full bg-blue-500 transition-all duration-500 ease-in-out"
        // MUST use the style object for dynamic widths so Tailwind does not purge it
        style={{ width: `${progressPercentage}%` }}
      />
    </div>
  );
};
