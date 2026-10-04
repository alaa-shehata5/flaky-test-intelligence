# Data Model (planned — Phase 0)

> Status: initial skeleton. Will be completed in Phase 14 after migrations
> are implemented and verified.

## Planned sections

- [ ] Tables: `projects`, `test_runs`, `test_cases`, `test_executions`
- [ ] Columns per table (see `docs/requirements.md` FR-4 + Phase 2 spec)
- [ ] Relationships (project → runs, project → cases, run/case → executions)
- [ ] Test identity: `project::classname::test_name` (unique key on `test_cases.unique_key`)
- [ ] Status enum: `passed | failed | error | skipped`
- [ ] Indexes: unique identity, `test_case_id`, `run_id`, timestamps, branch, composite dashboard indexes
- [ ] Alembic migration strategy
