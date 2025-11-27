# 🚀 Quick Start Guide

## 5-Minute Setup

### Step 1: Start the WebSocket Mock Server
```bash
npm run server
```

Expected output:
```
🚀 WebSocket server running on ws://localhost:8080
Waiting for client connections...
```

### Step 2: Start the Development Server (in another terminal)
```bash
npm run dev
```

Expected output:
```
➜  Local:   http://localhost:5173/
```

### Step 3: Open Dashboard
Visit `http://localhost:5173` in your browser

## What You'll See

✅ **Header**: Shows "CONNECTED" status in green  
✅ **Map**: Robot icon at coordinates with heading arrow  
✅ **Status Panel**: Live telemetry (battery, temp, CPU, memory)  
✅ **Teleop Panel**: Interactive joystick and buttons  
✅ **Logs Panel**: Real-time event messages

## Testing the Dashboard

### Test 1: Joystick Control
1. Drag the joystick in the Teleop Panel
2. Watch the robot icon move on the map
3. Check the heading arrow rotates
4. Verify path trail appears

### Test 2: Quick Buttons
1. Click "FWD" button
2. Robot moves forward on map
3. Check logs show the command

### Test 3: Emergency Stop
1. Click "🛑 EMERGENCY STOP" button
2. Button turns red and pulses
3. All commands are disabled (greyed out)
4. Click again to re-enable

### Test 4: Posture Change
1. Select different postures from dropdown
2. Check logs for posture change events
3. E-Stop disables the dropdown

### Test 5: Battery Depletion
1. Watch battery percentage in Status Panel
2. As it drops below 60%, bar turns yellow
3. Below 20%, bar turns red and status shows ERROR

### Test 6: Telemetry Updates
1. Observe CPU, Memory, FPS values changing
2. Signal strength bars updating (1-5)
3. Temperature fluctuating
4. All updates in real-time

## For Production Deployment

### Build for Production
```bash
npm run build
```
Creates optimized files in `dist/` folder

### Connect to Real Robot
Edit `src/services/websocketService.js`:
```javascript
constructor(url = 'ws://your-robot-ip:8080') {
  this.url = url;
  // ...
}
```

### Deploy
```bash
npm run build
# Upload dist/ folder to your web server
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connection DISCONNECTED" | Ensure `npm run server` is running |
| Map doesn't load | Check internet (OpenStreetMap tiles) or browser console |
| Joystick not working | Refresh page, check browser console for errors |
| Commands not sending | Verify WebSocket is CONNECTED in header |

## File Structure

```
src/
├── services/websocketService.js     ← WebSocket client
├── components/
│   ├── Header.jsx                   ← Status display
│   ├── MapPanel.jsx                 ← Leaflet map
│   ├── StatusPanel.jsx              ← Telemetry
│   ├── TeleopPanel.jsx              ← Joystick controls
│   └── LogsPanel.jsx                ← Event logs
├── pages/
│   └── Dashboard.jsx                ← Main layout
├── App.jsx
├── main.jsx
└── index.css                        ← Tailwind + custom styles

server.js                           ← Mock WebSocket server
```

## Performance Notes

- ⚡ **6-10 updates/second**: Smooth real-time feel
- 🎮 **<100ms latency**: Responsive joystick control
- 📱 **Mobile optimized**: Responsive design works on tablets/phones
- 🗺️ **Leaflet efficiency**: Map updates without full redraws

## Next Steps

1. ✅ Test all features with mock server
2. ✅ Verify WebSocket protocol matches your robot backend
3. 🔄 Update WebSocket URL for real robot
4. 🚀 Deploy to production server

---

**Happy testing! 🤖🎮**
