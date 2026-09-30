# Profile project split

Updated 2026-09-30. The generic checker and Profile Template are published at [mardwerk/td-profile](https://github.com/mardwerk/td-profile). Atlas uses its released binary. The local Go checker, duplicate checker tests and Go module files have been removed.

Atlas retains the exporter, accepted captures, patterns and the BTD6 Profile. The Profile includes BTD6 settings, source structure contracts and local copies of the shared schemas. Keep those schema copies byte-identical to the pinned release. Every Profile dependency resolves inside `profile/`, without a neighboring checkout or network access during validation.

Propose Profile, shared schema and checker updates through a PR to td-profile. Adopt the released changes here after upstream review. Preserve BTD6 settings and source contracts when updating shared schemas; the generic Profile Template does not replace the BTD6 Profile. `scripts/derive-model-contracts.py` remains available for capture audits and candidate authoring. Derived candidates require Profile review through a td-profile PR.

Install the pinned [v1.0.2 release](https://github.com/mardwerk/td-profile/releases/tag/v1.0.2):

```sh
python3 scripts/install-validator.py
bin/validator --profile profile --game-data data/56.3-build-24829026/game-data
bin/validator score-tower --profile profile --game-data data/56.3-build-24829026/game-data --tower Towers/DartMonkey/DartMonkey.json
```

The release supplies checker `5.0.1` with interface `5`. Supported binaries are Linux amd64, Windows amd64 and macOS arm64. Windows uses `bin/validator.exe`. Compiled binaries remain in ignored `bin/`; running the checker requires no Go installation. Archive checksums identify released software, not game-data completeness.

The public td-profile release includes a Profile Template, an empty `game-data/` directory and a synthetic example. The empty directory passes with zero records. Its example receives a complete score of 100. Atlas supplies its own BTD6 Profile and local capture to the same checker. Validation and scores describe declared structural coverage, not simulation or balance.

Migration verification checks the native binary installation, equality of all shared schema copies, Dart scoring 100 and the unchanged full capture retaining only its known duplicate Boomerang purchase. A required state deletion in temporary game-data must fail and lower the Tower score. Keep accepted captures unchanged and record results below.

Verification passed on 2026-09-30. The published Linux archive installed successfully and all 25 schema copies matched. The cached installer also ran without downloading again. Installer tests cover all three archive targets and reject damaged archives, schema drift and incompatible interfaces while preserving the installed binary. Run them with `python3 scripts/test-install-validator.py`. The retained derivation script's doctests and `git diff --check` passed.

The released checker validated 10,053 files, 65,854 references and 482,492 model instances with zero unbound instances. Integrity passed. The sole error remains the accepted capture's duplicate Boomerang purchase. The BTD6 Profile revision, dependency digest and settings are unchanged.

Dart scored 100/100 with complete coverage across 99 files and 1,001 references. Deleting `DartMonkey-100.json` in a temporary copy produced `missing_reference`, `missing-build` and purchase errors, exited with code 1 and lowered its score to 83.11. The accepted capture and exporter were unchanged. Reports remain in ignored `bin/td-profile-*-report.json` files.
