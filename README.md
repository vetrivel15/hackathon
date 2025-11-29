# S4 Robot Control System

A complete humanoid robot control system with MQTT backend and real-time React dashboard for monitoring and teleoperation.

## Project Structure

```
hackathon/
├── backend/           # MQTT Backend (Python/FastAPI)
│   ├── app/          # Main application code
│   ├── mosquitto/    # MQTT broker configuration
│   ├── data/         # Database and logs
│   ├── venv/         # Python virtual environment
│   ├── requirements.txt
│   ├── docker-compose.yml
│   ├── .env          # Environment configuration
│   └── start_application.sh
│
└── frontend/         # React Application (Vite)
    ├── src/         # React source code
    ├── public/      # Static assets
    ├── package.json
    └── vite.config.js
```

## Quick Start

### Backend (MQTT + FastAPI)

```bash
cd backend
./start_application.sh
```

The backend will be available at:
- **API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **WebSocket**: ws://localhost:8001/ws
- **MQTT Broker**: localhost:1884 (changed from 1883 to avoid port conflicts)
- **MQTT WebSocket**: localhost:9001

### Frontend (React Dashboard)

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at: http://localhost:5173

### Running Both Services

1. Terminal 1: `cd backend && ./start_application.sh`
2. Terminal 2: `cd frontend && npm run dev`

## System Configuration

### Port Configuration
- **MQTT Broker**: Port 1884 (host) → 1883 (container)
- **API/WebSocket**: Port 8001
- **Frontend**: Port 5173 (dev server)

**Note**: The MQTT port was changed from 1883 to 1884 to avoid conflicts with system-level mosquitto services.

### Environment Variables
All configuration is in [backend/.env](backend/.env):
```bash
MQTT_HOST=localhost
MQTT_PORT=1884
API_PORT=8001
NUM_SIMULATED_ROBOTS=1
```

## Features

### Backend
- ✅ MQTT broker (Mosquitto) with WebSocket support
- ✅ FastAPI REST API with WebSocket
- ✅ Robot simulator publishing telemetry
- ✅ SQLite database for persistence
- ✅ Real-time robot status, pose, GPS, and joint data
- ✅ Docker containerized MQTT broker

### Frontend
- ✅ Real-time OpenStreetMap with robot tracking
- ✅ Live telemetry (battery, temperature, CPU, memory)
- ✅ Virtual joystick for teleoperation
- ✅ Emergency stop functionality
- ✅ Posture control (Stand, Sit, Kneel, Wave)
- ✅ Real-time event logs
- ✅ Responsive 2x2 grid layout

## Testing

### Test MQTT Connection
```bash
cd backend
source venv/bin/activate
python test_mqtt_listener.py
```

### Test Robot Commands
```bash
cd backend
source venv/bin/activate
python test_robot_controller.py
```

### Test API
```bash
cd backend
source venv/bin/activate
python test_api.py
```

## Development

See detailed documentation:
- [Frontend README](frontend/README.md) - Dashboard features and WebSocket protocol
- [Backend Setup](backend/) - MQTT topics and API endpoints

## Troubleshooting

### MQTT Connection Issues
- Ensure MQTT broker is running: `docker ps` (should show mqtt-broker container)
- Check port 1884 is available: `netstat -an | grep 1884`
- Verify .env file has `MQTT_PORT=1884`

### Frontend Not Connecting
- Check WebSocket URL in `frontend/src/services/websocketService.js`
- Ensure backend is running on port 8001
- Check browser console for connection errors

### Port Conflicts
If you see "port already in use":
- MQTT: Stop system mosquitto: `sudo systemctl stop mosquitto`
- API: Change `API_PORT` in backend/.env

## System Status

✅ MQTT Broker: Fully operational
✅ Robot Simulator: Working (publishes at ~1 Hz)
✅ FastAPI Backend: Working
✅ Frontend Dashboard: Working
✅ WebSocket Communication: Working
✅ Message Throughput: 4.6 msg/sec (349 messages in 76s test)

## Next Steps

1. ✅ System is production-ready for frontend integration
2. 🔄 Increase NUM_SIMULATED_ROBOTS for multi-robot support
3. 🔄 Integrate real robot hardware
4. 🔄 Deploy to production server
