# Game-data Profile and validation

Atlas owns the Profile contract and `atlas-validate`. The checker applies local schemas and declared rules to separate raw `game-data/` records.
Preserve recorded fields, nesting and `$type`. Capture provenance belongs in the capture manifest; Tower instances remain in the capture.
This replaces the earlier ownership split with Tower Generator. Atlas validation has no dependency on that project.

The Profile manifest references collections, references, mechanics, rules, numerical units and their schemas.
Separate `tower.schema.json`, `mechanics.schema.json` and `mechanic-proposal.schema.json` define Tower records, catalog entries and external proposals.
Smaller model schemas keep individual files readable. All required schema dependencies stay inside the Profile directory.

Schemas define field shapes and intrinsic numerical bounds. Mechanics bind model classes to schemas.
Reference declarations define identity relationships. Rules supply cross-record operation parameters, including progression limits and scope.
The Go package implements those operations without embedding BTD6 names, purchase limits or Tower inventories.
The CLI in `cmd/atlas-validate/` handles invocation and output; `internal/atlasvalidate/` owns reusable validation.

The checker validates the Profile before reading game-data. Unknown operations, malformed arguments and unresolved Profile references fail loading.
It then checks JSON syntax and schemas, indexes identities and collects references recursively.
After scanning all files, it resolves references and runs the declared rules. Forward links and cycles remain valid.
The command reads files without modifying them or making network calls.

The ordinary purchase rule selects base Towers through a local schema and follows `upgrades[].tower`.
A separate member schema identifies candidate families that require roots. Required boolean flags prevent malformed records from silently escaping the selectors.
Completeness fails when a candidate family has no root, including when the entire scope has no roots.
The rule checks legal builds, same-family targets, one-step purchase transitions, unique permanent builds and complete reachable state sets.
It also requires every legal outgoing transition and rejects duplicate transitions.
The bundled limits derive 64 legal states per family. Paragons, heroes and separate temporary forms remain outside that progression graph.
Those records still receive applicable schema and reference checks, and the report exposes the scope boundary.
Upgrade path/tier metadata agreement remains separate because the captured Skywarden metadata has known inconsistencies.

Every JSON file receives syntax and root-object checks. Declared schemas permit additional raw fields.
Unknown model types are reported under the bundled policy; a Profile can require them to fail instead.
Assets and local mutation IDs have different semantics from exported record references.
Documented external symbols retain exact allowances and reasons. Existing exported records take precedence over those allowances.

Reports identify the Profile revision and content digest, checker build and executable hash, validation counts and actual coverage.
Each error provides a file, JSON pointer, code and message. Optional relation output includes resolved targets and backlinks.
Exit codes are 0 for valid data, 1 for invalid data, and 2 for an invalid invocation or Profile.
Passing means that the declared requirements passed. It does not establish runtime equivalence, simulation coverage or balance.

Use the existing JSON Schema dependency. Keep field constraints and game parameters in the Profile and reusable operations in Go.
Test broken records for illegal builds, duplicate identities, missing targets, invalid transitions, incomplete families and unknown operations.
Run the complete accepted capture and check that support Towers and temporary forms receive their intended coverage.
Keep this implementation on its separate review branch until the user decides how to integrate it.

The new checker run on 2026-09-30 reports valid integrity and one progression failure in the accepted BTD6 56.3 capture.
`BoomerangMonkey-012` repeats the purchase to `BoomerangMonkey-013`; the second entry fails with `duplicate-purchase`.
The rule covered 26 roots, 1,664 ordinary states and 2,887 recorded transitions, with 503 Tower records outside its scope.
The original capture remains unchanged. Full verification and follow-up results belong in [the implementation record](profile-implementation.md).
See [the Profile guide](../profile/README.md) for commands, file responsibilities and raw-data reading conventions.
