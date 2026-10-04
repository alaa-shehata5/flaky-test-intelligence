import { Link, useParams } from 'react-router-dom';
import { getTest, getTestHistory } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

export function TestDetail() {
  const { id } = useParams<{ id: string }>();
  const testId = Number(id);
  const detail = useApi(() => getTest(testId), [testId]);
  const history = useApi(() => getTestHistory(testId), [testId]);

  if (detail.loading) return <Loading label="Loading test…" />;
  if (detail.error)
    return (
      <ErrorState
        message={detail.error.message}
        requestId={detail.error.requestId}
        onRetry={detail.retry}
      />
    );
  if (!detail.data) return <EmptyState message="Test not found." />;

  const test = detail.data;
  return (
    <section>
      <p>
        <Link to="/tests">← All tests</Link>
      </p>
      <h1>{test.test_name}</h1>
      <p className="muted">{test.unique_key}</p>
      <dl className="facts">
        <div>
          <dt>Classification</dt>
          <dd>{test.classification}</dd>
        </div>
        <div>
          <dt>Flakiness score</dt>
          <dd>{test.flakiness_score.toFixed(2)}</dd>
        </div>
        <div>
          <dt>Pass rate</dt>
          <dd>{(test.pass_rate * 100).toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Sample size</dt>
          <dd>{test.sample_size}</dd>
        </div>
        <div>
          <dt>Avg duration</dt>
          <dd>{test.duration_mean.toFixed(2)}s</dd>
        </div>
        <div>
          <dt>Median duration</dt>
          <dd>{test.duration_median.toFixed(2)}s</dd>
        </div>
        <div>
          <dt>p95 duration</dt>
          <dd>{test.duration_p95.toFixed(2)}s</dd>
        </div>
      </dl>

      <h2>Execution history</h2>
      {history.loading && <Loading label="Loading history…" />}
      {history.error && (
        <ErrorState
          message={history.error.message}
          requestId={history.error.requestId}
          onRetry={history.retry}
        />
      )}
      {history.data && history.data.length === 0 && (
        <EmptyState message="No executions recorded." />
      )}
      {history.data && history.data.length > 0 && (
        <ol className="history">
          {history.data.map((point) => (
            <li key={point.run_id} className={`history-${point.status}`}>
              Run #{point.run_number} — {point.status.toUpperCase()} ({point.duration.toFixed(2)}s,
              score {point.score.toFixed(1)})
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
