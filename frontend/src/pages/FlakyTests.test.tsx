import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { listFlakyTests, listProjects, listRuns } from '../api/endpoints';
import { sampleFlakyItems, sampleProjects, sampleRuns } from '../test-fixtures';
import { FlakyTests } from './FlakyTests';

vi.mock('../api/endpoints', () => ({
  listFlakyTests: vi.fn(),
  listProjects: vi.fn(),
  listRuns: vi.fn(),
}));

describe('flaky tests page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(listProjects).mockResolvedValue({ items: sampleProjects, total: 1 });
    vi.mocked(listRuns).mockResolvedValue({ items: sampleRuns, total: 2, limit: 200, offset: 0 });
    vi.mocked(listFlakyTests).mockResolvedValue({
      items: sampleFlakyItems,
      total: 2,
      limit: 200,
      offset: 0,
    });
  });

  it('renders filters and the ranking table', async () => {
    render(
      <MemoryRouter>
        <FlakyTests />
      </MemoryRouter>,
    );
    expect(screen.getByLabelText('Filter by project')).toBeInTheDocument();
    expect(await screen.findByText('test_session_refresh')).toBeInTheDocument();
    expect(vi.mocked(listFlakyTests)).toHaveBeenCalledWith(
      expect.objectContaining({ sort: 'score_desc', limit: 200 }),
    );
  });
});
