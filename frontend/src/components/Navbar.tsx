import { useState, useEffect } from 'react';
import { checkHealth } from '../api';
import type { NavPage } from '../types';

interface NavbarProps {
  currentPage: NavPage;
  onNavigate: (page: NavPage) => void;
}

const NAV_ITEMS: { id: NavPage; label: string }[] = [
  { id: 'home', label: 'Home' },
  { id: 'optimize', label: 'Optimize' },
  { id: 'map', label: 'Map' },
  { id: 'scenarios', label: 'Scenarios' },
  { id: 'assistant', label: 'AI Assistant' },
  { id: 'methodology', label: 'Methodology' },
];

export default function Navbar({ currentPage, onNavigate }: NavbarProps) {
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    checkHealth().then(setApiOnline);
    const interval = setInterval(() => checkHealth().then(setApiOnline), 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#0A1626]/95 backdrop-blur border-b border-[#22344A]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <button
            onClick={() => onNavigate('home')}
            className="flex items-center gap-2.5 flex-shrink-0"
          >
            <div className="w-8 h-8 rounded-lg bg-[#21D4C2]/10 border border-[#21D4C2]/30 flex items-center justify-center">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M2 9 Q5 4 9 9 Q13 14 16 9" stroke="#21D4C2" strokeWidth="2" strokeLinecap="round" fill="none"/>
                <circle cx="2" cy="9" r="1.5" fill="#21D4C2"/>
                <circle cx="16" cy="9" r="1.5" fill="#21D4C2"/>
              </svg>
            </div>
            <div className="leading-tight">
              <div className="text-sm font-bold text-[#F1F5F9]">RouteWise AI</div>
              <div className="text-[10px] text-[#93A4B8] font-medium">Shipment Intelligence</div>
            </div>
          </button>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                  currentPage === item.id
                    ? 'bg-[#21D4C2]/15 text-[#21D4C2] border border-[#21D4C2]/30'
                    : 'text-[#93A4B8] hover:text-[#F1F5F9] hover:bg-[#14263B]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          {/* Status + Mobile menu */}
          <div className="flex items-center gap-3">
            {/* API Status */}
            <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#101F32] border border-[#22344A]">
              <div
                className={`w-1.5 h-1.5 rounded-full ${
                  apiOnline === null
                    ? 'bg-[#FBBF24] animate-pulse'
                    : apiOnline
                    ? 'bg-[#34D399]'
                    : 'bg-[#FB7185]'
                }`}
              />
              <span className="text-[10px] font-medium text-[#93A4B8]">
                {apiOnline === null ? 'Connecting…' : apiOnline ? 'API Online' : 'API Offline'}
              </span>
            </div>

            {/* Mobile hamburger */}
            <button
              className="md:hidden p-2 rounded-lg text-[#93A4B8] hover:bg-[#14263B] transition-colors"
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label="Menu"
            >
              <svg width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2">
                {menuOpen ? (
                  <path d="M6 6L14 14M14 6L6 14" strokeLinecap="round" />
                ) : (
                  <>
                    <path d="M3 6h14M3 10h14M3 14h14" strokeLinecap="round" />
                  </>
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        {menuOpen && (
          <div className="md:hidden border-t border-[#22344A] py-2 pb-4 space-y-1">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => { onNavigate(item.id); setMenuOpen(false); }}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                  currentPage === item.id
                    ? 'bg-[#21D4C2]/15 text-[#21D4C2]'
                    : 'text-[#93A4B8] hover:bg-[#14263B] hover:text-[#F1F5F9]'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </nav>
  );
}
