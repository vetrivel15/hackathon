# Movement Mode Dropdown Update

## Summary

Updated the Movement Mode dropdown in the frontend to include all robot control modes and properly map them to the MQTT backend.

## Changes Made

### Frontend (`frontend/src/components/TeleopPanel.jsx`)

1. **Updated dropdown options** (line 520-524):
   - ✅ **Sit** 🪑 - Robot sits down
   - ✅ **Stand** 🧍 - Robot stands up (default)
   - ✅ **Walk** 🚶 - Robot walks
   - ✅ **Run** 🏃 - Robot runs
   - ✅ **Stop** 🛑 - Emergency stop (goes to standing)

2. **Updated mode mapping** (line 187-193):
   ```javascript
   const modeMap = {
     'Sit': 'sitting',
     'Stand': 'standing',
     'Walk': 'walking',
     'Run': 'running',
     'Stop': 'standing'  // Stop means go to standing position
   };
   ```

3. **Changed default mode** to "Stand" (line 55)

## Backend Compatibility

The backend (`backend/app/robot_simulator.py`) already supports these modes:

### Mode Constants (lines 69-72)
```python
MODE_WALKING = "walking"
MODE_SITTING = "sitting"
MODE_STANDING = "standing"
MODE_RUNNING = "running"
```

### Mode Handler (lines 357-390)
The `_handle_mode_change` function accepts both forms:
- **Short form**: sit, stand, walk, run, stop
- **Long form**: sitting, standing, walking, running

The backend normalizes them using a mode_map (lines 371-376):
```python
mode_map = {
    "run": self.MODE_RUNNING,
    "walk": self.MODE_WALKING,
    "sit": self.MODE_SITTING,
    "stand": self.MODE_STANDING
}
```

## How It Works

### Frontend → Backend Flow

1. **User selects mode** from dropdown (e.g., "Walk")
2. **Frontend maps** to MQTT command: "Walk" → "walking"
3. **WebSocket sends** mode command to backend:
   ```javascript
   websocketService.sendMode('robot_01', 'walking')
   ```
4. **Backend receives** via WebSocket endpoint (main.py:494)
5. **MQTT publishes** to topic: `robot/mode/robot_01`
6. **Robot simulator** subscribes and handles via `_handle_mode_change`
7. **Mode changes** to walking, affects:
   - Battery drain (line 193-197)
   - Temperature (line 207-214)
   - Health degradation (line 232-237)
   - Movement speed

## Mode Behaviors

### Sit (sitting)
- Battery drain: **0.005%/s**
- Temperature: Decreases to 25°C
- Status: idle
- Health: Recovers slowly (+0.02/s)
- Movement: None

### Stand (standing)
- Battery drain: **0.01%/s**
- Temperature: Decreases to 30°C
- Status: idle
- Health: Neutral
- Movement: None (ready stance)

### Walk (walking)
- Battery drain: **0.05%/s**
- Temperature: Increases to max 50°C
- Status: moving
- Health: Slight degradation (-0.02/s)
- Movement: Linear velocity up to 1.0 m/s

### Run (running)
- Battery drain: **0.1%/s** (highest)
- Temperature: Increases to max 65°C
- Status: moving
- Health: Faster degradation (-0.05/s)
- Movement: Linear velocity up to 3.0 m/s

### Stop
- Maps to "standing" mode
- Stops all movement
- Returns robot to standing position

## MQTT Topics

When mode changes, the following happens:

1. **Command sent**:
   ```
   Topic: robot/mode/robot_01
   Payload: {"mode": "walking"}
   ```

2. **Telemetry updated** (published every 1 second):
   ```
   Topic: robot/status/robot_01
   Payload: {
     "robot_id": "robot_01",
     "mode": "walking",
     "status": "moving",
     "battery": 75.5,
     "health": 85.2,
     "temperature": 42.5,
     ...
   }
   ```

3. **Frontend receives** via WebSocket:
   ```json
   {
     "type": "health_telemetry",
     "battery": {"level": 75.5, "health": 85.2},
     "thermal": {"cpu_temp": 42.5},
     ...
   }
   ```

## Testing

### Test Mode Changes

1. **Open frontend** in browser
2. **Select different modes** from dropdown:
   - Sit → Battery should drain slowly, temp decreases
   - Stand → Battery drains slightly, temp stabilizes
   - Walk → Battery drains faster, temp increases moderately
   - Run → Battery drains fastest, temp increases significantly
   - Stop → Should go to standing position

3. **Watch telemetry** in backend logs or MQTT listener:
   ```bash
   cd backend
   python test_mqtt_listener.py --port 1884
   ```

4. **Verify values change**:
   - Battery drain rate
   - Temperature trend
   - Health percentage
   - Mode field in status messages

### Expected Console Output

**Frontend (Browser Console):**
```
🚀 Sending mode change: walking
📡 Mode command sent: SUCCESS
```

**Backend (Terminal):**
```
INFO - Robot robot_01 received mode change request: 'walking'
INFO - MODE: robot=robot_01, mode=walking
```

**MQTT Listener:**
```
[STATUS] Message @ HH:MM:SS
Robot: robot_01
Mode: walking
Status: moving
Battery: 75.5%
Health: 85.2% [GOOD]
Temperature: 42.5°C [NORMAL]
```

## UI Location

The Movement Mode dropdown is located in:
- **Component**: TeleopPanel
- **Section**: "🎮 Teleoperation Controls"
- **Label**: "⚡ Movement Mode"
- **Position**: Right side panel, below joystick controls

## Removed Components

- ✅ **Posture dropdown** - Removed (was redundant)
- The sit/stand functionality is now in the Movement Mode dropdown

## Summary of Benefits

✅ **Unified control** - All movement modes in one dropdown
✅ **Clear labeling** - Emoji icons for each mode
✅ **Proper mapping** - Frontend modes correctly map to backend
✅ **Real-time feedback** - Mode changes reflect immediately in telemetry
✅ **Battery awareness** - Different drain rates per mode
✅ **Temperature tracking** - Temperature varies by activity level
✅ **Health monitoring** - Health affected by mode choice
