# Shared record (S3 sync) — Cursor

**Current as of 2026-09-09.** Entry point for sharing `document-parser-lambda`'s
**gitignored `data/`** — ticket documentation, the ticket knowledge graph,
diagnostics, and client source documents — across machines and teammates over S3.

Your machine's `data/` is a **working copy**. The bucket is the source of truth.

**Agents:** company standard is **Cursor**. Open the repo so `AGENTS.md` /
`.cursor/rules` load; they point at machine-local `IDENTITY.md`.

New joiners: start at **For new joiners (Cursor)** (Confluence) **and** unzip
`ils-s3-sync-YYYYMMDD.zip` — same onboarding path. Onboarders: **Onboarder checklist**.

---

## Where things stand

| | |
|---|---|
| Bucket | `s3://ils-nonprod-knowledge-base` (eu-central-1) |
| Prefix | `document-parser-lambda/data` |
| Contents | KG, ticket markdown, diagnostics, client binaries |
| Size at last measure | ~4,675 objects · ~888 MiB (2026-09-04) |
| Versioning | enabled — **noncurrent versions expire at 30 days** |

```
                    ┌────────────────────────────────────┐
                    │  s3://ils-nonprod-knowledge-base   │
                    │  prefix: document-parser-lambda/   │
                    │          data                      │
                    │   versioning ON — 30-day recovery  │
                    └────────────────────────────────────┘
        push ▲  ▲ pull          pull ▲            (read-only)
             │  │                    │             mount ⤵
   ┌─────────┴──┴─────┐   ┌──────────┴───────┐  ┌──────────────────┐
   │ PUBLISHER        │   │ CONTRIBUTORS     │  │ ~/s3-ils-data    │
   │ one machine      │   │ everyone else    │  │ read-only browse │
   │ holds the baton  │   │ own ticket dirs  │  └──────────────────┘
   │ owns the KG      │   │ never push KG    │
   └──────────────────┘   └──────────────────┘

  WRITE = aws s3 sync   (data-push / data-pull)  — real local disk
  READ  = mountpoint-s3 (mount-data)             — live, read-only
```

---

## ⚠️⚠️ Recovery expires

An overwrite is recoverable **for 30 days, and only if somebody notices.** Nobody
audits your rows. Pull before you edit. Push what you changed. If something of
yours disappears, say so within the month or it is gone.

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

---

## Roles

| Role | Who | Does |
|---|---|---|
| **Publisher** | one machine at a time (currently named in live ops docs) | rebuilds/publishes KG; only role that may `--delete` |
| **Contributor** | every other machine / teammate | owns `changes/sst-NNNN/`; pushes docs; **reads** KG |

```bash
./publisher.sh status | claim "why" | release
```

> ⚠️ Two publishers destroy `community_labels.json` silently. Returning machines:
> set `MACHINE_ROLE="contributor"` and `./identity.sh --write` **before** pull/push.

**Contributor asks for rebuild (no locks):**

```bash
kg_refresh.sh request "why"
./data-push.sh --go
```

One file per request under `refresh_queue/`. Cursor: ask the agent to file the
request; do **not** ask it to publish the KG on a contributor machine.

---

## Access

| Profile | Account | Permission set | Here |
|---|---|---|---|
| `kb-s3` | 055622654641 | `KnowledgeBaseS3` | ⚠️ **only** role that can WRITE this bucket |
| `dev-nonprod` | 055622654641 | `DeveloperNonprod` | reads; PutObject denied by design |
| `shared-ecr` | 901059153226 | `SharedEcrPull` | ECR fallback — not needed for sync |

Read-only teammate: `READ_PROFILE="dev-nonprod"` in `config.env`.

> Never diagnose access from a CLI error without `aws sso logout && aws sso login` first.

---

## Machine identity (Cursor)

```bash
./identity.sh --write    # generates machine-local IDENTITY.md
```

`IDENTITY.md` records role + live checks (account, bucket, mount). Repository
**`AGENTS.md`** (and/or always-on `.cursor/rules`) **points at it** so every Cursor
session reads its role before shared writes. Gitignored, never synced, never zipped.

Re-run after any `config.env` change.

---

## Daily use

```bash
./data-pull.sh                # dry run DEFAULT
./data-pull.sh --go

# ... work locally in Cursor on real disk under data/changes/...

./data-push.sh
./data-push.sh --go
```

`--delete` is **publisher-only**. `data-pull.sh` runs `ledger_check.sh` first
(advisory).

**KG query (Cursor):** project **`kg` skill** / Agent, or
`.\scripts\kg_query.ps1` / `kg_query.sh`.

Contributors never run KG publish / rebuild.

---

## Behavioural rules people break

1. ⚠️⚠️ **Recovery expires** — see above.
2. **Shared ledgers are append-only** — `STATUS.md`, `TICKETS.md`, `FOLLOWUPS.md`,
   `TEST_MAP.md`, `CUSTOMER_GUIDANCE.md`. Add rows; never rewrite someone else's.
3. **Per-task folders need no coordination** — one folder per ticket, one owner.
4. **The shared store wins on divergence** — "I have it locally" is not an argument
   once theirs is published.
5. **Mirror-delete belongs to one role** — publisher only.
6. **Widening scope is a security event** — scan first, **canary the scanner**, then
   reconcile inventory (clean transfer ≠ completeness).

---

## Setting up a machine

1. AWS SSO → account **055622654641**.
2. `sudo apt-get install -y ./mount-s3.deb` (x86_64; WSL/Ubuntu).
3. Edit `config.env`: `LOCAL_DATA`, `MACHINE_NAME`, `MACHINE_ROLE`, optional
   `READ_PROFILE`. Leave `BUCKET` / `PREFIX` / `REGION` alone.
4. `./identity.sh --write`
5. `./validate.sh` → **MACHINE READY ✅**

Scripts live in the distributable zip (`ils-s3-sync-YYYYMMDD.zip`). After unzip: edit
config, then identity + validate.

---

## Troubleshooting (short)

| Symptom | Fix |
|---|---|
| Token expired / ForbiddenException | Re-login SSO first; then re-read the error |
| AccessDenied on PutObject | On `dev-nonprod` by design — need `kb-s3` to write |
| Mount empty / transport endpoint | Wrong `PREFIX`, or `./unmount-data.sh` then remount |
| Write fails on mount | By design — write via `data-push.sh` |
| Teammate work vanished after your push | You used `--delete` from stale view — restore within 30 days |
| `kg_labels.py check` lost/unnamed | Graph + labels unpaired — re-pull both; do not publish over it |

---

## Known gaps

- Two-machine live round-trip may still be unproven until the next joiner completes
  the onboarder acceptance test — record the result.
- Never trust a filter you have not seen reject something.
- A clean dry-run is not a completeness check.
