# S4 Robot System - Quick Start Guide

## 🚀 One-Command Startup

The entire backend (API + WebSocket + MQTT + Robot Simulators) now starts with **one command**:

```bash
cd backend
python run_backend.py
```

That's it! Everything is integrated.

## 📋 What You Need

### Prerequisites

1. **Python 3.10+** installed
2. **Mosquitto MQTT broker** running:
   ```bash
   sudo systemctl start mosquitto
   ```
3. **Node.js & npm** for frontend

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

## ▶️ Start the System

### Terminal 1: Backend (API + MQTT + Simulators)

```bash
cd backend
python run_backend.py
```

You'll see:
```
======================================================================
S4 ROBOT BACKEND - FastAPI Server with MQTT & WebSocket
======================================================================
Server: http://0.0.0.0:8001
API Docs: http://0.0.0.0:8001/docs
WebSocket: ws://0.0.0.0:8001/ws
MQTT Broker: localhost:1883

✓ Robot Simulator: ENABLED (1 robot(s))
======================================================================

======================================================================
ROBOT SIMULATOR
======================================================================
Number of robots: 1
MQTT Broker: localhost:1883
Spawn location: 37.7749, -122.4194
Spawn radius: 5.0 km
======================================================================

[✓] All 1 robot(s) started successfully!

Robots are now publishing telemetry to MQTT topics:
  - robot/status/<robot_id>   - Full telemetry
  - robot/battery/<robot_id>  - Battery info
  - robot/health/<robot_id>   - Health metrics
  - robot/pose/<robot_id>     - Position & GPS
  - robot/joints/<robot_id>   - Joint states
  - robot/gps/<robot_id>      - GPS coordinates
======================================================================
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

Open browser to the URL shown (usually `http://localhost:5173`)

### Terminal 3 (Optional): Monitor MQTT

```bash
cd backend
python test_mqtt_listener.py
```

You'll see real-time MQTT messages in color:
- 🔋 **BATTERY** messages (yellow)
- ❤️ **HEALTH** messages (cyan)
- 📊 **STATUS** messages (green)

## 🎮 Control Your Robots

### Via Web UI
- Open frontend in browser
- Use control panel to send commands
- Watch real-time updates

### Via REST API

```bash
# Make robot run
curl -X POST http://localhost:8001/robot/mode \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "mode": "running"}'

# Make robot sit (battery recovers)
curl -X POST http://localhost:8001/robot/mode \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "mode": "sitting"}'

# Get robot state
curl http://localhost:8001/robot/state/robot_01
```

## 🔧 Configuration Options

### Start with Multiple Robots

```bash
python run_backend.py --robots 5
```

### Change Location (New York)

```bash
python run_backend.py --center-lat 40.7128 --center-lon -74.0060 --radius 10
```

### Custom MQTT Broker

```bash
python run_backend.py --mqtt-host mqtt-broker --mqtt-port 1883
```

### Development Mode (Auto-Reload)

```bash
python run_backend.py --reload --log-level debug
```

### Backend Only (No Simulators)

```bash
python run_backend.py --no-simulator
```

## 📊 What Data Flows?

Each robot publishes to MQTT every second:

### Battery Data
```json
{
  "robot_id": "robot_01",
  "battery": 75.5,
  "charging": false,
  "timestamp": "2025-11-29T10:30:45.123456Z"
}
```

### Health Data
```json
{
  "robot_id": "robot_01",
  "health": 85.2,
  "temperature": 42.5,
  "battery": 75.5,
  "status": "moving",
  "timestamp": "2025-11-29T10:30:45.123456Z"
}
```

### Full Status
```json
{
  "robot_id": "robot_01",
  "mode": "walking",
  "status": "moving",
  "battery": 75.5,
  "health": 85.2,
  "temperature": 42.5,
  "pose": {"x": 10.5, "y": 20.3, "theta": 1.57},
  "gps": {"latitude": 37.7749, "longitude": -122.4194},
  "velocity": {"linear": 1.2, "angular": 0.0},
  "timestamp": "2025-11-29T10:30:45.123456Z"
}
```

## ✅ Verify It's Working

### Quick Test (30 seconds)

```bash
cd backend
python verify_battery_health.py
```

Should show:
```
✅ SUCCESS: Battery and health data is flowing correctly!

   Last Battery: 75.5%
   Last Health: 85.2%
   Last Temperature: 42.5°C
```

### Check in Browser

1. Open frontend
2. Press F12 (DevTools)
3. Console should show: `✅ WebSocket connected`
4. Network tab > WS > Messages should show data flowing

### Watch Values Change

1. Send command: Running mode
   - Temperature increases
   - Battery drains faster
   - Health decreases

2. Send command: Sitting mode
   - Temperature decreases
   - Battery drains slower
   - Health recovers

## 🐛 Troubleshooting

### Problem: Port 8001 already in use

```bash
python run_backend.py --port 8002
```

### Problem: Can't connect to MQTT

```bash
# Check mosquitto
sudo systemctl status mosquitto

# Start it
sudo systemctl start mosquitto
```

### Problem: No robots appearing

```bash
# Check simulator is enabled
python run_backend.py --robots 1

# Monitor MQTT
python test_mqtt_listener.py
```

### Problem: Frontend can't connect

1. Check backend is running on port 8001
2. Check WebSocket endpoint: `ws://localhost:8001/ws`
3. Check browser console for errors

## 📚 Documentation

- **[USAGE_GUIDE.md](backend/USAGE_GUIDE.md)** - Complete backend guide
- **[VERIFICATION_SUMMARY.md](VERIFICATION_SUMMARY.md)** - Battery/health verification
- **[BATTERY_HEALTH_VERIFICATION_GUIDE.md](BATTERY_HEALTH_VERIFICATION_GUIDE.md)** - Detailed guide
- **API Docs:** http://localhost:8001/docs (when running)

## 🎯 Common Use Cases

### Scenario 1: Demo/Presentation

```bash
# Terminal 1: Start everything
cd backend && python run_backend.py --robots 3

# Terminal 2: Start frontend
cd frontend && npm run dev

# Open browser, show real-time robot control and monitoring
```

### Scenario 2: Development

```bash
# Auto-reload backend on code changes
python run_backend.py --reload --log-level debug

# In another terminal: Monitor MQTT
python test_mqtt_listener.py
```

### Scenario 3: Testing with Real Robots

```bash
# Disable simulators, use real robots
python run_backend.py --no-simulator --mqtt-host 192.168.1.100
```

### Scenario 4: Load Testing

```bash
# Simulate 50 robots
python run_backend.py --robots 50
```

## 🔗 Architecture

```
User Browser
    ↓
Frontend (React) ← WebSocket → Backend (FastAPI)
                                    ↓
                            MQTT Manager
                                    ↓
                            MQTT Broker
                         ↗      ↓      ↖
                Robot #1   Robot #2   Robot #N
                (Simulators or Real Robots)
```

## ⚡ Performance Notes

- Each robot publishes 6 topics per second
- WebSocket broadcasts to all connected clients
- Database logs telemetry for history
- Typical resource usage:
  - 1 robot: ~50MB RAM
  - 10 robots: ~200MB RAM
  - 50 robots: ~500MB RAM

## 🚦 Status Indicators

### Healthy System
- ✅ Backend logs: "MQTT connection established successfully"
- ✅ Backend logs: "WebSocket connected"
- ✅ MQTT listener: Shows colored messages
- ✅ Browser console: "✅ WebSocket connected"
- ✅ Frontend: Values updating every second

### Problems
- ❌ "Connection refused" → MQTT broker not running
- ❌ "Port already in use" → Change port with `--port`
- ❌ "Database locked" → Close other connections, restart
- ❌ Frontend shows stale data → Check WebSocket connection

## 🎓 Learning Path

1. **Start simple:** `python run_backend.py`
2. **Monitor MQTT:** `python test_mqtt_listener.py`
3. **Explore API:** http://localhost:8001/docs
4. **Control robots:** Use frontend or REST API
5. **Customize:** Add CLI arguments for your needs
6. **Extend:** Modify robot simulator for your use case

## 📞 Need Help?

Check the detailed guides:
- [USAGE_GUIDE.md](backend/USAGE_GUIDE.md)
- [VERIFICATION_SUMMARY.md](VERIFICATION_SUMMARY.md)

---

**Ready to go? Start with:**
```bash
cd backend && python run_backend.py
```
