# Package Manifest

This file lists all artifacts included in the portable methodology package.

## Core docs

1. `README.md`
2. `TECHNICAL.md`
3. `CURSOR_ADAPTATION.md`
4. `COPILOT_ADAPTATION.md`
5. `START_HERE.md`
6. `TRANSFER_AND_BOOTSTRAP.md`
7. `NEW_REPO_CONFIGURATION_PLAN.md`

## Visual flow

1. `flow.mmd`
2. `flow.png`
3. `flow.svg`

## Templates

1. `templates/ORIENTATION_TEMPLATE.md`
2. `templates/STATUS_TEMPLATE.md`
3. `templates/FOLLOWUPS_TEMPLATE.md`
4. `templates/SHARP_EDGES_TEMPLATE.md`
5. `templates/ISSUE_NOTE_TEMPLATE.md`
6. `templates/HANDOVER_TEMPLATE.md`
7. `templates/QA_ACCEPTANCE_TEMPLATE.md`
8. `templates/COPILOT_WORKING_AGREEMENT_TEMPLATE.md`
9. `templates/CURSOR_WORKING_AGREEMENT_TEMPLATE.md`

## Cursor surface pack (`cursor/`)

1. `cursor/README.md`
2. `cursor/mcp.json.example`
3. `cursor/AGENTS.md.example`
4. `cursor/rules/00-methodology-core.mdc`
5. `cursor/rules/01-tool-prevalence.mdc`
6. `cursor/rules/02-gates-and-handoff.mdc`
7. `cursor/skills/kg/SKILL.md`
8. `cursor/skills/kg-refresh/SKILL.md`
9. `cursor/skills/methodology-plan/SKILL.md`
10. `cursor/skills/sanitise-diff/SKILL.md`
11. `cursor/hooks.json.example`
12. `cursor/hooks/block-external-git.ps1`

## Scripts

1. `scripts/bootstrap-new-repo.ps1.txt` — ledgers + shared templates
2. `scripts/bootstrap-cursor-repo.ps1.txt` — `.cursor/` rules, skills, MCP, hooks

## Intended use

1. Copy package to target repo under `data/changes/ai-agent-methodology`.
2. Rename `scripts/bootstrap-new-repo.ps1.txt` to `scripts/bootstrap-new-repo.ps1`.
3. Run `scripts/bootstrap-new-repo.ps1` from target repo root.
4. For Cursor: rename and run `scripts/bootstrap-cursor-repo.ps1.txt` → `.ps1`.
5. Fill generated templates and start first issue using the planning template
   in `CURSOR_ADAPTATION.md` or `COPILOT_ADAPTATION.md`.
