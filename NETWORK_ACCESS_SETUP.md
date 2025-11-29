# Network Access Setup Guide - MacBook & iPad

## Overview
This guide enables you to control the robot from both your MacBook and iPad over the same local network.

## Changes Made

### 1. Frontend (Vite Server)
**File**: `frontEnd/vite.config.js`
- Configured to listen on all network interfaces (`0.0.0.0`)
- Enabled CORS for cross-origin requests
- Added HMR configuration for proper hot module reloading

### 2. WebSocket Service
**File**: `frontEnd/src/services/websocketService.js`
- Changed from hardcoded `localhost:5001` to dynamic IP detection
- Automatically connects to the current host's IP address
- Allows both MacBook and iPad to connect to the backend

### 3. Backend (Already Supports Network Access)
**File**: `backend/app.py`
- Already configured with `host='0.0.0.0'` and CORS enabled
- Accepts connections from any network interface

## Setup Instructions

### Prerequisites
Ensure both MacBook and iPad are on the same WiFi network.

### Step 1: Find Your MacBook's IP Address

Open Terminal and run:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

Look for your local IP address (typically `192.168.x.x` or `10.0.x.x`)

Example output:
```
inet 192.168.1.100 netmask 0xffffff00 broadcast 192.168.1.255
```

**Note your IP address** (e.g., `192.168.1.100`)

### Step 2: Start the Backend

In Terminal, navigate to the backend folder:
```bash
cd /Users/vetrivel/repo/hackathon/backend
python app.py
```

You should see:
```
🚀 S4 REMOTE ROBOT MANAGEMENT CLOUD SYSTEM - BACKEND
📡 Flask API Server: http://0.0.0.0:5001
```

The backend is now listening on port **5001**

### Step 3: Start the Frontend (in another Terminal tab)

Navigate to the frontend folder:
```bash
cd /Users/vetrivel/repo/hackathon/frontEnd
npm run dev
```

You should see:
```
VITE v7.2.4  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.1.100:5173/
```

The frontend is now listening on port **5173**

## Accessing from Devices

### From MacBook
- **Frontend**: `http://localhost:5173` or `http://192.168.1.100:5173`
- **Backend API**: `http://localhost:5001` or `http://192.168.1.100:5001`

### From iPad (same network)
- **Frontend**: `http://192.168.1.100:5173` (replace with your MacBook's IP)
- The WebSocket automatically connects to `http://192.168.1.100:5001`

### Example Steps on iPad
1. Open Safari (or any web browser)
2. Enter: `http://192.168.1.100:5173` (use your actual MacBook IP)
3. The robot control dashboard will load
4. You can now control the robot from the iPad alongside your MacBook

## Troubleshooting

### Can't Connect from iPad?

1. **Check Network**
   ```bash
   # On iPad, try to ping your MacBook
   ping 192.168.1.100
   ```

2. **Check Firewall**
   - Go to **System Preferences → Security & Privacy → Firewall Options**
   - Ensure Python and Node.js are allowed, or disable firewall for testing

3. **Check IP Address**
   - Make sure you're using the correct local IP (not localhost)
   - Run `ifconfig` again to verify

4. **Check Ports**
   ```bash
   # Verify backend is running on 5001
   lsof -i :5001
   
   # Verify frontend is running on 5173
   lsof -i :5173
   ```

5. **Browser Console**
   - Open DevTools on iPad (or MacBook)
   - Check Console tab for connection errors
   - WebSocket should show "connected to: http://192.168.1.100:5001"

### Firewall Configuration (if needed)

Allow traffic on ports 5001 and 5173:
```bash
# Allow port 5001
sudo lsof -i :5001

# Check current firewall rules
sudo pfctl -s nat
```

## Multi-Device Control Features

✅ **Both MacBook and iPad can**:
- View real-time robot position and telemetry
- Send movement commands simultaneously
- Monitor battery, temperature, and system health
- Receive path logging and obstacle detection
- Trigger emergency stop
- View logs and event history

⚠️ **Notes**:
- If both send conflicting commands, the last command takes precedence
- Keep emergency stop accessible on all devices
- Ensure good WiFi signal for responsive control

## Production Deployment

For production use:
1. Use a static IP or hostname instead of dynamic IPs
2. Configure nginx/Apache reverse proxy for better performance
3. Use HTTPS/WSS for secure connections
4. Implement authentication for device access
5. Set up proper firewall rules instead of allowing all traffic

## Quick Reference

| Component | Port | Access |
|-----------|------|--------|
| Vite Frontend | 5173 | `http://<IP>:5173` |
| Flask Backend | 5001 | `http://<IP>:5001` |
| WebSocket | 5001 | `ws://<IP>:5001/socket.io` |

