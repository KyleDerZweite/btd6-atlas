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
| `data/` | Accepted captures per patch (empty until first export). |
| `patterns/` | Our derived analyses (empty until first write-up). |
| `docs/` | Workflow plans for mod, data, patterns. |
| `AGENTS.md` | Contributor rules for agents and humans. |

## Workflow

1. Install the mod (`mod/README.md`).
2. Mod Helper **Export Game Data** → base catalog.
3. Per map: load solo, pause, **Export Atlas Data**. Or arm **Export All Maps**
   at the main menu (press twice to confirm) and let it walk the catalog.
4. Copy outputs into `data/<patch>/`, publish to GitHub.

## Attribution

Built on [BTD Mod Helper](https://github.com/gurrenm3/BTD-Mod-Helper) (GPL-3.0) and
MelonLoader. Cross-checked against [btd6-game-data](https://github.com/Btd6ModHelper/btd6-game-data)
and [Cyber Quincy costs](https://raw.githubusercontent.com/hemisemidemipresent/cyberquincy/master/jsons/costs.json).
Bloons TD 6 and all related game content belong to Ninja Kiwi.
