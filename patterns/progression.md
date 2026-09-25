# Progression patterns (patch 56.3)

Purchase structure distilled from the full tower capture. Earlier web
research (September 2026, 26 towers) proposed most of these claims; every
number below was rechecked against all 26 standard towers, 18 heroes and
78 upgrade paths in this patch. See `towers.json` for the tables.

## Tier roles

- Tiers 1 and 2 build a foundation that stays useful as a crosspath. Early
  tiers are not limited to numeric boosts: secondary attacks, track effects,
  deployable actors and collection conveniences all appear at tier 1 or 2.
  The rule is a small focused early kit, not one effect per row.
- Tier 3 is the commitment point: only one path may pass tier 2, so the
  tier 3 choice fixes the advanced branch. Verified by zero build rule
  violations across all 1638 crosspath records.
- Tier 4 pays off the branch and tier 5 extends it, usually along the same
  axis (coverage, permanence, control eligibility) rather than by stacking
  the other branches. A tier 5 does not combine all three paths.
- Middle path tier 4 introduces a manual ability in 25 of 26 towers and
  tier 5 retains it. Top and bottom tier 4 show exactly 1 each. This is a
  strong template with named exceptions, not a universal law.

## Legality and economy

- Legal builds use at most two paths with at most one above tier 2.
- Final to previous tier purchase ratios: min 1.58, median 6.15, max 19.64
  across 78 paths. Ratios describe single purchases and do not establish
  output multipliers, affordability or balance.
- Heroes progress on XP (213560 to 365190 total, median 304329), never on
  cash upgrades. Paragons sit outside the crosspath system.

## Authoring checks derived from the above

- Reject duplicate early purchases by comparing resolved mechanic deltas,
  not names. Shared parameter dimensions with different scope or magnitude
  are not duplicates.
- Require each path to state a different deployment reason. Distinct role
  labels alone prove nothing.
- Judge capstones on their declared branch axis with measured deltas.
  Never demand invented damage to pass a support or economy capstone.
- Count independent manual activations per legal build. One manual boost
  path is the common shape; a second needs its own purpose.
- Treat automatic, triggered, activated, configuration and collection
  behavior as separate kinds. A cooldown alone does not make an effect
  manual; targeting and mode selection are configuration.
