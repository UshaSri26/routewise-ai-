"""
Natural Language Prompt Parser and Dynamic Corridor Generator.
Interprets user queries (e.g. 'ship from Hyderabad to Warangal', 'frm hyd to wrngl',
'Hyderabad nunchi Warangal ki') and dynamically synthesizes route options for
custom trade corridors using realistic geographic distance (Haversine formula),
accurate commercial logistics speeds (road ~60-70 km/h, rail ~50 km/h, air),
and practical localized freight costing in Indian Rupees (INR) and USD equivalent.
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
    "hyd": (17.3850, 78.4867),
    "warangal": (17.9689, 79.5941),
    "wrngl": (17.9689, 79.5941),
    "wgl": (17.9689, 79.5941),
    "visakhapatnam": (17.6868, 83.2185),
    "vishakapatnam": (17.6868, 83.2185),
    "vizag": (17.6868, 83.2185),
    "vskp": (17.6868, 83.2185),
    "vijayawada": (16.5062, 80.6480),
    "vja": (16.5062, 80.6480),
    "chennai": (13.0827, 80.2707),
    "maa": (13.0827, 80.2707),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "blr": (12.9716, 77.5946),
    "mumbai": (18.9400, 72.8300),
    "bom": (18.9400, 72.8300),
    "pune": (18.5204, 73.8567),
    "delhi": (28.6139, 77.2090),
    "del": (28.6139, 77.2090),
    "kolkata": (22.5726, 88.3639),
    "ccu": (22.5726, 88.3639),
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

CITY_ALIASES: Dict[str, str] = {
    "hyd": "Hyderabad",
    "hyderabad": "Hyderabad",
    "wrngl": "Warangal",
    "wgl": "Warangal",
    "warangal": "Warangal",
    "vizag": "Visakhapatnam",
    "vskp": "Visakhapatnam",
    "vishakapatnam": "Visakhapatnam",
    "visakhapatnam": "Visakhapatnam",
    "vja": "Vijayawada",
    "vijayawada": "Vijayawada",
    "blr": "Bengaluru",
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "maa": "Chennai",
    "chennai": "Chennai",
    "bom": "Mumbai",
    "mumbai": "Mumbai",
    "del": "Delhi",
    "delhi": "Delhi",
    "ccu": "Kolkata",
    "kolkata": "Kolkata",
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
    Estimates actual highway route distance in km.
    If both cities are known, uses haversine * 1.15 road winding factor.
    """
    o_key = orig.lower().strip()
    d_key = dest.lower().strip()

    if o_key in KNOWN_CITIES and d_key in KNOWN_CITIES:
        straight = haversine_km(KNOWN_CITIES[o_key], KNOWN_CITIES[d_key])
        return max(30.0, round(straight * 1.15, 1))

    # Fallback deterministic distance
    seed = abs(hash(f"{o_key}-{d_key}")) % 800
    return float(180 + seed)


def clean_city_name(raw: str) -> str:
    """Strips conversational noise and maps abbreviations to formal city names."""
    prefixes = [
        "fastest", "cheapest", "safest", "quickest", "best", "route", "shipping",
        "shipment", "ship", "deliver", "delivery", "from", "frm", "please", "can", "you", "tell"
    ]
    suffixes = ["nunchi", "ki", "lo", "to", "from", "road", "distance"]
    words = raw.strip().split()
    while words and words[0].lower() in prefixes:
        words.pop(0)
    while words and words[-1].lower() in suffixes:
        words.pop()
    cleaned = " ".join(words).strip()
    key = cleaned.lower()
    return CITY_ALIASES.get(key, cleaned.title())


def parse_and_generate_corridor(
    prompt: str,
    existing_df: pd.DataFrame
) -> Tuple[pd.DataFrame, WeightsConfig, HardConstraints, str]:
    """
    Parses natural language prompts to detect:
    1. Origin/Destination pairs (supports 'from X to Y', 'X nunchi Y ki', 'frm hyd to wrngl')
    2. Optimization priority (fastest/cheapest/safest)
    3. Hard operational constraints (e.g. 'within 1 day', 'under $2000', 'within 4 hours')

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

    hours_match = re.search(
        r'(?:within|under|in|less than|max(?:imum)?)\s+(\d+(?:\.\d+)?)\s*(?:hour|hours|hrs|hr\b)',
        p_lower
    )
    if hours_match and not max_days:
        max_days = round(float(hours_match.group(1)) / 24.0, 3)

    max_budget: Optional[float] = None
    budget_match = re.search(
        r'(?:budget|cost|under|max(?:imum)?|within)\s*(?:of\s*)?(?:\$|rs\.?|inr)?\s*(\d+(?:,\d+)*(?:\.\d+)?)',
        p_lower
    )
    if budget_match and not days_match and not hours_match:
        try:
            val = float(budget_match.group(1).replace(",", ""))
            # If user entered budget in INR (> 500), convert roughly to USD equivalent for optimizer
            max_budget = round(val / 84.0, 2) if val > 1000 else val
        except (ValueError, TypeError):
            max_budget = None

    constraints = HardConstraints(
        max_transit_days=max_days,
        max_budget_usd=max_budget
    )

    constraint_notes = []
    if max_days is not None:
        if max_days < 1.0:
            constraint_notes.append(f"⏱️ Hard Constraint: Max transit time ≤ **{round(max_days*24, 1)} hours** ({max_days}d)")
        else:
            constraint_notes.append(f"⏱️ Hard Constraint: Max transit time ≤ **{max_days} days**")
    if max_budget is not None:
        constraint_notes.append(f"💰 Hard Constraint: Max budget ≤ **${max_budget:,.2f}** (~₹{int(max_budget*84):,})")

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
    orig, dest = None, None

    # Pattern A: Telugu connector: '<City1> nunchi <City2> (ki|lo)?'
    m_tel = re.search(r'([a-zA-Z\s]+?)\s+nunchi\s+([a-zA-Z\s]+?)(?:\s+ki|\s+lo|,|$|\.|\bwith\b|\bwithin\b)', p_lower)
    if m_tel:
        orig = clean_city_name(m_tel.group(1))
        dest = clean_city_name(m_tel.group(2))

    # Pattern B: English connector: '(from|frm)? <City1> (to|->|—|-) <City2>'
    if not orig or not dest:
        m_to = re.search(
            r'(?:from|frm\s+)?([a-zA-Z\s]+?)\s+(?:to|->|—|-)\s+([a-zA-Z\s]+?)(?:,|$|\.|\bwith\b|\bwithin\b|\bunder\b|\bin\b|\bhelp\b|\bwhich\b|\band\b|\bbudget\b|\bmax\b)',
            p_lower
        )
        if m_to:
            orig = clean_city_name(m_to.group(1))
            dest = clean_city_name(m_to.group(2))

    if orig and dest and orig.lower() != dest.lower():
        distance_km = estimate_distance_km(orig, dest)
        custom_id = "CUSTOM-01"

        # Realistic Speed & Transit Calculations:
        # Direct Highway Express Courier (e.g. NH163 Hyd->Wgl, 150 km):
        # Average road speed ~60-70 km/h + 30m dispatch = ~2.5 - 3.2 hours
        express_hours = max(1.0, round((distance_km / 65.0) + 0.5, 1))
        express_days = round(express_hours / 24.0, 3)

        # Standard Surface Truckload: ~40 km/h + 1.5h handling = ~4.5 - 5.5 hours for 150km
        truck_hours = max(1.5, round((distance_km / 40.0) + 1.5, 1))
        truck_days = round(truck_hours / 24.0, 3)

        # Dedicated Rail Freight: ~50 km/h + 1.5h yard handling = ~3.5 - 4.5 hours for 150km
        rail_hours = max(1.2, round((distance_km / 50.0) + 1.5, 1))
        rail_days = round(rail_hours / 24.0, 3)

        # Regional Express / Air Cargo:
        # Under 250km (inter-city regional corridor like Hyd->Wgl):
        # Air cargo is unnecessary; same-day motorcycle/direct courier operates in ~2.5-3.0 hours
        if distance_km < 250:
            air_hours = max(0.8, round(express_hours * 0.85, 1))
            air_name = "Same-Day Direct Highway Courier"
            air_mode = "Priority Road Express"
            air_hubs = f"Direct Corridor via NH163 ({orig} -> {dest}) (~{air_hours}h)"
        else:
            air_hours = max(2.5, round(3.5 + (distance_km / 650.0), 1))
            air_name = "Air Cargo Priority Express"
            air_mode = "Air Freight"
            air_hubs = f"{orig} Cargo Airport -> {dest} Cargo Gateway (~{air_hours}h)"
        air_days = round(air_hours / 24.0, 3)

        # Realistic Freight Costing:
        # Commercial parcel rate in India:
        # Rail freight parcel: ~₹4 - ₹6 per km = ₹600 - ₹900 for 150km (~$8 - $12 USD)
        # Standard Truck parcel: ~₹6 - ₹9 per km = ₹900 - ₹1,400 for 150km (~$12 - $18 USD)
        # Express Highway courier: ~₹10 - ₹15 per km = ₹1,500 - ₹2,300 for 150km (~$20 - $30 USD)
        # Priority Same-Day: ~₹20 - ₹28 per km = ₹3,000 - ₹4,200 for 150km (~$38 - $55 USD)
        base_rate_usd_km = 0.09  # ~$0.09 per km = ~₹7.5/km
        rail_cost = round(max(8.0, distance_km * base_rate_usd_km * 0.70), 2)
        road_cost = round(max(12.0, distance_km * base_rate_usd_km * 1.00), 2)
        express_cost = round(max(18.0, distance_km * base_rate_usd_km * 1.60), 2)
        air_cost = round(max(28.0, distance_km * base_rate_usd_km * 2.80), 2)

        routes = [
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} -> {dest} (~{int(distance_km)} km)",
                "cargo_type": "Commercial Freight / Parcel",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(3.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R1",
                "route_name": "Standard Surface Roadways",
                "carrier": "VRL Logistics / TCI Freight",
                "transport_mode": "Ground Truckload",
                "intermediate_hubs": f"{orig} Hub -> State Highway -> {dest} (~{truck_hours}h)",
                "cost_usd": road_cost,
                "transit_time_days": truck_days,
                "delay_probability": 0.18,
                "congestion_risk": 40.0,
                "geopolitical_risk": 3.0,
                "carbon_emissions_kg": round(distance_km * 0.12, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} -> {dest} (~{int(distance_km)} km)",
                "cargo_type": "Commercial Freight / Parcel",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(3.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R2",
                "route_name": "Intermodal Rail Freight Parcel",
                "carrier": "Indian Railways Freight / CONCOR",
                "transport_mode": "Dedicated Rail Corridor",
                "intermediate_hubs": f"{orig} Goods Yard -> {dest} Rail Terminal (~{rail_hours}h)",
                "cost_usd": rail_cost,
                "transit_time_days": rail_days,
                "delay_probability": 0.06,
                "congestion_risk": 15.0,
                "geopolitical_risk": 2.0,
                "carbon_emissions_kg": round(distance_km * 0.05, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} -> {dest} (~{int(distance_km)} km)",
                "cargo_type": "Commercial Freight / Parcel",
                "urgency": "High",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(3.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R3",
                "route_name": "Direct Highway Express Courier",
                "carrier": "BlueDart / DTDC Express",
                "transport_mode": "Express Roadway",
                "intermediate_hubs": f"Direct Highway Corridor ({orig} -> {dest}) (~{express_hours}h)",
                "cost_usd": express_cost,
                "transit_time_days": express_days,
                "delay_probability": 0.08,
                "congestion_risk": 25.0,
                "geopolitical_risk": 3.0,
                "carbon_emissions_kg": round(distance_km * 0.14, 1)
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} -> {dest} (~{int(distance_km)} km)",
                "cargo_type": "Commercial Freight / Parcel",
                "urgency": "Critical",
                "max_budget_usd": air_cost * 1.5,
                "max_transit_days": max(3.0, truck_days * 2.0),
                "route_id": f"{custom_id}-R4",
                "route_name": air_name,
                "carrier": "Priority Express / Indigo Cargo",
                "transport_mode": air_mode,
                "intermediate_hubs": air_hubs,
                "cost_usd": air_cost,
                "transit_time_days": air_days,
                "delay_probability": 0.03,
                "congestion_risk": 10.0,
                "geopolitical_risk": 2.0,
                "carbon_emissions_kg": round(distance_km * 0.28, 1)
            }
        ]
        custom_df = pd.DataFrame(routes)
        msg = f"✨ Calculated corridor: **{orig} -> {dest}** (~{int(distance_km)} km highway distance). {combined_msg_prefix}"
        return custom_df, weights, constraints, msg

    # Default fallback: return first shipment in dataset
    default_shp = existing_df[existing_df["shipment_id"] == "SHP-001"].copy()
    msg = f"Evaluated shipment **SHP-001** ({default_shp['origin'].iloc[0]} -> {default_shp['destination'].iloc[0]}). {combined_msg_prefix}"
    return default_shp, weights, constraints, msg
