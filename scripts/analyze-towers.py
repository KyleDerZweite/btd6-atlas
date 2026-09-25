#!/usr/bin/env python3
"""Static tower pattern analysis.

Reads game-data/Towers (per crosspath entity files) and game-data/Upgrades
(per tier costs) for one capture and writes patterns/towers.json.
Factual identifiers only; the markdown write-up stays hand written.

Usage:
    uv run scripts/analyze-towers.py [data/<patch-dir>]

With no argument the newest data/*-build-* directory is used.
Standard library only.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SET_NAMES = {0: "unflagged", 1: "primary", 2: "military", 4: "magic",
             8: "support", 16: "hero", 64: "power"}
HERO_ALIASES = {"CaptainChurchill": "churchill"}


def load(path):
    return json.loads(path.read_text())


def find_patch(explicit=None):
    if explicit:
        return pathlib.Path(explicit)
    cands = sorted((ROOT / "data").glob("*-build-*"))
    if not cands:
        raise SystemExit("no capture found under data/")
    return cands[-1]


def upg_costs(upgrades_dir):
    """Map upgrade display name -> {cost, tier, path, xpCost}."""
    table = {}
    for path in upgrades_dir.glob("*.json"):
        try:
            datum = load(path)
        except Exception:
            continue
        if isinstance(datum, dict) and "cost" in datum:
            table[datum.get("name", path.stem)] = {
                "cost": datum.get("cost"),
                "tier": datum.get("tier"),
                "path": datum.get("path"),
                "xpCost": datum.get("xpCost"),
            }
    return table


def attack_summary(model):
    """Best effort per model attack readout; nulls where not extractable."""
    out = {"attacks": 0, "rate": None, "damage": None, "pierce": None,
           "projectiles": None}
    try:
        attacks = [b for b in model.get("behaviors", [])
                   if str(b.get("$type", "")).endswith(".AttackModel, Assembly-CSharp")]
    except Exception:
        return out
    out["attacks"] = len(attacks)
    if not attacks:
        return out
    weapons = attacks[0].get("weapons", []) or []
    if not weapons:
        return out
    weapon = weapons[0]
    out["rate"] = weapon.get("rate")
    emission = weapon.get("emission") or {}
    out["projectiles"] = emission.get("count", emission.get("Count"))
    proj = weapon.get("projectile") or {}
    out["pierce"] = proj.get("pierce")
    for behavior in proj.get("behaviors", []) or []:
        if str(behavior.get("$type", "")).endswith("DamageModel, Assembly-CSharp"):
            out["damage"] = behavior.get("damage", behavior.get("Damage"))
            break
    return out


def hero_level_costs(hero_id, models, costs):
    """Level 2..20 entries. New upgrades per level come from the
    appliedUpgrades diff against the previous level; xp costs are summed
    from the upgrade table. Filename matching is the fallback."""
    out = []
    prior = set((models.get("") or {}).get("appliedUpgrades", []) or [])
    for level in range(2, 21):
        model = models.get(str(level), {})
        current = set(model.get("appliedUpgrades", []) or [])
        new = sorted(current - prior)
        prior = current
        xp = sum((costs.get(name) or {}).get("xpCost") or 0 for name in new)
        cash = sum((costs.get(name) or {}).get("cost") or 0 for name in new)
        if not new:
            match = HERO_ALIASES.get(hero_id, hero_id).lower()
            rows = [v for n, v in costs.items()
                    if match in n.lower() and v.get("tier") == level - 1]
            xp = sum((v.get("xpCost") or 0) for v in rows)
            cash = sum((v.get("cost") or 0) for v in rows)
        out.append({"level": level, "upgrades": new, "xpCost": xp, "cost": cash})
    return out


def classify(directory, files, models):
    """Kind of entity based on flags and file layout."""
    base = models.get("")
    flags = base or {}
    stems = {p.stem for p in files}
    if flags.get("isParagon"):
        return "paragon"
    if flags.get("towerSet") == 64 or flags.get("isPowerTower"):
        return "power"
    if flags.get("isBeastHandlerPet") or flags.get("IsBeastHandlerPet"):
        return "pet"
    if flags.get("isSubTower") or flags.get("IsSubEntity"):
        return "sub"
    if flags.get("towerSet") == 16 and any(re.fullmatch(r".* \d+", s) for s in stems):
        return "hero"
    paths = base.get("upgrades", []) if base else []
    if isinstance(paths, list) and len(paths) == 3:
        return "standard"
    if flags.get("towerSet") == 16:
        return "hero-part"
    return "other"


def main():
    patch_dir = find_patch(sys.argv[1] if len(sys.argv) > 1 else None)
    towers_dir = patch_dir / "game-data" / "Towers"
    upgrades_dir = patch_dir / "game-data" / "Upgrades"
    try:
        manifest = json.loads((patch_dir / "manifest.json").read_text())
        patch = manifest.get("gameVersion", patch_dir.name)
    except Exception:
        patch = patch_dir.name
    out_path = ROOT / "patterns" / "towers.json"

    costs = upg_costs(upgrades_dir)
    entities = []
    for directory in sorted(towers_dir.iterdir(), key=lambda p: p.name):
        if not directory.is_dir():
            continue
        files = list(directory.glob("*.json"))
        models = {}
        for path in files:
            try:
                datum = load(path)
            except Exception:
                continue
            stem = path.stem
            if stem == directory.name:
                key = ""
            elif "-" in stem and re.fullmatch(r"[0-9]{3}|Paragon", stem.rsplit("-", 1)[-1]):
                key = stem.rsplit("-", 1)[-1]
            elif re.fullmatch(r".* \d+", stem):
                key = stem.rsplit(" ", 1)[-1]
            else:
                key = stem
            models[key] = datum
        if "" not in models:
            # Versioned variants (TowerV2/V3) or misnamed singles: use the
            # shortest same-prefix file, else the single file, as the base.
            cands = sorted((k for k in models if k.startswith(directory.name)),
                           key=len)
            if not cands and len(models) == 1:
                cands = list(models)
            if cands:
                models[""] = models[cands[0]]
        kind = classify(directory, files, models)
        base = models.get("") or {}
        base_inferred = False
        if not base and kind == "other":
            # Crosspaths but no usable base file; use the lowest tier file
            # (crosspath files repeat base cost, range and footprint).
            lows = sorted((k for k in models if re.fullmatch(r"[0-9]{3}", k)),
                          key=lambda k: sum(int(c) for c in k))
            if lows:
                base = models.get(lows[0], {})
                base_inferred = True
                paths = base.get("upgrades", [])
                if isinstance(paths, list) and len(paths) == 3:
                    kind = "standard"
        foot = base.get("footprint") or {}
        entry = {
            "id": directory.name,
            "kind": kind,
            "baseInferred": base_inferred,
            "hasParagon": any(str(p.stem).endswith("-Paragon") for p in files),
            "set": SET_NAMES.get(base.get("towerSet"), base.get("towerSet")),
            "files": len(files),
            "cost": base.get("cost"),
            "range": base.get("range"),
            "footprint": foot.get("radius"),
            "tiers": base.get("tiers"),
        }
        if kind == "standard":
            suffixes = sorted(k for k in models if re.fullmatch(r"[0-9]{3}", k))
            entry["crosspaths"] = len(suffixes)
            entry["extraFiles"] = sorted(
                k for k in models
                if k and not re.fullmatch(r"[0-9]{3}", k) and k != "Paragon")
            entry["paths"] = []
            for index in range(3):
                chain = []
                for tier in range(1, 6):
                    code = ["0", "0", "0"]
                    code[index] = str(tier)
                    name = "".join(code)
                    model = models.get(name)
                    if model is None:
                        break
                    prior = set()
                    if tier > 1:
                        prev = models.get("".join(
                            [str(tier - 1) if i == index else "0" for i in range(3)]), {})
                        prior = set(prev.get("appliedUpgrades", []) or [])
                    new = [u for u in (model.get("appliedUpgrades", []) or [])
                           if u not in prior]
                    upg = new[-1] if new else None
                    info = costs.get(upg, {}) if upg else {}
                    chain.append({"tier": tier, "upgrade": upg,
                                  "cost": info.get("cost"),
                                  "xpCost": info.get("xpCost")})
                entry["paths"].append({"path": index + 1, "maxTier": len(chain),
                                       "tiers": chain})
            entry["tier3plusCombos"] = len(
                [k for k in suffixes if any(int(ch) >= 3 for ch in k)])
            entry["ruleViolations"] = [
                k for k in suffixes
                if sum(1 for ch in k if int(ch) >= 3) > 1
                or any(int(ch) > 2 for i, ch in enumerate(k)
                       for j, ch2 in enumerate(k) if i != j and int(ch2) >= 5)]
            entry["attackBase"] = attack_summary(base)
            entry["attackTier5"] = {
                k: attack_summary(models[k]) for k in suffixes
                if "5" in k and sum(int(ch) for ch in k) >= 5}
        elif kind == "hero":
            levels = sorted(int(k) for k in models if re.fullmatch(r"\d+", k or "x"))
            entry["levels"] = [1] + levels
            entry["levelCosts"] = hero_level_costs(directory.name, models, costs)
            entry["attackBase"] = attack_summary(base)
        entities.append(entry)

    by_kind = {}
    for entry in entities:
        by_kind.setdefault(entry["kind"], []).append(entry["id"])

    standards = [e for e in entities if e["kind"] == "standard"]
    tier_costs = {}
    for entry in standards:
        for path in entry["paths"]:
            for tier in path["tiers"]:
                if isinstance(tier.get("cost"), (int, float)):
                    tier_costs.setdefault(
                        (path["path"], tier["tier"]), []).append(tier["cost"])
    cost_bands = {f"path{p}-tier{t}": {"n": len(v), "min": min(v),
                                       "max": max(v),
                                       "median": sorted(v)[len(v) // 2]}
                  for (p, t), v in sorted(tier_costs.items())}

    result = {
        "patch": patch,
        "entities": len(entities),
        "byKind": {k: {"n": len(v), "ids": sorted(v)} for k, v in by_kind.items()},
        "sets": SET_NAMES,
        "standardTowers": standards,
        "heroes": [e for e in entities if e["kind"] == "hero"],
        "paragons": [e for e in entities if e["kind"] == "paragon"],
        "upgradeCostBands": cost_bands,
        "upgradeEntries": len(costs),
    }
    out_path.write_text(json.dumps(result, indent=2))
    print(f"patch={patch} entities={len(entities)} kinds=" +
          ", ".join(f"{k}:{len(v)}" for k, v in sorted(by_kind.items())))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
