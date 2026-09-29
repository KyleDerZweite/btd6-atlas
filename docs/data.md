# Indexed data storage

`../data/` holds accepted captures, versioned per game patch. Policy: we host the
current version ourselves: full exports as actually used. Upstream (Mod Helper
data, Cyber Quincy costs) lags behind the live patch, so it is a cross-check,
not the source of truth.

Layout per patch:

- `data/<game-version>-build-<steam-build>/game-data/`: accepted Mod Helper exports.
- `data/<game-version>-build-<steam-build>/atlas-maps/`: accepted Atlas map captures.
- One `manifest.json` per patch: exporter version, capture method, accepted-by, known partials.

Read and validate `game-data/` through [the reusable profile](../profile/README.md).
The validator checks declared schemas and references. Capture versions, counts, and provenance remain in the manifest.
