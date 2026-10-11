"""
Synthetic Shipment and Route Dataset Generator for RouteWise AI.
Generates realistic global trade corridors with explicit trade-offs across cost, transit time, and risk.
"""

from pathlib import Path
from typing import List, Dict, Any
import numpy as np
import pandas as pd

from src.freight_costs import CORRIDOR_DISTANCE_KM, india_domestic_quotes, international_lcl_quotes

# India parcel lanes first so the demo catalog is SME-practical, then small export samples
INDIA_LANES = [
    {"origin": "Hyderabad", "destination": "Warangal", "corridor": "India Domestic", "km": 155},
    {"origin": "Hyderabad", "destination": "Visakhapatnam", "corridor": "India Domestic", "km": 620},
    {"origin": "Chennai", "destination": "Bengaluru", "corridor": "India Domestic", "km": 350},
    {"origin": "Mumbai", "destination": "Delhi", "corridor": "India Domestic", "km": 1410},
    {"origin": "Pune", "destination": "Hyderabad", "corridor": "India Domestic", "km": 560},
    {"origin": "Bengaluru", "destination": "Hyderabad", "corridor": "India Domestic", "km": 575},
    {"origin": "Ahmedabad", "destination": "Mumbai", "corridor": "India Domestic", "km": 530},
    {"origin": "Kolkata", "destination": "Chennai", "corridor": "India Domestic", "km": 1670},
    {"origin": "Hyderabad", "destination": "Vijayawada", "corridor": "India Domestic", "km": 275},
    {"origin": "Delhi", "destination": "Jaipur", "corridor": "India Domestic", "km": 280},
    {"origin": "Bengaluru", "destination": "Chennai", "corridor": "India Domestic", "km": 350},
    {"origin": "Mumbai", "destination": "Pune", "corridor": "India Domestic", "km": 150},
    {"origin": "Hyderabad", "destination": "Bengaluru", "corridor": "India Domestic", "km": 575},
    {"origin": "Chennai", "destination": "Hyderabad", "corridor": "India Domestic", "km": 630},
    {"origin": "Surat", "destination": "Mumbai", "corridor": "India Domestic", "km": 280},
    {"origin": "Nagpur", "destination": "Hyderabad", "corridor": "India Domestic", "km": 500},
    {"origin": "Kochi", "destination": "Bengaluru", "corridor": "India Domestic", "km": 550},
    {"origin": "Lucknow", "destination": "Delhi", "corridor": "India Domestic", "km": 550},
]

TRADE_LANES = INDIA_LANES + [
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

INDIA_CARGO_TYPES = [
    {"type": "Commercial carton (~10 kg)", "urgency": "Medium", "time_sensitivity": 0.4, "risk_sensitivity": 0.3},
    {"type": "Apparel / samples", "urgency": "High", "time_sensitivity": 0.7, "risk_sensitivity": 0.4},
    {"type": "Electronics accessories", "urgency": "High", "time_sensitivity": 0.8, "risk_sensitivity": 0.6},
    {"type": "Pharma samples", "urgency": "Critical", "time_sensitivity": 0.85, "risk_sensitivity": 0.7},
]

INTL_CARGO_TYPES = [
    {"type": "Export samples (~15 kg)", "urgency": "High", "time_sensitivity": 0.7, "risk_sensitivity": 0.5},
    {"type": "Apparel samples (0.1 CBM)", "urgency": "High", "time_sensitivity": 0.75, "risk_sensitivity": 0.4},
    {"type": "Spare parts parcel", "urgency": "Critical", "time_sensitivity": 0.85, "risk_sensitivity": 0.6},
    {"type": "Documents & product samples", "urgency": "Medium", "time_sensitivity": 0.5, "risk_sensitivity": 0.3},
]

CARGO_TYPES = INDIA_CARGO_TYPES + INTL_CARGO_TYPES

# Legacy ocean archetype labels kept for international LCL quote mapping
INTL_QUOTE_KEYS = ("ocean", "express", "resilient", "air")
INDIA_QUOTE_KEYS = ("surface", "rail", "express", "fast")


def generate_shipments_dataset(num_shipments: int = 30, seed: int = 42) -> pd.DataFrame:
    """
    Generates a synthetic dataset of shipments with 4 distinct route options each.
    Total records = num_shipments * 4 = 120 route options.
    """
    np.random.seed(seed)
    records: List[Dict[str, Any]] = []

    for i in range(num_shipments):
        lane = TRADE_LANES[i % len(TRADE_LANES)]
        shipment_id = f"SHP-{i+1:03d}"
        is_india = lane["corridor"] == "India Domestic"
        cargo_pool = INDIA_CARGO_TYPES if is_india else INTL_CARGO_TYPES
        cargo = cargo_pool[i % len(cargo_pool)]

        if is_india:
            quotes = india_domestic_quotes(float(lane.get("km", 450)))
            ordered = [quotes[k] for k in INDIA_QUOTE_KEYS]
        else:
            km = float(CORRIDOR_DISTANCE_KM.get(lane["corridor"], 12000))
            quotes = international_lcl_quotes(km)
            ordered = [quotes[k] for k in INTL_QUOTE_KEYS]

        peak_cost = max(q["cost_usd"] for q in ordered)
        if is_india:
            peak_days = max(q["hours"] for q in ordered) / 24.0
        else:
            peak_days = max(q["days"] for q in ordered)

        max_budget = round(peak_cost * np.random.uniform(1.25, 1.70), 2)
        max_transit_days = round(peak_days * np.random.uniform(1.15, 1.45), 2)

        # Every 7th shipment has tighter constraints to test boundary / infeasibility handling
        if (i + 1) % 7 == 0:
            max_transit_days = round(peak_days * 0.85, 2)
        if (i + 1) % 9 == 0:
            max_budget = round(peak_cost * 1.08, 2)

        for r_idx, quote in enumerate(ordered, start=1):
            route_id = f"{shipment_id}-R{r_idx}"
            cost = round(quote["cost_usd"] * float(np.random.uniform(0.94, 1.06)), 2)

            if is_india:
                hours = quote["hours"] * float(np.random.uniform(0.93, 1.07))
                transit_days = round(hours / 24.0, 3)
                hubs_str = f"{lane['origin']} -> {lane['destination']} (~{round(hours, 1)}h)"
                carbon_kg = round(float(lane.get("km", 450)) * quote["carbon_kg_per_km"], 1)
            else:
                transit_days = round(quote["days"] * float(np.random.uniform(0.94, 1.06)), 1)
                hubs_str = quote["hubs"]
                carbon_kg = round(float(transit_days * (18 if "Air" in quote["name"] else 6) * np.random.uniform(0.9, 1.1)), 1)

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
                "route_name": quote["name"],
                "carrier": quote["carrier"],
                "transport_mode": quote["mode"],
                "intermediate_hubs": hubs_str,
                "cost_usd": cost,
                "transit_time_days": transit_days,
                "delay_probability": quote["delay_probability"],
                "congestion_risk": quote["congestion_risk"],
                "geopolitical_risk": quote["geopolitical_risk"],
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
