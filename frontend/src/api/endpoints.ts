import { apiFetch } from './client';
import type {
  Classification,
  DashboardSummary,
  FlakyList,
  HistoryPoint,
  Project,
  ProjectList,
  RunList,
  TestDetail,
  TestList,
  TestRun,
} from './types';

export type TestFilters = {
  project_id?: number;
  branch?: string;
  workflow_name?: string;
  environment?: string;
  date_from?: string;
  date_to?: string;
  suite?: string;
  classification?: Classification;
  minimum_score?: number;
  q?: string;
  limit?: number;
  offset?: number;
};

export type FlakyFilters = TestFilters & {
  sort?: 'score_desc' | 'score_asc' | 'pass_rate_asc' | 'pass_rate_desc' | 'name_asc';
};

export type RunFilters = {
  project_id?: number;
  branch?: string;
  workflow_name?: string;
  environment?: string;
  date_from?: string;
  date_to?: string;
  limit?: number;
  offset?: number;
};

export type SummaryFilters = {
  project_id?: number;
  branch?: string;
  workflow_name?: string;
  environment?: string;
  date_from?: string;
  date_to?: string;
  classification?: Classification;
  minimum_score?: number;
};

export function listProjects(): Promise<ProjectList> {
  return apiFetch<ProjectList>('/api/projects');
}

export function getProject(id: number): Promise<Project> {
  return apiFetch<Project>(`/api/projects/${id}`);
}

export function listRuns(filters: RunFilters = {}): Promise<RunList> {
  return apiFetch<RunList>('/api/runs', filters);
}

export function getRun(id: number): Promise<TestRun> {
  return apiFetch<TestRun>(`/api/runs/${id}`);
}

export function listTests(filters: TestFilters = {}): Promise<TestList> {
  return apiFetch<TestList>('/api/tests', filters);
}

export function getTest(id: number): Promise<TestDetail> {
  return apiFetch<TestDetail>(`/api/tests/${id}`);
}

export function getTestHistory(id: number): Promise<HistoryPoint[]> {
  return apiFetch<HistoryPoint[]>(`/api/tests/${id}/history`);
}

export function listFlakyTests(filters: FlakyFilters = {}): Promise<FlakyList> {
  return apiFetch<FlakyList>('/api/flaky-tests', filters);
}

export function getSummary(filters: SummaryFilters = {}): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>('/api/dashboard/summary', filters);
}
