import { useEffect, useRef, useState } from 'react';
import nipplejs from 'nipplejs';
import websocketService from '../services/websocketService';

export default function TeleopPanel() {
  const joystickContainer = useRef(null);
  const joystickInstance = useRef(null);
  const [posture, setPosture] = useState('Stand');
  const [mode, setMode] = useState('Walk');
  const [isEmergencyStop, setIsEmergencyStop] = useState(false);
  const [joystickActive, setJoystickActive] = useState(false);
  const [velocityDisplay, setVelocityDisplay] = useState({ linear: 0, angular: 0 });
  const velocityRef = useRef({ linear: 0, angular: 0 });
  const velocitySendIntervalRef = useRef(null);

  // Initialize joystick with enhanced appearance
  useEffect(() => {
    if (!joystickContainer.current) return;

    try {
      joystickInstance.current = nipplejs.create({
        zone: joystickContainer.current,
        mode: 'static',
        position: { left: '50%', bottom: '50%', transform: 'translate(-50%, 50%)' },
        color: joystickActive ? '#06b6d4' : '#0ea5e9',
        size: 140,
        multitouch: false,
        dynamicPage: true,
        restOpacity: 0.5,
      });

      joystickInstance.current
        .on('start', () => {
          setJoystickActive(true);
        })
        .on('move', (evt, data) => {
          if (isEmergencyStop) return;

          const distance = Math.min(data.distance / 105, 1);
          const angle = data.angle.radian;

          // Convert joystick angle to robot linear and angular velocity
          const linear = distance * Math.cos(angle - Math.PI / 2);
          const angular = distance * Math.sin(angle - Math.PI / 2);

          velocityRef.current = { linear, angular };
          setVelocityDisplay({ 
            linear: parseFloat(linear.toFixed(2)), 
            angular: parseFloat(angular.toFixed(2)) 
          });
        })
        .on('end', () => {
          velocityRef.current = { linear: 0, angular: 0 };
          setVelocityDisplay({ linear: 0, angular: 0 });
          setJoystickActive(false);
        });

      // Send velocity commands periodically
      velocitySendIntervalRef.current = setInterval(() => {
        if (websocketService.isConnected() && !isEmergencyStop) {
          websocketService.send('control', {
            action: 'move',
            linear: velocityRef.current.linear.toFixed(2),
            angular: velocityRef.current.angular.toFixed(2),
            mode: mode,
          });
        }
      }, 100); // Send commands 10 times per second

      return () => {
        if (joystickInstance.current) {
          joystickInstance.current.destroy();
        }
        if (velocitySendIntervalRef.current) {
          clearInterval(velocitySendIntervalRef.current);
        }
      };
    } catch (error) {
      console.error('Failed to initialize joystick:', error);
    }
  }, [isEmergencyStop, mode, joystickActive]);

  const sendButtonCommand = (action) => {
    if (isEmergencyStop) return;

    let linear = 0;
    let angular = 0;

    // Map button actions to velocity values
    switch (action) {
      case 'move_forward':
        linear = 0.5;
        break;
      case 'move_backward':
        linear = -0.5;
        break;
      case 'rotate_left':
        angular = 0.5;
        break;
      case 'rotate_right':
        angular = -0.5;
        break;
      default:
        break;
    }

    websocketService.send('control', {
      action,
      linear: linear.toFixed(2),
      angular: angular.toFixed(2),
      mode: mode,
    });
  };

  const handleEmergencyStop = () => {
    const newState = !isEmergencyStop;
    setIsEmergencyStop(newState);
    websocketService.send('control', {
      action: 'emergency_stop',
      value: newState,
    });
  };

  const handlePostureChange = (e) => {
    const newPosture = e.target.value;
    setPosture(newPosture);
    websocketService.send('control', {
      action: 'set_posture',
      value: newPosture,
    });
  };

  const handleModeChange = (e) => {
    const newMode = e.target.value;
    setMode(newMode);
    websocketService.send('control', {
      action: 'set_mode',
      value: newMode,
    });
  };

  const getModeColor = () => {
    return mode === 'Run' ? 'border-orange-400 bg-orange-900/20' : 'border-blue-400 bg-blue-900/20';
  };

  const getVelocityColor = () => {
    const speed = Math.abs(velocityDisplay.linear);
    if (speed < 0.2) return 'text-slate-400';
    if (speed < 0.5) return 'text-cyan-400';
    return 'text-emerald-400';
  };

  return (
    <section className="bg-slate-900 rounded-xl p-4 border border-slate-700 shadow-lg h-96 max-h-96 flex flex-col">
      <h2 className="font-semibold mb-4 text-cyan-300 flex items-center gap-2">
        <span>🎮 Teleoperation Controls</span>
        {isEmergencyStop && (
          <span className="text-xs bg-red-900 text-red-300 px-2 py-1 rounded animate-pulse">
            E-STOP ACTIVE
          </span>
        )}
        <span className={`text-xs px-2 py-1 rounded border ${getModeColor()}`}>
          {mode === 'Run' ? '🏃' : '🚶'} {mode}
        </span>
      </h2>

      {/* Joystick Container with Enhanced Styling */}
      <div
        ref={joystickContainer}
        className={`relative flex-1 rounded-lg border-2 transition-all mb-4 flex flex-col items-center justify-center ${
          joystickActive
            ? 'border-cyan-400 bg-gradient-to-b from-slate-800 to-cyan-900/20 shadow-lg shadow-cyan-500/20'
            : 'border-slate-600 bg-gradient-to-b from-slate-800 to-slate-700'
        }`}
        style={{ minHeight: '220px', touchAction: 'none' }}
      >
        {/* Direction Guide */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="relative w-32 h-32 rounded-full border border-slate-600/30">
            <div className="absolute inset-0 flex items-start justify-center pt-1">
              <span className="text-slate-500 text-sm">↑</span>
            </div>
            <div className="absolute inset-0 flex items-center justify-end pr-1">
              <span className="text-slate-500 text-sm">→</span>
            </div>
            <div className="absolute inset-0 flex items-end justify-center pb-1">
              <span className="text-slate-500 text-sm">↓</span>
            </div>
            <div className="absolute inset-0 flex items-center justify-start pl-1">
              <span className="text-slate-500 text-sm">←</span>
            </div>
          </div>
        </div>

        {/* Velocity Display */}
        <div className="absolute top-3 left-3 right-3 flex justify-between items-center pointer-events-none">
          <div className="text-xs text-slate-400">
            <p className="font-mono">
              Linear: <span className={`font-bold ${getVelocityColor()}`}>{velocityDisplay.linear.toFixed(2)}</span>
            </p>
          </div>
          <div className="text-xs text-slate-400">
            <p className="font-mono">
              Angular: <span className={`font-bold ${getVelocityColor()}`}>{velocityDisplay.angular.toFixed(2)}</span>
            </p>
          </div>
        </div>

        {/* Status Message */}
        <div className="absolute bottom-3 text-center pointer-events-none">
          {joystickActive ? (
            <p className="text-xs text-cyan-400 font-semibold animate-pulse">
              ✓ Controlling robot
            </p>
          ) : (
            <div className="text-center text-slate-400">
              <p className="text-sm font-medium">Drag to control</p>
              <p className="text-xs text-slate-500">Move • Rotate</p>
            </div>
          )}
        </div>
      </div>

      {/* Quick Button Controls with Enhanced Styling */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <button
          onClick={() => sendButtonCommand('move_forward')}
          disabled={isEmergencyStop}
          className="bg-gradient-to-b from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed px-2 py-3 rounded-lg text-sm font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-emerald-500/50 disabled:shadow-none"
          title="Move Forward"
        >
          ⬆️ FWD
        </button>
        <button
          onClick={() => sendButtonCommand('rotate_left')}
          disabled={isEmergencyStop}
          className="bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed px-2 py-3 rounded-lg text-sm font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-blue-500/50 disabled:shadow-none"
          title="Rotate Left"
        >
          ⬅️ LEFT
        </button>
        <button
          onClick={() => sendButtonCommand('rotate_right')}
          disabled={isEmergencyStop}
          className="bg-gradient-to-b from-blue-500 to-blue-600 hover:from-blue-400 hover:to-blue-500 disabled:from-slate-700 disabled:to-slate-800 disabled:cursor-not-allowed px-2 py-3 rounded-lg text-sm font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-blue-500/50 disabled:shadow-none"
          title="Rotate Right"
        >
          ➡️ RIGHT
        </button>
        <button
          onClick={() => sendButtonCommand('move_backward')}
          disabled={isEmergencyStop}
          className="bg-gradient-to-b from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 disabled:from-slate-800 disabled:to-slate-800 disabled:cursor-not-allowed px-2 py-3 rounded-lg text-sm font-bold transition-all transform hover:scale-105 active:scale-95 shadow-lg hover:shadow-slate-500/50 disabled:shadow-none"
          title="Move Backward"
        >
          ⬇️ BWD
        </button>
      </div>

      {/* Mode Selection */}
      <div className="mb-4">
        <label className="text-sm text-slate-300 block mb-2 font-semibold">⚡ Movement Mode</label>
        <select
          value={mode}
          onChange={handleModeChange}
          disabled={isEmergencyStop}
          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 disabled:bg-slate-700 disabled:cursor-not-allowed transition-all"
        >
          <option value="Walk">🚶 Walk</option>
          <option value="Run">🏃 Run</option>
        </select>
      </div>

      {/* Posture Selection */}
      <div className="mb-4">
        <label className="text-sm text-slate-300 block mb-2 font-semibold">🧍 Posture</label>
        <select
          value={posture}
          onChange={handlePostureChange}
          disabled={isEmergencyStop}
          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-400 focus:ring-2 focus:ring-cyan-400/20 disabled:bg-slate-700 disabled:cursor-not-allowed transition-all"
        >
          <option value="Stand">Stand</option>
          <option value="Sit">Sit</option>
          <option value="Kneel">Kneel</option>
          <option value="Wave">Wave</option>
        </select>
      </div>

      {/* Emergency Stop Button */}
      <button
        onClick={handleEmergencyStop}
        className={`w-full font-bold py-3 rounded-lg text-white transition-all transform hover:scale-105 active:scale-95 shadow-lg ${
          isEmergencyStop
            ? 'bg-gradient-to-b from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 animate-pulse shadow-red-500/50'
            : 'bg-gradient-to-b from-red-700 to-red-800 hover:from-red-600 hover:to-red-700 shadow-red-700/50'
        }`}
      >
        {isEmergencyStop ? '🛑 EMERGENCY STOP - ACTIVE' : '🛑 EMERGENCY STOP'}
      </button>

      {/* Status Info */}
      <div className="mt-3 text-xs text-slate-400 border-t border-slate-700 pt-2">
        <p>
          {isEmergencyStop
            ? '⚠️ Emergency stop activated. All commands disabled.'
            : joystickActive
              ? `✅ Joystick active (${mode} mode). Move to control robot.`
              : `📡 Ready for control (${mode} mode)`}
        </p>
      </div>
    </section>
  );
}
