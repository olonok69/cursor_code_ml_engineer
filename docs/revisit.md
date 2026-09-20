# Upstream update 2026-09-19 — for the Cursor agent

**You are the agent working in `cursor_code_ml_engineer`.** This file tells you what changed in the
Claude Code training pack (`claude_code_ml_engineer`) and what to carry across — **adapted to
Cursor, not transcribed.**

**Reference implementation:** everything named below exists, finished, in the Claude Code repo.
Open the file, read how it is written, then write the Cursor equivalent. Do not invent a second
version of a rule that already has wording here.

> ⚠️ At the time of writing, the Claude Code changes are **committed to the working tree but not
> pushed** — the human owns those commits. If a path below is missing from `origin`, ask before
> assuming it was dropped.

**Local paths on the machine where this was written:**
`/mnt/d/repos/claude_code_ml_engineer` (source) · `/mnt/d/repos/cursor_code_ml_engineer` (target).

---

## Why there is anything to carry

On 2026-09-18 two machines edited the shared status ledger the same afternoon. The second push
replaced the first wholesale: **11 lines gone, no conflict, no error**, and nothing on the pushing
machine looked wrong afterwards. It went a full day unnoticed, and was recovered only because bucket
versioning happened to be enabled.

Both packs already teach *"shared ledgers are append-only"* and *"detect it with a pull-time
check"*. **Both were half right.** The pull-time check is the one everybody builds, because it
protects the person running it. The loss happens on **push**, against a copy the pusher never had.

Two further failures surfaced while fixing that, and both generalise beyond this tooling. They are
the substance of this update.

---

## ⚠️ Read before you start: measure, don't assume

The state below was **measured** in `cursor_code_ml_engineer` on 2026-09-19, not guessed.

### Already correct here — do NOT touch

| Item | Evidence |
|---|---|
| Append-only shared ledgers | 4 hits across `GUIA_TECNICA*.md` + `docs/synchro/s3-sync/README.md` |
| Recovery expires at ~30 days | 4 hits |
| Shared store wins on divergence | 4 hits |
| `sanitise-diff` skill, already free of the client-name list | 0 hits for client names — **cleaner than the live copy it came from** |
| Four methodology skills present | `docs/ai-agents-code-methodology/cursor/skills/{kg,kg-refresh,sanitise-diff,methodology-plan}/` |

The 2026-09-08 update landed properly. This one sits on top of it.

### Missing here — your work list

| # | Gap | Evidence it is missing | Reference in the Claude pack |
|---|---|---|---|
| 1 | Guard **both directions** (push clobbers the colleague) | 0 hits for `both directions` / `AMBAS direcciones` / `guard.*push` | `GUIA_TECNICA_EN.md` §15B table, new row 1 |
| 2 | The `exit 4` refusal + `--allow-clobber` and why not to use it | 0 hits for `exit 4` / `REFUSED` / `allow-clobber` | same table, new row 3 |
| 3 | A per-machine file needs exactly ONE writer | 0 hits | same table, new row 2 |
| 4 | A guard can disable the instrument that proves the habit (EXIT trap) | 0 hits for `EXIT trap` | `GUIA_TECNICA_EN.md` §15B, callout before "Budget for the judgement…" |
| 5 | Measure an optimisation before quoting it | — | same, second new callout |
| 6 | **The `day` skill is absent entirely** | 0 `SKILL.md` under any `day/` | `ejemplos/skills-plugins/.claude/skills/day/SKILL.md` |
| 7 | Why a skill beats a document (enforcement, not convenience) | — | §15B "the habit needs a mechanism" block + §8 cross-reference |
| 8 | The sync scripts are not shipped at all | no `data-push.sh`, no `config.env*` anywhere | `ejemplos/metodologia/s3-sync/` (11 scripts + template + README) |
| 9 | Deck bullet is misleading in the same way | `build_pptx_cursor.py:1116` (+ `_en.py:1116`) | see §6 below |

---

## 1 · §15B — three table rows and two callouts

**Source:** `claude_code_ml_engineer/GUIA_TECNICA_EN.md` and `GUIA_TECNICA.md`, section
*"B. The shared record: `data/` over S3"*.

**Target:** `cursor_code_ml_engineer/GUIA_TECNICA.md:711` and `GUIA_TECNICA_EN.md:711`.

Carry three rows into the rules table, after *"the shared store wins on divergence"*:

1. **Guard both directions.** A pull clobbers *you* and you can be made to notice. A push clobbers
   *your colleague* and you cannot — the evidence is on a machine you never look at. Refuse, do not
   warn: a warning inside a 60-line transfer preview is exactly what gets scrolled past.
2. **A per-machine file needs exactly one writer, enforced in the tool.** Splitting a ledger into
   one file per machine removes contention *by design*, and the tool can still break it — ours
   uploaded every machine's file, including its permanently-stale copy of someone else's. **The
   first symptom was not a corrupt file: it was a wrong conclusion about a person.** With his
   record erased, the dashboard said a colleague had never closed his day. He had.
3. **A guard that cries wolf on day one teaches people to override it.** The first version compared
   timestamps only and would have refused a teammate's very first push, on files he had just pulled
   and held byte-for-byte. A false-positive rate is a **safety property**, not a UX nicety.

And two callouts (place them beside the existing *"a role that exists only in documentation is
untested code"* one — they are the same genre):

4. **A safety guard can silently disable the instrument that proves the habit.** The pre-pull
   snapshot installed its own `trap ... EXIT`; bash keeps one, so it replaced the one writing the
   activity ledger. That block runs only on the real path, so dry runs kept logging and every real
   pull went unrecorded for two days while the dashboard stayed populated and plausible. Ask what
   else claims the same single-slot resource; remember the real path and the rehearsal path are
   different code. ⚠️ Keep the isolation detail — a marker line survived a real pull
   **byte-identical**, which separated *"written then overwritten"* from *"never written"* where a
   line count could not.
5. **Measure an optimisation before you quote it.** Restricting the sweep to the one directory that
   changes daily was predicted to take the check "from two minutes to seconds". Measured
   **212s → 123s, ~40%**. Quoted from intuition it would have entered onboarding as fact.

---

## 2 · §15B — "the habit needs a mechanism, not a paragraph"

Carry the block that introduces the `day` routine, and keep its point intact: *"pull at the start,
push at the end"* sat in the operations doc **for months without being followed** on the very
machine that published. Nothing recorded a sync, so nothing could show the drift — the lapse was
invisible even to the person lapsing. **Documentation cannot enforce a habit; a callable routine
can**, and its audit trail is what made both failures above detectable at all.

Add the matching one-liner to §8 (slash commands / skills): the strongest reason to reach for a
skill is **enforcement**, not convenience.

---

## 3 · The `day` skill — port it, do not transcribe it

**Source:** `ejemplos/skills-plugins/.claude/skills/day/SKILL.md` (242 lines, already genericised:
`<your-repo>` placeholders, no client names, no ticket IDs).

**Target:** `ejemplos/skills-plugins/.cursor/skills/day/SKILL.md`, beside the existing `audit`,
`audit-python` and `deploy-staging` examples — and, if you keep the parallel set,
`docs/ai-agents-code-methodology/cursor/skills/day/SKILL.md` next to the other four.

⚠️ **A live Cursor version already exists** in the production repo at
`document-parser-lambda/.cursor/skills/day/SKILL.md` — 191 lines as of 2026-09-19 (it gained the
exit-4 block the same day), already in Cursor's idiom. If you can reach it, adapt **that** and take the new material from the Claude copy;
it will read far better than a translated Claude skill. It needs the same genericising pass — it
carries a repo name and a client fixture directory name.

Frame it in the README the way the Claude pack does: **read it for the shape, not the commands.**
Every dangerous step is gated behind a question it answers first — *is there unpublished local
work? which files will this pull overwrite? may this machine publish the derived artifact?* — and
where the answer is ambiguous it **stops and asks**. A routine that resolves ambiguity on its own is
precisely the one that destroys someone else's work.

---

## 4 · Ship the sync scripts

**Source:** `ejemplos/metodologia/s3-sync/` — 11 scripts, `config.env.example`, and a README.

**Target:** the Cursor pack has **two** language folders (`ejemplos/metodologia/` and
`ejemplos/metodologia_en/`) where the Claude pack uses file suffixes. Decide where the scripts live
— they are language-neutral code, so one copy plus a README in each language is probably right, not
two copies. Add the row to whichever index files you use.

⛔ **Never ship `config.env`.** It names a bucket, two account profiles and a machine role. Start
from `config.env.example` — and note *why* the scripts are publishable at all: genericising the
eleven of them changed **one line in one file**, because everything environment-specific already
lived in the config. That fact is worth stating; it is the payoff of the design.

The template carries four filter rules, each of which cost a real incident: filter **order** decides
the winner · `--include` is **case-sensitive** · use **prefix globs**, not `<dir>/*` · **per-machine
files must be excluded**. Keep all four.

---

## 5 · The `docs/synchro/s3-sync/README.md` amendment

Both packs ship this file and both carry the same now-incomplete claim — that a pull-time
append-only check *"has essentially no false positives"*. True, and it still lost work. Carry the
correction from the Claude copy: the check covers one direction, the damage happens in the other,
plus the two refinements (compare **content** not just timestamps; one writer per per-machine file).

---

## 6 · The deck

⚠️ **The two packs build decks differently — do not copy the Claude procedure.**

The Claude deck is `build_pptx.py` (Spanish) + `translations_en.py` (keyed by the exact Spanish
string) **+ `merge_manual_slides.py`**, because three slides are hand-made and the generator
silently destroys them: it emits 37, the shipped deck is 40. Running the generator alone dropped the
deck from 1,915,779 to 1,057,904 bytes on 2026-09-19 before it was restored from git.

**The Cursor pack has no such landmine** — `build_pptx_cursor.py` / `build_pptx_cursor_en.py` are
standalone, with no manual-slide merge step. Build them directly.

**The change:** `build_pptx_cursor.py:1116`, card *"B · Día a día: registro sobre S3"*, bullet 3
currently reads:

```
"Dry-run por defecto; --delete opt-in (no borrar al compañero)"
```

and its twin at `build_pptx_cursor_en.py:1116`:

```
"Dry-run by default; --delete opt-in (don't delete a teammate's work)"
```

That is misleading in precisely the way this update is about — **you destroy your colleague's work
without `--delete` being involved at all.** Suggested replacement, same length class so the card
does not overflow:

```
"Dry-run por defecto; guardia en AMBAS direcciones (sin --delete también se pisa)"
```

English equivalent, same length class:

```
"Dry-run by default; guard BOTH directions (you clobber without --delete too)"
```

✅ Your two build scripts are **independent** — the bullet text is duplicated at the same line
number in each, not keyed across files, so edit both directly. (The Claude pack pairs Spanish→
English by exact string key, where changing one without the other silently leaves the English deck
untranslated. That trap does not apply to you.) Rebuild both and assert the new text is present
**and** the old text is gone.

---

## 7 · Sanitisation — one finding you should apply to yourselves

While extracting `sanitise-diff` for the Claude pack, the final leak scan caught exactly one hit,
and it was **in the sanitiser itself**: the skill carries the client-name blocklist inline. So the
one file whose entire job is catching client names is the one file guaranteed to contain all of
them — and it is exactly the file that gets copied into examples, pasted into tickets and shipped in
onboarding packs.

**Your copy is already clean** (measured: 0 hits), so nothing to fix here. But the reasoning is
worth adding to the skill's own text: keep the list in a gitignored side file and have the skill
read it. *The mechanism is shared; the content is not.* The Claude copy now ends with that note —
copy it.

⚠️ **The live production copy still has the list inline**, and it ships in the joiner pack. That is
the production team's to fix, not yours, but do not re-import it.

---

## How to verify you are done

Run these in `cursor_code_ml_engineer`. Each must go from 0 to non-zero — and **check the canary
column**, because a scan that finds nothing everywhere is not evidence of anything:

```bash
# each of these should be > 0 when the item has landed
grep -rEic 'AMBAS direcciones|both directions'        GUIA_TECNICA.md GUIA_TECNICA_EN.md
grep -rEic 'exit 4|REFUSED|allow-clobber'             GUIA_TECNICA.md GUIA_TECNICA_EN.md docs/synchro/s3-sync/README.md
grep -rEic 'trap .* EXIT|EXIT trap'                   GUIA_TECNICA.md GUIA_TECNICA_EN.md
test -f ejemplos/skills-plugins/.cursor/skills/day/SKILL.md && echo "day skill: yes"
test -f ejemplos/metodologia/s3-sync/config.env.example && echo "scripts: yes"

# canary — this MUST be 0, or your sanitisation is not working
cat ejemplos/metodologia/s3-sync/* ejemplos/skills-plugins/.cursor/skills/day/SKILL.md 2>/dev/null \
  | grep -Eic 'document-parser|SST-[0-9]+|<real-bucket-name>|<real-account-id>'
```

⚠️ **A leak scan piped into `head` always exits 0**, so `... | head || echo clean` can never fire.
That mistake was made twice while preparing this update. Assert on a **count**, and prove the
scanner works by running it against a file you know is dirty.

---

## What NOT to do

- **Do not blanket-copy the Claude guides.** This pack is ahead in places and the 09-08 update is
  already here. The nine items above are the whole job.
- **Do not vendor the `gsd-*` skills.** Third-party plugin; copying freezes a version and cuts it
  off from updates. The Claude pack says so explicitly — keep that line.
- **Do not ship `config.env`**, ever, in any form.
- **Do not commit on the human's behalf.** The Claude-side changes are staged in a working tree for
  exactly this reason.
