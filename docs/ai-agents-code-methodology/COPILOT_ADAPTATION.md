# Adapting the AI-agent methodology for GitHub Copilot in a different repo

> Purpose: take the methodology from this Lambda repo and use it effectively
> in a completely different codebase, ticketing process, and technology stack,
> while using GitHub Copilot agent workflows.

---

## 1) What transfers unchanged

These are stack-independent and should remain strict:

1. Plan -> agree -> implement.
2. Verify via the consumer-visible output contract, not internal functions.
3. Solve the general class of issue, not one sample input.
4. Keep a durable decision trail (why, what changed, how verified).
5. Human owns irreversible external actions (merge, deploy, stakeholder comms).

If you keep only five rules, keep these.

---

## 2) What must be adapted for a new repo

In a different repo, these usually differ and should be explicitly remapped:

1. Contract shape:
   - Replace "get-sl-upload-status" with the target system contract.
   - Examples: HTTP response payload, DB row shape, event message schema,
     UI-rendered fields, generated artifact format.
2. Status system:
   - Replace SST/PV ticket conventions with your tracker (Jira, Azure Boards,
     GitHub Issues, Linear, etc.).
3. Test pyramid:
   - Replace current pytest batteries with the local equivalent.
4. Environment/runtime:
   - Replace Lambda/image checks with the deployed runtime for that repo
     (container, VM service, serverless function, edge runtime, mobile build).
5. Compliance/redaction constraints:
   - Define local rules for secrets, names, IDs, and attribution policy.

---

## 3) No-knowledge-graph mode (fallback)

If no ticket knowledge graph exists, use this deterministic fallback:

1. Build a minimal index file:
   - data/changes/STATUS.md with newest-first entries.
   - Per change folder: data/changes/<ticket-or-issue-id>/
2. Use fast lexical search before broad reading:
   - Search by symptom terms, key function names, and contract fields.
3. Use commit/PR history as a lightweight graph substitute:
   - Identify nearby changes by file overlap and message keywords.
4. Create a "danger zones" section:
   - Keep a short list of high-risk invariants that looked refactorable but are
     intentionally split.

This gives 80% of knowledge-graph value with low setup effort.

---

## 4) Copilot agent operating model (practical)

Use Copilot as an implementation and evidence engine, not an autopilot.

1. Session start (mandatory context load):
   - Read orientation doc first (architecture, invariants, rules).
   - Read current status ledger (in-flight and recent changes).
2. Inbound triage:
   - Confirm symptom is present at contract output before code edits.
3. Root cause:
   - Prefer deterministic, cheap probes before expensive AI-dependent runs.
4. Plan gate:
   - Write an explicit plan and get agreement.
5. TDD gate:
   - Add failing test first, then minimal fix, then green.
6. Outbound gate:
   - Reproduce fixed contract output in the real runtime path.
7. Handover:
   - Record verification evidence and reviewer acceptance checks.

---

## 5) Suggested folder structure for any new repo

Use this portable structure in the new repository:

```text
data/
  changes/
    STATUS.md
    FOLLOWUPS.md
    SHARP_EDGES.md
    ai-agent-methodology/
      README.md
      TECHNICAL.md
      COPILOT_ADAPTATION.md
    <issue-or-ticket-id>/
      <issue-or-ticket-id>.md
      _handover.md
      qa_acceptance_criteria.md
```

Keep always-loaded files short; move detail to per-ticket docs.

---

## 6) Ticket-agnostic planning template

Use this exact template when starting work in the new repo:

```text
Issue: <tracker-id> - <short title>

1) Contract confirmation
- Consumer-visible contract: <API/UI/event/artifact>
- Symptom reproduced there: <yes/no + evidence source>

2) Provenance
- Reproduced on pre-change baseline: <yes/no>
- Classification: <regression | pre-existing>

3) Root cause hypothesis
- Deterministic probe used: <probe>
- Result: <what proved the hypothesis>

4) Fix shape (general-case)
- Structural class addressed: <class>
- Why not instance-specific: <one sentence>

5) Verification plan
- RED test: <test id>
- Scoped suite: <command>
- Regression suite: <command>
- Contract output repro: <command/path>
- Runtime parity check: <where and how>

6) Handover outputs
- Change summary doc
- Acceptance criteria
- Open follow-ups
```

---

## 7) Technology mapping table (quick start)

| Methodology concept | Lambda repo example | New repo remap questions |
|---|---|---|
| Output contract | API response JSON | What exact interface does downstream consume? |
| Runtime parity check | Lambda image verification | What is the deployed runtime equivalent? |
| Scoped regression suite | Ticket-specific pytest file | Which test subset isolates this component? |
| Canonical regression battery | Stable baseline fixtures | What is your long-lived golden set? |
| Status ledger | data/changes/STATUS.md | Where is in-flight state tracked today? |
| Sharp edges | Known invariants list | What must not be refactored without design review? |

---

## 8) Minimum governance policy for Copilot use

Define this once in the new repo and enforce consistently:

1. No direct merge/deploy by agent.
2. No secrets in code/tests/docs committed to remote.
3. No unexplained bot-review dismissal.
4. No "fixed" claim without command-level evidence.
5. No prompt/config changes without explicit plan acknowledgement.

---

## 9) 14-day rollout plan in a different repo

### Days 1-2: Baseline

1. Add the folder structure and orientation docs.
2. Define contract surface and one reproducible fixture path.
3. Record initial sharp edges (even if only 3-5 entries).

### Days 3-5: First controlled ticket

1. Run one issue fully with the planning template.
2. Enforce RED -> GREEN and outbound contract gate.
3. Capture one handover and one acceptance criteria file.

### Days 6-10: Stabilize

1. Add scoped test mappings by subsystem.
2. Add follow-up ledger and reviewer checklist.
3. Measure cycle time and defect reopen rate.

### Days 11-14: Harden

1. Tighten policy wording where drift appeared.
2. Add automation for sanitisation checks.
3. Publish a one-page "how we run Copilot here" summary.

---

## 10) Success criteria (to know this is working)

Track these KPIs for 2-4 weeks:

1. Reopened defects per merged fix.
2. Time from first repro to verified contract fix.
3. Percentage of fixes with explicit RED -> GREEN trace.
4. Percentage of handovers with actionable acceptance criteria.
5. Number of "pre-existing, not regression" findings proven early.

If reopen rate drops and verification quality rises, the methodology is
transferring correctly.

---

## 11) Direct answer to your constraints

Yes, this methodology is usable in a completely different repo with Copilot.

1. Knowledge graph is helpful, not required.
2. Different ticket systems are fine if you standardize one status ledger.
3. Different technologies are fine if you redefine contract + runtime checks.
4. The invariant gates (plan, contract proof, general fix, documented handoff)
   stay the same and are the real source of quality.
