"use strict";

const network = {
  nodes: ["A", "B", "C", "D"],
  positions: {
    A: [90, 180],
    B: [295, 85],
    C: [295, 275],
    D: [510, 180]
  },
  edges: [
    { u:"A", v:"B", length_m:80, slope_pct:2, curb_cm:0, width_m:1.6, surface_score:.95, shade_fraction:.05, crossing_risk:.15 },
    { u:"B", v:"D", length_m:70, slope_pct:2, curb_cm:6, width_m:1.5, surface_score:.95, shade_fraction:.05, crossing_risk:.10 },
    { u:"A", v:"C", length_m:95, slope_pct:3, curb_cm:0, width_m:1.4, surface_score:.90, shade_fraction:.85, crossing_risk:.05 },
    { u:"C", v:"D", length_m:95, slope_pct:3, curb_cm:0, width_m:1.4, surface_score:.90, shade_fraction:.80, crossing_risk:.05 }
  ]
};

const profiles = {
  wheelchair: {
    max_slope_pct: 8.3, max_curb_cm: 2, min_width_m: .9, min_surface_score: .55,
    distance_weight: 1, heat_weight: .9, crossing_weight: .8, uncertainty_weight: 1.4
  },
  walking: {
    max_slope_pct: 18, max_curb_cm: 15, min_width_m: .5, min_surface_score: .25,
    distance_weight: 1, heat_weight: .8, crossing_weight: .5, uncertainty_weight: .45
  }
};

const critical = ["slope_pct","curb_cm","width_m","surface_score"];
const $ = (id) => document.getElementById(id);

function finiteNumber(value) {
  if (value === null || value === undefined || typeof value === "boolean") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function accessNumber(edge, key) {
  const value = finiteNumber(edge[key]);
  if (value === null) return null;
  if (key === "curb_cm" && value < 0) return null;
  if (key === "width_m" && value <= 0) return null;
  if (key === "surface_score" && (value < 0 || value > 1)) return null;
  return value;
}

function unitInterval(edge, key) {
  const value = finiteNumber(edge[key]);
  return value !== null && value >= 0 && value <= 1 ? value : null;
}

function evaluateEdge(edge, profile, heatInput) {
  const heat = Math.min(1, Math.max(0, Number(heatInput)));
  const length = finiteNumber(edge.length_m);
  if (length === null || length <= 0) return { traversable:false };

  const checks = [
    ["slope_pct", profile.max_slope_pct, (x,lim) => Math.abs(x) <= lim],
    ["curb_cm", profile.max_curb_cm, (x,lim) => x <= lim],
    ["width_m", profile.min_width_m, (x,lim) => x >= lim],
    ["surface_score", profile.min_surface_score, (x,lim) => x >= lim]
  ];

  for (const [key, limit, predicate] of checks) {
    const value = accessNumber(edge, key);
    if (limit !== null && value !== null && !predicate(value, limit)) {
      return { traversable:false };
    }
  }

  let uncertainty = critical.filter((key) => accessNumber(edge, key) === null).length / critical.length;
  let shade = unitInterval(edge, "shade_fraction");
  if (shade === null) {
    shade = 0;
    uncertainty = Math.min(1, uncertainty + .15);
  }
  const exposed = length * (1 - shade);

  let crossing = unitInterval(edge, "crossing_risk");
  if (crossing === null) {
    crossing = 0;
    uncertainty = Math.min(1, uncertainty + .10);
  }

  const cost =
      profile.distance_weight * length
    + profile.heat_weight * heat * exposed
    + profile.crossing_weight * crossing * length
    + profile.uncertainty_weight * uncertainty * length;

  return { traversable:true, cost, length, exposed, uncertainty };
}

function route(source, target, profileName, heat) {
  if (source === target) return { nodes:[source], cost:0, distance:0, exposed:0, uncertainty:0 };

  const profile = profiles[profileName];
  const adjacency = new Map(network.nodes.map((n) => [n, []]));
  for (const edge of network.edges) {
    const ev = evaluateEdge(edge, profile, heat);
    if (!ev.traversable) continue;
    adjacency.get(edge.u).push({ to:edge.v, ev });
    adjacency.get(edge.v).push({ to:edge.u, ev });
  }

  const dist = Object.fromEntries(network.nodes.map((n) => [n, Infinity]));
  const prev = {};
  const used = new Set();
  dist[source] = 0;

  while (used.size < network.nodes.length) {
    let current = null;
    let best = Infinity;
    for (const node of network.nodes) {
      if (!used.has(node) && dist[node] < best) {
        current = node;
        best = dist[node];
      }
    }
    if (current === null) break;
    if (current === target) break;
    used.add(current);
    for (const {to, ev} of adjacency.get(current)) {
      const candidate = dist[current] + ev.cost;
      if (candidate < dist[to]) {
        dist[to] = candidate;
        prev[to] = { node:current, ev };
      }
    }
  }

  if (!Number.isFinite(dist[target])) throw new Error("No traversable route for this profile.");

  const nodes = [target];
  let cursor = target;
  const evals = [];
  while (cursor !== source) {
    const step = prev[cursor];
    if (!step) throw new Error("No traversable route for this profile.");
    evals.push(step.ev);
    cursor = step.node;
    nodes.push(cursor);
  }
  nodes.reverse();
  evals.reverse();

  return {
    nodes,
    cost: evals.reduce((a,x) => a + x.cost, 0),
    distance: evals.reduce((a,x) => a + x.length, 0),
    exposed: evals.reduce((a,x) => a + x.exposed, 0),
    uncertainty: evals.length ? evals.reduce((a,x) => a + x.uncertainty, 0) / evals.length : 0
  };
}

function edgeKey(a,b) { return [a,b].sort().join("-"); }

function drawNetwork() {
  const edges = $("edges");
  const nodes = $("nodes");
  edges.replaceChildren();
  nodes.replaceChildren();

  for (const edge of network.edges) {
    const [x1,y1] = network.positions[edge.u];
    const [x2,y2] = network.positions[edge.v];
    const line = document.createElementNS("http://www.w3.org/2000/svg","line");
    line.setAttribute("x1",x1); line.setAttribute("y1",y1);
    line.setAttribute("x2",x2); line.setAttribute("y2",y2);
    line.setAttribute("class","edge");
    line.dataset.edge = edgeKey(edge.u,edge.v);
    edges.appendChild(line);
  }

  for (const node of network.nodes) {
    const [x,y] = network.positions[node];
    const group = document.createElementNS("http://www.w3.org/2000/svg","g");
    group.setAttribute("class","node");
    group.dataset.node = node;
    const circle = document.createElementNS("http://www.w3.org/2000/svg","circle");
    circle.setAttribute("cx",x); circle.setAttribute("cy",y); circle.setAttribute("r",28);
    const text = document.createElementNS("http://www.w3.org/2000/svg","text");
    text.setAttribute("x",x); text.setAttribute("y",y+1); text.textContent=node;
    group.append(circle,text);
    nodes.appendChild(group);
  }
}

function highlight(result) {
  document.querySelectorAll(".edge,.node").forEach((el) => el.classList.remove("active"));
  result.nodes.forEach((n) => document.querySelector('[data-node="'+n+'"]')?.classList.add("active"));
  for (let i=0;i<result.nodes.length-1;i++) {
    document.querySelector('[data-edge="'+edgeKey(result.nodes[i],result.nodes[i+1])+'"]')?.classList.add("active");
  }
}

function update() {
  try {
    const result = route($("source").value,$("target").value,$("profile").value,Number($("heat").value));
    $("route-path").textContent = result.nodes.join(" → ");
    $("distance").textContent = result.distance.toFixed(0) + " m";
    $("exposed").textContent = result.exposed.toFixed(0) + " m";
    $("uncertainty").textContent = (result.uncertainty*100).toFixed(0) + "%";
    $("cost").textContent = result.cost.toFixed(1);
    $("route-note").textContent =
      $("profile").value === "wheelchair"
        ? "Wheelchair mode removes segments that exceed the configured hard accessibility limits."
        : "Walking mode allows more segments, so heat can change which route is preferred.";
    highlight(result);
  } catch (err) {
    $("route-path").textContent = "No route";
    $("route-note").textContent = err.message;
  }
}

function init() {
  drawNetwork();
  for (const id of ["source","target"]) {
    const select = $(id);
    for (const node of network.nodes) {
      const option = document.createElement("option");
      option.value = node; option.textContent = node;
      select.appendChild(option);
    }
  }
  $("source").value = "A";
  $("target").value = "D";
  $("heat").addEventListener("input", () => {
    $("heat-value").textContent = Number($("heat").value).toFixed(2);
    update();
  });
  $("profile").addEventListener("change", update);
  $("source").addEventListener("change", update);
  $("target").addEventListener("change", update);
  $("route-form").addEventListener("submit", (event) => { event.preventDefault(); update(); });
  update();
}
document.addEventListener("DOMContentLoaded", init);
