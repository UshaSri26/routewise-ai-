import { useState, useEffect } from 'react';
import { getShipments, optimize } from '../api';
import RouteCard from '../components/RouteCard';
import RouteTable from '../components/RouteTable';
import ScoreBar from '../components/ScoreBar';
import AIExplanation from '../components/AIExplanation';
import type { OptimizationResult, Shipment, Weights, Constraints } from '../types';

interface OptimizeProps {
  initialResult: OptimizationResult | null;
  initialShipment: Shipment | null;
  onResult: (result: OptimizationResult) => void;
}

const DEFAULT_WEIGHTS: Weights = { cost: 0.40, time: 0.30, risk: 0.30 };

export default function Optimize({ initialResult, initialShipment, onResult }: OptimizeProps) {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [weights, setWeights] = useState<Weights>(DEFAULT_WEIGHTS);
  const [constraints, setConstraints] = useState<Constraints>({});
  const [result, setResult] = useState<OptimizationResult | null>(initialResult);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getShipments().then((s) => {
      let list = s;
      if (initialShipment && !s.some((x) => x.shipment_id === initialShipment.shipment_id)) {
        list = [initialShipment, ...s];
      }
      setShipments(list);
      if (initialShipment) {
        setSelectedId(initialShipment.shipment_id);
      } else if (list.length > 0 && !selectedId) {
        setSelectedId(list[0].shipment_id);
      }
    }).catch(() => {});
  }, [initialShipment]);

  useEffect(() => {
    if (initialResult) setResult(initialResult);
  }, [initialResult]);

  const totalWeight = weights.cost + weights.time + weights.risk;
  const normalized: Weights = {
    cost: weights.cost / totalWeight,
    time: weights.time / totalWeight,
    risk: weights.risk / totalWeight,
  };

  const handleOptimize = async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await optimize(selectedId, normalized, constraints);
      setResult(res);
      onResult(res);
    } catch (err: any) {
      setError(err.message ?? 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const setWeight = (key: keyof Weights, value: number) => {
    setWeights((prev) => ({ ...prev, [key]: value }));
  };

  const selectedShipment = shipments.find((s) => s.shipment_id === selectedId);

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#F1F5F9]">Route Optimizer</h1>
        <p className="text-sm text-[#93A4B8] mt-1">
          Select a shipment, configure priorities, and run the MCDA optimizer.
        </p>
        <p className="text-xs text-[#93A4B8] mt-2">
          Costs are planning estimates for a 10 kg domestic carton or 15 kg / 0.1 CBM export sample—not live carrier quotes. Duties and taxes are excluded.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Config panel */}
        <div className="space-y-5">
          <div className="card space-y-4">
            <h2 className="text-sm font-semibold text-[#F1F5F9]">Shipment</h2>

            <div>
              <label className="label mb-2 block">Select Shipment</label>
              <select
                className="input-field"
                value={selectedId}
                onChange={(e) => setSelectedId(e.target.value)}
              >
                {shipments.map((s) => (
                  <option key={s.shipment_id} value={s.shipment_id}>
                    {s.shipment_id} — {s.origin} → {s.destination}
                  </option>
                ))}
              </select>
            </div>

            {selectedShipment && (
              <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-[#0A1626] border border-[#22344A]">
                <div>
                  <div className="label mb-1">Origin</div>
                  <div className="text-sm font-medium text-[#F1F5F9]">{selectedShipment.origin}</div>
                </div>
                <div>
                  <div className="label mb-1">Destination</div>
                  <div className="text-sm font-medium text-[#F1F5F9]">{selectedShipment.destination}</div>
                </div>
              </div>
            )}
          </div>

          <div className="card space-y-5">
            <h2 className="text-sm font-semibold text-[#F1F5F9]">Priority Weights</h2>
            <ScoreBar cost={normalized.cost} time={normalized.time} risk={normalized.risk} />

            {(['cost', 'time', 'risk'] as const).map((key) => (
              <div key={key}>
                <div className="flex justify-between items-center mb-2">
                  <label className="label capitalize">{key === 'time' ? 'Transit Time' : key}</label>
                  <span className="text-xs font-semibold text-[#21D4C2]">
                    {(normalized[key] * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range"
                  min={0}
                  max={10}
                  step={0.5}
                  value={weights[key]}
                  onChange={(e) => setWeight(key, parseFloat(e.target.value))}
                  className="w-full accent-[#21D4C2] cursor-pointer"
                />
              </div>
            ))}
          </div>

          <div className="card space-y-4">
            <h2 className="text-sm font-semibold text-[#F1F5F9]">Hard Constraints</h2>
            <p className="text-xs text-[#93A4B8]">Leave blank to apply no limit.</p>

            <div>
              <label className="label mb-2 block">Max Budget (USD)</label>
              <input
                type="number"
                className="input-field"
                placeholder="e.g. 12 (domestic) or 400 (export)"
                value={constraints.max_budget ?? ''}
                onChange={(e) => setConstraints((p) => ({ ...p, max_budget: e.target.value ? +e.target.value : undefined }))}
              />
            </div>
            <div>
              <label className="label mb-2 block">Max Transit Days</label>
              <input
                type="number"
                className="input-field"
                placeholder="e.g. 14"
                value={constraints.max_days ?? ''}
                onChange={(e) => setConstraints((p) => ({ ...p, max_days: e.target.value ? +e.target.value : undefined }))}
              />
            </div>
            <div>
              <label className="label mb-2 block">Max Risk Score</label>
              <input
                type="number"
                step="0.01"
                className="input-field"
                placeholder="e.g. 0.6"
                value={constraints.max_risk ?? ''}
                onChange={(e) => setConstraints((p) => ({ ...p, max_risk: e.target.value ? +e.target.value : undefined }))}
              />
            </div>

            <button
              onClick={handleOptimize}
              disabled={!selectedId || loading}
              className="btn-primary w-full flex items-center justify-center gap-2 py-3 mt-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
                  </svg>
                  Optimizing…
                </>
              ) : (
                <>
                  <svg width="14" height="14" fill="none" viewBox="0 0 24 24">
                    <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
                  </svg>
                  Optimize Routes
                </>
              )}
            </button>

            {error && (
              <div className="px-3 py-2 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-xs text-[#FB7185]">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Results panel */}
        <div className="lg:col-span-2 space-y-5">
          {!result ? (
            <div className="card flex flex-col items-center justify-center py-20 text-center">
              <div className="w-12 h-12 rounded-xl bg-[#21D4C2]/10 border border-[#21D4C2]/20 flex items-center justify-center mb-4">
                <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
                  <path d="M9 20l-5-5 5-5M4 15h16M15 4l5 5-5 5" stroke="#21D4C2" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <div className="text-sm font-medium text-[#F1F5F9] mb-1">No results yet</div>
              <div className="text-xs text-[#93A4B8]">Configure your preferences and click Optimize Routes</div>
            </div>
          ) : (
            <>
              {/* Recommended */}
              {result.recommended ? (
                <div>
                  <div className="label mb-3">Recommended Route</div>
                  <RouteCard route={result.recommended} isRecommended />
                </div>
              ) : (
                <div className="card border-[#FB7185]/30 bg-[#FB7185]/5">
                  <div className="text-sm font-semibold text-[#FB7185] mb-1">All routes infeasible</div>
                  <div className="text-xs text-[#93A4B8]">
                    {result.infeasible_reason ?? 'No route meets the current hard constraints.'}
                  </div>
                </div>
              )}

              {/* Summary stats */}
              <div className="grid grid-cols-3 gap-3">
                <StatCard label="Feasible" value={`${result.feasible_count}/${result.total_routes}`} color="#34D399" />
                <StatCard
                  label="Pareto-Dominant"
                  value={result.all_routes.filter((r) => r.pareto_dominant).length}
                  color="#21D4C2"
                />
                <StatCard
                  label="Best Score"
                  value={
                    result.recommended
                      ? `${Math.round((1 - result.recommended.score) * 100)}/100`
                      : '—'
                  }
                  color="#76E4D4"
                />
              </div>

              {/* AI Explanation */}
              {result.explanation && <AIExplanation explanation={result.explanation} />}

              {/* Route comparison table */}
              <div>
                <div className="label mb-3">All Route Alternatives</div>
                <RouteTable
                  routes={result.all_routes}
                  recommendedId={result.recommended?.route_id}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="card text-center">
      <div className="text-xl font-bold mb-0.5" style={{ color }}>{value}</div>
      <div className="text-xs text-[#93A4B8]">{label}</div>
    </div>
  );
}
