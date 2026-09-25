# Indexed data storage

`../data/` holds accepted captures, versioned per game patch. Policy: we host the
current version ourselves: full exports as actually used. Upstream (Mod Helper
data, Cyber Quincy costs) lags behind the live patch, so it is a cross-check,
not the source of truth.

Planned layout per patch (simplified snapshot scheme):

- `data/<game-version>/towers/`, `upgrades/`, `maps/`, `rounds/`: accepted exports plus SHA-256 manifest.
- One `manifest.json` per patch: exporter version, capture method, accepted-by, known partials.

Policy (decide before first publish): raw exports stay local until the data policy is settled; what goes public first is derivations in `../patterns/`, never full verbatim exports.
