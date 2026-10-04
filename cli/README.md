# `cli/` — command-line interface

The CLI is implemented in the backend package and installed as the
`flakyctl` console script:

```bash
pip install -e "backend[dev]"
flakyctl seed-demo
flakyctl ingest demo/sample-results.xml --project demo-project --run-number 101
flakyctl analyze
flakyctl list-flaky --min-score 40 --limit 20
```

Implementation: `backend/app/cli.py` (argparse over the ingestion, analysis,
and demo-generator services — no duplicated logic).
