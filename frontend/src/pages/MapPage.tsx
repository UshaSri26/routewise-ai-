import type { OptimizationResult } from '../types';

interface MapPageProps {
  result: OptimizationResult | null;
}

// City coordinates for known hubs
const CITY_COORDS: Record<string, [number, number]> = {
  'Shanghai': [121.5, 31.2],
  'Rotterdam': [4.5, 51.9],
  'Singapore': [103.8, 1.35],
  'Hamburg': [10.0, 53.6],
  'Los Angeles': [-118.2, 34.05],
  'New York': [-74.0, 40.7],
  'Dubai': [55.3, 25.2],
  'Mumbai': [72.9, 19.1],
  'Hong Kong': [114.2, 22.3],
  'Tokyo': [139.7, 35.7],
  'Sydney': [151.2, -33.9],
  'Cape Town': [18.4, -33.9],
  'Colombo': [79.9, 6.9],
  'Suez': [32.5, 30.0],
  'Panama': [-79.5, 9.0],
};

function SVGMap({ routes }: { routes: { hubs: string; feasible: boolean; route_id: string }[] }) {
  const W = 800, H = 400;

  const project = ([lon, lat]: [number, number]): [number, number] => {
    const x = ((lon + 180) / 360) * W;
    const y = ((90 - lat) / 180) * H;
    return [x, y];
  };

  const parseHubs = (hubStr: string): string[] =>
    hubStr.split(/[\-–→,]/).map((h) => h.trim()).filter(Boolean);

  const routeColors = ['#21D4C2', '#76E4D4', '#FBBF24', '#FB7185'];

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full rounded-xl" style={{ background: '#0A1626' }}>
      {/* Grid lines */}
      {[-60, -30, 0, 30, 60].map((lat) => {
        const [, y] = project([0, lat]);
        return <line key={lat} x1="0" y1={y} x2={W} y2={y} stroke="#22344A" strokeWidth="0.5" />;
      })}
      {[-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150].map((lon) => {
        const [x] = project([lon, 0]);
        return <line key={lon} x1={x} y1="0" x2={x} y2={H} stroke="#22344A" strokeWidth="0.5" />;
      })}

      {/* Routes */}
      {routes.map((route, ri) => {
        const hubs = parseHubs(route.hubs);
        const coords = hubs
          .map((h) => CITY_COORDS[h])
          .filter(Boolean) as [number, number][];
        if (coords.length < 2) return null;

        const color = route.feasible ? routeColors[ri % routeColors.length] : '#4A5568';

        return (
          <g key={route.route_id}>
            {coords.slice(0, -1).map((c, i) => {
              const [x1, y1] = project(c);
              const [x2, y2] = project(coords[i + 1]);
              return (
                <line
                  key={i}
                  x1={x1} y1={y1} x2={x2} y2={y2}
                  stroke={color}
                  strokeWidth="1.5"
                  strokeDasharray={route.feasible ? undefined : '4 4'}
                  opacity="0.8"
                />
              );
            })}
            {coords.map((c, i) => {
              const [cx, cy] = project(c);
              return (
                <g key={i}>
                  <circle cx={cx} cy={cy} r="4" fill={color} opacity="0.9"/>
                  <circle cx={cx} cy={cy} r="7" fill={color} opacity="0.15"/>
                  <text x={cx + 8} y={cy + 4} fill="#93A4B8" fontSize="9" fontFamily="sans-serif">
                    {hubs[i]}
                  </text>
                </g>
              );
            })}
          </g>
        );
      })}

      {/* Equator label */}
      <text x="4" y={project([0, 0])[1] - 3} fill="#22344A" fontSize="9" fontFamily="sans-serif">
        Equator
      </text>
    </svg>
  );
}

export default function MapPage({ result }: MapPageProps) {
  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-[#F1F5F9]">Route Map</h1>
        <p className="text-sm text-[#93A4B8] mt-1">
          Visual overview of route alternatives on a world map.
        </p>
      </div>

      {!result ? (
        <div className="card flex flex-col items-center justify-center py-20 text-center">
          <div className="text-sm font-medium text-[#F1F5F9] mb-2">No optimization results yet</div>
          <div className="text-xs text-[#93A4B8]">Run an optimization from the Home or Optimize page first.</div>
        </div>
      ) : (
        <div className="space-y-5">
          <div className="card p-0 overflow-hidden">
            <div className="px-5 py-4 border-b border-[#22344A]">
              <h2 className="text-sm font-semibold text-[#F1F5F9]">Route Alternatives</h2>
              <p className="text-xs text-[#93A4B8] mt-0.5">Solid lines = feasible · Dashed = infeasible</p>
            </div>
            <div className="p-4">
              <SVGMap routes={result.all_routes} />
            </div>
          </div>

          {/* Legend */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {result.all_routes.map((r, i) => {
              const colors = ['#21D4C2', '#76E4D4', '#FBBF24', '#FB7185'];
              return (
                <div key={r.route_id} className="card flex items-center gap-3 p-3">
                  <div className="w-3 h-3 rounded-full flex-shrink-0" style={{ backgroundColor: r.feasible ? colors[i % 4] : '#4A5568' }} />
                  <div>
                    <div className="text-xs font-medium text-[#F1F5F9]">Route {r.route_id}</div>
                    <div className="text-[10px] text-[#93A4B8] truncate max-w-[120px]">{r.hubs || r.mode}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
