# Map patterns (patch 56.3)

Derived from `data/56.3-build-24829026/atlas-maps` (89 maps) joined with the
static difficulty in `game-data/Maps`. Lengths are game units measured along
exported route polylines. Full per map tables are in `maps.json`.

## Difficulty comes from track structure, not canvas size

Average canvas is nearly flat across difficulties (about 440 by 350), so
harder maps are not smaller maps.

| Difficulty | Maps | Longest route avg | Full routes avg | Multi route maps |
| --- | --- | --- | --- | --- |
| Beginner | 26 | 1374.5 | 1.5 | 2 |
| Intermediate | 26 | 998.4 | 2.2 | 18 |
| Advanced | 23 | 748.1 | 3.2 | 17 |
| Expert | 14 | 466.7 | 3.8 | 12 |

- Longest usable track falls monotonically with difficulty while route,
  entrance and exit counts rise. Expert maps split pressure across about
  four short lanes; beginner maps run one long lane.
- Entrance and exit counts track full route counts almost exactly, so lane
  counting is a usable difficulty proxy.

## Secondary observations

- Water presence is common everywhere (share 0.57 to 0.92), highest outside
  Advanced. Placement restriction shape varies more than water share.
- Blocker counts average about 90 to 105 except Advanced at about 155.
  Circles are 24 point approximations, declared per file.
- Splitter junctions are rare: full route counts differ from raw route
  counts only on a handful of expert maps.
- Declared non projections everywhere: co-op layouts, map events, and the
  circle approximation above. BaseEditorMap has no atlas file (editor
  template, not loadable); every other catalog map does.
