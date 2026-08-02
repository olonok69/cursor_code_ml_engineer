# Working with AI coding agents — the technical playbook

> **Audience:** engineers who will run, supervise, or extend an AI-agent
> development loop. This is the implementation-level companion to
> [`README.md`](README.md) (which is the plain-English overview). Same
> methodology; here we describe the *mechanics* — the gates, the harnesses,
> the proofs — in enough detail to build them.
>
> **Deliberately technology-agnostic.** No tool, library, language, model
> vendor, or product is named. Everything below is a *role* or a *technique*;
> fill the roles with whatever your stack provides. Where we say "the model"
> we mean any probabilistic/LLM component; "the oracle" is any deterministic
> component that can answer a structural question for free; "the agent" is
> the AI coding assistant; "the review bot" is any automated reviewer.

---

## 0. The one-sentence version

Wrap a fast, breadth-strong, occasionally-overconfident generator in a set of
**deterministic gates** — contract reproduction, a free oracle, a layered test
battery, a generality proof, and a sanitisation scan — so that nothing reaches
the permanent record without evidence, and the human keeps the decisions and
the outward actions.

---

## 1. Contract-first: define the black box before you touch the inside

Pick the **output contract** — the exact interface a downstream consumer
observes — and make it the unit of truth. Not an internal function's return
value; the thing the next system actually reads. Two consequences:

- **Inbound gate.** Before writing any code, reproduce the reported symptom
  *at the contract*. If you can't make it appear there, the defect is not in
  your component — it's downstream, and the correct output is a pushback with
  the contract sample attached, not a patch. This single gate kills the most
  expensive class of wasted work: fixing the wrong system.
- **Outbound gate.** Before handing off, reproduce the *fixed* contract
  locally and show the symptom is gone. Internal unit green is necessary, not
  sufficient — the consumer sees the contract, so the contract is what you
  prove. "No local contract reproduction = not done."

Build a small harness that drives the component end-to-end and emits the
contract shape (the same structure, depth, and field set the consumer parses).
Reproduce bugs **through that full shape**, never through a single primitive in
isolation — a primitive can look correct while the assembled contract is wrong.

## 2. Deterministic root cause before any paid run

The generator is probabilistic and often metered. Do not use it to *diagnose*.
Instead:

- **Find a free, deterministic oracle.** Most systems contain a component that
  can answer the structural question deterministically and at zero marginal
  cost (a parser, a layout engine, a static analyser, a schema validator, or a
  **pre-computed graph/index over the codebase or the prior-decision record**).
  Use it to confirm the hypothesis: run it, get the same answer every time,
  and you have a root cause you can stand behind. Spend the paid/probabilistic
  run *only* at the end, to verify the finished fix against the live contract.
- **Probe predicates cheaply.** To test one decision function in isolation,
  instantiate just enough of the object to exercise it — bypass the heavy
  constructor by building a bare instance and setting only the fields the
  predicate reads. You get a millisecond, deterministic test of the exact
  branch, with no expensive initialisation and no network/model call.
- **Rule out logic and configuration before "variance."** "The model is just
  being flaky" is a conclusion of last resort. When a system genuinely is
  non-deterministic, the bug is usually a **sensitivity**, not the variance
  itself: the same input yields a correct result on one run and a wrong one on
  the next because some heuristic sits right at a threshold. Fix the
  sensitivity (move the input away from the threshold, make the boundary
  explicit) — do not "fix" it by re-running until it's green. One green run on
  a non-deterministic system is not a pass.

## 3. Regression vs. pre-existing — prove which, before you own it

When a defect surfaces during your change, establish its provenance before
accepting or refusing it:

- Reproduce on the **pre-change baseline** (the state before your work).
- Compare the contract output before and after your change — ideally
  byte-for-byte on the relevant slice. *Identical* before and after ⇒
  pre-existing, and your change is exonerated; *different* ⇒ you caused it.

This is not blame-shifting — it changes real decisions: the base you branch
from, whether the fix is in scope for the current ticket, and the story you
hand to whoever signs off. Owning an old bug silently, or waving off a real
regression, both cost more later. Make it a proof, not an assertion.

## 4. The test battery — layered, RED-first, zero-regression

Four concentric layers, each a real gate:

1. **Unit** — the decision function / helper in isolation (cheap predicate
   probe from §2).
2. **Scoped regression** — a dedicated test file for *this* defect, written
   RED first: watch it fail for the *right reason* before writing the fix, so
   you know the test actually exercises the bug. A test that never failed
   proves nothing.
3. **Full regression** — the entire existing suite green. The count goes *up*
   by exactly the tests you added and nothing pre-existing flips to red.
4. **Outbound** — the live contract reproduction from §1, driving the real
   (probabilistic) path end-to-end.

Keep each defect's scoped suite as a permanent artifact named for the defect,
so the next person sees both the guard and the example that motivated it.

## 5. Generic solution, with a no-op proof

Fix the **class**, never the instance. The patch keys on a *structural
property* of the input (a layout regime, a marker pattern, a token shape) — not
on the specific reported value. Two obligations that make "generic" real:

- **Positive coverage:** the scoped suite includes sibling inputs in the same
  class that the one report didn't mention.
- **Strict no-op proof:** demonstrate the change does *nothing* to inputs
  outside the class. The canonical regression documents (your known-good
  reference set) come out byte-identical. A fix that can't prove it leaves the
  unaffected cases untouched is a liability, not a fix.

## 6. Context architecture — lean core, on-demand detail, write-once

The agent reloads its always-present context on **every turn**, so that
context's size is a recurring cost, not a one-time one. Architect it:

- **Always-loaded core (small):** the orientation doc (architecture,
  conventions, *locked decisions* with their rationale, working rules), a
  **live snapshot** of current state, and **indexes** (one line per ticket /
  per sharp-edge / per lesson) that point into the detail. The index need not
  stay a flat list: materialise it as a **deterministic queryable graph over
  the durable record** — nodes are tickets/lessons/areas, edges are the
  relations between them — so "what prior work touches this area?" and "how
  are these two decisions connected?" become a zero-cost lookup that returns
  *what to read* before you open anything. This is the documentation-trail
  twin of the semantic code graph in §1: one indexes the code, the other
  indexes the decisions, and both are free deterministic oracles (§2) you
  consult before any linear read or paid run.
- **On-demand reference files (large):** the per-ticket ledgers, the full
  policy text, the investigation playbook, handover templates — opened only
  when that area is in play.
- **Write-once rule:** each record is authored in exactly **one** canonical
  ledger; the core file carries a *pointer*, never a copy. The failure this
  prevents is triplication — the same change pasted into the orientation doc,
  the status ledger, and memory, then drifting out of sync while inflating
  every future session's token bill. (Concretely: when our always-loaded set
  had bloated, we cut it ~73% with zero information loss purely by moving
  detail out to on-demand files and replacing it with pointers.)
- **Persistent memory** follows the same shape: a live snapshot plus an
  open-issues index that explicitly preserves *visibility* of every parked or
  deferred item — lean is not the same as lossy.

## 7. Handoff — artifacts, sanitisation, role separation

The agent prepares; a human (or human-driven automation) takes every outward
step. Concretely:

- **Artifacts per change:** a writeup (root cause → fix → verification
  evidence), an update to the live status ledger, acceptance criteria framed
  for the sign-off reviewer, and a handover note that states exactly what the
  pushing party must do.
- **Sanitisation gate (mechanical, every time):** before anything leaves the
  workbench, scan the **staged change** for content that must not enter the
  permanent record — customer/partner identifiers, internal ticket IDs in
  code bodies, secrets, and agent self-attribution. Make it a pattern scan,
  not a judgement call. Watch the scan's own footguns: a naive diff scan
  matches *removed* lines too, so filter to **added** lines only, and exclude
  paths that are intentionally local/ignored. The one time you eyeball it
  instead of running the scan is the time something leaks.
- **Role separation:** the agent authors the change and leaves the branch;
  it does **not** push, open/merge change requests, deploy, or message anyone.
  Those are the human's gate. This keeps every irreversible or outward-facing
  action behind a human decision, and keeps the shipped artifacts reading as
  the human author's work (no agent attribution in code, commit messages, or
  change-request text).

## 8. Automated review is part of the loop

When a review bot comments on the open change, treat its findings as
first-class:

- **Triage each one** like a human reviewer's: confirm the real defects,
  prepare a **follow-up change** for them, and dismiss false positives **with
  a stated reason** — never silently.
- **Don't merge over an unaddressed valid finding.** A machine-flagged defect
  is still a defect. The follow-up commit closes the loop before the change
  lands; the dismissal-with-reason is itself part of the durable record.

A common real example of the value: a fix that introduces a *new* ordering or
positional assumption (e.g. "this check now only fires at the start of a
string") can pass every hand-written test yet still have a gap the bot spots by
reasoning about the changed control flow. Triage, reproduce, add the missing
regression test, fix, re-verify.

---

## Per-task checklist (the loop, compressed)

```
[ ] Orient: query the record index for related prior work, read those records in full, AND check the live state (branch / open work)
[ ] Inbound gate: symptom reproduced at the OUTPUT CONTRACT? if not → push back
[ ] Provenance: regression or pre-existing? prove it on the pre-change baseline
[ ] Root cause: confirmed with a FREE DETERMINISTIC oracle (no paid run yet)
[ ] Plan: options + trade-offs presented; human agreed; rejected options recorded
[ ] Implement: scoped test RED for the right reason → minimal code → GREEN
[ ] Generic: keyed on a structural class; sibling inputs covered; no-op proof on the reference set
[ ] Verify: unit + scoped + full regression green; non-determinism = fix the sensitivity, not the variance
[ ] Outbound gate: fixed contract reproduced on the live path; symptom gone
[ ] Document: writeup + ledger update + acceptance criteria + handover (each written ONCE)
[ ] Sanitise: scan ADDED lines of the staged change for names / IDs / secrets / attribution
[ ] Hand off: human pushes / opens the change request / deploys — agent does not
[ ] Automated review: triage every bot finding; follow-up commit or dismiss-with-reason
[ ] Persist: update registries + lean memory; codify any reusable lesson into the playbook
```

---

## Technical anti-patterns

- **Diagnosing with the expensive generator.** It's metered and
  non-deterministic; use the free oracle to diagnose, the generator only to
  verify the finished fix.
- **Proving a fix at the wrong layer.** Internal unit green ≠ contract green.
  The consumer reads the contract; prove the contract.
- **Treating a single green run as a pass** on a non-deterministic system.
  Pin the sensitivity, not the seed.
- **Instance-fix masquerading as class-fix.** If the patch references the one
  reported value rather than the structural property, it will fix the demo and
  break the next input.
- **Letting the always-loaded context grow into a changelog.** Every line
  there is paid for on every turn. Detail goes to on-demand files; the core
  stays a map.
- **Skipping the sanitisation scan because "this one's obviously clean."**
  Run it every time; the exceptions are exactly where leaks happen.
- **Merging over a bot finding** because it "looks like a false positive"
  without reproducing it. Reproduce, then dismiss-with-reason or fix.

---

*Internal document. Keep it generic: no client names, no environment
specifics, no secrets. It is meant to be readable by any engineer on any
stack.*
