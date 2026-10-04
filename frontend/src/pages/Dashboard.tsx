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
    () =>
      getSummary({
        project_id: filters.projectId,
        branch: filters.branch,
        workflow_name: filters.workflowName,
        environment: filters.environment,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        classification: filters.classification || undefined,
        minimum_score: filters.minScore,
      }),
    [
      filters.projectId,
      filters.branch,
      filters.workflowName,
      filters.environment,
      filters.dateFrom,
      filters.dateTo,
      filters.classification,
      filters.minScore,
    ],
  );
  const projects = useApi(() => listProjects(), []);
  const allRuns = useApi(
    () => listRuns({ project_id: filters.projectId, limit: 200 }),
    [filters.projectId],
  );
  const scopedRuns = useApi(
    () =>
      listRuns({
        project_id: filters.projectId,
        branch: filters.branch,
        workflow_name: filters.workflowName,
        environment: filters.environment,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        limit: 200,
      }),
    [
      filters.projectId,
      filters.branch,
      filters.workflowName,
      filters.environment,
      filters.dateFrom,
      filters.dateTo,
    ],
  );
  const scopedTests = useApi(
    () =>
      listTests({
        project_id: filters.projectId,
        branch: filters.branch,
        workflow_name: filters.workflowName,
        environment: filters.environment,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        classification: filters.classification || undefined,
        minimum_score: filters.minScore,
        limit: 200,
      }),
    [
      filters.projectId,
      filters.branch,
      filters.workflowName,
      filters.environment,
      filters.dateFrom,
      filters.dateTo,
      filters.classification,
      filters.minScore,
    ],
  );
  const topFlaky = useApi(
    () =>
      listFlakyTests({
        project_id: filters.projectId,
        branch: filters.branch,
        workflow_name: filters.workflowName,
        environment: filters.environment,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        classification: filters.classification || undefined,
        minimum_score: filters.minScore,
        limit: 8,
      }),
    [
      filters.projectId,
      filters.branch,
      filters.workflowName,
      filters.environment,
      filters.dateFrom,
      filters.dateTo,
      filters.classification,
      filters.minScore,
    ],
  );

  const branches = [...new Set((allRuns.data?.items ?? []).map((run) => run.branch))].sort();
  const workflows = [
    ...new Set(
      (allRuns.data?.items ?? []).flatMap((run) => (run.workflow_name ? [run.workflow_name] : [])),
    ),
  ].sort();
  const environments = [
    ...new Set(
      (allRuns.data?.items ?? []).flatMap((run) => (run.environment ? [run.environment] : [])),
    ),
  ].sort();

  return (
    <section>
      <h1>Dashboard</h1>
      <DashboardFilters
        projects={projects.data?.items ?? []}
        branches={branches}
        workflows={workflows}
        environments={environments}
        value={filters}
        onChange={setFilters}
      />

      {projects.loading && <Loading label="Loading projects…" />}
      {projects.error && (
        <ErrorState
          message={projects.error.message}
          requestId={projects.error.requestId}
          onRetry={projects.retry}
        />
      )}
      {allRuns.loading && <Loading label="Loading branches…" />}
      {allRuns.error && (
        <ErrorState
          message={allRuns.error.message}
          requestId={allRuns.error.requestId}
          onRetry={allRuns.retry}
        />
      )}

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
      {scopedRuns.loading && <Loading label="Loading run charts…" />}
      {scopedRuns.error && (
        <ErrorState
          message={scopedRuns.error.message}
          requestId={scopedRuns.error.requestId}
          onRetry={scopedRuns.retry}
        />
      )}
      {scopedTests.loading && <Loading label="Loading test charts…" />}
      {scopedTests.error && (
        <ErrorState
          message={scopedTests.error.message}
          requestId={scopedTests.error.requestId}
          onRetry={scopedTests.retry}
        />
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
        workflow_name={filters.workflowName}
        environment={filters.environment}
        date_from={filters.dateFrom}
        date_to={filters.dateTo}
        classificationFilter={filters.classification ?? ''}
        minScore={filters.minScore}
        pageSize={10}
      />
    </section>
  );
}
