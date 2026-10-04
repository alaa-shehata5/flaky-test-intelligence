import { useState } from 'react';
import { listProjects, listRuns } from '../api/endpoints';
import { DashboardFilters, type FilterValues } from '../components/Filters';
import { FlakyTable } from '../components/FlakyTable';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

export function FlakyTests() {
  const [filters, setFilters] = useState<FilterValues>({});
  const projects = useApi(() => listProjects(), []);
  const allRuns = useApi(
    () => listRuns({ project_id: filters.projectId, limit: 200 }),
    [filters.projectId],
  );
  const runs = allRuns.data?.items ?? [];
  const branches = [...new Set(runs.map((run) => run.branch))].sort();
  const workflows = [
    ...new Set(runs.flatMap((run) => (run.workflow_name ? [run.workflow_name] : []))),
  ].sort();
  const environments = [
    ...new Set(runs.flatMap((run) => (run.environment ? [run.environment] : []))),
  ].sort();

  return (
    <section>
      <h1>Flaky Tests</h1>
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
      {projects.data?.items.length === 0 && (
        <EmptyState message="No projects yet. Ingest a run or seed demo data." />
      )}
      <FlakyTable
        project_id={filters.projectId}
        branch={filters.branch}
        workflow_name={filters.workflowName}
        environment={filters.environment}
        date_from={filters.dateFrom}
        date_to={filters.dateTo}
        classificationFilter={filters.classification ?? ''}
        minScore={filters.minScore}
      />
    </section>
  );
}
