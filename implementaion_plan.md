# Flaky Test Intelligence Platform

## Phased Implementation Plan for Codex

---

# ROLE

Act as a senior:

* QA Automation Engineer
* SDET
* Backend Engineer
* Frontend Engineer
* Data Engineer
* DevOps Engineer
* Test Infrastructure Engineer

Your job is to build a complete, professional **Flaky Test Intelligence Platform**.

This is a portfolio project intended to demonstrate real-world skills in:

* QA automation
* test infrastructure
* API testing
* Python
* SQL
* PostgreSQL
* data analysis
* CI/CD
* Docker
* GitHub Actions
* frontend development
* observability
* software architecture

Do not treat this as a beginner tutorial.

Build it as a small but credible engineering product.

---

# PROJECT CONCEPT

The platform collects automated test results from multiple CI runs, stores their historical execution data, analyzes their behavior, detects potentially flaky tests, and presents the results in a professional dashboard.

Example:

```text
Test: test_payment_timeout

Run 1 → PASS
Run 2 → PASS
Run 3 → FAIL
Run 4 → PASS
Run 5 → FAIL
Run 6 → PASS
Run 7 → PASS
Run 8 → FAIL
```

The system should recognize that this test behaves inconsistently.

It should NOT simply classify every failing test as flaky.

A test that fails every time is more likely to be consistently broken than flaky.

---

# CORE TECHNOLOGY

Use:

### Backend

* Python 3.12+
* FastAPI
* Pydantic
* SQLAlchemy
* Alembic
* PostgreSQL

### Testing

* pytest
* pytest-cov
* httpx

### Frontend

* React
* TypeScript
* Vite
* Recharts or Apache ECharts

### DevOps

* Docker
* Docker Compose
* GitHub Actions
* GitHub Codespaces

### Code Quality

* Ruff
* ESLint
* Prettier

---

# DEVELOPMENT RULES

Follow these rules throughout the entire project.

1. Work one phase at a time.
2. Work one task at a time.
3. Do not skip tasks.
4. After each task, verify the implementation.
5. Fix errors before moving forward.
6. Do not fabricate test results.
7. Do not fabricate screenshots.
8. Do not fabricate performance metrics.
9. Clearly label synthetic demo data.
10. Never commit secrets.
11. Keep the architecture simple and maintainable.
12. Write tests alongside important functionality.
13. Document important architectural decisions.
14. Do not replace working code unnecessarily.
15. Inspect the existing repository before modifying it.
16. If a decision is ambiguous, choose the simplest production-credible solution.
17. Do not silently reduce the scope.
18. Keep the project runnable throughout development.

---

# EXECUTION MODEL

For every phase use this workflow:

```text
PHASE
  ↓
TASK
  ↓
IMPLEMENT
  ↓
TEST
  ↓
VERIFY
  ↓
MARK COMPLETE
  ↓
NEXT TASK
```

At the end of every phase provide:

```text
Phase status:
Completed tasks:
Tests:
Known issues:
Files changed:
Ready for next phase: YES/NO
```

Do not move to the next phase if the current phase has broken tests or unresolved critical issues.

---

# PHASE 0 — PROJECT RECONNAISSANCE

### Description

Before writing code, understand the repository and establish the project foundation.

---

## TASK 0 — Inspect the Repository

Inspect:

* existing files
* existing source code
* package managers
* Python configuration
* Node configuration
* Git configuration
* existing tests
* Docker configuration
* CI configuration

Determine whether this is an empty repository or an existing project.

Do not delete useful existing work.

### Deliverable

Create a short internal/project assessment describing:

```text
Repository status
Existing technologies
Existing useful files
Potential conflicts
Recommended starting structure
```

---

## TASK 1 — Define Project Requirements

Create:

```text
docs/requirements.md
```

Document:

* problem statement
* target users
* functional requirements
* non-functional requirements
* major features
* constraints
* MVP scope
* future scope

### Verification

Make sure every major requirement maps to a later implementation task.

---

## TASK 2 — Create Initial Repository Structure

Create the initial structure:

```text
backend/
frontend/
cli/
demo/
docs/
scripts/
tests/
.github/
.devcontainer/
```

Do not implement business logic yet.

### Verification

Confirm the structure is clean and sensible.

---

## TASK 3 — Create Initial Documentation

Create:

```text
README.md
docs/architecture.md
docs/data-model.md
docs/detection-algorithm.md
```

The documents can initially contain planned sections.

Do not fill them with fake implementation details.

---

# PHASE 0 GATE

Before continuing:

* [ ] Repository inspected
* [ ] Requirements documented
* [ ] Structure created
* [ ] Initial documentation exists
* [ ] No useful existing work destroyed

---

# PHASE 1 — BACKEND FOUNDATION

### Description

Build the backend skeleton and establish configuration, application startup, database connectivity, and health monitoring.

---

## TASK 0 — Initialize Python Project

Configure:

```text
Python 3.12+
FastAPI
Pydantic
SQLAlchemy
Alembic
pytest
pytest-cov
httpx
Ruff
```

Create:

```text
backend/pyproject.toml
```

Use modern Python packaging practices.

---

## TASK 1 — Application Configuration

Create centralized configuration.

Support:

```text
DATABASE_URL
APP_ENV
LOG_LEVEL
CORS_ORIGINS
MIN_SAMPLE_SIZE
FLAKY_SCORE_THRESHOLD
HIGHLY_FLAKY_SCORE_THRESHOLD
SLOW_TEST_THRESHOLD
```

Create:

```text
.env.example
```

Never commit `.env`.

---

## TASK 2 — FastAPI Application

Create:

```text
backend/app/main.py
```

Implement:

```http
GET /health
```

Example:

```json
{
  "status": "ok"
}
```

---

## TASK 3 — Logging

Implement structured application logging.

Include:

* timestamp
* level
* logger
* request ID where appropriate

Do not log:

* passwords
* tokens
* secrets
* database credentials

---

## TASK 4 — Database Connection

Configure PostgreSQL with SQLAlchemy.

Create:

```text
backend/app/db/
```

Implement:

* engine
* session management
* base model
* dependency injection

---

## TASK 5 — Alembic

Configure Alembic.

Verify:

```bash
alembic upgrade head
```

works.

---

# PHASE 1 GATE

Verify:

```text
[ ] FastAPI starts
[ ] /health works
[ ] PostgreSQL connects
[ ] Alembic works
[ ] Configuration works
[ ] Tests execute
[ ] Ruff passes
```

---

# PHASE 2 — DATABASE MODEL

### Description

Create the relational data model required to store projects, CI runs, tests, and individual executions.

---

## TASK 0 — Projects Table

Create:

```text
projects
```

Fields:

```text
id
name
repository
created_at
```

---

## TASK 1 — Test Runs Table

Create:

```text
test_runs
```

Fields:

```text
id
project_id
run_number
commit_sha
branch
workflow_name
environment
started_at
finished_at
total_tests
passed_tests
failed_tests
skipped_tests
error_tests
total_duration
source
created_at
```

---

## TASK 2 — Test Cases Table

Create:

```text
test_cases
```

Fields:

```text
id
project_id
suite_name
classname
test_name
unique_key
first_seen_at
last_seen_at
```

The unique key must identify the logical test.

Example:

```text
demo-project::tests.test_auth::test_valid_login
```

---

## TASK 3 — Test Executions Table

Create:

```text
test_executions
```

Fields:

```text
id
run_id
test_case_id
status
duration
failure_message
failure_type
executed_at
```

Statuses:

```text
passed
failed
error
skipped
```

---

## TASK 4 — Database Indexes

Add useful indexes for:

* unique test identity
* test case ID
* run ID
* timestamps
* branch

Consider composite indexes for dashboard queries.

---

## TASK 5 — Migrations

Create Alembic migration.

Verify:

```bash
alembic upgrade head
```

and:

```bash
alembic downgrade base
```

work correctly.

---

## TASK 6 — Database Tests

Test:

* model creation
* relationships
* constraints
* unique test identity
* insertion
* retrieval

---

# PHASE 2 GATE

```text
[ ] All tables exist
[ ] Relationships work
[ ] Indexes exist
[ ] Migrations work
[ ] Database tests pass
```

---

# PHASE 3 — JUNIT INGESTION ENGINE

### Description

Build the core ingestion system.

The platform's first input format will be JUnit XML.

---

## TASK 0 — Define JUnit Data Model

Create internal normalized structures for:

```text
TestSuite
TestCaseResult
TestRunResult
```

Normalize statuses to:

```text
passed
failed
error
skipped
```

---

## TASK 1 — Secure XML Parser

Implement a secure JUnit XML parser.

It must handle:

* suites
* test cases
* classname
* test name
* duration
* failures
* errors
* skipped tests

Protect against unsafe XML features such as:

* XXE
* entity expansion
* malformed XML

---

## TASK 2 — Test Identity

Implement deterministic test identity:

```text
project::classname::test_name
```

Test:

* same test across runs → same identity
* different tests → different identity
* duplicate XML records handled safely

---

## TASK 3 — JUnit Validation

Reject:

* malformed XML
* unsupported structures
* missing required test information

Return useful errors.

---

## TASK 4 — Persistence Service

Convert parsed JUnit data into:

```text
project
run
test cases
executions
```

Store them in PostgreSQL.

---

## TASK 5 — Upload API

Implement:

```http
POST /api/runs/upload
```

Accept:

```text
JUnit XML
project
branch
commit_sha
run_number
workflow_name
environment
```

---

## TASK 6 — Ingestion Tests

Test:

* valid XML
* multiple suites
* passed tests
* failed tests
* errors
* skipped tests
* malformed XML
* empty XML
* missing metadata
* duplicate tests
* missing duration

---

# PHASE 3 GATE

The following must work:

```text
JUnit XML
    ↓
Parser
    ↓
Normalized data
    ↓
Database
```

And:

```text
POST /api/runs/upload
```

must successfully create historical test data.

---

# PHASE 4 — STATISTICAL ANALYSIS ENGINE

### Description

This is the most important part of the project.

Build the engine that turns raw test history into meaningful QA intelligence.

---

## TASK 0 — Basic Statistics

For every test calculate:

```text
sample size
pass count
failure count
error count
skip count
pass rate
failure rate
```

---

## TASK 1 — Duration Statistics

Calculate:

```text
minimum duration
maximum duration
average duration
median duration
p95 duration
standard deviation
```

---

## TASK 2 — Outcome Inconsistency

Implement a documented inconsistency measure.

A starting model may be:

```text
inconsistency =
1 - abs(pass_rate - 0.5) * 2
```

Normalize appropriately.

Do not blindly accept this formula if testing reveals a better approach.

Document the final formula in:

```text
docs/detection-algorithm.md
```

---

## TASK 3 — Recency Weighting

Recent failures should matter more than very old failures.

Implement a configurable recency mechanism.

Use a clear mathematical approach such as exponential decay.

Document:

* formula
* parameters
* reasoning

---

## TASK 4 — Duration Instability

Calculate whether test duration is unstable.

Use a defensible metric such as:

* standard deviation
* coefficient of variation
* percentile spread

Do not call a slow test flaky merely because it is slow.

---

## TASK 5 — Flakiness Score

Create a score:

```text
0–100
```

It should primarily represent inconsistent outcomes.

A possible conceptual model:

```text
Outcome inconsistency → 70%
Failure recency       → 15%
Duration instability  → 15%
```

Validate the weighting.

Keep all thresholds configurable.

---

## TASK 6 — Classification

Implement:

### INSUFFICIENT_DATA

Not enough executions.

### STABLE

Consistently reliable.

### MOSTLY_STABLE

Occasional failures but low flakiness.

### SUSPECTED_FLAKY

Mixed outcomes with meaningful score.

### HIGHLY_FLAKY

Strong repeated inconsistency.

### CONSISTENTLY_FAILING

Almost always failing.

---

## TASK 7 — Newly Flaky Detection

Detect:

```text
previously stable
        ↓
currently flaky
```

Mark:

```text
newly_flaky = true
```

---

## TASK 8 — Persistently Flaky Detection

Detect tests that remain flaky over multiple analysis windows.

---

## TASK 9 — Trend Analysis

Support:

```text
pass rate trend
failure rate trend
duration trend
flakiness score trend
```

---

## TASK 10 — Analysis Tests

Write extensive unit tests.

Test:

* all pass
* all fail
* mixed results
* low sample size
* 50/50 behavior
* mostly passing
* mostly failing
* recent failures
* old failures
* slow tests
* variable duration

---

# PHASE 4 GATE

Before continuing, verify:

```text
[ ] Statistics are correct
[ ] Flakiness score works
[ ] Classification works
[ ] Recency works
[ ] Duration analysis works
[ ] Trends work
[ ] Edge cases work
[ ] Tests pass
```

---

# PHASE 5 — SYNTHETIC CI DATA

### Description

Create deterministic demo data that makes the dashboard genuinely useful.

Never use uncontrolled randomness.

---

## TASK 0 — Demo Test Definitions

Create tests representing:

```text
always passing
always failing
intermittently failing
recently flaky
slow stable
variable duration
skipped
insufficient history
```

---

## TASK 1 — Deterministic History Generator

Create:

```bash
flakyctl seed-demo
```

Generate:

```text
30–100 CI runs
20–50 tests
```

Use deterministic patterns.

---

## TASK 2 — Ground Truth

Create internal ground-truth labels.

Example:

```json
{
  "test_payment_timeout": "flaky",
  "test_login": "stable",
  "test_database_config": "consistently_failing"
}
```

Do not use these labels to calculate the actual classification.

They exist only for evaluation.

---

## TASK 3 — Detector Evaluation

Compare:

```text
ground truth
vs
detector prediction
```

Calculate:

```text
true positives
true negatives
false positives
false negatives
precision
recall
```

---

## TASK 4 — CLI

Implement:

```bash
flakyctl seed-demo
flakyctl ingest results.xml
flakyctl analyze
flakyctl list-flaky
```

---

# PHASE 5 GATE

A fresh database should be able to go from:

```text
empty
 ↓
flakyctl seed-demo
 ↓
historical data
 ↓
analysis
 ↓
dashboard-ready results
```

---

# PHASE 6 — REST API

### Description

Expose the analysis through a clean REST API.

---

## TASK 0 — Projects API

Implement:

```http
GET /api/projects
POST /api/projects
GET /api/projects/{id}
```

---

## TASK 1 — Runs API

Implement:

```http
GET /api/runs
GET /api/runs/{id}
POST /api/runs/upload
```

Add pagination.

---

## TASK 2 — Tests API

Implement:

```http
GET /api/tests
GET /api/tests/{id}
```

Filters:

```text
classification
project
branch
suite
minimum_score
```

---

## TASK 3 — Flaky Tests API

Implement:

```http
GET /api/flaky-tests
```

Support:

```text
minimum_score
classification
limit
offset
sort
```

---

## TASK 4 — Test History API

Implement:

```http
GET /api/tests/{id}/history
```

Return:

```text
run
status
duration
timestamp
score
```

---

## TASK 5 — Dashboard Summary API

Implement:

```http
GET /api/dashboard/summary
```

Return:

```text
total_tests
total_runs
stable_tests
suspected_flaky_tests
highly_flaky_tests
consistently_failing_tests
slow_tests
newly_flaky_tests
average_pass_rate
```

---

## TASK 6 — API Error Handling

Create consistent errors.

Example:

```json
{
  "error": "INVALID_JUNIT_FILE",
  "message": "The uploaded file is not a valid JUnit report.",
  "request_id": "..."
}
```

---

## TASK 7 — API Tests

Test:

* success
* validation failures
* missing IDs
* filters
* pagination
* malformed XML
* invalid uploads

---

# PHASE 6 GATE

Verify all endpoints using:

* automated tests
* Swagger
* manual API calls

No undocumented endpoints should be required for the main workflow.

---

# PHASE 7 — FRONTEND FOUNDATION

### Description

Build the frontend as a professional engineering dashboard.

---

## TASK 0 — Initialize React

Create:

```text
frontend/
```

Use:

* React
* TypeScript
* Vite

---

## TASK 1 — API Client

Create typed API services.

Do not scatter raw `fetch()` calls throughout components.

---

## TASK 2 — Application Layout

Create:

```text
sidebar
header
main content
```

Pages:

```text
Dashboard
Tests
Flaky Tests
Runs
Test Details
```

---

## TASK 3 — Loading/Error States

Every API-driven page must support:

```text
loading
success
empty
error
```

---

# PHASE 7 GATE

Frontend must:

```text
start
connect to backend
handle API errors
display basic data
```

---

# PHASE 8 — DASHBOARD

### Description

Turn the backend intelligence into a polished QA observability dashboard.

---

## TASK 0 — KPI Cards

Display:

```text
Total Tests
CI Runs
Flaky Tests
Newly Flaky
Failing Tests
Slow Tests
```

---

## TASK 1 — Flaky Test Table

Columns:

```text
Test
Suite
Classification
Flakiness Score
Pass Rate
Failure Rate
Runs
Avg Duration
Last Seen
Trend
```

Add:

* search
* filters
* sorting
* pagination

---

## TASK 2 — Main Charts

Implement:

### Outcome distribution

Passed / Failed / Error / Skipped

### Flaky severity

Stable / Suspected / Highly Flaky / Consistently Failing

### Pass-rate trend

### Duration trend

### Top flaky tests

---

## TASK 3 — Test Detail Page

Display:

```text
test name
test identity
classification
flakiness score
sample size
pass rate
failure rate
average duration
median duration
p95
duration variability
```

---

## TASK 4 — Execution History

Show:

```text
Run 1 PASS
Run 2 PASS
Run 3 FAIL
...
```

Use visual indicators.

---

## TASK 5 — History Charts

Create:

```text
Outcome history
Duration history
Flakiness score history
```

---

## TASK 6 — Failure Messages

Display recent unique failure messages.

This should help engineers investigate the reason behind instability.

---

## TASK 7 — Dashboard Filters

Support:

```text
Project
Branch
Workflow
Environment
Classification
Date range
Minimum score
```

---

# PHASE 8 GATE

A reviewer must be able to:

```text
open dashboard
 ↓
see system health
 ↓
find flaky tests
 ↓
filter them
 ↓
open a test
 ↓
understand why it was flagged
 ↓
inspect its history
```

---

# PHASE 9 — FRONTEND TESTING

### Description

Test the dashboard itself.

---

## TASK 0 — Component Tests

Test:

* KPI cards
* tables
* filters
* charts
* detail pages

---

## TASK 1 — API Error Tests

Simulate:

```text
500
404
timeout
empty response
```

Ensure the UI handles them gracefully.

---

## TASK 2 — Build Validation

Verify:

```bash
npm run build
```

works.

---

# PHASE 9 GATE

```text
[ ] Frontend tests pass
[ ] Build passes
[ ] No console errors
[ ] Loading states work
[ ] Error states work
```

---

# PHASE 10 — DOCKER

### Description

Package the entire system so a reviewer can run it easily.

---

## TASK 0 — Backend Dockerfile

Create production-credible backend image.

---

## TASK 1 — Frontend Dockerfile

Create frontend image.

---

## TASK 2 — Docker Compose

Create:

```text
docker-compose.yml
```

Services:

```text
postgres
backend
frontend
```

---

## TASK 3 — Environment Configuration

Use:

```text
.env.example
```

Never hardcode secrets.

---

## TASK 4 — Full Startup Test

Run:

```bash
docker compose up --build
```

Verify the complete system.

---

# PHASE 10 GATE

A clean machine/repository should be able to run:

```bash
docker compose up --build
```

and reach:

```text
Frontend
Backend
Swagger
PostgreSQL
```

---

# PHASE 11 — GITHUB CODESPACES

### Description

Make the project easy to run in Codespaces.

---

## TASK 0 — Devcontainer

Create:

```text
.devcontainer/devcontainer.json
```

Include:

* Python
* Node
* Docker
* useful VS Code extensions

---

## TASK 1 — Codespaces Documentation

README must contain exact instructions:

```text
Open repository
 ↓
Create Codespace
 ↓
docker compose up --build
 ↓
open dashboard
```

---

## TASK 2 — Codespaces Validation

Actually validate the setup.

Fix environment-specific problems.

---

# PHASE 11 GATE

The project must be runnable without the developer manually fixing configuration.

---

# PHASE 12 — CI/CD

### Description

Use GitHub Actions to prove the project itself follows engineering-quality practices.

---

## TASK 0 — CI Workflow

Create:

```text
.github/workflows/ci.yml
```

---

## TASK 1 — Backend CI

Run:

```text
install
lint
pytest
coverage
```

---

## TASK 2 — Frontend CI

Run:

```text
npm install
lint
test
build
```

---

## TASK 3 — Docker CI

Build the Docker images.

---

## TASK 4 — JUnit Artifact

Generate:

```text
test-results.xml
```

Upload it as a GitHub Actions artifact.

---

## TASK 5 — Optional Self-Ingestion

If practical, demonstrate:

```text
GitHub Actions
 ↓
pytest
 ↓
JUnit XML
 ↓
Flaky Test Platform
```

Only implement this if it remains simple and secure.

---

# PHASE 12 GATE

GitHub Actions must pass on a clean commit.

---

# PHASE 13 — SECURITY & HARDENING

### Description

Add basic security controls so the project does not look like a toy application.

---

## TASK 0 — XML Security

Verify protection against:

* XXE
* entity expansion
* malicious XML

---

## TASK 1 — Upload Validation

Implement:

* file type validation
* size limits
* malformed file handling

---

## TASK 2 — CORS

Configure CORS from environment variables.

---

## TASK 3 — Error Safety

Do not expose:

* stack traces
* database credentials
* environment secrets

---

## TASK 4 — Dependency Review

Check dependencies for obvious issues.

Do not blindly upgrade everything.

---

# PHASE 13 GATE

Run security-oriented tests and verify no secrets are committed.

---

# PHASE 14 — DOCUMENTATION

### Description

Transform the implementation into a portfolio-quality engineering project.

---

## TASK 0 — README

README must contain:

```text
Project overview
Problem
Solution
Features
Architecture
Technology stack
Installation
Docker
Codespaces
CLI
API
Dashboard
Detection algorithm
Testing
CI/CD
Demo
Limitations
Roadmap
```

---

## TASK 1 — Architecture Documentation

Complete:

```text
docs/architecture.md
```

Include Mermaid architecture diagram.

---

## TASK 2 — Data Model Documentation

Complete:

```text
docs/data-model.md
```

Explain:

* tables
* relationships
* indexes
* test identity

---

## TASK 3 — Detection Algorithm

Complete:

```text
docs/detection-algorithm.md
```

Explain exactly how:

```text
raw executions
 ↓
statistics
 ↓
inconsistency
 ↓
recency
 ↓
duration instability
 ↓
flakiness score
 ↓
classification
```

works.

---

## TASK 4 — Demo Script

Create:

```text
docs/demo-script.md
```

Design a 3–5 minute demonstration.

---

## TASK 5 — API Documentation

Document important endpoints with examples.

---

# PHASE 14 GATE

A technical reviewer should be able to understand the entire system without reading the source code first.

---

# PHASE 15 — REAL DEMO & EVIDENCE

### Description

Generate actual evidence from the working system.

Do not fake anything.

---

## TASK 0 — Generate Demo Data

Run:

```bash
flakyctl seed-demo
```

---

## TASK 1 — Capture Dashboard Evidence

Capture actual screenshots of:

1. dashboard overview
2. flaky test ranking
3. test details
4. execution history
5. trend charts
6. API documentation

---

## TASK 2 — Run Full Test Suite

Run all backend and frontend tests.

Record actual results.

---

## TASK 3 — Detector Evaluation

Generate actual:

```text
precision
recall
false positives
false negatives
```

---

## TASK 4 — Docker Validation

Perform a clean:

```bash
docker compose down -v
docker compose up --build
```

Then repeat the demo.

---

# PHASE 15 GATE

All evidence must come from the actual implementation.

---

# PHASE 16 — FINAL QA AUDIT

### Description

Treat your own project as a client product and perform a final QA audit.

---

## TASK 0 — Functional Audit

Verify:

```text
upload
ingestion
storage
analysis
classification
API
dashboard
filters
history
```

---

## TASK 1 — Negative Testing

Test:

```text
malformed XML
empty XML
invalid file
oversized file
missing project
missing metadata
invalid test ID
invalid filters
invalid pagination
```

---

## TASK 2 — UI Audit

Check:

```text
desktop
smaller viewport
loading
empty state
error state
long test names
large datasets
```

---

## TASK 3 — Data Integrity Audit

Verify:

* duplicate runs
* duplicate tests
* consistent test identities
* correct pass rates
* correct counts
* correct dashboard metrics

---

## TASK 4 — Final Code Quality

Run:

```bash
ruff check .
pytest
npm run build
```

and all relevant frontend checks.

---

# PHASE 16 GATE

Nothing critical should remain broken.

---

# PHASE 17 — PORTFOLIO POLISH

### Description

The final phase makes the repository look like a serious engineering portfolio project.

---

## TASK 0 — Repository Naming

Recommended repository:

```text
flaky-test-intelligence
```

---

## TASK 1 — GitHub Description

Use a professional short description such as:

```text
Flaky test detection and CI analytics platform that analyzes historical JUnit results, scores test instability, tracks trends, and visualizes QA reliability.
```

---

## TASK 2 — Repository Topics

Suggested topics:

```text
qa
software-testing
test-automation
flaky-tests
pytest
fastapi
postgresql
react
typescript
docker
github-actions
ci-cd
sdet
devops
```

---

## TASK 3 — README Hero Section

README should immediately communicate:

```text
What problem does this solve?
How does it work?
What technologies are used?
What does the dashboard show?
```

---

## TASK 4 — Screenshots

Use only real screenshots from the finished application.

---

## TASK 5 — Portfolio Summary

Create:

```text
docs/portfolio-summary.md
```

Explain what the project demonstrates from the perspective of:

### QA

* flaky test analysis
* test reliability
* CI quality
* automation

### SDET

* test infrastructure
* automation architecture
* data processing
* API design

### DevOps

* CI/CD
* Docker
* GitHub Actions
* observability

### Software Engineering

* architecture
* database design
* REST APIs
* frontend/backend integration

---

# FINAL DEFINITION OF DONE

The project is complete only when every item below is true.

## Backend

* [ ] FastAPI works
* [ ] PostgreSQL works
* [ ] Alembic works
* [ ] JUnit ingestion works
* [ ] Secure XML parsing works
* [ ] Test identity works
* [ ] Historical executions are stored

## Analysis

* [ ] Pass rate works
* [ ] Failure rate works
* [ ] Duration metrics work
* [ ] Flakiness score works
* [ ] Classification works
* [ ] Recency works
* [ ] Trend analysis works
* [ ] Newly-flaky detection works
* [ ] Persistent flakiness works

## Demo

* [ ] Synthetic data generator works
* [ ] Data is deterministic
* [ ] Ground truth exists
* [ ] Detector evaluation works
* [ ] Precision/recall are calculated

## API

* [ ] Projects API
* [ ] Runs API
* [ ] Tests API
* [ ] Flaky tests API
* [ ] History API
* [ ] Dashboard API
* [ ] API tests

## Frontend

* [ ] Dashboard
* [ ] KPI cards
* [ ] Flaky test table
* [ ] Filters
* [ ] Charts
* [ ] Test details
* [ ] Execution history
* [ ] Error states
* [ ] Loading states

## DevOps

* [ ] Docker
* [ ] Docker Compose
* [ ] Codespaces
* [ ] GitHub Actions
* [ ] JUnit artifacts

## Quality

* [ ] Unit tests
* [ ] Integration tests
* [ ] API tests
* [ ] Frontend tests
* [ ] Linting
* [ ] Build verification
* [ ] Security checks

## Documentation

* [ ] README
* [ ] Architecture
* [ ] Data model
* [ ] Detection algorithm
* [ ] API documentation
* [ ] Demo script
* [ ] Limitations
* [ ] Roadmap
* [ ] Portfolio summary

---

# IMPORTANT CODING AGENT BEHAVIOR

Do not rush through all phases.

Start with:

```text
PHASE 0 — TASK 0
```

Inspect the repository first.

Then implement tasks sequentially.

After completing each task:

1. inspect your changes
2. run the relevant tests
3. fix failures
4. report the task status
5. continue to the next task

Do not jump directly to the frontend.

Do not build fake UI before the underlying data and API exist.

Do not create placeholder implementations for major features.

When a phase is complete, run its phase gate.

If a phase gate fails, stop and fix the issue before continuing.

The goal is a **working, tested, reproducible engineering product**, not merely a large amount of generated code.

---

# START NOW

Begin with:

## PHASE 0 — TASK 0

Inspect the current repository and report:

```text
1. Repository structure
2. Existing technologies
3. Existing implementation
4. Existing tests
5. Existing configuration
6. What can be reused
7. Recommended implementation starting point
```

Do NOT start implementing Phase 1 until the repository inspection is complete.
