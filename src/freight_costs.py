"""
Practical freight quotes for SME-scale shipments (not full 40ft peak-season FCL).

Domestic India: ~50 kg commercial carton / small PTL.
International: ~1 CBM LCL (~200 kg mixed cargo).
"""

from __future__ import annotations

from typing import Dict, Any

INR_PER_USD = 84.0


def usd_from_inr(inr: float) -> float:
    return round(max(0.5, inr / INR_PER_USD), 2)


def india_domestic_quotes(distance_km: float) -> Dict[str, Any]:
    """
    Realistic India carton rates (Delhivery / Gati / BlueDart ballpark).

    Hyderabad → Warangal (~150 km): about ₹180–₹750, not ₹3,000+.
    Mumbai → Delhi (~1,400 km): about ₹1,500–₹5,500.
    """
    km = max(30.0, float(distance_km))

    rail_inr = max(110.0, 40 + 1.00 * km)
    surface_inr = max(150.0, 60 + 1.45 * km)
    express_inr = max(240.0, 95 + 2.20 * km)

    truck_hours = max(1.5, round((km / 42.0) + 1.2, 1))
    rail_hours = max(1.2, round((km / 50.0) + 1.4, 1))
    express_hours = max(1.0, round((km / 62.0) + 0.4, 1))

    if km < 280:
        fast_inr = max(320.0, 170 + 2.90 * km)
        fast_hours = max(0.8, round(express_hours * 0.82, 1))
        fast_name = "Same-Day Highway Courier"
        fast_mode = "Priority Road Express"
        fast_carrier = "Dunzo / Porter / Local Express"
    else:
        fast_inr = max(480.0, 220 + 3.10 * km)
        fast_hours = max(2.5, round(3.0 + (km / 700.0), 1))
        fast_name = "Domestic Air Cargo"
        fast_mode = "Air Freight"
        fast_carrier = "Indigo Cargo / BlueDart Aviation"

    return {
        "rail": {
            "name": "Rail Parcel / CONCOR",
            "mode": "Dedicated Rail Corridor",
            "carrier": "Indian Railways Freight / CONCOR",
            "cost_usd": usd_from_inr(rail_inr),
            "hours": rail_hours,
            "delay_probability": 0.07,
            "congestion_risk": 16.0,
            "geopolitical_risk": 2.0,
            "carbon_kg_per_km": 0.05,
        },
        "surface": {
            "name": "Surface PTL Truck",
            "mode": "Ground Truckload",
            "carrier": "VRL Logistics / TCI Freight",
            "cost_usd": usd_from_inr(surface_inr),
            "hours": truck_hours,
            "delay_probability": 0.16,
            "congestion_risk": 38.0,
            "geopolitical_risk": 3.0,
            "carbon_kg_per_km": 0.12,
        },
        "express": {
            "name": "Express Road Courier",
            "mode": "Express Roadway",
            "carrier": "BlueDart / DTDC Express",
            "cost_usd": usd_from_inr(express_inr),
            "hours": express_hours,
            "delay_probability": 0.08,
            "congestion_risk": 22.0,
            "geopolitical_risk": 3.0,
            "carbon_kg_per_km": 0.14,
        },
        "fast": {
            "name": fast_name,
            "mode": fast_mode,
            "carrier": fast_carrier,
            "cost_usd": usd_from_inr(fast_inr),
            "hours": fast_hours,
            "delay_probability": 0.04,
            "congestion_risk": 10.0,
            "geopolitical_risk": 2.0,
            "carbon_kg_per_km": 0.26 if km >= 280 else 0.16,
        },
    }


def international_lcl_quotes(distance_km: float) -> Dict[str, Any]:
    """
    1 CBM LCL quotes (small-business shipment), not a peak-season 40ft box.

    Shanghai → Rotterdam (~20,000 km): ocean ~$350–$500, air ~$1,600.
    """
    km = max(400.0, float(distance_km))

    ocean_days = round(max(6.0, km / 780.0), 1)
    express_days = round(max(4.5, ocean_days * 0.72), 1)
    resilient_days = round(max(7.0, ocean_days * 1.16), 1)
    air_days = round(max(1.2, 1.0 + km / 7200.0), 1)

    ocean_cost = round(max(85.0, 65 + 0.0135 * km), 2)
    express_cost = round(max(115.0, 90 + 0.0180 * km), 2)
    resilient_cost = round(max(105.0, 80 + 0.0160 * km), 2)
    air_cost = round(max(190.0, 140 + 0.072 * km), 2)

    return {
        "ocean": {
            "name": "Standard Ocean LCL",
            "mode": "Ocean",
            "carrier": "MSC / Cosco Shipping",
            "cost_usd": ocean_cost,
            "days": ocean_days,
            "delay_probability": 0.28,
            "congestion_risk": 62.0,
            "geopolitical_risk": 35.0,
            "hubs": "Origin Port -> Transshipment Hub -> Destination Port",
        },
        "express": {
            "name": "Express Direct Ocean",
            "mode": "Ocean-Express",
            "carrier": "Maersk / CMA CGM",
            "cost_usd": express_cost,
            "days": express_days,
            "delay_probability": 0.14,
            "congestion_risk": 32.0,
            "geopolitical_risk": 28.0,
            "hubs": "Direct / Single Transshipment",
        },
        "resilient": {
            "name": "Resilient Ocean (Chokepoint Bypass)",
            "mode": "Ocean-Resilient",
            "carrier": "Hapag-Lloyd Alternative",
            "cost_usd": resilient_cost,
            "days": resilient_days,
            "delay_probability": 0.10,
            "congestion_risk": 22.0,
            "geopolitical_risk": 12.0,
            "hubs": "Cape of Good Hope (Bypasses Red Sea)",
        },
        "air": {
            "name": "Air Freight Priority",
            "mode": "Air Freight",
            "carrier": "Emirates SkyCargo / DHL",
            "cost_usd": air_cost,
            "days": air_days,
            "delay_probability": 0.05,
            "congestion_risk": 12.0,
            "geopolitical_risk": 10.0,
            "hubs": "Origin Airport -> Cargo Hub -> Destination Gateway",
        },
    }


# Typical nautical / highway distance (km) used when generating the benchmark dataset.
CORRIDOR_DISTANCE_KM = {
    "Asia-Europe": 19800,
    "Trans-Pacific": 11200,
    "South Asia-Europe": 17200,
    "Southeast Asia-US East Coast": 17800,
    "Latin America-Europe": 9800,
    "Middle East-Asia": 6400,
    "South Asia-Middle East": 2800,
    "Asia-Mediterranean": 15200,
    "Asia-Oceania": 7200,
    "Trans-Pacific Multi": 12500,
    "Africa-Europe": 11000,
    "Trans-Atlantic": 8200,
    "Intra-Med": 2200,
    "Middle East-Africa": 7800,
    "South Asia-Med": 6800,
    "South Asia-Mediterranean": 7200,
    "Southeast Asia-Europe": 16500,
    "Asia-Europe Air/Multi": 9000,
    "India Domestic": 450,
}
