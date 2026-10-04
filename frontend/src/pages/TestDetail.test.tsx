import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError } from '../api/client';
import { getTest, getTestHistory } from '../api/endpoints';
import { sampleDetail, sampleHistory } from '../test-fixtures';
import { TestDetail } from './TestDetail';

vi.mock('../api/endpoints', () => ({
  getTest: vi.fn(),
  getTestHistory: vi.fn(),
}));

function renderDetail() {
  return render(
    <MemoryRouter initialEntries={['/tests/23']}>
      <Routes>
        <Route path="/tests/:id" element={<TestDetail />} />
      </Routes>
    </MemoryRouter>,
  );
}

describe('test detail page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(getTest).mockResolvedValue(sampleDetail);
    vi.mocked(getTestHistory).mockResolvedValue(sampleHistory);
  });

  it('shows identity, stats, history, and failure messages', async () => {
    renderDetail();
    expect(await screen.findByText('test_session_refresh')).toBeInTheDocument();
    expect(
      screen.getByText('demo-project::tests.test_auth::test_session_refresh'),
    ).toBeInTheDocument();
    expect(screen.getByText('Highly flaky')).toBeInTheDocument();
    expect(screen.getByText('82.03')).toBeInTheDocument();
    expect(screen.getByText('Flakiness score history')).toBeInTheDocument();
    expect(screen.getByText('Duration history (s)')).toBeInTheDocument();
    expect(screen.getByText('Recent failure messages')).toBeInTheDocument();
    expect(screen.getByText('AssertionError: race on refresh')).toBeInTheDocument();
    expect(screen.getAllByText('FAILED')).not.toHaveLength(0);
  });

  it('dedupes repeated failure messages', async () => {
    renderDetail();
    await screen.findByText('Recent failure messages');
    // The same message on runs 2 and 3 is shown once.
    expect(screen.getAllByText('AssertionError: race on refresh')).toHaveLength(1);
  });

  it('shows an error state when the test does not exist', async () => {
    vi.mocked(getTest).mockRejectedValue(
      new ApiError(404, 'TEST_NOT_FOUND', 'test 23 not found', 'r404'),
    );
    renderDetail();
    const alert = await screen.findByRole('alert');
    expect(alert).toHaveTextContent('test 23 not found');
  });
});
