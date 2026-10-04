import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { getSummary, listFlakyTests, listProjects, listRuns, listTests } from '../api/endpoints';
import { sampleFlakyItems, sampleProjects, sampleRuns, sampleSummary } from '../test-fixtures';
import { Dashboard } from './Dashboard';

vi.mock('../api/endpoints', () => ({
  getSummary: vi.fn(),
  listFlakyTests: vi.fn(),
  listProjects: vi.fn(),
  listRuns: vi.fn(),
  listTests: vi.fn(),
}));

function seed() {
  vi.mocked(getSummary).mockResolvedValue(sampleSummary);
  vi.mocked(listProjects).mockResolvedValue({ items: sampleProjects, total: 1 });
  vi.mocked(listRuns).mockResolvedValue({ items: sampleRuns, total: 2, limit: 200, offset: 0 });
  vi.mocked(listTests).mockResolvedValue({ items: [], total: 0, limit: 200, offset: 0 });
  vi.mocked(listFlakyTests).mockResolvedValue({
    items: sampleFlakyItems,
    total: 2,
    limit: 8,
    offset: 0,
  });
}

describe('dashboard page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    seed();
  });

  it('shows KPI cards, charts, and the ranking', async () => {
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(await screen.findByText('51')).toBeInTheDocument();
    expect(screen.getByText('Outcome distribution (scoped runs)')).toBeInTheDocument();
    expect(screen.getByText('Pass-rate trend per run (%)')).toBeInTheDocument();
    expect(screen.getByText('Top flaky tests by score')).toBeInTheDocument();
    expect(screen.getByText('Flaky test ranking')).toBeInTheDocument();
    expect(screen.getByText('test_session_refresh')).toBeInTheDocument();
  });

  it('surfaces backend failures with retry', async () => {
    vi.mocked(getSummary).mockRejectedValue(new ApiError(500, 'INTERNAL_ERROR', 'Down', 'r1'));
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(await screen.findByRole('alert')).toHaveTextContent('Down');
    vi.mocked(getSummary).mockResolvedValue(sampleSummary);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('51')).toBeInTheDocument();
  });

  it('shows an empty state when nothing is in scope', async () => {
    vi.mocked(getSummary).mockResolvedValue({ ...sampleSummary, total_tests: 0 });
    render(
      <MemoryRouter>
        <Dashboard />
      </MemoryRouter>,
    );
    expect(await screen.findByText(/No tests in scope/)).toBeInTheDocument();
  });
});
