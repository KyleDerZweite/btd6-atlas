# Handoff: btd6-atlas

Independent BTD6 fan mod project: map-geometry exports plus indexed data storage
and derived patterns. Companion to Mod Helper's static Export Game Data, which it
does not replace.

## Current state (2026-09-25)

The `mod/` exporter compiles clean (`dotnet build`, net6.0) against the local
BTD6 assemblies and is installed in the Steam game dir (`Mods/Btd6Atlas.dll`).
It has never been launched in game. That is the next step.

## Layout

- `mod/`: `AtlasExporter.cs` (two buttons), `Dtos.cs` (geometry DTOs),
  `Btd6Atlas.csproj` (references via `BTD6_GAME_DIR`), `README.md` (build/install/use).
- `data/`: empty. Accepted captures go to `data/<game-version>-build-<steam-build>/`.
- `patterns/`: empty. Derived analyses go here first; they are the first public content.
- `docs/`: `mod.md`, `data.md`, `patterns.md` (short plans).
- `AGENTS.md`, `LICENSE` (MIT, code), `NOTICE` (non-affiliation, CC BY-NC data).

## Environment (this machine)

- Game: `~/.var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/BloonsTD6`
  (Flatpak Steam; no `~/.steam` here). Steam build 24829026 at last check.
- Build: `export BTD6_GAME_DIR=<that path>` then `dotnet build mod/Btd6Atlas.csproj`.
  dotnet runs natively on Linux; Proton is irrelevant to the build.
- Old `MardwerkReferenceExporter.dll` was removed from `Mods/` when Btd6Atlas.dll
  was installed. Keep it to one exporter.

## The mod's two buttons

1. Export Atlas Data: manual, current paused solo map only.
2. Export All Maps (auto): two-step confirm (arm, press again within 60s), walks
   the catalog through the normal Easy Sandbox loader, fault stops the run until
   restart, completed maps are kept. Start from the main menu, popups dismissed.

Output: `<game>/Mods/Btd6AtlasExports/atlas-<map>-<timestamp>.json` plus SHA-256
in the MelonLoader log. Known partials are declared per file in `unsupported`
(splitters, coop layouts, map events, circle approximation).

## Rules that already apply

- No em dashes in files or messages. Ever.
- No references to any other project by name in this repo. It stands alone.
- Every game-model access must match a compiled reference. The first build on a
  new machine (or after a game update) is the real test.
- The mod only reads and writes JSON. No progression writes, no network calls.
- Raw exports stay local until a data policy is recorded. Patterns go public first.
- Provenance for every capture: game version, build id, exporter version, hashes.

## Suggested next actions

1. Launch the game, one manual export, verify the JSON against the loaded map.
2. Arm the auto run and walk away; collect outputs into `data/<patch>/`.
3. Write the first pattern from real captures.
4. Push to GitHub (repo does not exist yet; local git only) when data exists.
