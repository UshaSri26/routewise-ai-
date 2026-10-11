"""Practical freight quotes for custom corridors."""

from src.custom_shipment import parse_and_generate_corridor
from src.data_generator import generate_shipments_dataset
from src.freight_costs import india_domestic_quotes, international_lcl_quotes


def test_hyderabad_warangal_costs_are_carton_scale():
    df = generate_shipments_dataset()
    routes, _, _, msg = parse_and_generate_corridor(
        "cheapest parcel from Hyderabad to Warangal", df
    )
    assert "Warangal" in msg
    # 10 kg carton estimates include a reasonable handling charge and stay parcel-scale.
    assert (routes["cost_usd"] < 10).all()
    assert routes["cost_usd"].min() >= 2.5
    assert routes["cost_usd"].max() >= 7.5


def test_international_sample_not_full_container():
    quotes = international_lcl_quotes(19800)
    assert 190 <= quotes["ocean"]["cost_usd"] <= 220
    assert 420 <= quotes["air"]["cost_usd"] <= 450


def test_india_quotes_hyd_wgl():
    quotes = india_domestic_quotes(155)
    assert 2.5 <= quotes["rail"]["cost_usd"] <= 3.0
    assert 8 <= quotes["fast"]["cost_usd"] <= 10


def test_domestic_long_haul_quotes_include_small_shipment_costs():
    quotes = india_domestic_quotes(1410)
    assert 1000 <= quotes["rail"]["cost_usd"] * 84 <= 1200
    assert 1400 <= quotes["surface"]["cost_usd"] * 84 <= 1700
    assert 2000 <= quotes["express"]["cost_usd"] * 84 <= 2400
    assert 3000 <= quotes["fast"]["cost_usd"] * 84 <= 3400
