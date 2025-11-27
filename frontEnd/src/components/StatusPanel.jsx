import { useEffect, useState } from 'react';
import websocketService from '../services/websocketService';

export default function StatusPanel() {
  const [telemetry, setTelemetry] = useState({
    battery: 82,
    temperature: 43,
    signalStrength: 5,
    systemStatus: 'OK',
    cpuUsage: 35,
    memoryUsage: 48,
    fpsCount: 30,
    jointErrors: 0,
    lastUpdate: new Date().toLocaleTimeString()
  });

  useEffect(() => {
    const unsubTelemetry = websocketService.on('telemetry_update', (data) => {
      setTelemetry(prev => ({
        ...prev,
        battery: data.battery ?? prev.battery,
        temperature: data.temperature ?? prev.temperature,
        signalStrength: data.signalStrength ?? prev.signalStrength,
        systemStatus: data.systemStatus ?? prev.systemStatus,
        cpuUsage: data.cpuUsage ?? prev.cpuUsage,
        memoryUsage: data.memoryUsage ?? prev.memoryUsage,
        fpsCount: data.fpsCount ?? prev.fpsCount,
        jointErrors: data.jointErrors ?? prev.jointErrors,
        lastUpdate: new Date().toLocaleTimeString()
      }));
    });

    return () => {
      unsubTelemetry();
    };
  }, []);

  const getBatteryColor = (battery) => {
    if (battery >= 60) return 'bg-emerald-500';
    if (battery >= 30) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getTempColor = (temp) => {
    if (temp <= 50) return 'text-emerald-400';
    if (temp <= 70) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getStatusColor = (status) => {
    if (status === 'OK') return 'bg-emerald-900 text-emerald-300';
    if (status === 'WARNING') return 'bg-yellow-900 text-yellow-300';
    return 'bg-red-900 text-red-300';
  };

  const getSignalBars = (strength) => {
    return Array(5).fill(0).map((_, i) => (
      <div
        key={i}
        className={`h-2 flex-1 rounded-sm ${
          i < strength ? 'bg-emerald-400' : 'bg-slate-700'
        }`}
      />
    ));
  };

  return (
    <section className="bg-slate-900 rounded-xl p-4 border border-slate-700 shadow-lg max-h-96 overflow-y-auto">
      <h2 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
        <span>⚙️ Robot Status</span>
      </h2>

      <div className="space-y-4">
        {/* Battery */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-300">🔋 Battery</span>
            <span className="text-sm font-semibold text-cyan-300">{telemetry.battery}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-3 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-300 ${getBatteryColor(
                telemetry.battery
              )}`}
              style={{ width: `${telemetry.battery}%` }}
            />
          </div>
        </div>

        {/* Temperature */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-300">🌡️ Temperature</span>
          <span className={`text-sm font-semibold ${getTempColor(telemetry.temperature)}`}>
            {telemetry.temperature}°C
          </span>
        </div>

        {/* Signal Strength */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-300">📶 Signal Strength</span>
            <span className="text-xs text-slate-400">{telemetry.signalStrength}/5</span>
          </div>
          <div className="flex gap-1">{getSignalBars(telemetry.signalStrength)}</div>
        </div>

        {/* System Status */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-300">Status Badge</span>
          <div className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
            telemetry.systemStatus
          )}`}>
            {telemetry.systemStatus}
          </div>
        </div>

        {/* CPU Usage */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-300">💻 CPU Usage</span>
            <span className="text-sm font-semibold text-slate-300">{telemetry.cpuUsage}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full transition-all duration-300"
              style={{ width: `${telemetry.cpuUsage}%` }}
            />
          </div>
        </div>

        {/* Memory Usage */}
        <div>
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-slate-300">🧠 Memory</span>
            <span className="text-sm font-semibold text-slate-300">{telemetry.memoryUsage}%</span>
          </div>
          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-purple-500 rounded-full transition-all duration-300"
              style={{ width: `${telemetry.memoryUsage}%` }}
            />
          </div>
        </div>

        {/* FPS Counter */}
        <div className="flex justify-between items-center pt-2 border-t border-slate-700">
          <span className="text-sm text-slate-300">⚡ FPS</span>
          <span className="text-sm font-semibold text-emerald-400">{telemetry.fpsCount}</span>
        </div>

        {/* Joint Errors */}
        <div className="flex justify-between items-center">
          <span className="text-sm text-slate-300">🔧 Joint Errors</span>
          <span className={`text-sm font-semibold ${
            telemetry.jointErrors === 0 ? 'text-emerald-400' : 'text-red-400'
          }`}>
            {telemetry.jointErrors}
          </span>
        </div>

        {/* Last Update */}
        <div className="pt-2 border-t border-slate-700">
          <span className="text-xs text-slate-500">Last update: {telemetry.lastUpdate}</span>
        </div>
      </div>
    </section>
  );
}
