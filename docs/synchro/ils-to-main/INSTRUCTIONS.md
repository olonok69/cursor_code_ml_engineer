# RUNBOOK — land the laptop→main delta (for an AI coding agent on the MAIN computer)

**You are an AI agent running on the MAIN computer.** A second machine (a laptop) did some work and produced this delta. Your ONLY job is to **land this delta safely** so the main computer has the same in-progress state. You are NOT implementing features, NOT merging PRs, NOT pushing anything. Read "Guardrails" before running any command.

- **Date produced:** 2026-06-30
- **Source:** laptop (WSL Debian 13). **Target:** this machine (MAIN) — the original source of the 2026-06-26 migration; it already has the full ILS workspace as of 2026-06-26, plus gh/uv/aws-cli, the SST-5385 uncommitted work, and 6 git stashes.
- **Nature of the delta:** code is already on GitHub (pull via `git fetch`); only ~1.8 MB of git-ignored `data/` docs need physical extraction from `ils-delta-20260630.tar.gz`.

---

## Guardrails (MUST follow)
1. **Non-destructive only.** Do NOT `rm -rf`, force-checkout, reset, or overwrite anything except exactly as specified. Never run two destructive/file-moving operations at once. (A prior session lost a workspace to concurrent `rm`/`chmod` on a Windows-mounted drive — do not repeat.)
2. **No git writes to the remote.** No `commit`, `push`, `merge`, PR creation, or PR comments. The two PRs are already open on GitHub. `git fetch` (read-only) is the only network git op you run.
3. **Back up before you overwrite.** The only file this delta overwrites that may already exist with different content is `data/changes/STATUS.md`. Always copy it to `STATUS.md.mainbak` first, then `diff`.
4. **STOP and ask the user** (do not improvise) if any "STOP condition" below is hit.
5. **Don't start the new investigation.** The delta includes a `side_letters_29062026/` folder of fresh inputs. Landing it = copying the files. Do NOT begin extracting/analysing them unless the user explicitly asks.
6. Obey the repo's own `CLAUDE.md` working rules; this task does not require any code change.

---

## Step 0 — Discover paths (do not assume)
The repo location differs per machine (laptop used `/mnt/c/repos/ILS`; this machine may use `/mnt/d/ILS` or elsewhere).
```bash
# find the document-parser-lambda repo
REPO=$(find /mnt/c /mnt/d /home -maxdepth 5 -type d -name document-parser-lambda 2>/dev/null | head -1)
echo "REPO=$REPO"
cd "$REPO" || { echo "STOP: repo not found — ask the user for the path"; exit 1; }
git rev-parse --is-inside-work-tree && git remote -v | head -1   # confirm it's the right git repo

# find the delta tarball the user copied from USB (ask if not found)
TARBALL=$(find /home /mnt/c /mnt/d /mnt/usb /mnt/e /mnt/f -maxdepth 4 -name 'ils-delta-20260630.tar.gz' 2>/dev/null | head -1)
echo "TARBALL=$TARBALL"
```
**STOP condition:** if `REPO` or `TARBALL` is empty, ask the user for the exact path. Do not guess further.

## Step 1 — CODE: pull from GitHub (no file copy)
```bash
cd "$REPO"
git fetch origin
git branch -r | grep -E 'sst-5404|sst-5016'
```
**Expected:** both remote branches present —
- `origin/fix/sst-5404-general-style-levels` (PR #122 — SST-5404)
- `origin/feat/sst-5016-provision-html-phase-2` (PR #119 — SST-5016)

Confirm the SST-5404 commit is intact:
```bash
git log origin/fix/sst-5404-general-style-levels -1 --oneline
```
**Expected:** `3f7ad4a fix: SST-5404 — deterministic boundaries for "General N L#" provision styles` (author Juan Huertas).

You do NOT need to check these branches out. Do NOT merge or rebase them.
**Note:** this machine already has the local `fix/sst-5385-oversized-result-s3` branch with uncommitted work and 6 stashes — leave them alone; they are not part of this delta.

## Step 2 — DATA: extract the git-ignored docs
```bash
cd "$REPO"
cp data/changes/STATUS.md data/changes/STATUS.md.mainbak   # back up FIRST
tar -xzf "$TARBALL" -C "$REPO"                              # paths inside the tar are relative to repo root
```
Files written/overwritten under `data/`:
- `data/changes/sst-5404/` — NEW (4 docs: `sst-5404.md`, `_handover_to_cursor.md`, `qa_acceptance_criteria.md`, `_jira_ticket_draft.md`)
- `data/changes/STATUS.md` — UPDATED (reconcile in Step 3)
- `data/error_loading/side_letters_26062026/` — SST-5404 fixture `.docx` + `.json` + jira draft
- `data/error_loading/side_letters_29062026/` — NEW fresh inputs (Avista / Niobrara / OHCP side letters + `comment support.txt` + screenshot) — copy only; do not process
- `data/issues/ASF IX Infra B_NYC BERS_SL_EXE (2).docx`, `data/webster/webster_vi_…state_farm…docx` — test fixtures

## Step 3 — Reconcile STATUS.md (needs judgment)
```bash
cd "$REPO"
diff data/changes/STATUS.md.mainbak data/changes/STATUS.md
```
Decision:
- **Diff shows only ADDITIONS that are SST-5404 / SST-5016-PR notes** → the laptop's copy is newer; keep it:
  ```bash
  rm data/changes/STATUS.md.mainbak
  ```
- **STOP condition — diff shows the main copy had its OWN edits** (lines present in `.mainbak` that the new file drops): the main computer was NOT dormant. Do NOT keep the overwrite blindly. Restore the backup and ask the user to merge:
  ```bash
  # if conflict detected, restore and stop:
  # cp data/changes/STATUS.md.mainbak data/changes/STATUS.md   # (only if you must revert)
  ```
  Report the diff to the user and wait.

## Step 4 — Verify (report each result)
```bash
cd "$REPO"
git branch -r | grep -E 'sst-5404|sst-5016' | wc -l        # expect 2
ls data/changes/sst-5404/ | wc -l                           # expect 4
ls "data/error_loading/side_letters_29062026/" | wc -l      # expect 5
command -v gh >/dev/null && gh pr view 122 --json state,title -q '.state+" "+.title' || echo "gh not available — skip"
command -v gh >/dev/null && gh pr view 119 --json state,title -q '.state+" "+.title' || echo "gh not available — skip"
```
**Expected:** 2 branches, 4 sst-5404 docs, 5 new-folder files; both PRs `OPEN`.

## Step 5 — Report back to the user
Summarise: REPO path used, both branches fetched (yes/no + the 3f7ad4a check), data delta extracted (file counts), STATUS.md outcome (kept laptop copy / conflict-stopped), and PR states. Note that no commits/pushes were made.

---

## Reference facts (for verification)
| Item | Value |
|------|-------|
| SST-5404 branch / PR | `fix/sst-5404-general-style-levels` / PR **#122** |
| SST-5404 commit | `3f7ad4a` — "fix: SST-5404 — deterministic boundaries for \"General N L#\" provision styles" |
| SST-5404 author | Juan Huertas <olonok@gmail.com> |
| SST-5404 files (in commit) | `src/data_extractors/doc_extractor.py` (+74/−4), `tests/test_sst_5404_general_style_levels.py` (new, +250) |
| SST-5016 branch / PR | `feat/sst-5016-provision-html-phase-2` / PR **#119** |
| Repo remote | `git@github.com:ils-tech/document-parser-lambda.git` |
| Delta tarball | `ils-delta-20260630.tar.gz` (15 files, ~1.8 MB; full list in `MANIFEST.txt`) |

## What this delta intentionally does NOT carry
- **Source code** — on GitHub (Step 1).
- **SST-5385 uncommitted work + 6 stashes** — already on this main computer (it was the migration source; never edited on the laptop).
- **venvs / node_modules / caches** — rebuild locally only if you will run code (`bash <ILS>/rebuild-all.sh`; canonical DOC battery needs `tesseract` + `libreoffice`, already installed on main).
- **`~/.claude` memory** — laptop-specific; not copied.

## PR status snapshot (2026-06-30)
- **PR #122 (SST-5404):** OPEN. CI `validate` ✅, Cursor Bugbot ✅ (no findings). `@ils-tech/backend` review requested. Mergeable; blocked only on review approval.
- **PR #119 (SST-5016):** OPEN. CI `validate` ✅, Cursor Bugbot ✅ (Low Risk). `@ils-tech/backend` requested. Blocked only on review approval; branch is 2 commits behind `development` (no conflicts).
Both are functionally complete and gate-cleared — they await a human backend approval. Do not attempt to merge them.
