# BTD6 Profile

Atlas owns the BTD6 Profile and checker. Its settings describe BTD6's separate `game-data/` records, and its schemas define reusable shapes. It contains no Tower instances or capture inventory. Raw field names, nesting, embedded abilities and `$type` remain unchanged.

## Structure

```text
profile/
  manifest.json
  collections.json
  references.json
  mechanics.json
  model-contracts.json
  model-contracts/
    models-001.json
    ...
  rules.json
  numerical-units.json
  scoring.json
  classifications.json
  schemas/
    profile/
      manifest.schema.json
      mechanics.schema.json
      model-contracts.schema.json
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
| `mechanics.json` | Model identity, shared schemas, source field bindings and required fields. |
| `model-contracts.json` | Index, requirements and provenance for source structure contracts in `model-contracts/`. |
| `rules.json` | Named source selectors, cross-record operations and progression limits. |
| `numerical-units.json` | Native units and their field bindings. |
| `scoring.json` | Scoring collection, family field and category weights. |
| `classifications.json` | Record categories and the validation coverage required for each. |
| [tower.schema.json](schemas/game-data/tower.schema.json) | The shared Tower shape, using smaller schemas for nested records. |
| [mechanics.schema.json](schemas/profile/mechanics.schema.json) | The mechanics catalog format. |
| [mechanic-proposal.schema.json](schemas/profile/mechanic-proposal.schema.json) | Separate proposals. A proposal does not enable a mechanic. |

Schemas own reusable field shapes, the source contract vocabulary and local numerical constraints. BTD6 source names, requirements and limits stay in the configuration documents. All required schemas resolve inside the Profile directory without network access.

`mechanics.json` maps shared schema fields to source fields. For example, Tower `placementPrice` reads raw `cost`, and `familyId` reads `baseId`. Its `requiredFields` declares which shared fields this game requires. The checker builds a temporary schema view, validates it and leaves the raw record unchanged. Another game can use the same schemas with different bindings.

`rules.json` defines named selectors over source fields and contained model classes. Collections and classifications refer to those names. BTD6 categories and behavior markers therefore remain settings rather than separate game-specific schemas.

## Model structure contracts

Validation checks both the raw structure and the shared schema view. `model-contracts.json` loads ten small contract documents covering the 1,175 exact source types observed in the active capture. BTD6 field names and full .NET type names are values in those documents. The reusable [model-contracts.schema.json](schemas/profile/model-contracts.schema.json) defines their format.

A source contract requires its listed fields, rejects unexpected fields and checks value types, nested objects, arrays and allowed nested model types. Reviewed dictionaries declare the shape of their values instead of listing captured keys. Exact source identities distinguish classes that share a short .NET name. Shared mechanic schemas still apply their canonical field requirements and numerical checks where bindings exist.

These contracts were derived from `56.3-build-24829026`. They describe observed structure without inferring behavior, balance, numerical ranges or gameplay string values. JSON numbers use `number`; whole-number observations do not establish an integer requirement. Fields observed only as null accept only null, and arrays with no observed elements accept only empty arrays. A previously unseen valid variant therefore needs review and a contract revision.

The derivation script audits a capture without modifying it:

```sh
python3 scripts/derive-model-contracts.py audit \
  --profile profile \
  --game-data data/56.3-build-24829026/game-data \
  --map-types-from profile/model-contracts.json
```

Its `generate` command requires an explicit `--output` directory and `--capture-revision`. Derive candidates from a trusted capture, then review their differences. Regenerating contracts from a failing record would change the requirement instead of proving the record valid.

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

Schema, reference and unit checks award credit per checked file. Layout also checks required role presence. Rules award credit per applicable rule result. Mechanics award credit per model instance with a shared schema binding or source structure contract. When a Profile requires source contracts, a shared schema binding alone cannot establish coverage. Source contract failures also reduce the schema category. Each category reports its checked and passed counts. Categories with no applicable checks are excluded from the weighted average. No detected models means incomplete mechanic coverage.

A Tower whose applicable checks and model-schema coverage all pass receives 100. Failed checks receive partial credit. Unbound model types prevent 100, including after rounding. The bundled Profile requires source contracts and sets `unknownModels: "error"`, so an unknown type fails validation. Other Profiles can report unknown types without failing validation; their scores still remain incomplete.

The Dart family scores 100/100 with the bundled Profile. Validation checks 99 files and 1,001 references, with source contracts covering all 6,346 detected model instances. Previously, it scored 84.73 because only 531 instances had shared schema bindings. Those 531 still receive shared schema checks as well as source contract checks. Complete structural coverage does not establish complete gameplay interpretation.

Reports distinguish `canonicalSchemaModelInstances` from `structuralContractModelInstances`; these counts overlap. `modelContracts.types` counts the 1,175 contracts configured in the whole Profile, not the distinct types encountered in the selected Tower scope. The full active capture has 482,492 source contract checks and 61,421 shared schema checks, with no unbound model instances.

Add `--format text` for terminal output or `--relations` for resolved references and backlinks in JSON. Backlinks describe only the checked graph in Tower scoring. Exit codes are 0 for passed validation, 1 for failed validation and 2 for invalid arguments, selection or Profile. A partial score caused only by coverage gaps retains exit code 0 when the Profile permits unknown types.

## Generalization and provenance

`mechanics.typeIdentity` selects a discriminator field and encoding. BTD6 uses `$type` and `dotnet`, which extracts the short class name. Another game can use `kind` and `literal`. Validation, dependency discovery, purchase aliases and unit bindings all use the same setting.

Capture metadata uses a configured `base`, `path` and label-to-source-field map. `base` is `gameData` or its `parent`. BTD6 binds generic `buildId` to `steamBuildId`. Metadata is informational and does not establish completeness.

Reports record Profile revision and dependency digest, actual checker version and executable identity, errors, counts and coverage. Numerical checks do not convert or rewrite data. Shared schemas permit additional projected fields, while source contracts reject undeclared raw fields unless they define a dictionary value shape. Coverage reports and contract provenance state the checked structure and its limits.

Reusable operations live in `internal/atlasvalidate/`. The command entry point only delegates to the package. Unknown operations and malformed Profile documents fail before checking game-data.

The current Profile and checker interface use format 5. Older Profiles must migrate their manifest version and review their source contracts and schema bindings before using this checker.

See [the implementation record](../docs/profile-implementation.md) for verification and the existing Boomerang duplicate found in the accepted capture.

See [the separate project proposal](../docs/profile-project.md) for a possible validator and base Profile repository. Implementation remains in Atlas while that split is planned.
