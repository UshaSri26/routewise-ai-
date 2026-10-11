"""Endpoint-focused map for the Streamlit shipment comparison views."""

import math
import re
from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go

Coordinate = Tuple[float, float]

PORT_COORDINATES: Dict[str, Coordinate] = {
    "Mumbai": (18.94, 72.83),
    "Hyderabad": (17.39, 78.49),
    "Warangal": (17.97, 79.59),
    "Visakhapatnam": (17.69, 83.22),
    "Vijayawada": (16.51, 80.65),
    "Chennai": (13.08, 80.27),
    "Bengaluru": (12.97, 77.59),
    "Pune": (18.52, 73.86),
    "Delhi": (28.61, 77.21),
    "Kolkata": (22.57, 88.36),
    "Ahmedabad": (23.02, 72.57),
    "Jaipur": (26.91, 75.79),
    "Surat": (21.17, 72.83),
    "Nagpur": (21.15, 79.09),
    "Kochi": (9.93, 76.27),
    "Lucknow": (26.85, 80.95),
    "Shanghai": (31.23, 121.47),
    "Ningbo": (29.87, 121.55),
    "Rotterdam": (51.92, 4.48),
    "Los Angeles": (33.74, -118.27),
    "Singapore": (1.29, 103.85),
    "New York": (40.71, -74.01),
    "Busan": (35.18, 129.08),
    "Long Beach": (33.77, -118.19),
    "Yokohama": (35.44, 139.64),
    "Antwerp": (51.22, 4.40),
    "Shenzhen": (22.54, 114.06),
    "Felixstowe": (51.96, 1.35),
    "Santos": (-23.96, -46.33),
    "Dubai": (25.20, 55.27),
    "Hamburg": (53.55, 9.99),
    "Ho Chi Minh": (10.82, 106.63),
    "Seattle": (47.61, -122.33),
    "Qingdao": (36.07, 120.38),
    "Valencia": (39.47, -0.38),
    "Kaohsiung": (22.63, 120.30),
    "Oakland": (37.80, -122.27),
    "Chittagong": (22.36, 91.80),
    "Le Havre": (49.49, 0.11),
    "Colombo": (6.93, 79.85),
    "London Gateway": (51.51, 0.48),
    "Tokyo": (35.68, 139.65),
    "Frankfurt": (50.11, 8.68),
    "Bangkok": (13.76, 100.50),
    "Jakarta": (-6.21, 106.85),
    "Mundra": (22.74, 69.72),
    "Genoa": (44.41, 8.93),
    "Manila": (14.60, 120.98),
    "Vancouver": (49.28, -123.12),
    "Port Klang": (3.00, 101.40),
    "Sydney": (-33.87, 151.21),
    "Tanjung Pelepas": (1.36, 103.55),
    "Bremerhaven": (53.54, 8.58),
    "Incheon": (37.46, 126.71),
    "Chicago": (41.88, -87.63),
    "Durban": (-29.88, 31.05),
    "Veracruz": (19.17, -96.13),
    "Barcelona": (41.39, 2.17),
    "Alexandria": (31.20, 29.92),
    "Marseille": (43.30, 5.37),
    "Kobe": (34.69, 135.20),
    "Savannah": (32.08, -81.09),
    "Jebel Ali": (24.99, 55.06),
    "Cape Town": (-33.92, 18.42),
    "Taipei": (25.03, 121.57),
    "Amsterdam": (52.37, 4.90),
    "Karachi": (24.86, 67.01),
    "Piraeus": (37.94, 23.65),
    "Suez Canal": (29.97, 32.55),
    "Cape of Good Hope": (-34.35, 18.47),
}

ROUTE_COLORS = ("#21D4C2", "#38BDF8", "#FB923C", "#A855F7")
ROUTE_DASHES = ("solid", "dot", "dash", "longdash")


def _resolve_coordinate(name: str) -> Optional[Coordinate]:
    clean_name = re.sub(r"\s*\([^)]*\)", "", name or "").strip()
    for known_name, coordinate in PORT_COORDINATES.items():
        if clean_name.casefold() == known_name.casefold():
            return coordinate
    return None


def _schematic_curve(
    origin: Coordinate,
    destination: Coordinate,
    offset_degrees: float,
    samples: int = 25,
) -> Tuple[List[float], List[float]]:
    origin_lat, origin_lon = origin
    destination_lat, destination_lon = destination
    delta_lon = ((destination_lon - origin_lon + 180) % 360) - 180
    end_lon = origin_lon + delta_lon
    mean_lat = math.radians((origin_lat + destination_lat) / 2)
    longitude_scale = max(abs(math.cos(mean_lat)), 0.2)
    dx = delta_lon * longitude_scale
    dy = destination_lat - origin_lat
    length = max(math.hypot(dx, dy), 1e-6)
    control_lon = (origin_lon + end_lon) / 2 - dy / length * offset_degrees / longitude_scale
    control_lat = (origin_lat + destination_lat) / 2 + dx / length * offset_degrees

    latitudes: List[float] = []
    longitudes: List[float] = []
    for index in range(samples):
        t = index / (samples - 1)
        inverse_t = 1 - t
        latitude = inverse_t**2 * origin_lat + 2 * inverse_t * t * control_lat + t**2 * destination_lat
        longitude = inverse_t**2 * origin_lon + 2 * inverse_t * t * control_lon + t**2 * end_lon
        latitudes.append(latitude)
        longitudes.append(((longitude + 180) % 360) - 180)
    return latitudes, longitudes


def build_route_map(
    origin_name: str,
    destination_name: str,
    candidate_routes: List[Dict[str, Any]],
) -> go.Figure:
    """Draw known endpoints and schematic alternatives; never invent endpoint locations."""
    origin = _resolve_coordinate(origin_name)
    destination = _resolve_coordinate(destination_name)
    fig = go.Figure()

    if origin is not None and destination is not None:
        route_count = len(candidate_routes)
        angular_distance = math.hypot(
            (destination[1] - origin[1]) * math.cos(math.radians((origin[0] + destination[0]) / 2)),
            destination[0] - origin[0],
        )
        offset_step = min(3.0, max(0.25, angular_distance * 0.008))
        for index, route in enumerate(candidate_routes):
            offset = (index - (route_count - 1) / 2) * offset_step
            latitudes, longitudes = _schematic_curve(origin, destination, offset)
            route_id = str(route.get("route_id") or f"Alternative {index + 1}")
            route_name = str(route.get("route_name") or route_id)
            mode = str(route.get("transport_mode") or "")
            fig.add_trace(go.Scattergeo(
                lat=latitudes,
                lon=longitudes,
                mode="lines",
                line={
                    "width": 2.5,
                    "color": ROUTE_COLORS[index % len(ROUTE_COLORS)],
                    "dash": ROUTE_DASHES[index % len(ROUTE_DASHES)],
                },
                name=route_name,
                legendgroup=route_id,
                customdata=[[route_id, mode]] * len(latitudes),
                hovertemplate="%{customdata[0]} · %{customdata[1]}<extra>%{fullData.name}</extra>",
            ))

    endpoint_names = []
    endpoint_lats = []
    endpoint_lons = []
    if origin is not None:
        endpoint_names.append(re.sub(r"\s*\([^)]*\)", "", origin_name).strip())
        endpoint_lats.append(origin[0])
        endpoint_lons.append(origin[1])
    if destination is not None:
        endpoint_names.append(re.sub(r"\s*\([^)]*\)", "", destination_name).strip())
        endpoint_lats.append(destination[0])
        endpoint_lons.append(destination[1])

    if endpoint_names:
        fig.add_trace(go.Scattergeo(
            lat=endpoint_lats,
            lon=endpoint_lons,
            mode="markers+text",
            text=endpoint_names,
            textposition="top center",
            textfont={"size": 11, "color": "#F1F5F9"},
            marker={"size": 10, "color": "#21D4C2", "line": {"width": 2, "color": "#FFFFFF"}},
            name="Known endpoints",
            showlegend=False,
            hovertemplate="%{text}<extra>Shipment endpoint</extra>",
        ))

    unmapped = []
    if origin is None:
        unmapped.append(f"origin: {origin_name}")
    if destination is None:
        unmapped.append(f"destination: {destination_name}")
    if unmapped:
        fig.add_annotation(
            text=f"Coordinates not available for {' and '.join(unmapped)}; omitted rather than guessed.",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"color": "#93A4B8", "size": 12},
            bgcolor="#0C1829",
        )

    fig.update_geos(
        projection_type="natural earth",
        fitbounds="locations" if endpoint_names else False,
        showland=True,
        landcolor="#10283A",
        showocean=True,
        oceancolor="#07111F",
        showlakes=True,
        lakecolor="#07111F",
        showcountries=True,
        countrycolor="#1B3045",
        countrywidth=0.5,
        coastlinecolor="#1E3A5F",
        coastlinewidth=0.8,
        bgcolor="#091725",
    )
    fig.update_layout(
        title={"text": "Endpoint corridor comparison", "font": {"size": 15, "color": "#F1F5F9"}},
        paper_bgcolor="#0C1829",
        plot_bgcolor="#0C1829",
        margin={"l": 0, "r": 0, "t": 38, "b": 42},
        height=360,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.15,
            "xanchor": "center",
            "x": 0.5,
            "font": {"size": 9, "color": "#93A4B8"},
        },
        annotations=list(fig.layout.annotations or []) + [{
            "text": "Curves are schematic comparisons, not carrier paths or live traffic.",
            "xref": "paper",
            "yref": "paper",
            "x": 0.5,
            "y": -0.12,
            "showarrow": False,
            "font": {"size": 9, "color": "#93A4B8"},
        }],
    )
    return fig
