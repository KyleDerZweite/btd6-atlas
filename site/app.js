"use strict";
/* Renders data/towers.json, data/maps.json and searches index.json.
   No dependencies. Charts are div bars styled in style.css. */
const DIFF_BLOON = { Beginner: "blue", Intermediate: "green", Advanced: "yellow", Expert: "red" };
const state = { towers: null, maps: null, index: [], setFilter: "all", diffFilter: "all" };

const fmt = (n) => n == null ? "?" : (Number.isInteger(n) ? n.toLocaleString("en-US") : n);
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text != null) node.textContent = text;
  if (cls) node.className = cls;
  return node;
};
const extIcon = '<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>';

async function loadJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(path);
  return res.json();
}

function barChart(host, rows) {
  host.replaceChildren();
  const max = Math.max(...rows.map((r) => r.value), 1);
  for (const row of rows) {
    const line = el("div", null, "bar");
    line.append(el("span", row.label));
    const track = el("div", null, "track");
    const fill = el("div", null, "fill");
    fill.style.width = `${(row.value / max * 100).toFixed(1)}%`;
    track.append(fill);
    line.append(track, el("span", fmt(row.num == null ? row.value : row.num), "num"));
    host.append(line);
  }
}

function tier5max(tower) {
  let best = 0;
  for (const path of tower.paths || [])
    for (const tier of path.tiers || [])
      if (tier.tier === 5 && typeof tier.cost === "number") best = Math.max(best, tier.cost);
  return best;
}

function renderTowers() {
  const data = state.towers;
  document.getElementById("patch").textContent = `patch ${data.patch}`;
  const std = data.standardTowers, heroes = data.heroes;
  const paras = std.filter((t) => t.hasParagon).length;
  const chips = document.getElementById("stat-towers");
  chips.replaceChildren(
    ...[[std.length, "standard"], [heroes.length, "heroes"], [paras, "paragons"],
        [78, "paths"], [63, "crosspaths each"]].map(([n, label]) => {
      const s = el("span"); const b = el("b", String(n)); s.append(b, ` ${label}`); return s;
    }));
  const bands = data.upgradeCostBands;
  barChart(document.getElementById("chart-tiers"),
    [1, 2, 3, 4, 5].map((t) => ({ label: `Tier ${t}`, value: Math.log10(bands[`path1-tier${t}`].median), num: bands[`path1-tier${t}`].median })));
  const sets = ["all", ...new Set(std.map((t) => t.set))];
  const filters = document.getElementById("set-filters");
  filters.replaceChildren(...sets.map((s) => {
    const b = el("button", s, s === state.setFilter ? "active" : "");
    b.onclick = () => { state.setFilter = s; renderTowers(); };
    return b;
  }));
  const body = document.querySelector("#tbl-towers tbody");
  body.replaceChildren(...std.filter((t) => state.setFilter === "all" || t.set === state.setFilter)
    .map((t) => {
      const tr = document.createElement("tr");
      tr.append(...[t.id, t.set, fmt(t.cost), fmt(t.range), t.hasParagon ? "yes" : "no", fmt(tier5max(t))]
        .map((v) => el("td", v)));
      return tr;
    }));
  const hb = document.querySelector("#tbl-heroes tbody");
  hb.replaceChildren(...heroes.map((h) => {
    const tr = document.createElement("tr");
    tr.append(...[h.id, fmt(h.cost), fmt(h.levelCosts.reduce((s, l) => s + (l.xpCost || 0), 0))]
      .map((v) => el("td", v)));
    return tr;
  }));
}

function renderMaps() {
  const data = state.maps;
  const groups = data.byDifficulty;
  const order = ["Beginner", "Intermediate", "Advanced", "Expert"].filter((d) => groups[d]);
  const cards = document.getElementById("diff-cards");
  cards.replaceChildren(...order.map((name) => {
    const g = groups[name], card = el("div", null, "card");
    const row = el("div", null, "row");
    const bloon = el("span", null, `bloon bloon-${DIFF_BLOON[name] || "blue"}`);
    bloon.setAttribute("aria-hidden", "true");
    row.append(bloon, el("span", `${name} (${g.n})`));
    const dl = document.createElement("dl");
    for (const [k, v] of [["Longest track", g.trackFullLongestAvg], ["Routes", g.fullRoutesAvg],
        ["Entrances", g.entrancesAvg], ["Water share", g.waterShare], ["Blockers", g.blockersAvg]])
      dl.append(el("dt", k), el("dd", String(v)));
    card.append(row, dl);
    return card;
  }));
  barChart(document.getElementById("chart-tracks"),
    order.map((name) => ({ label: name, value: groups[name].trackFullLongestAvg })));
  const filters = document.getElementById("diff-filters");
  filters.replaceChildren(...["all", ...order].map((d) => {
    const b = el("button", d, d === state.diffFilter ? "active" : "");
    b.onclick = () => { state.diffFilter = d; renderMaps(); };
    return b;
  }));
  const body = document.querySelector("#tbl-maps tbody");
  body.replaceChildren(...data.entries.filter((e) => state.diffFilter === "all" || e.difficulty === state.diffFilter)
    .map((e) => {
      const tr = document.createElement("tr");
      tr.append(...[e.mapId, e.difficulty, e.trackFullLongest, e.fullRoutes, e.entrances,
        e.hasWater ? "yes" : "no", e.blockers].map((v) => el("td", fmt(v))));
      return tr;
    }));
}

function renderSearch(query) {
  const box = document.getElementById("results");
  query = query.trim().toLowerCase();
  if (query.length < 2 || !state.index.length) { box.hidden = true; box.replaceChildren(); return; }
  const hits = state.index.filter((e) => e.id.toLowerCase().includes(query)).slice(0, 30);
  box.hidden = false;
  box.replaceChildren();
  if (!hits.length) { box.append(el("p", "No matches.")); return; }
  const groups = {};
  for (const hit of hits) (groups[hit.type] ||= []).push(hit);
  for (const [type, items] of Object.entries(groups)) {
    box.append(el("h3", `${type} (${items.length})`));
    const ul = document.createElement("ul");
    for (const item of items) {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = item.url; a.target = "_blank"; a.rel = "noopener";
      a.textContent = item.id;
      li.append(a);
      li.insertAdjacentHTML("beforeend", extIcon);
      if (item.facet) li.append(el("span", item.facet, "tag"));
      ul.append(li);
    }
    box.append(ul);
  }
}

function switchView(name) {
  for (const btn of document.querySelectorAll("nav button")) {
    const on = btn.dataset.view === name;
    btn.classList.toggle("active", on);
    if (on) btn.setAttribute("aria-current", "page"); else btn.removeAttribute("aria-current");
  }
  for (const section of document.querySelectorAll("main > section"))
    section.hidden = section.id !== `view-${name}`;
}

async function main() {
  for (const btn of document.querySelectorAll("nav button"))
    btn.onclick = () => switchView(btn.dataset.view);
  document.getElementById("q").addEventListener("input", (e) => renderSearch(e.target.value));
  try {
    const [towers, maps] = await Promise.all([loadJSON("data/towers.json"), loadJSON("data/maps.json")]);
    state.towers = towers; state.maps = maps;
    renderTowers(); renderMaps();
  } catch { /* tables stay empty when data is not built yet */ }
  try {
    state.index = await loadJSON("index.json");
  } catch { /* search stays disabled */ }
  document.getElementById("stat-prog").replaceChildren(
    ...[["63", "crosspaths each"], ["0", "rule violations"], ["6.15", "median final ratio"], ["25/26", "middle ability"]]
      .map(([n, label]) => { const s = el("span"); const b = el("b", n); s.append(b, ` ${label}`); return s; }));
}

main();
