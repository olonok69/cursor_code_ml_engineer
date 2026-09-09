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
>
> **This revision** turns to the gates' remaining blind spots and to the *time*
> dimension of the record. A gate can be sound, run clean, and still fail to
> distinguish the fix you shipped from a weaker one (§4); an in-artifact check
> proves nothing until it has been shown to fail on unfixed source (§4). A
> stated fact about the environment is a hypothesis, not evidence, and the
> exception handlers between you and a symptom are the first thing to suspect
> while diagnosing (§2). §6 gains the two dimensions it was missing — **time**,
> how in-flight state survives a session boundary, and **density**, the index
> tunable no structural gate can see. §7 gains **least privilege**: the obvious
> grant on a shared record widens access instead of narrowing it. It also adds
> the sharpest lesson of the set (§4): a test suite is downstream of your
> specification and cannot tell you the specification is wrong.

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
  with all several-hundred inputs reading as negative. Three rules make the
  shortcut safe:
  1. **Always canary against a known-answer case.** Before you trust a probe on
     unknown inputs, run it on one input whose answer you already know, and
     record that result next to the finding. A probe that cannot produce the
     known positive is measuring nothing.
  2. **Never wrap the measurement in your own `try/except → return False`.** Let
     it crash. A loud failure is a working instrument; a quiet one is a broken
     instrument that looks like evidence.
  3. **Canary the failure mode, not just the instrument.** A probe can be
     perfectly built and still prove nothing, because the perturbation it
     applies is not the one production applies. A synthetic test renamed the
     *containers* things were grouped into and churned a few percent of the
     items, recovered 100% of the mapping, and was reported as "verified". The
     real rebuild changed something the test never touched — the **identifiers
     of the items themselves**, 88% of them — and recovery fell to under 1%. The
     instrument was sound; the experiment was wrong. Before trusting a green
     canary, state in one sentence *what production does to this data* and check
     the canary does that same thing. If you cannot, say the gate is unproven —
     "the test I could build passed" is not "the risk is retired".
- **A rule that matches nothing looks exactly like a rule that works.** Filters,
  excludes, guards, allow-lists: when the correct behaviour is *silence*, success
  and total failure produce identical output. Four such defects were found in a
  single afternoon on one file — an exclude anchored at the wrong end of the path,
  another naming a directory that no longer existed under that name, a third that
  had never been reached — and every one of them had passed review, because the
  pattern *read* correctly. None was found by inspection. All four were found by
  running the operation in preview mode and **reading the list of what it actually
  matched and rejected**. The rule generalises: **never trust a filter you have not
  seen reject something.** If you cannot point at an item it excluded, you have not
  tested it, you have only read it.
- **A check must distinguish "no" from "could not ask."** A coordination lock
  reported *"nobody holds it"* whenever its read failed — expired credential, no
  network, denied permission all collapsed into the same reassuring answer, because
  the failure path defaulted to an empty result. The status command was merely
  misleading; the *claim* command used the same read, so an expired token would have
  granted the lock while somebody else held it, which is precisely the collision the
  lock existed to prevent. **A negative result and a failed measurement must not
  share an output.** When you write a check, enumerate its failure modes and make
  every one of them loud; reserve the quiet answer for the case you actually
  verified.
- **Rule out logic and configuration before "variance."** "The model is just
  being flaky" is a conclusion of last resort. When a system genuinely is
  non-deterministic, the bug is usually a **sensitivity**, not the variance
  itself: the same input yields a correct result on one run and a wrong one on
  the next because some heuristic sits right at a threshold. Fix the
  sensitivity (move the input away from the threshold, make the boundary
  explicit) — do not "fix" it by re-running until it's green. One green run on
  a non-deterministic system is not a pass.
- **Verify the premise, not just the steps.** A stated fact about the machine,
  the environment, or the identity you are running as is a **hypothesis, not
  evidence** — including one you stated yourself an hour ago. A procedure built
  on an unverified premise fails in the most expensive way available: every step
  executes correctly and the result is still wrong, so a trail of green checks
  points away from the cause. Verify the premise first, and design the check so
  that it *can actually fail* — a probe returning the same answer whether or not
  the premise holds has verified nothing. The specific trap for environment and
  access questions: **an error message describes the request you just made, not
  the state of the world.** A permission denial can mean the entitlement is
  absent, or merely that a cached credential expired. Diagnosing from the error
  text produced three separate wrong conclusions on the same question before
  anyone queried the authoritative directory directly.
- **Suspect the exception handlers between you and the symptom.** This is a
  *debugging heuristic, not a style rule* — handlers are frequently exactly
  right, and a blanket prohibition is not what the loop needs. But when a defect
  is invisible, intermittent, or presents as "variance", ask **which handler
  sits between you and it** before blaming logic or the model. A swallowed error
  arrives as a plausible value, and a plausible value ends an investigation.
  Two costs we can measure: a broad catch turned a crash into a
  degraded-but-successful result and the defect then ran for roughly **ten
  months** without a single report; and separately, a handler that *did* re-raise
  still dropped the original cause — so the re-raise preserved the failure and
  destroyed the only evidence of where it came from. **Re-raising is not enough;
  preserve the chain.** Having found such a handler, close it one of two ways:
  fix it, or **accept it in writing** in the durable record. An unrecorded
  decision to leave it is indistinguishable from not having noticed.

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

Five concentric layers, each a real gate:

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
   only here. **And prove the check can fail.** A harness that has only ever
   run against fixed source is not a gate, it is a screenshot: run it twice —
   once against the *unfixed* source, where it must reproduce the symptom, and
   once against the fix, where it must come out clean. The pair is the evidence;
   the second run alone is not.

There is a sixth layer nobody owns, and it is where the expensive failures live:
**the deployed artifact plus its configuration, together.** Layer 5 proves the artifact
is right. It does not prove the environment will let it start.

Two properties make this gap invisible. First, code and configuration frequently ship
through **different repositories with different reviewers and no ordering between them**
— so "merged" and "working" are separated by however long the second merge takes, and
nothing in either pipeline knows the other is pending. On one occasion that gap was four
hours of a downed shared environment; both changes were individually correct. Second,
the automated post-deploy check answers a *different question* than the one that broke:
a smoke suite calling the public interface passes cheerfully while a background listener
crashes at startup on a missing queue name, because nothing in the suite ever reaches
the listener. It reported green throughout the outage.

So: when a change consumes new configuration, say so explicitly in the handoff, name the
other repository, and state the required order. Prefer a service that **degrades loudly**
when its configuration is absent over one that consumes it at startup and dies quietly.
And when you add a post-deploy check, assert on the component that can actually fail —
not the one that is easiest to poll.

Keep each defect's scoped suite as a permanent artifact named for the defect,
so the next person sees both the guard and the example that motivated it.

**Reading the results is part of the gate.** Five habits separate a real pass
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
- **Ask whether the gate can tell your fix from a weaker one.** A gate that
  cannot fail is the trap above; the subtler one passes *identically* for two
  different candidate fixes, so the suite silently ratifies whichever you
  happened to write. We measured this on one defect: a minimal bounds guard and
  a bounds-guard-plus-clamp were **byte-identical on every case the unit suite
  could express**, and only a corpus-scale delta — counting the outputs that
  *changed* — separated them. Whenever you have chosen between two fix shapes,
  name the check that distinguishes them; if the honest answer is "none of the
  tests do", say which measurement does, and make it mandatory rather than
  optional. *(One measured instance. The shape is probably commoner than that,
  because the usual reason to prefer the broader fix is behaviour the narrow
  tests were never written to see.)*
- **Your suite cannot test your premise.** The previous habit is about two
  candidate fixes; this one is about the specification itself being wrong, and it
  is the more expensive of the two. A test you wrote and the code you wrote share
  an ancestor — your mental model of the problem. A test can only detect the code
  diverging from your intent; when the *intent* is the defective part, every test
  agrees with the bug. Writing more of them raises confidence without moving
  coverage of the actual risk, which is strictly worse than knowing you have not
  checked. We watched this twice in one day. A rule derived from three documents
  passed fifteen purpose-written tests and would have destroyed correct output on
  six of thirty-six real ones, because every case the author invented put the data
  where the author believed it lived. Hours earlier, a regression test reproduced a
  malformed input that failed for the wrong reason — six tests green against a
  defect the system never actually produces. **The trigger is a property of the
  change, not its size: when a change can only remove or alter existing output,
  and you already hold known-correct answers, run it against them.** That is not a
  broader test, it is a different instrument — a closed world of inputs you
  imagined, versus an open one you did not. Ask the question literally: *does this
  destroy a right answer?*

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

Everything above is *spatial* — what sits where, and how big it is. Two further
dimensions decide whether the architecture holds up in practice.

**Time — the session entry point.** Agent work is interrupted constantly: by
context limits, by the end of a day, by an urgent unrelated task. The
always-loaded core describes the *project*, never what you were in the middle
of, so with nowhere to put in-flight state it stays in the transcript — which is
precisely what does not survive. Keep **one rolling entry-point document**,
rewritten (not appended to) at the close of each working session and read first
at the start of the next. Only what is genuinely in flight earns a place: what
needs a human specifically, what is yours to build, what is blocked on someone
else, and — most valuable, most easily lost — **the caveats that would otherwise
be re-derived expensively or not at all**, such as which single gate is the only
one that can catch a given error. Two properties matter more than the format. It
is **one** file, replaced each time, because a folder of dated resume notes
becomes stale context that reads as current. And it is **deleted or superseded
on close**, for the same reason. Note what this actually is: a handoff to *your
own next Cursor context*, which happens far more often than §8's handoff across
people (or across irreversible actions), and is the one almost nobody writes down.
*(Observed over three days of deliberate use — enough to be confident in the shape,
not in the details.)*

**Density — the index has a tunable, and the structural gate cannot see it.**
The queryable index described above is built by some process with its own
parameters: how finely the source is divided before extraction, what threshold
groups things, how much context each unit carries. **Those parameters decide how
much of the record survives into the index, and the obvious health check cannot
detect a bad setting.** We rebuilt ours after a coarser division: the graph came
out materially thinner and the gate **passed**, because it tests that every node
is anchored, unique and reachable — properties a small graph satisfies *more*
easily than a large one. A structural gate measures integrity, never coverage.
So record the build parameters beside the artifact, treat the previous build's
node and edge counts as the baseline the next one is compared against, and read
a drop as a defect to explain rather than a tidier result. *(One rebuild: the
mechanism generalises, the magnitude is not established.)*

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
stale local view.

**Three behavioural rules the structural ones do not cover** (people break these
because nothing stops them):

1. ⚠️⚠️ **Recovery expires — and users own their own work.** Versioning is usually
   called "the recovery net", full stop. Half-truth: a lifecycle rule almost always
   **expires noncurrent versions after ~30 days**. An overwrite is recoverable *for
   30 days, and only if somebody notices*; nobody audits anyone else's files.
   Onboarding literal: *pull before you edit, push what you changed, and if
   something of yours disappears, say so within the month or it is gone.*
2. **Shared ledgers are append-only.** Status / follow-ups / shipped-work indexes
   are last-writer-wins with no merge: rewriting one silently drops somebody else's
   line — no conflict, no error. Add rows; never restructure someone else's. A
   pull-time warning (line present locally, absent incoming) has essentially no
   false positives — that is the **visibility** versioning does not give you.
3. **The shared store wins on divergence.** *"I have it locally"* stops being an
   argument once someone else's version is the published one. Agree it in advance;
   the instinct runs the other way because your copy is the one you can see.

**Source of truth vs. derived artifact — and the third category people miss.**
The written records are the source of truth; the queryable index from §6 is
**derived** from them. Everyone reads the index; exactly **one machine publishes
it**. Two people rebuilding and pushing the same generated index is the one
genuine contention point in an otherwise conflict-free system — per-task folders
rarely collide because people work on different tasks.

> ⚠️ **"Derived" is a property of a file, never of a directory.** This is the
> correction that cost real work. The obvious rule — *don't sync the built index,
> just rebuild it locally* — is safe only while the rebuild is **lossless**. It
> stops being safe the moment anything inside that generated tree is
> **hand-authored and unregenerable**: a curated set of cluster names, a tuned
> threshold file, a reviewed mapping. Rebuilding then *destroys* it, and because
> the file sits in the "derived" folder, every rule you wrote says it is safe to
> throw away. Classify per file — **source**, **derived**, or **authored-but-
> living-inside-derived** — and treat the third as source: it must travel, and it
> must never be clobbered by a stale copy.

**Pairs that must move together.** Sync tools move files **independently** — an
object sync compares each key's size and timestamp on its own. So two files that
are only meaningful *together* (a generated index and the curated overlay that
annotates it) can arrive from different builds, and the result is not an obvious
error but a **confident wrong answer**: labels attached to the wrong things. Give
the overlay a **fingerprint of the artifact it was built against** and make the
health check fail loudly when they disagree. A per-file sync cannot express
atomicity, so the consistency check has to live in the data.

**Coordinating without locks.** Object storage has no locking and no merge:
same-key writes resolve last-writer-wins, silently. Two patterns follow. First,
**single-writer for anything authored** — designate one publisher, and make the
role explicit rather than assumed. Second, when contributors need to signal the
publisher (*"I changed inputs, a rebuild is due"*), have each writer create **its
own uniquely-named file** rather than appending to a shared one. Distinct keys
never collide, so a queue of one-file-per-request is conflict-free with no
coordination at all — and it is the same interface a scheduled job can consume
later, so the manual publisher can be replaced without changing anything the
contributors do.

> **Treat the single-publisher rule as scaffolding, not architecture.** Pinning a
> shared artifact's rebuild to one person's machine stalls whenever that machine
> is off or busy. Design the trigger as data (the request queue above) so the
> rebuild can move to a scheduled or event-driven job later — the migration then
> changes *who runs it*, not the interface anyone uses.

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

**Least privilege — and why the obvious grant widens access.** The trail needs
exactly one capability: read, write and delete on **one** location in the shared
store. Granting that is the point at which teams reach for whatever role their
people already hold, and that is the mistake. A role or policy set is typically
provisioned into **every** environment it is assigned to and applies to **every**
person holding it — so attaching the write permission to the role you already
have does not grant access to one location in one environment, it grants it
everywhere that role exists, production included. The narrow instrument is a
**dedicated grant scoped to the single location**, attached to that one purpose
and nothing else.

Two things we got wrong, and would now do first. **Measure the entitlements you
actually hold before designing the request.** Ours turned out to be considerably
broader than anyone had asked for — inherited silently through group membership,
across environments nobody had thought about — and the request we had drafted
would have widened them further. It was written, reviewed, and never sent.
**Then ask the authoritative directory, never the tool's error message** (§2).
When you do file the request, state the *capability and the scope* rather than
naming a role, and check that a permission you are asking to have removed is not
the one thing the workflow depends on. Ours very nearly was.

**Before the first shared push.** Scrub the records for embedded secrets.
Investigation notes are the dangerous case: they often capture signed URLs,
tokens, or connection strings *on purpose*, as evidence, and those are exactly
the strings you do not want landing in shared storage. Run the sanitisation scan
from §8 over the whole trail once, not just over a diff, before it leaves the
machine for the first time.

### Widening the scope of a shared store is a security event

Each time the shared trail grows to cover a new class of content — records, then
diagnostics, then source material — it crosses a boundary that was never reviewed for
the new class. Two rules, both learned by nearly shipping the mistake:

**Scan before every widening, and canary the scanner first.** A scan over eleven hundred
files reported clean. The canary — the same scan against a deliberately planted
credential — *also* reported clean, so the first result meant nothing: one filename in
the list had been parsed as a command-line option, aborting the batch, while suppressed
error output and a zero exit code hid it. Repaired, the same scan found fifteen files
carrying signed URLs with live-format temporary credentials, captured deliberately as
evidence in old investigation notes. **The scanner is an instrument and needs its own
known-answer case**, every time, not once.

**A clean transfer report is not a completeness check.** "What I was asked to send, I
sent" is all a sync can tell you. It cannot tell you what it was never asked about. Two
whole directories and thirty source documents were omitted on one widening — the
documents because the include list was **case-sensitive** and the files used uppercase
extensions, the directories because nobody had added them to the scope list at all. Both
transfers reported success, and the follow-up preview reported nothing left to do.
**After any scope change, reconcile the local inventory against the published one and
account for every single difference** — including the ones you intend, in writing. The
differences you can explain are the point; the one you cannot is the finding.

---

## 8. Handoff — artifacts, sanitisation, human gate (Cursor)

**One tool.** This playbook assumes the company coding agent is **Cursor** end to
end. There is no formal handoff *from another agent product* into Cursor — the
human keeps the same role; only the session and the outward gates change.

"Handoff" here therefore means two things, both inside Cursor:

1. **Session continuity** — rewrite the rolling entry-point from §6 so the *next*
   Cursor chat (or the next day) does not re-derive caveats from a dead transcript.
2. **Human gate on outward actions** — the agent prepares; a human (or
   human-driven automation) takes every irreversible / external step.

Concretely:

- **Artifacts per change:** a writeup (root cause → fix → verification
  evidence), an update to the live status ledger, acceptance criteria framed
  for the sign-off reviewer, and a short **next-actions** note that states
  exactly what the human must do to ship (push, open/merge the change request,
  deploy, message stakeholders). That note is *not* a tool-migration checklist.
- **Sanitisation gate (mechanical, every time):** before anything leaves the
  workbench, scan the **staged change** for content that must not enter the
  permanent record — customer/partner identifiers, internal ticket IDs in
  code bodies, secrets, and agent self-attribution. Make it a pattern scan,
  not a judgement call. Watch the scan's own footguns: a naive diff scan
  matches *removed* lines too, so filter to **added** lines only, and exclude
  paths that are intentionally local/ignored. The one time you eyeball it
  instead of running the scan is the time something leaks. In Cursor, prefer
  the project **`sanitise-diff` skill** over ad-hoc judgement.
- **Role separation:** the Cursor agent authors the change and leaves the
  branch; it does **not** push, open/merge change requests, deploy, or message
  anyone unless the human **explicitly** asks in that session. Enforce with
  always-on rules + hooks (`.cursor/rules`, `.cursor/hooks.json`) and keep
  shipped artifacts reading as the human author's work (no agent attribution in
  code, commit messages, or change-request text).
- **Machine role before shared writes:** if the trail is on shared object
  storage, read machine-local `IDENTITY.md` first (`AGENTS.md` points at it) —
  a contributor session must not republish the derived index.

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
[ ] Premise: every stated fact about machine / environment / access verified against the AUTHORITATIVE source, not an error message
[ ] Root cause: confirmed with a FREE DETERMINISTIC oracle (no paid run yet)
[ ] Handlers: named the exception handlers sitting between you and the symptom; fixed, or accepted IN WRITING
[ ] Instrument: probe canaried on a KNOWN-ANSWER case; no try/except wrapping the measurement
[ ] Plan: options + trade-offs presented; human agreed; rejected options recorded
[ ] Implement: scoped test RED for the right reason → minimal code → GREEN
[ ] Generic: keyed on a structural class; sibling inputs covered; no-op proof on the reference set
[ ] Verify: unit + scoped + full regression green; non-determinism = fix the sensitivity, not the variance
[ ] Composition: assert on the MEMBER LIST, not the count; delta vs baseline where the fix has a direction
[ ] Gate honesty: state what each gate can and CANNOT show; name what carries the evidence if a gate can't fail
[ ] Discrimination: name the check that separates the fix you chose from the weaker candidate — "the suite" is usually not it
[ ] Premise vs implementation: if the change can only REMOVE or ALTER output, run it against known-correct real data — your own tests cannot disagree with your own model
[ ] Outbound gate: fixed contract reproduced on the live path; symptom gone
[ ] Deployed artifact: reproduction re-run INSIDE the shipping artifact; PROVEN to fail on unfixed source first; output identical to local
[ ] Look at it: render/inspect the actual output by eye — before/after artifacts for anything visual
[ ] Document: writeup + ledger update + acceptance criteria + next-actions note (each written ONCE)
[ ] Sanitise: scan ADDED lines of the staged change for names / IDs / secrets / attribution
[ ] Human gate: human pushes / opens the change request / deploys — Cursor agent does not (unless explicitly asked)
[ ] Automated review: reproduce, measure blast radius, then follow-up commit or dismiss-with-reason
[ ] Persist: update registries + lean memory; sync the shared trail; codify any reusable lesson into the playbook
[ ] Continuity: rewrite the single rolling entry-point doc — what is in flight, and the caveats that would be re-derived expensively (next Cursor session)
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
- **Reading a structural gate as a semantic one.** A check that every item is
  present, unique and correctly wired says nothing about whether any of it is
  *right*. A migration reported a clean bill of health — every group matched, none
  lost, no orphans — while **56% of the carried-over names did not describe the
  thing they were attached to**, because the fallback had matched on a shallow
  proxy. A wrong label is worse than a missing one: a missing one asks a question,
  a wrong one answers it incorrectly and sends the next person to the wrong place.
  When a value's correctness is a matter of *meaning*, no automated check retires
  it — schedule the human read and say so in the gate's description.
- **Believing a green canary that never applied the real perturbation.** See §2
  rule 3: "the test I could build passed" is not "the risk is retired".
- **Reporting a gate that cannot fail as validation.** If the reference set
  holds no example of the shape you changed, a clean run proves no-regression
  and nothing else. Say which is which.
- **Proving it locally and calling it shipped.** The artifact that runs in the
  target environment is the deliverable; your working tree is not it.
- **Trusting a rule you have never seen reject anything.** When correct behaviour is
  silence, a broken rule and a working one are indistinguishable. Read what it matched.
- **Letting a failed measurement return the same answer as a negative result.** "Nobody
  holds the lock" and "I could not find out" must never print the same line.
- **Reading a green deployment pipeline as evidence the service runs.** A smoke suite
  that exercises the public interface says nothing about a background listener that
  fails to start. Assert on the thing that broke, not the thing that is easy to poll.
- **Shipping code and its configuration through separate pipelines with nothing
  sequencing them.** Each repository is individually correct and the composition is
  undefined; the gap between the two merges is an outage window nobody is watching.
  If they must be split, the code must degrade loudly when its configuration is absent
  — not consume it at startup and die quietly.
- **A writable shared mount.** Object storage has no locking and no atomic
  rename. Mount read-only, write through an explicit sync.
- **Letting two machines publish the derived index.** Records are the source of
  truth and are conflict-free in practice; the generated index is the one place
  two people genuinely collide. One publisher, or rebuild locally.
- **Treating a green suite as evidence that the specification is right.** The
  tests and the defect share an ancestor: your model of the problem. When that
  model is what is wrong, every test agrees with the bug, and adding tests only
  raises confidence. Real known-correct data is the only instrument that can
  disagree with you.
- **A gate that cannot tell two candidate fixes apart.** Distinct from a gate
  that cannot fail: this one passes for *both*, so the suite silently ratifies
  whichever fix you happened to write. Name the measurement that separates them.
- **An in-artifact check never run against unfixed source.** It has not been
  shown to fail, so it is a screenshot, not a gate.
- **Building a procedure on an unverified premise** about the machine, the
  environment, or the access you hold — and then diagnosing that premise from an
  error message rather than the authoritative source.
- **Leaving a suppressed error unrecorded.** Fixing the handler and accepting it
  are both legitimate; silence is not, and it reads identically to not having
  noticed.
- **Keeping in-flight state only in the transcript** — the one part of the
  session guaranteed not to survive it.
- **Reading a structural index gate as a coverage gate.** A thinner index passes
  integrity checks *more* easily than a full one. Compare against the previous
  build's counts.
- **Granting the shared record's write access through a role you already hold.**
  A permission set lands in every environment it is provisioned into; the narrow
  instrument is a dedicated, single-location grant.

---

*Internal document. Keep it generic: no client names, no environment
specifics, no secrets. It is meant to be readable by any engineer on any
stack.*
