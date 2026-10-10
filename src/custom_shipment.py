"""
Natural Language Prompt Parser and Dynamic Corridor Generator.
Interprets user queries (e.g. 'ship from Hyderabad to Warangal')
and dynamically synthesizes route options for custom trade corridors, using
realistic geographic distance estimation (Haversine formula), real-world speed
and freight costing benchmarks (road, rail, express courier, air cargo).
"""

import math
import re
from typing import Tuple, Optional, Dict
import numpy as np
import pandas as pd
from src.optimizer import WeightsConfig, HardConstraints

# Real coordinates for common Indian & Global logistics hubs
KNOWN_CITIES: Dict[str, Tuple[float, float]] = {
    # South & Central India
    "hyderabad": (17.3850, 78.4867),
    "warangal": (17.9689, 79.5941),
    "visakhapatnam": (17.6868, 83.2185),
    "vishakapatnam": (17.6868, 83.2185),
    "vijayawada": (16.5062, 80.6480),
    "chennai": (13.0827, 80.2707),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "mumbai": (18.9400, 72.8300),
    "pune": (18.5204, 73.8567),
    "delhi": (28.6139, 77.2090),
    "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714),
    "nagpur": (21.1458, 79.0882),
    "kochi": (9.9312, 76.2673),
    "coimbatore": (11.0168, 76.9558),
    "jaipur": (26.9124, 75.7873),
    "surat": (21.1702, 72.8311),
    "bhopal": (23.2599, 77.4126),
    "lucknow": (26.8467, 80.9462),

    # Global Hubs
    "shanghai": (31.2304, 121.4737),
    "rotterdam": (51.9244, 4.4777),
    "singapore": (1.3521, 103.8198),
    "dubai": (25.2048, 55.2708),
    "los angeles": (34.0522, -118.2437),
    "new york": (40.7128, -74.0060),
    "hamburg": (53.5511, 9.9937),
    "london": (51.5074, -0.1278),
    "tokyo": (35.6762, 139.6503),
    "sydney": (33.8688, 151.2093),
}


def haversine_km(c1: Tuple[float, float], c2: Tuple[float, float]) -> float:
    """Computes great-circle distance in kilometers between two coordinates."""
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c


def estimate_distance_km(orig: str, dest: str) -> float:
    """
    Estimates actual highway distance in km.
    If both cities are known, uses haversine * 1.25 winding road factor.
    Otherwise falls back to a deterministic hash-based distance between 200 and 1200 km.
    """
    o_key = orig.lower().strip()
    d_key = dest.lower().strip()

    if o_key in KNOWN_CITIES and d_key in KNOWN_CITIES:
        straight = haversine_km(KNOWN_CITIES[o_key], KNOWN_CITIES[d_key])
        return max(50.0, round(straight * 1.22, 1))

    # Fallback deterministic distance based on city name hash
    seed = abs(hash(f"{o_key}-{d_key}")) % 1000
    return float(250 + seed)


def parse_and_generate_corridor(
    prompt: str,
    existing_df: pd.DataFrame
) -> Tuple[pd.DataFrame, WeightsConfig, HardConstraints, str]:
    """
    Parses natural language prompts to detect:
    1. Origin/Destination pairs (e.g. 'from Hyderabad to Warangal')
    2. Optimization priority (fastest/cheapest/safest)
    3. Hard operational constraints (e.g. 'within 1 day', 'under $2000')

    Returns:
        (DataFrame of 4 candidate routes, WeightsConfig, HardConstraints, explanation_message)
    """
    p_lower = prompt.lower().strip()

    # ── 1. Detect Hard Constraints ───────────────────────────────────────────
    max_days: Optional[float] = None
    days_match = re.search(
        r'(?:within|under|in|less than|max(?:imum)?)\s+(\d+(?:\.\d+)?)\s*(?:day|days|d\b)',
        p_lower
    )
    if days_match:
        max_days = float(days_match.group(1))

    # Also check hour constraints (e.g., 'within 6 hours', 'under 12 hours')
    hours_match = re.search(
        r'(?:within|under|in|less than|max(?:imum)?)\s+(\d+(?:\.\d+)?)\s*(?:hour|hours|hrs|hr\b)',
        p_lower
    )
    if hours_match and not max_days:
        max_days = round(float(hours_match.group(1)) / 24.0, 2)

    max_budget: Optional[float] = None
    budget_match = re.search(
        r'(?:budget|cost|under|max(?:imum)?|within)\s*(?:of\s*)?\$?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:usd|\$|dollars)?',
        p_lower
    )
    if budget_match and not days_match and not hours_match:
        try:
            max_budget = float(budget_match.group(1).replace(",", ""))
        except (ValueError, TypeError):
            max_budget = None

    constraints = HardConstraints(
        max_transit_days=max_days,
        max_budget_usd=max_budget
    )

    constraint_notes = []
    if max_days is not None:
        constraint_notes.append(f"⏱️ Hard Constraint: Max transit time ≤ **{max_days} days**")
    if max_budget is not None:
        constraint_notes.append(f"💰 Hard Constraint: Max budget ≤ **${max_budget:,.2f}**")

    # ── 2. Detect Priority Intent ────────────────────────────────────────────
    if any(k in p_lower for k in ["less time", "speed", "faster", "fastest", "quick", "urgent", "rush", "fast"]):
        weights = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
        intent_note = "⚡ Applied Priority: **Time-Critical (70% Time)** to prioritize delivery speed."
    elif any(k in p_lower for k in ["less cost", "cheap", "cheapest", "lowest cost", "low cost", "budget", "economical", "save money"]):
        weights = WeightsConfig(cost=0.70, time=0.15, risk=0.15)
        intent_note = "💰 Applied Priority: **Cost-Focused (70% Cost)** to minimize freight expenses."
    elif any(k in p_lower for k in ["safe", "safest", "risk", "resilient", "reliable", "avoid delay", "chokepoint"]):
        weights = WeightsConfig(cost=0.15, time=0.15, risk=0.70)
        intent_note = "🛡️ Applied Priority: **Risk-Averse (70% Risk)** to maximize schedule certainty."
    else:
        weights = WeightsConfig(cost=0.40, time=0.30, risk=0.30)
        intent_note = "⚖️ Applied Priority: **Balanced Baseline (40% Cost, 30% Time, 30% Risk)**."

    full_notes = [intent_note] + constraint_notes
    combined_msg_prefix = " | ".join(full_notes)

    # ── 3. Check for Explicit Benchmark Shipment ID ──────────────────────────
    shp_match = re.search(r'(?:shp-?|s)(\d{1,3})', p_lower)
    if shp_match:
        num = int(shp_match.group(1))
        target_id = f"SHP-{num:03d}"
        if target_id in existing_df["shipment_id"].values:
            matched_df = existing_df[existing_df["shipment_id"] == target_id].copy()
            msg = f"🔍 Benchmark shipment **{target_id}** ({matched_df['origin'].iloc[0]} -> {matched_df['destination'].iloc[0]}). {combined_msg_prefix}"
            return matched_df, weights, constraints, msg

    # ── 4. Detect Custom Origin & Destination ────────────────────────────────
    pattern = r'from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:,|$|\.|\bwith\b|\bwithin\b|\bunder\b|\bin\b|\bhelp\b|\bwhich\b|\band\b|\bbudget\b|\bmax\b)'
    match = re.search(pattern, p_lower)

    if match:
        orig = match.group(1).strip().title()
        dest = match.group(2).strip().title()

        distance_km = estimate_distance_km(orig, dest)
        custom_id = "CUSTOM-01"

        # Realistic duration calculation based on distance:
        # Ground Truckload: ~40 km/h average commercial freight + 2h terminal handling
        truck_hours = (distance_km / 40.0) + 2.0
        truck_days = round(max(0.2, truck_hours / 24.0), 2)

        # Dedicated Rail Freight: ~55 km/h + 3h railyard handling
        rail_hours = (distance_km / 55.0) + 3.0
        rail_days = round(max(0.15, rail_hours / 24.0), 2)

        # Express Road Courier (Direct Highway): ~70 km/h express + 1h dispatch
        express_hours = (distance_km / 70.0) + 1.0
        express_days = round(max(0.1, express_hours / 24.0), 2)

        # Air Freight / Priority Air:
        # For distances < 300 km (like Hyd-Warangal), air cargo is unnecessary or minimal airport-to-airport
        # For distances >= 300 km, commercial air cargo takes ~4-8h handling + flight
        if distance_km < 250:
            air_hours = express_hours * 0.9  # Not direct flight; helicopter / ultra-rapid courier
            air_name = "Same-Day Ultra-Rapid Courier"
            air_mode = "Priority Express Dispatch"
            air_hubs = f"{orig} Central Hub -> Express Transit -> {dest}"
        else:
            air_hours = 4.0 + (distance_km / 650.0)
            air_name = "Air Cargo Priority Express"
            air_mode = "Air Freight"
            air_hubs = f"{orig} Cargo Airport -> {dest} Cargo Gateway"
        air_days = round(max(0.1, air_hours / 24.0), 2)

        # Realistic Freight Costing (INR/USD scaled per commercial freight rates):
        # Base per-ton commercial rates: ~$0.25 - $0.80 per km for full parcel/pallet
        base_km_rate = 0.45  # USD per km for standard logistics package
        road_cost = round(max(45.0, distance_km * base_km_rate * 0.85), 2)
        rail_cost = round(max(35.0, distance_km * base_km_rate * 0.65), 2)
        express_cost = round(max(65.0, distance_km * base_km_rate * 1.35), 2)
        air_cost = round(max(120.0, distance_km * base_km_rate * 2.60), 2)

        routes = [
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} - {dest} (~{int(distance_km)} km)",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(5.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R1",
                "route_name": "Standard Surface Roadways",
                "carrier": "National Freightway Logistics",
                "transport_mode": "Ground Truckload",
                "intermediate_hubs": f"{orig} Hub -> State Highway -> {dest} (~{round(truck_hours, 1)}h)",
                "cost_usd": road_cost,
                "transit_time_days": truck_days,
                "delay_probability": 0.22,
                "congestion_risk": 45.0,
                "geopolitical_risk": 5.0,
                "carbon_emissions_kg": round(distance_km * 0.14, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} - {dest} (~{int(distance_km)} km)",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(5.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R2",
                "route_name": "Intermodal Dedicated Rail Corridor",
                "carrier": "National Rail Freight Logistics",
                "transport_mode": "Dedicated Rail Corridor",
                "intermediate_hubs": f"{orig} Rail Terminal -> {dest} Yard (~{round(rail_hours, 1)}h)",
                "cost_usd": rail_cost,
                "transit_time_days": rail_days,
                "delay_probability": 0.08,
                "congestion_risk": 15.0,
                "geopolitical_risk": 3.0,
                "carbon_emissions_kg": round(distance_km * 0.06, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} - {dest} (~{int(distance_km)} km)",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(5.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R3",
                "route_name": "Direct Highway Express Courier",
                "carrier": "BlueDart / Express Highway Courier",
                "transport_mode": "Express Roadway",
                "intermediate_hubs": f"Direct Highway ({orig} -> {dest}) (~{round(express_hours, 1)}h)",
                "cost_usd": express_cost,
                "transit_time_days": express_days,
                "delay_probability": 0.10,
                "congestion_risk": 25.0,
                "geopolitical_risk": 5.0,
                "carbon_emissions_kg": round(distance_km * 0.16, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} - {dest} (~{int(distance_km)} km)",
                "cargo_type": "Standard Package",
                "urgency": "Critical",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(5.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R4",
                "route_name": air_name,
                "carrier": "Priority Express Delivery",
                "transport_mode": air_mode,
                "intermediate_hubs": f"{air_hubs} (~{round(air_hours, 1)}h)",
                "cost_usd": air_cost,
                "transit_time_days": air_days,
                "delay_probability": 0.04,
                "congestion_risk": 10.0,
                "geopolitical_risk": 3.0,
                "carbon_emissions_kg": round(distance_km * 0.35, 1)
            }
        ]
        custom_df = pd.DataFrame(routes)
        msg = f"✨ Calculated corridor: **{orig} -> {dest}** (~{int(distance_km)} km highway distance). {combined_msg_prefix}"
        return custom_df, weights, constraints, msg

    # Default fallback: return first shipment in dataset
    default_shp = existing_df[existing_df["shipment_id"] == "SHP-001"].copy()
    msg = f"Evaluated shipment **SHP-001** ({default_shp['origin'].iloc[0]} -> {default_shp['destination'].iloc[0]}). {combined_msg_prefix}"
    return default_shp, weights, constraints, msg
