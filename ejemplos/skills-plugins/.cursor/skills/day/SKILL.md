---
name: day
description: >-
  Start-of-day and end-of-day routine for the shared record. Run `day start` before any
  work (pull the team's latest, then a briefing) and `day end` before stopping (publish
  today's writeups). Also: who synced recently, and moving the KG publisher role for travel.
---

# day — open and close the working day

> **Why this is a skill and not just a doc.** The rule "pull at the start, push at the end"
> sat in an operations doc for months and was not being followed on the publisher machine —
> nothing recorded a sync, so nothing could show the drift. Documentation cannot enforce a
> habit; a callable routine can. Read this for the **shape**, not the commands: every
> dangerous step answers a question first, and where the answer is ambiguous it **stops and
> asks**.

The shared record under `data/` is only as current as the last sync, and nothing else
prompts it. Two moments, packaged:

```
day start     # pull the team's latest, then a short orientation briefing
day end       # publish today's work, and flag the KG if the corpus moved
day status    # who pulled/pushed recently, across machines; who holds the KG baton
day baton     # hand the publisher role to another machine (travel, leave, handover)
```

Everything below runs on **macOS, Linux and WSL** — plain `bash`, no PowerShell.
Course copy of the scripts: `ejemplos/metodologia/s3-sync/` (start from
`config.env.example` — **never** ship a real `config.env`).

## Step 1 — find the sync folder and read this machine's role

The role decides what you are allowed to do. Read it **before** any bucket write.

```bash
S3=""
d="$PWD"
while [ "$d" != "/" ]; do
  if [ -f "$d/data/changes/s3-sync/data-pull.sh" ]; then S3="$d/data/changes/s3-sync"; break; fi
  d="$(dirname "$d")"
done
if [ -z "$S3" ]; then echo "No shared-record sync in this repo (open <your-repo> root)."; fi
sed -n '1,20p' "$S3/IDENTITY.md"
```

No `IDENTITY.md`, or it looks stale? Regenerate — it is what the agent reads to learn its
role, and a stale card once named an AWS profile that had been deleted:

```bash
(cd "$S3" && ./identity.sh --write)
```

If `S3` is empty, tell the user this repo has no shared record and STOP.

## Step 2 — `day start`

1. **⚠️ Check for unpublished local work FIRST — a pull can overwrite it.**
   `aws s3 sync` transfers whenever the **size differs**, not only when the remote is
   newer, so a pull replaces a locally-edited file with the bucket's older copy and
   re-creates anything you renamed locally under its old name. No `--delete` needed.

   ```bash
   (cd "$S3" && ./data-push.sh --root changes)   # dry run — anything listed is local-only work
   ```

   `--root changes` limits the sweep to the only root that moves day to day (measured
   212s → 123s: a trim, not an order of magnitude). Fine for this check; use the full
   sweep when publishing.

   Nothing listed → go on. Something listed → say what it is and offer to publish it
   first; do **not** pull past it without the user's explicit go-ahead.

2. **Pull.** Never `--delete`. The script now protects you, but you must READ what it says.

   ```bash
   (cd "$S3" && ./data-pull.sh --go)
   ```

   Before applying anything it dry-runs, **snapshots every local file the pull would
   replace** into `data/_prepull/<timestamp>/`, and lists them. Two outcomes to act on:

   - **"⚠️ N existing local file(s) will be REPLACED"** — read that list aloud to the user.
     Shared hub files (`STATUS.md`, `FOLLOWUPS.md`, `SHARP_EDGES.md`, `TEST_MAP.md`,
     `_PENDING_*.md`) appearing there means a colleague's copy is landing on top of yours,
     and **each side may hold content the other lacks — that needs a merge, not a winner.**
     Diff the snapshot against the new file before doing anything else:
     `diff data/_prepull/<ts>/changes/STATUS.md data/changes/STATUS.md`
     To undo the whole pull: `cp -a data/_prepull/<ts>/. data/`
   - **Exit code 3, "CASE-COLLIDING FILES"** — two bucket objects differ only in
     capitalisation and map to one file on this machine. **Stop.** The pull would pick a
     winner at random. Delete the wrong-cased key in the bucket first; canonical casing for
     ticket docs is lowercase `sst-NNNN.md` (placeholder pattern).

   Credential error? **Re-login before concluding anything** — an expired cached token
   looks exactly like a permissions problem: `aws sso logout && aws sso login`.

3. **See who else has been active:** `(cd "$S3" && ./activity.sh)`

4. **Orient — history first, status second.** Newest `data/changes/_PENDING_*.md`, then
   `data/changes/STATUS.md` for your area, then `git fetch --all --prune` and
   `git status -sb`. Use the **kg** skill for prior art before designing anything — never
   a grep of `data/changes/` as the first move.

5. **Publisher machines only** (`IDENTITY.md` says PUBLISHER): check the baton and the
   refresh queue.

   ```bash
   (cd "$S3" && ./publisher.sh status)
   bash data/knowledge-graph/kg_refresh.sh queue
   ```

   Report what is pending; do **not** start a refresh unasked — it is ~100 naming
   judgements and a full hour, and a half-named graph passes no gate.

6. **Brief the user in a few lines**, then stop. `day start` prepares the machine; it
   does not choose the work.

## Step 3 — `day end`

1. **Write the day down before publishing it**: the ticket doc under
   `data/changes/<ticket>/`, a `STATUS.md` row, any follow-up in `FOLLOWUPS.md`. Work with
   no written record is indistinguishable from work that never happened.

2. **Preview, and read the file list.** This is the sanitisation moment — no keys, no
   secrets, nothing that should not enter the shared record.

   ```bash
   (cd "$S3" && ./data-push.sh)
   ```

   ⚠️ Watch for **fixture files** (`.docx`/`.pdf` under fixture / issue / sample dirs).
   An extractor run re-saves fixtures in place, and a re-saved fixture can keep its exact
   byte size while its hash changes. Do not push over the bucket's pristine copy — restore
   yours from the bucket instead.

3. **Publish.** Never `--delete`.

   ```bash
   (cd "$S3" && ./data-push.sh --go)
   ```

   A contributor push that reports it **skipped `knowledge-graph/`** is correct, not an
   error — only `refresh_queue/` goes up from a contributor machine.

   ⛔ **If the push exits 4 — "REFUSED: shared hub file(s) changed in the bucket"** — a
   teammate wrote one of those files after this machine last synced, and our copy differs.
   `aws s3 sync` has no merge, so pushing would replace theirs. **Read the named files out
   to the user, diff each against the bucket copy, and merge.** Do NOT pass
   `--allow-clobber` on your own initiative — it is for "the user has confirmed ours
   supersedes theirs", nothing less.

   ```bash
   (cd "$S3" && source ./config.env && \
     aws s3 cp "s3://$BUCKET/$PREFIX/changes/STATUS.md" - --profile "$PROFILE" | diff - ../STATUS.md)
   ```

   Measured 2026-09-18: a push four minutes after a colleague closed his day destroyed his
   entire `STATUS.md` section AND his activity ledger — and nothing on this machine looked
   wrong afterwards, so it went a full day unnoticed. The guard does not fire when our copy
   is byte-identical to the bucket's, so a file we just pulled is never a collision.

4. **If ticket docs changed, flag the graph** so the publisher knows a rebuild is due:

   ```bash
   bash data/knowledge-graph/kg_refresh.sh request "<what changed and why it matters>"
   (cd "$S3" && ./data-push.sh --go)
   ```

5. **Confirm it landed:** `(cd "$S3" && ./activity.sh)` — this machine's push should read
   minutes old.

## `day status`

```bash
(cd "$S3" && ./activity.sh)          # last pull/push per machine
(cd "$S3" && ./activity.sh --log)    # full event stream
(cd "$S3" && ./publisher.sh status)  # who may rebuild and publish the KG
```

⚠️ It reports what was **recorded**. A machine that has never run the instrumented scripts
shows nothing; absence of a record is not evidence of no activity.

## `day baton` — moving the publisher role

One machine publishes the knowledge graph, because `aws s3 sync` is last-writer-wins with
no merge: two publishers silently destroy each other's hand-authored community names. The
baton is an advisory lock kept **in the bucket**, so either machine can check it.

```bash
(cd "$S3" && ./publisher.sh status)
(cd "$S3" && ./publisher.sh release)            # outgoing machine, FIRST
(cd "$S3" && ./publisher.sh claim "why")        # incoming machine, SECOND
```

The receiving machine must also set `MACHINE_ROLE="publisher"` in `config.env` and re-run
`./identity.sh --write`, or its agent keeps reading CONTRIBUTOR and declines the work it
now owns. `claim --force` overrides a held baton — confirm with the user every time.

## Rules that hold in every branch

- **Never `--delete`.** Publisher-only, deliberate, and only right after a fresh pull.
- **Never push `knowledge-graph/` from a contributor.** The tool enforces it; do not work
  around it.
- **Re-login before diagnosing an access error** — the error describes your cached token.
- **The human owns outward actions.** This skill syncs the shared record; it does not push
  branches, open PRs, deploy, or message anyone.
