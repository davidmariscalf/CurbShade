from curbshade.model import RoutingProfile
from curbshade.router import route_graph


def demo():
    return {
        "nodes": [{"id": x} for x in "ABCD"],
        "edges": [
            {"u":"A","v":"B","length_m":50,"slope_pct":2,"curb_cm":0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.0},
            {"u":"B","v":"D","length_m":50,"slope_pct":2,"curb_cm":6,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.0},
            {"u":"A","v":"C","length_m":70,"slope_pct":2,"curb_cm":0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.9},
            {"u":"C","v":"D","length_m":70,"slope_pct":2,"curb_cm":0,"width_m":1.4,"surface_score":0.9,"shade_fraction":0.9}
        ]
    }


def test_wheelchair_avoids_barrier():
    r = route_graph(demo(), "A", "D", RoutingProfile.wheelchair(), 0.0)
    assert r.nodes == ["A", "C", "D"]


def test_walking_can_take_short_route_without_heat():
    r = route_graph(demo(), "A", "D", RoutingProfile.walking(), 0.0)
    assert r.nodes == ["A", "B", "D"]


def test_heat_can_flip_walking_route():
    r = route_graph(demo(), "A", "D", RoutingProfile.walking(), 1.0)
    assert r.nodes == ["A", "C", "D"]
