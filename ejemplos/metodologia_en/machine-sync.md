# A real runbook: syncing the workspace across machines

> **Status note (updated).** This tarball + USB runbook is still valid and is
> the path for a **full bring-up** of a new machine. But it is **no longer** how
> day-to-day engineering-record sync works: that moved to
> **shared storage (S3)**. Jump to
> [§ Evolution: from tarball to shared storage](#evolution-from-tarball-to-shared-storage)
> at the end for what changed and why. Everything below still reads the same: the
> principles it illustrates (lean context, ops with guardrails, "discover, don't assume")
> did not change.
>
> ## Cursor adaptation (read me first)
>
> This runbook was born in a **Claude Code** environment (`~/.claude`, skills `/kg`, `CLAUDE.md`).
> The **principles** (asymmetric sync, agent with guardrails, evidence, human on externals) apply
> the same in Cursor. What changes:
>
> | Claude Code | Cursor |
> |---|---|
> | Pointer in `CLAUDE.md` | Pointer in `AGENTS.md` / on-demand rule |
> | Bundle of `~/.claude` (skills + memory) | Skills in `.cursor/skills/` or `~/.cursor/skills/`; Cursor memories ≠ `MEMORY.md` |
> | `codegraph` MCP in `~/.claude.json` | Re-pin `--path` in `.cursor/mcp.json` on the laptop |
> | `/kg-refresh` Claude skill | Cursor pack skill `kg-refresh` + same `kg_refresh.sh` scripts |
>
> Do not blindly copy the `~/.claude` tarball as “Cursor setup.” Bring `data/`, git repos, and
> reinstall the `.cursor/` surface (methodology pack bootstrap).
>
> ---
>
> Real procedure (sanitized) to move the ILS workspace between the **main machine** and a
> **laptop** (travel). A good example of three methodology things at once:
> **durable memory loaded on demand**, **agent-driven ops with guardrails**, and
> **"discover, don't assume"**. Lives under `data/` (gitignored) — machine/ops content, never
> committed.
>
> Always-on orientation does **not** hold the full runbook: there is a **one-line pointer** ("moving the
> workspace main ⇄ laptop? load `data/machine-sync/RUNBOOK.md`"). It loads **only when needed**.

## The idea: asymmetric sync

| Direction | Strategy | Why |
|---|---|---|
| **Outbound** (main → laptop, before travel) | **FULL COPY** | One tarball carries the whole workspace + home config; the laptop boots from an identical clean state. |
| **Inbound** (laptop → main, on return) | **DELTA ONLY** | Code is already on GitHub → bring with `git fetch`. Only gitignored `data/` docs (a few MB) travel in a small tarball. |

Transfer medium: **USB** (mounts in WSL as `/mnt/<letter>`). A FAT32 USB does not preserve
Linux permissions/symlinks — fine: everything goes inside the `.tar.gz`, which preserves them internally.

## Cross-cutting principle: "discover, don't assume"

Paths and dotfile layout **differ by machine**. Commands **derive** the workspace root instead of
hardcoding it:

```bash
WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)   # derive the root, don't assume it
echo "workspace: $WS"
# Re-check "machine facts" when time passes (drift):
ls -ld /home/$USER/.aws /home/$USER/.gnupg /home/$USER/.ssh /home/$USER/.claude
```

A **"machine facts" table** documents what varies (workspace root, whether `~/.aws` is a symlink or
real dir, whether `~/.gnupg` exists, the repo list, last tar size) — with a "confirm before you
trust." It drifts over time: the repo list **grows** (a new repo was added without touching the
command, because `-C` takes the whole directory), and the tar size too. Re-verify it every trip.

## Outbound — full copy (real command, sanitized)

Three fixes born from real failures are baked in: correct `-C`, `-h` to **dereference the
`.aws` symlink** (otherwise the laptop gets a dead link and AWS CLI unconfigured), and skip
`.gnupg` if it does not exist (otherwise `tar` errors):

```bash
WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)
STAMP=$(date +%Y%m%d)

tar -czhf ~/ils-migration-$STAMP.tar.gz \
  --exclude='*/node_modules' --exclude='*/.codegraph' \
  --exclude='*/.venv' --exclude='*/.venv-win' \
  --exclude='*/__pycache__' --exclude='*/.pytest_cache' \
  --exclude='*/.ruff_cache' --exclude='*/.mypy_cache' --exclude='*.pyc' \
  -C "$(dirname "$WS")" "$(basename "$WS")" \
  -C /home/$USER .claude .aws .ssh
ls -lh ~/ils-migration-$STAMP.tar.gz   # expect ~1 GB+ (grows); if KB, the -C was wrong
```

**Copy to USB — real gotchas (from a trip):**

- **WSL does not auto-mount a USB.** A USB you plug in *after* starting WSL does not appear alone under
  `/mnt/<letter>` (the mount point exists but empty). Mount it by hand:
  ```bash
  sudo mount -t drvfs F: /mnt/f    # replace with the real USB letter in Windows
  ```
- **Verify byte for byte before ejecting.** The mount is 9p (slow); after `cp`, `sync` and compare exact
  sizes — nothing like "it looks like it fits":
  ```bash
  cp ~/ils-migration-$STAMP.tar.gz /mnt/f/ && sync
  stat -c %s ~/ils-migration-$STAMP.tar.gz /mnt/f/ils-migration-$STAMP.tar.gz   # must match
  ```
- **Size the USB upward.** The bundle **grows** as repos are added (excluding venvs/caches: ~0.9 GB →
  ~1.5 GB in a few weeks). A 4 GB USB fits *one* bundle, with no margin for two.
- **Keep a prior full tar** as a safety net before any extract on the destination.

On the laptop: **park** (rename, don't delete) any prior workspace, extract, and **recreate the
excluded heavies** (`python -m venv`, `npm install`) per repo you will run. The AWS CLI **binary**
does **not** go in the bundle (system install) — reinstall on the destination and do
`aws sso login` once (the cached token travels expired). Same for **navigation tooling**: the
`.codegraph/` index is excluded (absolute paths, machine-local) and an idempotent `target-setup.sh`
reinstalls the CodeGraph CLI, updates GSD if behind, **fixes the MCP `--path`** to the real laptop
root, and rebuilds the index (`codegraph init`).

## Inbound — delta only (the return)

No full copy on the way back: it would clobber whatever the main machine did meanwhile.

1. **Code** → normal PRs from the laptop; on main, only `git fetch origin` (read-only).
2. **Gitignored `data/` docs** → the only physical that travels; packed from the repo root
   (repo-relative paths) and accompanied by `INSTRUCTIONS.md` + `MANIFEST.txt`.

## Two gaps closed by a few subcommands (bring-up + memory)

A real case: the workspace carries a **ticket knowledge graph** (skill `kg` / `/kg` in Claude, see
[`../../docs/KNOWLEDGE_GRAPH.md`](../../docs/KNOWLEDGE_GRAPH.md)). Travel surfaces two gaps solved
with idempotent subcommands, not easy-to-forget manual steps:

- **Bring-up from scratch (new laptop).** The bundle brings the already-built graph and some tooling,
  but **not** the `graphify` package or a correct interpreter. One command fixes it:
  ```bash
  bash data/knowledge-graph/kg_refresh.sh bootstrap   # install package, pin interpreter, smoke-test kg
  ```
  In Cursor: also re-bootstrap `.cursor/` (MCP `--path`, skills) if that machine did not have it.
- **Claude memory does not travel in the delta.** Classic inbound excludes `~/.claude`. If you use Cursor,
  decide explicitly what travels (`data/changes/`, snapshots) — do not assume IDE memories
  sync themselves:
  ```bash
  bash data/knowledge-graph/kg_refresh.sh snapshot-memory
  # on main:
  bash data/knowledge-graph/kg_refresh.sh restore-memory
  # then skill kg-refresh (Cursor) or /kg-refresh (Claude)
  ```

For the **laptop agent**, a single entry point —`LAPTOP_START_HERE.md`— orchestrates: restore
the bundle → `bootstrap` → orientation (`AGENTS.md` / rules, skill `kg` history-first) → delta back.
The graph is a **derived** artifact: it is rebuilt where the current corpus is. ⚠️ **But the curated
names overlay does travel both ways** — it lives inside the generated tree and nothing regenerates it,
so rebuilding without it leaves every community unnamed (see the rules table at the end).

## Landing is agent-driven — with guardrails

The delta's `INSTRUCTIONS.md` is written **for a coding agent** on the main machine. Its only
job is to **land the delta safely**, not to implement anything. Excerpts (sanitized):

> *"You are an agent on the MAIN machine. Your ONLY job is to land this delta safely. You are NOT
> implementing features, NOR merging PRs, NOR pushing."*

Mandatory guardrails:

- **Non-destructive only.** No `rm -rf`/reset/overwrite except as specified. **Never two file-moving
  operations at once** on a Windows mount `/mnt/c|d` (a prior session lost a
  workspace to a concurrent `rm`/`chmod` there).
- **No remote git writes.** No commit/push/merge/PR. `git fetch` (read-only) is the only network op.
- **Backup before overwrite.** The only file the delta may clobber is `STATUS.md`: copy to
  `STATUS.md.mainbak` **first**, then `diff`.
- **STOP and ask** if a "STOP condition" holds (e.g. the `diff` reveals the main machine
  made its **own** edits to `STATUS.md` → it was not asleep → do not clobber; restore and ask).
- **Discover paths** (Step 0): `find … -name document-parser-lambda`, do not assume the path.
- **Verify and report**: count expected files, PR states, and summarize without having made any
  commit/push.

```bash
# STATUS.md reconciliation — with judgment, not blind:
cp data/changes/STATUS.md data/changes/STATUS.md.mainbak   # backup FIRST
tar -xzf "$TARBALL" -C "$REPO"                             # paths relative to repo root
diff data/changes/STATUS.md.mainbak data/changes/STATUS.md # only additions? -> keep the new
#                                                            main had its own edits? -> STOP
```

## Why this is a good talk example

It gathers methodology principles in an **ops** task, not code:

- **Durable memory, on demand:** the runbook is not in always-on orientation; there is a pointer.
- **The human owns externals:** the agent lands the delta but does **not** push/merge; and stops if
  there is ambiguity.
- **Evidence before claims:** count files, `diff`, PR states — report facts.
- **Non-destructive + "discover, don't assume":** rename instead of delete; derive paths.

> Full detail (every step, the machine-facts table, `hash -r` and CLI shadowing
> gotchas) in the project's original `RUNBOOK.md`. Here goes the reusable, sanitized part.

## Evolution: from tarball to shared storage

The runbook above solves **transport** between two of your machines. It does not solve
**sharing**. As soon as a third machine and a second person appear, three
costs become obvious:

- The record lives in a gitignored directory → **cannot be linked** from a
  ticket, a PR, or an acceptance doc: the path only resolves on your machine.
- Moving between machines degenerates into *pack everything and copy it*: slow, easy to
  forget, and silently incomplete.
- Each teammate builds their **own private index** of the same supposedly shared
  history. The "single durable record" ceases to exist as soon as
  there are two people.

The answer is to put the record in **shared object storage**, with an
operating model. The model matters more than the technology:

| Rule | Why |
|---|---|
| **Narrow scope**: only `changes/**/*.md` + the graph | Confidentiality and size. Widening later is easy; retracting is not. |
| **Write via sync, read via read-only mount** | Object storage has **no** locking or atomic rename. A writable mount invites corruption that shows up weeks later. |
| **Dry-run by default**, explicit `--go`; `--delete` separate | The normal case is a teammate pushing at the same time; an exact mirror from a stale local view **deletes their work**. |
| **Docs are the source of truth; the graph is derived** | Per-ticket files almost never collide. The generated graph is the **only** real contention point → **one** machine publishes it. ⚠️ "Rebuild locally" is only safe if the generated tree is *purely* derived — see the note below. |
| **"Derived" is a property of the file, not of the folder** | Inside the generated tree lives a **hand-authored** file (the curated community names) that nothing regenerates: on a rebuild, **<1%** survived. Classify per file — *source* / *derived* / *authored inside derived* — and treat the third as source. |
| **Pairs must move together** | The names overlay is only meaningful against the graph it came from, but sync compares **object by object** → new graph + old names = names glued to the wrong community, **with no error**. Stamp the overlay with a **fingerprint of the graph** and make the health check fail loudly. |
| **Coordinate without locks** | To request a rebuild, each contributor writes **their own file** in a queue (`refresh_queue/<utc>-<machine>.request`). Distinct keys never collide; a shared queue file would be lost to last-writer-wins. It is also the same contract a scheduled job will consume. |
| **Each machine declares its identity** | See below: this is what is specific to working with agents. |

### What is specific to agents: the machine has a role

This detail only appears when the same record is reachable from several machines
with **different permissions**, and it is the easiest to miss: an agent session
must know **which machine it is on and what it is allowed to do** *before* acting. If
not, a *contributor* machine will rebuild and republish the shared graph —
exactly the one thing it must not do — and report it as work well done.

The solution is small: each machine declares `MACHINE_NAME` and `MACHINE_ROLE` in its
config, a **machine-local** `IDENTITY.md` is generated (with live checks: which
account is authenticated, whether the bucket responds, whether the mount is up), and the
repo's `AGENTS.md` (or `CLAUDE.md` in Claude Code) **points at it**, so every
session reads its own role first. `IDENTITY.md` is the only file that **must not**
be the same everywhere: gitignored, never synced, never packed.

> Full sanitized runbook (access modes, roles, bring-up order, checklist
> before the first push): [`../../docs/synchro/s3-sync/README.md`](../../docs/synchro/s3-sync/README.md).
> The generic principle, without tools:
> [`../../docs/ai-agents-code-methodology/TECHNICAL.md`](../../docs/ai-agents-code-methodology/TECHNICAL.md) §7.

### What still holds from the tarball

Full bring-up of a new machine. Shared storage brings the
**docs and the graph**; it does not bring the workspace, nor the agent surface (`.cursor/` /
`~/.claude`), nor venvs, nor the navigation index. For that the bundle +
`target-setup.sh` above remains the path — and the agent-driven landing
guardrails (non-destructive, no remote writes, backup before
overwrite, STOP on ambiguity) apply the same.
