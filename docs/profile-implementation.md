# Profile implementation

Implement on `feat/profile-rule-validation`. The user approved Atlas ownership of the Profile and semantic checker on 2026-09-30. This supersedes the earlier ownership statement in `docs/game-profile.md`.

Keep captured fields and `$type` unchanged. The Profile contains reusable schemas, bindings, units and rule parameters. Capture records, versions and hashes remain under `data/`.

Split model schemas by responsibility, including `tower.schema.json`, `mechanics.schema.json` and `mechanic-proposal.schema.json`. Resolve dependencies from the Profile directory without network access. Validate every Profile document before checking records.

The user's follow-up adds organized schema folders and reusable game-data layout requirements. Keep the six data documents at the Profile root. Group schemas under `schemas/profile/`, `schemas/game-data/` and `schemas/scopes/`.

Declare optional per-collection `layout` requirements in `collections.json`. `depth` counts path segments relative to the collection. `parentField` binds the containing folder to a recorded field; `stemField` binds the JSON filename stem. Towers and Bloons use depth two with `baseId` folders and `name` filenames. Upgrades use depth one without a filename binding because exported filenames can sanitize names. Generic Go checks read these requirements from the Profile.

Verify misplaced records, incorrect family folders and mismatched state filenames, while preserving valid sanitized upgrade filenames. Re-run the accepted capture and standalone copy after the schema move and layout checks. The final dependency digest and evidence below must reflect that run.

The layout implementation declares 22 primary collections and three shared family indexes. All primary collections have depth requirements. Safe filename bindings use recorded identities; Skins also binds its containing folder to `baseTowerName`. Upgrades and BloonOverlays remain depth-only. Rounds uses depth two without interpreting numeric filenames or checking continuity. Category and difficulty folder meanings remain outside coverage.

Add the exported `paragonDegreeData.json`, `rogueData.json` and `frontierData.json` singletons with the shared basic model schema. These additions bring all 10,055 capture files under a collection schema and layout while preserving explicit mechanic coverage gaps.

Set the bundled `unmatchedFiles` policy to `error` so records moved outside declared collections fail with `unmatched_file`. Other Profiles can use `report`, the default when the optional setting is absent. Unmatched files remain visible in `filesWithoutSchema` under either policy.

Keep the CLI in `cmd/atlas-validate`. Put loading, structural checks, reference resolution, coverage reporting and finite rule operations in `internal/atlasvalidate`. Keep game model names, field bindings, root selectors and progression limits in Profile data.

Select ordinary Tower roots with a Profile schema. Follow the configured purchase links to determine permanent states. Forms and paragons remain structurally checked and explicitly outside ordinary progression coverage. Derive complete legal state sets from rule limits instead of storing instance inventories.

Preserve duplicate-key detection, collection identities, forward references, aliases, documented external symbols and optional relations. Unsupported rules fail Profile loading. Unbound raw model types remain visible in coverage; a Profile can require complete coverage.

Record Profile content identity and actual checker build in reports. Numerical units describe native values; validation never converts or rewrites capture data. Mechanic proposals are separate artifacts and do not activate catalog entries.

Verification will cover the accepted 56.3 capture, all ordinary purchase families, illegal builds, incorrect transitions, missing states and targets, duplicate builds and identities, unknown rules, malformed Profile documents and local schema resolution. Check that copied standalone Profile and data directories work outside the repository.

Do not merge into `main`.

## Implementation and verification

Implemented Profile format 2 with separate data documents and 23 small schemas. The required Tower, mechanics catalog and mechanic proposal schemas are included. The old monolithic Profile files are replaced. The CLI is 52 lines; validation lives in `internal/atlasvalidate`.

The Profile supplies model schemas, root and family selectors, reference bindings, native units and progression limits. The checker implements the finite `purchaseProgression` operation. Its evaluation limits bound computation, not game design. No Tower names, prices, capture counts or BTD6 progression limits are embedded in the Go implementation.

Review found that malformed root flags could hide a family. Tower schemas now require the recorded boolean flags. A separate member selector requires a base record for every candidate family. Complete progression also rejects an empty scope and missing purchase edges. Alchemist's three separate forms remain outside the purchase graph.

Final review found that noncanonical collection paths could silently skip collection checks. The loader now normalizes local collection and required-file paths. A `.` collection checks the data directory's root and nested records. Regression tests verify that equivalent paths retain schema, identity, reference and required-file checks.

The unchanged accepted BTD6 56.3 capture passed integrity checks for 10,055 files and 66,728 references, including 93 documented external references. Progression checked 26 roots, 1,664 states and 2,887 purchase entries. It found one identical duplicate in `Towers/BoomerangMonkey/BoomerangMonkey-012.json#/upgrades/2/tower`, repeating the purchase to `BoomerangMonkey-013`. The original capture therefore fails the declared duplicate-purchase requirement.

A standalone disposable copy with only that duplicate removed passed all declared checks. It contained 2,886 purchase transitions and 66,726 references. Its 132,725 relation links matched every backlink. The copied binary, Profile and data ran outside the repository without Git or network dependencies. Original capture files remained unchanged.

Live mutations rejected `1-1-1`, `3-3-0`, a two-tier purchase jump, a missing classification field, a hidden root, a deleted state and a deleted family root. An unknown operation exited with code 2 before reading data. Regression tests additionally cover duplicate identities and builds, strict JSON, aliases, numerical units, schema dependency isolation, proposals and digest stability.

The final capture and standalone-copy runs include the organized schema folders and declared layouts. All 10,055 files pass layout checks. Tests reject incorrect depth, family folders, state filenames, missing layout fields, malformed layout settings and files outside declared collections under the strict policy. Alternative field and collection names prove that these checks use Profile bindings. Both runs retain the purchase counts and relation results above.

`go test ./...`, `go test -race ./...`, `go vet ./...`, the binary build and `git diff --check` passed. This implementation does not require a C# build because it does not change the mod or game-model accesses.

Coverage remains explicit. All 10,055 files received collection schema and layout checks. The three singleton additions use only the basic model schema. There are still 1,340 model classes without detailed mechanic schemas, 503 Tower records outside ordinary progression and 20,345 checked unit values. These checks establish the declared structural, reference, layout and purchase requirements, not complete behavior interpretation or simulation.

The final Profile dependency closure contains 29 files with SHA-256 `d9d42176353ebda3215e0c8f45fe019afa33c6c489e07f64d385b7df7edec0ff`. Each report records the actual checker executable hash and build identity. Local reports and the mutation summaries are in ignored `bin/profile-*.json` files.
