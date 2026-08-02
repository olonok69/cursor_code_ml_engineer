# Machine-sync runbook — main ⇄ laptop (travel)

**Load this only when moving the workspace between the main computer and the travel laptop.**
It is gitignored (lives under `data/`) — machine/ops content, never ships.

> **Handing the bundle to the laptop's Claude agent?** Point it at **`data/machine-sync/LAPTOP_START_HERE.md`** —
> the single orchestrator that sequences this RUNBOOK's restore steps + the KG bootstrap and tells the agent how
> to continue working identically and send an increment back. This RUNBOOK is the OS/tooling detail it links to.

- **Outbound (main → laptop, before travelling): FULL COPY.** One tarball carries the whole
  `/mnt/d/ILS` workspace + home config; the laptop starts from a clean, identical state.
- **Inbound (laptop → main, on return): DELTA ONLY.** Code is already on GitHub — pull it with
  `git fetch`. Only the gitignored `data/` docs (a few MB) travel in a small tarball.
  Canonical worked example: `data/ils-to-main/INSTRUCTIONS.md` (the 2026-06-30 landing).

Transfer medium assumed: **USB drive** (mounts under WSL as `/mnt/<letter>`, e.g. `/mnt/e`).
A FAT32 USB won't preserve Linux perms/symlinks — that's fine, everything is inside the `.tar.gz`
which preserves them internally.

---

## Machine facts (verified 2026-07-05, confirm before trusting)

| Fact | Value on the **main** computer | Why it matters |
|---|---|---|
| Workspace root | **`/mnt/d/ILS`** (NOT `/mnt/c/repos/ILS`) | wrong `-C` path = empty archive |
| Repos present | document-parser-lambda, frontend, monolith, message-exchange-service, index-vectorizing-service, infrastructure, helm-values, **mfn-lambda, mfn-service** | `-C /mnt/d/ILS ILS` grabs them all |
| `~/.claude` | real dir | copy as-is |
| `~/.ssh` | real dir | copy as-is |
| `~/.aws` | **symlink → `/mnt/c/Users/Administrator/.aws`** | must `-h` (dereference) or laptop gets a dead link |
| `~/.gnupg` | **absent** | do NOT list it — `tar` errors and returns non-zero |
| Last full tar size | ~931 MB | size the USB accordingly; "a few hundred MB" is stale |
| AWS CLI binary | **`/usr/local/bin/aws`** (aws-cli/2.35.15, system-wide) — installed 2026-07-05 | the binary is NOT in the bundle; the **target** installs it separately (see Step 4b) |
| GSD | `~/.claude/get-shit-done` v1.42.3 — **travels inside the `.claude` copy** | skills/engine come across; run `/gsd-update` on target only if behind + to re-link the SDK symlink/hooks |
| CodeGraph CLI | `codegraph` v1.2.0 — npm global, **NOT in the bundle**; index `.codegraph/` **excluded** from the tar | target installs CLI + rebuilds index (Step 4c) |
| codegraph MCP `--path` | hard-coded `/mnt/d/ILS/document-parser-lambda` in `~/.claude.json` `mcpServers.codegraph.args` | **must be fixed to the target's WS root** if it differs (Step 4c) |

> The path and dotfile layout differ per machine. **Discover, don't assume** — the commands below
> derive the workspace root instead of hardcoding it. Re-run the fact check any time:
> `ls -ld /home/$USER/.aws /home/$USER/.gnupg /home/$USER/.ssh /home/$USER/.claude; ls -d /mnt/*/ILS 2>/dev/null`

---

## OUTBOUND — main → laptop (full copy)

### Step 1 — On the MAIN computer: build the bundle

Three corrections vs. the old plan are baked in: `-C /mnt/d/ILS`, `.gnupg` dropped, **`-h` added
so the `.aws` symlink is dereferenced** (real creds archived, not a dead link).

```bash
WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)   # -> /mnt/d/ILS on main
echo "workspace: $WS"
STAMP=$(date +%Y%m%d)

tar -czhf ~/ils-migration-$STAMP.tar.gz \
  --exclude='*/node_modules' \
  --exclude='*/.codegraph' \
  --exclude='*/.venv' --exclude='*/.venv-win' --exclude='*/.venv-1' \
  --exclude='*/__pycache__' --exclude='*/.pytest_cache' \
  --exclude='*/.ruff_cache' --exclude='*/.mypy_cache' \
  --exclude='*.pyc' \
  -C "$(dirname "$WS")" "$(basename "$WS")" \
  -C /home/$USER .claude .aws .ssh
ls -lh ~/ils-migration-$STAMP.tar.gz
```

- `-h` = **dereference symlinks** — critical for `.aws`. Without it the laptop's AWS CLI is silently
  unconfigured.
- `.gnupg` intentionally omitted (absent on main; git-secret/GPG isn't used — the Docker build takes a
  GitHub PAT via BuildKit secret, not GPG). If a future machine *does* have `.gnupg` with git-secret
  keys, add it back to the home list.
- `.codegraph` excluded (like venvs/caches): it's a machine-local sqlite index with **absolute
  `/mnt/d/ILS/…` paths baked in**, so shipping it to a laptop with a different WS root would be wrong.
  Rebuilt fresh on the target with `codegraph init` — see Step 4c.
- Expect **~900 MB+**. If the number is a few KB, the `-C` path was wrong — check `$WS`.

### Step 2 — Copy to USB (on main), carry it over

```bash
cp ~/ils-migration-*.tar.gz /mnt/e/     # adjust drive letter (ls /mnt/)
sync                                     # flush before unplugging
ls -lh /mnt/e/ils-migration-*.tar.gz     # confirm full size landed
```

### Step 3 — On the LAPTOP: copy off USB and extract (non-destructive)

```bash
cp /mnt/e/ils-migration-*.tar.gz ~/       # adjust drive letter
INCOMING=$(ls -t ~/ils-migration-*.tar.gz | head -1)

WS=$(ls -d /mnt/*/ILS 2>/dev/null | head -1)   # laptop's workspace root (may differ!)
# If the laptop has no ILS yet, pick where it should live, e.g. WS=/mnt/c/repos/ILS; mkdir -p "$(dirname "$WS")"

# park any existing workspace first — never delete, rename
[ -d "$WS" ] && mv "$WS" "$WS.laptop.bak.$(date +%Y%m%d)"

tar -xzf "$INCOMING" -C "$(dirname "$WS")"        # restores the ILS/ tree
tar -xzf "$INCOMING" -C /home/$USER .claude .aws .ssh   # restores home config
```

> If the laptop's `~/.aws` is normally its own symlink to a Windows path, extracting a real `.aws`
> dir over it is fine (the creds are what you want). Just don't be surprised the symlink is gone.

### Step 4 — Verify the restore on the laptop, then rebuild

```bash
cd "$WS/document-parser-lambda"
git log --oneline -3      # main's commits present?
git stash list            # stashes came across?
git status -s             # uncommitted/untracked files present?
```

Recreate the excluded heavy dirs **per repo you'll actually run**:
`python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
for Python repos; `npm install` in `frontend`. Integration runs also need `tesseract` + `libreoffice`
on PATH (see `document-parser-lambda/CLAUDE.md` → Testing / External binaries). The `.codegraph/` index was
also excluded — rebuild it per repo you'll navigate with `codegraph init` (handled by Step 4c).

### Step 4b — AWS CLI on the laptop (the binary is NOT in the bundle)

The tarball carries your **`.aws` config** (dereferenced from the symlink → real files), but **not the
`aws` binary** — that's a system install. Config without a binary can't do anything, so on the laptop:

1. **Install the CLI if missing** (`command -v aws || echo missing`). System-wide (needs the sudo
   password — canonical `/usr/local/bin/aws`, matches the main machine):
   ```bash
   cd /tmp && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o awscliv2.zip
   unzip -q awscliv2.zip && sudo ./aws/install
   ```
   If sudo is password-blocked, fall back to a user-local install (no sudo), but then **use only one**
   to avoid a stale-path shadow: `./aws/install --install-dir ~/.local/aws-cli --bin-dir ~/.local/bin`.
2. **Confirm config restored** — profiles should already be there from the bundle:
   ```bash
   hash -r                       # clear any stale command-path cache first (see Guardrails)
   aws --version
   aws configure list-profiles   # expect: nonprod-dev, dev-new, prod-dev, default
   ```
   > After a full-copy restore, laptop `~/.aws` is a **real dir (a snapshot)**, not a live symlink to
   > Windows — it won't auto-track Windows-side changes. Fine for travel. The SSO *token cache* in it
   > is stale/expired regardless, so:
3. **Log in once** (one session covers all three profiles — shared `ils` sso-session; opens a browser):
   ```bash
   aws sso login --profile nonprod-dev
   aws sts get-caller-identity --profile dev-new   # expect Account 055622654641, ReadOnlyAccess
   ```

### Step 4c — CodeGraph + GSD on the laptop (tooling not fully in the bundle)

The `.claude` copy carries GSD's skills/engine and the codegraph **MCP config**, but **not** the `codegraph`
CLI binary (npm global) or the `.codegraph/` index (excluded; its paths are main-specific). And the copied
MCP `--path` still points at the **main** workspace root. Fix all of it in one idempotent pass:

```bash
bash "$WS/document-parser-lambda/data/machine-sync/target-setup.sh"
```

It (1) discovers the laptop's real `$WS`, (2) updates GSD to latest **only if behind**, (3) installs the
`codegraph` CLI if missing, (4) rewrites the codegraph MCP `--path` in `~/.claude.json` to the laptop's repo
(backs the file up first), (5) builds the index (`codegraph init`, or `sync` if one already exists). It is
safe to re-run. Then **restart Claude Code** and verify:

```bash
codegraph status                     # "Index is up to date", path = laptop repo
codegraph --version ; cat ~/.claude/get-shit-done/VERSION
# in a Claude session, a BARE query (no projectPath) must resolve, not error:
#   codegraph_explore "get_letter_end"   -> blast radius + source
```

Manual equivalent (if you'd rather not run the script): `npm i -g @colbymchenry/codegraph`; edit
`mcpServers.codegraph.args` `--path` in `~/.claude.json` to `$WS/document-parser-lambda`; `cd` there and
`codegraph init`; for GSD run `/gsd-update` in a session (or `npx -y get-shit-done-cc@latest --claude --global`).

### Step 4d — Ticket knowledge graph (`/kg`) on the laptop

The `.claude` copy carries the `/kg`, `/kg-refresh`, `/graphify` **skills** + the **memory corpus**, and the
workspace copy carries the **built graph** (`data/knowledge-graph/output/`) + **scripts**. Missing on a bare
machine: the `graphifyy` **package** and a correct interpreter pin. One idempotent command fixes both:

```bash
bash "$WS/document-parser-lambda/data/knowledge-graph/kg_refresh.sh" bootstrap
```

It installs `graphifyy`, re-pins `graphify-out/.graphify_python`, and smoke-tests `/kg SST-5623`. Then
`/kg <ticket-or-topic>` works immediately (the graph came in the bundle — no rebuild needed to query). Full
rationale + the memory round-trip: `data/changes/knowledge-graph/TRAVEL_SYNC.md`.

Only after Steps 4 + 4b + 4c + 4d look right: `rm -rf "$WS.laptop.bak."*`.

---

## INBOUND — laptop → main (delta only)

Don't full-copy back — you'd clobber whatever the main computer did meanwhile. Instead:

1. **Code** → push from the laptop as normal PRs, then on main just `git fetch origin` (read-only).
   Nothing physical to move.
2. **Gitignored `data/` docs** (ticket writeups, fixtures, captures) → the only thing that needs a
   tarball. **First snapshot memory** (excluded from the delta otherwise), then build repo-relative:
   ```bash
   cd "$WS/document-parser-lambda"
   bash data/knowledge-graph/kg_refresh.sh snapshot-memory     # -> data/knowledge-graph/_memory_snapshot/
   tar -czf ~/ils-delta-$(date +%Y%m%d).tar.gz \
     data/changes/<new-or-changed-dirs> \
     data/knowledge-graph/_memory_snapshot \
     data/<other-changed-paths>
   ```
   Write a short `INSTRUCTIONS.md` + `MANIFEST.txt` beside it (guardrails, file counts,
   STATUS.md-reconciliation note) — copy the shape of **`data/ils-to-main/`**.
3. On main, land it with the **`data/ils-to-main/INSTRUCTIONS.md`** runbook: `git fetch`, back up
   `data/changes/STATUS.md` → extract → `diff` → reconcile. Non-destructive; STOP and ask if
   STATUS.md shows the main side made its own edits. **Then fold in memory + rebuild the KG:**
   `bash data/knowledge-graph/kg_refresh.sh restore-memory` → `/kg-refresh` → verify a travelled ticket
   resolves via `/kg` → `rm -rf data/knowledge-graph/_memory_snapshot`.

**Never** move venvs / node_modules / caches — rebuild locally. **Never** full-copy inbound.

---

## Guardrails (both directions)

- Non-destructive only: **rename, don't delete**; never run two file-moving ops at once on a
  `/mnt/c|d` Windows mount (a prior session lost a workspace to concurrent `rm`/`chmod` there).
- No git writes to the remote as part of *landing* a delta — `git fetch` is the only network git op.
- The main's 931 MB `~/ils-migration-20260626.tar.gz` is a standing safety backup — keep one recent
  full tar around before any extract.
- Re-verify the "Machine facts" table if it's been a while — repo list and dotfile layout drift.
- **`bash: .../aws: No such file or directory` after (re)installing a binary** = bash cached the old
  path in its command hash. Run `hash -r` in that shell (or open a new one). Don't reinstall.
- If you ever run *both* a system (`/usr/local/bin`) and user-local (`~/.local/bin`) CLI install, the
  user-local one shadows the system one on PATH and can serve a stale version — keep exactly one.
