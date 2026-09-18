from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Any
import math


CRITICAL_ACCESS_FIELDS = ("slope_pct", "curb_cm", "width_m", "surface_score")


@dataclass(frozen=True)
class RoutingProfile:
    name: str
    max_slope_pct: float | None
    max_curb_cm: float | None
    min_width_m: float | None
    min_surface_score: float | None
    distance_weight: float = 1.0
    heat_weight: float = 0.8
    crossing_weight: float = 0.5
    uncertainty_weight: float = 0.9

    @classmethod
    def wheelchair(cls) -> "RoutingProfile":
        return cls(
            name="wheelchair",
            max_slope_pct=8.3,
            max_curb_cm=2.0,
            min_width_m=0.9,
            min_surface_score=0.55,
            distance_weight=1.0,
            heat_weight=0.9,
            crossing_weight=0.8,
            uncertainty_weight=1.4,
        )

    @classmethod
    def walking(cls) -> "RoutingProfile":
        return cls(
            name="walking",
            max_slope_pct=18.0,
            max_curb_cm=15.0,
            min_width_m=0.5,
            min_surface_score=0.25,
            distance_weight=1.0,
            heat_weight=0.8,
            crossing_weight=0.5,
            uncertainty_weight=0.45,
        )


@dataclass(frozen=True)
class EdgeEvaluation:
    traversable: bool
    cost: float
    length_m: float
    exposed_m: float
    uncertainty_fraction: float
    reason: str | None


def _number(edge: Mapping[str, Any], key: str) -> float | None:
    value = edge.get(key)
    if value is None:
        return None
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def _access_number(edge: Mapping[str, Any], key: str) -> float | None:
    value = _number(edge, key)
    if value is None:
        return None
    if key == "curb_cm" and value < 0:
        return None
    if key == "width_m" and value <= 0:
        return None
    if key == "surface_score" and not 0.0 <= value <= 1.0:
        return None
    return value


def _unit_interval(edge: Mapping[str, Any], key: str) -> float | None:
    value = _number(edge, key)
    return value if value is not None and 0.0 <= value <= 1.0 else None


def evaluate_edge(
    edge: Mapping[str, Any],
    profile: RoutingProfile,
    heat_intensity: float = 0.0,
) -> EdgeEvaluation:
    """Evaluate one segment under a mobility profile.

    Unknown critical fields are penalized rather than treated as safe.
    heat_intensity is a dimensionless [0, 1] routing preference signal, not a
    medical heat-risk estimate.
    """
    heat = min(1.0, max(0.0, float(heat_intensity)))
    length = _number(edge, "length_m")
    if length is None or length <= 0:
        return EdgeEvaluation(False, math.inf, 0.0, 0.0, 1.0, "invalid length")

    checks = (
        ("slope_pct", profile.max_slope_pct, lambda x, lim: abs(x) <= lim, "slope"),
        ("curb_cm", profile.max_curb_cm, lambda x, lim: x <= lim, "curb"),
        ("width_m", profile.min_width_m, lambda x, lim: x >= lim, "width"),
        ("surface_score", profile.min_surface_score, lambda x, lim: x >= lim, "surface"),
    )

    for key, limit, predicate, label in checks:
        if limit is None:
            continue
        value = _access_number(edge, key)
        if value is not None and not predicate(value, limit):
            return EdgeEvaluation(False, math.inf, length, length, 0.0, f"{label} barrier")

    unknown = sum(_access_number(edge, key) is None for key in CRITICAL_ACCESS_FIELDS)
    uncertainty = unknown / len(CRITICAL_ACCESS_FIELDS)

    shade = _unit_interval(edge, "shade_fraction")
    if shade is None:
        shade = 0.0
        uncertainty = min(1.0, uncertainty + 0.15)
    exposed = length * (1.0 - shade)

    crossing = _unit_interval(edge, "crossing_risk")
    if crossing is None:
        crossing = 0.0
        uncertainty = min(1.0, uncertainty + 0.10)

    cost = (
        profile.distance_weight * length
        + profile.heat_weight * heat * exposed
        + profile.crossing_weight * crossing * length
        + profile.uncertainty_weight * uncertainty * length
    )

    return EdgeEvaluation(True, cost, length, exposed, uncertainty, None)
