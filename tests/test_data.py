"""
Tests for synthetic dataset generation.
Verifies structure, scale, nulls, and realistic boundary conditions.
"""

import pandas as pd
from src.data_generator import generate_shipments_dataset, TRADE_LANES


def test_dataset_generation_shape():
    """Dataset should contain exactly 30 shipments with 4 routes each = 120 rows."""
    df = generate_shipments_dataset(num_shipments=30, seed=42)
    assert len(df) == 120
    assert df["shipment_id"].nunique() == 30
    
    # Each shipment must have exactly 4 routes
    route_counts = df.groupby("shipment_id")["route_id"].count()
    assert (route_counts == 4).all()


def test_dataset_value_ranges():
    """Verify numeric values fall within expected real-world domains."""
    df = generate_shipments_dataset(num_shipments=30, seed=42)
    
    # Costs must be positive and parcel-scale, not container freight
    assert (df["cost_usd"] > 0).all()
    assert df["cost_usd"].max() < 500
    
    # Transit days must be positive
    assert (df["transit_time_days"] > 0).all()
    
    # Delay probability must be strictly within [0, 1]
    assert (df["delay_probability"] >= 0.0).all()
    assert (df["delay_probability"] <= 1.0).all()
    
    # Congestion and Geopolitical Risk must be within [0, 100]
    assert (df["congestion_risk"] >= 0.0).all()
    assert (df["congestion_risk"] <= 100.0).all()
    assert (df["geopolitical_risk"] >= 0.0).all()
    assert (df["geopolitical_risk"] <= 100.0).all()
    
    # No null values across key fields
    assert not df[["shipment_id", "route_id", "cost_usd", "transit_time_days"]].isnull().any().any()
