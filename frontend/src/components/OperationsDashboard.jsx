import { useEffect, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  Battery,
  Cpu,
  Gauge,
  Heart,
  Map,
  Radio,
  Thermometer,
  Zap,
  AlertCircle,
  CheckCircle2,
  Clock
} from 'lucide-react';
import websocketService from '../services/websocketService';

/**
 * Operations Dashboard - Real-time Robot Status & Monitoring
 * Displays:
 * - Robot online/offline status
 * - Battery percentage and health
 * - Current mode (AUTO/MANUAL/STANDBY)
 * - Position (X,Y coordinates)
 * - Alert & warning panel
 * - Task queue panel
 */
export default function OperationsDashboard() {
  const [robotStatus, setRobotStatus] = useState('OFFLINE');
  const [battery, setBattery] = useState(85);
  const [batteryHealth, setBatteryHealth] = useState(95);
  const [mode, setMode] = useState('STANDBY');
  const [position, setPosition] = useState({ x: 0, y: 0, heading: 0 });
  const [alerts, setAlerts] = useState([]);
  const [taskQueue, setTaskQueue] = useState([
    { id: 1, name: 'Path Logging', status: 'ACTIVE', progress: 100 },
    { id: 2, name: 'Health Monitoring', status: 'ACTIVE', progress: 100 },
    { id: 3, name: 'System Diagnostics', status: 'PENDING', progress: 0 }
  ]);
  const [health, setHealth] = useState({
    temperature: 42,
    cpuUsage: 30,
    signal: 5,
    fps: 30
  });

  useEffect(() => {
    // Listen for connection status
    const unsubConnection = websocketService.on('connection', (data) => {
      setRobotStatus(data.status === 'connected' ? 'ONLINE' : 'OFFLINE');
    });

    // Listen for control state updates
    const unsubControl = websocketService.on('control_state', (data) => {
      setMode(data.mode || 'STANDBY');
      setPosition({
        x: parseFloat(data.position?.x || 0).toFixed(2),
        y: parseFloat(data.position?.y || 0).toFixed(2),
        heading: parseFloat(data.position?.heading || 0).toFixed(1)
      });
    });

    // Listen for health telemetry
    const unsubHealth = websocketService.on('health_telemetry', (data) => {
      setBattery(data.battery?.level || 85);
      setBatteryHealth(data.battery?.health || 95);
      setHealth({
        temperature: data.thermal?.cpu_temp || 42,
        cpuUsage: data.resources?.cpu_usage || 30,
        signal: data.performance?.signal_strength || 5,
        fps: data.performance?.fps || 30
      });

      // Generate alerts based on health thresholds
      const newAlerts = [];
      if (data.battery?.level < 20) {
        newAlerts.push({
          id: 'battery',
          type: 'warning',
          message: 'Battery low - consider charging',
          icon: 'battery'
        });
      }
      if (data.thermal?.cpu_temp > 70) {
        newAlerts.push({
          id: 'temp',
          type: 'critical',
          message: 'CPU temperature critical',
          icon: 'thermometer'
        });
      }
      if (data.performance?.signal_strength < 2) {
        newAlerts.push({
          id: 'signal',
          type: 'warning',
          message: 'Signal strength weak',
          icon: 'radio'
        });
      }
      setAlerts(newAlerts);
    });

    // Listen for maintenance alerts
    const unsubMaintenance = websocketService.on('maintenance_alert', (data) => {
      const maintenanceAlerts = data.warnings.map((w, i) => ({
        id: `maint-${i}`,
        type: w.severity === 'HIGH' ? 'critical' : 'warning',
        message: w.message,
        icon: 'alert'
      }));
      setAlerts(prev => [...prev, ...maintenanceAlerts]);
    });

    return () => {
      unsubConnection();
      unsubControl();
      unsubHealth();
      unsubMaintenance();
    };
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'ONLINE':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/50';
      case 'OFFLINE':
        return 'bg-red-500/20 text-red-300 border-red-500/50';
      default:
        return 'bg-slate-500/20 text-slate-300 border-slate-500/50';
    }
  };

  const getModeColor = (m) => {
    switch (m) {
      case 'MANUAL':
        return 'bg-yellow-900/40 text-yellow-300 border-yellow-600/50';
      case 'AUTO':
        return 'bg-blue-900/40 text-blue-300 border-blue-600/50';
      case 'STOPPED':
        return 'bg-red-900/40 text-red-300 border-red-600/50';
      default:
        return 'bg-slate-800/40 text-slate-300 border-slate-600/50';
    }
  };

  const getAlertIcon = (type) => {
    switch (type) {
      case 'battery':
        return <Battery className="w-5 h-5" />;
      case 'thermometer':
        return <Thermometer className="w-5 h-5" />;
      case 'radio':
        return <Radio className="w-5 h-5" />;
      default:
        return <AlertTriangle className="w-5 h-5" />;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      {/* Main Status Card */}
      <div className="lg:col-span-3 bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-slate-700 p-6 shadow-lg">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Robot Status */}
          <div className="flex flex-col items-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-full ${getStatusColor(robotStatus)} border mb-3`}>
              <span className={`w-2.5 h-2.5 rounded-full ${robotStatus === 'ONLINE' ? 'bg-emerald-400 animate-pulse' : 'bg-red-400'}`}></span>
              <span className="font-bold text-sm">{robotStatus}</span>
            </div>
            <Activity className="w-6 h-6 text-cyan-400 mb-2" />
            <span className="text-xs text-slate-400">Status</span>
          </div>

          {/* Mode */}
          <div className="flex flex-col items-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className={`flex items-center gap-2 px-3 py-2 rounded-full ${getModeColor(mode)} border mb-3 text-sm font-bold`}>
              {mode}
            </div>
            <Gauge className="w-6 h-6 text-blue-400 mb-2" />
            <span className="text-xs text-slate-400">Mode</span>
          </div>

          {/* Battery */}
          <div className="flex flex-col items-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="mb-3">
              <div className="w-12 h-6 border-2 border-slate-600 rounded-sm flex items-center justify-center">
                <div
                  className={`h-4 transition-all ${battery > 60 ? 'bg-emerald-500' : battery > 20 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${battery * 0.9}%` }}
                ></div>
              </div>
              <div className="w-1 h-2 bg-slate-600 rounded-r-sm mt-0.5 ml-11"></div>
            </div>
            <Battery className={`w-6 h-6 mb-2 ${battery > 60 ? 'text-emerald-400' : battery > 20 ? 'text-yellow-400' : 'text-red-400'}`} />
            <span className="text-sm font-bold">{battery.toFixed(1)}%</span>
            <span className="text-xs text-slate-400">Battery</span>
          </div>

          {/* Health Score */}
          <div className="flex flex-col items-center p-4 bg-slate-800/50 rounded-lg border border-slate-700">
            <div className="w-12 h-12 rounded-full bg-gradient-to-br from-emerald-500/30 to-cyan-500/30 flex items-center justify-center mb-2 border border-emerald-500/50">
              <Heart className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="text-sm font-bold">{batteryHealth.toFixed(0)}%</span>
            <span className="text-xs text-slate-400">Health</span>
          </div>
        </div>
      </div>

      {/* Position & Heading */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
        <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
          <Map className="w-5 h-5" />
          Position
        </h3>
        <div className="space-y-3">
          <div>
            <label className="text-xs text-slate-400">X Position</label>
            <div className="text-2xl font-bold text-emerald-400">{position.x}</div>
            <div className="text-xs text-slate-500">meters</div>
          </div>
          <div>
            <label className="text-xs text-slate-400">Y Position</label>
            <div className="text-2xl font-bold text-emerald-400">{position.y}</div>
            <div className="text-xs text-slate-500">meters</div>
          </div>
          <div>
            <label className="text-xs text-slate-400">Heading</label>
            <div className="text-2xl font-bold text-blue-400">{position.heading}°</div>
            <div className="text-xs text-slate-500">degrees</div>
          </div>
        </div>
      </div>

      {/* Health Metrics */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
        <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
          <Heart className="w-5 h-5" />
          Health Metrics
        </h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400">
              <Thermometer className="w-4 h-4 text-red-400" />
              <span>Temperature</span>
            </div>
            <span className={`font-bold ${health.temperature > 70 ? 'text-red-400' : 'text-emerald-400'}`}>
              {health.temperature.toFixed(1)}°C
            </span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400">
              <Cpu className="w-4 h-4 text-blue-400" />
              <span>CPU Usage</span>
            </div>
            <span className="font-bold text-blue-400">{health.cpuUsage.toFixed(1)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400">
              <Radio className="w-4 h-4 text-cyan-400" />
              <span>Signal</span>
            </div>
            <span className="font-bold text-cyan-400">{health.signal}/5</span>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-slate-400">
              <Zap className="w-4 h-4 text-yellow-400" />
              <span>FPS</span>
            </div>
            <span className="font-bold text-yellow-400">{health.fps.toFixed(1)}</span>
          </div>
        </div>
      </div>

      {/* Alerts & Warnings Panel */}
      <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
        <h3 className="font-semibold mb-4 text-orange-300 flex items-center gap-2">
          <AlertTriangle className="w-5 h-5" />
          Alerts & Warnings
        </h3>
        {alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-6 text-slate-500">
            <CheckCircle2 className="w-8 h-8 mb-2 text-emerald-500" />
            <span className="text-sm">All Systems Nominal</span>
          </div>
        ) : (
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className={`p-3 rounded-lg border flex items-start gap-3 ${
                  alert.type === 'critical'
                    ? 'bg-red-900/20 border-red-600/50 text-red-200'
                    : 'bg-yellow-900/20 border-yellow-600/50 text-yellow-200'
                }`}
              >
                <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <span className="text-sm">{alert.message}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Task Queue Panel */}
      <div className="lg:col-span-2 bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
        <h3 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
          <Clock className="w-5 h-5" />
          Task Queue
        </h3>
        <div className="space-y-2">
          {taskQueue.map((task) => (
            <div key={task.id} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700">
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-200">{task.name}</span>
                <span
                  className={`text-xs font-bold px-2 py-1 rounded-full ${
                    task.status === 'ACTIVE'
                      ? 'bg-emerald-900/40 text-emerald-300'
                      : 'bg-slate-700/40 text-slate-300'
                  }`}
                >
                  {task.status}
                </span>
              </div>
              <div className="w-full bg-slate-700/50 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full transition-all ${task.status === 'ACTIVE' ? 'bg-emerald-500' : 'bg-slate-600'}`}
                  style={{ width: `${task.progress}%` }}
                ></div>
              </div>
              <div className="text-xs text-slate-400 mt-1">{task.progress}% Complete</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
