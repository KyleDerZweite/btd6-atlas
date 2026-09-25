# Agent instructions (btd6-atlas)

Independent BTD6 fan project. Not affiliated with Ninja Kiwi.

## Layout

- `mod/`: the installable exporter (C#). Build with `dotnet build mod/Btd6Atlas.csproj`
  and `BTD6_GAME_DIR` set. First build on a new machine is the real test.
- `data/`: accepted captures per game patch. Empty until the first export run.
- `patterns/`: our derived analyses. First thing that goes public.
- `docs/`: workflow plans. Keep them shorter than the code.

## Rules

1. Never invent Il2Cpp API shapes. Every game-model access must match a compiled
   reference (Mod Helper sources or a successful local build).
2. The mod reads the loaded game and writes JSON. No scene loading outside the
   confirmed auto mode, no progression writes, no network calls. Ever.
3. Raw exports stay local until a data policy is recorded. Patterns go public first.
4. Record every capture's game version, build id, exporter version and hashes.
