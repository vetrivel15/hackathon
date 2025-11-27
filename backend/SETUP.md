# 🚀 Python Backend Setup Guide

## Quick Start (3 steps)

### 1. Activate Virtual Environment
```bash
cd /Users/vetrivel/repo/hackathon/backend
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Server
```bash
python app.py
```

Or use the convenience script:
```bash
./run.sh
```

---

## What's Included

✅ **Flask Web Framework** - HTTP server and REST API endpoints  
✅ **Flask-SocketIO** - WebSocket communication with frontend  
✅ **Flask-CORS** - Cross-origin request handling  
✅ **Python-dotenv** - Environment variable management  
✅ **Robot State Management** - Centralized state for robot telemetry and control  
✅ **Telemetry Broadcasting** - 6-7 Hz update rate matching frontend requirements  

---

## Server Details

**HTTP Server:**
- Host: 0.0.0.0
- Port: 5000
- URL: http://localhost:5000

**WebSocket Server:**
- Endpoint: ws://localhost:5000/socket.io
- Connected Clients: Tracked and managed
- Update Rate: 6-7 Hz (150ms intervals)

**REST API Endpoints:**
- `GET /api/health` - Server health check
- `GET /api/robot/state` - Current robot state
- `POST /api/robot/reset` - Reset robot to initial state
- `GET /api/logs` - System logs

---

## Features Implemented

### WebSocket Message Handling
- ✅ Joystick control (`move` action with linear/angular velocity)
- ✅ Quick action buttons (forward, backward, rotate left/right)
- ✅ Posture changes (Stand, Sit, Kneel, Wave)
- ✅ Emergency stop activation/deactivation
- ✅ Ping/pong for connection health checks

### Real-time Telemetry
- ✅ Position updates (latitude, longitude, heading)
- ✅ Battery level simulation (decreases during teleop, slower during idle)
- ✅ Temperature fluctuation
- ✅ CPU/Memory usage variations
- ✅ Signal strength indicator
- ✅ System status (OK, WARNING, ERROR)
- ✅ FPS counter
- ✅ Joint error tracking

### Robot Kinematics
- ✅ Position updates based on linear velocity
- ✅ Heading rotation based on angular velocity
- ✅ Realistic movement simulation

---

## Frontend Integration

### Update Frontend WebSocket URL

Edit `/Users/vetrivel/repo/hackathon/frontEnd/src/services/websocketService.js`

**Original (Node.js mock server):**
```javascript
constructor(url = 'ws://localhost:8080') {
```

**Updated (Python backend):**
```javascript
constructor(url = 'ws://localhost:5000/socket.io') {
```

### Run Both Together

**Terminal 1 - Start Backend:**
```bash
cd /Users/vetrivel/repo/hackathon/backend
source venv/bin/activate
python app.py
```

**Terminal 2 - Start Frontend:**
```bash
cd /Users/vetrivel/repo/hackathon/frontEnd
npm run dev
```

Then open: http://localhost:5173

---

## Testing the Backend

### Test API Endpoints

```bash
# Health check
curl http://localhost:5000/api/health

# Get robot state
curl http://localhost:5000/api/robot/state

# Reset robot
curl -X POST http://localhost:5000/api/robot/reset
```

### Test WebSocket with Python

```python
import socketio
import time

sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('✅ Connected to backend')
    
@sio.on('pose_update')
def on_pose_update(data):
    print(f'📍 Position: lat={data["lat"]:.4f}, lon={data["lon"]:.4f}, heading={data["heading"]:.1f}°')

@sio.on('telemetry_update')
def on_telemetry(data):
    print(f'🔋 Battery: {data["battery"]:.1f}% | 🌡️ Temp: {data["temperature"]:.1f}°C')

try:
    sio.connect('http://localhost:5000')
    sio.wait()
except Exception as e:
    print(f'Connection error: {e}')
```

---

## Environment Configuration

Edit `.env` to customize:

```env
FLASK_ENV=development          # development or production
FLASK_DEBUG=True               # Enable debug mode
SECRET_KEY=...                 # Change in production
PORT=5000                      # Server port
HOST=0.0.0.0                   # Server host
ROBOT_NAME=HUM-01              # Robot identifier
INITIAL_LATITUDE=37.7749       # Starting latitude
INITIAL_LONGITUDE=-122.4194    # Starting longitude
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'flask'"
**Solution:** Activate virtual environment
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: "Address already in use" (port 5000)
**Solution:** Kill existing process
```bash
lsof -i :5000
kill -9 <PID>
```

### Issue: WebSocket connection fails in frontend
**Solution:** 
1. Verify backend is running: `python app.py`
2. Check firewall allows port 5000
3. Update frontend WebSocket URL to `ws://localhost:5000/socket.io`
4. Restart frontend dev server

### Issue: Slow telemetry updates
**Solution:** Reduce update interval in `broadcast_telemetry()` from 0.15s

---

## Project Structure

```
backend/
├── app.py              # Main Flask app + SocketIO server
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── .gitignore         # Git ignore rules
├── run.sh             # Startup script
├── SETUP.md           # This file
└── README.md          # Full documentation
```

---

## Next Steps

1. ✅ Backend is ready to run
2. 📝 Update frontend WebSocket URL if needed
3. 🚀 Start backend: `python app.py`
4. 🎮 Start frontend: `npm run dev`
5. 🧪 Test controls in dashboard

---

**Happy Robot Controlling! 🤖**
