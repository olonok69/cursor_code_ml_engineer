# `s3-sync` — shared engineering record (scripts)

Language-neutral scripts live once under [`../../metodologia/s3-sync/`](../../metodologia/s3-sync/).
Start from `config.env.example` — **never** commit a real `config.env`.

Deliberate deletions go through `delete.sh` (publisher only), which records a tombstone in the
store so every machine follows; see point 6 of [`../../metodologia/s3-sync/README.md`](../../metodologia/s3-sync/README.md).

Drive them with the Cursor [`day` skill](../../skills-plugins/.cursor/skills/day/SKILL.md).
Full narrative: [`../../../docs/synchro/s3-sync/README.md`](../../../docs/synchro/s3-sync/README.md).
