# `s3-sync` — the shared engineering record, in runnable form

The scripts behind §15B of the technical guide. **These are the real ones**, copied from a
production installation and genericised — not a teaching reconstruction. Every warning in the
comments is there because it cost something.

> ⚠️ The one file NOT here is `config.env`. It names a bucket, two account profiles and a machine
> role, and it must never be committed, synced or packaged. Start from
> [`config.env.example`](./config.env.example) — and read it first, because **that is where the
> design lives**. Genericising the eleven scripts for this course changed *one line in one file*;
> everything environment-specific was already in the config.

## The model in one paragraph

A tarball moves a workspace between *your* machines. It does not solve **sharing**: the engineering
record is gitignored, so it cannot be linked from a ticket, and every teammate ends up with a
private index of the same history. Object storage fixes that — at the cost of last-writer-wins with
no merge. Everything here exists to make that cost survivable.

## Files

| Script | What it does |
|---|---|
| `data-pull.sh` | Store → local. Dry-run by default. Snapshots every local file it would replace, into `_prepull/<ts>/`, and prints the undo. Exits 3 on case-colliding keys. |
| `data-push.sh` | Local → store. Dry-run by default. **Refuses (exit 4)** if a shared hub file moved in the store since this machine last synced. Never uploads another machine's ledger. |
| `activity.sh` | Who pulled/pushed, per machine, from the append-only ledgers. |
| `publisher.sh` | The advisory baton for the single-writer role: `status` / `claim` / `release`. |
| `identity.sh` | Generates the machine-local `IDENTITY.md` with live checks (account authenticated, bucket reachable, mount present). |
| `ledger_check.sh` | Append-only check on pull: a line present locally and absent from the incoming copy is a deletion or a clobber. |
| `validate.sh` | A machine is not set up until this prints `MACHINE READY`. |
| `mount-data.sh` / `unmount-data.sh` | The **read-only** live view. Never write through a mount. |
| `_activity_log.sh` | One JSON line per run, to `_activity/<machine>.jsonl`. |
| `_config_check.sh` | Actionable failure when `config.env` predates the per-root model. |
| `delete.sh` | **Publisher only, baton held.** Deletes ONE file from the store on purpose and appends a tombstone to `_deletions.jsonl`; `--list`, `--check` (deleted files that came back), `--restore`, `--record-only`. Dry-run by default. |
| `_deletions.sh` | Sourced by pull, push and `delete.sh`: reads the tombstone list (404 = empty; any other failure = unreadable, never empty), moves tombstoned files aside on pull, excludes them on push. |

## Six things worth reading the code for

**1. The guard must cover both directions.** A pull clobbers *you*, and you can be made to notice.
A push clobbers *your colleague*, and you cannot — the evidence is on a machine you never look at.
Measured: two machines edited the status ledger the same afternoon and the second push replaced the
first wholesale. Eleven lines, no conflict, no error, and nothing on the pushing machine looked
wrong afterwards. It went a full day unseen. Most teams build the pull-side check, because it
protects the person running it. That is half the job.

**2. A per-machine file needs exactly one writer, enforced in the tool.** Splitting the sync ledger
into one file per machine removes contention *by design* — and the tool broke it anyway by
uploading every machine's file, including its permanently-stale copy of somebody else's. The first
symptom was not a corrupt file. It was **a wrong conclusion about a person**: with his record
erased, the dashboard said a colleague had never closed his day. He had.

**3. A guard can disable the instrument that proves the habit.** The pre-pull snapshot installed its
own `trap ... EXIT`; bash keeps one, so it silently replaced the one writing the activity ledger.
That block runs only on the real path, so dry runs kept logging and **every real pull went
unrecorded for two days** while the dashboard stayed populated and plausible. Ask what else claims
the same single-slot resource, and remember the real path and the rehearsal path are different code.

**4. A guard that cries wolf on day one teaches people to override it.** The push refusal first
compared timestamps alone and would have rejected a teammate's very first push — on files he had
just pulled and held byte-for-byte. It now asks whether the upload would actually *change* the
stored object. A false-positive rate is a safety property: every spurious refusal spends
credibility, and the override people learn to reach for (`--allow-clobber`) is the one that causes
the incident. Publish the escape hatch *and* the reason not to use it.

**5. Recovery expires.** Versioning is always described as "the recovery net", full stop. It will
almost certainly carry a lifecycle rule expiring noncurrent versions after ~30 days. So an
overwrite is recoverable *for 30 days, and only if somebody notices* — and nobody audits anyone
else's files. Say it literally in onboarding.

**6. "Deleted on purpose" is information sync cannot carry.** `aws s3 sync` sees a file removed
from the store as merely *missing*, so the next push from any machine uploads it again — a 176 MB
recording deleted by hand came back twice in two days. The fix is a tombstone list kept in the
store but **outside every synced root** (inside one, a contributor push would overwrite it with a
stale copy), written only by the publisher through `delete.sh`. A pull moves the file aside
(`_prepull/<ts>/deleted/`, never `rm`) only if the local copy still matches the recorded md5; a push
that cannot read the list **refuses** (exit 5), because an unreadable list read as empty is exactly
the bug it exists to stop. Note the 404 test: an expired SSO token also says "does not exist", so
only S3's own `NoSuchKey` counts as "no deletions yet".

## Try it

```bash
cp config.env.example config.env     # then edit it
./validate.sh                        # not set up until this says MACHINE READY
./data-pull.sh                       # preview  ->  --go to apply
./data-push.sh                       # preview  ->  --go to apply
./data-push.sh --root changes        # limit to one root
./activity.sh                        # who synced, when, per machine
./delete.sh <path> "why"             # publisher: preview a deliberate deletion  ->  --go
./delete.sh --list                   # what was deleted, by whom, why
```

⚠️ `--root` is a scope flag, not a speed trick. Measured on the real installation: full sweep 212s,
single root 123s — **about 40%, not an order of magnitude**, because most of the cost is inside the
one root that matters. Quoted from intuition it would have entered onboarding as "two minutes to
seconds" and stayed there.

The routine that drives all of this at the start and end of a session is the
[`day` skill](../../skills-plugins/.cursor/skills/day/SKILL.md).
