# Profile implementation

Historical implementation record, 2026-09-30. [PR #3](https://github.com/KyleDerZweite/btd6-atlas/pull/3) is merged. The sections below preserve the decisions and verification from that work, including earlier coverage limits that format 5 resolved.

The checker and its tests now live in [td-profile](https://github.com/mardwerk/td-profile). Atlas uses release `v1.0.2`, checker `5.0.1` and interface `5`, installed with `python3 scripts/install-validator.py`. See [the project split](profile-project.md) for the current ownership and migration checks.

## Confirmed decisions

The bundled settings define the BTD6 Profile. Every schema file defines a reusable shape. Game-specific source names, required concepts, category selectors, supported model bindings and progression limits belong in JSON settings. Validate a temporary generic view while preserving the raw exports, embedded abilities and `$type`. No `data/` or `mod/` files change.

Describe logical collections through configurable source paths, identities and layout. Require data roles only when enabled features or present consumers need them. Empty unused collections are valid. Completeness follows declared references and progression rules, without capture inventories, filename lists, expected capture counts or game-data content hashes.

Add `score-tower --profile <path> --game-data <path> --tower <path>`. All three flags are mandatory. Check the selected family, outgoing dependencies and applicable roles. Unrelated missing or malformed records must not affect the report. Backlinks describe the checked graph. Profile weights award partial credit across six categories. Incomplete model-schema coverage prevents 100, including after rounding. Scores measure contract compliance, without balance or simulation claims.

Account explicitly for every Tower record. Ordinary Towers and Power Pro Towers use configured purchase rules; canonical heroes use a configured linear rule. Paragons, forms, subtowers and other family variants receive shared schemas and reference checks with explicit coverage limits. Unknown or ambiguous classifications fail. Do not infer ownership, lifetime or transformations from a classification alone.

Configure model discriminator fields and encodings, metadata bindings and native units through the Profile. Unknown operations fail loading. Keep the command entry point minimal and the Profile dependency closure local and reproducible. Changing configuration values can reuse supported concepts; a new behavior still requires a shared schema and an implemented rule operation where appropriate.

## Historical format 4 implementation

Profile and validator interface format 4 use revision/version `4.0.0`. The format bump makes the new normalized-schema boundary explicit rather than silently reinterpreting older Profiles. Eight configuration documents reference smaller schemas under `schemas/profile/` and `schemas/game-data/`. The requested Tower, mechanics and mechanic-proposal schemas remain separate. There is no game-specific scopes schema directory.

Mechanic `fields` map shared names to direct source fields, such as `familyId` to `baseId` and `placementPrice` to `cost`. `requiredFields` supplies game-specific requiredness. Projection handles nested models without mutating raw values. Typed collections require their configured discriminator; untyped tables retain their original keys. `excludedKeys` configures source metadata exclusions for table identities. Each overlapping collection validates its own identity projection.

Named selectors in `rules.json` select raw categories and contained model classes. Collections use those selectors for rule scopes and conditional roles. Classifications distinguish records inspected by progression from structurally checked records. Purchase targets must satisfy their member selector. Linear rules check level ranges, required levels, roots and next-level transitions.

The command delegates to `internal/atlasvalidate`. Tower scoring selects a family, indexes possible dependencies without global diagnostics, and validates only the outgoing closure and required roles. Reference cycles terminate. Unknown model types include deterministic example locations and remain visible as coverage gaps.

## Original verification plan

Run unit tests, race tests, vet, builds and diff checks. Test identical schemas with .NET source types, renamed literal fields and native generic fields. Test invalid bindings, missing discriminators, alias collisions, unknown selectors, illegal builds, missing roots and levels, progression scope violations, unknown rules, partial scores and complete coverage.

Validate the unchanged accepted capture. Validate a disposable standalone copy after correcting only the known duplicate Boomerang purchase. Delete required ordinary, hero and Power Pro states and required roles in the copy; verify specific failures. Delete or break an unrelated family and confirm Dart scoring is unchanged. Keep capture corrections and reports local.

## Earlier verification

The format 3 implementation passed tests, race tests, vet and standalone builds. The unchanged capture checked 10,053 files and 65,854 references, including 93 documented external references. Integrity passed. Ordinary progression found the existing duplicate at `Towers/BoomerangMonkey/BoomerangMonkey-012.json#/upgrades/2/tower`. Removing only that duplicate in a disposable copy passed with 65,852 references.

Earlier deletion trials rejected a randomly selected `SpikeFactory-140` state and missing resources, localization or advanced-progression roles. Removing Rogue or Frontier data passed. Breaking or deleting an unrelated Glue Gunner state left Dart's report unchanged. Deleting Dart's `100` state lowered its score and reported missing references and progression states. These results are in ignored `bin/profile-v3-*.json` files.

## Format 4 verification

`go test ./...`, `go test -race ./...`, `go vet ./...`, both binary builds and `git diff --check` passed. Three source configurations reuse identical schema files. Complete synthetic coverage scores 100. Regression tests cover source-binding bypasses, table metadata, progression membership, invalid selectors and classifications, and scoped dependency checks. The command entry point remains 13 lines.

The unchanged BTD6 56.3 capture checked 10,053 files, skipped two disabled mode files, and checked 65,854 references with 93 documented external references. Integrity passed. The only error is the existing duplicate Boomerang purchase. All 2,167 Tower records are classified: 1,664 ordinary states, 360 hero levels, 50 Power Pro states, 13 paragons, 56 subtowers, 20 transformed forms, three family variants and one Frontier record.

A disposable standalone Profile, binary and capture passed after removing only that duplicate in the copy. It checked 65,852 references. Ordinary progression covered 26 roots, 1,664 states and 2,886 transitions; hero progression covered 18 roots, 360 levels and 342 transitions; Power Pro progression covered five roots, 50 states and 45 transitions. There are 1,155 unbound model types and 20,325 checked unit values.

Deletion trials used seed `20260930`. Removing the selected `SpikeFactory-230` state, Quincy level 10, Quincy's root or `PortableLakePro-200` failed with specific progression and reference diagnostics. Removing resources, localization or advanced progression data failed with required-role errors. Removing disabled Rogue or Frontier data passed. Files were restored between cases in the disposable copy.

Dart checked 99 files, 1,001 references, 64 ordinary states and 111 purchases. Its score is 84.73. Model-schema coverage is 531 of 6,346 instances with 62 unbound types. A dictionary wrapper is no longer miscounted as a gameplay model. Breaking or deleting an unrelated Glue Gunner state left the complete Dart report unchanged. Removing Dart's `100` state produced missing references and states and lowered its score to 67.84.

The final Profile dependency closure contains 32 files with SHA-256 `b477e2bfee4b542443fa45d4e4476d1ea800c03f2c4748cff7941b3d6261d1a6`. Reports identify the actual checker build and executable used. This hashes Profile dependencies, without hashing game-data for completeness. Reports and mutation evidence remain in ignored `bin/profile-v4-*.json` files. No raw capture or exporter files changed; no C# build was needed.


## Complete model-contract follow-up

The user requested coverage for all detected model types and a proposal for extracting the generic tooling on 2026-09-30. This follow-up was implemented in Atlas and merged through PR #3. Extraction remained a proposal during this stage.

Add explicit structural contracts for each exact source discriminator, using reusable contract syntax and a generic checker. Require known fields, accepted primitive shapes, nested model identities and checked dictionary values. Retain the existing stronger canonical schemas. Keep capture-derived structural coverage separate from canonical concept coverage in reports. Do not infer behavior semantics or silently replace missing coverage with a kind-only fallback.

Derive contracts deterministically from the fixed accepted capture. Record source revision and capture-derived limits without raw record values, filenames or game-data hashes. Null-only fields and empty-only arrays stay narrow until further evidence exists. Namespace collisions and generic dictionary specializations use exact source identities. Split configuration files to keep individual files manageable. BTD6 type names and field names remain configuration values; schema files remain reusable.

Test required-field deletion, wrong primitive values, incompatible nested model types, unexpected fields, dictionary values, source type collisions, unknown models and incomplete capture evidence. Verify all active capture models receive contracts, Dart can receive 100 when its checks pass, other Tower families score correctly, and missing related data still lowers the score. Preserve original captures and the exporter.

## Historical format 5 verification

Unit tests, race tests, vet, both binary builds, generator doctests and diff checks passed. An independent review found no remaining concrete bugs after the exact-discriminator and include-resolution fixes. Generic integration tests cover strict fields, partial scores, required exact contracts, shared includes, digest changes and invalid Profile documents. The command entry point remains 13 lines.

The unchanged capture checks 10,053 files, 65,854 references and 482,492 model instances. Two disabled mode files are skipped. All 1,175 exact source types have contracts, with zero unbound instances. There are 61,421 overlapping canonical schema checks. Integrity passes; the sole error remains the existing duplicate Boomerang purchase. A standalone copied binary, Profile and capture pass after correcting only that duplicate in the disposable copy, checking 65,852 references and 482,491 model instances.

Dart, Monkey Village, Banana Farm, Alchemist, Wizard, Quincy and Portable Lake Pro each score 100/100 with complete structural coverage. Dart checks 99 files, 1,001 references and 6,346 model instances, including 531 overlapping canonical schema checks. Removing Dart's `100` state lowers the score to 83.11 and reports missing progression and references. Breaking or deleting an unrelated Glue Gunner state leaves Dart's complete report unchanged.

Deletion trials use seed `20260930`. Removing the selected ordinary state, Quincy level 10 or a Power Pro state fails with specific progression and reference diagnostics. Missing localization fails its required-role check. Removing disabled Rogue or Frontier data passes. Corruption trials reject missing required fields on a previously unbound type, wrong primitives, unexpected fields, incompatible known nested models, namespace collisions, unknown exact types, malformed normalized names, null-only alternatives, nonempty restricted arrays and bad dictionary values. New dictionary keys with valid values pass. Empty game-data passes with zero files.

The Profile closure contains 44 dependencies with SHA-256 `e63bbc90a8f74482cf216b00107b09352a6173e3efdaff735b36a4b58b3ba5a8`. Reports identify checker version `5.0.0`, its actual build and executable digest, and contract provenance. Evidence remains in ignored `bin/profile-v5-*.json` files. Original captures and the exporter are unchanged. No repository move or packaging was implemented during this stage. [The project split](profile-project.md) records the subsequent extraction and current release setup.
