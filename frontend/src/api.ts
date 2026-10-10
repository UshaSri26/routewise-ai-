// API client — all fetch() calls to the FastAPI backend at port 8000

import type { OptimizationResult, Shipment, ScenarioResult, Weights, Constraints } from './types';

const BASE = 'http://localhost:8000';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? 'Request failed');
  }
  return res.json();
}

export async function getShipments(): Promise<Shipment[]> {
  const data = await request<{ shipments: Shipment[] }>('/api/shipments');
  return data.shipments;
}

export async function optimize(
  shipment_id: string,
  weights: Weights,
  constraints: Constraints = {},
): Promise<OptimizationResult> {
  return request<OptimizationResult>('/api/optimize', {
    method: 'POST',
    body: JSON.stringify({ shipment_id, weights, constraints }),
  });
}

export async function customOptimize(prompt: string): Promise<OptimizationResult> {
  return request<OptimizationResult>('/api/custom-optimize', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  });
}

export async function getScenarios(shipment_id: string): Promise<ScenarioResult[]> {
  const data = await request<{ scenarios: ScenarioResult[] }>(`/api/scenarios/${shipment_id}`);
  return data.scenarios;
}

export async function ask(
  question: string,
  shipment_id?: string,
  weights?: Weights,
): Promise<string> {
  const data = await request<{ answer: string }>('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question, shipment_id, weights }),
  });
  return data.answer;
}

export async function checkHealth(): Promise<boolean> {
  try {
    await request<{ status: string }>('/api/health');
    return true;
  } catch {
    return false;
  }
}
