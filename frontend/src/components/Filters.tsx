import type { Project } from '../api/types';

export interface FilterValues {
  projectId?: number;
  branch?: string;
  minScore?: number;
}

interface Props {
  projects: Project[];
  branches: string[];
  value: FilterValues;
  onChange: (next: FilterValues) => void;
}

export function DashboardFilters({ projects, branches, value, onChange }: Props) {
  return (
    <div className="toolbar" aria-label="Dashboard filters">
      <select
        value={value.projectId ?? ''}
        onChange={(event) =>
          onChange({
            ...value,
            projectId: event.target.value === '' ? undefined : Number(event.target.value),
          })
        }
        aria-label="Filter by project"
      >
        <option value="">All projects</option>
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
      <select
        value={value.branch ?? ''}
        onChange={(event) =>
          onChange({ ...value, branch: event.target.value === '' ? undefined : event.target.value })
        }
        aria-label="Filter by branch"
      >
        <option value="">All branches</option>
        {branches.map((branch) => (
          <option key={branch} value={branch}>
            {branch}
          </option>
        ))}
      </select>
      <input
        type="number"
        min={0}
        max={100}
        placeholder="Min score"
        value={value.minScore ?? ''}
        onChange={(event) =>
          onChange({
            ...value,
            minScore: event.target.value === '' ? undefined : Number(event.target.value),
          })
        }
        aria-label="Minimum flakiness score"
      />
    </div>
  );
}
