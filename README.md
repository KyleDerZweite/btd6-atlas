# BTD6 Atlas

Versioned Bloons TD 6 game data, map geometry and analyses for fan research.
Atlas pairs a map exporter with a BTD6 Profile that checks raw records, references
and upgrade progression using [td-profile](https://github.com/mardwerk/td-profile).

Independent fan project. Not affiliated with Ninja Kiwi.

## Explore the data

- [Accepted captures](data/README.md) keep game data, map exports and provenance together by patch.
- [Tower patterns](patterns/towers.md) describe the roster, costs and crosspaths.
- [Map patterns](patterns/maps.md) compare routes, placement geometry and difficulty.
- [Progression patterns](patterns/progression.md) describe purchases and upgrade paths.
- [The BTD6 Profile](profile/README.md) defines validation rules, model contracts and score coverage.

The current capture is BTD6 `56.3`, build `24829026`. The Profile preserves raw
fields, embedded abilities and `$type` names. Tower families have one directory
with one JSON file per state.

## Validate a capture

The Linux amd64 validator ships at `profile/validator` beside the Profile.
Run it from the repository root, without installing Go or Python:

```sh
./profile/validator \
  --profile profile \
  --game-data data/56.3-build-24829026/game-data \
  --format text
```

Score the Dart Monkey family and its required dependencies:

```sh
./profile/validator score-tower \
  --profile profile \
  --game-data data/56.3-build-24829026/game-data \
  --tower Towers/DartMonkey/DartMonkey.json \
  --format text
```

Dart scores **100/100**. This measures compliance with the declared contract;
it does not measure gameplay balance or simulate behavior. Whole-capture
validation currently exits with code 1 for one known duplicate Boomerang
purchase. See the [verification record](docs/profile-project.md) for coverage
and the missing-dependency check.

The bundled executable comes from td-profile release `v1.0.2`, checker `5.0.1`.
For Windows amd64 or macOS arm64, install the matching native executable:

```sh
python3 scripts/install-validator.py
```

The installer verifies the release checksum and shared schemas, then replaces
the bundled executable. Windows uses `profile/validator.exe`; other supported
platforms use `profile/validator`. Validation works offline.

## Capture a new patch

The [exporter setup](mod/README.md) explains the required BTD6 installation,
MelonLoader, BTD Mod Helper and .NET build.

1. Run Mod Helper's **Export Game Data** for the static catalog.
2. Run **Export Atlas Data** in a loaded solo map, or use the confirmed **Export All Maps** workflow.
3. Keep matching outputs under `data/<game-version>-build-<steam-build>/` with their provenance.
4. Validate the capture and review its diagnostics before accepting it.
5. Regenerate and review the [derived analyses](patterns/README.md).

## Project layout and contributions

| Path | Contents |
| --- | --- |
| [mod/](mod/README.md) | C# exporter for loaded map geometry. |
| [data/](data/README.md) | Versioned captures and derived tables. |
| [patterns/](patterns/README.md) | Reviewed observations from captures. |
| [profile/](profile/README.md) | BTD6 settings, source contracts, reusable schemas and the validator binary. |
| [scripts/](scripts/) | Analysis, contract derivation and validator installation. |
| [docs/](docs/) | Workflow plans and verification records. |

Read [AGENTS.md](AGENTS.md) before contributing. Propose Profile, shared schema
and validator changes through a PR to [td-profile](https://github.com/mardwerk/td-profile),
then adopt released changes here. Atlas keeps its BTD6 bindings and source
contracts alongside the capture exporter.

## License and attribution

Code is [MIT licensed](LICENSE). Exported game data and derived tables are
shared for non-commercial fan research under CC BY-NC 4.0, as recorded in
[NOTICE](NOTICE). Bloons TD 6 and all related game content belong to Ninja Kiwi.

The exporter uses [BTD Mod Helper](https://github.com/gurrenm3/BTD-Mod-Helper)
and MelonLoader under their own licenses. Reference checks include
[btd6-game-data](https://github.com/Btd6ModHelper/btd6-game-data) and
[Cyber Quincy costs](https://raw.githubusercontent.com/hemisemidemipresent/cyberquincy/master/jsons/costs.json).
