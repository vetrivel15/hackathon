import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar
} from 'recharts';
import {
  AlertTriangle,
  TrendingUp,
  Activity,
  Cpu,
  Thermometer,
  HardDrive,
  Zap
} from 'lucide-react';
import websocketService from '../services/websocketService';

/**
 * Health Monitoring Panel - Real-time Health Graphs & Analytics
 * Displays:
 * - Battery level trends over time
 * - Temperature monitoring (CPU & Motor)
 * - CPU and Memory usage
 * - Performance metrics (FPS, latency)
 * - Predictive maintenance warnings
 */
export default function HealthMonitoringPanel() {
  const [batteryHistory, setBatteryHistory] = useState([]);
  const [temperatureHistory, setTemperatureHistory] = useState([]);
  const [resourceHistory, setResourceHistory] = useState([]);
  const [maintenanceWarnings, setMaintenanceWarnings] = useState([]);
  const [currentHealth, setCurrentHealth] = useState({
    battery: 85,
    temperature: 42,
    motorTemp: 45,
    cpuUsage: 30,
    memoryUsage: 45,
    diskUsage: 32,
    fps: 30,
    latency: 45,
    healthScore: 85,
    healthStatus: 'HEALTHY'
  });

  useEffect(() => {
    // Listen for health telemetry updates and build history
    const unsubHealth = websocketService.on('health_telemetry', (data) => {
      const timestamp = new Date().toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      });

      // Update current health
      setCurrentHealth({
        battery: data.battery?.level || 85,
        temperature: data.thermal?.cpu_temp || 42,
        motorTemp: data.thermal?.motor_temp || 45,
        cpuUsage: data.resources?.cpu_usage || 30,
        memoryUsage: data.resources?.memory_usage || 45,
        diskUsage: data.resources?.disk_usage || 32,
        fps: data.performance?.fps || 30,
        latency: data.performance?.latency_ms || 45,
        healthScore: data.health_score || 85,
        healthStatus: data.health_status || 'HEALTHY'
      });

      // Update battery history (keep last 30 points)
      setBatteryHistory((prev) => {
        const updated = [
          ...prev,
          {
            timestamp,
            battery: data.battery?.level || 85,
            health: data.battery?.health || 95
          }
        ];
        return updated.slice(-30);
      });

      // Update temperature history (keep last 30 points)
      setTemperatureHistory((prev) => {
        const updated = [
          ...prev,
          {
            timestamp,
            cpu_temp: data.thermal?.cpu_temp || 42,
            motor_temp: data.thermal?.motor_temp || 45
          }
        ];
        return updated.slice(-30);
      });

      // Update resource history (keep last 20 points)
      setResourceHistory((prev) => {
        const updated = [
          ...prev,
          {
            timestamp,
            cpu: data.resources?.cpu_usage || 30,
            memory: data.resources?.memory_usage || 45,
            disk: data.resources?.disk_usage || 32
          }
        ];
        return updated.slice(-20);
      });
    });

    // Listen for maintenance alerts
    const unsubMaintenance = websocketService.on('maintenance_alert', (data) => {
      setMaintenanceWarnings(data.warnings || []);
    });

    return () => {
      unsubHealth();
      unsubMaintenance();
    };
  }, []);

  const getHealthColor = (status) => {
    switch (status) {
      case 'HEALTHY':
        return 'text-emerald-400';
      case 'WARNING':
        return 'text-yellow-400';
      case 'CRITICAL':
        return 'text-red-400';
      default:
        return 'text-slate-400';
    }
  };

  const getHealthBg = (status) => {
    switch (status) {
      case 'HEALTHY':
        return 'bg-emerald-900/20 border-emerald-600/50';
      case 'WARNING':
        return 'bg-yellow-900/20 border-yellow-600/50';
      case 'CRITICAL':
        return 'bg-red-900/20 border-red-600/50';
      default:
        return 'bg-slate-800/50 border-slate-600/50';
    }
  };

  return (
    <div className="space-y-6">
      {/* Health Score Card */}
      <div className={`rounded-lg border p-6 shadow-lg ${getHealthBg(currentHealth.healthStatus)}`}>
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              System Health Overview
            </h3>
            <p className={`text-4xl font-bold ${getHealthColor(currentHealth.healthStatus)}`}>
              {currentHealth.healthScore.toFixed(1)}%
            </p>
            <p className={`text-sm mt-2 font-semibold ${getHealthColor(currentHealth.healthStatus)}`}>
              Status: {currentHealth.healthStatus}
            </p>
          </div>
          <div className="flex-1 max-w-xs">
            <div className="w-full bg-slate-700/50 rounded-full h-4 overflow-hidden border border-slate-600">
              <div
                className={`h-full transition-all ${
                  currentHealth.healthScore > 70
                    ? 'bg-emerald-500'
                    : currentHealth.healthScore > 40
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                }`}
                style={{ width: `${currentHealth.healthScore}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Battery & Temperature Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Battery Trend */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Battery Trend
          </h3>
          {batteryHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={batteryHistory}>
                <defs>
                  <linearGradient id="colorBattery" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#e2e8f0' }}
                  formatter={(value) => `${value.toFixed(1)}%`}
                />
                <Area
                  type="monotone"
                  dataKey="battery"
                  stroke="#10b981"
                  fillOpacity={1}
                  fill="url(#colorBattery)"
                  name="Battery Level"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-slate-500">Waiting for data...</div>
          )}
          <div className="mt-4 text-sm text-slate-400">
            Current: <span className="text-emerald-400 font-bold">{currentHealth.battery.toFixed(1)}%</span>
          </div>
        </div>

        {/* Temperature Monitoring */}
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
            <Thermometer className="w-5 h-5" />
            Temperature Monitoring
          </h3>
          {temperatureHistory.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={temperatureHistory}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="timestamp" tick={{ fontSize: 11, fill: '#94a3b8' }} />
                <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[30, 80]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px'
                  }}
                  labelStyle={{ color: '#e2e8f0' }}
                  formatter={(value) => `${value.toFixed(1)}°C`}
                />
                <Legend wrapperStyle={{ color: '#94a3b8' }} />
                <Line
                  type="monotone"
                  dataKey="cpu_temp"
                  stroke="#f59e0b"
                  dot={false}
                  isAnimationActive={false}
                  name="CPU Temp"
                />
                <Line
                  type="monotone"
                  dataKey="motor_temp"
                  stroke="#ef4444"
                  dot={false}
                  isAnimationActive={false}
                  name="Motor Temp"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-slate-500">Waiting for data...</div>
          )}
          <div className="mt-4 text-sm text-slate-400">
            CPU: <span className="text-yellow-400 font-bold">{currentHealth.temperature.toFixed(1)}°C</span>
            {' '} / Motor: <span className="text-red-400 font-bold">{currentHealth.motorTemp.toFixed(1)}°C</span>
          </div>
        </div>
      </div>

      {/* Resource Usage */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
        <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
          <Cpu className="w-5 h-5" />
          System Resources
        </h3>
        {resourceHistory.length > 0 ? (
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={resourceHistory}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="timestamp" tick={{ fontSize: 11, fill: '#94a3b8' }} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px'
                }}
                labelStyle={{ color: '#e2e8f0' }}
                formatter={(value) => `${value.toFixed(1)}%`}
              />
              <Legend wrapperStyle={{ color: '#94a3b8' }} />
              <Bar dataKey="cpu" stackId="a" fill="#3b82f6" name="CPU Usage" />
              <Bar dataKey="memory" stackId="a" fill="#8b5cf6" name="Memory Usage" />
              <Bar dataKey="disk" stackId="a" fill="#06b6d4" name="Disk Usage" />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-60 flex items-center justify-center text-slate-500">Waiting for data...</div>
        )}
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-slate-400">CPU</span>
            <div className="text-lg font-bold text-blue-400">{currentHealth.cpuUsage.toFixed(1)}%</div>
          </div>
          <div>
            <span className="text-slate-400">Memory</span>
            <div className="text-lg font-bold text-purple-400">{currentHealth.memoryUsage.toFixed(1)}%</div>
          </div>
          <div>
            <span className="text-slate-400">Disk</span>
            <div className="text-lg font-bold text-cyan-400">{currentHealth.diskUsage.toFixed(1)}%</div>
          </div>
        </div>
      </div>

      {/* Maintenance Warnings */}
      {maintenanceWarnings.length > 0 && (
        <div className="bg-yellow-900/20 border border-yellow-600/50 rounded-lg p-4 shadow-lg">
          <h3 className="font-semibold mb-4 text-yellow-300 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5" />
            Maintenance Alerts
          </h3>
          <div className="space-y-3">
            {maintenanceWarnings.map((warning, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-lg border ${
                  warning.severity === 'HIGH'
                    ? 'bg-red-900/20 border-red-600/50 text-red-200'
                    : 'bg-yellow-900/20 border-yellow-600/50 text-yellow-200'
                }`}
              >
                <div className="font-semibold text-sm mb-1">{warning.type}</div>
                <div className="text-sm">{warning.message}</div>
                {warning.recommended_action && (
                  <div className="text-xs mt-2 opacity-75">
                    💡 {warning.recommended_action}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-slate-400 text-sm mb-2">Frame Rate</div>
          <div className="text-2xl font-bold text-yellow-400">{currentHealth.fps.toFixed(1)}</div>
          <div className="text-xs text-slate-500">FPS</div>
        </div>
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-slate-400 text-sm mb-2">Latency</div>
          <div className="text-2xl font-bold text-cyan-400">{currentHealth.latency.toFixed(0)}</div>
          <div className="text-xs text-slate-500">ms</div>
        </div>
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-slate-400 text-sm mb-2">Battery</div>
          <div className="text-2xl font-bold text-emerald-400">{currentHealth.battery.toFixed(1)}</div>
          <div className="text-xs text-slate-500">%</div>
        </div>
        <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
          <div className="text-slate-400 text-sm mb-2">Health Score</div>
          <div className={`text-2xl font-bold ${getHealthColor(currentHealth.healthStatus)}`}>
            {currentHealth.healthScore.toFixed(1)}
          </div>
          <div className="text-xs text-slate-500">%</div>
        </div>
      </div>
    </div>
  );
}
