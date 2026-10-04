import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { listRuns } from '../api/endpoints';
import { sampleRuns } from '../test-fixtures';
import { Runs } from './Runs';

vi.mock('../api/endpoints', () => ({
  listRuns: vi.fn(),
}));

const mockedList = vi.mocked(listRuns);

describe('runs page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedList.mockResolvedValue({ items: sampleRuns, total: 2, limit: 20, offset: 0 });
  });

  it('lists runs with outcome counters', async () => {
    render(
      <MemoryRouter>
        <Runs />
      </MemoryRouter>,
    );
    expect(await screen.findByText('#51')).toBeInTheDocument();
    expect(screen.getByText('#50')).toBeInTheDocument();
    expect(screen.getAllByText('demo-project')).toHaveLength(2);
    expect(screen.getByText(/2 runs/)).toBeInTheDocument();
  });

  it('paginates through runs', async () => {
    mockedList.mockResolvedValue({ items: sampleRuns, total: 45, limit: 20, offset: 0 });
    render(
      <MemoryRouter>
        <Runs />
      </MemoryRouter>,
    );
    await screen.findByText('#51');
    fireEvent.click(screen.getByRole('button', { name: 'Next' }));
    expect(await screen.findByText(/Page 2 of 3/)).toBeInTheDocument();
    expect(mockedList).toHaveBeenLastCalledWith({ limit: 20, offset: 20 });
  });
});
