# Separate Profile project

Proposal, 2026-09-30. Continue the current implementation in Atlas. No repository move or new remote is part of this proposal.

A separate project makes sense. Atlas collects BTD6 data; the validator and shared schemas also serve other games. Keep two repositories initially. A separate repository for every Profile document or schema would add coordination without helping this use case.

## Ownership and layout

Use `td-profile` as a working project name. `/home/kyle/CodingProjects` exists with that spelling, so a future checkout could live at `/home/kyle/CodingProjects/td-profile`. `mardwerk/td-profile` is a possible future remote; its availability has not been checked.

```text
td-profile/
  cmd/atlas-validator/
  internal/atlasvalidate/
  profile/
    manifest.json
    collections.json
    mechanics.json
    rules.json
    references.json
    numerical-units.json
    scoring.json
    schemas/
      profile/
      game-data/
  game-data/
    .gitkeep
  examples/
    minimal-game/
  docs/
  go.mod
```

Keep the established `atlas-validator` binary name at first. A repository rename does not require users to change their commands. Move the existing package and its tests together. Keep the package internal until another Go application actually needs an importable library.

The root `profile/` becomes the base Profile. It uses generic source names such as `kind`, `id`, `familyId` and `placementPrice`. It includes the same reusable `tower.schema.json`, `mechanics.schema.json` and `mechanic-proposal.schema.json` used by game Profiles. Its settings define a small documented starting contract. They do not pretend to express every possible tower-defense mechanic.

Atlas retains `mod/`, captures, patterns and the BTD6 Profile configuration. Its Profile includes a pinned copy of the shared schemas. A release update copies that exact schema version and verifies the BTD6 bindings against it. This preserves the existing requirement that every Profile resolves locally without network access or parent-directory dependencies. Avoid Git submodules and runtime Profile inheritance for the first split.

## An empty game that passes

Declare enabled collections for Towers, enemies, upgrades and other supported record kinds. Allow each collection to contain zero records. Keep schemas, unknown-model errors, reference checks and applicable progression rules enabled. Conditional dependencies become required when records use them.

An empty directory can then pass because no records violate the contract. It does not receive a Tower score or establish that a playable game exists. The report should say zero files and zero applicable checks. Git needs a `.gitkeep` to retain the directory; the release archive can contain an actually empty directory.

Keep a small synthetic game under `examples/`, separate from the empty directory. Release checks should prove that the empty game passes, the example passes, and a missing required dependency or progression state fails. Unknown mechanics and malformed records must still fail. The base progression policy should be an explicit starter choice, with BTD6's three-path limits remaining in its own settings.

## Ship a matching binary and Profile

Publish downloadable release archives containing the executable and a self-contained Profile. Keep compiled binaries out of Git.

```text
td-profile-<release>-<os>-<architecture>/
  atlas-validator
  profile/
  game-data/
  README.md
  LICENSE
  release.json
```

Build separate archives for supported operating systems and architectures. Windows uses `atlas-validator.exe`; Linux and macOS builds use their native executable. Start with Linux amd64, Windows amd64 and macOS arm64, then add targets with actual users and release tests. Every advertised target needs its own build and smoke test.

`release.json` should record the checker version, checker interface version, Profile revision, source commit and build target. Publish archive checksums alongside releases. These identify distributed software and configuration, not an inventory of game-data files.

Version the checker and Profile independently. A checker bug fix need not change a game's rules; a Profile rule change need not change the executable. The existing manifest interface version controls compatibility, and the bundle pins an exact tested pair. Existing validation reports already record the checker identity and Profile digest.

The base release contains no BTD6 exports. A BTD6 bundle can combine the same binary with the BTD6 Profile and an empty `game-data/` directory. Atlas users supply their local capture. Keep current source notices when moving files and separate the generic project's code license from BTD6 data notices.

## Extraction order

1. Finish and test the current BTD6 contract here.
2. Build the base Profile and synthetic example here, proving shared schemas work without BTD6 settings.
3. Move the validator, reusable schemas and generic tests into the new project. Move BTD6 integration tests with the BTD6 configuration owner.
4. Add release bundles and verify them from an extracted archive outside either checkout.
5. Replace Atlas's validator source with commands that use the pinned release. Keep its BTD6 Profile independently editable.

The current code supports this boundary: `cmd/atlas-validate/main.go` delegates to `internal/atlasvalidate`, and portability tests already reuse identical schemas across different source-field conventions. There is no release workflow yet. The base Profile, bundle builder and extraction remain proposed work.
