import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { DashboardFilters } from './Filters';
import { sampleProjects } from '../test-fixtures';

describe('dashboard filters', () => {
  it('emits project, branch, and min-score changes', () => {
    const onChange = vi.fn();
    render(
      <DashboardFilters
        projects={sampleProjects}
        branches={['dev', 'main']}
        value={{}}
        onChange={onChange}
      />,
    );
    fireEvent.change(screen.getByLabelText('Filter by project'), { target: { value: '1' } });
    expect(onChange).toHaveBeenLastCalledWith({ projectId: 1 });
    fireEvent.change(screen.getByLabelText('Filter by branch'), { target: { value: 'dev' } });
    expect(onChange).toHaveBeenLastCalledWith({ branch: 'dev' });
    fireEvent.change(screen.getByLabelText('Minimum flakiness score'), { target: { value: '40' } });
    expect(onChange).toHaveBeenLastCalledWith({ minScore: 40 });
  });

  it('reflects the current selection', () => {
    render(
      <DashboardFilters
        projects={sampleProjects}
        branches={['main']}
        value={{ projectId: 1, branch: 'main', minScore: 40 }}
        onChange={() => {}}
      />,
    );
    expect(screen.getByLabelText('Filter by project')).toHaveValue('1');
    expect(screen.getByLabelText('Minimum flakiness score')).toHaveValue(40);
  });
});
