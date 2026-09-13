from __future__ import annotations

import argparse
import json

from .model import RoutingProfile
from .router import load_graph, route_graph


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="curbshade")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("route", help="route through a CurbShade graph")
    r.add_argument("graph")
    r.add_argument("source")
    r.add_argument("target")
    r.add_argument("--profile", choices=["walking", "wheelchair"], default="wheelchair")
    r.add_argument("--heat", type=float, default=0.0, help="heat intensity preference in [0,1]")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.command != "route":
        return 2

    profile = RoutingProfile.wheelchair() if args.profile == "wheelchair" else RoutingProfile.walking()
    result = route_graph(
        load_graph(args.graph),
        source=args.source,
        target=args.target,
        profile=profile,
        heat_intensity=args.heat,
    )
    print(json.dumps(result.as_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
