"""
Unit and Integration Tests for RouteWise AI Optimizer and Explainability Layer.
Tests mathematical scoring, constraints, Pareto dominance, edge cases, and zero-division resilience.
"""

import pytest
import pandas as pd
import numpy as np
from src.optimizer import (
    RouteOptimizer,
    WeightsConfig,
    HardConstraints,
    EvaluatedRoute,
    run_sensitivity_analysis
)
from src.explanations import RuleBasedExplainer
from src.data_generator import generate_shipments_dataset


@pytest.fixture
def sample_routes_df():
    """Returns 4 realistic routes for a single shipment."""
    return pd.DataFrame([
        {
            "shipment_id": "SHP-TEST",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "cargo_type": "Electronics",
            "urgency": "High",
            "route_id": "R1-BUDGET",
            "route_name": "Budget Ocean",
            "carrier": "MSC",
            "transport_mode": "Ocean",
            "intermediate_hubs": "Singapore -> Suez",
            "cost_usd": 3000.0,
            "transit_time_days": 28.0,
            "delay_probability": 0.35,
            "congestion_risk": 70.0,
            "geopolitical_risk": 50.0
        },
        {
            "shipment_id": "SHP-TEST",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "cargo_type": "Electronics",
            "urgency": "High",
            "route_id": "R2-EXPRESS",
            "route_name": "Express Direct",
            "carrier": "Maersk",
            "transport_mode": "Ocean-Express",
            "intermediate_hubs": "Direct",
            "cost_usd": 4200.0,
            "transit_time_days": 18.0,
            "delay_probability": 0.12,
            "congestion_risk": 30.0,
            "geopolitical_risk": 30.0
        },
        {
            "shipment_id": "SHP-TEST",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "cargo_type": "Electronics",
            "urgency": "High",
            "route_id": "R3-RESILIENT",
            "route_name": "Resilient Cape",
            "carrier": "Hapag-Lloyd",
            "transport_mode": "Ocean-Resilient",
            "intermediate_hubs": "Cape of Good Hope",
            "cost_usd": 3800.0,
            "transit_time_days": 32.0,
            "delay_probability": 0.08,
            "congestion_risk": 15.0,
            "geopolitical_risk": 10.0
        },
        {
            "shipment_id": "SHP-TEST",
            "origin": "Shanghai",
            "destination": "Rotterdam",
            "cargo_type": "Electronics",
            "urgency": "High",
            "route_id": "R4-AIR",
            "route_name": "Air Multimodal",
            "carrier": "Emirates",
            "transport_mode": "Multimodal",
            "intermediate_hubs": "Dubai Air Cargo",
            "cost_usd": 8500.0,
            "transit_time_days": 7.0,
            "delay_probability": 0.05,
            "congestion_risk": 10.0,
            "geopolitical_risk": 15.0
        }
    ])


def test_weights_validation():
    """Ensures weights must be non-negative and sum to 1.0."""
    valid = WeightsConfig(cost=0.5, time=0.3, risk=0.2)
    valid.validate()  # Should not raise

    with pytest.raises(ValueError, match="must sum to 1.0"):
        invalid_sum = WeightsConfig(cost=0.6, time=0.6, risk=0.1)
        invalid_sum.validate()

    with pytest.raises(ValueError, match="cannot be negative"):
        invalid_neg = WeightsConfig(cost=-0.2, time=0.7, risk=0.5)
        invalid_neg.validate()


def test_polar_weight_cost(sample_routes_df):
    """When cost weight is 1.0, the cheapest route must win."""
    weights = WeightsConfig(cost=1.0, time=0.0, risk=0.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, weights=weights)
    assert result.recommended_route is not None
    assert result.recommended_route.route_id == "R1-BUDGET"
    assert result.recommended_route.cost_usd == 3000.0


def test_polar_weight_time(sample_routes_df):
    """When time weight is 1.0, the fastest route must win."""
    weights = WeightsConfig(cost=0.0, time=1.0, risk=0.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, weights=weights)
    assert result.recommended_route is not None
    assert result.recommended_route.route_id == "R4-AIR"
    assert result.recommended_route.transit_time_days == 7.0


def test_polar_weight_risk(sample_routes_df):
    """When risk weight is 1.0, the route with lowest composite risk must win."""
    weights = WeightsConfig(cost=0.0, time=0.0, risk=1.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, weights=weights)
    assert result.recommended_route is not None
    # R3 has very low delay, congestion, and geopolitical risk
    assert result.recommended_route.route_id in ["R3-RESILIENT", "R4-AIR"]


def test_hard_constraint_budget_exclusion(sample_routes_df):
    """Routes exceeding max budget must be invalidated."""
    constraints = HardConstraints(max_budget_usd=4000.0)
    # Even if time is 1.0 (favoring Air $8500), Air must be excluded due to budget
    weights = WeightsConfig(cost=0.0, time=1.0, risk=0.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, weights=weights, constraints=constraints)
    
    assert result.recommended_route.route_id != "R4-AIR"
    assert result.recommended_route.cost_usd <= 4000.0
    
    # R4-AIR should be in all_routes marked as not feasible
    air_route = next(r for r in result.all_routes if r.route_id == "R4-AIR")
    assert not air_route.is_feasible
    assert any("budget" in reason.lower() for reason in air_route.invalidation_reasons)


def test_hard_constraint_transit_time(sample_routes_df):
    """Routes exceeding max transit days must be invalidated."""
    constraints = HardConstraints(max_transit_days=20.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, constraints=constraints)
    
    assert result.recommended_route.transit_time_days <= 20.0
    budget_route = next(r for r in result.all_routes if r.route_id == "R1-BUDGET")
    assert not budget_route.is_feasible
    assert any("transit time" in reason.lower() for reason in budget_route.invalidation_reasons)


def test_all_infeasible_graceful_fallback(sample_routes_df):
    """When constraints are impossible to satisfy, engine handles it gracefully."""
    impossible_constraints = HardConstraints(max_budget_usd=1000.0, max_transit_days=3.0)
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df, constraints=impossible_constraints)
    
    assert result.all_infeasible is True
    assert result.recommended_route is not None  # Best effort fallback provided
    explanation = RuleBasedExplainer.generate_explanation(result)
    assert "INFEASIBLE CONSTRAINTS DETECTED" in explanation


def test_pareto_dominance_detection():
    """A route strictly worse in all metrics must be flagged as Pareto-dominated."""
    df = pd.DataFrame([
        {
            "shipment_id": "TEST-DOM",
            "origin": "A",
            "destination": "B",
            "route_id": "R-SUPERIOR",
            "route_name": "Superior Route",
            "carrier": "Carrier A",
            "transport_mode": "Ocean",
            "intermediate_hubs": "Direct",
            "cost_usd": 3000.0,
            "transit_time_days": 15.0,
            "delay_probability": 0.1,
            "congestion_risk": 20.0,
            "geopolitical_risk": 20.0
        },
        {
            "shipment_id": "TEST-DOM",
            "origin": "A",
            "destination": "B",
            "route_id": "R-INFERIOR",
            "route_name": "Inferior Route",
            "carrier": "Carrier B",
            "transport_mode": "Ocean",
            "intermediate_hubs": "Hub X",
            "cost_usd": 4000.0,         # Worse cost
            "transit_time_days": 25.0,  # Worse time
            "delay_probability": 0.4,   # Worse risk
            "congestion_risk": 60.0,
            "geopolitical_risk": 60.0
        }
    ])
    result = RouteOptimizer.evaluate_shipment_routes(df)
    inferior = next(r for r in result.all_routes if r.route_id == "R-INFERIOR")
    assert inferior.is_pareto_dominated is True
    assert "R-SUPERIOR" in inferior.dominated_by


def test_identical_metrics_zero_division():
    """Identical routes must not crash or trigger division by zero."""
    df = pd.DataFrame([
        {
            "shipment_id": "IDENTICAL",
            "origin": "A",
            "destination": "B",
            "route_id": f"R{i}",
            "route_name": f"Route {i}",
            "carrier": "Carrier",
            "transport_mode": "Ocean",
            "intermediate_hubs": "None",
            "cost_usd": 3000.0,
            "transit_time_days": 20.0,
            "delay_probability": 0.2,
            "congestion_risk": 40.0,
            "geopolitical_risk": 30.0
        }
        for i in range(1, 4)
    ])
    result = RouteOptimizer.evaluate_shipment_routes(df)
    assert result.recommended_route is not None
    assert np.isclose(result.recommended_route.total_score, 0.0)


def test_sensitivity_analysis_structure(sample_routes_df):
    """Sensitivity analysis should yield distinct recommendations across 4 profiles."""
    sens_df = run_sensitivity_analysis(sample_routes_df)
    assert len(sens_df) == 4
    assert "Profile" in sens_df.columns
    assert "Recommended Route" in sens_df.columns


def test_rule_based_explainer(sample_routes_df):
    """Explainer must produce rich markdown containing numbers and carrier details."""
    result = RouteOptimizer.evaluate_shipment_routes(sample_routes_df)
    text = RuleBasedExplainer.generate_explanation(result)
    assert result.recommended_route.route_id in text
    assert "$" in text
    assert "Trade-off" in text
