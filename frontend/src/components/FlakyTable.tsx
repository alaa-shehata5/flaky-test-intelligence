import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { Classification } from '../api/types';
import { listFlakyTests } from '../api/endpoints';
import { EmptyState, ErrorState, Loading } from './States';
import { ClassificationBadge } from './Badges';
import { useApi } from '../hooks/useApi';

const CLASSIFICATIONS: Array<Classification | ''> = [
  '',
  'SUSPECTED_FLAKY',
  'HIGHLY_FLAKY',
  'CONSISTENTLY_FAILING',
  'MOSTLY_STABLE',
  'STABLE',
  'INSUFFICIENT_DATA',
];

const SORTS = [
  { value: 'score_desc', label: 'Score (high first)' },
  { value: 'score_asc', label: 'Score (low first)' },
  { value: 'pass_rate_asc', label: 'Pass rate (low first)' },
  { value: 'pass_rate_desc', label: 'Pass rate (high first)' },
  { value: 'name_asc', label: 'Name (A–Z)' },
] as const;

type SortValue = (typeof SORTS)[number]['value'];

export interface FlakyTableFilters {
  project_id?: number;
  branch?: string;
  workflow_name?: string;
  environment?: string;
  date_from?: string;
  date_to?: string;
  classificationFilter?: Classification | '';
  minScore?: number;
  showControls?: boolean;
  pageSize?: number;
}

const DEFAULT_PAGE_SIZE = 15;

export function FlakyTable({
  project_id,
  branch,
  workflow_name,
  environment,
  date_from,
  date_to,
  classificationFilter,
  minScore,
  showControls = true,
  pageSize = DEFAULT_PAGE_SIZE,
}: FlakyTableFilters) {
  const [query, setQuery] = useState('');
  const [localClassification, setLocalClassification] = useState<Classification | ''>('');
  const [sort, setSort] = useState<SortValue>('score_desc');
  const [page, setPage] = useState(0);
  const classification = classificationFilter ?? localClassification;

  // Reset to the first page whenever the scope changes. This render-phase
  // adjustment (re-render and bail out) is the documented alternative to
  // resetting inside an effect.
  const scopeKey = [
    project_id,
    branch,
    workflow_name,
    environment,
    date_from,
    date_to,
    classification,
    minScore,
    query,
    sort,
    pageSize,
  ].join('|');
  const [prevScopeKey, setPrevScopeKey] = useState(scopeKey);
  if (prevScopeKey !== scopeKey) {
    setPrevScopeKey(scopeKey);
    setPage(0);
  }

  const { data, loading, error, retry } = useApi(
    () =>
      listFlakyTests({
        project_id,
        branch,
        workflow_name,
        environment,
        date_from,
        date_to,
        classification: classification || undefined,
        minimum_score: minScore,
        q: query || undefined,
        sort,
        limit: pageSize,
        offset: page * pageSize,
      }),
    [
      project_id,
      branch,
      workflow_name,
      environment,
      date_from,
      date_to,
      classification,
      minScore,
      query,
      sort,
      page,
      pageSize,
    ],
  );

  const totalPages = Math.max(1, Math.ceil((data?.total ?? 0) / pageSize));
  const pageItems = data?.items ?? [];

  return (
    <div>
      {showControls && (
        <div className="toolbar">
          <input
            type="search"
            placeholder="Search flaky tests…"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value);
              setPage(0);
            }}
            aria-label="Search flaky tests"
          />
          {classificationFilter === undefined && (
            <select
              value={localClassification}
              onChange={(event) => {
                setLocalClassification(event.target.value as Classification | '');
                setPage(0);
              }}
              aria-label="Filter by classification"
            >
              {CLASSIFICATIONS.map((value) => (
                <option key={value || 'all'} value={value}>
                  {value || 'All classifications'}
                </option>
              ))}
            </select>
          )}
          <select
            value={sort}
            onChange={(event) => setSort(event.target.value as SortValue)}
            aria-label="Sort flaky tests"
          >
            {SORTS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      )}

      {loading && <Loading label="Loading flaky tests…" />}
      {error && <ErrorState message={error.message} requestId={error.requestId} onRetry={retry} />}
      {data && data.total === 0 && (
        <EmptyState message="No flaky tests match the current filters." />
      )}
      {pageItems.length > 0 && (
        <>
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Suite</th>
                <th>Classification</th>
                <th>Score</th>
                <th>Pass rate</th>
                <th>Failure rate</th>
                <th>Runs</th>
                <th>Avg duration</th>
                <th>Last seen</th>
                <th>Trend</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map((test) => (
                <tr key={test.test_case_id}>
                  <td>
                    <Link to={`/tests/${test.test_case_id}`}>{test.test_name}</Link>
                    <div className="muted">{test.classname}</div>
                    {test.newly_flaky && <span className="badge badge-new">newly flaky</span>}
                  </td>
                  <td>{test.suite_name ?? '—'}</td>
                  <td>
                    <ClassificationBadge value={test.classification} />
                  </td>
                  <td>{test.flakiness_score.toFixed(1)}</td>
                  <td>{(test.pass_rate * 100).toFixed(1)}%</td>
                  <td>{(test.failure_rate * 100).toFixed(1)}%</td>
                  <td>{test.sample_size}</td>
                  <td>{test.avg_duration.toFixed(2)}s</td>
                  <td>{new Date(test.last_seen_at).toLocaleDateString()}</td>
                  <td>
                    {test.newly_flaky || test.score_delta > 1
                      ? '↗ worsening'
                      : test.score_delta < -1
                        ? '↘ improving'
                        : '→ stable'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pagination">
            <button type="button" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
              Previous
            </button>
            <span>
              Page {page + 1} of {totalPages} ({data?.total ?? 0} tests)
            </span>
            <button
              type="button"
              disabled={page + 1 >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}
