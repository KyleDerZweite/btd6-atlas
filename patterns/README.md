# patterns/

Our derived analyses: the first thing that goes public. Analysis of data, never the
data itself.

Current patch: 56.3 (also recorded inside each JSON).

Files keep stable names across patches; only the content and the patch note
change:

- `towers.json` (generated) and `towers.md`: roster, tiers, costs.
- `maps.json` (generated) and `maps.md`: geometry by difficulty.
- `progression.md`: purchase structure.

Regenerate the JSON after a new capture, then review and update the markdown:

```sh
uv run scripts/analyze-towers.py [data/<patch-dir>]
uv run scripts/analyze-maps.py [data/<patch-dir>]
```

With no argument both scripts use the newest `data/*-build-*` directory.
Rewrite from captures; never copy game text verbatim.
