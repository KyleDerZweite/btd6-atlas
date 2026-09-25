# Btd6Atlas mod (installable)

Reads the loaded real-match map and writes its geometry. Companion to Mod Helper's
Export Game Data button: run theirs first (static catalog), then ours (spatial layer).

## Build

Requires .NET 6 SDK, a Steam copy of BTD6, and MelonLoader + BTD Mod Helper installed
(their DLLs are referenced, never copied).

```sh
export BTD6_GAME_DIR="$HOME/.var/app/com.valvesoftware.Steam/data/Steam/steamapps/common/BloonsTD6"
dotnet build mod/Btd6Atlas.csproj
```

(Flatpak Steam on this machine; plain `~/.steam` does not exist here. dotnet runs
natively on Linux (only the path matters; Proton is irrelevant to the build).

## Install

With BTD6 closed, copy `mod/bin/Debug/net6.0/Btd6Atlas.dll` into the game's `Mods`
directory next to `Btd6ModHelper.dll`. No config, no startup work.

## Use

Two buttons, in Mods menu → BTD6 Atlas exporter settings:

1. **Export Atlas Data** writes the current map's geometry. Load a normal solo
   match first, pause, then export. Use Mod Helper's Export Game Data button
   beforehand for the static tower/enemy/round catalog.
2. **Export All Maps (auto)** walks every map through the normal game loader
   (Easy Sandbox) and exports each. Press once to arm, press again within
   60 seconds to confirm, then close Mod settings so the game sits on a
   clean main menu with no popups open (you have 5 minutes for that part). Takes a long time; do not touch
   the game while it runs.
   Any fault stops the run (restart BTD6 to retry); completed maps are kept.
   Start from the main menu with all popups dismissed.

Output lands in `<game>/Mods/Btd6AtlasExports/atlas-<map>-<timestamp>.json` plus
its SHA-256 in the MelonLoader log, with a success popup per file.
