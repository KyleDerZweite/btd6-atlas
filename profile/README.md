# Game-data Profile

The Profile defines the schemas, references, mechanics and rules that `atlas-validate` applies to separate `game-data/` records.
Atlas owns both the Profile and its checker. They work without another project or a game runtime.
Keep raw field names, nesting and `$type`. Tower instances, capture versions and source hashes belong with the capture.

## Files

```text
profile/
  manifest.json
  collections.json
  references.json
  mechanics.json
  rules.json
  numerical-units.json
  schemas/
    profile/
      manifest.schema.json
      mechanics.schema.json
      mechanic-proposal.schema.json
      ...
    game-data/
      tower.schema.json
      attack.schema.json
      ...
    scopes/
      ordinary-tower-root.schema.json
      ordinary-tower-member.schema.json
```

| File | Responsibility |
|---|---|
| `manifest.json` | Profile identity, revision, format version and local document references. |
| `collections.json` | Record locations, identity selectors, validation scopes and required files. |
| `references.json` | Typed links between collections, aliases and documented external symbols. |
| `mechanics.json` | Model classes, their schemas and the policy for unknown model types. |
| `rules.json` | Cross-record operations, their field bindings and progression limits. |
| `numerical-units.json` | Numerical units and bindings to raw fields. |
| [tower.schema.json](schemas/game-data/tower.schema.json) | Raw Tower records, including nested behavior slots and purchase links. |
| [mechanics.schema.json](schemas/profile/mechanics.schema.json) | The format of the mechanics catalog. |
| [mechanic-proposal.schema.json](schemas/profile/mechanic-proposal.schema.json) | Separate proposals for extending the catalog. A proposal does not enable a mechanic. |
| [ordinary-tower-root.schema.json](schemas/scopes/ordinary-tower-root.schema.json) | Select the starting record for each ordinary purchase graph. |
| [ordinary-tower-member.schema.json](schemas/scopes/ordinary-tower-member.schema.json) | Select candidate families that must have a starting record. |
| Other schemas in `schemas/` | Smaller schemas for raw models and Profile documents, grouped by responsibility. |

Schemas own field shapes and local numerical bounds. The mechanics catalog selects schemas by model class.
Rules own relationships between records. The same constraint should have one authoritative definition.
Schema references resolve inside the Profile directory. No network lookup or capture file is required to load the Profile.

## Game-data layout

The data directory contains records separately from the Profile:

```text
game-data/
  Towers/
    DartMonkey/
      DartMonkey.json
      DartMonkey-100.json
      ...
  Bloons/
    Red/
      Red.json
      ...
  Upgrades/
    Sharp Shots.json
    ...
  textTable.json
  paragonDegreeData.json
  rogueData.json
  frontierData.json
  ...
```

These names illustrate a compatible capture. The Profile declares the layout pattern without listing every expected file.
Each collection can declare `layout.depth`: zero for a singleton file, one for a flat collection and two for files inside family folders.
Optional `parentField` and `stemField` bindings compare the containing folder and JSON filename stem with recorded field values.
Towers and Bloons bind their family folders to `baseId` and filenames to `name`. Each file contains one root record, and record identities must be unique.
Upgrades require a flat directory but keep their `name` identity independent of filenames, which can contain sanitized names.
The Profile declares layouts for all 22 primary collections, plus three shared family indexes.
Other filename bindings use recorded names or IDs when the capture preserves them; Skins also binds its family folder to `baseTowerName`.
BloonOverlays has only a depth constraint because its filenames differ from recorded names.
Rounds requires two levels, but the checker does not interpret numeric round filenames or require consecutive rounds.
Category and difficulty folder meanings are also outside these layout checks.
`collections.json` sets `unmatchedFiles: "error"`, so files outside declared collections fail with `unmatched_file`.
This also catches a Tower moved outside `Towers/`. Other Profiles can choose `"report"`, the default when omitted, to permit and count unclassified files.
The same generic checks support a different game's declared layout.

## Run the checker

Build from the repository root with Go 1.23 or newer:

```sh
CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o bin/atlas-validate ./cmd/atlas-validate
bin/atlas-validate --data data/56.3-build-24829026/game-data --profile profile
```

Both arguments accept absolute paths. The binary reads the Profile at runtime and does not modify either directory.
Generated binaries stay in the ignored `bin/` directory. The command is a small CLI; reusable validation code lives in `internal/atlasvalidate/`.

JSON output separates `integrityValid` and `rulesValid`; `valid` requires both to pass.
It also includes file and reference counts, diagnostics, Profile identity, checker identity and coverage.
Profile identity includes its revision and a content digest. Checker identity includes its version and executable hash, with VCS information when available.
An optional sibling capture `manifest.json` supplies game, build and exporter metadata, plus its own digest.
These fields record the source without constraining compatible captures or verifying every capture file hash.

Each diagnostic contains `file`, `pointer`, `code` and `message`. Pointers use JSON Pointer syntax.
Use `--format text` for terminal diagnostics:

```text
Towers/DartMonkey/DartMonkey.json#/upgrades/0/tower: missing_reference: Towers record "DartMonkey-100" does not exist
```

Exit codes are 0 for valid data, 1 for invalid data, and 2 for an invalid invocation or Profile.
An unknown rule operation fails Profile loading before game-data validation.

Add `--relations` to include resolved references and file backlinks in JSON output:

```sh
bin/atlas-validate --data /path/to/game-data --profile /path/to/profile --relations > relations.json
```

Relations retain the source pointer and value, target collection, canonical identity and target files.
Family targets can contain several files. External symbols have `external: true` and no target files.
Unresolved references appear in diagnostics and are absent from the resolved graph.

## What validation covers

Every JSON file receives syntax and root-object checks. Duplicate JSON keys and duplicate record identities fail.
Declared layouts reject incorrect nesting, family folders and state filenames as integrity errors.
Declared collections and known model classes receive schema checks, including nested records.
The checker indexes identities and gathers typed references while scanning files, then resolves links after all files are indexed.
Forward references and cycles are allowed.

The bundled `purchaseProgression` rule starts from records selected by `ordinary-tower-root.schema.json`.
These have `IsBaseTower: true`, `isSubTower: false` and an ordinary `towerSet`. It follows `upgrades[].tower` within each family.
The member schema selects ordinary categories with `isSubTower: false` and `isParagon: false`.
Every candidate family must have a root when completeness is required. A scope with no roots also fails.
The Tower schema requires boolean selection flags, so malformed flags cannot silently exclude a record from these checks.
Paragons, heroes and separate temporary forms receive applicable schemas and reference checks but remain outside this progression scope.
Tier tuples alone cannot identify ordinary permanent builds because transformed Alchemist records reuse those tuples.
Alchemist's transformed records share its candidate family without becoming required purchase-graph members.

The rule checks legal tier combinations, unique permanent builds, same-family purchase targets and increments of exactly one tier on one path.
Its limits live in `rules.json`: three paths, at most tier five, at most two purchased paths and at most one path above tier two.
These limits derive 64 legal builds. Complete-family checking requires every derived build to be reachable.
It also requires every legal outgoing purchase transition and rejects duplicate transitions.
The Profile contains no copied list of Tower states or prices.

Reports identify executed rules, root and record counts, checked transitions, expected state counts and records outside their scope.
They also count model types without a catalog schema. The bundled `unknownModels: "report"` policy permits those models and reports the gap.
Set the policy to `"error"` to require catalog coverage for encountered model types.
A catalog schema checks recorded structure. It does not prove simulation behavior, balance or compatibility with a consuming game.

Additional raw fields remain permitted. Support and economy Towers need no damaging attack.
All 10,055 files in the accepted capture now belong to a collection with a layout and a schema.
The singleton `paragonDegreeData.json`, `rogueData.json` and `frontierData.json` use only the shared basic model schema.
File coverage therefore includes basic structure checks as well as the deeper schemas for core models.
Upgrade metadata agreement is separate from purchase-graph validation. Skywarden's captured upgrade tier metadata remains outside the progression check.
Detailed Atlas map geometry is also outside these schemas.

The accepted BTD6 56.3 capture passes integrity checks but fails the new progression rule on one repeated purchase.
`Towers/BoomerangMonkey/BoomerangMonkey-012.json` repeats its purchase to `BoomerangMonkey-013` at `upgrades[2]`.
The checker reports the second entry as `duplicate-purchase` at `/upgrades/2/tower`.
This is a finding in the recorded data; the original capture remains unchanged.
See [the implementation evidence](../docs/profile-implementation.md) for the complete run and follow-up checks.

## Reading the raw records

Tower `name` identifies a recorded state; `baseId` identifies its Tower family, and `tiers` describes its build.
Resolve upgrade identifiers using `UpgradeModel.name`, never a guessed filename.
Repeated or empty embedded model names are valid and do not constitute globally unique record identifiers.
Model dispatch uses the `$type` class name, ignoring namespace and assembly suffix. Generic dictionaries remain containers.

`TowerModel.cost` is the base placement cost. Ordinary baseline investment adds the prices of `appliedUpgrades` from `UpgradeModel.cost`.
`UpgradeModel.xpCost` is unlock XP; captured `-1` values remain valid. Difficulty modifiers and Knowledge are separate conditions.

Tower names and descriptions use `baseId` and `baseId` plus ` Description` in `textTable.json`.
Ordinary upgrade names use `LocsKey`; their descriptions append ` Description`.
Hero progression uses different text conventions. Localization prose can disagree with captured behavior values.

`WeaponModel.rate`, `AbilityModel.cooldown` and `MonkeyFanClubModel.lifespan` use seconds.
`TravelStraitModel.speed` uses game units per second, Tower range uses game units, and projectile pierce is a budget.
Unit bindings require a bound field to be numeric when present. They do not convert or rewrite values.
Zero derived frame caches can be uninitialized. Preserve them, but do not substitute them for canonical durations.

The `towerSet` flags are primary `1`, military `2`, magic `4`, support `8`, hero `16`, paragon `32` and power `64`.
Immunity flags are lead `1`, black `2`, white `4`, purple `8`, frozen `16`, immune `32` and glass `64`.
These meanings describe the raw flags, not a new damage model.

Assets and display references point to game resources. They are retained without requiring corresponding JSON files.
Local mutation identifiers also differ from exported record references.
The reference catalog retains explicit allowances for five modifier names without exported Knowledge records and the unexported `BossRush` mode.
Their reasons record the observed capture omission. An exported target takes precedence over an allowance; other unresolved values fail.
`ProtecttheYacht` resolves through an explicit alias to `ProtectTheYacht`.

## Change the contract

Edit a schema for field requirements, `references.json` for record links, or `rules.json` for cross-record constraints.
Add mechanic bindings only with a reviewed schema. Keep proposals and their evidence outside gameplay records.
A proposal contains a `mechanic` entry and a `reason`; its entry uses the catalog's schema. Proposals are not loaded by game-data validation.
New executable rule operations need a Go implementation and tests; changing existing rule limits does not.

Collections support recorded fields plus `@keys`, `@parent`, `@stem` and `@path` identity selectors.
Collection and required-file paths normalize locally; a `.` collection includes root and nested records.
The same files can supply separate state and family indexes. Renaming preserves a field-based identity, but the new path must also satisfy any declared layout.
The Profile requires `textTable.json`; other unreferenced records can be removed unless a declared completeness rule requires them.

Reuse the Profile across captures while their format remains compatible. Change its revision when its requirements change.
See [the design](../docs/game-profile.md), [implementation evidence](../docs/profile-implementation.md) and [domain terms](../CONTEXT.md).
