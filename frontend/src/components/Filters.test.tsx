import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DashboardFilters } from './Filters';
import { sampleProjects } from '../test-fixtures';

const PROPS = {
  projects: sampleProjects,
  branches: ['dev', 'main'],
  workflows: ['ci'],
  environments: ['staging'],
};

describe('dashboard filters', () => {
  it('emits project, branch, and min-score changes', () => {
    const onChange = vi.fn();
    render(<DashboardFilters {...PROPS} value={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Filter by project'), { target: { value: '1' } });
    expect(onChange).toHaveBeenLastCalledWith({ projectId: 1 });
    fireEvent.change(screen.getByLabelText('Filter by branch'), { target: { value: 'dev' } });
    expect(onChange).toHaveBeenLastCalledWith({ branch: 'dev' });
    fireEvent.change(screen.getByLabelText('Minimum flakiness score'), { target: { value: '40' } });
    expect(onChange).toHaveBeenLastCalledWith({ minScore: 40 });
  });

  it('emits workflow, environment, classification, and date changes', () => {
    const onChange = vi.fn();
    render(<DashboardFilters {...PROPS} value={{}} onChange={onChange} />);
    fireEvent.change(screen.getByLabelText('Filter by workflow'), { target: { value: 'ci' } });
    expect(onChange).toHaveBeenLastCalledWith({ workflowName: 'ci' });
    fireEvent.change(screen.getByLabelText('Filter by environment'), {
      target: { value: 'staging' },
    });
    expect(onChange).toHaveBeenLastCalledWith({ environment: 'staging' });
    fireEvent.change(screen.getByLabelText('Filter by classification'), {
      target: { value: 'HIGHLY_FLAKY' },
    });
    expect(onChange).toHaveBeenLastCalledWith({ classification: 'HIGHLY_FLAKY' });
    fireEvent.change(screen.getByLabelText('Start date'), { target: { value: '2026-01-01' } });
    expect(onChange).toHaveBeenLastCalledWith({ dateFrom: '2026-01-01' });
    fireEvent.change(screen.getByLabelText('End date'), { target: { value: '2026-02-01' } });
    expect(onChange).toHaveBeenLastCalledWith({ dateTo: '2026-02-01' });
  });

  it('reflects the current selection', () => {
    render(
      <DashboardFilters
        {...PROPS}
        value={{ projectId: 1, branch: 'main', minScore: 40 }}
        onChange={() => {}}
      />,
    );
    expect(screen.getByLabelText('Filter by project')).toHaveValue('1');
    expect(screen.getByLabelText('Minimum flakiness score')).toHaveValue(40);
  });
});
