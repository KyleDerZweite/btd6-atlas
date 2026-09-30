#!/usr/bin/env python3
"""Build the static site payload (manual action).

Copies the current towers.json/maps.json into site/data/ and rebuilds
site/index.json: one lean entry per tower, hero, upgrade and map, each
linking to its raw capture file on GitHub. Run by hand after a new
capture, review the diff, commit, push. Pages serves site/ as is.

Usage:
    uv run scripts/build-site.py [data/<patch-dir>]

Standard library only.
"""
import json
import pathlib
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = "https://github.com/KyleDerZweite/btd6-atlas"
BRANCH = "main"


def find_patch(explicit=None):
    if explicit:
        return pathlib.Path(explicit)
    cands = sorted((ROOT / "data").glob("*-build-*"))
    if not cands:
        raise SystemExit("no capture found under data/")
    return cands[-1]


def blob(path):
    rel = path.relative_to(ROOT).as_posix()
    return f"{REPO}/blob/{BRANCH}/{urllib.parse.quote(rel)}"


def tree(path):
    rel = path.relative_to(ROOT).as_posix()
    return f"{REPO}/tree/{BRANCH}/{urllib.parse.quote(rel)}"


def main():
    patch_dir = find_patch(sys.argv[1] if len(sys.argv) > 1 else None)
    site_data = ROOT / "site" / "data"
    site_data.mkdir(parents=True, exist_ok=True)

    towers = json.loads((patch_dir / "towers.json").read_text())
    maps = json.loads((patch_dir / "maps.json").read_text())
    (site_data / "towers.json").write_text((patch_dir / "towers.json").read_text())
    (site_data / "maps.json").write_text((patch_dir / "maps.json").read_text())

    index = []
    towers_dir = patch_dir / "game-data" / "Towers"
    for entry in towers.get("standardTowers", []):
        index.append({"type": "tower", "id": entry["id"],
                      "facet": entry.get("set"),
                      "url": tree(towers_dir / entry["id"])})
    for entry in towers.get("heroes", []):
        index.append({"type": "hero", "id": entry["id"], "facet": "hero",
                      "url": tree(towers_dir / entry["id"])})

    upgrades_dir = patch_dir / "game-data" / "Upgrades"
    for path in sorted(upgrades_dir.glob("*.json")):
        try:
            datum = json.loads(path.read_text())
        except Exception:
            continue
        if not isinstance(datum, dict) or "cost" not in datum:
            continue
        tier = datum.get("tier")
        index.append({"type": "upgrade", "id": datum.get("name", path.stem),
                      "facet": f"tier {tier + 1}" if isinstance(tier, int) else None,
                      "url": blob(path)})

    atlas_dir = patch_dir / "atlas-maps"
    by_id = {e.get("mapId"): e for e in maps.get("entries", [])}
    for path in sorted(atlas_dir.glob("atlas-*.json")):
        try:
            map_id = json.loads(path.read_text()).get("mapId")
        except Exception:
            continue
        facet = (by_id.get(map_id) or {}).get("difficulty")
        index.append({"type": "map", "id": map_id, "facet": facet,
                      "url": blob(path)})

    (ROOT / "site" / "index.json").write_text(json.dumps(index))
    kinds = {}
    for entry in index:
        kinds[entry["type"]] = kinds.get(entry["type"], 0) + 1
    print(f"patch={patch_dir.name} index entries={len(index)} {kinds}")
    for name in ("towers.json", "maps.json", "index.json"):
        path = site_data / name if name != "index.json" else ROOT / "site" / name
        print(f"  {path.relative_to(ROOT)}: {path.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
