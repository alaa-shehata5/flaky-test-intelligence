import { useState } from 'react';
import { listRuns } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

const PAGE_SIZE = 20;

export function Runs() {
  const [page, setPage] = useState(0);
  const { data, loading, error, retry } = useApi(
    () => listRuns({ limit: PAGE_SIZE, offset: page * PAGE_SIZE }),
    [page],
  );

  if (loading) return <Loading label="Loading runs…" />;
  if (error)
    return <ErrorState message={error.message} requestId={error.requestId} onRetry={retry} />;
  if (!data || data.items.length === 0) return <EmptyState message="No CI runs ingested yet." />;

  return (
    <section>
      <h1>Runs</h1>
      <table>
        <thead>
          <tr>
            <th>Run</th>
            <th>Project</th>
            <th>Branch</th>
            <th>Passed</th>
            <th>Failed</th>
            <th>Error</th>
            <th>Skipped</th>
          </tr>
        </thead>
        <tbody>
          {data.items.map((run) => (
            <tr key={run.id}>
              <td>#{run.run_number}</td>
              <td>{run.project_name}</td>
              <td>{run.branch}</td>
              <td>{run.passed_tests}</td>
              <td>{run.failed_tests}</td>
              <td>{run.error_tests}</td>
              <td>{run.skipped_tests}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <button type="button" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
          Previous
        </button>
        <span>
          Page {page + 1} of {Math.max(1, Math.ceil(data.total / PAGE_SIZE))} ({data.total} runs)
        </span>
        <button
          type="button"
          disabled={(page + 1) * PAGE_SIZE >= data.total}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </button>
      </div>
    </section>
  );
}
