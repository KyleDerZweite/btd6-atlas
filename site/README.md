# site/

Static GitHub Pages front end for the patterns. No dependencies: one HTML
file, one stylesheet, one vanilla script, plus generated payloads.

- Source: `index.html`, `style.css`, `app.js` (icons are inlined Lucide paths).
- Generated, never hand edited: `data/towers.json`, `data/maps.json`,
  `index.json` (search index linking to raw capture files on GitHub).

Refresh after a new capture (manual action):

```sh
uv run scripts/build-site.py [data/<patch-dir>]
```

Review the diff, commit, push. Hosting: repo Settings, Pages, deploy from
branch `main`, folder `/site`. The per patch numbers in the Progression tab
are hand written; update them alongside `patterns/progression.md`.
