import { useState } from 'react';
import { getSummary, listFlakyTests, listProjects, listRuns, listTests } from '../api/endpoints';
import { KpiCards, summaryKpis } from '../components/Badges';
import {
  DurationTrend,
  OutcomeDonut,
  PassRateTrend,
  SeverityBars,
  TopFlakyBars,
} from '../components/Charts';
import { DashboardFilters, type FilterValues } from '../components/Filters';
import { FlakyTable } from '../components/FlakyTable';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

export function Dashboard() {
  const [filters, setFilters] = useState<FilterValues>({});
  const summary = useApi(
    () => getSummary({ project_id: filters.projectId, branch: filters.branch }),
    [filters.projectId, filters.branch],
  );
  const projects = useApi(() => listProjects(), []);
  const allRuns = useApi(
    () => listRuns({ project_id: filters.projectId, limit: 200 }),
    [filters.projectId],
  );
  const scopedRuns = useApi(
    () => listRuns({ project_id: filters.projectId, branch: filters.branch, limit: 200 }),
    [filters.projectId, filters.branch],
  );
  const scopedTests = useApi(
    () => listTests({ project_id: filters.projectId, branch: filters.branch, limit: 200 }),
    [filters.projectId, filters.branch],
  );
  const topFlaky = useApi(
    () =>
      listFlakyTests({
        project_id: filters.projectId,
        branch: filters.branch,
        minimum_score: filters.minScore,
        limit: 8,
      }),
    [filters.projectId, filters.branch, filters.minScore],
  );

  const branches = [...new Set((allRuns.data?.items ?? []).map((run) => run.branch))].sort();

  return (
    <section>
      <h1>Dashboard</h1>
      <DashboardFilters
        projects={projects.data?.items ?? []}
        branches={branches}
        value={filters}
        onChange={setFilters}
      />

      {summary.loading && <Loading label="Loading summary…" />}
      {summary.error && (
        <ErrorState
          message={summary.error.message}
          requestId={summary.error.requestId}
          onRetry={summary.retry}
        />
      )}
      {summary.data && <KpiCards kpis={summaryKpis(summary.data)} />}
      {summary.data && summary.data.total_tests === 0 && (
        <EmptyState message="No tests in scope. Adjust filters or seed demo data." />
      )}

      {scopedRuns.data && scopedTests.data && (
        <div className="chart-grid">
          <OutcomeDonut runs={scopedRuns.data.items} />
          <SeverityBars tests={scopedTests.data.items} />
          <PassRateTrend runs={scopedRuns.data.items} />
          <DurationTrend runs={scopedRuns.data.items} />
        </div>
      )}

      <h2>Top flaky tests</h2>
      {topFlaky.loading && <Loading label="Loading top flaky tests…" />}
      {topFlaky.error && (
        <ErrorState
          message={topFlaky.error.message}
          requestId={topFlaky.error.requestId}
          onRetry={topFlaky.retry}
        />
      )}
      {topFlaky.data && <TopFlakyBars tests={topFlaky.data.items} />}

      <h2>Flaky test ranking</h2>
      <FlakyTable
        project_id={filters.projectId}
        branch={filters.branch}
        minScore={filters.minScore}
        pageSize={10}
      />
    </section>
  );
}
