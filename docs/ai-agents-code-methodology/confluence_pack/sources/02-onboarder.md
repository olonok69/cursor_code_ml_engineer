# Onboarder checklist (Cursor) — your side, not theirs

**Current as of 2026-09-10.** Brings a new team member online as a **contributor**.
They start in **Cursor** (Confluence joiner page + open the lambda repo). Hand them
**For new joiners (Cursor)** and **`ils-s3-sync-YYYYMMDD.zip`** together.

Also read **Shared record (S3 sync)** if you have not — this checklist assumes it.

---

## ⛔ Step 0 — the gate, and it is not yours

**Nothing below works until they hold the AWS access.**

- Request text as sent: package file `_teammate_access_request.txt`
- Rationale: `_entitlement_audit_20260904.md` (in the s3-sync zip)

What was asked for, on account **055622654641** (nonprod):

| Permission set | Why |
|---|---|
| `DeveloperNonprod` | reads the bucket; logs / lambda / sqs / eks / ecr for normal work |
| `KnowledgeBaseS3` | ⚠️ **the only role that can write `s3://ils-nonprod-knowledge-base`** |

Do **not** hand DevOps `poc-iam-policy.json` — access is SSO permission sets now.

**Chase this before doing anything else.**

---

## Step 1 — Cursor from day one (say this out loud)

1. They install **Cursor** and open **`document-parser-lambda`** as the workspace
   (so `AGENTS.md` + `.cursor/rules` + skills load).
2. You give them Confluence **For new joiners** **and** `ils-s3-sync-YYYYMMDD.zip` in the
   same breath — zip is required for sync scripts, not an optional extra.
3. Machine role: `IDENTITY.md` via `AGENTS.md` — contributor never publishes the KG.
4. Human gate: agent does not push / open-merge PRs / deploy unless they explicitly
   ask in that session.
5. KG query = Cursor **`kg` skill** / `scripts/kg_query.ps1`. Refresh = file a
   `kg_refresh.sh request` only (publisher owns rebuild).

> ⚠️⚠️ **`KnowledgeBaseS3` does not distinguish `knowledge-graph/` from `changes/`.**
> A contributor *can* overwrite the KG. Single-writer is **baton + convention**, not
> IAM. Say this out loud.
>
> The baton gate in `data-push.sh` is **scoped to `knowledge-graph/` only** (as of
> 2026-09-10). Contributors push ticket folders normally; the gate skips publishing
> the graph and still allows `refresh_queue/`. Expect them to see a **`SKIPPED
> knowledge-graph/`** line — that is success, not a failure.

---

## Step 2 — decide write posture before they configure

| Posture | `config.env` | They can |
|---|---|---|
| **Read-only start** (recommended day 1) | `READ_PROFILE="dev-nonprod"` | pull, ledger check, read baton — never write |
| **Full contributor** | `PROFILE="kb-s3"` | above + push their own ticket folders + refresh requests |

---

## Step 3 — their setup, per machine

1. **AWS SSO** — start URL `https://ils-provision.awsapps.com/start/`, sso-region
   `us-east-1`. `aws sts get-caller-identity` must show **055622654641**.
2. **Tooling** — AWS CLI v2 + mountpoint-s3 (from the package `mount-s3.deb` on
   x86_64 Ubuntu/WSL).
3. **Copy `s3-sync/`**, edit `config.env`:

   | Field | Value |
   |---|---|
   | `LOCAL_DATA` | absolute path to **their** `document-parser-lambda/data` |
   | `MACHINE_NAME` | distinctive — appears in baton / refresh queue |
   | `MACHINE_ROLE` | ⚠️ **`contributor`** |
   | `PROFILE` / `READ_PROFILE` | per Step 2 |

4. **`./identity.sh --write`** → confirm **CONTRIBUTOR**. This is what a **Cursor**
   session must read (via `AGENTS.md`) so it does not publish the KG.
5. **`./validate.sh`** → `MACHINE READY ✅` (read-only denial is OK when expected).
6. **First pull:** `./data-pull.sh` then `./data-pull.sh --go` (~888 MiB).

---

## Step 4 — teach the five rules (10 minutes)

1. ⚠️⚠️ Recovery expires at **30 days** — own your own work; push what you changed;
   pull before edit **unless** you have unpushed work (dry-run first).
2. Write via sync, read via mount (`~/s3-ils-data` read-only on purpose).
3. Pull at start → work locally → push at end. One owner per ticket folder.
4. Never `--delete` (publisher-only).
5. Never **publish** `knowledge-graph/` / never rebuild KG; file
   `kg_refresh.sh request` instead. **`SKIPPED knowledge-graph/`** on push is expected;
   `refresh_queue/` still goes up. Names: **102** authored; ~**37–48%** survive a
   rebuild — refresh is a naming budget, not free.

**Append-only ledgers** — add rows only; `ledger_check.sh` warns on pull.

---

## Step 5 — prove the round trip (acceptance test)

> ▶▶ **Two-machine § of `GO_LIVE_CHECKLIST` may never have been run with two real
> people.** A simulated contributor (second `MACHINE_NAME` + `dev-nonprod` read) can
> exercise baton + queue paths, but writes may still use the publisher's `kb-s3`
> credentials. A second person joining **is** the full acceptance test — treat it as
> one and record the result.

On their machine:

- [ ] `./identity.sh` → **CONTRIBUTOR**
- [ ] `./data-pull.sh --go` completes
- [ ] `python3 <their data>/knowledge-graph/kg_labels.py check` → **0 unnamed, 0 lost**,
      no fingerprint mismatch (graph + labels arrived as a **matched pair**; expect
      **102/102** matched on a healthy pull)
- [ ] In **Cursor**, KG query for a known ticket returns a community **name**, not a
      bare integer (proves hand-authored labels survived)
- [ ] Their first `./data-push.sh --go` shows **`SKIPPED knowledge-graph/`** (expected)
      and still pushes ticket work

Contributor loop:

- [ ] They create `changes/sst-SANDBOX/notes.md` → `./data-push.sh --go`
- [ ] You pull on publisher and see it
- [ ] They `kg_refresh.sh request "smoke test"` → push; you see queue with **their**
      machine name (`refresh_queue/` must not be baton-blocked)
- [ ] `kg_refresh.sh queue --clear` → push → both sides empty
  (`--clear` must **delete the consumed keys in the bucket**, not only archive locally —
  otherwise the next pull resurrects the request everywhere)
- [ ] They delete sandbox and push — `--delete` stays with publisher

---

## Step 6 — methodology adoption (Cursor)

- [ ] They know where the Confluence playbook lives (parent + Diagnose / Verify /
      Context / Human gate)
- [ ] They can open Plan mode and state the output contract (`get-sl-upload-status`)
- [ ] They know: canary instruments; assert on member lists not totals; human gate
- [ ] `sanitise-diff` skill (or equivalent) before code leaves the workbench
- [ ] Session continuity: rolling entry-point rewritten at end of day

---

## Known sharp edges — tell them before they hit these

- Never diagnose access from a CLI error without re-login first.
- A check that cannot distinguish "no" from "couldn't ask" is not evidence
  (baton once reported "nobody holds it" on an expired token).
- A clean dry-run only says "what I was asked to send, I sent".
- `aws s3 --include` is case-sensitive.
- Sync walks the whole tree before filters — use `SYNC_ROOTS`, not raw `data/`.
- Gate a path → enumerate what else lives under it (`refresh_queue/` inside
  `knowledge-graph/` was the classic trap).

---

## Confirm they are productive

- [ ] `./validate.sh` → READY on each of their machines
- [ ] They can pull and see tickets + KG
- [ ] Round trip proven (Step 5)
- [ ] KG query works in **Cursor**
- [ ] They know 30-day rule, append-only ledgers, `--delete` is not theirs,
      **`SKIPPED knowledge-graph/`** is normal
- [ ] They use **Cursor** from day one (repo open; `AGENTS.md` loads)
- [ ] They received **`ils-s3-sync-YYYYMMDD.zip`** with the Confluence joiner page
