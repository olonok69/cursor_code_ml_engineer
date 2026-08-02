"""Enumerate the curated knowledge-graph corpus into manifest.txt (design §2)."""
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]          # data/knowledge-graph/ -> repo root
CHANGES = REPO / "data" / "changes"
MEMORY = Path.home() / ".claude" / "projects" / "-mnt-d-ILS" / "memory"

FALLBACK_EXCLUDE = ("_handover_to_cursor.md", "qa_acceptance_criteria.md")


def is_excluded_path(p: Path) -> bool:
    return "payload" in p.parts


def largest_md(folder: Path) -> Path | None:
    cands = [p for p in folder.glob("*.md")
             if p.name not in FALLBACK_EXCLUDE and not p.name.startswith("_diag_")]
    return max(cands, key=lambda p: p.stat().st_size) if cands else None


def collect() -> list[Path]:
    paths: list[Path] = []
    for folder in sorted(CHANGES.glob("sst-*")):
        if not folder.is_dir():
            continue
        primary = folder / f"{folder.name}.md"
        paths.append(primary if primary.exists() else largest_md(folder))
    for name in ("comment_memo", "doc", "pdf", "table"):
        paths.append(CHANGES / "extractors" / name / "process.md")
    for name in ("STATUS", "PLAYBOOK", "SHARP_EDGES", "FOLLOWUPS", "TICKETS", "CONVENTIONS"):
        paths.append(CHANGES / f"{name}.md")
    paths.append(REPO / "CLAUDE.md")
    paths.append(REPO / "data" / "docs" / "CODE_NAVIGATION.md")
    paths.append(REPO / "data" / "machine-sync" / "RUNBOOK.md")
    paths.append(REPO / "data" / "ils-to-main" / "INSTRUCTIONS.md")
    if MEMORY.exists():
        paths.extend(sorted(MEMORY.glob("*.md")))
    seen, out = set(), []
    for p in paths:
        if p and p.exists() and not is_excluded_path(p) and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def main():
    paths = collect()
    out = REPO / "data" / "knowledge-graph" / "manifest.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(str(p) for p in paths) + "\n")
    assert not [p for p in paths if "payload" in p.parts], "payload leak"
    assert sum(p.name == "STATUS.md" for p in paths) == 1, "expected exactly one STATUS.md"
    print(f"manifest: {len(paths)} files -> {out}")


if __name__ == "__main__":
    main()
