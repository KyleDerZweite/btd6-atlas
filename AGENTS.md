# Agent instructions (btd6-atlas)

Independent BTD6 fan project. Not affiliated with Ninja Kiwi.

## Layout

- `mod/`: the installable exporter (C#). Build with `dotnet build mod/Btd6Atlas.csproj`
  and `BTD6_GAME_DIR` set. First build on a new machine is the real test.
- `data/`: accepted captures per game patch.
- `patterns/`: our derived analyses. First thing that goes public.
- `docs/`: workflow plans. Keep them shorter than the code.
- `profile/`: BTD6 settings, source contracts and pinned copies of the reusable schemas. Preserve raw field names and `$type`.
- `profile/validator`: the shipped Linux amd64 [td-profile](https://github.com/mardwerk/td-profile) binary. `python3 scripts/install-validator.py` replaces it for supported native platforms. Track upstream binaries, identity and licenses alongside the Profile.

## Rules

1. Never invent Il2Cpp API shapes. Every game-model access must match a compiled
   reference (Mod Helper sources or a successful local build).
2. The mod reads the loaded game and writes JSON. No scene loading outside the
   confirmed auto mode, no progression writes, no network calls. Ever.
3. Raw exports stay local until a data policy is recorded. Patterns go public first.
4. Record every capture's game version, build id, exporter version and hashes.
5. If the Profile, shared schemas or validator need an update, propose it in a PR
   to [td-profile](https://github.com/mardwerk/td-profile). Adopt released changes
   here. Keep BTD6 bindings and source contracts local, and shared schemas identical
   to the pinned release. Do not restore a local checker implementation.
6. After changing the validator release or Profile, validate the accepted capture
   and score Dart with `profile/validator`. Check a missing required dependency in a
   disposable copy. Preserve the accepted capture and record actual coverage.
