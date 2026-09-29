# Game-data profile

Use raw `game-data/` files directly. Preserve every field, including `$type`.
The profile describes the format and its references; it does not require a particular version, file count, or filename inventory.
The bundled rules describe BTD6 data, with deeper schemas for core Tower models.

`game-profile.json` declares collections, identity fields, model schemas, reference rules, and reading conventions.
`schema.json` contains JSON Schema draft 2020-12 definitions. Additional game fields remain permitted.
Capture provenance stays in the data directory's manifest, outside the profile.

Build a standalone binary from the repository root with Go 1.23 or newer:

```sh
CGO_ENABLED=0 go build -trimpath -ldflags='-s -w' -o bin/atlas-validate ./cmd/atlas-validate
bin/atlas-validate --data data/56.3-build-24829026/game-data --profile profile
```

Both arguments accept absolute paths. The binary requires the profile files at runtime and has no Git or network dependency.
Generated binaries stay in the ignored `bin/` directory.

The validator parses each JSON file once. During that traversal it checks schemas, indexes exported identities, and collects references recursively.
After scanning every file, it resolves references against the indices. Forward references and cycles are allowed.
Identities come from the profile's selectors, usually recorded fields rather than filenames.
Family identifiers and individual state identifiers use separate collections.
Moving or renaming a file preserves a field-based identity if the file still belongs to the same collection.

The default output is JSON with `valid`, `filesChecked`, `referencesChecked`, `externalReferences`, and an `errors` array.
An optional sibling `manifest.json` supplies the informational `gameVersion` field. Its version and file counts do not constrain validation.
Each error contains `file`, `pointer`, `code`, and `message`. Pointers use JSON Pointer syntax and refer to the reported file.
Use `--format text` for terminal diagnostics such as:

```text
Towers/DartMonkey/DartMonkey.json#/upgrades/0/tower: missing_reference: Towers record "DartMonkey-100" does not exist
```

Exit codes are 0 for valid data, 1 for invalid data, and 2 for an invalid invocation or profile.
The validator reads files without modifying them.

Add `--relations` to include the graph in JSON output:

```sh
bin/atlas-validate --data /path/to/game-data --profile /path/to/profile --relations > relations.json
```

`relations` lists each resolved source file and JSON pointer, original value, target collection, target identity, and target files.
A family target can have several files. Aliases retain the original value and report the canonical target identity.
`backlinks` maps each target file to its incoming source files and pointers.
Documented external symbols have `external: true` and an empty target-file list.
Unresolved references appear in `errors` and are absent from the resolved graph.

Every JSON file receives syntax and root-object checks. Duplicate JSON keys and duplicate record identities fail validation.
Declared collections and core models receive schema checks. Known model slots also require the appropriate `$type` class.
Reference rules cover purchases, applied upgrades, Knowledge prerequisites, Bloon emissions, selected actor and artifact references, and map catalogs.
Unknown files and behavior parameters remain permitted. Add schemas and reference rules when those fields need validation.

Deleting a referenced record fails. Adding a valid record or removing an unreferenced record can pass.
Optional `requiredFiles` declares files required by the format. The bundled profile requires `textTable.json` for localization.
This checks structural and reference integrity, not whether the data reproduces an earlier capture or implements correct gameplay.

Reuse the same profile for later captures while their format remains compatible.
For your own game, copy the profile directory and edit the collections, schemas, reference rules, required files, and reading conventions to match your format.
The walker does not contain BTD6 model names or file counts. Model dispatch uses the `$type` class name, ignoring namespace and assembly suffix.
A reference rule identifies the source class, field, and target collection. Values can be strings or arrays of strings; null and empty values mean no reference.
Indices support record fields, dictionary keys with `@keys`, directory families with `@parent`, filename stems with `@stem`, and collection-relative paths with `@path`.
The same files can supply a state index and a family index.

The BTD6 rules retain exact documented symbols for five modifier names without exported Knowledge definitions and the unexported `BossRush` mode.
An exported target takes precedence over an external-symbol allowance. Other unresolved values fail.
`ProtecttheYacht` resolves through an explicit alias to `ProtectTheYacht`.
Assets and local mutation IDs have different semantics from exported record references.
Nullable fields, anonymous embedded Tower models, and `xpCost: -1` values remain valid as captured.
Skywarden's purchase links resolve, so it passes integrity checks; inconsistent upgrade tiers remain a gameplay-data concern.
Upgrade descriptions use `textTable.json` keys built from `LocsKey` plus ` Description`. Hero progression uses different text conventions.

See [the reviewed design and validation evidence](../docs/game-profile.md).
