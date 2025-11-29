import { useEffect, useState } from 'react';
import { ChevronDown, Settings, RotateCw } from 'lucide-react';
import Header from '../components/Header';
import OperationsDashboard from '../components/OperationsDashboard';
import TeleopPanel from '../components/TeleopPanel';
import HealthMonitoringPanel from '../components/HealthMonitoringPanel';
import PathLoggingPanel from '../components/PathLoggingPanel';
import OTAUpdatePanel from '../components/OTAUpdatePanel';
import LogsPanel from '../components/LogsPanel';
import HumanoidRobotVisual from '../components/HumanoidRobotVisual';
import RobotJointsPanel from '../components/RobotJointsPanel';
import websocketService from '../services/websocketService';

/**
 * S4 Remote Robot Management Cloud System - Main Dashboard
 * 
 * Integrated Control Room featuring:
 * - Real-time Operations Dashboard with robot status, battery, mode, position
 * - Tele-operated Driving with joystick and emergency controls
 * - Health Monitoring with real-time graphs and predictive maintenance
 * - Path Logging & Kinematics with trajectory visualization and playback
 * - OTA Update Management for remote software updates
 * - Event Logging & System Events
 * - Mobile-responsive layout for remote operations
 */
export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('operations');
  const [isConnected, setIsConnected] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [joints, setJoints] = useState([]);
  const [robotMode, setRobotMode] = useState('standing');
  const [robotStatus, setRobotStatus] = useState({});

  useEffect(() => {
    // Initialize WebSocket connection
    websocketService.connect().catch(error => {
      console.error('Failed to connect to WebSocket:', error);
    });

    // Listen for connection status
    const unsubConnection = websocketService.on('connection', (data) => {
      setIsConnected(data.status === 'connected');
    });

    // Listen for joint updates (18 joints for humanoid robot)
    const unsubJoints = websocketService.on('joints', (data) => {
      if (data.robot_id === 'robot_01') {
        setJoints(data.data.joints || []);
      }
    });

    // Listen for telemetry updates (includes mode)
    const unsubTelemetry = websocketService.on('telemetry', (data) => {
      if (data.robot_id === 'robot_01') {
        setRobotStatus(data.data);
        const newMode = data.data.mode || 'standing';
        console.log('📊 Telemetry received - Mode:', newMode);
        setRobotMode(newMode);
      }
    });

    // Listen for pose updates (for lat/lng visualization)
    const unsubPose = websocketService.on('pose', (data) => {
      if (data.robot_id === 'robot_01') {
        console.log('📍 Pose update:', data.data);
      }
    });

    // Commented out: GPS subscription (not needed unless displaying GPS coordinates)
    // const unsubGPS = websocketService.on('gps', (data) => {
    //   if (data.robot_id === 'robot_01') {
    //     console.log('🛰️ GPS update:', data.data);
    //   }
    // });

    // Cleanup subscriptions
    return () => {
      unsubConnection();
      unsubJoints();
      unsubTelemetry();
      unsubPose();
    };
  }, []);

  const tabs = [
    { id: 'operations', label: '📊 Operations', icon: '🎯' },
    { id: 'teleop', label: '🎮 Teleoperation', icon: '👾' },
    { id: 'robot-viz', label: '🤖 Robot Visual', icon: '🦾' },
    { id: 'joints', label: '⚙️ Joint Monitor', icon: '🔧' },
    { id: 'health', label: '❤️ Health Monitor', icon: '📈' },
    { id: 'path', label: '🗺️ Path Logging', icon: '📍' },
    { id: 'updates', label: '⬇️ Software Updates', icon: '🔄' },
    { id: 'logs', label: '📋 System Logs', icon: '📝' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100">
      {/* Header */}
      <Header />

      {/* Main Content Area */}
      <main className="p-4 md:p-6 max-w-7xl mx-auto">
        {/* Tab Navigation */}
        <div className="mb-6 flex flex-wrap gap-2 overflow-x-auto pb-2 scrollbar-hide">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 rounded-lg font-semibold transition-all whitespace-nowrap transform hover:scale-105 active:scale-95 ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/50'
                  : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Connection Status Alert */}
        {!isConnected && (
          <div className="mb-6 bg-red-900/20 border border-red-600/50 rounded-lg p-4 flex items-center gap-3 animate-pulse">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-red-300 font-semibold">
              ⚠️ Disconnected - Attempting to reconnect...
            </span>
          </div>
        )}

        {/* Tab Content */}
        <div className="space-y-6">
          {/* Operations Dashboard */}
          {activeTab === 'operations' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Operations Dashboard</h2>
                <p className="text-slate-400">Real-time robot status, metrics, and alerts</p>
              </div>
              <OperationsDashboard />
            </div>
          )}

          {/* Teleoperation Control */}
          {activeTab === 'teleop' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Teleoperation Control</h2>
                <p className="text-slate-400">Remote driving with real-time control and emergency stop</p>
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <TeleopPanel />
                </div>
                <div className="space-y-4">
                  <div className="bg-slate-900 rounded-lg border border-slate-700 p-4 shadow-lg">
                    <h3 className="font-semibold mb-4 text-cyan-300">Control Guide</h3>
                    <div className="space-y-3 text-sm">
                      <div>
                        <div className="font-semibold text-slate-300 mb-1">Joystick</div>
                        <p className="text-slate-400">Drag to move and rotate robot</p>
                      </div>
                      <div>
                        <div className="font-semibold text-slate-300 mb-1">Quick Buttons</div>
                        <p className="text-slate-400">Forward, Backward, Left, Right movements</p>
                      </div>
                      <div>
                        <div className="font-semibold text-slate-300 mb-1">Emergency Stop</div>
                        <p className="text-slate-400">Instantly stops all robot movement</p>
                      </div>
                      <div>
                        <div className="font-semibold text-slate-300 mb-1">Mode Selection</div>
                        <p className="text-slate-400">Walk for normal operation, Run for high speed</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Robot Visualization */}
          {activeTab === 'robot-viz' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Humanoid Robot Visualization</h2>
                <p className="text-slate-400">Real-time 2D visualization of all 18 joints with pose and mode display</p>
              </div>
              <div className="flex justify-center items-center">
                <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
                  <HumanoidRobotVisual joints={joints} mode={robotMode} />
                  {joints.length === 0 && (
                    <div className="text-center mt-4 text-slate-500">
                      <p className="text-sm">⏳ Waiting for joint data from robot...</p>
                      <p className="text-xs mt-2">Ensure backend is running and robot simulator is active</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Joint Monitor */}
          {activeTab === 'joints' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Joint Monitor Dashboard</h2>
                <p className="text-slate-400">Comprehensive view of all 18 humanoid robot joints with filtering and sorting</p>
              </div>
              <div className="bg-slate-900 rounded-lg border border-slate-700 p-6 shadow-lg">
                <RobotJointsPanel joints={joints} />
              </div>
            </div>
          )}

          {/* Health Monitoring */}
          {activeTab === 'health' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Health Monitoring & Analytics</h2>
                <p className="text-slate-400">Real-time system metrics with predictive maintenance alerts</p>
              </div>
              <HealthMonitoringPanel />
            </div>
          )}

          {/* Path Logging */}
          {activeTab === 'path' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Path Logging & Kinematics</h2>
                <p className="text-slate-400">Trajectory tracking, visualization, and analysis</p>
              </div>
              <PathLoggingPanel />
            </div>
          )}

          {/* Software Updates */}
          {activeTab === 'updates' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">Remote Software Updates (OTA)</h2>
                <p className="text-slate-400">Manage robot firmware and software versions</p>
              </div>
              <OTAUpdatePanel />
            </div>
          )}

          {/* System Logs */}
          {activeTab === 'logs' && (
            <div className="animate-in fade-in">
              <div className="mb-4">
                <h2 className="text-2xl font-bold text-cyan-300 mb-2">System Event Log</h2>
                <p className="text-slate-400">Comprehensive audit trail of all system events</p>
              </div>
              <LogsPanel />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 border-t border-slate-800 py-6 px-6 text-center text-slate-400 text-sm">
        <div className="max-w-7xl mx-auto space-y-2">
          <p className="font-semibold text-slate-400">
            Remote Robot Management Cloud System v1.0
          </p>
        </div>
      </footer>

      {/* Global Styles for Scrollbar */}
      <style jsx>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-in {
          animation: fadeIn 0.3s ease-in-out;
        }
      `}</style>
    </div>
  );
}
