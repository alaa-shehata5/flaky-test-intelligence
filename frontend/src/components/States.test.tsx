import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { EmptyState, ErrorState, Loading } from './States';

describe('shared states', () => {
  it('renders a loading indicator', () => {
    render(<Loading label="Loading tests…" />);
    expect(screen.getByRole('status')).toHaveTextContent('Loading tests…');
  });

  it('renders an empty state', () => {
    render(<EmptyState message="No tests match the current filters." />);
    expect(screen.getByText('No data')).toBeInTheDocument();
    expect(screen.getByText('No tests match the current filters.')).toBeInTheDocument();
  });

  it('renders an error with request id and working retry', () => {
    const onRetry = vi.fn();
    render(<ErrorState message="Boom" requestId="req-1" onRetry={onRetry} />);
    expect(screen.getByRole('alert')).toHaveTextContent('Boom');
    expect(screen.getByText(/Request ID: req-1/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });
});
