# Welcome — start here (Cursor)

**Written for you**, the person joining. Your colleague has a companion checklist
(`Onboarder checklist`) — you do not need to read that one.

**You start in Cursor.** These Confluence pages + the Cursor IDE are your path.
Open `document-parser-lambda` in Cursor from day one — that is how always-on
guidance (`AGENTS.md`, `.cursor/rules`, skills) loads. Do not wait for another
tooling setup.

Work through this in order. Sections 1–4 are setup; 5 onwards is how the team works.
Budget half a day, most of which is waiting on access.

**What your lead also gives you (not optional):** the `ils-s3-sync-YYYYMMDD.zip` package
(scripts + `mount-s3.deb`). Confluence explains *what* to do; the zip is *how* you
run pull/push. Both are part of onboarding — Confluence does not replace the zip.

---

## 1. What you are joining

We build and maintain **`document-parser-lambda`** — an AWS Lambda that extracts
structured data from legal side letters and comment memos (DOCX, DOC, PDF) using
LLM-assisted parsing. It is one service in a larger system:

| Repo | What it is | Do you edit it? |
|---|---|---|
| `document-parser-lambda` | our service — extraction | ✅ **yes, this is ours** |
| `monolith` | Django backend; stores and re-serves what we extract | ❌ read-only context |
| `frontend` | React SPA the reviewers actually look at | ❌ read-only context |
| `infrastructure`, `helm-values` | Terraform + deployment config | ❌ read-only context |

You read the others freely to understand contracts. You do **not** edit, commit or
push to them. If something needs fixing there, we write it up and hand it to the
responsible team.

**The single most useful thing to internalise early:** what QA, product and clients
see is the JSON returned by the monolith's `get-sl-upload-status` endpoint.
Everything inside our repo — prompts, thresholds, provider routing — is
implementation detail. That JSON is the contract.

---

## 2. Day 0 — start in Cursor (do this first)

1. Install **Cursor**, sign in.
2. Clone / get `document-parser-lambda`, then **File → Open Folder** on that repo
   root (not a parent monorepo unless your lead says otherwise).
3. Confirm **`AGENTS.md`** is at the root and Customize → MCP shows your team's
   tools green. Always-on rules live under `.cursor/rules/`; skills under
   `.cursor/skills/` (`kg`, `sanitise-diff`, …). Detail stays in `data/changes/`
   after you pull — do not paste it into rules.
4. Habit from day one: **Plan → agree → implement** (Cursor **Plan** mode for
   non-trivial work). Do **not** let the agent push, open/merge PRs, or deploy
   unless you explicitly ask in that session.
5. Ask your lead for **`ils-s3-sync-YYYYMMDD.zip`** if you do not have it yet — you need
   it for §4. While AWS access is pending, you can already read `AGENTS.md` and
   skim the playbook siblings (Diagnose → Human gate).

---

## 3. Access — this is the long pole, chase it first

You need AWS SSO on account **055622654641** with two permission sets:

| Permission set | Gets you |
|---|---|
| `DeveloperNonprod` | CloudWatch logs, Lambda config, SQS, ECR, and **read** on the shared bucket |
| `KnowledgeBaseS3` | ⚠️ the **only** role that can write the shared bucket — i.e. contribute your own work |

Ask your colleague where the request stands before doing anything else. You can make
progress with `DeveloperNonprod` alone (read-only), so if only one has landed, start
anyway.

Once you have it:

```bash
aws configure sso                      # start URL https://ils-provision.awsapps.com/start/
                                       # sso-region us-east-1
aws sso login --profile <your-profile>
aws sts get-caller-identity --profile <your-profile>     # must show 055622654641
```

> ⚠️⚠️ **Learn this now, it will save you hours.** When an AWS command fails with
> `Token has expired` or `ForbiddenException`, that describes your **cached login**,
> not your permissions. Always `aws sso logout && aws sso login` *first*, then
> re-read the error.

**Shell environment:** sync scripts expect Linux or **WSL2** (`apt-get`,
`mount-s3.deb`). If Cursor runs on Windows, do S3 sync steps inside WSL against the
same `data/` tree (`/mnt/d/...`).

---

## 4. Set up the shared record

Ticket documentation, diagnostics, client source documents and a knowledge graph live
in `data/` inside the repo. `data/` is **gitignored** — it never goes to GitHub. It is
shared through S3 instead.

Your local `data/` is a **working copy**. The bucket is the source of truth.

Unzip **`ils-s3-sync-YYYYMMDD.zip`**, then:

```bash
# in the s3-sync folder from the zip
#   edit config.env:
#     LOCAL_DATA     absolute path to YOUR document-parser-lambda/data
#     MACHINE_NAME   something distinctive — it shows up in shared state
#     MACHINE_ROLE   contributor          <-- yours is always this
#     READ_PROFILE   dev-nonprod          <-- only if you are read-only for now

sudo apt-get install -y ./mount-s3.deb    # x86_64 (WSL/Ubuntu)
./identity.sh --write                     # writes IDENTITY.md; confirm CONTRIBUTOR
./validate.sh                             # must print MACHINE READY ✅
./data-pull.sh                            # dry run — this is the default
./data-pull.sh --go                       # ~888 MiB, takes a while
```

`MACHINE READY ✅ (read-only — N write operation(s) denied as expected)` is a **pass**
if you are read-only. A denied write there is correct, not broken.

After identity is written: **`AGENTS.md`** (already in the repo) points Cursor at
this machine's `IDENTITY.md` so every session reads **contributor** before shared
writes.

Full diagram, troubleshooting, and publisher rules: sibling page
**Shared record (S3 sync)**.

---

## 5. ⚠️⚠️ The rules that actually matter

**1. Recovery expires at 30 days, and you own your own work.**
The bucket is versioned, so if someone overwrites your file it can be recovered — for
30 days, and only if somebody notices. Nobody audits your rows. **Pull before you
edit, push what you changed**, and if something of yours disappears, say so within
the month or it is gone.

**2. Write via sync, read via mount.**
`data-push.sh` / `data-pull.sh` work on real local disk. The mount at `~/s3-ils-data`
is read-only *on purpose* — object storage has no locking and no atomic rename.

**3. Never use `--delete`.**
It mirrors exactly. From a stale local view it erases a colleague's work. Publisher-only.

**4. Never push `knowledge-graph/`, never rebuild/publish the KG.**
The graph tree includes **hand-authored** community names that nothing regenerates.
Two machines publishing destroys them silently. You *read* it in Cursor with the
project **`kg` skill** (or ask the agent; under the hood: `.\scripts\kg_query.ps1`
/ `kg_query.sh`).

If you think a refresh is due, **file a request** and push that — do not rebuild:

```bash
bash ../knowledge-graph/kg_refresh.sh request "why you think so"
./data-push.sh --go
```

**5. Shared ledgers are append-only.**
`STATUS.md`, `TICKETS.md`, `FOLLOWUPS.md`, `TEST_MAP.md`, `CUSTOMER_GUIDANCE.md`.
Add your rows; never rewrite someone else's. Last-writer-wins drops their line silently
— `ledger_check.sh` only *warns* on the next pull.

Everything else is naturally safe: **your ticket folders are yours.**
`changes/sst-NNNN/` is one person's workstream.

---

## 6. Confidentiality — non-negotiable

Anything pushed to **GitHub** (`src/`, `tests/`, commit messages, PR titles and
descriptions) must contain:

- ❌ **no client names** — funds, firms, investors, matters
- ❌ **no ticket IDs** in code or config **bodies** (filenames like `test_sst_1234_*.py` OK)
- ❌ **no AI/agent attribution** anywhere — the author of record is you

✅ Fine inside `data/**` (gitignored). Ticket IDs are fine in commit/PR text.

Before you stage a push of code: run the repo **`sanitise-diff`** skill in Cursor
every time.

---

## 7. How a piece of work actually goes (Cursor)

1. **Triage before code.** Confirm the symptom in *our* `get-sl-upload-status` JSON.
   If the data is correct there, push back — do not start work in this repo.
2. **History first.** Read `data/changes/<TICKET>/` and query the KG (`kg` skill /
   Agent) before inventing a fix shape.
3. **Plan, agree, then code** in Cursor. No production code until the plan is agreed.
4. **Test first.** Failing scoped test → minimal code → green.
5. **Verify before claiming done.** Look at the actual output — not just counts.
6. **Document** in `data/changes/<TICKET>/`, then `./data-push.sh --go`.
7. **Human gate:** you (or your lead) push / open the PR / deploy — do not let the
   agent do irreversible outward actions unless you explicitly ask in that session.
8. **Session continuity:** at the end of a day, rewrite the rolling entry-point note
   (what is in flight + expensive caveats) so the *next* Cursor chat is not blind.

Branches: `fix/sst-1234-short-description`, based on `development`, squash-merged.

---

## 8. A habit worth borrowing

**Before you believe a check, prove it can fail.** Run it against a case whose answer
you already know. Filters, locks and scanners whose correct answer is *silence* look
identical when broken. Canary the instrument first.

Full playbook: sibling Confluence pages under this parent (Diagnose → Verify →
Context → Human gate).

---

## 9. Where to read next

| You want | Read |
|---|---|
| Cursor orientation (always-on) | `AGENTS.md` + `.cursor/rules/` in the repo (loads when you open the folder) |
| Shared-record mechanics | Confluence: **Shared record (S3 sync)** + your `ils-s3-sync-YYYYMMDD.zip` |
| Methodology playbook | Confluence siblings: Diagnose, Verify, Context, Human gate |
| Why code looks the way it does | `data/changes/<TICKET>/<TICKET>.md` (after first pull) |
| Current in-flight state | `data/changes/STATUS.md` |
| What we have told clients | `data/changes/CUSTOMER_GUIDANCE.md` |

---

## 10. Ask about these — known-unsettled

- Whether commits reach `stage/<release>` per ticket or in batches
- What counts as "one provision" — open with Legal
- Anything in `data/changes/_PENDING_<date>.md`

Nobody expects you to resolve these. Knowing they are open stops you assuming there
is a rule you failed to find.
