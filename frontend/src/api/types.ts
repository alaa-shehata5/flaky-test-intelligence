/** Backend API shapes (mirror backend/app/api/schemas.py). */

export type Classification =
  | 'INSUFFICIENT_DATA'
  | 'STABLE'
  | 'MOSTLY_STABLE'
  | 'SUSPECTED_FLAKY'
  | 'HIGHLY_FLAKY'
  | 'CONSISTENTLY_FAILING';

export type TestStatus = 'passed' | 'failed' | 'error' | 'skipped';

export interface Project {
  id: number;
  name: string;
  repository: string | null;
  created_at: string;
  run_count: number;
  test_count: number;
}

export interface ProjectList {
  items: Project[];
  total: number;
}

export interface TestRun {
  id: number;
  project_id: number;
  project_name: string;
  run_number: number;
  branch: string;
  commit_sha: string | null;
  workflow_name: string | null;
  environment: string | null;
  started_at: string | null;
  finished_at: string | null;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  error_tests: number;
  total_duration: number;
  source: string;
  created_at: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type RunList = Page<TestRun>;

export interface TestListItem {
  test_case_id: number;
  unique_key: string;
  project_id: number;
  project_name: string;
  suite_name: string | null;
  classname: string;
  test_name: string;
  classification: Classification;
  flakiness_score: number;
  pass_rate: number;
  sample_size: number;
  avg_duration: number;
  last_seen_at: string;
  newly_flaky: boolean;
  is_slow: boolean;
}

export type TestList = Page<TestListItem>;
export type FlakyList = Page<TestListItem>;

export interface TestDetail extends TestListItem {
  passed: number;
  failed: number;
  error: number;
  skipped: number;
  failure_rate: number;
  duration_min: number;
  duration_max: number;
  duration_mean: number;
  duration_median: number;
  duration_p95: number;
  duration_stddev: number;
  inconsistency: number;
  recency: number;
  duration_instability: number;
  persistently_flaky: boolean;
  pass_rate_delta: number;
  failure_rate_delta: number;
  duration_delta: number;
  score_delta: number;
}

export interface HistoryPoint {
  run_id: number;
  run_number: number;
  branch: string;
  status: TestStatus;
  duration: number;
  executed_at: string;
  score: number;
  failure_message: string | null;
  failure_type: string | null;
}

export interface DashboardSummary {
  total_tests: number;
  total_runs: number;
  stable_tests: number;
  suspected_flaky_tests: number;
  highly_flaky_tests: number;
  consistently_failing_tests: number;
  slow_tests: number;
  newly_flaky_tests: number;
  average_pass_rate: number;
}

export interface ApiErrorBody {
  error: string;
  message: string;
  request_id: string;
}
