# Raw game profile and validation

The reviewed design reads `game-data/` exactly as captured. It replaces the gameplay Tower exporter and derived copies.
Atlas owns the raw-data profile, schema, and integrity tool. Tower Generator owns its consumer and engine behavior.

`profile/game-profile.json` defines collections, record identifiers, typed references, and reading conventions.
`profile/schema.json` uses JSON Schema draft 2020-12 for structural checks, with deeper coverage for Tower, upgrade, attack, weapon, projectile, ability, Knowledge, Bloon, and round models.
The profile describes a reusable format. It does not prescribe a capture version, file count, or filename inventory.
Capture provenance remains in the data directory's existing manifest.
The validator reads each JSON file once, indexes exported identities, and collects typed references during that traversal.
It resolves references after indexing every file, so forward references and different collection sizes work.
Optional relation output includes resolved targets and backlinks. Family references resolve to the files currently in that family.

The Go command reads one data directory and one profile directory. It performs no writes or network calls.
It returns JSON containing `valid`, file and reference counts, and diagnostics with file paths, JSON pointers, error codes, and messages.
Text output is available for terminal use. Exit codes are 0 for valid data, 1 for invalid data, and 2 for an invalid invocation or profile.

All JSON files receive syntax and root structure checks. Declared collections and models receive schema checks.
Typed reference rules apply recursively, including embedded actors and effects.
Assets and documented runtime symbols are not treated as missing JSON files.
Reference rules are explicit because tags, asset IDs, local model IDs, and external record IDs can share string values.
Known external symbols have exact values and documented reasons. Exported targets take precedence over symbol allowances.
The tool checks recorded structure and references. It does not enforce gameplay assumptions that the current capture contradicts, including Skywarden's upgrade tier metadata.

Use the existing cached Go JSON Schema implementation instead of writing a partial schema evaluator.
Keep the validator small and test actual broken fixtures, including missing targets, invalid field types, duplicate identities, and duplicate JSON keys.
Accept additional files, different collection sizes, and renamed files whose recorded identities and links remain valid.
An absent unreferenced record is valid unless the profile explicitly requires its file.
Run it against the entire accepted capture, then delete referenced files in a disposable copy and verify actionable failures.
Build the local binary, commit the cleanup and replacement, and push the current branch after the checks pass.

Extend the profile when a capture or another game changes its layout, model schemas, or reference conventions.
Keep data-specific versions and counts outside the contract. Maps currently receive catalog and reference checks; detailed Atlas map geometry remains outside this profile.

Validation on 2026-09-30 passed for BTD6 56.3, Steam build 24829026: 10,055 JSON files, 66,728 references, and 93 documented external references.
The optional graph contained 132,727 file links across 3,914 target files; every backlink matched its corresponding relation.
Profile model-member bindings matched the installed compiled Il2Cpp references.
Fixture tests cover different collection sizes and versions, added records, renamed files, forward references, aliases, family targets, and graph output.
Live checks in a disposable copy rejected deleted Tower, upgrade, Knowledge, Bloon, map, family, and required localization files.
They accepted an added valid Tower, an identity-preserving rename, and removal of an unreferenced round.
Invalid Tower types and weapon intervals failed. A restored standalone copy passed outside the repository.
`go test ./...` and `go vet ./...` passed. Raw captures and their existing manifests remained unchanged.
