import type { RouteResult } from '../types';

interface RouteCardProps {
  route: RouteResult;
  isRecommended?: boolean;
}

export default function RouteCard({ route, isRecommended }: RouteCardProps) {
  const scorePercent = Math.round((1 - route.score) * 100); // lower score = better

  return (
    <div
      className={`relative rounded-xl border p-5 transition-all ${
        isRecommended
          ? 'bg-[#0D2236] border-[#21D4C2]/40 shadow-[0_0_24px_#21D4C210]'
          : 'bg-[#101F32] border-[#22344A] hover:border-[#21D4C2]/30'
      }`}
    >
      {isRecommended && (
        <div className="absolute -top-3 left-4">
          <span className="px-3 py-1 bg-[#21D4C2] text-[#07111F] text-xs font-bold rounded-full uppercase tracking-wide">
            ★ Recommended
          </span>
        </div>
      )}

      <div className="flex items-start justify-between mb-4 mt-1">
        <div>
          <div className="text-xs font-medium text-[#93A4B8] mb-1">Route {route.route_id}</div>
          <div className="font-semibold text-[#F1F5F9] text-sm">{route.hubs || route.mode}</div>
        </div>
        <div className="flex gap-2 flex-wrap justify-end">
          {route.feasible ? (
            <span className="badge-feasible">✓ Feasible</span>
          ) : (
            <span className="badge-infeasible">✗ Infeasible</span>
          )}
          {route.pareto_dominant && (
            <span className="badge-pareto">◆ Pareto</span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
        <Metric label="Cost" value={`$${route.cost.toLocaleString()}`} />
        <Metric label="Transit" value={`${route.transit_days}d`} />
        <Metric label="Delay Risk" value={`${(route.delay_probability * 100).toFixed(0)}%`} color={
          route.delay_probability > 0.4 ? '#FB7185' : route.delay_probability > 0.2 ? '#FBBF24' : '#34D399'
        } />
        <Metric label="Composite Risk" value={route.composite_risk.toFixed(2)} />
      </div>

      {/* Score bar */}
      <div>
        <div className="flex justify-between items-center mb-1.5">
          <span className="text-xs text-[#93A4B8]">Composite Score</span>
          <span className="text-xs font-semibold text-[#21D4C2]">{scorePercent}/100</span>
        </div>
        <div className="h-1.5 bg-[#22344A] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#21D4C2] to-[#76E4D4] transition-all duration-500"
            style={{ width: `${scorePercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div>
      <div className="label mb-1">{label}</div>
      <div className="text-sm font-semibold" style={{ color: color ?? '#F1F5F9' }}>
        {value}
      </div>
    </div>
  );
}
