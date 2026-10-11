import { useState, useEffect } from 'react';
import { getShipments, optimize } from '../api';
import type { OptimizationResult, Shipment } from '../types';

interface MapPageProps {
  result: OptimizationResult | null;
}

// Global coordinates covering all trade lane ports and intermediate chokepoints
const PORT_COORDS: Record<string, [number, number]> = {
  // Asia Ports
  'Shanghai': [121.5, 31.2],
  'Ningbo': [121.6, 29.9],
  'Shenzhen': [114.1, 22.5],
  'Qingdao': [120.3, 36.1],
  'Hong Kong': [114.2, 22.3],
  'Kaohsiung': [120.3, 22.6],
  'Taipei': [121.5, 25.0],
  'Tokyo': [139.7, 35.7],
  'Yokohama': [139.6, 35.4],
  'Kobe': [135.2, 34.7],
  'Busan': [129.0, 35.1],
  'Incheon': [126.7, 37.5],
  'Singapore': [103.8, 1.35],
  'Port Klang': [101.4, 3.0],
  'Tanjung Pelepas': [103.5, 1.4],
  'Ho Chi Minh': [106.7, 10.8],
  'Bangkok': [100.5, 13.8],
  'Jakarta': [106.8, -6.2],
  'Manila': [121.0, 14.6],

  // South Asia Ports & Cities
  'Mumbai': [72.9, 19.1],
  'Chennai': [80.3, 13.1],
  'Mundra': [69.7, 22.8],
  'Hyderabad': [78.5, 17.4],
  'Vishakapatnam': [83.3, 17.7],
  'Visakhapatnam': [83.3, 17.7],
  'Warangal': [79.6, 18.0],
  'Delhi': [77.2, 28.6],
  'Kolkata': [88.4, 22.6],
  'Colombo': [79.9, 6.9],
  'Chittagong': [91.8, 22.3],
  'Karachi': [67.0, 24.9],

  // Middle East & Africa
  'Dubai': [55.3, 25.2],
  'Jebel Ali': [55.0, 25.0],
  'Alexandria': [29.9, 31.2],
  'Durban': [31.0, -29.9],
  'Cape Town': [18.4, -33.9],
  'Cape of Good Hope': [18.5, -34.4],
  'Port Louis': [57.5, -20.2],

  // Chokepoints
  'Suez Canal': [32.5, 30.0],
  'Suez': [32.5, 30.0],
  'Panama': [-79.5, 9.0],
  'Malacca': [101.5, 2.5],
  'Baku': [49.9, 40.4],

  // Europe Ports
  'Rotterdam': [4.5, 51.9],
  'Hamburg': [10.0, 53.6],
  'Antwerp': [4.4, 51.2],
  'Felixstowe': [1.3, 52.0],
  'Le Havre': [0.1, 49.5],
  'London': [0.1, 51.5],
  'London Gateway': [0.5, 51.5],
  'Frankfurt': [8.7, 50.1],
  'Amsterdam': [4.9, 52.4],
  'Bremerhaven': [8.6, 53.5],
  'Valencia': [-0.4, 39.5],
  'Barcelona': [2.2, 41.4],
  'Genoa': [8.9, 44.4],
  'Marseille': [5.4, 43.3],
  'Piraeus': [23.6, 37.9],

  // North & South America
  'Los Angeles': [-118.2, 34.05],
  'Long Beach': [-118.2, 33.8],
  'Oakland': [-122.3, 37.8],
  'Seattle': [-122.3, 47.6],
  'New York': [-74.0, 40.7],
  'Savannah': [-81.1, 32.1],
  'Chicago': [-87.6, 41.9],
  'Vancouver': [-123.1, 49.3],
  'Veracruz': [-96.1, 19.2],
  'Santos': [-46.3, -23.9],

  // Oceania
  'Sydney': [151.2, -33.9],
  'Melbourne': [144.9, -37.8],
};

// Simplified SVG world landmass contours (Geo projection)
const WORLD_LANDMASSES = [
  // North America
  "M 150 70 L 190 70 L 230 90 L 260 110 L 250 160 L 220 180 L 190 190 L 170 170 L 140 120 Z",
  // South America
  "M 215 195 L 245 205 L 260 250 L 240 310 L 220 330 L 210 270 L 205 220 Z",
  // Eurasia
  "M 370 70 L 460 65 L 560 70 L 640 90 L 670 120 L 650 170 L 590 180 L 530 190 L 490 170 L 440 160 L 390 140 L 370 100 Z",
  // Africa
  "M 385 155 L 435 155 L 460 200 L 445 280 L 415 315 L 385 280 L 370 200 Z",
  // India subcontinent
  "M 510 180 L 535 195 L 525 240 L 505 210 Z",
  // Australia
  "M 650 250 L 710 250 L 730 290 L 690 320 L 640 290 Z",
  // UK & Scandinavia
  "M 370 80 L 400 65 L 410 100 L 380 110 Z",
  // Japan
  "M 670 130 L 685 140 L 680 160 L 665 150 Z"
];

function resolveCoord(name: string): [number, number] | null {
  const clean = name.replace(/\s*\([A-Z0-9]+\)/g, '').trim();
  if (PORT_COORDS[clean]) return PORT_COORDS[clean];
  for (const [key, val] of Object.entries(PORT_COORDS)) {
    if (clean.toLowerCase().includes(key.toLowerCase()) || key.toLowerCase().includes(clean.toLowerCase())) {
      return val;
    }
  }
  return null;
}

export default function MapPage({ result: initialResult }: MapPageProps) {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [currentResult, setCurrentResult] = useState<OptimizationResult | null>(initialResult);
  const [loading, setLoading] = useState(false);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  useEffect(() => {
    getShipments().then((s) => {
      setShipments(s);
      if (!currentResult && s.length > 0) {
        setSelectedId(s[0].shipment_id);
        fetchShipmentRoutes(s[0].shipment_id);
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (initialResult) {
      setCurrentResult(initialResult);
      if (initialResult.recommended) {
        setSelectedRouteId(initialResult.recommended.route_id);
      }
    }
  }, [initialResult]);

  const fetchShipmentRoutes = async (id: string) => {
    setLoading(true);
    try {
      const res = await optimize(id, { cost: 0.40, time: 0.30, risk: 0.30 });
      setCurrentResult(res);
      if (res.recommended) setSelectedRouteId(res.recommended.route_id);
    } catch {
      // fallback
    } finally {
      setLoading(false);
    }
  };

  const handleSelectShipment = (id: string) => {
    setSelectedId(id);
    fetchShipmentRoutes(id);
  };

  const W = 880;
  const H = 460;

  const project = ([lon, lat]: [number, number]): [number, number] => {
    const x = ((lon + 180) / 360) * W;
    const y = ((90 - lat) / 180) * H;
    return [Math.max(10, Math.min(W - 10, x)), Math.max(10, Math.min(H - 10, y))];
  };

  const routeColors = ['#21D4C2', '#38BDF8', '#FBBF24', '#A855F7'];

  // Parse origin and destination
  const activeRoutes = currentResult?.all_routes || [];
  const recRoute = currentResult?.recommended;

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      {/* Header with Shipment Selector */}
      <div className="mb-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F1F5F9]">Global Corridor Route Map</h1>
          <p className="text-sm text-[#93A4B8] mt-1">
            Visual geospatial trajectories of evaluated route alternatives and intermediate maritime/intermodal hubs.
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <label className="text-xs text-[#93A4B8] whitespace-nowrap font-medium">Select Shipment:</label>
          <select
            className="input-field py-1.5 px-3 text-xs w-auto min-w-[200px]"
            value={selectedId}
            onChange={(e) => handleSelectShipment(e.target.value)}
          >
            {shipments.map((s) => (
              <option key={s.shipment_id} value={s.shipment_id}>
                {s.shipment_id}: {s.origin} → {s.destination}
              </option>
            ))}
          </select>

          {/* Direct Google Maps Live Route Launcher */}
          {(() => {
            const currentShipment = shipments.find((s) => s.shipment_id === selectedId);
            const orig = currentShipment?.origin || currentResult?.parsed_origin || 'Hyderabad';
            const dest = currentShipment?.destination || currentResult?.parsed_destination || 'Warangal';
            const gmapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(orig)}&destination=${encodeURIComponent(dest)}`;
            return (
              <a
                href={gmapsUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-[#21D4C2]/15 hover:bg-[#21D4C2]/25 text-[#21D4C2] border border-[#21D4C2]/40 text-xs font-semibold transition-all shadow-sm"
                title="Open live ground navigation & turn-by-turn traffic directly in Google Maps"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polygon points="3 11 22 2 13 21 11 13 3 11"/>
                </svg>
                <span>Live Google Maps</span>
                <span className="text-[10px] opacity-75">↗</span>
              </a>
            );
          })()}
        </div>
      </div>

      {loading ? (
        <div className="card flex items-center justify-center py-28">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin w-8 h-8 text-[#21D4C2]" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
            </svg>
            <span className="text-sm text-[#93A4B8]">Rendering geospatial trade corridors…</span>
          </div>
        </div>
      ) : activeRoutes.length > 0 ? (
        <div className="space-y-6">
          {/* Main Map Canvas */}
          <div className="card p-0 overflow-hidden border border-[#22344A] bg-[#07111F] shadow-2xl relative">
            <div className="px-5 py-3.5 border-b border-[#22344A] bg-[#0A1626]/80 backdrop-blur flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#21D4C2] animate-pulse" />
                <span className="text-xs font-semibold text-[#F1F5F9] uppercase tracking-wide">
                  Geodesic Route Plotter
                </span>
                {recRoute && (
                  <span className="text-xs text-[#21D4C2] bg-[#21D4C2]/10 border border-[#21D4C2]/30 px-2 py-0.5 rounded-full ml-2">
                    Winner: {recRoute.route_name || recRoute.route_id}
                  </span>
                )}
              </div>
              <div className="text-xs text-[#93A4B8]">
                Click any route card below to focus trajectory
              </div>
            </div>

            <div className="p-4 sm:p-6 overflow-x-auto">
              <svg viewBox={`0 0 ${W} ${H}`} className="w-full min-w-[700px] h-auto rounded-xl bg-[#091524]">
                <defs>
                  <radialGradient id="oceanGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#0B1C30" />
                    <stop offset="100%" stopColor="#06101D" />
                  </radialGradient>
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>

                {/* Ocean Background */}
                <rect width={W} height={H} fill="url(#oceanGlow)" />

                {/* Latitude / Longitude Coordinate Grids */}
                {[-60, -30, 0, 30, 60].map((lat) => {
                  const [, y] = project([0, lat]);
                  return (
                    <g key={lat}>
                      <line x1="0" y1={y} x2={W} y2={y} stroke="#1A2B40" strokeWidth="0.6" strokeDasharray="3 3" />
                      <text x="8" y={y - 3} fill="#243850" fontSize="8" fontFamily="monospace">
                        {lat > 0 ? `${lat}°N` : lat < 0 ? `${Math.abs(lat)}°S` : 'Equator'}
                      </text>
                    </g>
                  );
                })}
                {[-120, -60, 0, 60, 120].map((lon) => {
                  const [x] = project([lon, 0]);
                  return (
                    <g key={lon}>
                      <line x1={x} y1="0" x2={x} y2={H} stroke="#1A2B40" strokeWidth="0.6" strokeDasharray="3 3" />
                      <text x={x + 3} y={H - 6} fill="#243850" fontSize="8" fontFamily="monospace">
                        {lon > 0 ? `${lon}°E` : lon < 0 ? `${Math.abs(lon)}°W` : '0°'}
                      </text>
                    </g>
                  );
                })}

                {/* Continents Outline */}
                {WORLD_LANDMASSES.map((d, idx) => (
                  <path
                    key={idx}
                    d={d}
                    fill="#102238"
                    stroke="#1D3654"
                    strokeWidth="0.8"
                    opacity="0.9"
                  />
                ))}

                {/* Plot Route Curves */}
                {activeRoutes.map((route, ri) => {
                  const isSelected = selectedRouteId === route.route_id || (!selectedRouteId && route.route_id === recRoute?.route_id);
                  const color = routeColors[ri % routeColors.length];

                  // Resolve coordinates from intermediate hubs string or corridor
                  const hubParts = (route.hubs || route.mode || '').split(/->|–|—|,/).map((s) => s.trim()).filter(Boolean);
                  
                  // Extract waypoints
                  const waypoints: { name: string; coord: [number, number] }[] = [];
                  hubParts.forEach((part) => {
                    const c = resolveCoord(part);
                    if (c) waypoints.push({ name: part, coord: c });
                  });

                  // If fewer than 2 valid waypoints, fallback to representative route
                  if (waypoints.length < 2) {
                    const defaultCoords: [number, number][] = [
                      [121.5, 31.2], // Shanghai / Asia
                      [103.8, 1.35], // Singapore
                      [32.5, 30.0],  // Suez
                      [4.5, 51.9]    // Rotterdam / Europe
                    ];
                    waypoints.push(
                      { name: 'Origin', coord: defaultCoords[0] },
                      { name: 'Transit Hub', coord: defaultCoords[1 + (ri % 2)] },
                      { name: 'Destination', coord: defaultCoords[3] }
                    );
                  }

                  // Build smooth path
                  const projectedPts = waypoints.map((w) => project(w.coord));
                  const pathData = projectedPts.reduce((acc, pt, i) => {
                    if (i === 0) return `M ${pt[0]} ${pt[1]}`;
                    const prev = projectedPts[i - 1];
                    // Curved quadratic bezier arc
                    const cx = (prev[0] + pt[0]) / 2;
                    const cy = Math.min(prev[1], pt[1]) - (30 * ((ri % 2 === 0) ? 1 : -1));
                    return `${acc} Q ${cx} ${cy} ${pt[0]} ${pt[1]}`;
                  }, '');

                  return (
                    <g
                      key={route.route_id}
                      onClick={() => setSelectedRouteId(route.route_id)}
                      className="cursor-pointer"
                    >
                      {/* Glow effect on selected route */}
                      {isSelected && (
                        <path
                          d={pathData}
                          fill="none"
                          stroke={color}
                          strokeWidth="6"
                          opacity="0.3"
                          filter="url(#glow)"
                        />
                      )}

                      {/* Main route stroke */}
                      <path
                        d={pathData}
                        fill="none"
                        stroke={color}
                        strokeWidth={isSelected ? 3.0 : 1.5}
                        strokeDasharray={route.feasible ? (isSelected ? 'none' : '4 2') : '6 4'}
                        opacity={isSelected ? 1.0 : 0.45}
                        className="transition-all duration-300"
                      />

                      {/* Waypoint Nodes */}
                      {projectedPts.map((pt, pi) => (
                        <g key={pi}>
                          <circle
                            cx={pt[0]}
                            cy={pt[1]}
                            r={isSelected ? 5 : 3.5}
                            fill={color}
                            stroke="#07111F"
                            strokeWidth="1.5"
                            opacity={isSelected ? 1.0 : 0.6}
                          />
                          {isSelected && (
                            <text
                              x={pt[0]}
                              y={pt[1] - 8}
                              fill="#F1F5F9"
                              fontSize="9"
                              fontWeight="600"
                              textAnchor="middle"
                              className="pointer-events-none drop-shadow"
                            >
                              {waypoints[pi]?.name?.split(' ')[0]}
                            </text>
                          )}
                        </g>
                      ))}
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Interactive Route Cards */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold text-[#93A4B8] uppercase tracking-wider">
                Corridor Trajectories ({activeRoutes.length} Options)
              </span>
              <span className="text-xs text-[#21D4C2]">
                Highlighting: {selectedRouteId || recRoute?.route_id || 'All'}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {activeRoutes.map((r, i) => {
                const color = routeColors[i % routeColors.length];
                const isSelected = selectedRouteId === r.route_id;
                const isRec = r.route_id === recRoute?.route_id;

                return (
                  <div
                    key={r.route_id}
                    onClick={() => setSelectedRouteId(r.route_id)}
                    className={`card cursor-pointer transition-all duration-200 border ${
                      isSelected
                        ? 'border-[#21D4C2] bg-[#14263B] shadow-[0_0_15px_#21D4C220]'
                        : 'border-[#22344A] hover:border-[#21D4C2]/40 bg-[#101F32]'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-3 h-3 rounded-full flex-shrink-0"
                          style={{ backgroundColor: color }}
                        />
                        <span className="text-xs font-bold text-[#F1F5F9]">{r.route_id}</span>
                      </div>
                      {isRec && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#21D4C2] text-[#07111F]">
                          ★ BEST
                        </span>
                      )}
                    </div>

                    <div className="text-xs font-semibold text-[#F1F5F9] mb-1 line-clamp-1" title={r.route_name}>
                      {r.route_name || r.mode}
                    </div>
                    <div className="text-[11px] text-[#93A4B8] mb-3 line-clamp-1" title={r.hubs}>
                      {r.hubs || r.mode}
                    </div>

                    <div className="grid grid-cols-3 gap-1 pt-2 border-t border-[#22344A] text-center">
                      <div>
                        <div className="text-[9px] text-[#93A4B8] uppercase">Cost</div>
                        <div className="text-xs font-semibold text-[#F1F5F9]">${r.cost?.toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}</div>
                        <div className="text-[9px] text-[#21D4C2]">≈₹{Math.round(r.cost * 84).toLocaleString()}</div>
                      </div>
                      <div>
                        <div className="text-[9px] text-[#93A4B8] uppercase">Transit</div>
                        <div className="text-xs font-semibold text-[#F1F5F9]">{r.transit_days < 1.0 ? `${Math.round(r.transit_days * 24 * 10) / 10}h` : `${r.transit_days}d`}</div>
                        <div className="text-[9px] text-[#93A4B8]">{r.transit_days < 1.0 ? `(${r.transit_days}d)` : `(${Math.round(r.transit_days*24)}h)`}</div>
                      </div>
                      <div>
                        <div className="text-[9px] text-[#93A4B8] uppercase">Status</div>
                        <div className={`text-xs font-semibold ${r.feasible ? 'text-[#34D399]' : 'text-[#FB7185]'}`}>
                          {r.feasible ? '✓ OK' : '✗ Viol'}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      ) : (
        <div className="card text-center py-24 space-y-3">
          <div className="w-12 h-12 rounded-xl bg-[#21D4C2]/10 border border-[#21D4C2]/20 flex items-center justify-center mx-auto text-[#21D4C2]">
            <svg width="24" height="24" fill="none" viewBox="0 0 24 24">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 110-5 2.5 2.5 0 010 5z" stroke="currentColor" strokeWidth="2"/>
            </svg>
          </div>
          <h3 className="text-base font-semibold text-[#F1F5F9]">No Route Data Available</h3>
          <p className="text-xs text-[#93A4B8] max-w-md mx-auto">
            Select a benchmark shipment from the dropdown above or run an optimization to view route trajectories on the map.
          </p>
        </div>
      )}
    </div>
  );
}
