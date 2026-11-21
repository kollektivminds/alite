// app/frontend/src/pages/AnalyticsPage.tsx
import axios from "axios";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useAuth } from "../../contexts/useAuth";
import {
  StudentAnalyticsOverview,
  type StudentDashboardSummary,
  type StudentKSAMasteryItem,
} from "./StudentAnalyticsOverview";

export type AnalyticsRole = "student" | "instructor" | "admin";

export interface AnalyticsPageProps {
  activeGroupId?: number | null;
  onBackToWorkspace?: () => void;
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
}

export interface LessonListRecord {
  id: number;
  title?: string | null;
  name?: string | null;
  module_id?: number | null;
  mod_id?: number | null;
  module_name?: string | null;
}

export interface CurriculumOption {
  id: number;
  label: string;
}

export interface CurriculumModuleSummary {
  module_id: number;
  module_name: string;
  lessons: CurriculumOption[];
}

export interface CurriculumScopeBarProps {
  modules: CurriculumOption[];
  lessons: CurriculumOption[];
  selectedModuleId: number | null;
  selectedLessonId: number | null;
  onModuleChange: (moduleId: number | null) => void;
  onLessonChange: (lessonId: number | null) => void;
  onClearScope: () => void;
}

// Pure presentational bar letting learners narrow KSA mastery to a module or lesson.
export function CurriculumScopeBar({
  modules,
  lessons,
  selectedModuleId,
  selectedLessonId,
  onModuleChange,
  onLessonChange,
  onClearScope,
}: CurriculumScopeBarProps) {
  return (
    <section
      aria-label="Curriculum scope filter"
      className="rounded-lg border p-4 flex flex-wrap items-end gap-4"
    >
      {/* Module selector: resets lesson selection when changed so stale lesson IDs never linger. */}
      <div className="flex flex-col gap-1">
        <label
          htmlFor="scope-module"
          className="text-xs font-medium opacity-75"
        >
          Module
        </label>
        <select
          id="scope-module"
          value={selectedModuleId ?? ""}
          onChange={(e) => {
            const next = e.target.value ? Number(e.target.value) : null;
            onModuleChange(next);
            onLessonChange(null);
          }}
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

      {/* Lesson selector: narrows further to a specific LessonList within the chosen scope. */}
      <div className="flex flex-col gap-1">
        <label
          htmlFor="scope-lesson"
          className="text-xs font-medium opacity-75"
        >
          Lesson
        </label>
        <select
          id="scope-lesson"
          value={selectedLessonId ?? ""}
          onChange={(e) => {
            const next = e.target.value ? Number(e.target.value) : null;
            onLessonChange(next);
          }}
          className="rounded border px-3 py-1.5 text-sm bg-transparent"
        >
          <option value="">All Lessons in Scope</option>
          {lessons.map((lesson) => (
            <option key={lesson.id} value={lesson.id}>
              {lesson.label}
            </option>
          ))}
        </select>
      </div>

      {(selectedModuleId !== null || selectedLessonId !== null) && (
        <button
          type="button"
          onClick={onClearScope}
          className="rounded border px-3 py-1.5 text-xs font-medium"
        >
          Reset to Overall
        </button>
      )}
    </section>
  );
}

// Generic authenticated fetcher using axios ^1.19.0; relies on server-side RBAC.
function useAnalyticsEndpoint<T>(
  endpoint: string | null,
  params?: Record<string, number | boolean | null | undefined>,
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(Boolean(endpoint));
  const [error, setError] = useState<string | null>(null);

  // Normalize active query parameters into a stable dependency key.
  const serializedParams = useMemo(() => {
    if (!params) return "";
    const activeEntries = Object.entries(params).filter(
      ([, v]) => v !== null && v !== undefined,
    );
    return JSON.stringify(activeEntries);
  }, [params]);

  const fetchEndpoint = useCallback(
    async (signal?: AbortSignal) => {
      if (!endpoint) {
        setData(null);
        setLoading(false);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      const parsedEntries = serializedParams
        ? (JSON.parse(serializedParams) as Array<[string, number | boolean]>)
        : [];
      const queryParams = Object.fromEntries(parsedEntries);

      try {
        const response = await axios.get<T>(endpoint, {
          params: queryParams,
          signal,
          withCredentials: true,
        });
        if (!signal?.aborted) {
          setData(response.data);
        }
      } catch (err) {
        if (axios.isCancel(err) || signal?.aborted) return;
        const message = axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? err.message)
          : "Unable to load analytics data.";
        setError(String(message));
      } finally {
        if (!signal?.aborted) {
          setLoading(false);
        }
      }
    },
    [endpoint, serializedParams],
  );

  useEffect(() => {
    const controller = new AbortController();
    void fetchEndpoint(controller.signal);
    return () => controller.abort();
  }, [fetchEndpoint]);

  return { data, loading, error, refresh: () => fetchEndpoint() };
}

function StudentAnalyticsSection({
  onPracticeKsa,
}: {
  onPracticeKsa?: (item: StudentKSAMasteryItem) => void;
}) {
  const [selectedModuleId, setSelectedModuleId] = useState<number | null>(null);
  const [selectedLessonId, setSelectedLessonId] = useState<number | null>(null);

  // load module / lesson hierarchy from modules endpoint.
  const { data: hierarchy } = useAnalyticsEndpoint<CurriculumModuleSummary[]>(
    "/api/v1/modules/hierarchy",
  );

  // derive unique modules and filtered lessons declaratively from `/api/v1/lesslists/all`.
  const { moduleOptions, lessonOptions } = useMemo(() => {
    const modulesList = Array.isArray(hierarchy) ? hierarchy : [];
    const modOpts: CurriculumOption[] = modulesList.map((m) => ({
      id: m.module_id,
      label: m.module_name,
    }));

    const scopedModules =
      selectedModuleId === null
        ? modulesList
        : modulesList.filter((mod) => mod.module_id === selectedModuleId);

    // Deduplicate lessons across matching modules by lesson ID while preserving order.
    const lessonMap = new Map<number, string>();
    for (const mod of scopedModules) {
      for (const lesson of mod.lessons) {
        if (!lessonMap.has(lesson.id)) {
          lessonMap.set(lesson.id, lesson.label);
        }
      }
    }

    const lesOpts: CurriculumOption[] = Array.from(
      lessonMap,
      ([id, label]) => ({ id, label }),
    );

    return { moduleOptions: modOpts, lessonOptions: lesOpts };
  }, [hierarchy, selectedModuleId]);

  // 3. Re-query /api/v1/analytics/student/me whenever module_id or lesson_id changes.
  const queryParams = useMemo(
    () => ({
      module_id: selectedModuleId,
      lesson_id: selectedLessonId,
    }),
    [selectedModuleId, selectedLessonId],
  );

  const { data, loading, error } =
    useAnalyticsEndpoint<StudentDashboardSummary>(
      "/api/v1/analytics/student/me",
      queryParams,
    );

  const handleModuleChange = (nextModuleId: number | null) => {
    setSelectedModuleId(nextModuleId);
    // clear stale lesson selection whenever the parent module changes.
    setSelectedLessonId(null);
  };

  const handleClearScope = () => {
    setSelectedModuleId(null);
    setSelectedLessonId(null);
  };

  if (loading)
    return <p className="text-sm opacity-75">Loading personal mastery...</p>;
  if (error)
    return (
      <div role="alert" className="rounded-lg border p-4 text-sm">
        {error}
      </div>
    );
  if (!data) return null;

  return (
    <StudentAnalyticsOverview
      data={data}
      onPracticeKsa={onPracticeKsa}
      modules={moduleOptions}
      lessons={lessonOptions}
      selectedModuleId={selectedModuleId}
      selectedLessonId={selectedLessonId}
      onModuleChange={handleModuleChange}
      onLessonChange={setSelectedLessonId}
      onClearScope={handleClearScope}
    />
  );
}

function InstructorAnalyticsSection({ groupId }: { groupId?: number | null }) {
  const endpoint = groupId
    ? `/api/v1/analytics/instructor/class/${groupId}`
    : null;
  const { data, loading, error } =
    useAnalyticsEndpoint<Record<string, unknown>>(endpoint);

  if (!groupId) {
    return (
      <div className="rounded-lg border p-6 text-sm opacity-80">
        Select a class group to inspect cohort KSA mastery and learner support
        flags.
      </div>
    );
  }
  if (loading)
    return <p className="text-sm opacity-75">Loading cohort analytics...</p>;
  if (error)
    return (
      <div role="alert" className="rounded-lg border p-4 text-sm">
        {error}
      </div>
    );
  if (!data) return null;

  return (
    <pre className="rounded-lg border p-4 text-xs overflow-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function AdminAnalyticsSection() {
  const { data, loading, error } = useAnalyticsEndpoint<
    Record<string, unknown>
  >("/api/v1/analytics/admin/overview");

  if (loading)
    return <p className="text-sm opacity-75">Loading platform telemetry...</p>;
  if (error)
    return (
      <div role="alert" className="rounded-lg border p-4 text-sm">
        {error}
      </div>
    );
  if (!data) return null;

  return (
    <pre className="rounded-lg border p-4 text-xs overflow-auto">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

export default function AnalyticsPage({
  activeGroupId = null,
  onBackToWorkspace,
  onPracticeKsa,
}: AnalyticsPageProps) {
  // 1. Call ALL hooks unconditionally at the top of the component (Rules of Hooks).
  const { user, loading: authLoading } = useAuth();
  const userRole: AnalyticsRole = (user?.role as AnalyticsRole) ?? "student";

  const [activeLens, setActiveLens] = useState<AnalyticsRole>(userRole);

  // Synchronize activeLens once AuthProvider finishes resolving user.role.
  useEffect(() => {
    setActiveLens(userRole);
  }, [userRole]);

  // 2. Conditional early return is safe ONLY after all hooks have been called.
  if (authLoading) {
    return (
      <p className="p-8 text-sm opacity-75">Verifying account permissions...</p>
    );
  }

  // Admins can audit all three lenses; instructors can view cohort + personal; students see personal.
  const availableLenses: AnalyticsRole[] =
    userRole === "admin"
      ? ["admin", "instructor", "student"]
      : userRole === "instructor"
        ? ["instructor", "student"]
        : ["student"];

  return (
    <main className="min-h-screen w-full px-6 py-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header className="flex flex-wrap items-center justify-between gap-4 border-b pb-4">
          <div>
            <h1 className="text-2xl font-bold capitalize">
              {activeLens} Analytics
            </h1>
            <p className="text-xs opacity-70">Signed in as {userRole}</p>
          </div>

          <div className="flex items-center gap-3">
            {availableLenses.length > 1 && (
              <div
                role="group"
                aria-label="Analytics perspective"
                className="flex rounded-lg border p-1"
              >
                {availableLenses.map((lens) => (
                  <button
                    key={lens}
                    type="button"
                    onClick={() => setActiveLens(lens)}
                    className={`rounded px-2.5 py-1 text-xs font-medium capitalize ${
                      activeLens === lens
                        ? "bg-indigo-600 text-white"
                        : "opacity-75 hover:opacity-100"
                    }`}
                  >
                    {lens}
                  </button>
                ))}
              </div>
            )}

            {onBackToWorkspace && (
              <button
                type="button"
                onClick={onBackToWorkspace}
                className="rounded-lg border px-3 py-1.5 text-sm font-medium"
              >
                Back to Workspace
              </button>
            )}
          </div>
        </header>

        {/* Backend endpoints independently enforce RBAC on every request. */}
        {activeLens === "student" && (
          <StudentAnalyticsSection onPracticeKsa={onPracticeKsa} />
        )}
        {activeLens === "instructor" && (
          <InstructorAnalyticsSection groupId={activeGroupId} />
        )}
        {activeLens === "admin" && <AdminAnalyticsSection />}
      </div>
    </main>
  );
}
