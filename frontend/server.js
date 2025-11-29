import http from 'http';
import { WebSocketServer } from 'ws';

const server = http.createServer();
const wss = new WebSocketServer({ server });

// Simulation state
let robotState = {
  lat: 37.7749,
  lon: -122.4194,
  heading: 0,
  battery: 82,
  temperature: 43,
  signalStrength: 5,
  systemStatus: 'OK',
  cpuUsage: 35,
  memoryUsage: 48,
  fpsCount: 30,
  jointErrors: 0,
  mode: 'IDLE',
  emergencyStop: false,
};

let updateInterval;
let clientConnected = false;

wss.on('connection', (ws) => {
  clientConnected = true;
  console.log('✅ Client connected');

  // Send initial state
  ws.send(
    JSON.stringify({
      type: 'connection',
      status: 'connected',
    })
  );

  // Handle incoming messages
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data);
      console.log('📨 Received:', message.type, message);

      if (message.type === 'control') {
        handleControl(message, ws);
      }
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  });

  ws.on('close', () => {
    clientConnected = false;
    console.log('🔌 Client disconnected');
    if (updateInterval) {
      clearInterval(updateInterval);
    }
  });

  ws.on('error', (error) => {
    console.error('❌ WebSocket error:', error);
  });

  // Start sending telemetry updates if not already started
  if (!updateInterval) {
    updateInterval = setInterval(() => {
      if (clientConnected && ws.readyState === WebSocket.OPEN) {
        sendTelemetryUpdate(ws);
      }
    }, 150); // ~6-7 updates per second
  }
});

function handleControl(message, ws) {
  const { action, value, linear, angular } = message;

  if (action === 'emergency_stop') {
    robotState.emergencyStop = value;
    robotState.mode = value ? 'STOPPED' : 'IDLE';
    console.log(
      `🛑 Emergency stop: ${value ? 'ACTIVATED' : 'DEACTIVATED'}`
    );

    ws.send(
      JSON.stringify({
        type: 'log_event',
        level: 'WARN',
        message: `Emergency stop ${value ? 'activated' : 'deactivated'}`,
      })
    );
  } else if (action === 'move' && !robotState.emergencyStop) {
    robotState.mode = 'TELEOP';
    // Simulate robot movement
    if (linear !== 0) {
      robotState.lat += (linear * Math.sin(robotState.heading * (Math.PI / 180))) * 0.00005;
      robotState.lon += (linear * Math.cos(robotState.heading * (Math.PI / 180))) * 0.00005;
    }
    if (angular !== 0) {
      robotState.heading += angular * 5;
      robotState.heading = (robotState.heading + 360) % 360;
    }

    console.log(
      `🎮 Move: linear=${linear.toFixed(2)}, angular=${angular.toFixed(2)}`
    );
  } else if (action === 'set_posture') {
    console.log(`🧍 Posture changed to: ${value}`);
    ws.send(
      JSON.stringify({
        type: 'log_event',
        level: 'INFO',
        message: `Robot posture changed to: ${value}`,
      })
    );
  } else if (action === 'move_forward') {
    robotState.lat += 0.0002;
    console.log('⬆️ Moving forward');
  } else if (action === 'move_backward') {
    robotState.lat -= 0.0002;
    console.log('⬇️ Moving backward');
  } else if (action === 'rotate_left') {
    robotState.heading += 15;
    console.log('⬅️ Rotating left');
  } else if (action === 'rotate_right') {
    robotState.heading -= 15;
    console.log('➡️ Rotating right');
  }
}

function sendTelemetryUpdate(ws) {
  // Simulate dynamic telemetry changes
  robotState.temperature = Math.max(
    35,
    robotState.temperature + (Math.random() - 0.5) * 2
  );
  robotState.battery = Math.max(
    0,
    robotState.battery + (Math.random() - 0.495) * 0.5
  );
  robotState.cpuUsage = Math.max(
    0,
    Math.min(100, robotState.cpuUsage + (Math.random() - 0.5) * 3)
  );
  robotState.memoryUsage = Math.max(
    0,
    Math.min(100, robotState.memoryUsage + (Math.random() - 0.5) * 2)
  );
  robotState.signalStrength = Math.floor(Math.random() * 5) + 1;

  // Randomly trigger obstacles or warnings
  if (Math.random() < 0.02) {
    ws.send(
      JSON.stringify({
        type: 'obstacle_detected',
        lat: robotState.lat + (Math.random() - 0.5) * 0.001,
        lon: robotState.lon + (Math.random() - 0.5) * 0.001,
        radius: Math.random() * 2 + 0.5,
      })
    );
  }

  // Send pose update
  ws.send(
    JSON.stringify({
      type: 'pose_update',
      lat: robotState.lat,
      lon: robotState.lon,
      heading: robotState.heading,
    })
  );

  // Send telemetry update
  ws.send(
    JSON.stringify({
      type: 'telemetry_update',
      battery: robotState.battery.toFixed(1),
      temperature: robotState.temperature.toFixed(1),
      signalStrength: robotState.signalStrength,
      systemStatus: robotState.battery < 20 ? 'ERROR' : 'OK',
      cpuUsage: robotState.cpuUsage.toFixed(0),
      memoryUsage: robotState.memoryUsage.toFixed(0),
      fpsCount: robotState.fpsCount,
      jointErrors: robotState.jointErrors,
    })
  );

  // Randomly send mode updates
  if (Math.random() < 0.05) {
    ws.send(
      JSON.stringify({
        type: 'mode_update',
        mode: robotState.mode,
      })
    );
  }
}

const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log(`🚀 WebSocket server running on ws://localhost:${PORT}`);
  console.log('Waiting for client connections...');
});
