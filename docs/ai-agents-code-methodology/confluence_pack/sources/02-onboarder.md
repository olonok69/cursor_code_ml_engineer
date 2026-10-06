# Onboarder checklist (Cursor) — your side, not theirs

**Current as of 2026-10-05** (re-walked end to end: a read-only joiner simulated from the pack). Brings a new team member online as a **contributor**.
They start in **Cursor** (Confluence joiner page + open the lambda repo). Hand them
**For new joiners (Cursor)** and **`ils-s3-sync-YYYYMMDD.zip`** together.

Also read **Shared record (S3 sync)** if you have not — this checklist assumes it.

---

## ⛔ Step 0 — the gate, and it is not yours

**Nothing below works until they hold the AWS access.** Raise it for every new person as
early as possible — the September request took about two weeks to land.

- Template: package file `_teammate_access_request.txt` (the September text — change name and date)

What was asked for, on account **055622654641** (nonprod):

| Permission set | Why |
|---|---|
| `DeveloperNonprod` | reads the bucket; logs / lambda / sqs / eks / ecr for normal work |
| `KnowledgeBaseS3` | ⚠️ **the only role that can write `s3://ils-nonprod-knowledge-base`** |

Do **not** hand DevOps `poc-iam-policy.json` — access is SSO permission sets now.

**Chase this before doing anything else.**

### Step 0b — hand over on day one (none of these reach them any other way)

- [ ] GitHub **`ils-tech`** org access + their SSH key — `pip install -r requirements.txt` pulls
      `ils-message-broker` over `git+ssh` and fails without it
- [ ] **`.sanitise-names`** (client-name blocklist) — never committed, synced or packed by design;
      the `sanitise-diff` skill aborts without it. Hand to hand
- [ ] An OpenAI key for their own `.env.test` (the default `pytest -q` needs none)
- [ ] A **freshly built** pack: run `./package.sh` the day you send it, send only the file it names,
      quote its `PACK_BUILD.txt` stamp, delete any older pack it warns about. Publish your day
      (`day end`) first so the bucket matches the pack

---

## Step 1 — Cursor from day one (say this out loud)

1. They install **Cursor**, clone the repo, unzip the pack into `data/changes/`, and **copy
   `AGENTS.md` and `.cursor/` from `_pack_extras/` into the repo root** — both are gitignored and
   are not in the clone. Then they open **`document-parser-lambda`** as the workspace.
2. You give them Confluence **For new joiners** **and** `ils-s3-sync-YYYYMMDD.zip` in the
   same breath — zip is required for sync scripts, not an optional extra.
3. Machine role: `IDENTITY.md` via `AGENTS.md` — contributor never publishes the KG.
4. Human gate: agent does not push / open-merge PRs / deploy unless they explicitly
   ask in that session.
5. Daily loop = Cursor **`day` skill** (`day start` / `day end`) — not raw
   `data-pull` / `data-push` from memory. A page cannot enforce the habit.
6. KG query = Cursor **`kg` skill** / `bash data/knowledge-graph/kg_query.sh` (full queries need
   a Python 3.10+ graphify venv — joiner page § 4). Refresh = Cursor
   **`kg-refresh`** (files a request) / `kg_refresh.sh request` only (publisher
   owns rebuild).

> ⚠️⚠️ **`KnowledgeBaseS3` does not distinguish `knowledge-graph/` from `changes/`.**
> A contributor *can* overwrite the KG. Single-writer is **baton + convention**, not
> IAM. Say this out loud.
>
> The baton gate in `data-push.sh` is **scoped to `knowledge-graph/` only** (as of
> 2026-09-10). Contributors push ticket folders normally; the gate skips publishing
> the graph and still allows `refresh_queue/`. On `--go` expect *"knowledge-graph/: 'groundtruth'
> holds the publisher baton … NOT an error"* — that is success, not a failure.

---

## Step 2 — decide write posture before they configure

| Posture | `config.env` | They can |
|---|---|---|
| **Read-only start** (recommended day 1) | uncomment `READ_PROFILE="dev-nonprod"` | pull, ledger check, read baton — never write. `validate.sh` → **READY (read-only)** |
| **Full contributor** | `PROFILE="kb-s3"` (template default) | above + push their own ticket folders + refresh requests |

---

## Step 3 — their setup, per machine

1. **AWS SSO** — the exact `~/.aws/config` block on the joiner page § 3 (profiles `dev-nonprod`
   and `kb-s3`, sso-session `ils`). `aws sts get-caller-identity --profile dev-nonprod` must show
   **055622654641**.
2. **Tooling** — AWS CLI v2 + python3. mountpoint-s3 is optional (`mount-s3.deb`, x86_64
   Ubuntu/WSL only; skip on a Mac).
3. **Unzip the pack into `<repo>/data/changes/`** (`mkdir -p data/changes` first — a fresh clone has
   no `data/`), then `cp templates/config.corporate.env config.env`. Bucket / profile / region /
   prefix are pre-filled; they edit:

   | Field | Value |
   |---|---|
   | `LOCAL_DATA` | absolute path to **their** `document-parser-lambda/data` |
   | `MACHINE_NAME` | distinctive — appears in baton / refresh queue |
   | `MACHINE_ROLE` | ⚠️ **`contributor`** (template default) |
   | `READ_PROFILE` | per Step 2 |

4. **`./identity.sh --write`** → confirm **CONTRIBUTOR**. This is what a **Cursor**
   session must read (via `AGENTS.md`) so it does not publish the KG.
5. **`./validate.sh`** → `MACHINE READY ✅` (read-only denial is OK when expected).
6. **First pull:** `./data-pull.sh` then `./data-pull.sh --go` (~1.2 GiB). Their first sync is a
   **pull, never a push** — before it, a push dry run lists the pack's own files as if they were
   their work. After that they use **`day start`** / **`day end`** in Cursor.

---

## Step 4 — teach the rules (10 minutes)

1. ⚠️⚠️ Recovery expires at **30 days** — own your own work; push what you changed;
   pull before edit **unless** you have unpushed work (dry-run first).
2. Write via sync, read via mount (`~/s3-ils-data` read-only on purpose).
3. **`day start` → work locally → `day end`.** One owner per ticket folder.
   Documentation of pull/push does not enforce this; the skill does.
4. Never `--delete` (publisher-only).
5. Never **publish** `knowledge-graph/` / never rebuild KG; **`kg-refresh`** files
   a request (by hand from `s3-sync/`: `bash ../../knowledge-graph/kg_refresh.sh request "why"`).
   The *"holds the publisher baton … NOT an error"* line on push is expected; `refresh_queue/`
   still goes up. Names: **115** authored (2026-10-02); a rebuild keeps a third to a half —
   refresh is a naming budget, not free.
7. **Record conventions:** one main doc per ticket, `sst-nnnn/sst-nnnn.md`, **lowercase** (the KG
   indexes it); QA evidence in `sst-nnnn/qa_review_N/`; a follow-up is a `FOLLOWUPS.md` entry —
   agents never open Jira tickets.
6. ⚠️⚠️ **Guard BOTH directions.** A pull clobbers them; a push clobbers a
   colleague and nothing on their machine looks wrong. **Exit 4 / `REFUSED`** is
   not noise — merge the hub file; do not teach `--allow-clobber`.

**Append-only ledgers** — add rows only; `ledger_check.sh` warns on pull; the
push guard **refuses** when a hub file moved in the bucket.

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
      **115/115** matched on a healthy pull, as of 2026-10-02)
- [ ] In **Cursor**, KG query (`kg` skill) for a known ticket returns a community
      **name**, not a bare integer (proves hand-authored labels survived)
- [ ] Their first `./data-push.sh --go` shows the *"holds the publisher baton … NOT an error"*
      line (expected) and still pushes ticket work
- [ ] They can run **`day start`** in Cursor after the first pull (skill present
      under `.cursor/skills/day/`)

Contributor loop:

- [ ] They create `changes/_sandbox_<their-machine>/notes.md` → `./data-push.sh --go`
      (not `sst-*`: that pattern is indexed by the KG)
- [ ] You pull on publisher and see it
- [ ] They `kg_refresh.sh request "smoke test"` (or Cursor **`kg-refresh`**) → push;
      you see queue with **their** machine name (`refresh_queue/` must not be
      baton-blocked)
- [ ] `kg_refresh.sh queue --clear` → push → both sides empty.
  ⚠️ As of 2026-10-05 consumed requests can survive in the bucket and come back on every pull
  (4 did; removed by hand). If they reappear, the publisher removes those bucket keys.
- [ ] The **publisher** removes the sandbox folder at the end (`--delete` is publisher-only)

---

## Step 6 — methodology adoption (Cursor)

- [ ] They know where the Confluence playbook lives (parent + Diagnose / Verify /
      Context / Human gate)
- [ ] They can open Plan mode and state the output contract (`get-sl-upload-status`)
- [ ] They know: canary instruments; assert on member lists not totals; human gate
- [ ] `sanitise-diff` skill (or equivalent) before code leaves the workbench
- [ ] **`day` skill** — they open with `day start` and close with `day end`
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
- Exit 4 / `REFUSED` on push is a **merge**, not a winner. `--allow-clobber` is
  how the 2026-09-18 ledger loss happened.
- A per-machine activity file has **one writer**. If the dashboard says someone
  never closed their day, check whether *your* tooling ate the evidence.

---

## Confirm they are productive

- [ ] `./validate.sh` → READY on each of their machines
- [ ] They can pull and see tickets + KG
- [ ] Round trip proven (Step 5)
- [ ] KG query works in **Cursor**
- [ ] They know 30-day rule, append-only ledgers, `--delete` is not theirs,
      the publisher-baton line on push is normal, **exit 4** means merge
- [ ] They use **Cursor** from day one (repo open; `AGENTS.md` loads) and
      **`day start` / `day end`**
- [ ] They received **`ils-s3-sync-YYYYMMDD.zip`** with the Confluence joiner page
