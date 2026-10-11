import { useEffect, useState } from 'react';
import { getShipments, optimize } from '../api';
import type { OptimizationResult, RouteResult, Shipment } from '../types';
import { formatMoney } from '../money';

interface MapPageProps {
  result: OptimizationResult | null;
}

type Coordinate = [longitude: number, latitude: number];

const PORT_COORDS: Record<string, Coordinate> = {
  Shanghai: [121.5, 31.2], Ningbo: [121.6, 29.9], Shenzhen: [114.1, 22.5],
  Qingdao: [120.3, 36.1], 'Hong Kong': [114.2, 22.3], Kaohsiung: [120.3, 22.6],
  Taipei: [121.5, 25], Tokyo: [139.7, 35.7], Yokohama: [139.6, 35.4],
  Kobe: [135.2, 34.7], Busan: [129, 35.1], Incheon: [126.7, 37.5],
  Singapore: [103.8, 1.35], 'Port Klang': [101.4, 3], 'Tanjung Pelepas': [103.5, 1.4],
  'Ho Chi Minh': [106.7, 10.8], Bangkok: [100.5, 13.8], Jakarta: [106.8, -6.2],
  Manila: [121, 14.6], Mumbai: [72.9, 19.1], Chennai: [80.3, 13.1],
  Mundra: [69.7, 22.8], Hyderabad: [78.5, 17.4], Vishakapatnam: [83.3, 17.7],
  Visakhapatnam: [83.3, 17.7], Warangal: [79.6, 18], Vijayawada: [80.65, 16.51],
  Jaipur: [75.79, 26.91], Surat: [72.83, 21.17], Nagpur: [79.09, 21.15],
  Kochi: [76.27, 9.93], Lucknow: [80.95, 26.85], Pune: [73.86, 18.52],
  Ahmedabad: [72.57, 23.03], Delhi: [77.2, 28.6], Kolkata: [88.4, 22.6],
  Colombo: [79.9, 6.9], Chittagong: [91.8, 22.3], Karachi: [67, 24.9],
  Dubai: [55.3, 25.2], 'Jebel Ali': [55, 25], Alexandria: [29.9, 31.2],
  Durban: [31, -29.9], 'Cape Town': [18.4, -33.9], 'Cape of Good Hope': [18.5, -34.4],
  'Port Louis': [57.5, -20.2], 'Suez Canal': [32.5, 30], Suez: [32.5, 30],
  Panama: [-79.5, 9], Malacca: [101.5, 2.5], Baku: [49.9, 40.4],
  Rotterdam: [4.5, 51.9], Hamburg: [10, 53.6], Antwerp: [4.4, 51.2],
  Felixstowe: [1.3, 52], 'Le Havre': [0.1, 49.5], London: [0.1, 51.5],
  'London Gateway': [0.5, 51.5], Frankfurt: [8.7, 50.1], Amsterdam: [4.9, 52.4],
  Bremerhaven: [8.6, 53.5], Valencia: [-0.4, 39.5], Barcelona: [2.2, 41.4],
  Genoa: [8.9, 44.4], Marseille: [5.4, 43.3], Piraeus: [23.6, 37.9],
  'Los Angeles': [-118.2, 34.05], 'Long Beach': [-118.2, 33.8],
  Oakland: [-122.3, 37.8], Seattle: [-122.3, 47.6], 'New York': [-74, 40.7],
  Savannah: [-81.1, 32.1], Chicago: [-87.6, 41.9], Vancouver: [-123.1, 49.3],
  Veracruz: [-96.1, 19.2], Santos: [-46.3, -23.9], Sydney: [151.2, -33.9],
  Melbourne: [144.9, -37.8],
};

const LAND_POLYGONS: Coordinate[][] = [
  [[-168, 72], [-145, 70], [-125, 58], [-130, 50], [-123, 42], [-117, 32], [-105, 25], [-97, 18], [-82, 9], [-77, 25], [-60, 48], [-80, 60], [-105, 73], [-140, 72]],
  [[-81, 12], [-68, 10], [-50, 4], [-35, -8], [-42, -23], [-53, -35], [-69, -55], [-75, -38], [-80, -12]],
  [[-10, 36], [-8, 52], [10, 58], [25, 70], [70, 75], [110, 68], [150, 60], [170, 53], [150, 45], [135, 38], [125, 25], [110, 18], [100, 5], [80, 8], [65, 25], [45, 30], [30, 37], [15, 36]],
  [[-18, 35], [10, 37], [35, 30], [50, 12], [42, -12], [35, -30], [20, -35], [10, -25], [0, -5], [-15, 15]],
  [[112, -11], [130, -10], [152, -25], [145, -39], [130, -44], [114, -32]],
  [[-52, 82], [-25, 78], [-18, 68], [-40, 58], [-54, 65]],
];

function resolveCoord(name: string): Coordinate | null {
  const clean = name.replace(/\s*\([^)]*\)/g, '').trim();
  const match = Object.keys(PORT_COORDS).find(
    (key) => clean.toLowerCase() === key.toLowerCase(),
  );
  return match ? PORT_COORDS[match] : null;
}

function shortestLongitudeDelta(from: number, to: number): number {
  return ((to - from + 540) % 360) - 180;
}

function routePath(
  start: [number, number],
  end: [number, number],
  offset: number,
): string {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const length = Math.max(1, Math.hypot(dx, dy));
  const controlX = (start[0] + end[0]) / 2 - (dy / length) * offset;
  const controlY = (start[1] + end[1]) / 2 + (dx / length) * offset;
  return `M ${start[0]} ${start[1]} Q ${controlX} ${controlY} ${end[0]} ${end[1]}`;
}

function routeColor(index: number): string {
  return ['#21D4C2', '#60A5FA', '#FBBF24', '#C084FC'][index % 4];
}

function RouteOption({
  route,
  color,
  selected,
  recommended,
  onSelect,
}: {
  route: RouteResult;
  color: string;
  selected: boolean;
  recommended: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      key={route.route_id}
      onClick={onSelect}
      aria-pressed={selected}
      className={`rounded-xl border p-4 text-left transition-colors focus:outline-none focus:ring-2 focus:ring-[#21D4C2] ${
        selected
          ? 'border-[#21D4C2] bg-[#14263B]'
          : 'border-[#22344A] bg-[#101F32] hover:border-[#21D4C2]/50'
      }`}
    >
      <div className="mb-3 flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-2">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />
          <span className="truncate text-xs font-bold text-[#F1F5F9]">{route.route_id}</span>
        </span>
        {recommended && (
          <span className="rounded-full bg-[#21D4C2]/15 px-2 py-0.5 text-[10px] font-bold text-[#21D4C2]">
            RECOMMENDED
          </span>
        )}
      </div>
      <div className="truncate text-sm font-semibold text-[#F1F5F9]" title={route.route_name}>
        {route.route_name || route.mode}
      </div>
      <div className="mt-1 truncate text-xs text-[#93A4B8]" title={route.mode}>
        {route.mode}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2 border-t border-[#22344A] pt-3">
        <div>
          <div className="text-[10px] uppercase text-[#93A4B8]">Freight</div>
          <div className="mt-1 text-sm font-semibold text-[#F1F5F9]">{formatMoney(route.cost).primary}</div>
          <div className="text-[10px] text-[#93A4B8]">{formatMoney(route.cost).secondary}</div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[#93A4B8]">Transit</div>
          <div className="mt-1 text-sm font-semibold text-[#F1F5F9]">
            {route.transit_days < 1
              ? `${Math.round(route.transit_days * 24)}h`
              : `${route.transit_days}d`}
          </div>
        </div>
        <div>
          <div className="text-[10px] uppercase text-[#93A4B8]">Feasibility</div>
          <div className={`mt-1 text-sm font-semibold ${route.feasible ? 'text-[#34D399]' : 'text-[#FB7185]'}`}>
            {route.feasible ? 'Feasible' : 'Infeasible'}
          </div>
        </div>
      </div>
    </button>
  );
}

export default function MapPage({ result: initialResult }: MapPageProps) {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selectedId, setSelectedId] = useState('');
  const [currentResult, setCurrentResult] = useState<OptimizationResult | null>(initialResult);
  const [loading, setLoading] = useState(false);
  const [mapError, setMapError] = useState<string | null>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  useEffect(() => {
    getShipments()
      .then((items) => {
        setShipments(items);
        if (!currentResult && items.length > 0) {
          setSelectedId(items[0].shipment_id);
          void fetchShipmentRoutes(items[0].shipment_id);
        }
      })
      .catch(() => setMapError('Could not load shipments. Check that the API is running.'));
  }, []);

  useEffect(() => {
    if (initialResult) {
      setCurrentResult(initialResult);
      setSelectedRouteId(initialResult.recommended?.route_id ?? null);
    }
  }, [initialResult]);

  const fetchShipmentRoutes = async (id: string) => {
    setLoading(true);
    setMapError(null);
    try {
      const response = await optimize(id, { cost: 0.4, time: 0.3, risk: 0.3 });
      setCurrentResult(response);
      setSelectedRouteId(response.recommended?.route_id ?? null);
    } catch (error) {
      setMapError(error instanceof Error ? error.message : 'Could not load routes for this shipment.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectShipment = (id: string) => {
    setSelectedId(id);
    void fetchShipmentRoutes(id);
  };

  const activeRoutes = currentResult?.all_routes ?? [];
  const recommended = currentResult?.recommended ?? null;
  const selectedShipment = shipments.find((shipment) => shipment.shipment_id === selectedId);
  const originName = currentResult?.parsed_origin || selectedShipment?.origin || '';
  const destinationName = currentResult?.parsed_destination || selectedShipment?.destination || '';
  const originCoord = resolveCoord(originName);
  const destinationCoord = resolveCoord(destinationName);
  const mapReady = originCoord !== null && destinationCoord !== null;

  const width = 880;
  const height = 440;
  const centerLat = mapReady ? (originCoord[1] + destinationCoord[1]) / 2 : 0;
  const startLon = mapReady ? originCoord[0] : 0;
  const endLon = mapReady
    ? startLon + shortestLongitudeDelta(startLon, destinationCoord[0])
    : 0;
  const centerLon = (startLon + endLon) / 2;
  const longitudeScale = Math.cos((centerLat * Math.PI) / 180);
  const deltaX = Math.abs((endLon - startLon) * longitudeScale);
  const deltaY = mapReady ? Math.abs(destinationCoord[1] - originCoord[1]) : 0;
  const compactCorridor = deltaX < 5 && deltaY < 5;
  const minimumExtentDegrees = 8;
  const scale = Math.min(
    (width - 300) / Math.max(deltaX, minimumExtentDegrees),
    (height - 190) / Math.max(deltaY, minimumExtentDegrees),
  );

  const project = ([longitude, latitude]: Coordinate): [number, number] => {
    const adjustedLongitude = centerLon + shortestLongitudeDelta(centerLon, longitude);
    return [
      width / 2 + (adjustedLongitude - centerLon) * longitudeScale * scale,
      height / 2 - (latitude - centerLat) * scale,
    ];
  };

  const startPoint = mapReady ? project([startLon, originCoord[1]]) : null;
  const endPoint = mapReady ? project([endLon, destinationCoord[1]]) : null;
  const originLabel = originName.replace(/\s*\([^)]*\)/g, '').trim();
  const destinationLabel = destinationName.replace(/\s*\([^)]*\)/g, '').trim();
  const customRoute = Boolean(currentResult?.parsed_origin || currentResult?.parsed_destination);

  return (
    <div className="mx-auto max-w-7xl px-6 py-8">
      <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <div className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#21D4C2]">
            Route comparison
          </div>
          <h1 className="text-2xl font-bold text-[#F1F5F9]">Corridor map</h1>
          <p className="mt-1 text-sm text-[#93A4B8]">
            Compare candidate routes between the shipment endpoints.
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <label htmlFor="map-shipment" className="text-xs font-medium text-[#93A4B8]">
            Shipment
          </label>
          <select
            id="map-shipment"
            className="input-field min-w-[260px] py-2 text-sm"
            value={selectedId}
            onChange={(event) => handleSelectShipment(event.target.value)}
          >
            {customRoute && (
              <option value="">Current custom route: {originLabel} → {destinationLabel}</option>
            )}
            {shipments.map((shipment) => (
              <option key={shipment.shipment_id} value={shipment.shipment_id}>
                {shipment.shipment_id} · {shipment.origin} → {shipment.destination}
              </option>
            ))}
          </select>
        </div>
      </div>

      {mapError && (
        <div className="mb-4 rounded-lg border border-[#FB7185]/30 bg-[#FB7185]/10 px-4 py-3 text-sm text-[#FB7185]">
          {mapError}
        </div>
      )}

      {loading ? (
        <div className="card flex min-h-[420px] items-center justify-center text-sm text-[#93A4B8]">
          Loading corridor options…
        </div>
      ) : activeRoutes.length > 0 ? (
        <>
          <section className="overflow-hidden rounded-2xl border border-[#22344A] bg-[#0A1626] shadow-xl">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#22344A] px-5 py-4">
              <div>
                <div className="text-sm font-semibold text-[#F1F5F9]">
                  {originLabel || 'Origin'} <span className="mx-2 text-[#21D4C2]">→</span>{' '}
                  {destinationLabel || 'Destination'}
                </div>
                <div className="mt-1 text-xs text-[#93A4B8]">
                  {activeRoutes.length} alternatives · {currentResult?.feasible_count ?? 0} feasible
                </div>
              </div>
              {recommended && (
                <div className="rounded-full border border-[#21D4C2]/30 bg-[#21D4C2]/10 px-3 py-1.5 text-xs text-[#21D4C2]">
                  Recommended: <span className="font-semibold">{recommended.route_name || recommended.route_id}</span>
                </div>
              )}
            </div>

            {mapReady && startPoint && endPoint ? (
              <div className="bg-[#07111F] p-3 sm:p-5">
                <svg
                  role="img"
                  aria-label={`Schematic route comparison map from ${originLabel} to ${destinationLabel}`}
                  viewBox={`0 0 ${width} ${height}`}
                  className="h-auto w-full rounded-xl border border-[#1B2D43] bg-[#091725]"
                >
                  <defs>
                    <linearGradient id="map-ocean" x1="0" y1="0" x2="1" y2="1">
                      <stop offset="0%" stopColor="#0B1D2D" />
                      <stop offset="100%" stopColor="#07111F" />
                    </linearGradient>
                    <filter id="map-glow" x="-100%" y="-100%" width="300%" height="300%">
                      <feGaussianBlur stdDeviation="5" result="blur" />
                      <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
                    </filter>
                  </defs>
                  <rect width={width} height={height} fill="url(#map-ocean)" />
                  {Array.from({ length: 10 }, (_, index) => (
                    <line
                      key={`grid-x-${index}`}
                      x1={(index + 1) * (width / 11)}
                      y1="0"
                      x2={(index + 1) * (width / 11)}
                      y2={height}
                      stroke="#193047"
                      strokeWidth="1"
                    />
                  ))}
                  {Array.from({ length: 5 }, (_, index) => (
                    <line
                      key={`grid-y-${index}`}
                      x1="0"
                      y1={(index + 1) * (height / 6)}
                      x2={width}
                      y2={(index + 1) * (height / 6)}
                      stroke="#193047"
                      strokeWidth="1"
                    />
                  ))}
                  {!compactCorridor && LAND_POLYGONS.map((polygon, index) => {
                    const path = polygon
                      .map((point, pointIndex) => {
                        const [x, y] = project(point);
                        return `${pointIndex === 0 ? 'M' : 'L'} ${x} ${y}`;
                      })
                      .join(' ') + ' Z';
                    return (
                      <path
                        key={`land-${index}`}
                        d={path}
                        fill="#10283A"
                        stroke="#1D4052"
                        strokeWidth="1.2"
                        opacity="0.78"
                      />
                    );
                  })}
                  {activeRoutes.map((route, index) => {
                    const isSelected = (selectedRouteId ?? recommended?.route_id) === route.route_id;
                    const path = routePath(startPoint, endPoint, (index - (activeRoutes.length - 1) / 2) * 23);
                    const color = routeColor(index);
                    return (
                      <g
                        key={route.route_id}
                        className="cursor-pointer"
                        role="button"
                        tabIndex={0}
                        aria-label={`Highlight ${route.route_name || route.route_id}`}
                        onClick={() => setSelectedRouteId(route.route_id)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter' || event.key === ' ') {
                            event.preventDefault();
                            setSelectedRouteId(route.route_id);
                          }
                        }}
                      >
                        {isSelected && (
                          <path
                            d={path}
                            fill="none"
                            stroke={color}
                            strokeWidth="12"
                            opacity="0.18"
                            filter="url(#map-glow)"
                          />
                        )}
                        <path
                          d={path}
                          fill="none"
                          stroke={color}
                          strokeWidth={isSelected ? 4 : 2}
                          strokeDasharray={route.feasible ? undefined : '7 6'}
                          opacity={isSelected ? 1 : 0.55}
                        />
                      </g>
                    );
                  })}
                  {[{ point: startPoint, label: originLabel, anchor: 'start' as const },
                    { point: endPoint, label: destinationLabel, anchor: 'end' as const }].map(({ point, label, anchor }) => {
                      const labelOffset = compactCorridor
                        ? (anchor === 'start' ? 34 : -29)
                        : -13;
                      const labelY = point[1] + labelOffset;
                      return (
                        <g key={label}>
                          <circle cx={point[0]} cy={point[1]} r="12" fill="#21D4C2" opacity="0.16" />
                          <circle cx={point[0]} cy={point[1]} r="5.5" fill="#21D4C2" stroke="#D8FFF9" strokeWidth="2" />
                          <text
                            x={point[0] + (anchor === 'start' ? 14 : -14)}
                            y={labelY}
                            textAnchor={anchor}
                            fill="#F1F5F9"
                            fontSize="13"
                            fontWeight="700"
                            paintOrder="stroke"
                            stroke="#07111F"
                            strokeWidth="4"
                          >
                            {label}
                          </text>
                          <text
                            x={point[0] + (anchor === 'start' ? 14 : -14)}
                            y={labelY + 18}
                            textAnchor={anchor}
                            fill="#21D4C2"
                            fontSize="9"
                            letterSpacing="1.5"
                          >
                            {anchor === 'start' ? 'ORIGIN' : 'DESTINATION'}
                          </text>
                        </g>
                      );
                    })}
                  <text x="20" y="28" fill="#7792A8" fontSize="10" letterSpacing="1.4">
                    ENDPOINT-FOCUSED VIEW
                  </text>
                </svg>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#93A4B8]">
                  <span>Colors identify alternatives; select a card to highlight its schematic corridor.</span>
                  <span>Illustrative comparison only—not a live navigation or carrier route.</span>
                </div>
              </div>
            ) : (
              <div className="flex min-h-64 flex-col items-center justify-center gap-2 bg-[#07111F] px-6 text-center">
                <div className="text-sm font-semibold text-[#F1F5F9]">Map coordinates are unavailable</div>
                <p className="max-w-lg text-xs leading-5 text-[#93A4B8]">
                  The route alternatives are still listed below. Add coordinates for both locations to display their corridor; no substitute route is drawn.
                </p>
              </div>
            )}
          </section>

          <section className="mt-5">
            <div className="mb-3 flex items-end justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-[#F1F5F9]">Candidate routes</h2>
                <p className="mt-1 text-xs text-[#93A4B8]">Select an option to highlight it on the corridor map.</p>
              </div>
              <div className="text-xs text-[#93A4B8]">
                {activeRoutes.length > 0 && currentResult?.feasible_count === 0
                  ? 'All candidates violate at least one constraint.'
                  : `${currentResult?.feasible_count ?? 0} of ${activeRoutes.length} meet the active constraints.`}
              </div>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {activeRoutes.map((route, index) => (
                <RouteOption
                  key={route.route_id}
                  route={route}
                  color={routeColor(index)}
                  selected={(selectedRouteId ?? recommended?.route_id) === route.route_id}
                  recommended={route.route_id === recommended?.route_id}
                  onSelect={() => setSelectedRouteId(route.route_id)}
                />
              ))}
            </div>
          </section>
        </>
      ) : (
        <div className="card py-20 text-center">
          <h2 className="text-base font-semibold text-[#F1F5F9]">No route options to display</h2>
          <p className="mt-2 text-sm text-[#93A4B8]">
            Choose a shipment once the API is available, or optimize a custom corridor first.
          </p>
        </div>
      )}
    </div>
  );
}
