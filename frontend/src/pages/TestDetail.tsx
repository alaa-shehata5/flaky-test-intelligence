import { Link, useParams } from 'react-router-dom';
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { HistoryPoint } from '../api/types';
import { getTest, getTestHistory } from '../api/endpoints';
import { ClassificationBadge, StatusBadge } from '../components/Badges';
import { EmptyState, ErrorState, Loading } from '../components/States';
import { useApi } from '../hooks/useApi';

const STATUS_COLORS: Record<string, string> = {
  passed: '#2a9d48',
  failed: '#d64545',
  error: '#c77700',
  skipped: '#8a929b',
};

function uniqueFailures(history: HistoryPoint[]): HistoryPoint[] {
  const seen = new Set<string>();
  const unique: HistoryPoint[] = [];
  for (const point of [...history].reverse()) {
    if (point.status !== 'failed' && point.status !== 'error') continue;
    const key = `${point.failure_type ?? ''}|||${point.failure_message ?? ''}`;
    if (seen.has(key)) continue;
    seen.add(key);
    unique.push(point);
  }
  return unique.slice(0, 5);
}

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
  const points = history.data ?? [];
  const scoreData = points.map((p) => ({ run: `#${p.run_number}`, score: p.score }));
  const durationData = points.map((p) => ({ run: `#${p.run_number}`, duration: p.duration }));
  const outcomeData = points.map((p) => ({ run: p.run_number, y: 1, status: p.status }));

  return (
    <section>
      <p>
        <Link to="/tests">← All tests</Link>
      </p>
      <h1>{test.test_name}</h1>
      <p className="muted">{test.unique_key}</p>
      <p>
        <ClassificationBadge value={test.classification} />{' '}
        {test.newly_flaky && <span className="badge badge-new">newly flaky</span>}{' '}
        {test.persistently_flaky && (
          <span className="badge badge-persistent">persistently flaky</span>
        )}{' '}
        {test.is_slow && <span className="badge badge-slow">slow</span>}
      </p>

      <dl className="facts">
        <div>
          <dt>Flakiness score</dt>
          <dd>{test.flakiness_score.toFixed(2)}</dd>
        </div>
        <div>
          <dt>Sample size</dt>
          <dd>{test.sample_size}</dd>
        </div>
        <div>
          <dt>Pass rate</dt>
          <dd>{(test.pass_rate * 100).toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Failure rate</dt>
          <dd>{(test.failure_rate * 100).toFixed(1)}%</dd>
        </div>
        <div>
          <dt>Passed / failed / error / skipped</dt>
          <dd>
            {test.passed} / {test.failed} / {test.error} / {test.skipped}
          </dd>
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
        <div>
          <dt>Duration range</dt>
          <dd>
            {test.duration_min.toFixed(2)}s – {test.duration_max.toFixed(2)}s
          </dd>
        </div>
        <div>
          <dt>Duration variability (stddev)</dt>
          <dd>{test.duration_stddev.toFixed(2)}s</dd>
        </div>
        <div>
          <dt>Pass-rate trend</dt>
          <dd>
            {test.pass_rate_delta >= 0 ? '+' : ''}
            {(test.pass_rate_delta * 100).toFixed(1)} pts
          </dd>
        </div>
        <div>
          <dt>Score trend</dt>
          <dd>
            {test.score_delta >= 0 ? '+' : ''}
            {test.score_delta.toFixed(1)}
          </dd>
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
      {points.length > 0 && (
        <>
          <div className="outcome-strip" aria-label="Outcome per run">
            {points.map((point) => (
              <span
                key={point.run_id}
                title={`Run #${point.run_number}: ${point.status}`}
                className={`outcome-cell outcome-${point.status}`}
              >
                {point.status === 'passed' ? '✓' : point.status === 'skipped' ? '–' : '✗'}
              </span>
            ))}
          </div>
          <ol className="history">
            {points.map((point) => (
              <li key={point.run_id}>
                <StatusBadge status={point.status} /> Run #{point.run_number} —{' '}
                {point.duration.toFixed(2)}s, score {point.score.toFixed(1)}
              </li>
            ))}
          </ol>

          <div className="chart-grid">
            <div className="chart-card">
              <h3>Outcome history</h3>
              <ResponsiveContainer width="100%" height={200}>
                <ScatterChart margin={{ left: -30 }}>
                  <XAxis dataKey="run" type="number" />
                  <YAxis dataKey="y" type="number" domain={[0, 2]} tick={false} />
                  <Tooltip />
                  <Scatter data={outcomeData}>
                    {outcomeData.map((entry) => (
                      <Cell key={entry.run} fill={STATUS_COLORS[entry.status] ?? '#888'} />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-card">
              <h3>Duration history (s)</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={durationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="run" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="duration" stroke="#4a6fa5" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
            <div className="chart-card">
              <h3>Flakiness score history</h3>
              <ResponsiveContainer width="100%" height={200}>
                <LineChart data={scoreData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="run" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Line type="monotone" dataKey="score" stroke="#d64545" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <h2>Recent failure messages</h2>
          {uniqueFailures(points).length === 0 && (
            <p className="muted">No failures recorded — nothing to investigate.</p>
          )}
          {uniqueFailures(points).map((point) => (
            <div key={`${point.run_id}-${point.failure_type}`} className="failure-card">
              <div>
                <StatusBadge status={point.status} /> Run #{point.run_number}
                {point.failure_type && <span className="muted"> · {point.failure_type}</span>}
              </div>
              <pre>{point.failure_message ?? '(no message captured)'}</pre>
            </div>
          ))}
        </>
      )}
    </section>
  );
}
