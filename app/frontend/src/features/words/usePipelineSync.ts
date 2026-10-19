// src/features/words/hooks/usePipelineSync.ts
import axios from "axios";
import { useEffect, useRef } from "react";
import { TrackedPipelineJob } from "./pipelineJobDrawer";

interface UsePipelineSyncProps {
  jobs: TrackedPipelineJob[];
  onJobStatusChange: (updatedJobs: TrackedPipelineJob[]) => void;
  onLemmaIngested: (lemmaId: number) => void;
}

export const usePipelineSync = ({
  jobs,
  onJobStatusChange,
  onLemmaIngested,
}: UsePipelineSyncProps) => {
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const hasActiveJobs = jobs.some(
      (j) => j.status === "queued" || j.status === "in_progress",
    );

    if (!hasActiveJobs) {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      return;
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        // Query server for latest state of all pending tokens
        const pendingTokens = jobs
          .filter((j) => j.status === "queued" || j.status === "in_progress")
          .map((j) => j.token);

        if (pendingTokens.length === 0) return;

        const response = await axios.post("/api/trainer/lemmas/queue-status", {
          tokens: pendingTokens,
        });

        const statusMap = response.data; // e.g. { "банан": { status: "completed", lemma_id: 104 } }

        let stateChanged = false;
        const updated = jobs.map((job) => {
          const remoteState = statusMap[job.token];
          if (remoteState && remoteState.status !== job.status) {
            stateChanged = true;
            if (remoteState.status === "completed" && remoteState.lemma_id) {
              onLemmaIngested(remoteState.lemma_id);
            }
            return {
              ...job,
              status: remoteState.status,
              message: remoteState.message || job.message,
            };
          }
          return job;
        });

        if (stateChanged) {
          onJobStatusChange(updated);
        }
      } catch (err) {
        console.error("Queue telemetry poll failed:", err);
      }
    }, 2500);

    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [jobs, onJobStatusChange, onLemmaIngested]);
};
