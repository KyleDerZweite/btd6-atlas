# Tower patterns (patch 56.3)

Derived from `data/56.3-build-24829026/game-data/Towers` (94 entities, 2167
files) and `game-data/Upgrades` (790 tier records). Full per entity tables are
in `towers.json`. Amounts are Medium list prices unless noted.

## Roster shape

- 26 standard towers: 3 upgrade paths, 5 tiers each. Sets split 7 primary,
  7 military, 7 magic, 5 support.
- 18 heroes: base placement plus 20 levels. Levels cost XP, never cash.
  Total XP to level 20 ranges 213560 to 365190, median 304329.
- 13 of the 26 standard towers have a paragon form recorded.
- 41 sub entities (pets, summons, parts, transformed states), 5 power items,
  3 beast pets, 1 single file hero set entity.
- Tower sets are bit flags: 1 primary, 2 military, 4 magic, 8 support,
  16 hero, 64 power.

## Crosspath law, verified on all 26

- Every standard tower exposes exactly 63 purchasable crosspaths.
- Zero violations of the build rule: at most two paths per build, at most
  one path above tier 2, and a tier 5 caps its sibling paths at tier 2.
- Special cases ride along inside the same structure: one tower ships extra
  transform target files, one ships an extra companion file.

## Price shape

- Base costs: primary 200 to 400, military 325 to 1500, magic 205 to 2500,
  support 250 to 1250. Base range 20 to 60 (median 40), footprint 6 to 11.
- Tier medians across the roster: tier 1 about 200 to 275 per path, tier 3
  about 1500 to 2000, tier 4 about 4000 to 6500, tier 5 about 30000 to 38000.
- Final to previous tier ratio per path: min 1.58, median 6.15, max 19.64
  across all 78 paths. Ratios describe single purchases, not builds, and do
  not imply output multipliers.

## Attack readout coverage

- Base attack cadence extracted for 22 of 26 standards; damage for 16.
  Damage lives in nested projectile behaviors, so per tier DPS modeling is
  future work, not part of this pattern.
- Middle path tier 4 carries an ability behavior in 25 of 26 standards and
  persists it at tier 5. Top and bottom tier 4 show 1 each. Exceptions are
  listed per tower in the JSON.
