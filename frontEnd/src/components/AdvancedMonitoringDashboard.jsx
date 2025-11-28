import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  TrendingUp,
  BarChart3,
  Zap,
  RefreshCw,
  Download,
  Save
} from 'lucide-react';
import websocketService from '../services/websocketService';

/**
 * Advanced Monitoring Dashboard - Performance & System Analytics
 * Displays:
 * - Real-time performance metrics
 * - Network latency and bandwidth
 * - System resource trends
 * - Client connection status
 * - Data export capabilities
 * - System health overview
 */
export default function AdvancedMonitoringDashboard() {
  const [metrics, setMetrics] = useState({
    latency: 45,
    bandwidth: 1.2,
    uptime: 0,
    clientCount: 1,
    fps: 30,
    cpuLoad: 30,
    memoryUsage: 45
  });

  const [history, setHistory] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingData, setRecordingData] = useState([]);

  useEffect(() => {
    // Listen for health telemetry to calculate metrics
    const unsubHealth = websocketService.on('health_telemetry', (data) => {
      setMetrics(prev => ({
        ...prev,
        fps: data.performance?.fps || 30,
        cpuLoad: data.resources?.cpu_usage || 30,
        memoryUsage: data.resources?.memory_usage || 45,
        latency: data.performance?.latency_ms || 45
      }));

      // Record metrics if recording
      if (isRecording) {
        setRecordingData(prev => [...prev, {
          timestamp: new Date().toISOString(),
          ...metrics
        }]);
      }

      // Build history
      setHistory(prev => {
        const updated = [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          ...metrics
        }];
        return updated.slice(-60); // Keep last 60 entries
      });
    });

    // Simulate uptime counter
    const uptimeInterval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        uptime: prev.uptime + 1
      }));
    }, 1000);

    return () => {
      unsubHealth();
      clearInterval(uptimeInterval);
    };
  }, [isRecording]);

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours}h ${minutes}m ${secs}s`;
  };

  const exportMetrics = () => {
    const csv = [
      ['Timestamp', 'Latency (ms)', 'FPS', 'CPU Load (%)', 'Memory Usage (%)'],
      ...recordingData.map(d => [
        d.timestamp,
        d.latency,
        d.fps,
        d.cpuLoad.toFixed(1),
        d.memoryUsage.toFixed(1)
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `s4-metrics-${Date.now()}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const getLatencyColor = (ms) => {
    if (ms < 50) return 'text-emerald-400';
    if (ms < 100) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getResourceColor = (percent) => {
    if (percent < 50) return 'text-emerald-400';
    if (percent < 80) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-6">
      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Latency */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-300 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Latency
            </h3>
            <span className={`text-lg font-bold ${getLatencyColor(metrics.latency)}`}>
              {metrics.latency.toFixed(0)}ms
            </span>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all ${
                metrics.latency < 50 ? 'bg-emerald-500' :
                metrics.latency < 100 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(metrics.latency, 200) / 2}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-400 mt-2">Network Round-Trip</p>
        </div>

        {/* FPS */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-300 flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              Frame Rate
            </h3>
            <span className="text-lg font-bold text-yellow-400">
              {metrics.fps.toFixed(0)} fps
            </span>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
            <div
              className="h-full bg-yellow-500 transition-all"
              style={{ width: `${(metrics.fps / 60) * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-400 mt-2">Video Capture Rate</p>
        </div>

        {/* CPU Load */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-300 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              CPU Load
            </h3>
            <span className={`text-lg font-bold ${getResourceColor(metrics.cpuLoad)}`}>
              {metrics.cpuLoad.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all ${
                metrics.cpuLoad < 50 ? 'bg-emerald-500' :
                metrics.cpuLoad < 80 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${metrics.cpuLoad}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-400 mt-2">Processor Usage</p>
        </div>

        {/* Memory */}
        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-slate-300 flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Memory
            </h3>
            <span className={`text-lg font-bold ${getResourceColor(metrics.memoryUsage)}`}>
              {metrics.memoryUsage.toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all ${
                metrics.memoryUsage < 50 ? 'bg-emerald-500' :
                metrics.memoryUsage < 80 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${metrics.memoryUsage}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-400 mt-2">RAM Usage</p>
        </div>
      </div>

      {/* System Status & Recording */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* System Status */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Activity className="w-5 h-5" />
            System Status
          </h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <span className="text-slate-300">System Uptime</span>
              <span className="font-bold text-emerald-400">{formatUptime(metrics.uptime)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <span className="text-slate-300">Connected Clients</span>
              <span className="font-bold text-cyan-400">{metrics.clientCount}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <span className="text-slate-300">Network Bandwidth</span>
              <span className="font-bold text-blue-400">{metrics.bandwidth.toFixed(2)} Mb/s</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-emerald-900/20 rounded-lg border border-emerald-600/50">
              <span className="text-emerald-300">System Status</span>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="font-bold text-emerald-400">HEALTHY</span>
              </div>
            </div>
          </div>
        </div>

        {/* Recording Controls */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <RefreshCw className="w-5 h-5" />
            Data Collection
          </h3>
          <div className="space-y-4">
            <div className="p-4 bg-slate-800/50 rounded-lg border border-slate-700">
              <p className="text-sm text-slate-400 mb-3">
                {isRecording 
                  ? `Recording ${recordingData.length} data points`
                  : 'Ready to record metrics'
                }
              </p>
              <button
                onClick={() => setIsRecording(!isRecording)}
                className={`w-full px-4 py-2 rounded-lg font-semibold transition-all transform hover:scale-105 active:scale-95 ${
                  isRecording
                    ? 'bg-red-600 hover:bg-red-500 text-white'
                    : 'bg-emerald-600 hover:bg-emerald-500 text-white'
                }`}
              >
                {isRecording ? '⏹️ Stop Recording' : '⏺️ Start Recording'}
              </button>
            </div>

            {recordingData.length > 0 && (
              <div className="p-4 bg-blue-900/20 rounded-lg border border-blue-600/50">
                <p className="text-sm text-blue-300 mb-3">
                  {recordingData.length} data points collected
                </p>
                <button
                  onClick={exportMetrics}
                  className="w-full px-4 py-2 rounded-lg font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all transform hover:scale-105 active:scale-95 flex items-center justify-center gap-2"
                >
                  <Download className="w-4 h-4" />
                  Export as CSV
                </button>
              </div>
            )}

            <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-700 text-xs text-slate-400">
              <p>💡 Recording captures system metrics for analysis and optimization</p>
            </div>
          </div>
        </div>
      </div>

      {/* Performance History */}
      {history.length > 0 && (
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300">Performance History (Last 60s)</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {history.map((entry, idx) => (
              <div key={idx} className="flex items-center justify-between p-2 bg-slate-800/30 rounded text-xs">
                <span className="text-slate-400">{entry.timestamp}</span>
                <div className="flex gap-4">
                  <span className="text-slate-400">
                    Latency: <span className={getLatencyColor(entry.latency)}>{entry.latency.toFixed(0)}ms</span>
                  </span>
                  <span className="text-slate-400">
                    FPS: <span className="text-yellow-400">{entry.fps.toFixed(0)}</span>
                  </span>
                  <span className="text-slate-400">
                    CPU: <span className={getResourceColor(entry.cpuLoad)}>{entry.cpuLoad.toFixed(0)}%</span>
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
