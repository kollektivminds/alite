// src/components/modals/Tooltip.tsx
import React, { useState } from "react";

interface TooltipProps {
  title?: string;
  content: React.ReactNode; // Allows rich JSX layouts like TranslitGuidePopover
  children?: React.ReactNode;
}

export const Tooltip: React.FC<TooltipProps> = ({
  title,
  content,
  children,
}) => {
  const [isVisible, setIsVisible] = useState(false);

  return (
    <div
      className="relative inline-flex items-center"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
    >
      {/* Anchor Trigger: Uses children if provided, otherwise defaults to accessible info badge */}
      {children ? (
        children
      ) : (
        <button
          type="button"
          aria-label={title || "Information Guide"}
          className="inline-flex h-4 w-4 items-center justify-center rounded-full border border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-800 text-[10px] font-bold text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors focus:outline-none focus:ring-1 focus:ring-blue-500"
        >
          ?
        </button>
      )}

      {/* Popover Flyout */}
      {isVisible && (
        <div
          role="tooltip"
          className="absolute left-1/2 bottom-full mb-2 -translate-x-1/2 z-50 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-2.5 shadow-xl animate-in fade-in zoom-in-95 duration-100"
        >
          {content}
          {/* Arrow Pointer */}
          <div className="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-white dark:border-t-slate-800" />
        </div>
      )}
    </div>
  );
};
