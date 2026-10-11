import { useState, useRef, useEffect } from 'react';
import { customOptimize, getShipments } from '../api';
import type { NavPage, OptimizationResult, Shipment } from '../types';

interface HomeProps {
  onResult: (result: OptimizationResult, shipment?: Shipment) => void;
  onNavigate: (page: NavPage) => void;
}

const SUGGESTIONS = [
  'Cheapest parcel from Hyderabad to Warangal',
  'Fastest courier from Chennai to Bengaluru',
  'Ship from Mumbai to Delhi within 2 days',
  'Ocean freight from Shanghai to Rotterdam',
];

export default function Home({ onResult, onNavigate }: HomeProps) {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [shipments, setShipments] = useState<Shipment[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    getShipments().then(setShipments).catch(() => {});
  }, []);

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setError(null);
    try {
      const result = await customOptimize(prompt);
      const customShipment: Shipment | undefined =
        result.parsed_origin && result.parsed_destination
          ? {
              shipment_id: result.recommended?.route_id.split('-R')[0] || 'CUSTOM-01',
              origin: result.parsed_origin,
              destination: result.parsed_destination,
            }
          : undefined;
      onResult(result, customShipment);
    } catch (err: any) {
      setError(err.message ?? 'Something went wrong. Is the API running?');
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <div className="relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-[#21D4C2]/5 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/4 w-[400px] h-[200px] bg-[#1a4a7a]/20 rounded-full blur-3xl" />
        </div>

        {/* Globe SVG hint */}
        <div className="absolute right-0 top-0 w-1/3 opacity-[0.04] pointer-events-none select-none overflow-hidden">
          <svg viewBox="0 0 400 400" fill="none">
            <circle cx="200" cy="200" r="180" stroke="#21D4C2" strokeWidth="1"/>
            <ellipse cx="200" cy="200" rx="90" ry="180" stroke="#21D4C2" strokeWidth="0.7"/>
            <ellipse cx="200" cy="200" rx="180" ry="60" stroke="#21D4C2" strokeWidth="0.7"/>
            <line x1="20" y1="200" x2="380" y2="200" stroke="#21D4C2" strokeWidth="0.7"/>
            <line x1="200" y1="20" x2="200" y2="380" stroke="#21D4C2" strokeWidth="0.7"/>
            <path d="M80 120 Q200 100 320 120" stroke="#21D4C2" strokeWidth="0.5" fill="none"/>
            <path d="M50 200 Q200 160 350 200" stroke="#21D4C2" strokeWidth="0.5" fill="none"/>
            <path d="M80 280 Q200 300 320 280" stroke="#21D4C2" strokeWidth="0.5" fill="none"/>
          </svg>
        </div>

        <div className="relative max-w-4xl mx-auto px-6 pt-20 pb-16 text-center">
          {/* Tag */}
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#21D4C2]/10 border border-[#21D4C2]/20 mb-8">
            <div className="w-1.5 h-1.5 rounded-full bg-[#21D4C2] animate-pulse" />
            <span className="text-xs font-medium text-[#21D4C2]">Powered by deterministic MCDA optimization</span>
          </div>

          <h1 className="text-4xl md:text-5xl font-bold text-[#F1F5F9] leading-tight mb-4">
            Smarter shipment routes
            <br />
            <span className="text-[#21D4C2]">for a global world.</span>
          </h1>

          <p className="text-base md:text-lg text-[#93A4B8] max-w-2xl mx-auto mb-10 leading-relaxed">
            Optimize cost, transit time, and risk simultaneously — with grounded AI explanations,
            Pareto-dominant selection, and sensitivity analysis across trade strategies.
          </p>

          {/* Prompt composer */}
          <form onSubmit={handleSubmit} className="max-w-2xl mx-auto">
            <div className="relative rounded-2xl bg-[#101F32] border border-[#22344A] focus-within:border-[#21D4C2]/60 focus-within:ring-1 focus-within:ring-[#21D4C2]/20 transition-all shadow-xl">
              <textarea
                ref={textareaRef}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyDown={handleKey}
                rows={3}
                placeholder="Describe your shipment… e.g. cheapest parcel from Hyderabad to Warangal"
                className="w-full bg-transparent px-5 pt-4 pb-2 text-sm text-[#F1F5F9] placeholder:text-[#4A5568] resize-none focus:outline-none leading-relaxed"
              />
              <div className="flex items-center justify-between px-4 pb-3">
                <span className="text-xs text-[#4A5568]">Press Enter ↵ to optimize · Shift+Enter for newline</span>
                <button
                  type="submit"
                  disabled={!prompt.trim() || loading}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-[#21D4C2] hover:bg-[#1bbfad] disabled:opacity-40 disabled:cursor-not-allowed text-[#07111F] font-semibold text-sm transition-all duration-200"
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
                        <path d="M5 12h14M12 5l7 7-7 7" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      Optimize
                    </>
                  )}
                </button>
              </div>
            </div>

            {error && (
              <div className="mt-3 px-4 py-3 rounded-lg bg-[#FB7185]/10 border border-[#FB7185]/30 text-sm text-[#FB7185]">
                {error}
              </div>
            )}
          </form>

          {/* Suggestion chips */}
          <div className="flex flex-wrap gap-2 justify-center mt-5">
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                onClick={() => setPrompt(s)}
                className="px-3.5 py-1.5 rounded-full bg-[#101F32] border border-[#22344A] hover:border-[#21D4C2]/40 text-xs text-[#93A4B8] hover:text-[#21D4C2] transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* KPI strip */}
      <div className="max-w-5xl mx-auto px-6 pb-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard label="Shipments" value={shipments.length || '30'} sub="in dataset" />
          <KpiCard label="Route Alternatives" value="4" sub="per shipment" />
          <KpiCard label="Optimization Criteria" value="3" sub="cost · time · risk" />
          <KpiCard label="AI Fallback" value="100%" sub="offline mode" />
        </div>

        {/* Recent shipment examples */}
        {shipments.length > 0 && (
          <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-[#F1F5F9]">Example Shipments</h2>
              <button
                onClick={() => onNavigate('optimize')}
                className="text-xs text-[#21D4C2] hover:underline"
              >
                Open Optimizer →
              </button>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {shipments.slice(0, 6).map((s) => (
                <button
                  key={s.shipment_id}
                  onClick={() => {
                    setPrompt(`Optimize shipment from ${s.origin} to ${s.destination}`);
                    textareaRef.current?.focus();
                  }}
                  className="text-left p-3.5 rounded-xl bg-[#101F32] border border-[#22344A] hover:border-[#21D4C2]/40 transition-all group"
                >
                  <div className="text-[10px] text-[#93A4B8] mb-1 font-medium uppercase tracking-wide">
                    {s.shipment_id}
                  </div>
                  <div className="text-sm font-medium text-[#F1F5F9] group-hover:text-[#21D4C2] transition-colors">
                    {s.origin} → {s.destination}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value, sub }: { label: string; value: string | number; sub: string }) {
  return (
    <div className="card text-center">
      <div className="text-2xl font-bold text-[#21D4C2] mb-1">{value}</div>
      <div className="text-sm font-medium text-[#F1F5F9]">{label}</div>
      <div className="text-xs text-[#93A4B8] mt-0.5">{sub}</div>
    </div>
  );
}
