# Welcome — start here (Cursor)

**Written for you**, the person joining. Your colleague has a companion checklist
(`Onboarder checklist`) — you do not need to read that one. Last re-walked end to end
on 2026-10-05.

**You start in Cursor.** These Confluence pages + the Cursor IDE are your path.
Claude Code is second choice only if your lead says so.

Work through this in order. Sections 1–4 are setup; 5 onwards is how the team works.
Budget half a day, most of which is waiting on access.

**What your lead also gives you (not optional):** the `ils-s3-sync-YYYYMMDD.zip` pack.
It carries the sync scripts **and** the Cursor files (`AGENTS.md`, `.cursor/`), which are
gitignored and therefore **not in your clone**. Check its `PACK_BUILD.txt` stamp matches the
build your lead announced. Confluence explains *what* to do; the pack is *how*.

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

## 2. Day 0 — what to ask for, and the local setup

Ask your lead on day one for everything in this table. None of it reaches you any other way.

| What | Why |
|---|---|
| AWS access (§3) | the long pole — chase it first |
| GitHub access to the **`ils-tech`** org + an SSH key on your account | `pip install -r requirements.txt` installs the private `ils-message-broker` over `git+ssh` and fails without it |
| `.sanitise-names` (client-name blocklist) | the `sanitise-diff` skill aborts without it; never committed, synced or packed by design |
| An OpenAI key for your own `.env.test` | local extraction and integration tests; the default `pytest -q` needs **no** keys |
| The `ils-s3-sync-YYYYMMDD.zip` pack | sync scripts + Cursor files |

You also need: **AWS CLI v2**, **python3**, `tesseract` and `LibreOffice` on your PATH, and a
GitHub PAT (`GH_PAT`) only if you build the Docker image.

```bash
git clone git@github.com:ils-tech/document-parser-lambda.git && cd document-parser-lambda
git switch development
python3.12 -m venv .venv && source .venv/bin/activate      # the Lambda image runs 3.12
pip install --upgrade pip && pip install -r requirements.txt
pip install pre-commit && pre-commit install
pytest -q                                                  # no keys needed
```

⚠️ `test_async_client_recreated_across_asyncio_run_calls` is a known pre-existing failure in a
full run (it passes alone). It is not you.

Habit from day one: **Plan → agree → implement** (Cursor **Plan** mode for non-trivial work).
Do **not** let the agent push, open/merge PRs, or deploy unless you explicitly ask in that
session.

---

## 3. Access — this is the long pole, chase it first

You need AWS SSO on account **055622654641** with two permission sets:

| Permission set | Gets you |
|---|---|
| `DeveloperNonprod` | CloudWatch logs, Lambda config, SQS, ECR, and **read** on the shared bucket |
| `KnowledgeBaseS3` | ⚠️ the **only** role that can write the shared bucket — i.e. contribute your own work |

You can make progress with `DeveloperNonprod` alone (read-only), so if only one has
landed, start anyway.

Put exactly this in `~/.aws/config` — every script and doc on this team uses these profile names:

```ini
[sso-session ils]
sso_start_url = https://ils-provision.awsapps.com/start/
sso_region = us-east-1
sso_registration_scopes = sso:account:access

[profile dev-nonprod]
sso_session = ils
sso_account_id = 055622654641
sso_role_name = DeveloperNonprod
region = eu-central-1

[profile kb-s3]
sso_session = ils
sso_account_id = 055622654641
sso_role_name = KnowledgeBaseS3
region = eu-central-1
```

```bash
aws sso login --sso-session ils
aws sts get-caller-identity --profile dev-nonprod     # must show 055622654641
```

The Confluence pages **AWS SSO Access** and **ECR Login for Local Docker** are the source of
truth for access; if they disagree with this page, they win.

> ⚠️⚠️ **Learn this now, it will save you hours.** When an AWS command fails with
> `Token has expired` or `ForbiddenException`, that describes your **cached login**,
> not your permissions. Always `aws sso logout && aws sso login` *first*, then
> re-read the error.

---

## 4. Set up the shared record

Ticket documentation, diagnostics, client source documents and a knowledge graph live
in `data/` inside the repo. `data/` is **gitignored** — it never goes to GitHub, and a fresh
clone does not have it. It is shared through S3 instead.

Your local `data/` is a **working copy**. The bucket is the source of truth.

Unzip the pack **into the repo**, copy the Cursor files, then configure:

```bash
cd document-parser-lambda
mkdir -p data/changes
unzip ~/Downloads/ils-s3-sync-YYYYMMDD.zip -d data/changes     # -> data/changes/s3-sync/
cd data/changes/s3-sync

cp _pack_extras/AGENTS.md ../../../AGENTS.md
mkdir -p ../../../.cursor && cp -R _pack_extras/dot-cursor/. ../../../.cursor/
chmod +x ../../../.cursor/hooks/*.sh

cp templates/config.corporate.env config.env
#   bucket / profile / region / prefix are pre-filled. Edit only:
#     LOCAL_DATA     absolute path to YOUR document-parser-lambda/data
#     MACHINE_NAME   something distinctive — it shows up in shared state
#     READ_PROFILE   uncomment READ_PROFILE="dev-nonprod" while you only have DeveloperNonprod
#   MACHINE_ROLE is already "contributor" — yours always is.

./identity.sh --write        # writes IDENTITY.md; confirm it says CONTRIBUTOR
./validate.sh                # must print MACHINE READY ✅
./data-pull.sh               # dry run — this is the default
./data-pull.sh --go          # ~1.2 GiB, takes a while
```

`MACHINE READY ✅ (read-only — N write operation(s) denied as expected)` is a **pass**
if you are read-only. A denied write there is correct, not broken.

⚠️ **Your first sync is a pull, never a push.** Before that first pull, a push dry run lists the
pack's own files as if they were your work — pushing them could put an older copy over the team's.

**macOS / Linux / WSL all work.** On a Mac, skip `mount-s3.deb` (Linux only; the read-only mount is
optional and `validate.sh` treats its absence as info, not failure). On Windows, run the sync inside
WSL2 against the same `data/` tree.

Then open the repo in Cursor (**File → Open Folder** on the repo root): `AGENTS.md` loads, MCP
should show green, rules are under `.cursor/rules/`, skills under `.cursor/skills/` (`day`, `kg`,
`kg-refresh`, `sanitise-diff`, `methodology-plan`).

From then on, **do not run pull/push from memory.** In Cursor ask for the **`day`
skill**: `day start` at the beginning (pulls the team's latest, then a short
briefing) and `day end` before you stop (writes the day up and publishes). It
reads `IDENTITY.md` first so it will not publish the KG from your machine.

### Knowledge-graph queries

`kg_query.sh find <text>` works with plain python3. Full queries need **graphify**, which needs
**Python 3.10+** (stock macOS python3 is 3.9). Use a venv and pin the team's version:

```bash
python3.12 -m venv ~/.venvs/graphify
~/.venvs/graphify/bin/pip install graphifyy==0.9.8
mkdir -p data/knowledge-graph/graphify-out                         # from the repo root
echo ~/.venvs/graphify/bin/python3 > data/knowledge-graph/graphify-out/.graphify_python
bash data/knowledge-graph/kg_query.sh SST-5623                     # prints a node with a community name
```

Full diagram, troubleshooting, and publisher rules: sibling page
**Shared record (S3 sync)**.

---

## 5. ⚠️⚠️ The rules that actually matter

**1. Recovery expires at 30 days, and you own your own work.**
The bucket is versioned, so if someone overwrites your file it can be recovered — for
30 days, and only if somebody notices. Nobody audits your rows. **Push what you
changed.** `data-pull.sh --go` copies every local file it is about to replace into
`data/_prepull/<timestamp>/` and lists them — read that list. If a shared file
(`STATUS.md`, `FOLLOWUPS.md`, `_RESUME_*.md`) is in it, a colleague's copy is landing on yours:
that needs a merge, not a winner. If something of yours disappears, say so within the
month or it is gone.

**2. Write via sync, read via mount.**
`data-push.sh` / `data-pull.sh` work on real local disk. The mount at `~/s3-ils-data`
is read-only *on purpose* — object storage has no locking and no atomic rename.

**3. Never use `--delete`.**
It mirrors exactly. From a stale local view it erases a colleague's work. Publisher-only.

**4. Never publish `knowledge-graph/`, never rebuild the KG.**
There are **115** hand-authored community names (2026-10-02) that nothing regenerates — a
rebuild keeps only a third to a half of them. Two machines publishing destroys them
silently. You *read* the graph in Cursor with the **`kg` skill** (it runs
`kg_query.sh`). History first — never grep `data/changes/` as the first move. New tickets
appear in the graph only after the publisher's next refresh.

If you think a refresh is due, ask Cursor for **`kg-refresh`** (it files a request
because you are a contributor) — do not rebuild. By hand, from `s3-sync/`:

```bash
bash ../../knowledge-graph/kg_refresh.sh request "why you think so"
./data-push.sh --go
```

✅ **The tool enforces this, and your normal pushes are unaffected.** On a contributor
machine `data-push.sh --go` pushes every other root as usual and still uploads
`knowledge-graph/refresh_queue/` (your request mailbox). Expect:

```
  knowledge-graph/: 'groundtruth' holds the publisher baton; this machine is '<yours>'.
    The graph and its names are publisher-only, so only refresh_queue/ is pushed from here.
    This is expected on a contributor machine and is NOT an error.
>>> knowledge-graph  (refresh_queue/ only — the publisher owns the rest)
```

That is normal (a dry run does not print it). Do not "fix" it or escalate it.

**5. Shared ledgers are append-only — and you must guard the push, not only the pull.**
`STATUS.md`, `TICKETS.md`, `FOLLOWUPS.md`, `TEST_MAP.md`, `CUSTOMER_GUIDANCE.md`.
Add your rows; never rewrite someone else's. Last-writer-wins drops their line silently.
A push that overwrites a hub file your colleague just edited protects *nobody on your
machine* — measured 2026-09-18: **11 lines gone, no conflict, no error**. If
`data-push.sh` **refuses (exit 4)**, that is not noise: diff yours against the bucket,
**merge**, push again. Do not reach for `--allow-clobber`.

**6. Use the `day` skill.** Documentation of "pull at the start, push at the end"
does not enforce the habit. `day start` / `day end` does, and its audit trail is
what made the losses above detectable.

Everything else is naturally safe: **your ticket folders are yours.**
`changes/sst-nnnn/` is one person's workstream.

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

1. **Open the day.** In Cursor: **`day start`** — pulls the shared record (after
   checking for unpublished local work), then a short briefing. Do not skip this
   because you "already pulled yesterday".
2. **Triage before code.** Confirm the symptom in *our* `get-sl-upload-status` JSON.
   If the data is correct there, push back — do not start work in this repo.
3. **History first.** Query the KG (`kg` skill / Agent) *before* grepping
   `data/changes/`. Then read the records it names.
4. **Plan, agree, then code** in Cursor. No production code until the plan is agreed.
5. **Test first.** Failing scoped test → minimal code → green.
6. **Verify before claiming done.** Look at the actual output — not just counts.
7. **Document** in `data/changes/sst-nnnn/sst-nnnn.md` — one main doc per ticket, exactly that
   name, **lowercase** (the KG indexes it; S3 keys are case-sensitive while your disk may not be).
   QA evidence goes in `sst-nnnn/qa_review_N/`. A "follow-up" is an entry in
   `data/changes/FOLLOWUPS.md` — agents never open Jira tickets.
8. Close the day with **`day end`** (writes the record, publishes). If the corpus moved and a
   rebuild is due, **`kg-refresh`** files a request — you do not rebuild.
9. **Human gate:** you (or your lead) push / open the PR / deploy — do not let the
   agent do irreversible outward actions unless you explicitly ask in that session.
10. **Session continuity:** `day end` plus rewrite the rolling entry-point note
    (`data/changes/_RESUME_<date>.md`) so the *next* Cursor chat is not blind.

Branches: `fix/sst-1234-short-description` (or `feat/`, `ops/`, `chore/`), based on
`development`; PR title `SST-1234 Short description`; squash-merged. PR comments are short
plain prose.

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
| Cursor orientation (always-on) | `AGENTS.md` + `.cursor/rules/` (copied from the pack; load when you open the folder) |
| Daily shared-record loop | Cursor **`day`** skill (`day start` / `day end`) |
| Ticket history / KG | Cursor **`kg`**; rebuild request **`kg-refresh`** (contributor) |
| Shared-record mechanics | Confluence: **Shared record (S3 sync)** + `s3-sync/FOR_NEW_JOINERS.md` in the pack |
| Methodology playbook | Confluence siblings: Diagnose, Verify, Context, Human gate |
| Why code looks the way it does | `data/changes/sst-nnnn/sst-nnnn.md` (after first pull) |
| Current in-flight state | `data/changes/STATUS.md` and the newest `data/changes/_RESUME_<date>.md` |
| What we have told clients | `data/changes/CUSTOMER_GUIDANCE.md` |

---

## 10. Ask about these — known-unsettled

- How fixes reach stage: `origin/stage` is frozen (since 2026-08-14); live refs are
  `release/NN.NN` branches. Ask before promising QA a stage deploy
- What counts as "one provision" — open with Legal
- Anything in the newest `data/changes/_RESUME_<date>.md`

Nobody expects you to resolve these. Knowing they are open stops you assuming there
is a rule you failed to find.
