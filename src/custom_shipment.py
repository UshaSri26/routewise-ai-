"""
Natural Language Prompt Parser and Dynamic Corridor Generator.
Interprets user queries (e.g. 'ship from Hyderabad to Warangal', 'frm hyd to wrngl',
'Hyderabad nunchi Warangal ki') and dynamically synthesizes route options for
custom trade corridors using realistic geographic distance (Haversine formula),
accurate commercial logistics speeds (road ~60-70 km/h, rail ~50 km/h, air),
and practical localized freight costing in Indian Rupees (INR) and USD equivalent.
"""

import hashlib
import math
import re
from typing import Tuple, Optional, Dict
import pandas as pd
from src.optimizer import WeightsConfig, HardConstraints
from src.freight_costs import INR_PER_USD, india_domestic_quotes, international_lcl_quotes

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

GLOBAL_HUB_KEYS = {
    "shanghai", "rotterdam", "singapore", "dubai", "los angeles", "new york",
    "hamburg", "london", "tokyo", "sydney",
}

INDIA_CITY_KEYS = {
    k for k in KNOWN_CITIES
    if k not in GLOBAL_HUB_KEYS
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
    "pune": "Pune",
    "ahmedabad": "Ahmedabad",
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

    # Stable fallback (avoid PYTHONHASHSEED randomization)
    digest = hashlib.md5(f"{o_key}-{d_key}".encode("utf-8")).hexdigest()
    seed = int(digest[:6], 16) % 800
    return float(180 + seed)


def clean_city_name(raw: str) -> str:
    """Strips conversational noise, port codes, and maps abbreviations to formal city names."""
    raw = re.sub(r"\s*\([^)]*\)", "", raw or "")
    prefixes = [
        "fastest", "cheapest", "safest", "quickest", "best", "route", "shipping",
        "shipment", "ship", "deliver", "delivery", "from", "frm", "please", "can",
        "you", "tell", "optimize", "parcel", "package", "courier", "freight",
    ]
    suffixes = ["nunchi", "ki", "lo", "to", "from", "road", "distance", "port", "via"]
    words = raw.strip().split()
    while words and words[0].lower() in prefixes:
        words.pop(0)
    while words and words[-1].lower() in suffixes:
        words.pop()
    cleaned = " ".join(words).strip()
    key = cleaned.lower()
    return CITY_ALIASES.get(key, cleaned.title())


def is_india_corridor(orig: str, dest: str) -> bool:
    o = orig.lower().strip()
    d = dest.lower().strip()
    if o in GLOBAL_HUB_KEYS or d in GLOBAL_HUB_KEYS:
        return False
    if o in INDIA_CITY_KEYS and d in INDIA_CITY_KEYS:
        return True
    # Unknown local names (e.g. small Indian towns) stay on the domestic model
    return o not in KNOWN_CITIES and d not in KNOWN_CITIES


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
            # INR amounts are typically 4+ digits; keep small USD budgets as USD
            max_budget = round(val / INR_PER_USD, 2) if val >= 400 else val
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
        constraint_notes.append(
            f"💰 Hard Constraint: Max budget ≤ **₹{int(max_budget * INR_PER_USD):,}** (${max_budget:,.2f})"
        )

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
    p_norm = re.sub(r"\s*\([^)]*\)", " ", p_lower)
    p_norm = re.sub(r"\s+", " ", p_norm).strip()

    # Pattern A: Telugu connector: '<City1> nunchi <City2> (ki|lo)?'
    m_tel = re.search(r'([a-zA-Z\s]+?)\s+nunchi\s+([a-zA-Z\s]+?)(?:\s+ki|\s+lo|,|$|\.|\bwith\b|\bwithin\b)', p_norm)
    if m_tel:
        orig = clean_city_name(m_tel.group(1))
        dest = clean_city_name(m_tel.group(2))

    # Pattern B: 'from X to Y' / 'frm hyd to wrngl'
    if not orig or not dest:
        m_to = re.search(
            r'(?:from|frm)\s+([a-zA-Z][a-zA-Z\s]{1,32}?)\s+(?:to|->|—)\s+([a-zA-Z][a-zA-Z\s]{1,32}?)(?:,|$|\.|\bwith\b|\bwithin\b|\bunder\b|\bin\b|\bhelp\b|\bwhich\b|\band\b|\bbudget\b|\bmax\b)',
            p_norm
        )
        if m_to:
            orig = clean_city_name(m_to.group(1))
            dest = clean_city_name(m_to.group(2))

    # Pattern C: short 'hyd to warangal' without 'from'
    if not orig or not dest:
        m_short = re.search(r'\b([a-z]{3,20})\s+to\s+([a-z]{3,20})\b', p_norm)
        if m_short:
            orig = clean_city_name(m_short.group(1))
            dest = clean_city_name(m_short.group(2))

    if orig and dest and orig.lower() != dest.lower():
        distance_km = estimate_distance_km(orig, dest)
        custom_id = "CUSTOM-01"
        domestic = is_india_corridor(orig, dest)

        if domestic:
            quotes = india_domestic_quotes(distance_km)
            keys = ("surface", "rail", "express", "fast")
            cargo_label = "Commercial carton (~50 kg)"
            peak_hours = max(quotes[k]["hours"] for k in keys)
            max_days_default = max(2.0, (peak_hours / 24.0) * 2.0)
            note_scale = "50 kg carton / small PTL"
        else:
            quotes = international_lcl_quotes(distance_km)
            keys = ("ocean", "express", "resilient", "air")
            cargo_label = "LCL consignment (~1 CBM)"
            peak_days = max(quotes[k]["days"] for k in keys)
            max_days_default = max(8.0, peak_days * 1.25)
            note_scale = "1 CBM LCL, not a full container"

        peak_cost = max(quotes[k]["cost_usd"] for k in keys)
        routes = []
        for r_idx, key in enumerate(keys, start=1):
            q = quotes[key]
            if domestic:
                hours = q["hours"]
                transit_days = round(hours / 24.0, 3)
                hubs = f"{orig} -> {dest} (~{hours}h)"
                carbon = round(distance_km * q["carbon_kg_per_km"], 1)
            else:
                transit_days = float(q["days"])
                hubs = q["hubs"]
                carbon = round(transit_days * (18 if "Air" in q["name"] else 6), 1)
            routes.append({
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig} -> {dest} (~{int(distance_km)} km)",
                "cargo_type": cargo_label,
                "urgency": "High" if r_idx < 4 else "Critical",
                "max_budget_usd": round(peak_cost * 1.35, 2),
                "max_transit_days": max_days_default,
                "route_id": f"{custom_id}-R{r_idx}",
                "route_name": q["name"],
                "carrier": q["carrier"],
                "transport_mode": q["mode"],
                "intermediate_hubs": hubs,
                "cost_usd": q["cost_usd"],
                "transit_time_days": transit_days,
                "delay_probability": q["delay_probability"],
                "congestion_risk": q["congestion_risk"],
                "geopolitical_risk": q["geopolitical_risk"],
                "carbon_emissions_kg": carbon,
            })
        custom_df = pd.DataFrame(routes)
        msg = (
            f"✨ Calculated corridor: **{orig} -> {dest}** (~{int(distance_km)} km, {note_scale}). "
            f"{combined_msg_prefix}"
        )
        return custom_df, weights, constraints, msg

    # Default fallback: return first shipment in dataset
    default_shp = existing_df[existing_df["shipment_id"] == "SHP-001"].copy()
    msg = f"Evaluated shipment **SHP-001** ({default_shp['origin'].iloc[0]} -> {default_shp['destination'].iloc[0]}). {combined_msg_prefix}"
    return default_shp, weights, constraints, msg
