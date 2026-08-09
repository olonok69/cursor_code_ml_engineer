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
people rebuilding and pushing it will silently clobber each other. Two acceptable
resolutions, in order of preference:

1. **Rebuild locally from the synced records** (`/kg-refresh`) and don't share the
   built graph at all. The records are already shared; the graph is cheap to derive.
2. **Designate one publisher machine** that owns `knowledge-graph/` as its single
   writer. Everyone else pulls it and never pushes it.

Enable **versioning on the bucket** either way. It is the recovery net for the day
someone gets this wrong.

---

## Roles

| Role | Does |
|---|---|
| **Publisher** | Seeds the bucket; rebuilds and publishes the graph; the single writer of `knowledge-graph/` |
| **Contributor** | Owns their own tasks, pushes their records, **reads** the graph |

The publisher role is pinned to one machine until it is deliberately transferred.
Transferring it is a documented procedure, not an ad-hoc decision — the point of one
publisher is lost the moment two machines believe they hold the role.

---

## Machine identity — how the agent knows what it may do

This is the part that only exists because agents are involved, and it is the easiest
to skip.

Once the same trail is reachable from several machines with **different roles**, an
agent session (Cursor or Claude Code) must know *which machine it is on* before it
acts. Otherwise a contributor machine will helpfully rebuild and republish the
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
orientation doc (`AGENTS.md` in Cursor, `CLAUDE.md` in Claude Code) points at it, so
every session reads its own role first.

**`IDENTITY.md` is machine-local.** It is gitignored, never synced, and never
packaged. It is the one file that must *not* be identical everywhere. Re-run
`identity.sh --write` after any `config.env` change.

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
- **Versioning.** Turn it on before the first push, not after the first accident.

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
