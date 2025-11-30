# Battery & Health Information Verification Guide

## Summary of Changes

Battery and health information has been integrated into the MQTT backend and is now properly connected to the web frontend. Here's what was implemented:

### Backend Changes

1. **Robot Simulator** ([backend/app/robot_simulator.py](backend/app/robot_simulator.py))
   - Added `health` (0-100%) and `temperature` (°C) tracking
   - Health calculation based on:
     - Battery level (30% weight)
     - Temperature (40% weight) - optimal < 45°C
     - General wear and tear (30% weight)
   - New MQTT topics published:
     - `robot/battery/{robot_id}` - Battery level and charging status
     - `robot/health/{robot_id}` - Health %, temperature, battery, status
     - `robot/status/{robot_id}` - Includes health and temperature in telemetry

2. **MQTT Listener** ([backend/test_mqtt_listener.py](backend/test_mqtt_listener.py))
   - Added subscriptions to `robot/battery/#` and `robot/health/#`
   - Color-coded display: Battery (yellow), Health (cyan)
   - Status indicators: [GOOD], [FAIR], [POOR] for health
   - Temperature warnings: [NORMAL], [WARM], [HIGH]

3. **Backend WebSocket Bridge** ([backend/app/main.py](backend/app/main.py))
   - Added handlers for `robot/battery/*` and `robot/health/*` topics
   - Forwards MQTT messages to WebSocket clients

### Frontend Integration

The frontend already has components ready to display health data:

- **HealthMonitoringPanel** ([frontend/src/components/HealthMonitoringPanel.jsx](frontend/src/components/HealthMonitoringPanel.jsx))
  - Listens to `health_telemetry` event from WebSocket
  - Displays battery trends, temperature graphs, health score

- **StatusPanel** ([frontend/src/components/StatusPanel.jsx](frontend/src/components/StatusPanel.jsx))
  - Listens to `telemetry_update` event
  - Shows battery and temperature status

## How to Verify the Connection

### Step 1: Start the Backend

```bash
cd /home/sruthi/Documents/workspace/hackathon/backend

# Start the FastAPI backend with robot simulators
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The backend will automatically:
- Start the MQTT manager
- Launch robot simulators (if enabled in config)
- Begin publishing battery and health data every second

### Step 2: Start the MQTT Listener (Optional but Recommended)

In a separate terminal:

```bash
cd /home/sruthi/Documents/workspace/hackathon/backend

# Listen to all MQTT messages including battery and health
python test_mqtt_listener.py
```

You should see colored output showing:
- **[BATTERY]** messages in yellow with charging indicator
- **[HEALTH]** messages in cyan with health status (GOOD/FAIR/POOR)
- Temperature warnings (NORMAL/WARM/HIGH)

### Step 3: Start the Frontend

```bash
cd /home/sruthi/Documents/workspace/hackathon/frontend

# Start the Vite dev server
npm run dev
```

Open your browser to the URL shown (usually `http://localhost:5173`)

### Step 4: Verify Data Flow

#### A. Check MQTT Topics (using MQTT listener)

You should see these topics publishing every second:
```
robot/status/robot_01     - Full telemetry (includes battery, health, temperature)
robot/battery/robot_01    - Battery-specific data
robot/health/robot_01     - Health metrics
robot/pose/robot_01       - Position/GPS data
robot/joints/robot_01     - Joint states
robot/gps/robot_01        - GPS coordinates
```

#### B. Check Backend Logs

Look for:
```
INFO - MQTT connection established successfully
INFO - Subscribing to 7 topic patterns...
INFO - Started robot 'robot_01' at GPS (...)
INFO - Robots are now publishing telemetry to MQTT topics
```

#### C. Check WebSocket Connection

In the backend logs, when the frontend connects:
```
INFO - WebSocket connected. Total connections: 1
```

#### D. Check Browser Console

Open browser DevTools (F12) > Console:
```
✅ WebSocket connected
```

Network tab should show:
- WebSocket connection to `ws://localhost:8001/ws` (Status: 101 Switching Protocols)
- Messages flowing in/out

#### E. Verify Frontend Display

**StatusPanel** should show:
- Battery level with progress bar
- Temperature reading with color coding
- Real-time updates every second

**HealthMonitoringPanel** (if visible) should show:
- Battery trend graph
- Temperature monitoring chart
- Health score percentage
- System resources

### Step 5: Test Real-Time Updates

1. **Send a command to change robot mode:**

```bash
# Via WebSocket (in browser console):
websocketService.sendMode('robot_01', 'running')

# Or via REST API:
curl -X POST http://localhost:8001/robot/mode \
  -H "Content-Type: application/json" \
  -d '{"robot_id": "robot_01", "mode": "running"}'
```

2. **Watch the values change:**
   - Battery should drain faster
   - Temperature should increase
   - Health score should decrease over time
   - Frontend should update in real-time

3. **Test sitting mode (recovery):**

```bash
websocketService.sendMode('robot_01', 'sitting')
```

   - Temperature should decrease
   - Health should slowly recover
   - Battery drain should slow down

## Troubleshooting

### Problem: Frontend not receiving battery/health updates

**Check:**
1. Backend logs show MQTT messages are being published
2. WebSocket is connected (check browser console)
3. Network tab shows WebSocket messages

**Solution:**
- Restart the backend to ensure handlers are registered
- Clear browser cache and reload

### Problem: MQTT listener shows messages but frontend doesn't

**Check:**
1. WebSocket connection in backend logs
2. Browser console for JavaScript errors
3. Network tab for WebSocket frame data

**Solution:**
- The WebSocket service expects specific message types
- Check that `main.py` handlers are registered (lines 263-264)

### Problem: Health/Battery values don't make sense

**Check:**
- Robot simulator initialization (random starting values)
- Mode affects drain/recovery rates
- Temperature affects health calculation

**Solution:**
- This is a simulator - values are calculated based on activity
- Let it run for 30-60 seconds to see realistic trends

## Expected Data Flow

```
Robot Simulator (Python)
    ↓ publishes MQTT
MQTT Broker (Mosquitto)
    ↓ subscribes
MQTT Manager (backend/app/mqtt_manager.py)
    ↓ handlers
FastAPI Handlers (backend/app/main.py)
    ↓ broadcasts
WebSocket Manager (backend/app/websocket_server.py)
    ↓ sends JSON
WebSocket (ws://localhost:8001/ws)
    ↓ receives
Frontend WebSocketService (frontend/src/services/websocketService.js)
    ↓ emits events ('battery', 'health', 'telemetry')
React Components
    ↓ displays
User Interface
```

## MQTT Message Formats

### Battery Message (`robot/battery/{robot_id}`)
```json
{
  "robot_id": "robot_01",
  "battery": 75.5,
  "charging": false,
  "timestamp": "2025-11-29T10:30:45.123456Z"
}
```

### Health Message (`robot/health/{robot_id}`)
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

### Status Message (`robot/status/{robot_id}`)
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

## WebSocket Message Format

When forwarded to frontend via WebSocket:

```json
{
  "type": "battery",
  "robot_id": "robot_01",
  "data": {
    "battery": 75.5,
    "charging": false,
    "timestamp": "2025-11-29T10:30:45.123456Z"
  }
}
```

```json
{
  "type": "health",
  "robot_id": "robot_01",
  "data": {
    "health": 85.2,
    "temperature": 42.5,
    "battery": 75.5,
    "status": "moving",
    "timestamp": "2025-11-29T10:30:45.123456Z"
  }
}
```

## Quick Verification Commands

```bash
# 1. Check if MQTT broker is running
mosquitto -h

# 2. Subscribe to all robot topics
mosquitto_sub -t 'robot/#' -v

# 3. Check backend health
curl http://localhost:8001/health

# 4. Get robot state
curl http://localhost:8001/robot/state/robot_01

# 5. Test WebSocket (using websocat if installed)
websocat ws://localhost:8001/ws
```

## Success Indicators

✅ MQTT listener shows BATTERY and HEALTH messages
✅ Backend logs show "WebSocket connected"
✅ Browser console shows "WebSocket connected"
✅ Frontend displays updating battery percentage
✅ Frontend displays updating temperature
✅ Frontend displays updating health score
✅ Values change when robot mode changes
✅ Temperature increases during running mode
✅ Battery drains during movement
✅ Health recovers during sitting mode

## Configuration Files

- **Backend Config**: [backend/app/config.py](backend/app/config.py)
- **MQTT Settings**: Check `MQTT_HOST`, `MQTT_PORT` in `.env` or defaults
- **Frontend WebSocket URL**: Auto-detected in [frontend/src/services/websocketService.js](frontend/src/services/websocketService.js)

## Next Steps

1. **Monitor for 1-2 minutes** to see realistic value changes
2. **Test different robot modes** (sit, stand, walk, run)
3. **Check database** if telemetry logging is enabled
4. **Add more robots** by changing `num_simulated_robots` in config
5. **Customize health calculations** in [robot_simulator.py:208-243](backend/app/robot_simulator.py#L208-L243)
