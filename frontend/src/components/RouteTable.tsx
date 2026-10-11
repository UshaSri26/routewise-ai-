import type { RouteResult } from '../types';

interface RouteTableProps {
  routes: RouteResult[];
  recommendedId?: string;
}

export default function RouteTable({ routes, recommendedId }: RouteTableProps) {
  if (!routes.length) return null;

  return (
    <div className="overflow-x-auto rounded-xl border border-[#22344A]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#22344A] bg-[#0A1626]">
            {['Route', 'Hubs / Mode', 'Cost', 'Days', 'Delay %', 'Risk', 'Score', 'Status'].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-[#93A4B8] uppercase tracking-wider whitespace-nowrap">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {routes.map((r, i) => {
            const isRec = r.route_id === recommendedId;
            return (
              <tr
                key={r.route_id}
                className={`border-b border-[#22344A]/50 transition-colors ${
                  isRec
                    ? 'bg-[#21D4C2]/5 border-l-2 border-l-[#21D4C2]'
                    : i % 2 === 0
                    ? 'bg-[#101F32]'
                    : 'bg-[#0E1C2E]'
                } hover:bg-[#14263B]`}
              >
                <td className="px-4 py-3 font-medium text-[#F1F5F9] whitespace-nowrap">
                  {isRec && <span className="text-[#21D4C2] mr-1">★</span>}
                  {r.route_id}
                </td>
                <td className="px-4 py-3 text-[#93A4B8] max-w-[160px] truncate" title={r.hubs || r.mode}>
                  {r.hubs || r.mode}
                </td>
                <td className="px-4 py-3 text-[#F1F5F9] whitespace-nowrap">
                  <div>${r.cost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                  <div className="text-[10px] text-[#21D4C2]">≈ ₹{Math.round(r.cost * 84).toLocaleString()}</div>
                </td>
                <td className="px-4 py-3 text-[#F1F5F9] whitespace-nowrap">
                  <div>{r.transit_days < 1.0 ? `${Math.round(r.transit_days * 24 * 10) / 10} hrs` : `${r.transit_days}d`}</div>
                  <div className="text-[10px] text-[#93A4B8]">{r.transit_days < 1.0 ? `(${r.transit_days}d)` : `(${Math.round(r.transit_days * 24)}h)`}</div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`font-medium ${
                    r.delay_probability > 0.4 ? 'text-[#FB7185]' :
                    r.delay_probability > 0.2 ? 'text-[#FBBF24]' : 'text-[#34D399]'
                  }`}>
                    {(r.delay_probability * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="px-4 py-3 text-[#93A4B8]">{r.composite_risk.toFixed(3)}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div className="w-16 h-1.5 bg-[#22344A] rounded-full overflow-hidden">
                      <div
                        className="h-full bg-[#21D4C2] rounded-full"
                        style={{ width: `${Math.round((1 - r.score) * 100)}%` }}
                      />
                    </div>
                    <span className="text-[#F1F5F9] text-xs font-medium">
                      {Math.round((1 - r.score) * 100)}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {r.feasible ? (
                    <span className="badge-feasible">Feasible</span>
                  ) : (
                    <span className="badge-infeasible">Infeasible</span>
                  )}
                  {r.pareto_dominant && (
                    <span className="badge-pareto ml-1">Pareto</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
