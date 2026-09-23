# CurbShade

**Routes that are not only short, but actually traversable and less heat-exposed.**

CurbShade is an uncertainty-aware pedestrian and wheelchair router. It combines sidewalk accessibility attributes (curbs, slope, width, surface and crossing risk) with segment-level shade exposure, then routes on a graph without making the dangerous assumption that missing data means "accessible".

## The problem

Most route planners optimize distance or travel time. For a wheelchair user, an apparently minor curb or steep ramp can make the shortest route impossible. During extreme heat, a slightly longer shaded route can also be materially better than an exposed one.

The harder problem is missing data. A routing engine should not silently treat an unmapped curb, slope or surface as safe. CurbShade therefore makes **uncertainty a first-class routing cost**.

## What works now

- JSON graph input with accessibility and shade metadata
- walking and wheelchair profiles
- hard barriers for profile limits
- uncertainty penalty for missing safety-critical fields
- thermal exposure cost weighted by current heat intensity
- NetworkX shortest-path routing
- route metrics and explanations
- command-line interface
- deterministic synthetic example
- unit tests and GitHub Actions

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

curbshade route examples/demo_network.json A D --profile wheelchair --heat 1.0
```

Expected result: CurbShade avoids the geometrically shorter route when it contains a wheelchair barrier, and prefers the more shaded accessible path.

## Input format

```json
{
  "nodes": [{"id": "A"}, {"id": "B"}],
  "edges": [{
    "u": "A",
    "v": "B",
    "length_m": 50,
    "slope_pct": 2.0,
    "curb_cm": 0.0,
    "width_m": 1.8,
    "surface_score": 0.95,
    "shade_fraction": 0.75,
    "crossing_risk": 0.1
  }]
}
```

`shade_fraction` and `surface_score` are in `[0, 1]`. Missing accessibility attributes are allowed, but they increase uncertainty rather than being interpreted as safe.

## Cost model

For a traversable edge:

```text
cost =
    distance_weight * length
  + heat_weight * heat_intensity * exposed_length
  + crossing_weight * crossing_risk * length
  + uncertainty_weight * unknown_fraction * length
```

Edges that violate hard profile limits receive infinite cost.

This is intentionally transparent. CurbShade is not claiming a medical heat model or universal accessibility standard. The weights are routing preferences that should be calibrated and validated locally.

## Three-repository layout

- **CurbShade** — routing engine and CLI
- **CurbShade-data** — OSM/OpenSidewalks-compatible ingestion and enrichment
- **CurbShade-benchmarks** — reproducible route-quality benchmark cases

## Open-source components combined

CurbShade is designed around existing open ecosystems rather than inventing a new mapping universe:

- **NetworkX** — graph representation and shortest-path algorithms.
- **OpenStreetMap / OSMnx** — baseline street/pedestrian network extraction in `CurbShade-data`.
- **OpenSidewalks** — compatibility target for explicit sidewalk, curb and pedestrian-network semantics.
- **Project Sidewalk** — a potential external source of audited accessibility observations for future validation/enrichment.

No OpenSidewalks schema file or Project Sidewalk code is copied into this repository. Their licenses and data terms remain independent.

## Why uncertainty matters

Suppose two routes are equally short. One has fully mapped curb and slope information. The other has no curb or slope data. A conventional router may treat them as equivalent. CurbShade prefers the route with evidence.

For safety-critical deployment, "unknown" should never be conflated with "safe".

## Limitations

This is an engineering prototype, not a certified accessibility or emergency navigation system. Real deployments need verified local curb and sidewalk data, time-dependent shade estimates, local accessibility rules, field validation with wheelchair users and pedestrians, weather/heat calibration, and live construction/obstruction data.

## Related repositories

- https://github.com/davidmariscalf/CurbShade-data
- https://github.com/davidmariscalf/CurbShade-benchmarks

## License

MIT for CurbShade code. External data and dependencies retain their own licenses. OpenStreetMap-derived databases are subject to ODbL requirements.

## Netlify web demo

The repository includes a static interactive demo under `site/`. The browser implementation mirrors the current Python edge-cost model against the bundled demo network, including mobility-profile barriers, heat exposure, crossing risk and uncertainty penalties.

Netlify configuration is committed in `netlify.toml`:

- publish directory: `site`
- no build command is required
- static security headers are configured at the edge

To deploy from GitHub, import this repository in Netlify and let Netlify read `netlify.toml`; no additional build settings are required. For a manual drag-and-drop deploy, upload the contents of `site/` (the demo works statically, although repository-level Netlify headers require deploying from the repository config).
