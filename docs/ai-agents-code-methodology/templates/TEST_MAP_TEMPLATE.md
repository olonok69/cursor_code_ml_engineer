# TEST_MAP

Which test file guards which change. An on-demand Tier-2 file — the always-loaded
orientation doc carries a one-line pointer here, never this list.

Group by **component/variant**, because that is the unit you are asked to run: a
change scoped to one component runs that component's block plus the canonical
regression battery, not the whole suite.

## <Component / variant A>

- `tests/<file>.py` — <ticket/change> (<what invariant it locks, in one line>)

## <Component / variant B>

- `tests/<file>.py` — <ticket/change> (<what invariant it locks, in one line>)

## Shared / cross-component

A change here is cross-component by definition — run the full battery, not a block.

- `tests/<file>.py` — <what it locks>

## Canonical regression battery

```bash
<the command that runs the known-good reference set>
```

---

## Maintenance

Add the test file **to its component block** as part of "done" — and put that step in
the done-checklist, or this file will rot. It always rots the same way: the list is
correct on the day it is written and then silently stops tracking reality.

**Two traps, both learned the hard way:**

1. **Moving a stale list does not refresh it.** Extracting this list out of the
   always-loaded doc makes it *look* freshly authored while it inherits every bit of
   the original's staleness.
2. **Do not verify it against itself.** A check that asserts "this file has N
   entries" cannot fail, because N was derived from the same stale source. Verify
   against **the filesystem**:

```bash
# every test file should appear here
for f in $(ls tests/ | grep -oE '<your test file pattern>'); do
  grep -q "$f" <path>/TEST_MAP.md || echo "UNMAPPED $f"; done
```

The real test of this file is not its line count — it is whether someone can ask
"which test guards X?" and get an answer without being told where to look.
