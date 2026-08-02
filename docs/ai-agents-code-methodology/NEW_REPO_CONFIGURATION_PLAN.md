# New Repo Configuration Plan

## Phase 1: Foundations (Day 1)

1. Copy methodology folder into `data/changes/ai-agent-methodology`.
2. Create baseline trackers:
   - `data/changes/STATUS.md`
   - `data/changes/FOLLOWUPS.md`
   - `data/changes/SHARP_EDGES.md`
3. Define the product-facing output contract for the repo.
4. Define branch and PR naming rules.
5. **If using Cursor:** run `bootstrap-cursor-repo.ps1`, wire `.cursor/mcp.json`, add lean rules under `.cursor/rules/`, fill `AGENTS.md` + Cursor working agreement.

Exit criteria:

1. All baseline docs exist.
2. Team agrees on contract and naming conventions.
3. (Cursor) MCP tools load after window reload.

## Phase 2: Operationalization (Days 2-3)

1. Map test suites by component/subsystem.
2. Add handover and QA acceptance templates.
3. Define minimum evidence required to claim "fixed".
4. Add sanitization checks for names/IDs/secrets (Cursor: `sanitise-diff` skill; optional shell hook for push/deploy).
5. (Cursor) Confirm Plan-mode gate on the first non-trivial change.

Exit criteria:

1. One issue completed with full trail and evidence.
2. Reviewer can execute QA acceptance checks without extra context.

## Phase 3: Stabilization (Days 4-7)

1. Track reopen rate and cycle time.
2. Add new sharp edges discovered in triage and review.
3. Tighten weak areas in templates and checklists.

Exit criteria:

1. Reopen rate trending down.
2. New contributors can run the flow from docs only.

## Phase 4: Hardening (Week 2)

1. Automate repetitive gates where possible.
2. Keep always-loaded docs lean; move detail to ticket folders.
3. Review methodology monthly and prune stale rules.

Exit criteria:

1. Durable process with low manual overhead.
2. Clear evidence quality on each fix handover.
