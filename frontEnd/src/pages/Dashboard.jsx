import { useEffect } from 'react';
import Header from '../components/Header';
import MapPanel from '../components/MapPanel';
import StatusPanel from '../components/StatusPanel';
import TeleopPanel from '../components/TeleopPanel';
import LogsPanel from '../components/LogsPanel';
import websocketService from '../services/websocketService';

export default function Dashboard() {
  useEffect(() => {
    // Initialize WebSocket connection
    websocketService.connect().catch(error => {
      console.error('Failed to connect to WebSocket:', error);
    });

    return () => {
      // Cleanup not needed as service persists across renders
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <Header />

      <main className="p-6 max-w-7xl mx-auto">
        {/* 2x2 Responsive Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 auto-rows-max lg:auto-rows-fr">
          {/* Top Left: Live Map - takes full height on large screens */}
          <div className="lg:row-span-2">
            <MapPanel />
          </div>

          {/* Top Right: Teleoperation Control */}
          <div>
            <TeleopPanel />
          </div>

          {/* Bottom Right: Robot Status */}
          <div>
            <StatusPanel />
          </div>

          {/* Bottom: Logs & Events - spans full width on mobile */}
          <div className="lg:col-span-2">
            <LogsPanel />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-800 py-4 px-6 text-center text-slate-500 text-sm">
        <p>🤖 Humanoid Robot Command Center v1.0 | Real-time Remote Control Dashboard</p>
      </footer>
    </div>
  );
}
