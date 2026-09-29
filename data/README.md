# data/

Accepted captures, versioned per game patch. We host the current version ourselves:
full exports (towers, upgrades, bloons, rounds, maps, costs) as we actually use them.
Upstream repos lag and go stale, so they are cross-checks, not the source of truth.

Layout per patch:

```
data/<game-version>-build-<steam-build>/
  atlas-maps/                  accepted map captures (from the mod)
  game-data/                   matching Mod Helper Export Game Data output
  gameplay-towers/             derived ordinary Tower gameplay JSON
  manifest.json                exporter/mod-helper versions, method, SHA-256s,
                               accepted-by, known partials
```

Workflow: install the mod (`../mod/README.md`), run the base export, run the atlas
export per map, copy the files here, record them in PROVENANCE.md, then publish.

Generate gameplay Tower files with `python3 scripts/export-gameplay-towers.py` from the repository root.
The converter reads the latest committed capture and processes every family; `--tower DartMonkey` selects one family for inspection.
See [the format and workflow](../docs/gameplay-towers.md).
