# S4 Robot Backend - Complete Usage Guide

## Overview

The S4 Robot Backend is now a **unified application** that combines:
- ✅ FastAPI REST API
- ✅ WebSocket Server (MQTT bridge)
- ✅ Robot Simulator(s)
- ✅ MQTT Client
- ✅ Database (SQLite)

**No need to run multiple commands!** Everything starts with one script.

## Quick Start

### Option 1: Simple Start (Recommended)

```bash
cd /home/sruthi/Documents/workspace/hackathon/backend

# Start with default settings (1 robot simulator)
python run_backend.py
```

This starts:
- FastAPI server on `http://0.0.0.0:8001`
- WebSocket on `ws://0.0.0.0:8001/ws`
- 1 robot simulator publishing to MQTT
- MQTT client connected to `localhost:1883`

### Option 2: Custom Configuration

```bash
# Start with 5 robots
python run_backend.py --robots 5

# Configure MQTT broker
python run_backend.py --mqtt-host mqtt-broker --mqtt-port 1883

# Custom GPS location (New York City)
python run_backend.py --center-lat 40.7128 --center-lon -74.0060 --radius 10

# Combine options
python run_backend.py --robots 3 --mqtt-host localhost --port 8001
```

### Option 3: Backend Only (No Simulators)

```bash
# If you have real robots or external simulators
python run_backend.py --no-simulator
```

## Command Line Arguments

### Robot Simulator
- `--robots N` - Number of robots to simulate (default: 1)
- `--no-simulator` - Disable robot simulator entirely

### MQTT Configuration
- `--mqtt-host HOST` - MQTT broker hostname (default: localhost)
- `--mqtt-port PORT` - MQTT broker port (default: 1883)

### GPS Spawn Settings
- `--center-lat LAT` - Center latitude for spawning (default: 37.7749)
- `--center-lon LON` - Center longitude for spawning (default: -122.4194)
- `--radius KM` - Spawn radius in kilometers (default: 5.0)

### Server Settings
- `--host HOST` - Server host (default: 0.0.0.0)
- `--port PORT` - Server port (default: 8001)
- `--reload` - Enable auto-reload for development
- `--log-level LEVEL` - Set log level (debug, info, warning, error, critical)

## What Gets Started?

When you run `python run_backend.py`, the following happens automatically:

### 1. Database Initialization
```
✓ SQLite database created at ./data/robot_telemetry.db
✓ Tables: robot_path_log, battery_history, error_log, telemetry_log
```

### 2. MQTT Client
```
✓ Connected to MQTT broker at localhost:1883
✓ Subscribed to topics:
  - robot/status/*
  - robot/pose/*
  - robot/battery/*
  - robot/health/*
  - robot/joints/*
  - robot/gps/*
  - robot/errors/*
```

### 3. Robot Simulators (if enabled)
```
✓ Robot simulators started:
  - robot_01 at GPS (37.774900, -122.419400)
  - robot_02 at GPS (37.780123, -122.415678)
  - ... (configurable via --robots)

✓ Each robot publishes to MQTT every 1 second:
  - robot/status/{robot_id}   - Full telemetry
  - robot/battery/{robot_id}  - Battery info
  - robot/health/{robot_id}   - Health metrics
  - robot/pose/{robot_id}     - Position & GPS
  - robot/joints/{robot_id}   - Joint states
  - robot/gps/{robot_id}      - GPS coordinates
```

### 4. WebSocket Server
```
✓ WebSocket endpoint: ws://localhost:8001/ws
✓ Bridges MQTT messages to frontend
✓ Accepts commands from frontend
```

### 5. FastAPI REST API
```
✓ Server: http://localhost:8001
✓ API Docs: http://localhost:8001/docs
✓ Endpoints available for robot control
```

## Full System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      run_backend.py                              │
│  (Single unified startup script)                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
    ┌──────────────────────────────────────────────────────────┐
    │              FastAPI Application (main.py)                │
    └──────────────────────────────────────────────────────────┘
         ↓              ↓               ↓                ↓
    ┌────────┐    ┌──────────┐    ┌─────────┐     ┌──────────┐
    │  REST  │    │WebSocket │    │  MQTT   │     │ Database │
    │  API   │    │ Server   │    │ Client  │     │ (SQLite) │
    └────────┘    └──────────┘    └─────────┘     └──────────┘
         ↓              ↓               ↑                ↑
         └──────────────┴───────────────┘                │
                        ↓                                 │
                ┌──────────────┐                          │
                │ MQTT Broker  │                          │
                │ (Mosquitto)  │                          │
                └──────────────┘                          │
                        ↑                                 │
         ┌──────────────┴───────────────┐                │
         ↓              ↓               ↓                 ↓
    ┌─────────┐   ┌─────────┐    ┌─────────┐      ┌──────────┐
    │Robot #1 │   │Robot #2 │    │Robot #N │      │Telemetry │
    │Simulator│   │Simulator│    │Simulator│      │Processor │
    └─────────┘   └─────────┘    └─────────┘      └──────────┘
```

## Environment Variables

Create a `.env` file in the backend directory:

```bash
# MQTT Settings
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Robot Simulator
ENABLE_ROBOT_SIMULATOR=true
NUM_SIMULATED_ROBOTS=1
SIMULATOR_CENTER_LAT=37.7749
SIMULATOR_CENTER_LON=-122.4194
SIMULATOR_SPAWN_RADIUS=5.0

# Database
DATABASE_PATH=./data/robot_telemetry.db

# Dummy Publisher (legacy)
DUMMY_PUBLISH_ENABLED=false
```

**Note:** CLI arguments override `.env` settings.

## Examples

### Example 1: Development with Auto-Reload

```bash
python run_backend.py --reload --log-level debug
```

### Example 2: Production with Multiple Robots

```bash
python run_backend.py --robots 10 --host 0.0.0.0 --port 8001
```

### Example 3: Custom Location (London)

```bash
python run_backend.py \
  --robots 5 \
  --center-lat 51.5074 \
  --center-lon -0.1278 \
  --radius 20
```

### Example 4: Backend Only (Real Robots)

```bash
# Use when you have real robots or external simulators
python run_backend.py --no-simulator --mqtt-host 192.168.1.100
```

## Monitoring

### Check Logs

The application logs to console. You'll see:

```
INFO - Database initialized
INFO - MQTT connection established successfully
INFO - Subscribing to 7 topic patterns...
INFO - Started robot 'robot_01' at GPS (37.774900, -122.419400)...
INFO - [✓] All 1 robot simulator(s) started successfully!
INFO - Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Monitor MQTT Messages

In another terminal:

```bash
# Watch all MQTT messages
python test_mqtt_listener.py

# Or use mosquitto_sub
mosquitto_sub -t 'robot/#' -v
```

### Check Health

```bash
# API health check
curl http://localhost:8001/health

# MQTT health check
curl http://localhost:8001/health/mqtt
```

## API Endpoints

### Health & Status
- `GET /health` - Overall health
- `GET /health/mqtt` - MQTT connection status
- `GET /robot/state/{robot_id}` - Get robot state
- `GET /robot/states` - Get all robot states

### Robot Control
- `POST /robot/mode` - Switch mode (sitting, standing, walking, running)
- `POST /robot/cmd_vel` - Send velocity command
- `POST /robot/teleop` - Send teleop command
- `POST /robot/emergency_stop` - Emergency stop

### Telemetry History
- `GET /robot/{robot_id}/path` - Get path history
- `GET /robot/{robot_id}/battery` - Get battery history
- `GET /robot/{robot_id}/errors` - Get error logs

### Full API Documentation
- `http://localhost:8001/docs` - Interactive Swagger UI
- `http://localhost:8001/redoc` - ReDoc documentation

## Control via REST API

### Change Robot Mode

```bash
# Make robot run
curl -X POST http://localhost:8001/robot/mode \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "mode": "running"}'

# Make robot sit
curl -X POST http://localhost:8001/robot/mode \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "mode": "sitting"}'
```

### Send Velocity Command

```bash
curl -X POST http://localhost:8001/robot/cmd_vel \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "linear": 1.0, "angular": 0.5}'
```

### Get Robot State

```bash
curl http://localhost:8001/robot/state/robot_01
```

## Control via WebSocket

See [frontend/src/services/websocketService.js](../frontend/src/services/websocketService.js) for examples.

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8001/ws');

// Send mode change
ws.send(JSON.stringify({
  type: 'mode',
  robot_id: 'robot_01',
  mode: 'running'
}));

// Send velocity command
ws.send(JSON.stringify({
  type: 'cmd_vel',
  robot_id: 'robot_01',
  linear: 1.0,
  angular: 0.0
}));

// Receive updates
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
  // data.type can be: 'battery', 'health', 'telemetry', 'pose', etc.
};
```

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.

The shutdown process will:
1. Stop all robot simulators
2. Disconnect MQTT client
3. Close database connections
4. Shutdown FastAPI server

## Troubleshooting

### Port Already in Use

```bash
# Change the port
python run_backend.py --port 8002
```

### MQTT Connection Failed

```bash
# Check if mosquitto is running
sudo systemctl status mosquitto

# Start mosquitto
sudo systemctl start mosquitto

# Or use different broker
python run_backend.py --mqtt-host mqtt.example.com
```

### Database Locked

```bash
# Remove the database file and restart
rm data/robot_telemetry.db
python run_backend.py
```

### No Robots Appearing

```bash
# Check robot simulator is enabled
python run_backend.py --robots 1

# Check MQTT listener
python test_mqtt_listener.py
```

## Migration from Old Setup

### Old Way (Multiple Commands)

```bash
# Terminal 1: Start backend
python -m uvicorn app.main:app --port 8001

# Terminal 2: Start robot simulator
python run_robot_simulator.py --robots 5
```

### New Way (Single Command)

```bash
# One command does it all!
python run_backend.py --robots 5
```

## Development Tips

### Auto-Reload During Development

```bash
python run_backend.py --reload --log-level debug
```

### Test Without Simulators

```bash
python run_backend.py --no-simulator
```

### Combine with MQTT Listener

```bash
# Terminal 1: Backend
python run_backend.py --robots 3

# Terminal 2: Monitor MQTT
python test_mqtt_listener.py

# Terminal 3: Frontend
cd ../frontend && npm run dev
```

## Next Steps

1. **Start the backend:** `python run_backend.py`
2. **Start the frontend:** `cd ../frontend && npm run dev`
3. **Open browser:** Navigate to frontend URL (usually `http://localhost:5173`)
4. **Control robots:** Use the web UI or API endpoints

For verification that battery and health data is working:
- See [VERIFICATION_SUMMARY.md](VERIFICATION_SUMMARY.md)
- Run `python verify_battery_health.py`
