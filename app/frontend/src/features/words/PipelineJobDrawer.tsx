// src/features/words/PipelineJobDrawer.tsx
import React, { useState } from "react";

export interface TrackedPipelineJob {
  token: string;
  status: "queued" | "already_exists" | "in_progress" | "failed";
  message: string;
  timestamp: Date;
}

interface PipelineJobDrawerProps {
  jobs: TrackedPipelineJob[];
  onDismissJob?: (index: number) => void;
}

export const PipelineJobDrawer: React.FC<PipelineJobDrawerProps> = ({
  jobs,
  onDismissJob,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (jobs.length === 0) return null;

  return (
    <div className="fixed bottom-0 right-6 z-40 w-96 rounded-t-xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-800 transition-all">
      {/* Header bar / accordion toggle */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-2.5 bg-slate-50 hover:bg-slate-100 dark:bg-slate-800/80 dark:hover:bg-slate-700 rounded-t-xl border-b border-slate-200 dark:border-slate-700 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
          <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
            Pipeline Tasks ({jobs.length})
          </span>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          {isExpanded ? "▼ Hide" : "▲ Show"}
        </span>
      </button>

      {/* Expanded list view */}
      {isExpanded && (
        <div className="max-h-60 overflow-y-auto divide-y divide-slate-100 p-2 dark:divide-slate-700">
          {jobs.map((job, index) => (
            <div
              key={`${job.token}-${index}`}
              className="flex items-start justify-between p-2 text-xs"
            >
              <div>
                <span className="font-semibold text-slate-900 dark:text-slate-100">
                  {job.token}
                </span>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  {job.message}
                </p>
                <span className="text-[10px] text-slate-400">
                  {job.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                  job.status === "queued" || job.status === "in_progress"
                    ? "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300"
                    : job.status === "already_exists"
                      ? "bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300"
                      : "bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300"
                }`}
              >
                {job.status.replace("_", " ")}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
