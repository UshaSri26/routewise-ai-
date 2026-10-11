"""Tests for the Streamlit endpoint corridor map."""

from src.views.map_component import build_route_map


def test_route_map_uses_candidate_options_and_known_endpoints():
    routes = [
        {"route_id": "SHP-019-R1", "route_name": "Standard Ocean", "transport_mode": "Ocean"},
        {"route_id": "SHP-019-R2", "route_name": "Express Ocean", "transport_mode": "Ocean-Express"},
    ]

    figure = build_route_map("Shanghai (CNSHA)", "Rotterdam (NLRTM)", routes)
    route_traces = [trace for trace in figure.data if trace.mode == "lines"]
    endpoint_trace = next(trace for trace in figure.data if trace.name == "Known endpoints")

    assert [trace.name for trace in route_traces] == ["Standard Ocean", "Express Ocean"]
    assert list(endpoint_trace.text) == ["Shanghai", "Rotterdam"]
    assert all(len(trace.lat) == 25 for trace in route_traces)
    assert "not carrier paths or live traffic" in figure.layout.annotations[-1].text


def test_route_map_does_not_invent_unknown_endpoint_coordinates():
    figure = build_route_map(
        "A city without coordinates",
        "Hyderabad",
        [{"route_id": "R1", "route_name": "Candidate"}],
    )

    assert not any(trace.mode == "lines" for trace in figure.data)
    endpoint_trace = next(trace for trace in figure.data if trace.name == "Known endpoints")
    assert list(endpoint_trace.text) == ["Hyderabad"]
    assert "omitted rather than guessed" in figure.layout.annotations[0].text
