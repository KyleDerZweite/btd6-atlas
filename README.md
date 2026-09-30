# btd6-atlas

Independent fan project: the map-and-behavior layer Mod Helper's static export doesn't cover, plus indexed game-data storage and derived patterns.

Not affiliated with Ninja Kiwi. Requires a legitimately owned copy of BTD6; nothing here helps piracy.

## Licenses

- Code: MIT (`LICENSE`).
- Exported game data and derived tables: CC BY-NC 4.0 (see `NOTICE`). Non-commercial fan research.
- We host current-version exports ourselves because upstream lags the live patch.

## Layout

| Path | Meaning |
|---|---|
| `mod/` | The installable exporter mod (build + install: `mod/README.md`). |
| `data/` | Accepted captures per patch. |
| `patterns/` | Our derived analyses (empty until first write-up). |
| `profile/` | BTD6 settings, source contracts and reusable schemas for game-data validation. |
| `profile/schemas/` | Reusable schemas grouped into `profile/` and `game-data/`. |
| `cmd/atlas-validate/` | Small CLI for the Profile checker. |
| `internal/atlasvalidate/` | Reusable Go validation package. |
| `docs/` | Workflow plans for mod, data, patterns. |
| `AGENTS.md` | Contributor rules for agents and humans. |

## Workflow

1. Install the mod (`mod/README.md`).
2. Mod Helper **Export Game Data** → base catalog.
3. Per map: load solo, pause, **Export Atlas Data**. Or arm **Export All Maps**
   at the main menu (press twice to confirm) and let it walk the catalog.
4. Copy outputs into `data/<patch>/`, publish to GitHub.

Build the data validator with `go build -o bin/atlas-validator ./cmd/atlas-validate`.
Run `bin/atlas-validator --data data/56.3-build-24829026/game-data --profile profile`.
See [the game profile](profile/README.md) for validation coverage and diagnostics.
Add `--relations` to include resolved references and file backlinks in the JSON result.
The checker applies the Profile to separate raw game-data, including ordinary, Hero and Power Pro progression.
Configuration maps source fields into shared schema shapes for validation while preserving the raw files.
Source contracts check required raw fields and value shapes for all 1,175 captured model types.
The reusable schemas define the contract format; BTD6 field names and type names remain configuration values.
The Profile also defines directory depth and field bindings for family folders and record filenames.
For example, Towers use `Towers/<baseId>/<name>.json`; upgrades retain independent record identifiers and filenames.
Its report records Profile and checker identities, rule coverage, source contract coverage and shared schema coverage.
Each Tower receives a declared category with explicit validation coverage.
Tower scoring checks one family and its outgoing dependencies, with category weights from `profile/scoring.json`.
Use `bin/atlas-validator score-tower --profile profile --game-data <path> --tower <path>`.
Required roles are conditional; empty unused collections are valid. Rogue and Frontier settings are outside scope.
Atlas owns this contract and checker independently of any consuming game or generator.

## Attribution

Built on [BTD Mod Helper](https://github.com/gurrenm3/BTD-Mod-Helper) (GPL-3.0) and
MelonLoader. Cross-checked against [btd6-game-data](https://github.com/Btd6ModHelper/btd6-game-data)
and [Cyber Quincy costs](https://raw.githubusercontent.com/hemisemidemipresent/cyberquincy/master/jsons/costs.json).
Bloons TD 6 and all related game content belong to Ninja Kiwi.
