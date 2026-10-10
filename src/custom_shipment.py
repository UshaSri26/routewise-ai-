"""
Natural Language Prompt Parser and Dynamic Corridor Generator.
Interprets user queries (e.g. 'fastest route from Hyderabad to Vishakapatnam within 1 day')
and dynamically synthesizes route options for custom trade corridors, including
hard constraints (max transit days, budget, etc.).
"""

import re
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from src.optimizer import WeightsConfig, HardConstraints


def parse_and_generate_corridor(
    prompt: str,
    existing_df: pd.DataFrame
) -> Tuple[pd.DataFrame, WeightsConfig, HardConstraints, str]:
    """
    Parses natural language prompts to detect:
    1. Origin/Destination pairs (e.g. 'from Hyderabad to Vishakapatnam')
    2. Optimization priority (fastest/cheapest/safest)
    3. Hard operational constraints (e.g. 'within 1 day', 'under $2000')

    Returns:
        (DataFrame of 4 candidate routes, WeightsConfig, HardConstraints, explanation_message)
    """
    p_lower = prompt.lower().strip()

    # ── 1. Detect Hard Constraints ───────────────────────────────────────────
    # Transit days constraint: 'within 1 day', 'in 2 days', 'under 1.5 days', 'less than 3 days', 'max 2 days'
    max_days: Optional[float] = None
    days_match = re.search(
        r'(?:within|under|in|less than|max(?:imum)?)\s+(\d+(?:\.\d+)?)\s*(?:day|days|d\b)',
        p_lower
    )
    if days_match:
        max_days = float(days_match.group(1))

    # Budget constraint: 'under $1000', 'budget 2000', 'max budget $1500', 'within $500'
    max_budget: Optional[float] = None
    budget_match = re.search(
        r'(?:budget|cost|under|max(?:imum)?|within)\s*(?:of\s*)?\$?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(?:usd|\$|dollars)?',
        p_lower
    )
    if budget_match and not days_match:
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
    # Supports 'from <Origin> to <Destination>' with delimiters like 'within', 'under', 'with', punctuation, etc.
    pattern = r'from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:,|$|\.|\bwith\b|\bwithin\b|\bunder\b|\bin\b|\bhelp\b|\bwhich\b|\band\b|\bbudget\b|\bmax\b)'
    match = re.search(pattern, p_lower)

    if match:
        orig = match.group(1).strip().title()
        dest = match.group(2).strip().title()

        # Seed based on city names for deterministic reproducibility
        city_seed = abs(hash(f"{orig}-{dest}")) % (2**31)
        rng = np.random.RandomState(city_seed)

        custom_id = "CUSTOM-01"
        base_cost = float(rng.uniform(450, 1800))

        # Realistic transit durations:
        # Air Freight: 0.5 - 0.8 days (sub-1-day express delivery)
        # Direct Highway: 1.2 - 2.0 days
        # Intermodal Rail: 2.0 - 3.2 days
        # Standard Truckload: 3.0 - 4.5 days
        routes = [
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": base_cost * 3.0,
                "max_transit_days": 5.0,
                "route_id": f"{custom_id}-R1",
                "route_name": "Standard Surface Roadways",
                "carrier": "National Freightway Logistics",
                "transport_mode": "Ground Truckload",
                "intermediate_hubs": f"{orig} Hub -> State Transit Hub -> {dest}",
                "cost_usd": round(base_cost * 0.70, 2),
                "transit_time_days": 3.5,
                "delay_probability": 0.28,
                "congestion_risk": 55.0,
                "geopolitical_risk": 15.0,
                "carbon_emissions_kg": 180.0
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": base_cost * 3.0,
                "max_transit_days": 5.0,
                "route_id": f"{custom_id}-R2",
                "route_name": "Intermodal Dedicated Rail Corridor",
                "carrier": "National Rail Freight Logistics",
                "transport_mode": "Dedicated Rail Corridor",
                "intermediate_hubs": f"{orig} Rail Terminal -> {dest} Yard",
                "cost_usd": round(base_cost * 0.90, 2),
                "transit_time_days": 2.2,
                "delay_probability": 0.10,
                "congestion_risk": 20.0,
                "geopolitical_risk": 5.0,
                "carbon_emissions_kg": 95.0
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": base_cost * 3.0,
                "max_transit_days": 5.0,
                "route_id": f"{custom_id}-R3",
                "route_name": "Direct Highway Express Courier",
                "carrier": "BlueDart / DHL Highway Express",
                "transport_mode": "Express Roadway",
                "intermediate_hubs": f"Direct Highway Corridor ({orig} -> {dest})",
                "cost_usd": round(base_cost * 1.30, 2),
                "transit_time_days": 1.4,
                "delay_probability": 0.12,
                "congestion_risk": 32.0,
                "geopolitical_risk": 10.0,
                "carbon_emissions_kg": 210.0
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "Critical",
                "max_budget_usd": base_cost * 3.0,
                "max_transit_days": 5.0,
                "route_id": f"{custom_id}-R4",
                "route_name": "Air Cargo Priority Same-Day Express",
                "carrier": "Indigo / Priority Air Cargo",
                "transport_mode": "Air Freight",
                "intermediate_hubs": f"{orig} Cargo Airport -> {dest} Cargo Gateway",
                "cost_usd": round(base_cost * 2.40, 2),
                "transit_time_days": 0.7,  # Less than 1 day (~17 hours door-to-door)
                "delay_probability": 0.04,
                "congestion_risk": 12.0,
                "geopolitical_risk": 8.0,
                "carbon_emissions_kg": 420.0
            }
        ]
        custom_df = pd.DataFrame(routes)
        msg = f"✨ Dynamically generated custom corridor: **{orig} -> {dest}** (4 route candidates). {combined_msg_prefix}"
        return custom_df, weights, constraints, msg

    # Default fallback: return first shipment in dataset
    default_shp = existing_df[existing_df["shipment_id"] == "SHP-001"].copy()
    msg = f"Evaluated shipment **SHP-001** ({default_shp['origin'].iloc[0]} -> {default_shp['destination'].iloc[0]}). {combined_msg_prefix}"
    return default_shp, weights, constraints, msg
