from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

import networkx as nx

from .model import RoutingProfile, evaluate_edge


@dataclass(frozen=True)
class RouteResult:
    nodes: list[str]
    cost: float
    distance_m: float
    exposed_m: float
    mean_uncertainty: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "nodes": self.nodes,
            "cost": round(self.cost, 3),
            "distance_m": round(self.distance_m, 3),
            "exposed_m": round(self.exposed_m, 3),
            "mean_uncertainty": round(self.mean_uncertainty, 4),
        }


def load_graph(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("edges"), list):
        raise ValueError("graph must contain an 'edges' list")
    return data


def route_graph(
    data: dict[str, Any],
    source: str,
    target: str,
    profile: RoutingProfile,
    heat_intensity: float = 0.0,
) -> RouteResult:
    graph = nx.Graph()

    for node in data.get("nodes", []):
        if "id" in node:
            graph.add_node(str(node["id"]))

    best_eval: dict[tuple[str, str], Any] = {}

    for edge in data["edges"]:
        u, v = str(edge["u"]), str(edge["v"])
        ev = evaluate_edge(edge, profile, heat_intensity)
        if not ev.traversable:
            continue

        key = tuple(sorted((u, v)))
        old = best_eval.get(key)
        if old is None or ev.cost < old.cost:
            best_eval[key] = ev
            graph.add_edge(
                u,
                v,
                weight=ev.cost,
                length_m=ev.length_m,
                exposed_m=ev.exposed_m,
                uncertainty=ev.uncertainty_fraction,
            )

    if source not in graph or target not in graph:
        raise nx.NodeNotFound("source or target is absent from the traversable graph")

    try:
        nodes = nx.shortest_path(graph, source=source, target=target, weight="weight")
    except nx.NetworkXNoPath as exc:
        raise ValueError(f"no traversable route from {source} to {target}") from exc

    total_cost = 0.0
    distance = 0.0
    exposed = 0.0
    uncertainties = []

    for u, v in zip(nodes, nodes[1:]):
        d = graph[u][v]
        total_cost += d["weight"]
        distance += d["length_m"]
        exposed += d["exposed_m"]
        uncertainties.append(d["uncertainty"])

    return RouteResult(
        nodes=nodes,
        cost=total_cost,
        distance_m=distance,
        exposed_m=exposed,
        mean_uncertainty=sum(uncertainties) / len(uncertainties) if uncertainties else 0.0,
    )
