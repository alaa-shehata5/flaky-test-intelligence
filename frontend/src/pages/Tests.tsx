import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Classification } from '../api/types';
import { listTests } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

const CLASSIFICATIONS: Array<Classification | ''> = [
  '',
  'STABLE',
  'MOSTLY_STABLE',
  'SUSPECTED_FLAKY',
  'HIGHLY_FLAKY',
  'CONSISTENTLY_FAILING',
  'INSUFFICIENT_DATA',
];

const PAGE_SIZE = 20;

export function Tests() {
  const [query, setQuery] = useState('');
  const [classification, setClassification] = useState<Classification | ''>('');
  const [page, setPage] = useState(0);

  const { data, loading, error, retry } = useApi(
    () =>
      listTests({
        q: query || undefined,
        classification: classification || undefined,
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      }),
    [query, classification, page],
  );

  return (
    <section>
      <h1>Tests</h1>
      <div className="toolbar">
        <input
          type="search"
          placeholder="Search tests…"
          value={query}
          onChange={(event) => {
            setQuery(event.target.value);
            setPage(0);
          }}
          aria-label="Search tests"
        />
        <select
          value={classification}
          onChange={(event) => {
            setClassification(event.target.value as Classification | '');
            setPage(0);
          }}
          aria-label="Filter by classification"
        >
          {CLASSIFICATIONS.map((value) => (
            <option key={value || 'all'} value={value}>
              {value || 'All classifications'}
            </option>
          ))}
        </select>
      </div>

      {loading && <Loading label="Loading tests…" />}
      {error && <ErrorState message={error.message} requestId={error.requestId} onRetry={retry} />}
      {data && data.items.length === 0 && (
        <EmptyState message="No tests match the current filters." />
      )}
      {data && data.items.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Classification</th>
                <th>Score</th>
                <th>Pass rate</th>
                <th>Runs</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((test) => (
                <tr key={test.test_case_id}>
                  <td>
                    <Link to={`/tests/${test.test_case_id}`}>{test.test_name}</Link>
                    <div className="muted">{test.classname}</div>
                  </td>
                  <td>{test.classification}</td>
                  <td>{test.flakiness_score.toFixed(1)}</td>
                  <td>{(test.pass_rate * 100).toFixed(1)}%</td>
                  <td>{test.sample_size}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button type="button" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {page + 1} of {Math.max(1, Math.ceil(data.total / PAGE_SIZE))} ({data.total}{' '}
              tests)
            </span>
            <button
              type="button"
              disabled={(page + 1) * PAGE_SIZE >= data.total}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </section>
  );
}
