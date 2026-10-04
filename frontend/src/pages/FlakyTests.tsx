import { Link } from 'react-router-dom';
import { listFlakyTests } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

export function FlakyTests() {
  const { data, loading, error, retry } = useApi(() => listFlakyTests({ limit: 20 }));

  if (loading) return <Loading label="Loading flaky tests…" />;
  if (error)
    return <ErrorState message={error.message} requestId={error.requestId} onRetry={retry} />;
  if (!data || data.items.length === 0)
    return <EmptyState message="No flaky tests detected. Seed demo data to explore this view." />;

  return (
    <section>
      <h1>Flaky Tests</h1>
      <p className="muted">
        {data.total} test{data.total === 1 ? '' : 's'} flagged — ranked by flakiness score.
      </p>
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
              <td>
                {test.classification}
                {test.newly_flaky && ' (new)'}
              </td>
              <td>{test.flakiness_score.toFixed(1)}</td>
              <td>{(test.pass_rate * 100).toFixed(1)}%</td>
              <td>{test.sample_size}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
