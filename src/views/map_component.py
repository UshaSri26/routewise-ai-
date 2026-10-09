"""
Interactive Route Map Visualizer for RouteWise AI.
Renders maritime and multimodal trade corridors with glowing ports and geodesic routes.
Matches the Reference Design (media_1791572320523_beee24c4.jpg).
"""

import plotly.graph_objects as go
import pandas as pd

PORT_COORDINATES = {
    "Mumbai (INBOM)": {"lat": 18.94, "lon": 72.83, "name": "Mumbai"},
    "Mumbai": {"lat": 18.94, "lon": 72.83, "name": "Mumbai"},
    "Rotterdam (NLRTM)": {"lat": 51.92, "lon": 4.48, "name": "Rotterdam"},
    "Rotterdam": {"lat": 51.92, "lon": 4.48, "name": "Rotterdam"},
    "Singapore (SGSIN)": {"lat": 1.29, "lon": 103.85, "name": "Singapore"},
    "Singapore": {"lat": 1.29, "lon": 103.85, "name": "Singapore"},
    "Suez Canal": {"lat": 29.97, "lon": 32.55, "name": "Suez Canal"},
    "Cape of Good Hope": {"lat": -34.35, "lon": 18.47, "name": "Cape of Good Hope"},
    "Dubai": {"lat": 25.20, "lon": 55.27, "name": "Dubai Hub"},
    "Shanghai (CNSHA)": {"lat": 31.23, "lon": 121.47, "name": "Shanghai"},
    "Hamburg (DEHAM)": {"lat": 53.55, "lon": 9.99, "name": "Hamburg"},
    "Los Angeles (USLAX)": {"lat": 33.74, "lon": -118.27, "name": "Los Angeles"},
    "New York (USNYC)": {"lat": 40.71, "lon": -74.00, "name": "New York"}
}


def build_route_map(origin_name: str, destination_name: str, candidate_routes: list) -> go.Figure:
    fig = go.Figure()

    # Geo Map Styling (Dark High-Tech Navy)
    fig.update_geos(
        projection_type="natural earth",
        showland=True,
        landcolor="#0A1626",
        showocean=True,
        oceancolor="#07111F",
        showlakes=True,
        lakecolor="#07111F",
        showrivers=False,
        showcountries=True,
        countrycolor="#16273C",
        countrywidth=0.5,
        coastlinecolor="#1E3A5F",
        coastlinewidth=0.8,
        bgcolor="#0C1829"
    )

    colors = {
        "R1": "#38BDF8",  # Sky Blue
        "R2": "#21D4C2",  # Cyan / Teal (Winner default)
        "R3": "#FB923C",  # Orange (Cape bypass)
        "R4": "#A855F7"   # Purple (Air / Multimodal)
    }

    # Resolve Key Ports
    o_coord = PORT_COORDINATES.get(origin_name, {"lat": 18.94, "lon": 72.83, "name": origin_name})
    d_coord = PORT_COORDINATES.get(destination_name, {"lat": 51.92, "lon": 4.48, "name": destination_name})
    suez = PORT_COORDINATES["Suez Canal"]
    cape = PORT_COORDINATES["Cape of Good Hope"]
    singapore = PORT_COORDINATES["Singapore"]
    dubai = PORT_COORDINATES["Dubai"]

    # Trajectories for the 4 Archetypes
    routes_waypoints = [
        {"id": "R2", "name": "R2 - Express (Recommended)", "pts": [o_coord, singapore, suez, d_coord], "dash": "solid", "width": 3.0, "color": colors["R2"]},
        {"id": "R1", "name": "R1 - Standard Ocean", "pts": [o_coord, suez, d_coord], "dash": "dot", "width": 2.0, "color": colors["R1"]},
        {"id": "R3", "name": "R3 - Cape Route", "pts": [o_coord, cape, d_coord], "dash": "dash", "width": 2.0, "color": colors["R3"]},
        {"id": "R4", "name": "R4 - Air/Sea Multimodal", "pts": [o_coord, dubai, d_coord], "dash": "longdash", "width": 2.0, "color": colors["R4"]}
    ]

    # Draw Route Lines
    for r in routes_waypoints:
        lats = [p["lat"] for p in r["pts"]]
        lons = [p["lon"] for p in r["pts"]]
        fig.add_trace(go.Scattergeo(
            locationmode="ISO-3",
            lat=lats,
            lon=lons,
            mode="lines",
            line=dict(width=r["width"], color=r["color"], dash=r["dash"]),
            name=r["name"],
            hoverinfo="name"
        ))

    # Add Glowing Port Markers
    all_ports = [o_coord, d_coord, suez, cape, singapore]
    p_lats = [p["lat"] for p in all_ports]
    p_lons = [p["lon"] for p in all_ports]
    p_texts = [p["name"] for p in all_ports]

    fig.add_trace(go.Scattergeo(
        lat=p_lats,
        lon=p_lons,
        mode="markers+text",
        text=p_texts,
        textposition="top center",
        textfont=dict(family="Plus Jakarta Sans", size=10, color="#F1F5F9"),
        marker=dict(
            size=9,
            color="#21D4C2",
            line=dict(width=2, color="#FFFFFF")
        ),
        name="Key Trade Hubs",
        showlegend=False
    ))

    fig.update_layout(
        paper_bgcolor="#0C1829",
        plot_bgcolor="#0C1829",
        margin=dict(l=0, r=0, t=10, b=10),
        height=320,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Plus Jakarta Sans", size=9, color="#8A9FB8")
        )
    )

    return fig
