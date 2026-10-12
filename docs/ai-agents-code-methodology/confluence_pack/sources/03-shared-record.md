# Shared record (S3 sync) — Cursor

**Current as of 2026-10-05.** Entry point for sharing `sample-service`'s
**gitignored `data/`** — ticket documentation, the ticket knowledge graph,
diagnostics, and client source documents — across machines and teammates over S3.

Your machine's `data/` is a **working copy**. The bucket is the source of truth.

**Agents:** company standard is **Cursor**. Open the repo so `AGENTS.md` /
`.cursor/rules` load; they point at machine-local `IDENTITY.md`.

**Cursor skills for this page** (project `.cursor/skills/`, not always-on):

| Skill | Who | Does |
|---|---|---|
| **`day`** | everyone | `day start` pulls, refreshes the ticket status table (publisher writes it; everyone else gets a report-only summary) and briefs; on the publisher it also runs `delete.sh --check`; `day end` writes up and publishes; `day status` / `day baton` for collaboration |
| **`kg`** | everyone | history-first lookup — query the graph *before* grepping `data/changes/` |
| **`kg-refresh`** | contributor files a request; **publisher** rebuilds | never rebuild on a contributor machine |
| **`sanitise-diff`** | everyone | before code leaves the workbench |
| `atlassian` (Cursor rule) | everyone, optional | read-only Jira/Confluence lookups (GET only); writing stays with people |

New joiners: start at **For new joiners (Cursor)** (Confluence) **and** unzip
`ws-s3-sync-YYYYMMDD.zip` into `data/changes/` of the clone — same onboarding path. The pack
also carries `AGENTS.md` and `.cursor/`, which are gitignored and must be copied into the repo
root. Onboarders: **Onboarder checklist**.

---

## Where things stand

| | |
|---|---|
| Bucket | `s3://<shared-record-bucket>` (eu-central-1) |
| Prefix | `sample-service/data` |
| Contents | KG, ticket markdown, diagnostics, client binaries |
| Size at last measure | ~6,129 objects · ~1.2 GiB (2026-10-05) |
| Versioning | enabled — **noncurrent versions expire at 30 days** |
| Hand-authored KG names | **125** (2026-10-10; 2,163 nodes) — a rebuild keeps a third to a half (10-10 kept 45%); refresh = naming budget |

```
                    ┌────────────────────────────────────┐
                    │  s3://<shared-record-bucket>   │
                    │  prefix: sample-service/   │
                    │          data                      │
                    │   versioning ON — 30-day recovery  │
                    └────────────────────────────────────┘
        push ▲  ▲ pull          pull ▲            (read-only)
             │  │                    │             mount ⤵
   ┌─────────┴──┴─────┐   ┌──────────┴───────┐  ┌──────────────────┐
   │ PUBLISHER        │   │ CONTRIBUTORS     │  │ ~/s3-ws-data    │
   │ one machine      │   │ everyone else    │  │ read-only browse │
   │ holds the baton  │   │ own ticket dirs  │  └──────────────────┘
   │ owns the KG      │   │ never publish KG │
   └──────────────────┘   └──────────────────┘

  WRITE = aws s3 sync   (data-push / data-pull)  — real local disk
  READ  = mountpoint-s3 (mount-data)             — live, read-only
```

---

## ⚠️⚠️ Recovery expires

An overwrite is recoverable **for 30 days, and only if somebody notices.** Nobody
audits your rows. Push what you changed. Prefer pull before edit — **unless you have
unpushed local work**: dry-run first; sync does not delete inbound and will overwrite
newer local files with the store's older copy, and resurrect files you deleted locally.

---

## Structural rules

1. **WRITE via sync, READ via mount.** Mount is read-only on purpose — no locking,
   no atomic rename on object storage.
2. **Docs are the source of truth; the KG is derived — and single-writer.**
   `knowledge-graph/community_labels.json` is hand-authored names that *nothing*
   regenerates. One machine publishes the KG and claims a baton first.
3. **"Derived" is per file, not per folder.** Classify: source / derived /
   authored-inside-derived. The third must travel; never clobber it with a rebuild.
4. **Pairs must move together.** Stamp the names overlay with a fingerprint of the
   graph; health check must fail on mismatch.
5. ⚠️⚠️ **Guard BOTH directions.** A pull clobbers *you* and can be made to warn you.
   A push clobbers *your colleague*, and nothing on your machine looks wrong
   afterwards. Measured 2026-09-18: two machines edited `STATUS.md` the same
   afternoon and the second push replaced the first whole — **11 lines, no conflict,
   no error**, unnoticed for a day. `data-push.sh` now **refuses (exit 4)** when a
   shared hub file moved in the bucket after your last sync. See "Behavioural rules".
6. ⚠️ **A per-machine file has exactly ONE writer, enforced in the tool.** One file
   per machine removes contention *by design* — and the tool broke it anyway, pushing
   every machine's activity ledger including its stale copy of someone else's. **The
   first symptom was not a corrupt file: it was a wrong conclusion about a person** —
   the dashboard said a colleague had never closed his day. He had.

---

## Roles and baton scope (2026-09-10)

| Role | Who | Does |
|---|---|---|
| **Publisher** | one machine at a time | rebuilds/publishes KG; the only role that deletes from the bucket (with `delete.sh`) |
| **Contributor** | every other machine / teammate | owns `changes/sst-NNNN/`; pushes docs + **refresh requests**; **reads** KG |

```bash
./publisher.sh status | claim "why" | release
```

The baton gate in `data-push.sh` protects **`knowledge-graph/` only** — not the whole
sync. Contributors push ticket folders and other roots normally. When they lack the
baton a `--go` push prints *"knowledge-graph/: '<publisher>' holds the publisher baton … NOT an
error"* (expected) and still uploads **`refresh_queue/`** only from that tree.

> ⚠️ Two publishers destroy `community_labels.json` silently. Returning machines:
> set `MACHINE_ROLE="contributor"` and `./identity.sh --write` **before** pull/push.
>
> IAM still does **not** enforce this — `KnowledgeBaseS3` can write the whole prefix.
> Baton + convention are the real guard.

**Contributor asks for rebuild (no locks) — Cursor `kg-refresh` skill, or:**

```bash
bash ../../knowledge-graph/kg_refresh.sh request "why"     # from s3-sync/
./data-push.sh --go
```

One file per request under `refresh_queue/`. In Cursor: ask the agent to run
**`kg-refresh`**; it reads `IDENTITY.md` and **files a request** on a contributor
machine. Do **not** ask it to publish the KG there.

Publisher: Cursor **`kg-refresh`** on the publisher (or `kg_refresh.sh queue` before
rebuild; after health check `kg_refresh.sh queue --clear` then push). **`--clear`
deletes the consumed keys in the bucket** (a local-only archive leaves the original
keys in S3; the next pull resurrects them everywhere). Reconcile zombies against the
receipt — sync does not delete on pull. ⚠️ As of 2026-10-05 this still happens: 4 consumed
requests had come back to the bucket and were removed by hand; a machine that still holds them
locally re-uploads them on its next push.

**Query (everyone):** Cursor **`kg` skill** / Agent, or `bash data/knowledge-graph/kg_query.sh`.
`find` works with plain python3; full queries need a **Python 3.10+** venv with
`graphifyy==0.9.8` (recipe on the joiner page). History first — never grep `data/changes/` as
the first move.

---

## Access

| Profile | Account | Permission set | Here |
|---|---|---|---|
| `kb-s3` | <account-id> | `KnowledgeBaseS3` | ⚠️ **only** role that can WRITE this bucket |
| `dev-nonprod` | <account-id> | `DeveloperNonprod` | reads; PutObject denied by design |
| `shared-ecr` | <account-id> | `SharedEcrPull` | ECR fallback — not needed for sync |

Read-only teammate: uncomment `READ_PROFILE="dev-nonprod"` in `config.env`. Since 2026-10-05
every read (pull, validate, identity, push dry run) uses `READ_PROFILE`, so a read-only machine
gets **MACHINE READY ✅ (read-only)**; writes use `PROFILE` and fail loudly without `kb-s3`.
Exact `~/.aws/config` block: joiner page § 3.

> Never diagnose access from a CLI error without `aws sso logout && aws sso login` first.

---

## Machine identity (Cursor)

```bash
./identity.sh --write    # generates machine-local IDENTITY.md
```

`IDENTITY.md` records role + live checks (account, bucket, mount). Repository
**`AGENTS.md`** (and/or always-on `.cursor/rules`) **points at it** so every Cursor
session reads its role before shared writes. Gitignored, never synced, never zipped.

Re-run after any `config.env` change. The **`day`** skill re-reads this card before
any bucket write — a stale card once named a profile that had been deleted.

---

## Daily use — the `day` skill, not the raw scripts

```bash
# Do not run these from memory. In Cursor, ask for:
#   day start     pull the team's latest, then a short briefing
#   day end       write the day up, publish, confirm it landed
#   day status    who pulled/pushed recently; who holds the KG baton
#   day baton     hand the publisher role to another machine (travel / leave)

./data-pull.sh                # dry run DEFAULT — read overwrite intent if you have local edits
./data-pull.sh --go

# ... work locally in Cursor on real disk under data/changes/...

./data-push.sh
./data-push.sh --go           # contributors: the publisher-baton line is normal
```

Nobody runs `--delete`; removing a file is `delete.sh` on the publisher (below). `data-pull.sh` runs `ledger_check.sh` first
(advisory). Add `--root changes` to either script to skip the roots that never move
(measured 212s → 123s — a trim, not an order of magnitude). Quoted from intuition
it would have entered onboarding as "minutes to seconds"; **measure before you quote**.

**Do not run these from memory — use the Cursor `day` skill.** `day start` pulls and
briefs you; `day end` writes the day up, publishes, and confirms it landed. It is
role-aware: it reads `IDENTITY.md` before touching anything, because a contributor
and the publisher do different things. Every dangerous step answers a question first
(*is there unpublished local work? which files will this pull overwrite? may this
machine publish the KG?*) — and where the answer is ambiguous it **stops and asks**.

⚠️⚠️ **Why a skill and not this page.** "Pull at the start, push at the end" lived in
an operations document **for months without being followed** on the machine that
published. Nothing recorded a sync, so nothing could show the drift — the lapse was
invisible even to the person lapsing. A page cannot enforce a habit; a callable
Cursor skill can, and its audit trail (`./activity.sh`) is what made the two
failures above detectable at all.

Contributors never run KG publish / rebuild. Publisher rebuild = naming budget
(a third to a half of the 125 names survive).

### Deleting a file from the shared record

**Publisher only, since 2026-10-10.** `aws s3 sync` cannot tell "deleted on purpose" from "missing", so a file removed
by hand came back on the next push from any machine (a 176 MB recording returned twice). Deletions now go through one
tool, which records them in a deletion list in the bucket (`_deletions.jsonl`, outside every synced root):

```
./delete.sh "changes/sst-NNNN/file.ext" "why"         # dry run (default)
./delete.sh --go "changes/sst-NNNN/file.ext" "why"    # delete + record
./delete.sh --list                                    # everything deleted so far, by whom, why
./delete.sh --check                                   # deleted files that came back (report only)
./delete.sh --go --restore "changes/..." "why"        # lift a deletion record
```

Single files only (no folders, no wildcards), and only while the machine holds the baton. On every machine's next
pull the file is moved to `data/_prepull/<ts>/deleted/` (recoverable). A copy someone edited is kept and flagged,
and no push uploads it again. The bucket keeps the deleted version for 30 days. A push that cannot read the list
refuses with exit 5. The publisher's `day start` runs `delete.sh --check`.
**Never `aws s3 rm` and never `--delete` by hand: neither tells the other machines.**

### Ticket status table

`STATUS_Tickets.xlsx` (and the `STATUS_Tickets.md` / `STATUS_CR_PLAT.md` made from it) is refreshed from Jira and
GitHub at the publisher's `day start`. Status, type, links and row colour come from Jira; PR, merge date, on dev and
first release come from GitHub.

- **Only the publisher machine writes the workbook.** It is binary, so two writers overwrite each other with no merge.
  On every other machine the same script runs report-only (the Cursor session-start rule runs it; it needs `uv`).
- Publisher: close the workbook in Excel before `day start`, or the refresh is skipped. You may edit `brief`, `folder`
  and any column you add; everything else is overwritten from Jira/GitHub. One row per ticket; rows are added, never deleted.
- Everyone: read the `.md` files; fix wrong data in Jira, not in Excel.

**Read-only Jira/Confluence for agents (optional).** `data/changes/tools/atlassian/atl.py` (Cursor rule `atlassian`)
reads tickets, links, comments and Confluence pages. It only sends GET requests and cannot create, edit, comment or
transition anything; those stay with people. Each person uses their own API token in `~/.config/ils/jira.env`
(`chmod 600`). Never paste a token into a chat or a file under `data/`.

---

## Behavioural rules people break

0. ⛔ **"REFUSED: shared hub file(s) changed in the bucket" (exit 4) is not noise.**
   Somebody edited a shared file after you last synced and your copy differs. Diff
   yours against the bucket copy, fold in what you lack, push again. **These files are
   shared: the answer is a merge, not a winner.** `--allow-clobber` skips the check and
   exists only for "I am certain mine supersedes theirs" — using it to clear the
   message is how the 2026-09-18 loss happened. It never fires when your copy is
   byte-identical to the bucket's, so a file you just pulled is never a collision.
   The **`day`** skill must not pass `--allow-clobber` on its own initiative.
1. ⚠️⚠️ **Recovery expires** — see above; unpushed work makes blind pull unsafe.
2. **Shared ledgers are append-only** — `STATUS.md`, `TICKETS.md`, `FOLLOWUPS.md`,
   `TEST_MAP.md`, `CUSTOMER_GUIDANCE.md`. Add rows; never rewrite someone else's.
   Pull-time check is half the job: **also guard the push**. A per-machine ledger
   file needs exactly **one** writer enforced in the tool. Not in this list, because nobody
   hand-edits them: `STATUS_Tickets.xlsx`/`.md` and `STATUS_CR_PLAT.md` are regenerated from
   Jira + GitHub on the publisher every morning.
3. **Per-task folders need no coordination** — one folder per ticket, one owner.
4. **The shared store wins on divergence** — "I have it locally" is not an argument
   once theirs is published.
5. **Deletion belongs to one role and one tool** — the publisher, with `delete.sh`, which records it so every machine follows. A mirror-delete or `aws s3 rm` reaches nobody, and the next push brings the file back.
6. **Widening scope is a security event** — scan first, **canary the scanner**, then
   reconcile inventory (clean transfer ≠ completeness).
7. **Habit needs a mechanism** — Cursor **`day`** (`day start` / `day end`);
   documentation alone does not enforce pull/push.

### Lessons from shipping the contributor role broken

A documented role is untested code until someone executes it. Four defects of the
same family (described protocol ≠ running protocol):

1. **A guard scoped to a directory can swallow a control channel inside it** —
   `refresh_queue/` lived under `knowledge-graph/`; an early whole-tree baton blocked
   requests from leaving the machine. Enumerate children before gating a path.
   The **`kg-refresh`** skill exists so a contributor files a request instead of
   "helpfully" rebuilding.
2. **A "done" marker must reach the shared store** — local archive without deleting
   bucket keys resurrects the queue on every pull. Targeted delete of consumed keys;
   never contributor `--delete`.
3. **Sync does not delete on the way in** — remote removals stay local; stale local
   requests re-upload. Reconcile against the receipt. Fixed for deliberate deletions on 2026-10-10:
   `delete.sh` writes a record to the bucket's deletion list (`_deletions.jsonl`, outside every
   synced root), every pull moves the file aside, and no push uploads it again. The refresh-queue
   zombies above are a separate path and still apply.
4. **Therefore "pull before you edit" is unsafe with unpushed work** — dry-run first.
   `day start` checks for unpublished local work **before** pulling.

> **Simulate the role before you onboard into it.** A distinct `MACHINE_NAME` + empty
> tree exercises real scripts safely. Record honesty: a same-box simulation with the
> publisher's write credentials is **not** a two-person proof.

> ⚠️⚠️ **A safety guard can silently disable the instrument that proves the habit.**
> A pre-pull snapshot installed its own `trap ... EXIT` to clean up a temp file.
> Bash keeps **one** EXIT trap, so it replaced the one writing the activity ledger.
> That block runs only on the real (`--go`) path, so dry runs kept logging and
> every real pull went unrecorded for two days while the dashboard stayed
> populated and plausible. Ask what else claims the same single-slot resource;
> remember the real path and the rehearsal path are different code. A marker line
> that survived a real pull **byte-identical** separated *"written then
> overwritten"* from *"never written"* where a line count could not.

---

## Setting up a machine

1. AWS SSO → account **<account-id>** (profiles `dev-nonprod`, `kb-s3`). Prerequisites: AWS CLI
   v2 and python3 (the push guard and the activity log need it).
2. Unzip the pack into `<repo>/data/changes/`; check `PACK_BUILD.txt` against the announced build.
3. Optional, Linux/WSL only: `sudo apt-get install -y ./mount-s3.deb`. Skip on a Mac.
4. `cp templates/config.corporate.env config.env` — bucket / profile / region / prefix are
   pre-filled; edit `LOCAL_DATA`, `MACHINE_NAME`, and `READ_PROFILE` if read-only.
5. `./identity.sh --write`
6. `./validate.sh` → **MACHINE READY ✅**
7. First sync is a **pull** (`./data-pull.sh --go`), never a push.
8. In Cursor, from then on: **`day start`** / **`day end`** — not raw pull/push
   from memory.

Scripts live in the distributable zip (`ws-s3-sync-YYYYMMDD.zip`), built with `package.sh` on
the day it is sent (it warns about older packs; packs never travel through the bucket).

---

## Troubleshooting (short)

| Symptom | Fix |
|---|---|
| Token expired / ForbiddenException | Re-login SSO first; then re-read the error |
| AccessDenied on PutObject | On `dev-nonprod` by design — need `kb-s3` to write |
| Mount empty / transport endpoint | Wrong `PREFIX`, or `./unmount-data.sh` then remount |
| Write fails on mount | By design — write via `data-push.sh` |
| "holds the publisher baton … NOT an error" on contributor push | **Expected** — ticket roots + `refresh_queue/` still push |
| `validate.sh` NOT READY on a read-only machine | Set `READ_PROFILE="dev-nonprod"` in `config.env`; re-login |
| `REFUSED` / exit 4 on push | Colleague edited a hub file — **merge**, do not `--allow-clobber` |
| Teammate work vanished after your push | You used `--delete` from stale view, or overwrote a hub file — restore within 30 days |
| Queue never empties after `--clear` | Consumed keys came back from a machine that still holds them — delete those bucket keys and the local copies on that machine |
| `kg_labels.py check` lost/unnamed | Graph + labels unpaired — re-pull both; do not publish over it |
| Dashboard says a colleague never closed their day | Check whether **your** push overwrote their per-machine ledger |
| Pull says "N file(s) deleted upstream" | Normal: the publisher deleted them (`./delete.sh --list`); they are in `data/_prepull/<ts>/deleted/` |
| Pull says "your copy differs — kept" | You edited a file the publisher deleted. Tell the publisher before deleting it yourself |
| Push stops with exit 5 | Deletion list unreadable: `aws sso logout && aws sso login`, retry |
| Push says "not uploading N file(s) deleted upstream" | Correct: those files were deleted on purpose |
| A deleted file is back in the bucket | Publisher: `./delete.sh --check` lists it; find which machine still runs pre-10-10 scripts |
| Ticket status refresh "skipped — workbook is open in Excel" | Publisher: close `STATUS_Tickets.xlsx`, re-run `day start` step |

---

## Known gaps

- Full two-person live round-trip may still be unproven; simulated-role passes are
  partial. Next joiner completes the onboarder acceptance test — record the result.
- Never trust a filter you have not seen reject something.
- A clean dry-run is not a completeness check.
