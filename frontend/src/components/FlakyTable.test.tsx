import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { listFlakyTests } from '../api/endpoints';
import { sampleFlakyItems } from '../test-fixtures';
import { FlakyTable } from './FlakyTable';

vi.mock('../api/endpoints', () => ({
  listFlakyTests: vi.fn(),
}));

const mockedList = vi.mocked(listFlakyTests);

function renderTable() {
  return render(
    <MemoryRouter>
      <FlakyTable />
    </MemoryRouter>,
  );
}

describe('flaky table', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedList.mockResolvedValue({ items: sampleFlakyItems, total: 2, limit: 200, offset: 0 });
  });

  it('renders ranked rows with all columns', async () => {
    renderTable();
    expect(await screen.findByText('test_session_refresh')).toBeInTheDocument();
    expect(screen.getByText('test_payment_timeout')).toBeInTheDocument();
    expect(screen.getByText('newly flaky')).toBeInTheDocument();
    expect(screen.getByText('82.0')).toBeInTheDocument();
    expect(screen.getByText('Suite')).toBeInTheDocument();
    expect(screen.getByText('Avg duration')).toBeInTheDocument();
  });

  it('filters client-side as the user types', async () => {
    renderTable();
    await screen.findByText('test_session_refresh');
    fireEvent.change(screen.getByLabelText('Search flaky tests'), {
      target: { value: 'payment' },
    });
    await waitFor(() => {
      expect(screen.queryByText('test_session_refresh')).not.toBeInTheDocument();
    });
    expect(screen.getByText('test_payment_timeout')).toBeInTheDocument();
    expect(mockedList).toHaveBeenCalledTimes(1);
  });

  it('shows an empty state when nothing matches', async () => {
    mockedList.mockResolvedValue({ items: [], total: 0, limit: 200, offset: 0 });
    renderTable();
    expect(await screen.findByText(/No flaky tests match/)).toBeInTheDocument();
  });

  it('shows an error state with retry on API failure', async () => {
    mockedList.mockRejectedValue(new ApiError(500, 'INTERNAL_ERROR', 'Boom', 'req-9'));
    renderTable();
    expect(await screen.findByRole('alert')).toHaveTextContent('Boom');
    expect(screen.getByText(/Request ID: req-9/)).toBeInTheDocument();
    mockedList.mockResolvedValue({ items: sampleFlakyItems, total: 2, limit: 200, offset: 0 });
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(await screen.findByText('test_session_refresh')).toBeInTheDocument();
  });
});
