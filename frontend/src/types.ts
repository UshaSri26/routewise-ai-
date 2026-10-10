// Shared TypeScript types matching Python API response shapes

export interface Shipment {
  shipment_id: string;
  origin: string;
  destination: string;
}

export interface RouteResult {
  route_id: string;
  hubs: string;
  mode: string;
  cost: number;
  transit_days: number;
  delay_probability: number;
  composite_risk: number;
  score: number;
  feasible: boolean;
  pareto_dominant: boolean;
}

export interface OptimizationResult {
  recommended: RouteResult | null;
  all_routes: RouteResult[];
  feasible_count: number;
  total_routes: number;
  infeasible_reason: string | null;
  explanation: string;
  parsed_origin?: string;
  parsed_destination?: string;
}

export interface ScenarioResult {
  profile: string;
  recommended_route: string;
  cost: number;
  transit_days: number;
  score: number;
  feasible: boolean;
}

export interface Weights {
  cost: number;
  time: number;
  risk: number;
}

export interface Constraints {
  max_budget?: number;
  max_days?: number;
  max_risk?: number;
}

export type NavPage = 'home' | 'optimize' | 'map' | 'scenarios' | 'assistant' | 'methodology';
