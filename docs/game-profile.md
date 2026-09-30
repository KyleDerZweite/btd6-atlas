# Atlas game-data contract

Atlas owns a self-contained Profile and validator. Game-data records remain separate and retain their original fields, type names and embedded abilities. Another project can use the contract without becoming a dependency of Atlas.

The Profile describes collections, identities, layouts, references, mechanic schemas, units, progression and scoring. Generic keys select operations and bindings; BTD6 source names and limits are settings. `enemies` can point to `Bloons`, model detection can use `$type` or a literal `kind`, and metadata labels bind to source fields.

Schemas define shapes. Mechanics bind model types to schemas. Rules check relationships across records. Required roles depend on consumers and enabled features. Ordinary Tower families require their complete rule-derived progression. Empty unused collections are valid. Rogue and Frontier data are outside the bundled primary-game scope.

Completeness is content and reference driven. There is no capture inventory, expected capture count or game-data hash check. Missing required states, dependencies or roles fail. Optional unreferenced deletions can pass, including removal of a whole unused family. The Profile does not claim that every possible deletion will fail.

Tower scoring checks the selected family, outbound dependencies and applicable roles. Unrelated records and inbound consumers do not enter the score. Profile weights combine passed checks and mechanic coverage. Incomplete mechanic schemas prevent a perfect score. Compliance does not establish runtime equivalence, balance or character fidelity.

All Profile dependencies stay local. Unknown operations fail loading. Reports identify the Profile and checker and state actual coverage. Original captures and the exporter remain unchanged.

See [the Profile guide](../profile/README.md) for the structure and commands, and [the implementation record](profile-implementation.md) for decisions and verification. Work remains on `feat/profile-rule-validation` in PR #3 without merging.
