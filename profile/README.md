# BTD6 Profile

Atlas owns the BTD6 Profile and checker. Its settings describe BTD6's separate `game-data/` records, and its schemas define reusable shapes. It contains no Tower instances or capture inventory. Raw field names, nesting, embedded abilities and `$type` remain unchanged.

## Structure

```text
profile/
  manifest.json
  collections.json
  references.json
  mechanics.json
  rules.json
  numerical-units.json
  scoring.json
  classifications.json
  schemas/
    profile/
      manifest.schema.json
      mechanics.schema.json
      mechanic-proposal.schema.json
      scoring.schema.json
      selectors.schema.json
      ...
    game-data/
      tower.schema.json
      attack.schema.json
      ability.schema.json
      upgrade.schema.json
      ...
```

| Document | Responsibility |
|---|---|
| `manifest.json` | Identity, revision, checker interface, local document references and capture metadata bindings. |
| `collections.json` | Logical collections, source paths, identities, layout, enabled features, required roles and rule scopes. |
| `references.json` | Typed outgoing links, aliases and documented external symbols. |
| `mechanics.json` | Model identity, schemas, source field bindings and required fields. |
| `rules.json` | Named source selectors, cross-record operations and progression limits. |
| `numerical-units.json` | Native units and their field bindings. |
| `scoring.json` | Scoring collection, family field and category weights. |
| `classifications.json` | Record categories and the validation coverage required for each. |
| [tower.schema.json](schemas/game-data/tower.schema.json) | The shared Tower shape, using smaller schemas for nested records. |
| [mechanics.schema.json](schemas/profile/mechanics.schema.json) | The mechanics catalog format. |
| [mechanic-proposal.schema.json](schemas/profile/mechanic-proposal.schema.json) | Separate proposals. A proposal does not enable a mechanic. |

Schemas own reusable field shapes and local numerical constraints. BTD6 source names, requirements and limits stay in the configuration documents. All required schemas resolve inside the Profile directory without network access.

`mechanics.json` maps shared schema fields to source fields. For example, Tower `placementPrice` reads raw `cost`, and `familyId` reads `baseId`. Its `requiredFields` declares which shared fields this game requires. The checker builds a temporary schema view, validates it and leaves the raw record unchanged. Another game can use the same schemas with different bindings.

`rules.json` defines named selectors over source fields and contained model classes. Collections and classifications refer to those names. BTD6 categories and behavior markers therefore remain settings rather than separate game-specific schemas.

## Layout and required data

The bundled Profile describes the existing export:

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
  resources.json
  paragonDegreeData.json
```

Each Tower family has one directory and each state has one JSON file. Collection settings define depth, family folder and filename bindings. `Towers/<baseId>/<name>.json` follows those settings. Upgrade identities remain independent of sanitized filenames. Abilities remain embedded in the raw records; another Profile can declare an ability collection and references to it.

`typed: true` requires the configured model discriminator on each collection record. Localization and resource tables use untyped `@keys` identities; their keys remain ordinary data even if one is named `kind`. `excludedKeys` omits configured metadata keys from identity lookup. BTD6 uses it for `$type`.

Logical names and source paths are separate. `enemies` uses path `Bloons` and raw `BloonModel` bindings. `localization` uses path `textTable.json`. Change the configured path to rename or relocate a role without changing Go.

`requireWhen` is an OR list of consumers. A condition selects a present collection, optionally filtered by a named selector, or a nonempty field on configured model types. A required role must contain at least one JSON record. Its records receive their declared schema checks.

The bundled settings require localization when Towers or upgrades exist, resources when typed asset references are used, and advanced progression data when paragons exist. They require the resource table, without claiming that every asset identifier resolves in it. Some raw identifiers refer to runtime sprite libraries.

`enabled: false` skips a collection's records and requirements. Rogue and Frontier data are outside this Profile's primary-game scope. Their absence or malformed contents do not fail validation, and skipped files are counted separately.

Empty unused collections are valid. Once a progression family exists, it must have a root, all legal states, every legal outgoing transition and all declared references. Ordinary Towers use 64 derived purchase states. Heroes use levels 1 through 20. Power Pro Towers use ten states with one purchased path up to tier three.

No capture filenames, expected capture counts or game-data content hashes are stored for completeness. Deleting a required state, dependency or role fails. Deleting an optional unreferenced record or an entire family can pass if no applicable requirement needs it. Round continuity and category folder meanings remain outside coverage.

`unmatchedFiles: "error"` rejects JSON files outside declared collections. `"report"` permits them and records missing schema coverage.

## Tower categories

The Profile classifies every Tower record and reports its actual validation coverage. Missing or ambiguous categories fail validation. The accepted capture contains 2,167 Tower records:

| Category | Records | Coverage |
|---|---:|---|
| Ordinary builds | 1,664 | Schemas, references and purchase progression. |
| Hero levels | 360 | Schemas, references and linear progression. |
| Power Pro builds | 50 | Schemas, references and purchase progression. |
| Paragons | 13 | Schemas and references. |
| Subtowers | 56 | Schemas and references. |
| Transformed forms | 20 | Schemas and references. |
| Family variants | 3 | Schemas and references, outside their family's purchase graph. |
| Frontier record | 1 | Shared schemas and references; feature behavior is outside scope. |

These counts describe the capture rather than imposing an inventory. Structural checks for a subtower or form do not establish its ownership, lifetime or transformation behavior.

## Validate and score

Build the binary from the existing command package:

```sh
go build -o bin/atlas-validator ./cmd/atlas-validate
bin/atlas-validator --data data/56.3-build-24829026/game-data --profile profile
```

The existing `atlas-validate` binary name and `--data` invocation still work. Whole-dataset validation also accepts `--game-data`.

Score one Tower with all three required flags:

```sh
bin/atlas-validator score-tower \
  --profile profile \
  --game-data data/56.3-build-24829026/game-data \
  --tower data/56.3-build-24829026/game-data/Towers/DartMonkey/DartMonkey.json
```

The target can be a full path or a path relative to game-data. Scoring checks its whole family, follows outgoing dependencies and includes applicable required roles. Referenced Tower dependencies include their families. It does not follow unrelated incoming consumers. Unrelated missing or malformed records do not affect diagnostics, counts or score. Capture metadata is omitted from Tower scoring.

The score measures contract compliance. It does not measure balance, character fidelity or behavior simulation. `scoring.json` supplies positive weights for schema, layout, references, rules, units and mechanics. They initially have equal weights.

Schema, reference and unit checks award credit per checked file. Layout also checks required role presence. Rules award credit per applicable rule result. Mechanics award credit per model instance with a schema binding. Each category reports its checked and passed counts. Categories with no applicable checks are excluded from the weighted average. No detected models means incomplete mechanic coverage.

A Tower whose applicable checks and model-schema coverage all pass receives 100. Failed checks receive partial credit. Unbound model types prevent 100, including after rounding. `valid: true` means the declared validation checks passed; `score.complete: false` can still identify incomplete schema coverage. Unknown model types can instead be configured as validation errors.

The Dart family scores 84.73/100 with the bundled weights. Its model-schema category covers 531 of 6,346 detected instances, about 8.37%, with 62 unbound types. Those types include assets and other supporting objects as well as gameplay behaviors. The total score combines that coverage with the other check categories; it is not a percentage of simulated or understood gameplay.

Add `--format text` for terminal output or `--relations` for resolved references and backlinks in JSON. Backlinks describe only the checked graph in Tower scoring. Exit codes are 0 for passed validation, 1 for failed validation and 2 for invalid arguments, selection or Profile. A partial score caused only by coverage gaps retains exit code 0.

## Generalization and provenance

`mechanics.typeIdentity` selects a discriminator field and encoding. BTD6 uses `$type` and `dotnet`, which extracts the short class name. Another game can use `kind` and `literal`. Validation, dependency discovery, purchase aliases and unit bindings all use the same setting.

Capture metadata uses a configured `base`, `path` and label-to-source-field map. `base` is `gameData` or its `parent`. BTD6 binds generic `buildId` to `steamBuildId`. Metadata is informational and does not establish completeness.

Reports record Profile revision and dependency digest, actual checker version and executable identity, errors, counts and coverage. Numerical checks do not convert or rewrite data. Known schemas still permit additional raw fields. A binding establishes the declared structural coverage, not complete runtime interpretation.

Reusable operations live in `internal/atlasvalidate/`. The command entry point only delegates to the package. Unknown operations and malformed Profile documents fail before checking game-data.

The current Profile and checker interface use format 4. Format 3 Profiles must migrate their schema bindings before using this checker.

See [the implementation record](../docs/profile-implementation.md) for verification and the existing Boomerang duplicate found in the accepted capture.
