import type { Classification, DashboardSummary } from '../api/types';

export function classificationLabel(value: Classification): string {
  switch (value) {
    case 'INSUFFICIENT_DATA':
      return 'Insufficient data';
    case 'STABLE':
      return 'Stable';
    case 'MOSTLY_STABLE':
      return 'Mostly stable';
    case 'SUSPECTED_FLAKY':
      return 'Suspected flaky';
    case 'HIGHLY_FLAKY':
      return 'Highly flaky';
    case 'CONSISTENTLY_FAILING':
      return 'Failing';
  }
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status.toLowerCase()}`}>{status.toUpperCase()}</span>;
}

export function ClassificationBadge({ value }: { value: Classification }) {
  return <span className={`badge class-${value.toLowerCase()}`}>{classificationLabel(value)}</span>;
}

export interface Kpi {
  label: string;
  value: string | number;
  hint?: string;
}

export function summaryKpis(summary: DashboardSummary): Kpi[] {
  const flaky = summary.suspected_flaky_tests + summary.highly_flaky_tests;
  return [
    { label: 'Total Tests', value: summary.total_tests },
    { label: 'CI Runs', value: summary.total_runs },
    { label: 'Flaky Tests', value: flaky, hint: 'suspected + highly flaky' },
    { label: 'Newly Flaky', value: summary.newly_flaky_tests },
    { label: 'Failing Tests', value: summary.consistently_failing_tests },
    { label: 'Slow Tests', value: summary.slow_tests },
  ];
}

export function KpiCards({ kpis }: { kpis: Kpi[] }) {
  return (
    <div className="kpi-grid">
      {kpis.map((kpi) => (
        <div key={kpi.label} className="kpi-card">
          <div className="kpi-label">{kpi.label}</div>
          <div className="kpi-value">{kpi.value}</div>
          {kpi.hint && <div className="muted">{kpi.hint}</div>}
        </div>
      ))}
    </div>
  );
}
