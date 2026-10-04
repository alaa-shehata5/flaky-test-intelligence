import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ClassificationBadge, KpiCards, StatusBadge, summaryKpis } from './Badges';
import { sampleSummary } from '../test-fixtures';

describe('KPI cards', () => {
  it('renders all six dashboard metrics', () => {
    render(<KpiCards kpis={summaryKpis(sampleSummary)} />);
    expect(screen.getByText('Total Tests').parentElement).toHaveTextContent('35');
    expect(screen.getByText('CI Runs').parentElement).toHaveTextContent('51');
    expect(screen.getByText('Flaky Tests').parentElement).toHaveTextContent('7');
    expect(screen.getByText('Newly Flaky').parentElement).toHaveTextContent('2');
    expect(screen.getByText('Failing Tests').parentElement).toHaveTextContent('3');
    expect(screen.getByText('Slow Tests').parentElement).toHaveTextContent('2');
  });
});

describe('badges', () => {
  it('labels every classification in human terms', () => {
    const { rerender } = render(<ClassificationBadge value="HIGHLY_FLAKY" />);
    expect(screen.getByText('Highly flaky')).toBeInTheDocument();
    rerender(<ClassificationBadge value="INSUFFICIENT_DATA" />);
    expect(screen.getByText('Insufficient data')).toBeInTheDocument();
    rerender(<ClassificationBadge value="CONSISTENTLY_FAILING" />);
    expect(screen.getByText('Failing')).toBeInTheDocument();
  });

  it('renders statuses uppercased', () => {
    render(<StatusBadge status="failed" />);
    expect(screen.getByText('FAILED')).toBeInTheDocument();
  });
});
