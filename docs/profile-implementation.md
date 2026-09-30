# Profile implementation

Implement on `feat/profile-rule-validation` in PR #3. The user approved the final interview decisions on 2026-09-30. Keep the branch separate and do not merge.

The earlier Profile format 2 established split schemas, reusable layout checks and purchase progression. The confirmed follow-up uses format 3. Atlas owns both the Profile and checker. Preserve captured records and embedded abilities. No mod or game-model accesses change.

## Confirmed decisions

Use generic logical collections with configured source paths. Express required data as roles with conditional consumers. Empty unused collections are valid. A present ordinary Tower family requires its root, all legal builds, all legal outgoing purchases and referenced dependencies. Derive states from limits, without a capture inventory, expected capture counts, filename lists or game-data content-hash checks.

Feature settings control applicability. Rogue and Frontier data are disabled and outside primary-game scope. Required role paths can move without changing Go. Resource usage requires the resource catalog, without claiming complete asset-key resolution.

Configure the model discriminator and type-name encoding in mechanics data. Apply them consistently to validation, dependency discovery, aliases and units. Configure metadata base, path and source-field bindings. Metadata remains informational.

Add `score-tower --profile <path> --game-data <path> --tower <path>`. All three flags are mandatory. Check the selected family, outbound dependencies and applicable roles. Unrelated missing or malformed records must not affect the score. Backlinks describe the checked graph without expanding into unrelated incoming consumers.

Use Profile weights for six categories. Award partial credit; incomplete mechanic schema coverage prevents 100 even after rounding. Scoring measures compliance, without simulation or balance claims. Keep command parsing and output in the reusable package and preserve whole-dataset invocation.

Review implementation against these decisions and test scoped isolation, conditional roles, alternate fields and formats, broken progression, partial scores and complete coverage. Run unchanged accepted data and a disposable corrected copy. Keep originals unchanged.

## Implementation

Profile format 3 contains seven configuration documents and split schemas under `schemas/profile/`, `schemas/game-data/` and `schemas/scopes/`. The requested Tower, mechanics and proposal schemas remain separate. Profile loading validates every document and resolves only local schema dependencies.

Logical `enemies` binds to `Bloons`; `localization` binds to `textTable.json`. Collections configure depth and family/filename bindings. Towers use `Towers/<baseId>/<name>.json`. Upgrades retain identity independent of sanitized filenames. Conditional roles require localization for Tower/upgrade consumers, resources for asset consumers and advanced progression data for paragons.

The same configured type identity drives every engine operation. BTD6 uses `$type` and .NET names. Tests use literal `kind` values, renamed fields and different progression limits. Metadata labels bind to source fields without BTD6 names in Go.

The command entry point delegates to `internal/atlasvalidate`. Tower scoring selects the family before validation, indexes possible dependencies without collecting global errors, then checks only its outgoing closure and required roles. Cycles terminate. Rule results, coverage and backlinks use the selected set.

Scores report category weights and passed/checked counts. Schema, reference and unit credit is per file; layout includes role presence; rule credit is per applicable result; mechanics credit is per model instance. Inapplicable categories are excluded. Missing coverage and failed checks prevent 100.

## Verification

Final verification results follow below. The historical single-file deletion trial selected Glue Gunner state `240` using seed `20260930` and rejected its deletion. The confirmed implementation deliberately replaces the previously proposed capture inventory with conditional roles and graph completeness.

`go test ./...`, `go test -race ./...`, `go vet ./...`, both binary builds and `git diff --check` passed. The command entry point is 13 lines. Tests cover literal type identities, typed aliases, conditional roles, relocated data, generic metadata, disabled features, dependency cycles, complete and partial scores, unknown coverage, rounding, configurable weights, invalid settings and CLI flags. Ordinary-root requirements apply only when ordinary candidate members exist.

The final unchanged BTD6 56.3 run checked 10,053 files, skipping Rogue and Frontier. It checked 65,854 references, including 93 documented external references. Integrity passed. Progression checked 26 roots, 1,664 states and 2,887 purchases. It still found the existing duplicate at `Towers/BoomerangMonkey/BoomerangMonkey-012.json#/upgrades/2/tower`, repeating `BoomerangMonkey-013`. Original data stayed unchanged.

A disposable standalone copy with only that duplicate removed passed with 65,852 references and 2,886 purchase transitions. Its graph contained 122,288 target/backlink links. The copied Profile, binary and data ran outside the repository. There were 1,155 unbound model types, 503 Tower records outside ordinary progression and 20,325 checked unit values. Mode exclusion accounts for the difference from earlier whole-capture counts.

Deletion trials on that passing baseline used seed `20260930`. The selected `Towers/SpikeFactory/SpikeFactory-140.json` failed with missing-reference and progression diagnostics. Removing `resources.json`, `textTable.json` or `paragonDegreeData.json` failed with a specific required-role error. Removing Rogue or Frontier data passed. Each file was restored between cases.

Dart Monkey scoring checked 99 files, 1,001 references, 64 ordinary states and 111 purchases. It passed the declared validation checks and scored 84.73 because 63 model types were unbound. Mechanics coverage bound 531 of 6,347 model instances. Breaking or deleting an unrelated Glue Gunner state left the full score report unchanged. Deleting Dart's `100` state produced missing-reference and progression errors and lowered the score to 67.84. Synthetic complete coverage scored 100.

The final Profile dependency closure contains 32 files with SHA-256 `d241f56408b4bfc071c34e847b0657811e8563768cb76470683c7d226f0cb270`. This identifies Profile content, without hashing or inventorying game-data for completeness. Reports and mutation evidence are in ignored `bin/profile-v3-*.json` files. No C# build is needed because the mod is unchanged.
