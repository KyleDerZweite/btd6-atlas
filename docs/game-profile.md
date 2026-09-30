# Atlas game-data contract

Atlas keeps a self-contained BTD6 Profile and uses the released [td-profile](https://github.com/mardwerk/td-profile) validator. Game-data records remain separate and retain their original fields, type names and embedded abilities. Shared schemas are local copies from td-profile release `v1.0.2`, so validation needs no network access.

The Profile describes collections, identities, layouts, references, mechanic schemas, source structure contracts, units, progression, classification and scoring. Reusable schemas live in `schemas/profile/` and `schemas/game-data/`. BTD6 source names and limits are configuration settings. `enemies` can point to `Bloons`, model detection can use `$type` or a literal `kind`, and metadata labels bind to source fields.

Schemas define shared shapes. Mechanics bind model types and source fields to those shapes and declare required fields. The checker validates a temporary schema view without replacing the raw records. Named selectors in `rules.json` describe source categories and model markers. They drive progression scopes, conditional requirements and classifications without separate game-specific schema files.

Source structure contracts check the raw records before projection. The reusable `model-contracts.schema.json` defines a vocabulary for required fields, value types, nested models and dictionary values. BTD6 source names and allowed nested types live as values in `model-contracts.json` and its ten included documents. Exact source identities keep same-named .NET classes distinct. All 1,175 source types observed in the active capture have contracts, and unknown types fail validation.

The contracts describe structure derived from `56.3-build-24829026`. They reject missing or unexpected fields and incompatible values without inferring numerical ranges, integer intent or gameplay behavior. Null-only fields and empty-only arrays remain restricted to those observed shapes. New variants require review and an explicit contract revision. `scripts/derive-model-contracts.py` can audit a capture or generate candidates. Submit candidate changes for Profile review through a td-profile PR. Regeneration changes the requirements; it does not prove a failing record valid.

Ordinary Towers and Power Pro Towers use configured purchase progression. Heroes use configured linear progression. All 2,167 captured Tower records have a declared category, including forms, subtowers and paragons that receive structural and reference checks. Required roles depend on consumers and enabled features. Empty unused collections are valid. Rogue and Frontier behavior remains outside the bundled primary-game scope.

Completeness is content and reference driven. There is no capture inventory, expected capture count or game-data hash check. Missing required states, dependencies or roles fail. Optional unreferenced deletions can pass, including removal of a whole unused family. The Profile does not claim that every possible deletion will fail.

Tower scoring checks the selected family, outbound dependencies and applicable roles. Unrelated records and inbound consumers do not enter the score. Profile weights combine passed checks and model-schema coverage. Detected model classes include presentation and supporting objects. A shared schema binding or source structure contract establishes model coverage, subject to the Profile's required-contract policy. Reports count those checks separately, and missing coverage prevents a perfect score. Contract failures reduce the schema score. A perfect score means the declared checks pass; it does not measure runtime equivalence, balance or character fidelity.

All Profile dependencies stay local. Unknown operations fail loading. The Profile and checker use interface version 5. Reports identify both versions, state actual coverage and include source contract provenance. Original captures and the exporter remain unchanged.

Install the pinned td-profile `v1.0.2` binary with `python3 scripts/install-validator.py`. It supplies checker `5.0.1` at `bin/validator`, or `bin/validator.exe` on Windows. The executable stays outside Git. Atlas has no local Go checker.

Propose Profile, shared schema and checker updates through a PR to [td-profile](https://github.com/mardwerk/td-profile), then adopt the released changes here. Keep the schema copies byte-identical to the pinned release and preserve BTD6 settings and raw captures.

See [the Profile guide](../profile/README.md) for the structure and commands, [the implementation record](profile-implementation.md) for historical decisions and verification, and [the project split](profile-project.md) for the current setup. [PR #3](https://github.com/KyleDerZweite/btd6-atlas/pull/3) is merged.
