# Profile implementation

Implement on `feat/profile-rule-validation`. The user approved Atlas ownership of the Profile and semantic checker on 2026-09-30. This supersedes the earlier ownership statement in `docs/game-profile.md`.

Keep captured fields and `$type` unchanged. The Profile contains reusable schemas, bindings, units and rule parameters. Capture records, versions and hashes remain under `data/`.

Split model schemas by responsibility, including `tower.schema.json`, `mechanics.schema.json` and `mechanic-proposal.schema.json`. Resolve dependencies from the Profile directory without network access. Validate every Profile document before checking records.

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

`go test ./...`, `go test -race ./...`, `go vet ./...`, the binary build and `git diff --check` passed. This implementation does not require a C# build because it does not change the mod or game-model accesses.

Coverage remains explicit. Three files have no collection schema, 1,340 encountered model classes lack detailed mechanic schemas, and 503 Tower records are outside ordinary progression. Native unit bindings checked 20,345 values. This establishes the declared structural, reference and purchase checks, not complete behavior interpretation or simulation.

The Profile dependency closure contains 29 files with SHA-256 `b83f1413b49f0d0f4c66153450bb6169467fbfd23177d923dbcac8aa75c654e4`. Each report records the actual checker executable hash and build identity. Local reports and the mutation summary are in ignored `bin/profile-*.json` files.
