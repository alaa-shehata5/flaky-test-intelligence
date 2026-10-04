import { Link } from 'react-router-dom';
import { getSummary } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

export function Dashboard() {
  const { data, loading, error, retry } = useApi(() => getSummary());

  if (loading) return <Loading label="Loading dashboard…" />;
  if (error)
    return <ErrorState message={error.message} requestId={error.requestId} onRetry={retry} />;
  if (!data) return <EmptyState message="No summary available." />;

  const rows: Array<[string, number | string]> = [
    ['Total tests', data.total_tests],
    ['CI runs', data.total_runs],
    ['Stable tests', data.stable_tests],
    ['Suspected flaky', data.suspected_flaky_tests],
    ['Highly flaky', data.highly_flaky_tests],
    ['Consistently failing', data.consistently_failing_tests],
    ['Slow tests', data.slow_tests],
    ['Newly flaky', data.newly_flaky_tests],
    ['Average pass rate', `${(data.average_pass_rate * 100).toFixed(1)}%`],
  ];

  return (
    <section>
      <h1>Dashboard</h1>
      <dl className="kpis">
        {rows.map(([label, value]) => (
          <div key={label} className="kpi">
            <dt>{label}</dt>
            <dd>{value}</dd>
          </div>
        ))}
      </dl>
      <p>
        <Link to="/flaky">View flaky tests →</Link>
      </p>
    </section>
  );
}
