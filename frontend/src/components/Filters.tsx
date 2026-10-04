import type { Classification, Project } from '../api/types';

export interface FilterValues {
  projectId?: number;
  branch?: string;
  workflowName?: string;
  environment?: string;
  dateFrom?: string;
  dateTo?: string;
  classification?: Classification | '';
  minScore?: number;
}

interface Props {
  projects: Project[];
  branches: string[];
  workflows: string[];
  environments: string[];
  value: FilterValues;
  onChange: (next: FilterValues) => void;
}

const CLASSIFICATIONS: Array<Classification | ''> = [
  '',
  'STABLE',
  'MOSTLY_STABLE',
  'SUSPECTED_FLAKY',
  'HIGHLY_FLAKY',
  'CONSISTENTLY_FAILING',
  'INSUFFICIENT_DATA',
];

export function DashboardFilters({
  projects,
  branches,
  workflows,
  environments,
  value,
  onChange,
}: Props) {
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
        value={value.workflowName ?? ''}
        onChange={(event) => onChange({ ...value, workflowName: event.target.value || undefined })}
        aria-label="Filter by workflow"
      >
        <option value="">All workflows</option>
        {workflows.map((workflow) => (
          <option key={workflow} value={workflow}>
            {workflow}
          </option>
        ))}
      </select>
      <select
        value={value.environment ?? ''}
        onChange={(event) => onChange({ ...value, environment: event.target.value || undefined })}
        aria-label="Filter by environment"
      >
        <option value="">All environments</option>
        {environments.map((environment) => (
          <option key={environment} value={environment}>
            {environment}
          </option>
        ))}
      </select>
      <select
        value={value.classification ?? ''}
        onChange={(event) =>
          onChange({
            ...value,
            classification: (event.target.value as Classification | '') || undefined,
          })
        }
        aria-label="Filter by classification"
      >
        {CLASSIFICATIONS.map((classification) => (
          <option key={classification || 'all'} value={classification}>
            {classification || 'All classifications'}
          </option>
        ))}
      </select>
      <label>
        From
        <input
          type="date"
          value={value.dateFrom ?? ''}
          onChange={(event) => onChange({ ...value, dateFrom: event.target.value || undefined })}
          aria-label="Start date"
        />
      </label>
      <label>
        To
        <input
          type="date"
          value={value.dateTo ?? ''}
          onChange={(event) => onChange({ ...value, dateTo: event.target.value || undefined })}
          aria-label="End date"
        />
      </label>
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
