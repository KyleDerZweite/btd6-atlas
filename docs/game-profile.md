# Game-data Profile and validation

Atlas owns the Profile contract and `atlas-validate`. The checker applies local schemas and declared rules to separate raw `game-data/` records.
Preserve recorded fields, nesting and `$type`. Capture provenance belongs in the capture manifest; Tower instances remain in the capture.
This replaces the earlier ownership split with Tower Generator. Atlas validation has no dependency on that project.

The Profile manifest references collections, references, mechanics, rules, numerical units and their schemas.
Separate `tower.schema.json`, `mechanics.schema.json` and `mechanic-proposal.schema.json` define Tower records, catalog entries and external proposals.
The six data documents stay at the Profile root. Schemas are grouped into `schemas/profile/`, `schemas/game-data/` and `schemas/scopes/`.
Smaller model schemas keep individual files readable. All required schema dependencies stay inside the Profile directory.

Collections declare optional layout requirements alongside identity and schema bindings. `depth` counts path segments relative to the collection.
`parentField` and `stemField` bind the containing folder and JSON filename stem to recorded fields.
Towers and Bloons use two levels with `baseId` family folders and `name` filenames. Upgrades use one level without a filename binding.
The Profile covers 22 primary collection layouts and three shared family indexes, including the exported singleton model files.
Filename bindings use recorded identities where supported. Rounds only checks depth; round numbering, continuity and category or difficulty folder meanings remain outside coverage.
The bundled `unmatchedFiles: "error"` policy rejects files outside declared collections, including Towers moved beyond their collection path.
The optional `"report"` policy permits and counts those files; it is the default when omitted.
This validates the actual capture organization through reusable data rules; the checker contains no fixed game directory tree.

Schemas define field shapes and intrinsic numerical bounds. Mechanics bind model classes to schemas.
Reference declarations define identity relationships. Rules supply cross-record operation parameters, including progression limits and scope.
The Go package implements those operations without embedding BTD6 names, purchase limits or Tower inventories.
The CLI in `cmd/atlas-validate/` handles invocation and output; `internal/atlasvalidate/` owns reusable validation.

Profile configuration keys describe general concepts. A collection can be named `enemies` while its configured path remains `Bloons`, and a mechanic named `enemy` can bind the raw `BloonModel` class. References use the logical collection name. This already works without changing Go or captured records. Raw schema properties retain their exact source names because they describe the game's JSON format.

Further generalization can make the model discriminator and type-name encoding configurable, then replace fixed capture-report fields with metadata bindings. The current checker still reads `$type`, shortens .NET class names and recognizes BTD6 capture metadata keys. These are proposed follow-up changes.

The checker validates the Profile before reading game-data. Unknown operations, malformed arguments and unresolved Profile references fail loading.
It then checks JSON syntax, declared layouts and schemas, indexes identities and collects references recursively.
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

The checker does not verify the full capture inventory. Missing required files, references and ordinary progression states fail, but deleting an unreferenced record can pass. A guarantee for every deleted file requires a capture-owned inventory or expected counts. Keep those expected records beside the capture; the reusable Profile should declare how to check them rather than contain capture-specific filenames. Inventory checking remains a proposed follow-up.

Use the existing JSON Schema dependency. Keep field constraints and game parameters in the Profile and reusable operations in Go.
Test broken records for illegal builds, duplicate identities, missing targets, invalid transitions, incomplete families and unknown operations.
Run the complete accepted capture and check that support Towers and temporary forms receive their intended coverage.
Keep this implementation on its separate review branch until the user decides how to integrate it.

The new checker run on 2026-09-30 reports valid integrity and one progression failure in the accepted BTD6 56.3 capture.
`BoomerangMonkey-012` repeats the purchase to `BoomerangMonkey-013`; the second entry fails with `duplicate-purchase`.
The rule covered 26 roots, 1,664 ordinary states and 2,887 recorded transitions, with 503 Tower records outside its scope.
The original capture remains unchanged. Full verification and follow-up results belong in [the implementation record](profile-implementation.md).
See [the Profile guide](../profile/README.md) for commands, file responsibilities and raw-data reading conventions.
