import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { DurationTrend, OutcomeDonut, PassRateTrend, SeverityBars, TopFlakyBars } from './Charts';
import { sampleFlakyItems, sampleRuns } from '../test-fixtures';

describe('dashboard charts', () => {
  it('renders every main chart shell with data', () => {
    render(
      <>
        <OutcomeDonut runs={sampleRuns} />
        <SeverityBars tests={sampleFlakyItems} />
        <PassRateTrend runs={sampleRuns} />
        <DurationTrend runs={sampleRuns} />
        <TopFlakyBars tests={sampleFlakyItems} />
      </>,
    );
    expect(screen.getByText('Outcome distribution (scoped runs)')).toBeInTheDocument();
    expect(screen.getByText('Classification breakdown')).toBeInTheDocument();
    expect(screen.getByText('Pass-rate trend per run (%)')).toBeInTheDocument();
    expect(screen.getByText('Average test duration per run (s)')).toBeInTheDocument();
    expect(screen.getByText('Top flaky tests by score')).toBeInTheDocument();
  });

  it('renders nothing without data', () => {
    const { container } = render(
      <>
        <OutcomeDonut runs={[]} />
        <SeverityBars tests={[]} />
        <PassRateTrend runs={[]} />
        <DurationTrend runs={[]} />
        <TopFlakyBars tests={[]} />
      </>,
    );
    expect(container).toBeEmptyDOMElement();
  });
});
