// app/frontend/src/components/dashboard/StudentAnalyticsOverview.tsx
// Built for React ^19.2.8 and Tailwind CSS ^3.4.19[cite: 30].

export type KSAStatusBand =
  | "needs_review"
  | "foundational_gap"
  | "zpd_focus"
  | "strong";

export interface StudentKSAMasteryItem {
  ksa_id: number;
  ksa_name: string;
  parent_id: number | null;
  avg_p_known: number;
  avg_retention: number;
  tracked_targets: number;
  last_practiced: string | null;
  status_band?: KSAStatusBand;
  is_due_for_review?: boolean;
}

export interface StudentDomainRollup {
  parent_id: number | null;
  domain_name: string;
  avg_p_known: number;
  avg_retention: number;
  ksa_count: number;
}

export interface StudentDashboardSummary {
  user_id: number;
  total_attempts: number;
  first_attempt_accuracy: number;
  exercises_completed: number;
  mean_p_known: number;
  mean_retention: number;
  retry_attempts?: number;
  recommended_focus?: StudentKSAMasteryItem[];
  domain_rollups?: StudentDomainRollup[];
  ksa_breakdown: StudentKSAMasteryItem[];
}

export interface StudentAnalyticsOverviewProps {
  data: StudentDashboardSummary;
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
}

export interface CurriculumOption {
  id: number;
  label: string;
}

export interface StudentAnalyticsOverviewProps {
  data: StudentDashboardSummary;
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
  modules?: CurriculumOption[];
  lessons?: CurriculumOption[];
  selectedModuleId?: number | null;
  selectedLessonId?: number | null;
  onModuleChange?: (moduleId: number | null) => void;
  onLessonChange?: (lessonId: number | null) => void;
  onClearScope?: () => void;
}

// Focused subcomponent rendering module & lesson dropdowns alongside your existing tables.
function CurriculumScopeBar({
  modules = [],
  lessons = [],
  selectedModuleId = null,
  selectedLessonId = null,
  onModuleChange,
  onLessonChange,
  onClearScope,
}: Omit<StudentAnalyticsOverviewProps, "data" | "onPracticeKsa">) {
  if (!onModuleChange || !onLessonChange) return null;

  const hasActiveScope = selectedModuleId !== null || selectedLessonId !== null;

  return (
    <section
      aria-label="Curriculum scope filter"
      className="rounded-lg border p-4 flex flex-wrap items-end gap-4"
    >
      <div className="flex flex-col gap-1">
        <label htmlFor="analytics-module-select" className="text-xs opacity-75">
          Module
        </label>
        <select
          id="analytics-module-select"
          value={selectedModuleId ?? ""}
          onChange={(e) =>
            onModuleChange(e.target.value ? Number(e.target.value) : null)
          }
          className="rounded border px-3 py-1.5 text-sm bg-transparent"
        >
          <option value="">All Modules</option>
          {modules.map((mod) => (
            <option key={mod.id} value={mod.id}>
              {mod.label}
            </option>
          ))}
        </select>
      </div>

      <div className="flex flex-col gap-1">
        <label htmlFor="analytics-lesson-select" className="text-xs opacity-75">
          Lesson
        </label>
        <select
          id="analytics-lesson-select"
          value={selectedLessonId ?? ""}
          onChange={(e) =>
            onLessonChange(e.target.value ? Number(e.target.value) : null)
          }
          className="rounded border px-3 py-1.5 text-sm bg-transparent"
        >
          <option value="">All Lessons</option>
          {lessons.map((lesson) => (
            <option key={lesson.id} value={lesson.id}>
              {lesson.label}
            </option>
          ))}
        </select>
      </div>

      {hasActiveScope && onClearScope && (
        <button
          type="button"
          onClick={onClearScope}
          className="rounded border px-3 py-1.5 text-xs font-medium"
        >
          Reset Scope
        </button>
      )}
    </section>
  );
}

function formatPercent(ratio: number): string {
  const clamped = Math.max(0, Math.min(1, ratio));
  return `${(clamped * 100).toFixed(1)}%`;
}

function formatTimestamp(iso: string | null): string {
  if (!iso) return "Never";
  const dt = new Date(iso);
  return Number.isNaN(dt.getTime()) ? iso : dt.toLocaleString();
}

function getStatusLabel(item: StudentKSAMasteryItem): string {
  if (item.status_band === "needs_review" || item.is_due_for_review) {
    return "Needs Review";
  }
  if (item.status_band === "zpd_focus") return "ZPD Focus";
  if (item.status_band === "strong") return "Strong";
  return "Foundational Gap";
}

// 1. High-level plain-text summary cards for core learner metrics.
function KpiSummaryRow({ data }: { data: StudentDashboardSummary }) {
  const retries = data.retry_attempts ?? 0;
  const cards = [
    {
      label: "First-Attempt Accuracy",
      value: formatPercent(data.first_attempt_accuracy),
      detail: `${data.total_attempts} total attempts (${retries} retries)`,
    },
    {
      label: "Mean Mastery P(L)",
      value: formatPercent(data.mean_p_known),
      detail: "Bayesian Knowledge Tracing average",
    },
    {
      label: "Mean Retention R",
      value: formatPercent(data.mean_retention),
      detail: "Time-decayed Ebbinghaus estimate",
    },
    {
      label: "Exercises Completed",
      value: String(data.exercises_completed),
      detail: `Learner ID #${data.user_id}`,
    },
  ];

  return (
    <section
      aria-label="Summary metrics"
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {cards.map((card) => (
        <div key={card.label} className="rounded-lg border p-4 space-y-1">
          <p className="text-xs uppercase tracking-wide opacity-70">
            {card.label}
          </p>
          <p className="text-2xl font-semibold tabular-nums">{card.value}</p>
          <p className="text-xs opacity-75">{card.detail}</p>
        </div>
      ))}
    </section>
  );
}

// 2. Concise list of recommended next focus skills with optional drill launch.
function RecommendedFocusSection({
  items,
  onPracticeKsa,
}: {
  items: StudentKSAMasteryItem[];
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
}) {
  // Render each recommended item's name, status label, mastery/retention figures,
  // and a button calling `onPracticeKsa(item)` if provided.
  return (
    <section
      aria-label="Recommended focus"
      className="rounded-lg border p-4 space-y-3"
    >
      <h2 className="text-base font-semibold">Recommended Focus</h2>
      <ul className="divide-y">
        {items.map((item) => (
          <li
            key={item.ksa_id}
            className="py-2.5 flex flex-wrap items-center justify-between gap-2 text-sm"
          >
            <div>
              <span className="font-medium">{item.ksa_name}</span>
              <span className="ml-2 opacity-75">[{getStatusLabel(item)}]</span>
              <span className="ml-2 tabular-nums opacity-80">
                Mastery: {formatPercent(item.avg_p_known)} | Retention:{" "}
                {formatPercent(item.avg_retention)}
              </span>
            </div>
            {onPracticeKsa && (
              <button
                type="button"
                onClick={() => onPracticeKsa(item)}
                className="rounded border px-2.5 py-1 text-xs font-medium"
              >
                Practice
              </button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

// 3. Parent-domain rollup table (when domain_rollups is populated).
function DomainRollupTable({ rollups }: { rollups: StudentDomainRollup[] }) {
  // Render a <table> with columns: Domain, KSAs, Avg Mastery P(L), Avg Retention R.
  return (
    <section
      aria-label="Domain rollups"
      className="rounded-lg border p-4 space-y-3 overflow-x-auto"
    >
      <h2 className="text-base font-semibold">Domain Rollups</h2>
      <table className="w-full text-left border-collapse text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2 pr-4">Domain</th>
            <th className="py-2 px-4 tabular-nums">KSAs</th>
            <th className="py-2 px-4 tabular-nums">Avg Mastery</th>
            <th className="py-2 pl-4 tabular-nums">Avg Retention</th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {rollups.map((row) => (
            <tr key={String(row.parent_id ?? row.domain_name)}>
              <td className="py-2 pr-4 font-medium">{row.domain_name}</td>
              <td className="py-2 px-4 tabular-nums">{row.ksa_count}</td>
              <td className="py-2 px-4 tabular-nums">
                {formatPercent(row.avg_p_known)}
              </td>
              <td className="py-2 pl-4 tabular-nums">
                {formatPercent(row.avg_retention)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

// 4. Primary KSA breakdown table showing mastery, retention, review status, and last practice.
function KSABreakdownTable({
  items,
  onPracticeKsa,
}: {
  items: StudentKSAMasteryItem[];
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
}) {
  if (items.length === 0) {
    return (
      <section
        aria-label="KSA breakdown"
        className="rounded-lg border p-4 text-sm opacity-75"
      >
        No KSA mastery records recorded yet. Complete an exercise to populate
        your skill breakdown.
      </section>
    );
  }

  return (
    <section
      aria-label="KSA breakdown"
      className="rounded-lg border p-4 space-y-3 overflow-x-auto"
    >
      <h2 className="text-base font-semibold">
        KSA Mastery &amp; Retention Breakdown
      </h2>
      <table className="w-full text-left border-collapse text-sm">
        <thead>
          <tr className="border-b">
            <th className="py-2 pr-4">Skill (KSA)</th>
            <th className="py-2 px-4">Status</th>
            <th className="py-2 px-4 tabular-nums">Mastery P(L)</th>
            <th className="py-2 px-4 tabular-nums">Retention R</th>
            <th className="py-2 px-4 tabular-nums">Targets</th>
            <th className="py-2 px-4">Last Practiced</th>
            {onPracticeKsa && <th className="py-2 pl-4">Action</th>}
          </tr>
        </thead>
        <tbody className="divide-y">
          {items.map((item) => (
            <tr key={item.ksa_id}>
              <td className="py-2 pr-4 font-medium">{item.ksa_name}</td>
              <td className="py-2 px-4">{getStatusLabel(item)}</td>
              <td className="py-2 px-4 tabular-nums">
                {formatPercent(item.avg_p_known)}
              </td>
              <td className="py-2 px-4 tabular-nums">
                {formatPercent(item.avg_retention)}
              </td>
              <td className="py-2 px-4 tabular-nums">{item.tracked_targets}</td>
              <td className="py-2 px-4 whitespace-nowrap">
                {formatTimestamp(item.last_practiced)}
              </td>
              {onPracticeKsa && (
                <td className="py-2 pl-4">
                  <button
                    type="button"
                    onClick={() => onPracticeKsa(item)}
                    className="rounded border px-2 py-1 text-xs font-medium"
                  >
                    Practice
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

export function StudentAnalyticsOverview({
  data,
  onPracticeKsa,
  modules = [],
  lessons = [],
  selectedModuleId = null,
  selectedLessonId = null,
  onModuleChange,
  onLessonChange,
  onClearScope,
}: StudentAnalyticsOverviewProps) {
  const focusItems =
    data.recommended_focus && data.recommended_focus.length > 0
      ? data.recommended_focus
      : data.ksa_breakdown.slice(0, 3);

  return (
    <div className="space-y-6">
      {/* Mount the scope filter bar so learners can filter by module and/or lesson[cite: 25]. */}
      <CurriculumScopeBar
        modules={modules}
        lessons={lessons}
        selectedModuleId={selectedModuleId}
        selectedLessonId={selectedLessonId}
        onModuleChange={onModuleChange}
        onLessonChange={onLessonChange}
        onClearScope={onClearScope}
      />

      <KpiSummaryRow data={data} />
      {focusItems.length > 0 && (
        <RecommendedFocusSection
          items={focusItems}
          onPracticeKsa={onPracticeKsa}
        />
      )}
      {data.domain_rollups && data.domain_rollups.length > 0 && (
        <DomainRollupTable rollups={data.domain_rollups} />
      )}
      <KSABreakdownTable
        items={data.ksa_breakdown}
        onPracticeKsa={onPracticeKsa}
      />
    </div>
  );
}
