import { useState, useEffect } from 'react';
import { getShipments, getScenarios } from '../api';
import type { Shipment, ScenarioResult } from '../types';

interface ScenariosProps {
  selectedShipment: Shipment | null;
}

const PROFILES = [
  {
    key: 'Balanced',
    label: 'Balanced',
    desc: 'Equal weight across cost, time, and risk.',
    color: '#21D4C2',
    icon: '⚖',
  },
  {
    key: 'Cost-Focused',
    label: 'Cost-Focused',
    desc: 'Minimize shipping cost above all else.',
    color: '#76E4D4',
    icon: '$',
  },
  {
    key: 'Time-Critical',
    label: 'Time-Critical',
    desc: 'Fastest transit time regardless of cost.',
    color: '#FBBF24',
    icon: '⏱',
  },
  {
    key: 'Risk-Averse',
    label: 'Risk-Averse',
    desc: 'Lowest delay probability and geopolitical risk.',
    color: '#34D399',
    icon: '🛡',
  },
];

export default function Scenarios({ selectedShipment }: ScenariosProps) {
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const [selectedId, setSelectedId] = useState<string>('');
  const [scenarios, setScenarios] = useState<ScenarioResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getShipments().then((s) => {
      setShipments(s);
      const id = selectedShipment?.shipment_id ?? s[0]?.shipment_id;
      if (id) {
        setSelectedId(id);
        loadScenarios(id);
      }
    }).catch(() => {});
  }, []);

  const loadScenarios = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await getScenarios(id);
      setScenarios(data);
    } catch (err: any) {
      setError(err.message ?? 'Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  };

  const handleShipmentChange = (id: string) => {
    setSelectedId(id);
    loadScenarios(id);
  };

  const getScenario = (key: string) =>
    scenarios.find((s) => s.profile?.toLowerCase().includes(key.toLowerCase()));

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <div className="mb-6 flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#F1F5F9]">Scenario Analysis</h1>
          <p className="text-sm text-[#93A4B8] mt-1">
            Compare sensitivity across 4 priority profiles for the same shipment.
          </p>
        </div>
        <select
          className="input-field w-auto"
          value={selectedId}
          onChange={(e) => handleShipmentChange(e.target.value)}
        >
          {shipments.map((s) => (
            <option key={s.shipment_id} value={s.shipment_id}>
              {s.shipment_id} — {s.origin} → {s.destination}
            </option>
          ))}
        </select>
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-sm text-[#FB7185]">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <svg className="animate-spin w-8 h-8 text-[#21D4C2]" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4l3-3-3-3v4a8 8 0 00-8 8h4z"/>
          </svg>
        </div>
      ) : (
        <>
          {/* 2x2 scenario grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-8">
            {PROFILES.map((profile) => {
              const s = getScenario(profile.key);
              return (
                <div
                  key={profile.key}
                  className="card-elevated space-y-4"
                  style={{ borderColor: s ? `${profile.color}30` : '#22344A' }}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className="w-9 h-9 rounded-lg flex items-center justify-center text-lg font-bold"
                      style={{ backgroundColor: `${profile.color}15`, border: `1px solid ${profile.color}30` }}
                    >
                      <span style={{ color: profile.color }}>{profile.icon}</span>
                    </div>
                    <div>
                      <div className="font-semibold text-[#F1F5F9] text-sm">{profile.label}</div>
                      <div className="text-xs text-[#93A4B8]">{profile.desc}</div>
                    </div>
                  </div>

                  {s ? (
                    <>
                      <div className="grid grid-cols-3 gap-3">
                        <div>
                          <div className="label mb-1">Cost</div>
                          <div className="text-sm font-semibold text-[#F1F5F9]">
                            ${s.cost?.toLocaleString() ?? '—'}
                          </div>
                        </div>
                        <div>
                          <div className="label mb-1">Days</div>
                          <div className="text-sm font-semibold text-[#F1F5F9]">
                            {s.transit_days ?? '—'}d
                          </div>
                        </div>
                        <div>
                          <div className="label mb-1">Score</div>
                          <div className="text-sm font-semibold" style={{ color: profile.color }}>
                            {s.score !== undefined ? Math.round((1 - s.score) * 100) : '—'}/100
                          </div>
                        </div>
                      </div>

                      <div>
                        <div className="label mb-1.5">Recommended Route</div>
                        <div className="text-xs font-medium text-[#F1F5F9] bg-[#0A1626] rounded-lg px-3 py-2 border border-[#22344A]">
                          {s.recommended_route || '—'}
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        {s.feasible ? (
                          <span className="badge-feasible">✓ Feasible</span>
                        ) : (
                          <span className="badge-infeasible">✗ Infeasible</span>
                        )}
                        <span className="text-xs text-[#93A4B8]">{profile.key} Profile</span>
                      </div>
                    </>
                  ) : (
                    <div className="text-xs text-[#93A4B8] italic">No data — run an optimization first</div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Comparison table */}
          {scenarios.length > 0 && (
            <div>
              <div className="label mb-3">Full Comparison</div>
              <div className="overflow-x-auto rounded-xl border border-[#22344A]">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-[#22344A] bg-[#0A1626]">
                      {['Profile', 'Recommended Route', 'Cost (USD)', 'Transit Days', 'Score', 'Feasible'].map((h) => (
                        <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-[#93A4B8] uppercase tracking-wider">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {scenarios.map((s, i) => {
                      const profile = PROFILES[i % PROFILES.length];
                      return (
                        <tr key={i} className="border-b border-[#22344A]/50 bg-[#101F32] hover:bg-[#14263B] transition-colors">
                          <td className="px-4 py-3 font-medium" style={{ color: profile.color }}>
                            {s.profile}
                          </td>
                          <td className="px-4 py-3 text-[#93A4B8] max-w-[160px] truncate" title={s.recommended_route}>
                            {s.recommended_route}
                          </td>
                          <td className="px-4 py-3 text-[#F1F5F9]">${s.cost?.toLocaleString()}</td>
                          <td className="px-4 py-3 text-[#F1F5F9]">{s.transit_days}d</td>
                          <td className="px-4 py-3 font-semibold" style={{ color: profile.color }}>
                            {s.score !== undefined ? Math.round((1 - s.score) * 100) : '—'}/100
                          </td>
                          <td className="px-4 py-3">
                            {s.feasible ? (
                              <span className="badge-feasible">✓</span>
                            ) : (
                              <span className="badge-infeasible">✗</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
