import { useEffect, useState } from 'react';
import websocketService from '../services/websocketService';

export default function Header() {
  const [isConnected, setIsConnected] = useState(false);
  const [mode, setMode] = useState('IDLE');

  useEffect(() => {
    const unsubConnection = websocketService.on('connection', (data) => {
      setIsConnected(data.status === 'connected');
    });

    const unsubMode = websocketService.on('mode_update', (data) => {
      setMode(data.mode || 'IDLE');
    });

    return () => {
      unsubConnection();
      unsubMode();
    };
  }, []);

  return (
    <header className="flex flex-col md:flex-row justify-between items-start md:items-center px-6 py-4 border-b border-slate-700 bg-gradient-to-r from-slate-900 to-slate-800">
      <div>
        <h1 className="text-2xl font-bold text-cyan-400">🤖 Humanoid Command Center</h1>
        <p className="text-sm text-slate-400">Robot ID: zeeno • 32-DOF Remote Control</p>
      </div>
      
      <div className="flex flex-wrap gap-6 text-sm mt-4 md:mt-0">
        <div className="flex items-center gap-2">
          <span className="text-slate-300">Connection:</span>
          <div className={`flex items-center gap-2 px-3 py-1 rounded-full ${
            isConnected 
              ? 'bg-emerald-900 text-emerald-300' 
              : 'bg-red-900 text-red-300'
          }`}>
            <span className={`w-2 h-2 rounded-full animate-pulse ${
              isConnected ? 'bg-emerald-400' : 'bg-red-400'
            }`}></span>
            {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-slate-300">Mode:</span>
          <div className={`px-3 py-1 rounded-full font-semibold ${
            mode === 'TELEOP' 
              ? 'bg-yellow-900 text-yellow-300' 
              : 'bg-slate-700 text-slate-300'
          }`}>
            {mode}
          </div>
        </div>
      </div>
    </header>
  );
}
