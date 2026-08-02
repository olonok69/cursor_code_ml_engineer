---
name: methodology-plan
description: >-
  Fill the methodology planning template after inbound triage and cheap
  investigation. Use in Plan mode before writing production code.
---

# methodology-plan

## When to use

- After stages 1–4 (orient, inbound triage, provenance, cheap root-cause probe).
- Before any production implementation.
- User asks for a plan, options, or “should we fix this?”.

## Rules

1. Stay in **Plan** posture: propose, do not implement.
2. Prefer evidence already gathered (contract sample, oracle output, KG hits).
3. Record rejected options, not only the chosen one.

## Template (fill completely)

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
- Options considered (incl. rejected): <bullets>

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

## Exit

Stop and ask for explicit human agreement. Only after agreement, switch to implementation (Agent mode) and TDD.
