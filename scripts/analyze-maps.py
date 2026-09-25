#!/usr/bin/env python3
"""Static map geometry pattern analysis.

Reads atlas-maps (route/area/blocker geometry) plus game-data/Maps (static
difficulty) for one capture and writes patterns/maps.json. Lengths are
game units. The markdown write-up stays hand written.

Usage:
    uv run scripts/analyze-maps.py [data/<patch-dir>]

With no argument the newest data/*-build-* directory is used.
Standard library only.
"""
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def find_patch(explicit=None):
    if explicit:
        return pathlib.Path(explicit)
    cands = sorted((ROOT / "data").glob("*-build-*"))
    if not cands:
        raise SystemExit("no capture found under data/")
    return cands[-1]


def polyline_length(points):
    total = 0.0
    for first, second in zip(points, points[1:]):
        total += math.hypot(second["x"] - first["x"], second["y"] - first["y"])
    return total


def main():
    patch_dir = find_patch(sys.argv[1] if len(sys.argv) > 1 else None)
    atlas_dir = patch_dir / "atlas-maps"
    static_dir = patch_dir / "game-data" / "Maps"
    try:
        manifest = json.loads((patch_dir / "manifest.json").read_text())
        patch = manifest.get("gameVersion", patch_dir.name)
    except Exception:
        patch = patch_dir.name
    out_path = ROOT / "patterns" / "maps.json"

    difficulties = {}
    for path in static_dir.rglob("*.json"):
        try:
            datum = json.loads(path.read_text())
        except Exception:
            continue
        difficulties[path.stem] = {
            "difficulty": path.parent.name,
            "id": datum.get("id"),
        }
    by_id = {v["id"]: v for v in difficulties.values() if v.get("id")}

    entries = []
    for path in sorted(atlas_dir.glob("atlas-*.json")):
        envelope = json.loads(path.read_text())
        game_map = envelope.get("map", {})
        routes = game_map.get("routes", [])
        full = [r for r in routes
                if str(r.get("entranceId", "")).startswith("entrance-")]
        lengths = [polyline_length(r.get("points", [])) for r in routes]
        full_lengths = [polyline_length(r.get("points", [])) for r in full]
        areas = game_map.get("areas", [])
        kinds = {}
        for area in areas:
            kinds[area.get("kind", "other")] = kinds.get(area.get("kind", "other"), 0) + 1
        blockers = game_map.get("blockers", [])
        bounds = game_map.get("bounds", {})
        lower, upper = bounds.get("min", {}), bounds.get("max", {})
        width = (upper.get("x") or 0) - (lower.get("x") or 0)
        height = (upper.get("y") or 0) - (lower.get("y") or 0)
        map_id = envelope.get("mapId")
        static = by_id.get(map_id, {})
        entries.append({
            "mapId": map_id,
            "difficulty": static.get("difficulty", "unknown"),
            "routes": len(routes),
            "fullRoutes": len(full),
            "routeLengths": [round(v, 1) for v in lengths],
            "trackTotal": round(sum(lengths), 1),
            "trackFullTotal": round(sum(full_lengths), 1),
            "trackLongest": round(max(lengths) if lengths else 0, 1),
            "trackFullLongest": round(max(full_lengths) if full_lengths else 0, 1),
            "entrances": len(game_map.get("entrances", [])),
            "exits": len(game_map.get("exits", [])),
            "areas": len(areas),
            "areaKinds": kinds,
            "blockers": len(blockers),
            "hasWater": kinds.get("water", 0) > 0,
            "bounds": {"w": round(width, 1), "h": round(height, 1)},
            "unsupported": envelope.get("unsupported", []),
        })

    groups = {}
    for entry in entries:
        groups.setdefault(entry["difficulty"], []).append(entry)

    def aggregate(items):
        count = len(items)
        avg = lambda values: round(sum(values) / count, 1) if count else 0
        return {
            "n": count,
            "trackTotalAvg": avg([e["trackTotal"] for e in items]),
            "trackTotalMin": round(min((e["trackTotal"] for e in items), default=0), 1),
            "trackTotalMax": round(max((e["trackTotal"] for e in items), default=0), 1),
            "trackLongestAvg": avg([e["trackLongest"] for e in items]),
            "routesAvg": avg([e["routes"] for e in items]),
            "fullRoutesAvg": avg([e["fullRoutes"] for e in items]),
            "multiRoute": sum(1 for e in items if e["fullRoutes"] > 1),
            "trackFullTotalAvg": avg([e["trackFullTotal"] for e in items]),
            "trackFullLongestAvg": avg([e["trackFullLongest"] for e in items]),
            "entrancesAvg": avg([e["entrances"] for e in items]),
            "exitsAvg": avg([e["exits"] for e in items]),
            "areasAvg": avg([e["areas"] for e in items]),
            "blockersAvg": avg([e["blockers"] for e in items]),
            "waterShare": round(sum(1 for e in items if e["hasWater"]) / count, 2) if count else 0,
            "boundsAvg": {
                "w": avg([e["bounds"]["w"] for e in items]),
                "h": avg([e["bounds"]["h"] for e in items]),
            },
        }

    result = {
        "patch": patch,
        "maps": len(entries),
        "units": "game units; lengths are polyline sums over route points",
        "byDifficulty": {name: aggregate(items) for name, items in sorted(groups.items())},
        "entries": sorted(entries, key=lambda e: e["mapId"] or ""),
    }
    out_path.write_text(json.dumps(result, indent=2))
    print(f"patch={patch} maps={len(entries)}")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
