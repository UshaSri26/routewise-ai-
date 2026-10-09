"""
Natural Language Prompt Parser and Dynamic Corridor Generator.
Interprets user queries (e.g. 'ship from Hyderabad to Warangal with less time')
and dynamically synthesizes route options for custom trade corridors.
"""

import re
import numpy as np
import pandas as pd
from typing import Tuple, Optional
from src.optimizer import WeightsConfig


def parse_and_generate_corridor(prompt: str, existing_df: pd.DataFrame) -> Tuple[pd.DataFrame, WeightsConfig, str]:
    """
    Parses natural language prompts to detect origin/destination pairs and optimization priorities.
    Generates synthetic candidate routes dynamically if custom cities are requested.
    """
    p_lower = prompt.lower().strip()
    
    # 1. Detect Priority Intent
    if any(k in p_lower for k in ["less time", "speed", "faster", "fastest", "quick", "urgent", "rush"]):
        weights = WeightsConfig(cost=0.15, time=0.70, risk=0.15)
        intent_note = "⚡ Applied Priority: **Time-Critical (70% Time)** to minimize transit duration."
    elif any(k in p_lower for k in ["less cost", "cheap", "cheapest", "lowest cost", "low cost", "budget", "economical", "save money"]):
        weights = WeightsConfig(cost=0.70, time=0.15, risk=0.15)
        intent_note = "💰 Applied Priority: **Cost-Focused (70% Cost)** to minimize freight expenses."
    elif any(k in p_lower for k in ["safe", "safest", "risk", "resilient", "reliable", "avoid delay", "chokepoint"]):
        weights = WeightsConfig(cost=0.15, time=0.15, risk=0.70)
        intent_note = "🛡️ Applied Priority: **Risk-Averse (70% Risk)** to maximize schedule certainty."
    else:
        weights = WeightsConfig(cost=0.40, time=0.30, risk=0.30)
        intent_note = "⚖️ Applied Priority: **Balanced Baseline (40% Cost, 30% Time, 30% Risk)**."

    # 2. Check for explicit Shipment ID mentions (e.g. 'S001', 'SHP-005')
    shp_match = re.search(r'(?:shp-?|s)(\d{1,3})', p_lower)
    if shp_match:
        num = int(shp_match.group(1))
        target_id = f"SHP-{num:03d}"
        if target_id in existing_df["shipment_id"].values:
            matched_df = existing_df[existing_df["shipment_id"] == target_id].copy()
            msg = f"🔍 Identified benchmark shipment **{target_id}** ({matched_df['origin'].iloc[0]} ➔ {matched_df['destination'].iloc[0]}). {intent_note}"
            return matched_df, weights, msg

    # 3. Detect Custom 'From <City A> to <City B>' pattern
    pattern = r'from\s+([a-zA-Z\s]+?)\s+to\s+([a-zA-Z\s]+?)(?:,|$|\.|\bwith\b|\bhelp\b|\bwhich\b|\band\b)'
    match = re.search(pattern, p_lower)

    if match:
        orig = match.group(1).strip().title()
        dest = match.group(2).strip().title()
        
        # Synthesize realistic 4-archetype route candidates for this corridor
        custom_id = "CUSTOM-01"
        base_cost = np.random.uniform(350, 2400)
        base_days = np.random.uniform(1.5, 6.0)

        routes = [
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": base_cost * 2.5,
                "max_transit_days": base_days * 2.0,
                "route_id": f"{custom_id}-R1",
                "route_name": "Standard Surface Roadways",
                "carrier": "National Logistics / Freightway",
                "transport_mode": "Ground Truckload",
                "intermediate_hubs": f"{orig} Hub -> Transit Hub -> {dest}",
                "cost_usd": round(base_cost * 0.75, 2),
                "transit_time_days": round(base_days * 1.35, 1),
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
                "max_budget_usd": base_cost * 2.5,
                "max_transit_days": base_days * 2.0,
                "route_id": f"{custom_id}-R2",
                "route_name": "Direct Highway Express",
                "carrier": "BlueDart / DHL Express",
                "transport_mode": "Express Roadway",
                "intermediate_hubs": f"Direct Express Highway ({orig} -> {dest})",
                "cost_usd": round(base_cost * 1.15, 2),
                "transit_time_days": round(base_days * 0.85, 1),
                "delay_probability": 0.12,
                "congestion_risk": 30.0,
                "geopolitical_risk": 10.0,
                "carbon_emissions_kg": 210.0
            },
            {
                "shipment_id": custom_id,
                "origin": orig,
                "destination": dest,
                "corridor": f"{orig}-{dest} Corridor",
                "cargo_type": "Standard Package",
                "urgency": "High",
                "max_budget_usd": base_cost * 2.5,
                "max_transit_days": base_days * 2.0,
                "route_id": f"{custom_id}-R3",
                "route_name": "Intermodal Rail Freight",
                "carrier": "Rail Freight Logistics",
                "transport_mode": "Dedicated Rail Corridor",
                "intermediate_hubs": f"{orig} Freight Terminal -> {dest} Yard",
                "cost_usd": round(base_cost * 0.90, 2),
                "transit_time_days": round(base_days * 1.10, 1),
                "delay_probability": 0.08,
                "congestion_risk": 18.0,
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
                "max_budget_usd": base_cost * 2.5,
                "max_transit_days": base_days * 2.0,
                "route_id": f"{custom_id}-R4",
                "route_name": "Air Cargo Priority Express",
                "carrier": "Priority Air Delivery",
                "transport_mode": "Air Freight",
                "intermediate_hubs": f"{orig} Airport -> {dest} Cargo Gateway",
                "cost_usd": round(base_cost * 2.20, 2),
                "transit_time_days": round(max(base_days * 0.35, 0.5), 1),
                "delay_probability": 0.05,
                "congestion_risk": 12.0,
                "geopolitical_risk": 8.0,
                "carbon_emissions_kg": 420.0
            }
        ]
        custom_df = pd.DataFrame(routes)
        msg = f"✨ Dynamically generated custom corridor: **{orig} ➔ {dest}** (4 route candidates). {intent_note}"
        return custom_df, weights, msg

    # Default fallback: return current default shipment with updated weights
    default_shp = existing_df[existing_df["shipment_id"] == "SHP-001"].copy()
    msg = f"Evaluated shipment **SHP-001** ({default_shp['origin'].iloc[0]} ➔ {default_shp['destination'].iloc[0]}). {intent_note}"
    return default_shp, weights, msg
