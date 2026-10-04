import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { TestListItem, TestRun } from '../api/types';

const OUTCOME_COLORS: Record<string, string> = {
  Passed: '#2a9d48',
  Failed: '#d64545',
  Error: '#c77700',
  Skipped: '#8a929b',
};

const SEVERITY_COLORS: Record<string, string> = {
  Stable: '#2a9d48',
  'Mostly stable': '#7ab648',
  'Suspected flaky': '#d9a400',
  'Highly flaky': '#d64545',
  'Consistently failing': '#8f1d1d',
  'Insufficient data': '#8a929b',
};

function ChartShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="chart-card">
      <h3>{title}</h3>
      {children}
    </div>
  );
}

export function OutcomeDonut({ runs }: { runs: TestRun[] }) {
  const totals = runs.reduce(
    (acc, run) => ({
      Passed: acc.Passed + run.passed_tests,
      Failed: acc.Failed + run.failed_tests,
      Error: acc.Error + run.error_tests,
      Skipped: acc.Skipped + run.skipped_tests,
    }),
    { Passed: 0, Failed: 0, Error: 0, Skipped: 0 },
  );
  const data = Object.entries(totals).map(([name, value]) => ({ name, value }));
  if (data.every((entry) => entry.value === 0)) return null;
  return (
    <ChartShell title="Outcome distribution (scoped runs)">
      <ResponsiveContainer width="100%" height={240}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>
            {data.map((entry) => (
              <Cell key={entry.name} fill={OUTCOME_COLORS[entry.name] ?? '#888'} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function SeverityBars({ tests }: { tests: TestListItem[] }) {
  const counts = new Map<string, number>();
  for (const test of tests) {
    const label =
      test.classification === 'STABLE'
        ? 'Stable'
        : test.classification === 'MOSTLY_STABLE'
          ? 'Mostly stable'
          : test.classification === 'SUSPECTED_FLAKY'
            ? 'Suspected flaky'
            : test.classification === 'HIGHLY_FLAKY'
              ? 'Highly flaky'
              : test.classification === 'CONSISTENTLY_FAILING'
                ? 'Consistently failing'
                : 'Insufficient data';
    counts.set(label, (counts.get(label) ?? 0) + 1);
  }
  const data = [...counts.entries()].map(([name, value]) => ({ name, value }));
  if (data.length === 0) return null;
  return (
    <ChartShell title="Classification breakdown">
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={data} layout="vertical" margin={{ left: 90 }}>
          <XAxis type="number" allowDecimals={false} />
          <YAxis type="category" dataKey="name" width={140} />
          <Tooltip />
          <Bar dataKey="value">
            {data.map((entry) => (
              <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name] ?? '#888'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function PassRateTrend({ runs }: { runs: TestRun[] }) {
  const data = [...runs]
    .sort((a, b) => a.run_number - b.run_number)
    .map((run) => ({
      run: `#${run.run_number}`,
      passRate: run.total_tests === 0 ? 0 : (run.passed_tests / run.total_tests) * 100,
    }));
  if (data.length === 0) return null;
  return (
    <ChartShell title="Pass-rate trend per run (%)">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="run" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Line type="monotone" dataKey="passRate" stroke="#2a9d48" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function DurationTrend({ runs }: { runs: TestRun[] }) {
  const data = [...runs]
    .sort((a, b) => a.run_number - b.run_number)
    .map((run) => ({
      run: `#${run.run_number}`,
      avgDuration: run.total_tests === 0 ? 0 : run.total_duration / run.total_tests,
    }));
  if (data.length === 0) return null;
  return (
    <ChartShell title="Average test duration per run (s)">
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="run" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="avgDuration" stroke="#4a6fa5" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}

export function TopFlakyBars({ tests }: { tests: TestListItem[] }) {
  const data = tests.slice(0, 8).map((test) => ({
    name: test.test_name.length > 24 ? `${test.test_name.slice(0, 23)}…` : test.test_name,
    score: test.flakiness_score,
  }));
  if (data.length === 0) return null;
  return (
    <ChartShell title="Top flaky tests by score">
      <ResponsiveContainer width="100%" height={Math.max(200, data.length * 36)}>
        <BarChart data={data} layout="vertical" margin={{ left: 40 }}>
          <XAxis type="number" domain={[0, 100]} />
          <YAxis type="category" dataKey="name" width={170} />
          <Tooltip />
          <Bar dataKey="score" fill="#d64545" />
        </BarChart>
      </ResponsiveContainer>
    </ChartShell>
  );
}
