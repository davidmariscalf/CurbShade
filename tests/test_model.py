import math
from curbshade.model import RoutingProfile, evaluate_edge


def complete_edge(**overrides):
    edge = {
        "length_m": 100,
        "slope_pct": 2,
        "curb_cm": 0,
        "width_m": 1.5,
        "surface_score": 0.9,
        "shade_fraction": 0.8,
        "crossing_risk": 0.0,
    }
    edge.update(overrides)
    return edge


def test_wheelchair_rejects_high_curb():
    ev = evaluate_edge(complete_edge(curb_cm=7), RoutingProfile.wheelchair())
    assert not ev.traversable
    assert math.isinf(ev.cost)


def test_unknown_access_data_is_penalized():
    known = evaluate_edge(complete_edge(), RoutingProfile.wheelchair())
    unknown = complete_edge()
    unknown.pop("curb_cm")
    ev = evaluate_edge(unknown, RoutingProfile.wheelchair())
    assert ev.cost > known.cost
    assert ev.uncertainty_fraction > known.uncertainty_fraction


def test_heat_rewards_shade():
    sun = evaluate_edge(complete_edge(shade_fraction=0.0), RoutingProfile.walking(), 1.0)
    shade = evaluate_edge(complete_edge(shade_fraction=1.0), RoutingProfile.walking(), 1.0)
    assert shade.cost < sun.cost
