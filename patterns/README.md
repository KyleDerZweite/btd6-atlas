# patterns/

Our derived analyses: the first thing that goes public. Analysis of data, never the
data itself.

Current patch: 56.3 (also recorded inside each JSON).

Files keep stable names across patches; only the content and the patch note
change:

- `towers.md`: roster, tiers, costs (tables in `../data/<patch>/towers.json`).
- `maps.md`: geometry by difficulty (tables in `../data/<patch>/maps.json`).
- `progression.md`: purchase structure.

Regenerate the JSON into the capture dir after a new export, then review and
update the markdown:

```sh
uv run scripts/analyze-towers.py [data/<patch-dir>]
uv run scripts/analyze-maps.py [data/<patch-dir>]
```

With no argument both scripts use the newest `data/*-build-*` directory.
Rewrite from captures; never copy game text verbatim.
