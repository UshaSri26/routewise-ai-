import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Optimize from './pages/Optimize';
import MapPage from './pages/MapPage';
import Scenarios from './pages/Scenarios';
import Assistant from './pages/Assistant';
import Methodology from './pages/Methodology';
import type { NavPage, OptimizationResult, Shipment } from './types';

export default function App() {
  const [page, setPage] = useState<NavPage>('home');
  const [lastResult, setLastResult] = useState<OptimizationResult | null>(null);
  const [selectedShipment, setSelectedShipment] = useState<Shipment | null>(null);

  const navigate = (p: NavPage) => setPage(p);

  const handleResult = (result: OptimizationResult, shipment?: Shipment) => {
    setLastResult(result);
    if (shipment) setSelectedShipment(shipment);
    setPage('optimize');
  };

  return (
    <div className="min-h-screen bg-[#07111F] text-[#F1F5F9]">
      <Navbar currentPage={page} onNavigate={navigate} />
      <main className="pt-16">
        {page === 'home' && (
          <Home onResult={handleResult} onNavigate={navigate} />
        )}
        {page === 'optimize' && (
          <Optimize
            initialResult={lastResult}
            initialShipment={selectedShipment}
            onResult={setLastResult}
          />
        )}
        {page === 'map' && (
          <MapPage result={lastResult} />
        )}
        {page === 'scenarios' && (
          <Scenarios selectedShipment={selectedShipment} />
        )}
        {page === 'assistant' && (
          <Assistant result={lastResult} selectedShipment={selectedShipment} />
        )}
        {page === 'methodology' && <Methodology />}
      </main>
    </div>
  );
}
