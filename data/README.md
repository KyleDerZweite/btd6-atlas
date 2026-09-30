# data/

Accepted captures, versioned per game patch. We host the current version ourselves:
full exports (towers, upgrades, bloons, rounds, maps, costs) as we actually use them.
Upstream repos lag and go stale, so they are cross-checks, not the source of truth.

Layout per patch:

```
data/<game-version>-build-<steam-build>/
  atlas-maps/                  accepted map captures (from the mod)
  game-data/                   matching Mod Helper Export Game Data output
  manifest.json                exporter/mod-helper versions, method, SHA-256s,
                               accepted-by, known partials
```

Workflow: install the mod (`../mod/README.md`), run the base export, run the atlas
export per map, copy the files here, record them in PROVENANCE.md, then publish.

Read the raw files through [the game profile](../profile/README.md).
Install the pinned td-profile binary with `python3 scripts/install-validator.py`.
Run `bin/validator --game-data data/56.3-build-24829026/game-data --profile profile` from the repository root.
The validator reports structural and reference errors without rewriting the capture.
It discovers files and identities dynamically; different versions and collection sizes do not require an inventory update.
