# Atlas game-data contract

Atlas owns a self-contained Profile and validator. Game-data records remain separate and retain their original fields, type names and embedded abilities. Another project can use the contract without becoming a dependency of Atlas.

The Profile describes collections, identities, layouts, references, mechanic schemas, units, progression, classification and scoring. Reusable schemas live in `schemas/profile/` and `schemas/game-data/`. BTD6 source names and limits are configuration settings. `enemies` can point to `Bloons`, model detection can use `$type` or a literal `kind`, and metadata labels bind to source fields.

Schemas define shared shapes. Mechanics bind model types and source fields to those shapes and declare required fields. The checker validates a temporary schema view without replacing the raw records. Named selectors in `rules.json` describe source categories and model markers. They drive progression scopes, conditional requirements and classifications without separate game-specific schema files.

Ordinary Towers and Power Pro Towers use configured purchase progression. Heroes use configured linear progression. All 2,167 captured Tower records have a declared category, including forms, subtowers and paragons that receive structural and reference checks. Required roles depend on consumers and enabled features. Empty unused collections are valid. Rogue and Frontier behavior remains outside the bundled primary-game scope.

Completeness is content and reference driven. There is no capture inventory, expected capture count or game-data hash check. Missing required states, dependencies or roles fail. Optional unreferenced deletions can pass, including removal of a whole unused family. The Profile does not claim that every possible deletion will fail.

Tower scoring checks the selected family, outbound dependencies and applicable roles. Unrelated records and inbound consumers do not enter the score. Profile weights combine passed checks and model-schema coverage. Detected model classes include presentation and supporting objects. Missing schema bindings prevent a perfect score; the score does not measure runtime equivalence, balance or character fidelity.

All Profile dependencies stay local. Unknown operations fail loading. Reports identify the Profile and checker and state actual coverage. Original captures and the exporter remain unchanged.

See [the Profile guide](../profile/README.md) for the structure and commands, and [the implementation record](profile-implementation.md) for decisions and verification. Work remains on `feat/profile-rule-validation` in PR #3 without merging.
