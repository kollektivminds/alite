// src/components/ui/Tooltip.tsx
import React, { useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";

interface TooltipProps {
  content: React.ReactNode;
  children?: React.ReactNode;
  title?: string;
  position?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  children,
  title,
  position = "top",
  className = "",
}) => {
  const [isVisible, setIsVisible] = useState<boolean>(false);
  const [coords, setCoords] = useState<{ top: number; left: number }>({
    top: 0,
    left: 0,
  });
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const tooltipId = useId();

  // 1. Calculate real-time viewport positioning on display to avoid overflow truncation
  const updateCoordinates = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    const scrollX = window.scrollX || document.documentElement.scrollLeft;
    const scrollY = window.scrollY || document.documentElement.scrollTop;

    let top = 0;
    let left = 0;
    const offset = 8; // Pixel separation between trigger and tooltip bubble

    switch (position) {
      case "bottom":
        top = rect.bottom + scrollY + offset;
        left = rect.left + scrollX + rect.width / 2;
        break;
      case "left":
        top = rect.top + scrollY + rect.height / 2;
        left = rect.left + scrollX - offset;
        break;
      case "right":
        top = rect.top + scrollY + rect.height / 2;
        left = rect.right + scrollX + offset;
        break;
      case "top":
      default:
        top = rect.top + scrollY - offset;
        left = rect.left + scrollX + rect.width / 2;
        break;
    }

    setCoords({ top, left });
  };

  const handleShow = () => {
    updateCoordinates();
    setIsVisible(true);
  };

  const handleHide = () => {
    setIsVisible(false);
  };

  // 2. Keyboard dismissal: Ensure escape key clears visual obstruction per WCAG 2.2
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isVisible) {
        setIsVisible(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isVisible]);

  // Recalculate if user scrolls or resizes while tooltip is open
  useEffect(() => {
    if (!isVisible) return;
    window.addEventListener("scroll", updateCoordinates, true);
    window.addEventListener("resize", updateCoordinates);
    return () => {
      window.removeEventListener("scroll", updateCoordinates, true);
      window.removeEventListener("resize", updateCoordinates);
    };
  }, [isVisible, position]);

  return (
    <span className={`inline-flex items-center ${className}`}>
      {/* Interactive Trigger Button: Focusable via Tab, hoverable via Mouse */}
      <button
        ref={triggerRef}
        type="button"
        onMouseEnter={handleShow}
        onMouseLeave={handleHide}
        onFocus={handleShow}
        onBlur={handleHide}
        aria-describedby={isVisible ? tooltipId : undefined}
        className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors focus:outline-none focus:ring-1 focus:ring-blue-500 rounded-full inline-flex items-center justify-center"
      >
        {children || (
          // Default: Subtle, standard educational informational glyph
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <circle cx="12" cy="12" r="10" />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 16v-4m0-4h.01"
            />
          </svg>
        )}
      </button>

      {/* 3. Render directly into document.body to bypass overflow-y-auto clipping */}
      {isVisible &&
        createPortal(
          <div
            id={tooltipId}
            role="tooltip"
            style={{
              position: "absolute",
              top: `${coords.top}px`,
              left: `${coords.left}px`,
              transform:
                position === "top"
                  ? "translate(-50%, -100%)"
                  : position === "bottom"
                    ? "translate(-50%, 0)"
                    : position === "left"
                      ? "translate(-100%, -50%)"
                      : "translate(0, -50%)",
            }}
            className="z-50 w-72 rounded-lg bg-slate-900 px-3.5 py-2.5 text-xs text-slate-100 shadow-xl border border-slate-700/80 animate-in fade-in zoom-in-95 duration-150 pointer-events-none"
          >
            {title && (
              <strong className="block pb-1 text-blue-300 font-semibold border-b border-slate-800 mb-1.5">
                {title}
              </strong>
            )}
            <div className="leading-relaxed text-slate-200">{content}</div>
          </div>,
          document.body,
        )}
    </span>
  );
};
