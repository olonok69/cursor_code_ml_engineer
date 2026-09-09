# Upstream methodology update — for the Cursor agent

**Written 2026-09-08.** You are being pointed at this file to bring **this repo**
(`cursor_code_ml_engineer`) level with the Claude Code training repo, and then to adapt the
new material to Cursor rather than transcribe it.

**Upstream:** `github.com/olonok69/claude_code_ml_engineer`, branch
`docs/methodology-update-s3-sync`, head **`c69a7db`** (pushed 2026-09-08; a fast-forward onto
`master` is pending, so read the branch, not `master`).

Relevant upstream commits, oldest first:

| Commit | What it did |
|---|---|
| `987ec88` | Closed eight measured gaps in the technical playbook (TECHNICAL.md 502 → 635 lines) |
| `a0a8833` | Added the premise-versus-implementation lesson |
| `69a44a3` | Added the shared-store operating rules + the measurement lessons (→ 741 lines) |
| `4188209` | Carried those rules into the course guides, both languages |
| `c69a7db` | Replaced an internal ticket identifier in an example |

---

## ⚠️ Read this before you start: most of the work is already done here

**This repo is ahead of the Claude repo in places.** Do not blanket-copy — you will overwrite
better text. The state below was measured on 2026-09-08, not assumed.

### Already correct here — DO NOT TOUCH

| Item | Where | Status |
|---|---|---|
| Per-file source/derived/**authored-inside-derived** classification | `GUIA_TECNICA.md:836` (correction block) | ✅ present |
| Same classification in the talk track | `GUIA_PRESENTACION.md:658–663`, `:777` | ✅ present, and better worded than upstream's was |
| Pairs-move-together (fingerprint the overlay) | `GUIA_TECNICA.md` §16 | ✅ present |
| Cursor adaptation layer | `docs/ai-agents-code-methodology/CURSOR_ADAPTATION.md` | ✅ exists; extend, don't rewrite |

### Actually missing or wrong here — this is your work list

| # | Gap | Where | Evidence it is missing |
|---|---|---|---|
| 1 | The **wrong** "graph never travels" rule survives | `docs/KNOWLEDGE_GRAPH.md:101` | carries `nunca viaja de vuelta` with no caveat |
| 2 | Same | `docs/synchro/machine-sync/LAPTOP_START_HERE.md:121` | carries `it never travels back` with no caveat |
| 3 | Recovery-expires rule | anywhere | 0 hits for `30 días`/`noncurrent`/`caduca` |
| 4 | Append-only shared ledgers | anywhere | 0 hits for `append-only`/`solo-append` |
| 5 | Shared store wins on divergence | anywhere | 0 hits for `divergenc` |
| 6 | The four new playbook lessons | `docs/ai-agents-code-methodology/TECHNICAL.md` | **502 lines vs upstream 741** — this file is at the pre-2026-09-03 state, so `987ec88`, `a0a8833` and `69a44a3` are all absent |
| 7 | **Count-vs-list defect, located** | `docs/ai-agents-code-methodology/TECHNICAL.md:115` | says *"Two rules make the shortcut safe"* over **three** numbered rules. Verified 2026-09-08 by counting. Upstream fixed the identical line in `69a44a3`. (`:185` "Three habits" over 3 bullets is correct — leave it.) |

---

## The changes, with enough substance to adapt rather than copy

### A. The "derived artifact" rule — narrow it, do not reverse it (gaps 1–2)

The claim *"the graph is derived, it never travels, rebuild it wherever the corpus is"* is **false
in one specific way**, and it was measured: inside the generated tree lives a **hand-authored**
file (the curated community names) that nothing regenerates. On a real rebuild **under 1%
survived**; even after fixing the root cause, ~38%.

⚠️ **In the travel/machine-sync context the surrounding model is still correct** — the built graph
genuinely is rebuilt where the corpus is. So add the caveat; do not rewrite the flow. Upstream
made exactly that distinction: full reversal in the guides, narrow caveat in the travel docs.

The rule to state: **"derived" is a property of the FILE, not of the folder.** Classify per file
as *source* / *derived* / *authored-but-inside-derived*, and treat the third as source.

### B. Three behavioural rules for a shared store (gaps 3–5)

Upstream's structural rules (single-writer, pairs move together, read-only mount) were already
there. These three were not, and they are the ones people actually break because nothing stops
them:

1. ⚠️⚠️ **Recovery expires, and users own their own work.** Versioning is universally described
   as "the recovery net", full stop. Half-truth: it will almost always carry a lifecycle rule
   expiring **noncurrent versions after 30 days**. So an overwrite is recoverable *for 30 days,
   and only if somebody notices*. Nobody audits anyone else's files. State it literally in
   onboarding: *pull before you edit, push what you changed, and if something of yours
   disappears, say so within the month or it is gone.*
2. **Shared ledgers are append-only.** Last-writer-wins with no merge means rewriting one
   silently drops someone else's line — no conflict, no error, no prompt. Add rows; never
   restructure another person's. Detection is cheap precisely *because* it is append-only: a line
   present locally and absent from the incoming copy is either a deliberate deletion or a
   clobber, so a pull-time warning has essentially no false positives. That is the **visibility**
   versioning does not give you — versioning makes the loss *recoverable*, not *noticed*.
3. **The shared store wins on divergence.** *"I have it locally"* stops being an argument once
   someone else's version is the published one. Agree it in advance: the instinct runs the other
   way, because your local copy is the one you can see.

Also worth carrying: **per-task folders need no coordination at all.** The corpus is partitioned
by construction — one folder per task, one owner. Reserve ceremony for the genuinely shared files.
If your layout forces two people into one file for routine work, no process will save it.

### C. Four playbook lessons (gap 6)

Upstream added these to `TECHNICAL.md`. They are stack-independent — they transfer to Cursor
unchanged in substance.

1. **A rule that matches nothing looks exactly like a rule that works.** Filters, excludes,
   guards, allow-lists: where correct behaviour is *silence*, success and total failure produce
   identical output. Four such defects were found in one afternoon in a single file — one
   anchored at the wrong end of the path, one naming a directory that no longer existed under
   that name, one never reached. All had passed review, because the pattern *read* correctly.
   None was found by inspection; all four by running in preview mode and **reading what was
   actually matched and rejected**. ▶ *Never trust a filter you have not seen reject something.*
2. **A check must distinguish "no" from "could not ask."** A coordination lock reported *"nobody
   holds it"* whenever its read failed — expired credential, no network, denied permission all
   collapsed into the same reassuring answer. The status command was merely misleading; the
   *claim* command shared that read, so an expired token would have granted the lock while
   somebody else held it — precisely the collision the lock existed to prevent. ▶ *A negative
   result and a failed measurement must not share an output.*
3. **The layer nobody owns: the deployed artifact together with its configuration.** Proving the
   artifact is right does not prove the environment will let it start. Code and configuration
   frequently ship through **different repositories with no ordering between them**, so "merged"
   and "working" are separated by however long the second merge takes — on one occasion, four
   hours of a downed shared environment, with both changes individually correct. Meanwhile the
   post-deploy smoke suite reported green throughout, because it called the public interface and
   never reached the background listener that crashed on a missing queue name. ▶ *Assert on the
   component that can actually fail, not the one that is easiest to poll. Prefer a service that
   degrades loudly when its configuration is absent.*
4. **Widening the scope of a shared store is a security event.** Two rules: **scan before every
   widening and canary the scanner first** — a scan over 1,141 files reported clean, and so did
   the canary with a planted secret, because one filename parsed as a command-line option and
   aborted the batch while suppressed stderr and a zero exit code hid it; repaired, it found 15
   files carrying signed URLs with temporary credentials. And **a clean transfer report is not a
   completeness check** — it only says *"what I was asked to send, I sent"*, never *"what exists
   is there"*. Two directories and thirty documents were missed on one widening (a case-sensitive
   include list, plus roots nobody had added). ▶ *After any scope change, reconcile the local
   inventory against the published one and account for every difference, including the intended
   ones, in writing.*

---

## Adapting to Cursor — where these actually land here

Do **not** copy Claude-Code-specific plumbing. The mapping this repo already uses:

| Upstream concept | This repo's surface |
|---|---|
| `CLAUDE.md` always-on memory | `.cursor/rules/00-methodology-core.mdc`, `00-lean-memory.mdc`, `AGENTS.md` |
| Slash commands / skills | `.cursor/skills/*` |
| Subagents | `.cursor/agents/*.md` |
| Hooks | `.cursor/hooks.json` |
| Permissions / allowlists | `.cursor/permissions.json` |

Two things deserve to become **enforced rules** here rather than prose, because they are exactly
the failure modes an agent walks into:

- **Rule: an instrument must be canaried before its result is believed.** Lessons C1 and C2 are
  the same defect class. A rule file that requires a known-answer run before any "verified" claim
  is cheap and catches all of it.
- **Rule: a machine/session must know its role before it writes to shared state.** This is the
  single-writer rule, and it is agent-specific: without it a contributor session will republish
  the shared index — the one thing it must not do — and report it as work done.

`CURSOR_ADAPTATION.md` §1 ("What transfers unchanged") is the right home for the five stack-
independent rules; extend that list rather than starting a parallel one. `COPILOT_ADAPTATION.md`
is the sibling — keep the two consistent in *shape*.

---

## How to verify you actually did it

Do not trust a diff summary. Upstream's own lesson applies to this task:

```bash
# 1. the wrong rule is gone from THIS repo (expect: only correction blocks match)
grep -rn 'nunca viaja\|never travels' --include='*.md' . | grep -v '\.git/'

# 2. the three behavioural rules now exist (expect: non-zero, all three)
grep -rEic '30 días|noncurrent|caduca|expires'   GUIA_TECNICA.md docs/ai-agents-code-methodology/TECHNICAL.md
grep -rEic 'append-only|solo-append'             GUIA_TECNICA.md docs/ai-agents-code-methodology/TECHNICAL.md
grep -rEic 'divergenc'                           GUIA_TECNICA.md docs/ai-agents-code-methodology/TECHNICAL.md

# 3. ES/EN parity — these must match, in line count and in section structure
diff <(grep -c '' GUIA_TECNICA.md) <(grep -c '' GUIA_TECNICA_EN.md)
diff <(grep '^## \|^### ' GUIA_TECNICA.md | wc -l) <(grep '^## \|^### ' GUIA_TECNICA_EN.md | wc -l)

# 4. count-vs-list defects — the recurring one in this material
grep -niE '(two|three|four|five|six)[ -](rules|layers|habits|checks|things)' \
  docs/ai-agents-code-methodology/TECHNICAL.md GUIA_TECNICA.md
```

⚠️ **Check 4 is not optional, and it already fails here.** Running it on 2026-09-08 found
`TECHNICAL.md:115` announcing *"Two rules make the shortcut safe"* over **three** numbered rules —
the same line upstream fixed in `69a44a3`. This defect class — a sentence announcing *N* items over
a list of *N±1* — has now occurred **five separate times** in this material, twice surviving a
sweep whose entire purpose was to find it. Count every list you touch, and every list adjacent to
one you touch. `:185` ("Three habits", 3 bullets) is correct; do not "fix" it.

⚠️ **And verify composition, not totals.** When upstream fixed the "never travels" rule it first
found five instances, then a sixth in a file missing from the grep list, then three more in files
nobody had thought to check — nine, from an initial confident five. Sweep **every** tracked
markdown file, in both languages, and read the match list.

---

## What NOT to bring over

- **Anything naming a client, a fund, a matter, or an internal ticket ID.** Upstream's pre-publish
  sweep caught one ticket ID in an example command; it was fixed at source in `c69a7db`. Re-run
  that sweep here after you edit.
- **The deck.** Upstream's `build_pptx.py` still carries the old wrong rule at ~line 940 and was
  deliberately left alone, because fixing it forces a deck rebuild and a matching re-point of the
  translation table or the changed line ships untranslated. If this repo's deck has the same
  claim, treat it the same way: flag it, do not rebuild unilaterally.
- **Bucket names, AWS account numbers, SSO URLs, permission-set names.** Upstream's guides are
  written generically for exactly this reason.

---

## One-line summary for the commit

> Bring the methodology level with the Claude training repo at `c69a7db`: narrow the
> derived-artifact rule, add the three shared-store behavioural rules, and add the four
> measurement lessons.
