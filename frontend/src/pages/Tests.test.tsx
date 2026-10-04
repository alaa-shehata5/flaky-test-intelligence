import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { listTests } from '../api/endpoints';
import { sampleFlakyItems } from '../test-fixtures';
import { Tests } from './Tests';

vi.mock('../api/endpoints', () => ({
  listTests: vi.fn(),
}));

const mockedList = vi.mocked(listTests);

function renderPage() {
  return render(
    <MemoryRouter>
      <Tests />
    </MemoryRouter>,
  );
}

describe('tests page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockedList.mockResolvedValue({ items: sampleFlakyItems, total: 2, limit: 20, offset: 0 });
  });

  it('lists tests with pagination info', async () => {
    renderPage();
    expect(await screen.findByText('test_session_refresh')).toBeInTheDocument();
    expect(screen.getByText(/2 tests/)).toBeInTheDocument();
  });

  it('passes search and classification to the API', async () => {
    renderPage();
    await screen.findByText('test_session_refresh');
    fireEvent.change(screen.getByLabelText('Search tests'), { target: { value: 'payment' } });
    await screen.findByText('test_session_refresh');
    expect(mockedList).toHaveBeenLastCalledWith(
      expect.objectContaining({ q: 'payment', offset: 0 }),
    );
    fireEvent.change(screen.getByLabelText('Filter by classification'), {
      target: { value: 'HIGHLY_FLAKY' },
    });
    await screen.findByText('test_session_refresh');
    expect(mockedList).toHaveBeenLastCalledWith(
      expect.objectContaining({ classification: 'HIGHLY_FLAKY' }),
    );
  });

  it.each([
    ['server error', new ApiError(500, 'INTERNAL_ERROR', 'Server blew up', 'r500')],
    ['not found', new ApiError(404, 'NOT_FOUND', 'Missing', 'r404')],
    ['timeout', new ApiError(0, 'NETWORK_ERROR', 'Cannot reach API', '-')],
  ])('handles %s from the API', async (_label, failure) => {
    mockedList.mockRejectedValue(failure);
    renderPage();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent(failure.message);
  });

  it('handles empty responses', async () => {
    mockedList.mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 });
    renderPage();
    expect(await screen.findByText(/No tests match/)).toBeInTheDocument();
  });
});
