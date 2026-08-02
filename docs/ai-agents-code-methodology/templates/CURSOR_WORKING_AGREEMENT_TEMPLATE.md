# CURSOR_WORKING_AGREEMENT_TEMPLATE

## Scope and role

1. Cursor Agent may investigate, propose, implement, and test.
2. Human approves plan before code for non-trivial changes (Plan mode).
3. Human owns merge/deploy/external communication unless they explicitly ask the agent to run a specific outward command in-session.

## Required gates

1. Inbound gate: symptom reproduced at output contract.
2. Provenance gate: pre-change baseline check (regression vs pre-existing).
3. TDD gate: RED -> GREEN.
4. Outbound gate: fixed contract output reproduction (and runtime parity when applicable).
5. Sanitise gate: added staged lines scanned before handoff.

## Tool prevalence (agreed)

1. CodeGraph `codegraph_explore` before reading large files for survey.
2. Serena `find_referencing_symbols` before rename/delete.
3. Playwright (or equivalent) for consumer-visible contract checks.
4. `kg` skill / STATUS fallback before grepping all change history.
5. Deterministic oracle before expensive model diagnosis.

## Cursor surface (installed)

1. Rules under `.cursor/rules/` stay lean (gates + pointers).
2. Skills under `.cursor/skills/` for kg / plan / sanitise / kg-refresh.
3. Optional hooks block push/PR/deploy pending human approval.
4. MCP servers listed in `.cursor/mcp.json` are the preferred tool layer.

## Documentation outputs per issue

1. Issue note.
2. Handover note.
3. QA acceptance criteria.
4. Status/Followups/Sharp-edges updates as needed.

## Security and confidentiality

1. No secrets in committed files.
2. No forbidden names/IDs according to repo policy.
3. Run sanitisation checks before handoff.

## Review policy

1. Automated reviewer comments are triaged like human comments.
2. No unresolved valid findings at merge time.
