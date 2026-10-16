---
name: evidence
description: Collect the evidence of a service run (source as it was at the run, generated artefact, result JSON, log lines, manifest) from a non-prod environment by app URL, document id or container id + file name, or discover every failed run in a time window. Read-only. Use when a document failed or is reported, when QA/support sends an app URL, or to gather a ticket's evidence.
---

# evidence: capture run evidence (read-only)

Tool: `data/changes/tools/evidence/evidence.py` in the project repo. Read-only AWS profile
(`EVIDENCE_PROFILE`, e.g. `<read-only-profile>`). The course copy of the reusable core (version
selection, read-only client, scrubbing) and the design are in `ejemplos/metodologia/tools/evidence/`.

```bash
cd data/changes/tools/evidence
uv run -q --with boto3 python evidence.py fetch --url "<app page URL>" [--file "<part of name>"] [--ticket PROJ-NNNN]
uv run -q --with boto3 python evidence.py fetch --env dev --doc <doc_id> [--all-runs]
uv run -q --with boto3 python evidence.py discover --env dev --since 24h --list   # counts only
uv run -q --with boto3 python evidence.py discover --env dev --since 2h            # downloads (cap 50)
uv run -q --with boto3 python evidence.py selftest
```

- Default output:
  - `--ticket` → `data/changes/<ticket>/evidence/runs/`;
  - otherwise → `data/changes/_evidence/<env>/<date>/`. That folder is NOT pushed to the shared
    store (excluded in `JUNK_ARGS`). Move a run into a ticket folder only once it matters.
- Each run folder: `source__…` (as it was at the run), `artefact__…`, `result.json`, `log.txt`, `run.json`.
  Read `run.json` first: `outcome`, `signature`, per-artefact `status`/`reason`, `checks.image_changed_since_run`.
- `result.json` is the service's raw output, NOT the consumer-facing contract JSON (that one needs an
  app login and is not collected — never mistake one for the other).
- Exit codes:

  | Code | Meaning |
  |---|---|
  | 0 | ok |
  | 1 | usage |
  | 2 | login: run `aws sso login` and retry; do not diagnose |
  | 3 | AWS error |
  | 4 | nothing found |
  | 5 | guard (narrow `--since`) |
  | 6 | bucket no longer keeps old versions (versioning off or an expiry rule): tell the user |

## Hard rules
1. Never run the processor on a fetched `source__` file in place: it may re-save its input. Copy to scratch first.
2. Re-login before drawing any conclusion from an AWS error.
3. Prod is not supported (no access, by design).
