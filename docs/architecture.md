# Architecture (planned — Phase 0)

> Status: initial skeleton. Will be completed in Phase 14 with final
> implementation details and a Mermaid diagram. No fake details below —
> only the intended structure.

## Planned sections

- [ ] System overview + Mermaid diagram
- [ ] Components: FastAPI backend, PostgreSQL, React/Vite frontend, CLI (`flakyctl`), ingestion pipeline, analysis engine
- [ ] Data flow: JUnit XML → parser → normalized results → PostgreSQL → analysis → REST API → dashboard
- [ ] Backend layout (`backend/app/...`)
- [ ] Configuration & environments
- [ ] Deployment: Docker Compose services, Codespaces, CI
- [ ] Key decisions (ADR-style): why PostgreSQL, why server-computed scores, why deterministic demo data

## Intended data flow

```text
JUnit XML
  ↓
Secure parser (defusedxml)
  ↓
Normalized TestRunResult
  ↓
Persistence service → PostgreSQL (projects, test_runs, test_cases, test_executions)
  ↓
Analysis engine (statistics → score → classification → trends)
  ↓
REST API (/api/...)
  ↓
React dashboard
```
