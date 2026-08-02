"""Copy manifest files into _corpus/ with provenance-preserving flat names."""
from pathlib import Path
import re
import shutil

REPO = Path(__file__).resolve().parents[2]
KG = REPO / "data" / "knowledge-graph"
CORPUS = KG / "_corpus"


def flat_name(p: Path) -> str:
    parts = p.parts
    if "memory" in parts and ".claude" in parts:
        name = f"memory__{p.name}"
    elif "extractors" in parts:
        variant = parts[parts.index("extractors") + 1]
        name = f"extractor__{variant}__{p.name}"
    elif any(part.startswith("sst-") for part in parts):
        ticket = next(part for part in parts if part.startswith("sst-"))
        name = f"{ticket}__{p.name}"
    elif "machine-sync" in parts or "ils-to-main" in parts:
        name = f"ops__{p.name}"
    elif len(parts) >= 2 and parts[-2] == "changes":
        name = f"hub__{p.name}"
    else:
        name = f"orient__{p.name}"
    # graphify sees a flat dir; keep names shell-safe (no whitespace).
    return re.sub(r"\s+", "_", name)


def main():
    lines = [l.strip() for l in (KG / "manifest.txt").read_text().splitlines() if l.strip()]
    if CORPUS.exists():
        shutil.rmtree(CORPUS)
    CORPUS.mkdir(parents=True)
    seen: dict[str, str] = {}
    for line in lines:
        src = Path(line)
        assert "payload" not in src.parts, f"payload leak: {src}"
        name = flat_name(src)
        if name in seen:
            raise SystemExit(f"name collision: {name} <- {src} and {seen[name]}")
        seen[name] = line
        shutil.copy2(src, CORPUS / name)
    print(f"staged {len(seen)} files -> {CORPUS}")


if __name__ == "__main__":
    main()
