"""
Synthetic Shipment and Route Dataset Generator for RouteWise AI.
Generates realistic global trade corridors with explicit trade-offs across cost, transit time, and risk.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd

# Global trade corridors (Origin -> Destination pairs)
TRADE_LANES = [
    {"origin": "Shanghai (CNSHA)", "destination": "Rotterdam (NLRTM)", "corridor": "Asia-Europe"},
    {"origin": "Ningbo (CNNGB)", "destination": "Los Angeles (USLAX)", "corridor": "Trans-Pacific"},
    {"origin": "Mumbai (INBOM)", "destination": "Hamburg (DEHAM)", "corridor": "South Asia-Europe"},
    {"origin": "Singapore (SGSIN)", "destination": "New York (USNYC)", "corridor": "Southeast Asia-US East Coast"},
    {"origin": "Busan (KRPUS)", "destination": "Long Beach (USLGB)", "corridor": "Trans-Pacific"},
    {"origin": "Yokohama (JPYOK)", "destination": "Antwerp (BEANR)", "corridor": "Asia-Europe"},
    {"origin": "Shenzhen (CNSZX)", "destination": "Felixstowe (GBFXT)", "corridor": "Asia-Europe"},
    {"origin": "Santos (BRSSZ)", "destination": "Rotterdam (NLRTM)", "corridor": "Latin America-Europe"},
    {"origin": "Dubai (AEDXB)", "destination": "Singapore (SGSIN)", "corridor": "Middle East-Asia"},
    {"origin": "Chennai (INMAA)", "destination": "Dubai (AEDXB)", "corridor": "South Asia-Middle East"},
    {"origin": "Ho Chi Minh (VNSGN)", "destination": "Seattle (USSEA)", "corridor": "Trans-Pacific"},
    {"origin": "Qingdao (CNTAO)", "destination": "Valencia (ESVLC)", "corridor": "Asia-Mediterranean"},
    {"origin": "Kaohsiung (TWKHH)", "destination": "Oakland (USOAK)", "corridor": "Trans-Pacific"},
    {"origin": "Chittagong (BDCGP)", "destination": "Le Havre (FRLEH)", "corridor": "South Asia-Europe"},
    {"origin": "Colombo (LKCMB)", "destination": "London Gateway (GBLGW)", "corridor": "South Asia-Europe"},
    {"origin": "Tokyo (TYO)", "destination": "Frankfurt (FRA)", "corridor": "Asia-Europe Air/Multi"},
    {"origin": "Bangkok (THBKK)", "destination": "Rotterdam (NLRTM)", "corridor": "Southeast Asia-Europe"},
    {"origin": "Jakarta (IDJKT)", "destination": "Los Angeles (USLAX)", "corridor": "Trans-Pacific"},
    {"origin": "Mundra (INMUN)", "destination": "Genoa (ITGOA)", "corridor": "South Asia-Mediterranean"},
    {"origin": "Manila (PHMNL)", "destination": "Vancouver (CAVAN)", "corridor": "Trans-Pacific"},
    {"origin": "Port Klang (MYPKG)", "destination": "Sydney (AUMEL)", "corridor": "Asia-Oceania"},
    {"origin": "Tanjung Pelepas (MYTPP)", "destination": "Bremerhaven (DEBRV)", "corridor": "Asia-Europe"},
    {"origin": "Incheon (KRINC)", "destination": "Chicago (USCHI)", "corridor": "Trans-Pacific Multi"},
    {"origin": "Durban (ZADUR)", "destination": "Rotterdam (NLRTM)", "corridor": "Africa-Europe"},
    {"origin": "Veracruz (MXVER)", "destination": "Barcelona (ESBCN)", "corridor": "Trans-Atlantic"},
    {"origin": "Alexandria (EGALY)", "destination": "Marseille (FRMRS)", "corridor": "Intra-Med"},
    {"origin": "Kobe (JPUKB)", "destination": "Savannah (USSAV)", "corridor": "Trans-Pacific"},
    {"origin": "Jebel Ali (AEJEA)", "destination": "Cape Town (ZACPT)", "corridor": "Middle East-Africa"},
    {"origin": "Taipei (TPE)", "destination": "Amsterdam (AMS)", "corridor": "Asia-Europe Air/Multi"},
    {"origin": "Karachi (PKKHI)", "destination": "Piraeus (GRPIR)", "corridor": "South Asia-Med"}
]

CARGO_TYPES = [
    {"type": "High-Value Electronics", "urgency": "High", "time_sensitivity": 0.8, "risk_sensitivity": 0.9},
    {"type": "Pharmaceuticals (Cold Chain)", "urgency": "Critical", "time_sensitivity": 0.9, "risk_sensitivity": 0.95},
    {"type": "Industrial Machinery", "urgency": "Medium", "time_sensitivity": 0.4, "risk_sensitivity": 0.5},
    {"type": "Apparel & Fast Fashion", "urgency": "High", "time_sensitivity": 0.7, "risk_sensitivity": 0.4},
    {"type": "Raw Commodities", "urgency": "Low", "time_sensitivity": 0.2, "risk_sensitivity": 0.3},
    {"type": "Automotive Parts (JIT)", "urgency": "Critical", "time_sensitivity": 0.85, "risk_sensitivity": 0.7}
]

ROUTE_ARCHETYPES = [
    {
        "name": "Economic Standard Ocean",
        "mode": "Ocean",
        "carrier_pool": ["MSC", "Cosco Shipping", "Evergreen", "Ocean Network Express"],
        "cost_multiplier": 1.0,
        "time_multiplier": 1.0,
        "delay_prob_range": (0.25, 0.45),
        "congestion_range": (50, 85),
        "geopolitical_range": (20, 60),
        "hubs": ["Singapore", "Colombo", "Suez Canal"]
    },
    {
        "name": "Express Direct Ocean",
        "mode": "Ocean-Express",
        "carrier_pool": ["Maersk", "CMA CGM", "Hapag-Lloyd"],
        "cost_multiplier": 1.35,
        "time_multiplier": 0.75,
        "delay_prob_range": (0.10, 0.22),
        "congestion_range": (20, 45),
        "geopolitical_range": (20, 50),
        "hubs": ["Direct / Single Transshipment"]
    },
    {
        "name": "Resilient Cape / Geopolitical Bypass",
        "mode": "Ocean-Resilient",
        "carrier_pool": ["Maersk", "MSC Resilient Lane", "Hapag-Lloyd Alternative"],
        "cost_multiplier": 1.25,
        "time_multiplier": 1.20,
        "delay_prob_range": (0.08, 0.18),
        "congestion_range": (15, 35),
        "geopolitical_range": (5, 20),
        "hubs": ["Cape of Good Hope (Bypasses Red Sea)", "Port Louis"]
    },
    {
        "name": "Multimodal Sea-Air / Sea-Rail Express",
        "mode": "Multimodal / Air-Sea",
        "carrier_pool": ["Emirates SkyCargo / DP World", "DHL Global Forwarding", "Kuehne+Nagel"],
        "cost_multiplier": 2.40,
        "time_multiplier": 0.45,
        "delay_prob_range": (0.05, 0.12),
        "congestion_range": (10, 30),
        "geopolitical_range": (10, 30),
        "hubs": ["Dubai Air Cargo Hub", "Baku Rail Hub"]
    }
]


def generate_shipments_dataset(num_shipments: int = 30, seed: int = 42) -> pd.DataFrame:
    """
    Generates a synthetic dataset of shipments with 4 distinct route options each.
    Total records = num_shipments * 4 = 120 route options.
    """
    np.random.seed(seed)
    records: List[Dict[str, Any]] = []

    for i in range(num_shipments):
        lane = TRADE_LANES[i % len(TRADE_LANES)]
        cargo = CARGO_TYPES[i % len(CARGO_TYPES)]
        shipment_id = f"SHP-{i+1:03d}"

        # Baseline cost and time based on lane distance heuristics
        base_cost = np.random.uniform(2800, 4800)
        base_days = np.random.uniform(22, 34)

        # Baseline constraints for the shipment
        # Max budget ~ 1.8x base cost, Max transit days ~ 1.3x base days
        max_budget = round(base_cost * np.random.uniform(1.6, 2.2), -2)
        max_transit_days = round(base_days * np.random.uniform(1.15, 1.45), 1)

        # Every 7th shipment has tighter constraints to test boundary / infeasibility handling
        if (i + 1) % 7 == 0:
            max_transit_days = round(base_days * 0.85, 1)  # Strict rush
        if (i + 1) % 9 == 0:
            max_budget = round(base_cost * 1.15, -2)       # Tight budget

        for r_idx, archetype in enumerate(ROUTE_ARCHETYPES, start=1):
            route_id = f"{shipment_id}-R{r_idx}"
            carrier = np.random.choice(archetype["carrier_pool"])

            # Calculate metrics with realistic random variation
            cost = round(base_cost * archetype["cost_multiplier"] * np.random.uniform(0.95, 1.05), 2)
            transit_days = round(base_days * archetype["time_multiplier"] * np.random.uniform(0.93, 1.07), 1)

            delay_p = round(float(np.random.uniform(*archetype["delay_prob_range"])), 3)
            congestion = round(float(np.random.uniform(*archetype["congestion_range"])), 1)
            geopol_risk = round(float(np.random.uniform(*archetype["geopolitical_range"])), 1)

            # Carbon estimation (approx 0.03 kg CO2/ton-km for ocean, 0.5 for air-multimodal)
            carbon_factor = 3200 if "Multimodal" in archetype["name"] else 950
            carbon_kg = round(float(transit_days * carbon_factor * np.random.uniform(0.9, 1.1)), 1)

            # Intermediate hubs
            hubs_str = " -> ".join(archetype["hubs"])

            records.append({
                "shipment_id": shipment_id,
                "origin": lane["origin"],
                "destination": lane["destination"],
                "corridor": lane["corridor"],
                "cargo_type": cargo["type"],
                "urgency": cargo["urgency"],
                "max_budget_usd": max_budget,
                "max_transit_days": max_transit_days,
                "route_id": route_id,
                "route_name": archetype["name"],
                "carrier": carrier,
                "transport_mode": archetype["mode"],
                "intermediate_hubs": hubs_str,
                "cost_usd": cost,
                "transit_time_days": transit_days,
                "delay_probability": delay_p,
                "congestion_risk": congestion,
                "geopolitical_risk": geopol_risk,
                "carbon_emissions_kg": carbon_kg
            })

    df = pd.DataFrame(records)
    return df


def save_dataset(output_path: str = "data/shipments.csv", num_shipments: int = 30) -> Path:
    """Generates and saves the dataset to CSV format."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_shipments_dataset(num_shipments=num_shipments)
    df.to_csv(path, index=False)
    print(f"Generated {len(df)} routes across {num_shipments} shipments saved to: {path}")
    return path


if __name__ == "__main__":
    save_dataset()
