# COPILOT_WORKING_AGREEMENT_TEMPLATE

## Scope and role

1. Copilot may investigate, propose, implement, and test.
2. Human approves plan before code for non-trivial changes.
3. Human owns merge/deploy/external communication.

## Required gates

1. Inbound gate: symptom reproduced at output contract.
2. Provenance gate: pre-change baseline check (regression vs pre-existing).
3. TDD gate: RED -> GREEN.
4. Outbound gate: fixed contract output reproduction.

## Documentation outputs per issue

1. Issue note.
2. Handover note.
3. QA acceptance criteria.
4. Status/Followups/Sharp-edges updates as needed.

## Security and confidentiality

1. No secrets in committed files.
2. No forbidden names/IDs according to repo policy.
3. Run sanitization checks before handoff.

## Review policy

1. Automated reviewer comments are triaged like human comments.
2. No unresolved valid findings at merge time.
