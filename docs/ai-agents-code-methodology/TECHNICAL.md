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
>
> **This revision** adds the lessons from a run of changes where the *gates*
> themselves turned out to be the weak point: validate a diagnostic against a
> known-answer case before trusting it (§2 — including the sharp edge on the
> cheap-probe shortcut this document used to recommend unguarded); assert on
> composition rather than totals, and say out loud what a gate *cannot* show
> (§4); verify inside the artifact that actually ships, not just locally (§4);
> find the true final writer of a contract field, and check where an "expected"
> value came from (§1); treat the contract as a living document with three
> legitimate outcomes (§1); and a new §7 on **sharing the durable trail across
> machines and people** via object storage, including the machine-identity
> problem that only appears once an agent can run in more than one role.

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

**Find the true final stage.** The contract is produced by whatever runs *last*,
which is often a wrapper or assembly step that rebuilds a field the inner
component already populated. If you reproduce against the inner component you
are reading a pre-final stage: a fix there can be silently discarded by the
rebuild, and your harness will show it working while the shipped output is
wrong. Identify the last writer of every field you care about and reproduce
through it. Getting this wrong costs entire debugging sessions that end in a
false "not reproducible".

**Establish the provenance of the expected value.** When a ticket states an
expected number or output, ask where it came from. "The other environment
returns X" is evidence *about that environment*, never a specification — and if
that environment runs the same code path you are fixing, matching it faithfully
reproduces the bug. Derive the target from the input's own structure and the
written contract, and say so plainly when the stated expectation is wrong. A
reported expectation being off by one is common and is itself a finding.

**Treat the contract as a living document, not a fixed oracle.** When a change
alters what the component emits, consult the governing rule *before* designing
the fix, then do exactly one of three things: **comply** with the rule,
**revise** the rule as part of the same change, or **record** why the change is
out of the rule's scope. All three are legitimate outcomes; **silence is not.**
Revision is normal and expected — a shipped fix revealing that an agreed rule
was wrong is how the contract improves, and a rule that was written wrong on day
one will otherwise outlive everyone who remembers why. Two practical notes:
cite the rule by a **stable identifier** in anything outward-facing (review
text, tickets, sign-off criteria), never by a file path, because local paths do
not resolve for the people reading it; and resist the urge to enforce this with
a merge-time check — the decision is three-valued, and a binary gate would block
the *correct* "revise the rule" outcome.

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
- **Probe predicates cheaply — but canary the probe.** To test one decision
  function in isolation, instantiate just enough of the object to exercise it —
  bypass the heavy constructor by building a bare instance and setting only the
  fields the predicate reads. You get a millisecond, deterministic test of the
  exact branch, with no expensive initialisation and no network/model call.
  **This shortcut has a sharp edge, and it has drawn blood.** Skipping the
  constructor leaves unset every attribute you did not think to set; if the
  method under test reads one of them *and* contains its own `try/except`, the
  resulting attribute error is swallowed and returned as a plausible negative.
  The probe then reports a confident, uniform "no" for every input — and a
  survey built on it reported the right headline for entirely the wrong reason,
  with all several-hundred inputs reading as negative. Two rules make the
  shortcut safe:
  1. **Always canary against a known-answer case.** Before you trust a probe on
     unknown inputs, run it on one input whose answer you already know, and
     record that result next to the finding. A probe that cannot produce the
     known positive is measuring nothing.
  2. **Never wrap the measurement in your own `try/except → return False`.** Let
     it crash. A loud failure is a working instrument; a quiet one is a broken
     instrument that looks like evidence.
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
5. **Deployed artifact** — the same reproduction run *inside the artifact that
   actually ships* (container image, bundle, packaged runtime), not just in
   your working tree. Pull or build the artifact, mount the fixed source, re-run
   the outbound reproduction, and confirm it is byte-for-byte what local
   produced. "Tests pass" is a statement about your machine; the deliverable is
   what runs in the artifact. Environment-only defects — a missing locale, a
   font, a native library — are invisible to every earlier layer and show up
   only here.

Keep each defect's scoped suite as a permanent artifact named for the defect,
so the next person sees both the guard and the example that motivated it.

**Reading the results is part of the gate.** Three habits separate a real pass
from a green-looking one:

- **Assert on composition, never on the total.** A count that matches the
  expectation is not a passing test. Totals are lossy: an item wrongly added
  and an item wrongly dropped cancel exactly. Assert on the *member list* —
  titles, ids, keys — and print the members next to any headline number. The
  closer a count lands to the expected value, the more suspicion it deserves,
  not less; the worst outcome available is a green number with wrong content
  inside it, because nobody re-opens it. Where a defect has a known direction,
  prefer a **delta against a baseline** (gained / lost) over two totals.
- **Match the measurement to the defect class.** A geometry defect needs
  geometry measurement — compare the actual rectangles — not a count. Real
  fixes exist whose before/after counts are *identical* while the output moved;
  any count-based check reports "nothing happened" for them.
- **State what each gate can and cannot show.** If a gate is structurally
  incapable of failing for this change — the reference corpus holds no positive
  example of the shape you just added — say so explicitly and name what carries
  the evidence instead. A clean run over inputs that cannot exercise the new
  code proves *no regression* and says nothing whatsoever about correctness.
  Reporting it as validation is the most respectable-looking way to ship an
  unverified change.

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

## 7. Sharing the trail — one record, many machines and people

§6 makes the durable trail *cheap*. This section makes it **shared**. The trail
described so far has a structural weakness: it usually lives in a directory that
is deliberately excluded from version control (it holds working notes,
diagnostics, captures, and generated indexes that have no business in the
repository). That exclusion is correct, and it has three costs:

- You cannot reference the trail from a ticket, a change request, or a sign-off
  document — the path resolves only on your own machine.
- Moving between machines degenerates into archiving the whole directory and
  copying it across, which is slow, easy to forget, and silently lossy.
- Teammates each build their own private index of the same shared history, so
  the "one durable record" is a fiction the moment there are two people.

The fix is to put the trail in **shared object storage** and give it an
operating model. The model matters more than the technology.

**Scope it deliberately, and narrowly.** Share *engineering knowledge only* —
the written records and the derived index. Do **not** widen it to customer
documents, test fixtures, captures, or binaries without an explicit owner
sign-off. This is both a confidentiality boundary and a size boundary, and it is
much easier to widen later than to retract.

**Two access modes, and a rule that prevents most accidents.**

| | Sync (push / pull) | Mount (object-storage filesystem view) |
|---|---|---|
| Where you work | real local disk, fast | a live view of the shared store |
| Good for | **writing** records, building the index, version control, search | **reading** and browsing what others have |
| Concurrency | explicit, and you see what moved | read-only, so nothing to clobber |
| Caveat | not live — you run it when you want | no locking, no atomic rename, partial writes are visible |

> **Write via sync, read via mount.** Mount the shared store **read-only on
> purpose**: object storage has no file-locking and no atomic rename, so a
> writable mount invites silent corruption that looks like a mystery bug weeks
> later. The read-only mount is not a limitation to work around; it is the
> safety property.

**Make the destructive direction opt-in.** Sync commands should **dry-run by
default** and require an explicit flag to transfer. Mirror-delete (removing on
one side what was deleted on the other) is a separate, additional opt-in — the
default should only add and update, because the common case is that a teammate
is pushing at the same time and you do not want to erase their work with a
stale local view. Enable versioning on the store as the recovery net.

**Source of truth vs. derived artifact.** The written records are the source of
truth; the queryable index from §6 is **derived** from them. Everyone reads the
index; exactly **one machine publishes it**. Two people rebuilding and pushing
the same generated graph is the one genuine contention point in an otherwise
conflict-free system — per-task folders rarely collide because people work on
different tasks. Prefer *rebuild-locally-from-synced-records* over syncing the
built index at all; if you do share it, designate a single publisher.

**Machine identity — so the agent knows which machine it is on.** This is the
part that is specific to agent workflows and easy to miss. Once the same trail
is reachable from several machines with *different roles*, an agent session must
know **which machine it is running on and what that machine is allowed to do** —
otherwise a contributor machine will helpfully rebuild and publish the shared
index, which is precisely the one thing it must not do. Give each machine a
small declared identity (a name and a role), generate a machine-local identity
card from it that also runs live checks (is the store reachable? is the mount
present? which account are we authenticated as?), and have the always-loaded
orientation doc point at that card so every session reads its own role first.
Keep the card machine-local and out of both version control and the shared
store — it is the one file that must *not* be the same everywhere.

**Before the first shared push.** Scrub the records for embedded secrets.
Investigation notes are the dangerous case: they often capture signed URLs,
tokens, or connection strings *on purpose*, as evidence, and those are exactly
the strings you do not want landing in shared storage. Run the sanitisation scan
from §8 over the whole trail once, not just over a diff, before it leaves the
machine for the first time.

## 8. Handoff — artifacts, sanitisation, role separation

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

## 9. Automated review is part of the loop

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

Two things worth knowing before you answer a bot:

- **Reproduce before you agree, and before you push back.** Both directions are
  failure modes. Performative agreement produces a needless "fix" to code that
  was correct; reflexive dismissal merges a real defect. Measure the blast
  radius either way — a valid finding is frequently **latent rather than inert**
  (the flawed logic is reached on a minority of inputs and currently produces no
  wrong output), and "latent" changes the urgency but not the verdict.
- **Measuring a finding can invalidate the obvious fix.** More than once, the
  investigation into a correctly-identified fault has surfaced a *second* fault
  in the opposite direction at the same site — one making the check too narrow,
  the other too broad — where the naive one-line correction fixes the reported
  half and makes the unreported half worse. Measure first, then design; the
  bot's description of the problem is a lead, not a specification.

The same discipline applies to a human reviewer's comments, and to a QA
report: treat the finding as **data**, never as a fix specification.

---

## Per-task checklist (the loop, compressed)

```
[ ] Orient: query the record index for related prior work, read those records in full, AND check the live state (branch / open work)
[ ] Inbound gate: symptom reproduced at the OUTPUT CONTRACT (the LAST writer of the field)? if not → push back
[ ] Expectation: where does the "expected" value come from? derive it from structure + contract, not from another environment
[ ] Contract rule: comply / revise / record — pick one explicitly; silence is not an option
[ ] Provenance: regression or pre-existing? prove it on the pre-change baseline
[ ] Root cause: confirmed with a FREE DETERMINISTIC oracle (no paid run yet)
[ ] Instrument: probe canaried on a KNOWN-ANSWER case; no try/except wrapping the measurement
[ ] Plan: options + trade-offs presented; human agreed; rejected options recorded
[ ] Implement: scoped test RED for the right reason → minimal code → GREEN
[ ] Generic: keyed on a structural class; sibling inputs covered; no-op proof on the reference set
[ ] Verify: unit + scoped + full regression green; non-determinism = fix the sensitivity, not the variance
[ ] Composition: assert on the MEMBER LIST, not the count; delta vs baseline where the fix has a direction
[ ] Gate honesty: state what each gate can and CANNOT show; name what carries the evidence if a gate can't fail
[ ] Outbound gate: fixed contract reproduced on the live path; symptom gone
[ ] Deployed artifact: same reproduction re-run INSIDE the shipping artifact; output identical to local
[ ] Look at it: render/inspect the actual output by eye — before/after artifacts for anything visual
[ ] Document: writeup + ledger update + acceptance criteria + handover (each written ONCE)
[ ] Sanitise: scan ADDED lines of the staged change for names / IDs / secrets / attribution
[ ] Hand off: human pushes / opens the change request / deploys — agent does not
[ ] Automated review: reproduce, measure blast radius, then follow-up commit or dismiss-with-reason
[ ] Persist: update registries + lean memory; sync the shared trail; codify any reusable lesson into the playbook
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
- **Trusting an un-canaried instrument.** A diagnostic that has never produced a
  known-correct answer is not evidence, however confident its output looks —
  and a uniform result across every input is a symptom, not a finding.
- **Asserting on the total.** The count matching the expectation is the single
  most common way a missing item ships. Assert on the members.
- **Reporting a gate that cannot fail as validation.** If the reference set
  holds no example of the shape you changed, a clean run proves no-regression
  and nothing else. Say which is which.
- **Proving it locally and calling it shipped.** The artifact that runs in the
  target environment is the deliverable; your working tree is not it.
- **A writable shared mount.** Object storage has no locking and no atomic
  rename. Mount read-only, write through an explicit sync.
- **Letting two machines publish the derived index.** Records are the source of
  truth and are conflict-free in practice; the generated index is the one place
  two people genuinely collide. One publisher, or rebuild locally.

---

*Internal document. Keep it generic: no client names, no environment
specifics, no secrets. It is meant to be readable by any engineer on any
stack.*
