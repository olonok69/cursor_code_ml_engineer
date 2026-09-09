# Shared `data/` over object storage — sync + read-only mount

**What this replaces.** The travel runbook next door (`../machine-sync/RUNBOOK.md`)
moves the workspace between two machines by building a tarball and carrying it on a
USB stick. That works, and it stays as the fallback for a full machine bring-up —
but it is a *transport*, not a *shared home*. It cannot help when three machines and
two people all need the same always-current engineering record. This document is
that shared home.

Sanitised: bucket names, account identifiers, profiles and machine names below are
placeholders. The structure is the real one.

---

## What is shared, and what is deliberately not

Scope is **engineering knowledge only**:

- the written per-task records (`changes/**/*.md`)
- the derived ticket knowledge graph (`knowledge-graph/`)

**Not** shared: customer documents, fixtures, captures, rendered artifacts, videos,
or anything binary and large. That boundary is both a confidentiality line and a
size line, and it is far easier to widen later than to retract. Widening it needs
the sign-off of whoever owns the storage account — not a unilateral decision.

---

## Two access modes, and the rule

| | `data-push` / `data-pull` (sync) | `mount-data` (object-storage mount) |
|---|---|---|
| Where you work | real local disk, fast | a live view of the shared store |
| Good for | **writing** records, building the graph, git, grep | **reading**, browsing what teammates have |
| Concurrency | explicit push/pull; you see what moved | read-only, so nothing to clobber |
| Caveat | not live — you run it when you want | no locking, no atomic rename, partial writes visible |

> **Write via sync. Read via mount.** The mount is **read-only on purpose.** Object
> storage has no file locking and no atomic rename, so a writable mount invites
> corruption that surfaces weeks later as an unexplainable bug. The read-only mount
> is a safety property, not a limitation to engineer around.

---

## Source of truth vs. derived artifact

**The written records are the source of truth. The knowledge graph is derived from
them.** Everyone reads the graph; exactly **one machine publishes it**.

Per-task folders almost never collide — people work on different tasks. The single
genuine contention point in the whole system is the generated graph, because two
people rebuilding and pushing it will silently clobber each other.

> ### ⚠️ "Derived" is a property of a file, not of a folder
>
> An earlier version of this page offered *"rebuild locally and don't share the
> built graph at all — the graph is cheap to derive"* as the **preferred** option.
> **That is wrong, and it was corrected the hard way.**
>
> It holds only while the rebuild is **lossless**. In practice the generated tree
> also contains a **hand-authored** file — the curated community names — that
> nothing regenerates. A rebuild re-derives the graph's internal identifiers from
> scratch, so the names no longer attach to anything: measured on a real rebuild,
> **under 1% of them survived**, and even after fixing the underlying cause only
> ~38% carried across. Recreating them is an hour of judgement, not a command.
>
> Nor is the graph "cheap to derive": a full rebuild is a fan-out of extraction
> agents over the whole corpus.
>
> So classify **per file**, in three categories:
>
> | Category | Example | Must it travel? |
> |---|---|---|
> | Source | the written records | ✅ yes |
> | Derived | the built graph, indexes, caches | optional — saves a rebuild |
> | **Authored, living inside the derived tree** | the curated names overlay | ✅ **yes, always** |
>
> The third category is the trap: every rule you wrote about the folder says it is
> safe to discard.

**The resolution is therefore a single publisher** that owns `knowledge-graph/` as
its single writer. Everyone else pulls it and never pushes it. "Rebuild locally
instead" is only safe for a tree that is *purely* derived — check before assuming
yours is.

**Pairs must move together.** The names overlay is only meaningful against the exact
graph it was built from, but `aws s3 sync` compares each object independently, so a
machine can pull a new graph and keep an old overlay. That produces no error — just
names attached to the wrong clusters. Stamp the overlay with a **fingerprint of the
graph it was built against** and make the health check exit non-zero when they
disagree. A per-file sync cannot express atomicity; the consistency check has to
live in the data.

Enable **versioning on the bucket** either way. It is the recovery net for the day
someone gets this wrong — but see the expiry caveat in the next section before you
lean on it.

---

## Roles

| Role | Does |
|---|---|
| **Publisher** | Seeds the bucket; rebuilds and publishes the graph; the single writer of `knowledge-graph/` |
| **Contributor** | Owns their own tasks, pushes their records, **reads** the graph |

The publisher role is pinned to one machine until it is deliberately transferred.
Transferring it is a documented procedure, not an ad-hoc decision — the point of one
publisher is lost the moment two machines believe they hold the role.

**How a contributor asks for a rebuild — without any locking.** A contributor who
changes records does not rebuild; they flag it, and the publisher rebuilds. The flag
is deliberately **one file per request**:

```bash
kg_refresh.sh request "added the payment-retry record"   # -> refresh_queue/<utc>-<machine>.request
./data-push.sh --go
```

A single shared queue file would hit the same last-writer-wins problem as everything
else here and silently drop requests. **Distinct keys never collide**, so a queue of
one-file-per-request needs no coordination whatsoever. The publisher runs
`kg_refresh.sh queue` before rebuilding and `queue --clear` after the health check
passes.

> **Treat the single publisher as scaffolding, not architecture.** Pinning the rebuild
> to one person's machine stalls the moment that machine is off, travelling, or
> mid-task. The queue above is deliberately the *trigger contract*, so the rebuild can
> later move to a scheduled or event-driven job with **no change to anything
> contributors do** — the migration swaps the operator, not the interface. What still
> blocks a fully unattended run is the judgement step: naming the clusters the rebuild
> could not carry across.

---

## Machine identity — how the agent knows what it may do

This is the part that only exists because agents are involved, and it is the easiest
to skip.

Once the same trail is reachable from several machines with **different roles**, a
**Cursor** agent session must know *which machine it is on* before it acts.
Otherwise a contributor machine will helpfully rebuild and republish the
shared graph — the one thing its role forbids — and be entirely pleased with itself
for doing so.

Each machine declares its identity in its own `config.env`:

```bash
MACHINE_NAME=<this-machine>
MACHINE_ROLE=publisher      # or: contributor
```

Then:

```bash
./identity.sh --write        # generates IDENTITY.md
```

`IDENTITY.md` records the declared role **and runs live checks** — which account are
we authenticated as, is the bucket reachable, is the mount present. The repository
`AGENTS.md` (and/or always-on `.cursor/rules`) points at it, so every session reads
its own role first.

**`IDENTITY.md` is machine-local.** It is gitignored, never synced, and never
packaged. It is the one file that must *not* be identical everywhere. Re-run
`identity.sh --write` after any `config.env` change.

---

## The rules a shared store needs

Single-writer and pairs-move-together (above) are the *structural* rules. These are the
behavioural ones — the ones people break, because nothing stops them.

### ⚠️⚠️ Recovery has an expiry, and users own their own work

Versioning is routinely described as "the recovery net", full stop. That is a half-truth
worth correcting explicitly, because people plan around it.

A bucket with versioning on will almost always also carry a lifecycle rule expiring
**noncurrent** versions — 30 days is a common default. So an overwrite is recoverable
**for 30 days, and only if somebody notices in time**. Nobody is auditing other people's
files, and there is no backstop on day 31.

State it plainly in onboarding rather than implying a safety net that thins out:

> Pull before you edit. Push what you changed. If something of yours disappears, say so
> within the month or it is gone.

The alternative — a team that believes storage is durable in a way it is not — produces
exactly one kind of incident, and it is unrecoverable by the time anyone reports it.

### Shared ledgers are append-only

A handful of files are *shared by nature*: a status ledger, a shipped-work index, an open
follow-ups list, a test map, a record of what has been told to customers. Everyone writes
to them.

Object sync is last-writer-wins with no merge, so **rewriting one of these silently drops
somebody else's line**. There is no conflict, no error, no prompt. Make the rule explicit:
**add rows, never restructure someone else's**.

This is cheap to *detect* even though it is expensive to prevent. Append-only means a line
present locally and absent in the incoming copy is either a deliberate deletion or a
clobber — so a pull-time check that diffs the two and warns has essentially no false
positives. A few lines of shell, not a merge engine. That check is the visibility that
versioning does not give you: versioning makes the loss *recoverable*, not *noticed*.

### Per-task folders need no coordination at all

The reason this model works without locking is that the bulk of the corpus is partitioned
by construction: one folder per task, one owner per task. No protocol is needed for the
90% case. Reserve the ceremony for the genuinely shared files — the derived artifact and
the ledgers — and let everything else be free.

Design for this deliberately. If your layout forces two people into the same file for
routine work, no amount of process will save it.

### The shared store is authoritative on divergence

When a local copy and the published copy disagree, the published one wins. "I have it
locally" stops being an argument the moment someone else's version is the one everybody
pulls.

This needs saying out loud because the instinct runs the other way — your local copy is
the one you can see, and it feels more real. A team that has not agreed this in advance
resolves each divergence by argument instead of by rule.

### Mirror-delete belongs to one role

Covered under `--delete` below, but it belongs in this list too: the flag that propagates
a removal is the same flag that destroys unpushed work from a stale view. Scope it to the
publisher role, not to whoever remembers the caveat.

---

## Daily use

```bash
# Dry-run is the DEFAULT — nothing transfers until you say --go
./data-pull.sh              # preview, then:  ./data-pull.sh --go
./data-push.sh              # preview, then:  ./data-push.sh --go

# Browse the shared store live, read-only
./mount-data.sh             # mounts at ~/s3-<name>-data
ls -la ~/s3-<name>-data
./unmount-data.sh
```

**On `--delete`.** Passing it mirrors exactly, removing files on one side that were
deleted on the other. Leave it off by default: the common case is that a teammate is
pushing while you are, and an exact mirror from a stale local view erases their work.
Add/update-only is the safe default; mirror-delete is a deliberate, occasional
cleanup.

**Readiness.** A machine is only set up when `./validate.sh` prints `MACHINE READY`.
Don't skip it — it is what catches the half-configured profile that otherwise fails
on first push.

---

## Bring-up order

Order matters: the bucket must be seeded before anyone can pull from it.

1. **Publisher first** — install, seed the bucket, first graph publish.
2. **Each contributor** — install, set `MACHINE_NAME`/`MACHINE_ROLE`, `identity.sh
   --write`, then `./validate.sh` until it reports ready.

Each machine sets its own `LOCAL_DATA` to that machine's `data` path. Paths differ
per machine and are the most common setup mistake — derive them, don't copy them
from someone else's config (the "discover, don't assume" rule from the travel
runbook applies here unchanged).

---

## Before the first shared push — read this

- **Confidentiality.** Only records and the graph are in scope. Do not widen to
  customer data without the storage owner's sign-off.
- **Secrets.** Scrub the records for embedded credentials **before** the first push.
  This is not hypothetical: investigation notes routinely capture signed URLs and
  tokens *on purpose*, as evidence of a bug — and those are exactly the strings you
  do not want in shared storage. Run the sanitisation scan over the whole trail once,
  not just over a diff.
- **Versioning.** Turn it on before the first push, not after the first accident — and
  read its retention policy at the same time. A default lifecycle rule that expires
  noncurrent versions turns "recoverable" into "recoverable for N days".

---

## Why this is in the course

It closes the honest gap in the "durable trail" story. A trail that lives in a
gitignored directory on one laptop is a *personal* trail: it cannot be linked from a
ticket, it does not survive the machine, and the moment a second person joins, the
"single durable record" quietly becomes two divergent ones. Object storage plus an
operating model — narrow scope, write-via-sync, read-only mount, one publisher for
derived artifacts, and an identity each machine reads before acting — is what turns
it into a team asset.

The generic principle, with no tooling attached, is in
[`../../ai-agents-code-methodology/TECHNICAL.md`](../../ai-agents-code-methodology/TECHNICAL.md)
§7.
