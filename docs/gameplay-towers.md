# Gameplay Tower JSON

Issue [#2](https://github.com/KyleDerZweite/btd6-atlas/issues/2) moves reusable BTD6 cleanup into Atlas.
Tower Generator owns its BTD6 Profile and Profile Validator.

The reviewed design uses one complete JSON per eligible Tower, with source attribution, Tower identity, 15 upgrade definitions, and 64 explicit ordinary states.
Each state comes from its captured model and retains its purchase links and gameplay mechanics.
Paragons stay outside this format.

Run `python3 scripts/export-gameplay-towers.py` from the repository root.
The script reads the latest capture at one recorded Git revision and writes `data/<capture>/gameplay-towers/<tower>.json`.
It resolves data and output paths relative to the script, so an absolute script path also works from another directory.
Use `--tower DartMonkey` to regenerate one family for inspection.
Raw captures remain unchanged.
Progress, skips, and errors appear only in the terminal.

Use direct projections of captured gameplay fields and explicit removal of known presentation models.
Confirm enum values and model fields against the installed game references before translating them.
Reject unsupported gameplay models rather than emit incomplete Towers.
Keep the script self-contained and use the Python standard library.

The all-family scan requires specialized mechanics as well as the common attack models.
Represent reviewed mechanics as named effects and retain their captured parameters after translating common fields.
The compiled-reference audit matched every inspected model type and serialized member, including inherited members.
The reference assembly SHA-256 is `52a95679f457f9f105caa751672b845b14f7fa89292d4369e13a3f4998d3f653`.
This format describes captured models; it does not recreate the game's simulation or infer undocumented trigger rules.

Record the game version, build, exporter versions, Atlas revision, relative source paths, and SHA-256 hashes.
Read the manifest and model files from that same revision, including when the working tree has edits.
Record the converter's hash separately so local converter changes remain identifiable.

The first review verified capture 56.3, build 24829026, at Atlas commit `a380413ed809c98654acec7aa37cba40f80bf5c5`.
Dart Monkey has 64 ordinary states, 15 upgrades, and 111 valid single-purchase links.
Every raw state repeats the base cost of 200; purchase costs come from the upgrade definitions.
Upgrade definitions use zero-based indices, while state tiers count attained upgrades.

Use structured mechanics rather than descriptive text.
Plasma Fan Club's description says 40 monkeys and 10 seconds, while the model fields say 20 monkeys and 15 seconds.
Retain conditional modifier references without applying difficulty or Monkey Knowledge adjustments to the baseline.

Verify Dart's base attack, triple emission, critical hits, rebound projectiles, child-projectile triggers, and both Fan Club abilities.
Then run against every family and inspect the generated files, source hashes, links, ordering, and unsupported cases.
Keep checks inside the converter and use direct inspection instead of a separate test suite.

The approved scope now includes running every family immediately after implementation.
It does not add a Profile schema, validator, network importer, or generalized conversion framework.

The output contains `formatVersion`, `source`, `tower`, `upgrades`, `states`, and `additionalModels`.
Upgrade paths and attained tiers use numbers 1 through 3 and 1 through 5 respectively.
State keys contain the three attained tiers, such as `000` and `502`.
Each state groups placement, targeting, attacks, abilities, and other effects, with explicit next purchases and baseline total cost.

Additional non-Paragon family models retain transformations and reinforcement actors without counting them as ordinary states.
Alchemist has three such models; Heli Pilot has one.
Nested actors retain their identity and entity flags, and referenced model IDs remain available for named relationships.

Effects use readable `kind` values and retain captured gameplay parameters.
Weapon intervals, duration, cooldown, and travel speed have explicit units; distances use game units.
Nonzero native frame counts remain frame counts, and zero derived frame caches are omitted.
Firing offsets and timing remain because they can affect projectile origin or attack behavior.
Conditional modifier references remain unapplied, and specialized parameters keep their source meaning.

The converter validates every ordinary state, applied upgrade, purchase link, and upgrade definition before replacing a Tower file.
Identical repeated purchase links collapse to one link, and both targeting fields remain when their configured and resolved values differ.
It finds upgrade definitions by their recorded names because export filenames can omit punctuation.
Unknown models, unknown immunity flags, incomplete families, and conflicting source definitions cause terminal skips.
An unsuccessful family leaves any previously generated file intact.

Validation on 2026-09-29 checked 1,600 ordinary states, 375 upgrades, 2,775 purchase links, and 1,980 unique source hashes.
Dart's complex mechanics matched the captured values, and regeneration from another working directory produced identical files.
Direct checks also confirmed rejection of unreviewed models and unknown immunity flags.
