import { useEffect, useState, useRef } from 'react';
import websocketService from '../services/websocketService';

export default function LogsPanel() {
  const [logs, setLogs] = useState([
    { time: new Date(), level: 'INFO', message: 'Dashboard initialized' },
    { time: new Date(), level: 'INFO', message: 'WebSocket connecting...' }
  ]);
  const scrollContainer = useRef(null);

  useEffect(() => {
    const unsubLogEvent = websocketService.on('log_event', (data) => {
      const newLog = {
        time: new Date(data.timestamp || Date.now()),
        level: data.level || 'INFO',
        message: data.message
      };

      setLogs(prev => {
        const updated = [...prev, newLog];
        // Keep only last 100 logs
        return updated.slice(-100);
      });
    });

    const unsubConnection = websocketService.on('connection', (data) => {
      const newLog = {
        time: new Date(),
        level: 'INFO',
        message: `WebSocket ${data.status === 'connected' ? 'connected' : 'disconnected'}`
      };

      setLogs(prev => [...prev, newLog].slice(-100));
    });

    const unsubControl = websocketService.on('control', (data) => {
      const newLog = {
        time: new Date(),
        level: 'INFO',
        message: `Command sent: ${data.action} (${JSON.stringify(data.value || {})})`
      };

      setLogs(prev => [...prev, newLog].slice(-100));
    });

    const unsubMode = websocketService.on('mode_update', (data) => {
      const newLog = {
        time: new Date(),
        level: 'INFO',
        message: `Mode changed to: ${data.mode}`
      };

      setLogs(prev => [...prev, newLog].slice(-100));
    });

    return () => {
      unsubLogEvent();
      unsubConnection();
      unsubControl();
      unsubMode();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollContainer.current) {
      scrollContainer.current.scrollTop = scrollContainer.current.scrollHeight;
    }
  }, [logs]);

  const getLevelColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-400 bg-red-900/20';
      case 'WARN':
        return 'text-yellow-400 bg-yellow-900/20';
      case 'INFO':
        return 'text-emerald-400 bg-emerald-900/20';
      case 'DEBUG':
        return 'text-slate-400 bg-slate-800/50';
      default:
        return 'text-slate-300';
    }
  };

  const getLevelBadgeColor = (level) => {
    switch (level) {
      case 'ERROR':
        return 'bg-red-900 text-red-300';
      case 'WARN':
        return 'bg-yellow-900 text-yellow-300';
      case 'INFO':
        return 'bg-emerald-900 text-emerald-300';
      case 'DEBUG':
        return 'bg-slate-800 text-slate-400';
      default:
        return 'bg-slate-700 text-slate-300';
    }
  };

  return (
    <section className="bg-slate-900 rounded-xl p-4 border border-slate-700 shadow-lg h-96 max-h-96 flex flex-col">
      <h2 className="font-semibold mb-3 text-cyan-300 flex items-center justify-between">
        <span>📋 System Logs & Events</span>
        <span className="text-xs bg-slate-800 px-2 py-1 rounded text-slate-400">
          {logs.length} events
        </span>
      </h2>

      <div
        ref={scrollContainer}
        className="flex-1 overflow-y-auto space-y-2 bg-slate-800 rounded-lg p-3 border border-slate-700"
      >
        {logs.length === 0 ? (
          <div className="text-center text-slate-500 text-sm py-8">
            No logs yet. System events will appear here.
          </div>
        ) : (
          logs.map((log, idx) => (
            <div
              key={idx}
              className={`text-xs font-mono ${getLevelColor(
                log.level
              )} p-2 rounded border border-slate-600/30 hover:bg-slate-700/50 transition-colors`}
            >
              <div className="flex gap-2 items-start">
                <span className="text-slate-400">
                  [{log.time.toLocaleTimeString()}]
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${getLevelBadgeColor(
                  log.level
                )}`}>
                  {log.level}
                </span>
                <span className="flex-1 text-slate-200 break-words">
                  {log.message}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {logs.length > 0 && (
        <div className="mt-2 text-xs text-slate-500 border-t border-slate-700 pt-2">
          <button
            onClick={() => setLogs([])}
            className="text-slate-400 hover:text-slate-300 transition-colors"
          >
            Clear logs
          </button>
        </div>
      )}
    </section>
  );
}
