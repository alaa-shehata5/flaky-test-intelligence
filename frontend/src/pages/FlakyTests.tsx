import { useState } from 'react';
import { listProjects, listRuns } from '../api/endpoints';
import { DashboardFilters, type FilterValues } from '../components/Filters';
import { FlakyTable } from '../components/FlakyTable';
import { useApi } from '../hooks/useApi';

export function FlakyTests() {
  const [filters, setFilters] = useState<FilterValues>({});
  const projects = useApi(() => listProjects(), []);
  const allRuns = useApi(
    () => listRuns({ project_id: filters.projectId, limit: 200 }),
    [filters.projectId],
  );
  const branches = [...new Set((allRuns.data?.items ?? []).map((run) => run.branch))].sort();

  return (
    <section>
      <h1>Flaky Tests</h1>
      <DashboardFilters
        projects={projects.data?.items ?? []}
        branches={branches}
        value={filters}
        onChange={setFilters}
      />
      <FlakyTable
        project_id={filters.projectId}
        branch={filters.branch}
        minScore={filters.minScore}
      />
    </section>
  );
}
