"""
Humanoid Robot Backend Server
WebSocket-based real-time teleoperation and telemetry service
"""

import os
import json
import math
import random
import time
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv

load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
CORS(app)

# Initialize SocketIO for WebSocket support
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ============================================================================
# ROBOT STATE MANAGEMENT
# ============================================================================

class RobotState:
    """Manages the state of the humanoid robot"""
    def __init__(self):
        # Position and heading - BTM, Bangalore
        self.latitude = 12.9352
        self.longitude = 77.6245
        self.heading = 0.0
        
        # Telemetry
        self.battery = 85.0
        self.temperature = 42.0
        self.signal_strength = 5
        self.system_status = "OK"
        self.cpu_usage = 30
        self.memory_usage = 45
        self.fps_count = 30
        self.joint_errors = 0
        
        # Control state
        self.mode = "IDLE"  # IDLE, TELEOP, STOPPED
        self.previous_mode = None  # Track previous mode for change detection
        self.emergency_stop = False
        self.posture = "Stand"
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        
        # Connected clients
        self.connected_clients = set()
        self.last_update = time.time()

robot = RobotState()

# ============================================================================
# WEBSOCKET EVENT HANDLERS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    client_id = request.sid
    robot.connected_clients.add(client_id)
    print(f"✅ Client connected: {client_id}")
    print(f"📊 Connected clients: {len(robot.connected_clients)}")
    
    # Send initial state to client
    emit('connection', {
        'status': 'connected',
        'robot_name': 'zeeno',
        'timestamp': time.time()
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    client_id = request.sid
    robot.connected_clients.discard(client_id)
    print(f"🔌 Client disconnected: {client_id}")
    print(f"📊 Connected clients: {len(robot.connected_clients)}")

@socketio.on('message')
def handle_message(data):
    """Handle incoming WebSocket messages"""
    try:
        msg_type = data.get('type')
        
        if msg_type == 'control':
            handle_control_command(data)
        elif msg_type == 'ping':
            emit('pong', {'timestamp': time.time()})
        else:
            print(f"⚠️ Unknown message type: {msg_type}")
    except Exception as e:
        print(f"❌ Error handling message: {e}")
        emit('error', {'message': str(e)})

def handle_control_command(data):
    """Process control commands from the frontend"""
    action = data.get('action')
    
    if action == 'move':
        # Joystick movement
        robot.linear_velocity = float(data.get('linear', 0))
        robot.angular_velocity = float(data.get('angular', 0))
        robot.mode = "TELEOP"
        
        print(f"🎮 Move - Linear: {robot.linear_velocity:.2f}, Angular: {robot.angular_velocity:.2f}")
    
    elif action in ['move_forward', 'move_backward', 'rotate_left', 'rotate_right']:
        # Quick action buttons
        if action == 'move_forward':
            robot.linear_velocity = 0.5
            robot.angular_velocity = 0.0
        elif action == 'move_backward':
            robot.linear_velocity = -0.5
            robot.angular_velocity = 0.0
        elif action == 'rotate_left':
            robot.linear_velocity = 0.0
            robot.angular_velocity = 0.5
        elif action == 'rotate_right':
            robot.linear_velocity = 0.0
            robot.angular_velocity = -0.5
        
        robot.mode = "TELEOP"
        print(f"🔘 Quick action: {action}")
    
    elif action == 'set_posture':
        robot.posture = data.get('value', 'Stand')
        log_event('INFO', f"Posture changed to {robot.posture}")
        print(f"🧍 Posture: {robot.posture}")
    
    elif action == 'emergency_stop':
        robot.emergency_stop = data.get('value', False)
        robot.mode = "STOPPED" if robot.emergency_stop else "IDLE"
        robot.linear_velocity = 0.0
        robot.angular_velocity = 0.0
        status = "activated" if robot.emergency_stop else "deactivated"
        log_event('WARN' if robot.emergency_stop else 'INFO', f"Emergency stop {status}")
        print(f"🛑 Emergency stop: {robot.emergency_stop}")
    
    else:
        print(f"⚠️ Unknown control action: {action}")

def update_robot_position():
    """Update robot position based on velocity"""
    # Simple kinematic model
    dt = 0.15  # Match the telemetry broadcast interval (150ms)
    speed_factor = 0.0008  # Increased 10x for more visible movement (~6.7 meters per velocity unit)
    
    if robot.linear_velocity != 0:
        # Move in the direction of heading
        angle_rad = math.radians(robot.heading)
        robot.latitude += robot.linear_velocity * math.cos(angle_rad) * speed_factor * dt
        robot.longitude += robot.linear_velocity * math.sin(angle_rad) * speed_factor * dt
    
    if robot.angular_velocity != 0:
        # Rotate heading
        robot.heading += robot.angular_velocity * 15 * dt  # Scale rotation with dt
        robot.heading = robot.heading % 360

def log_event(level, message):
    """Log an event and broadcast to clients"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"📋 [{timestamp}] {level}: {message}")
    socketio.emit('log_event', {
        'level': level,
        'message': message,
        'timestamp': timestamp
    })

# ============================================================================
# TELEMETRY BROADCAST
# ============================================================================

def simulate_telemetry():
    """Simulate realistic telemetry changes for a humanoid robot"""
    
    # ===== BATTERY SIMULATION (more realistic drain rates) =====
    # Idle: 0.5% per hour = 0.0000833% per second ≈ 0.0000125% per 150ms
    # Teleop walking: 5% per hour = 0.000833% per second ≈ 0.000125% per 150ms
    # Teleop running: 12% per hour = 0.002% per second ≈ 0.0003% per 150ms
    
    if robot.mode == "TELEOP":
        # Simulate more realistic battery drain
        robot.battery -= random.uniform(0.005, 0.015)  # ~0.3-0.9% per minute
    elif robot.mode == "STOPPED":
        robot.battery -= random.uniform(0.001, 0.003)  # ~0.06-0.18% per minute
    else:  # IDLE
        robot.battery -= random.uniform(0.0005, 0.002)  # ~0.03-0.12% per minute
    
    robot.battery = max(0, min(100, robot.battery))
    
    # ===== TEMPERATURE SIMULATION (realistic thermal dynamics) =====
    # Base temperature drift towards equilibrium (37°C ambient)
    ambient_temp = 37.0
    thermal_equilibrium = 0.95  # Exponential cooling factor
    robot.temperature = robot.temperature * thermal_equilibrium + ambient_temp * (1 - thermal_equilibrium)
    
    # Add activity-based heat generation
    if robot.mode == "TELEOP":
        robot.temperature += random.uniform(0.05, 0.15)  # Active operation heats up
    elif robot.mode == "IDLE":
        robot.temperature += random.uniform(-0.05, 0.05)  # Minor fluctuations
    
    # Add small random noise
    robot.temperature += random.uniform(-0.1, 0.1)
    robot.temperature = max(25, min(90, robot.temperature))
    
    # ===== CPU USAGE SIMULATION (realistic load patterns) =====
    # Base load: 15-20% (system overhead)
    # Teleop adds 30-50% load
    # Motion planning adds 20-30% load
    
    base_cpu = 18
    activity_cpu = 0
    
    if robot.mode == "TELEOP":
        activity_cpu = random.uniform(30, 55)  # Active control
    elif robot.mode == "IDLE":
        activity_cpu = random.uniform(5, 15)   # Minimal activity
    else:  # STOPPED
        activity_cpu = random.uniform(8, 12)
    
    target_cpu = base_cpu + activity_cpu
    # Smooth transitions instead of sudden jumps
    robot.cpu_usage = robot.cpu_usage * 0.7 + target_cpu * 0.3
    robot.cpu_usage = max(5, min(95, robot.cpu_usage))
    
    # ===== MEMORY USAGE SIMULATION (more stable) =====
    # Memory doesn't change as frequently as CPU
    # Add very small random fluctuations
    robot.memory_usage += random.uniform(-1, 1)
    robot.memory_usage = max(25, min(90, robot.memory_usage))
    
    # ===== SIGNAL STRENGTH SIMULATION (realistic wireless) =====
    # Signal strength varies more slowly and realistically
    # Occasional drops/spikes but generally stable
    
    if random.random() < 0.15:  # 15% chance of fluctuation each update
        robot.signal_strength += random.choice([-1, 1])
    
    # Occasional interference events (5% chance)
    if random.random() < 0.05:
        robot.signal_strength = max(0, robot.signal_strength - random.randint(1, 2))
    
    robot.signal_strength = max(0, min(5, robot.signal_strength))
    
    # ===== FPS SIMULATION (activity-dependent) =====
    # Running at 30 FPS baseline, drops under heavy load
    base_fps = 30
    
    if robot.mode == "TELEOP":
        # During active control, FPS varies based on CPU load
        fps_variance = (robot.cpu_usage / 100.0) * 10  # Higher CPU → more FPS drops
        robot.fps_count = max(15, 30 - fps_variance + random.uniform(-2, 2))
    else:
        robot.fps_count = max(25, 30 + random.uniform(-1, 2))
    
    robot.fps_count = int(robot.fps_count)
    
    # ===== SYSTEM STATUS DETERMINATION =====
    # More granular status logic
    if robot.battery < 10 or robot.temperature > 85 or robot.cpu_usage > 90:
        robot.system_status = "ERROR"
    elif robot.battery < 25 or robot.temperature > 75 or robot.cpu_usage > 75:
        robot.system_status = "WARNING"
    else:
        robot.system_status = "OK"
    
    # ===== JOINT ERRORS (rare events) =====
    # Occasionally thermal stress or overload causes joint errors
    if robot.temperature > 80 and random.random() < 0.1:
        robot.joint_errors = min(5, robot.joint_errors + 1)
    elif robot.joint_errors > 0 and random.random() < 0.3:
        robot.joint_errors = max(0, robot.joint_errors - 1)  # Self-recovery

def broadcast_telemetry():
    """Broadcast robot state to all connected clients"""
    # ===== APPLY CONTINUOUS MOVEMENT =====
    # Update position based on current velocity (continuous motion)
    if robot.linear_velocity != 0 or robot.angular_velocity != 0:
        update_robot_position()
    
    # ===== SIMULATE TELEMETRY CHANGES =====
    simulate_telemetry()
    
    # Send pose update
    socketio.emit('pose_update', {
        'lat': robot.latitude,
        'lon': robot.longitude,
        'heading': robot.heading
    })
    
    # Send telemetry update
    socketio.emit('telemetry_update', {
        'battery': round(robot.battery, 1),
        'temperature': round(robot.temperature, 1),
        'signalStrength': robot.signal_strength,
        'systemStatus': robot.system_status,
        'cpuUsage': round(robot.cpu_usage, 1),
        'memoryUsage': round(robot.memory_usage, 1),
        'fpsCount': robot.fps_count,
        'jointErrors': robot.joint_errors
    })
    
    # Send mode update only if mode has changed
    if robot.mode != robot.previous_mode:
        socketio.emit('mode_update', {
            'mode': robot.mode
        })
        robot.previous_mode = robot.mode

@socketio.on('telemetry_request')
def handle_telemetry_request():
    """Handle explicit telemetry requests"""
    broadcast_telemetry()

# ============================================================================
# REST API ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'connected_clients': len(robot.connected_clients)
    })

@app.route('/api/robot/state', methods=['GET'])
def get_robot_state():
    """Get current robot state"""
    return jsonify({
        'position': {
            'latitude': robot.latitude,
            'longitude': robot.longitude,
            'heading': robot.heading
        },
        'telemetry': {
            'battery': robot.battery,
            'temperature': robot.temperature,
            'signal_strength': robot.signal_strength,
            'system_status': robot.system_status,
            'cpu_usage': robot.cpu_usage,
            'memory_usage': robot.memory_usage,
            'fps_count': robot.fps_count,
            'joint_errors': robot.joint_errors
        },
        'control': {
            'mode': robot.mode,
            'emergency_stop': robot.emergency_stop,
            'posture': robot.posture,
            'linear_velocity': robot.linear_velocity,
            'angular_velocity': robot.angular_velocity
        }
    })

@app.route('/api/robot/reset', methods=['POST'])
def reset_robot():
    """Reset robot to initial state"""
    robot.latitude = 12.9352
    robot.longitude = 77.6245
    robot.heading = 0.0
    robot.battery = 85.0
    robot.mode = "IDLE"
    robot.emergency_stop = False
    log_event('INFO', 'Robot reset to initial state')
    return jsonify({'status': 'reset successful'})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Placeholder for log retrieval"""
    return jsonify({'logs': []})

# ============================================================================
# BACKGROUND TASKS
# ============================================================================

def background_telemetry_broadcast():
    """Background task to continuously broadcast telemetry"""
    with app.app_context():
        while True:
            try:
                if robot.connected_clients:
                    broadcast_telemetry()
                time.sleep(0.15)  # ~6.7 Hz update rate
            except Exception as e:
                print(f"❌ Error in telemetry broadcast: {e}")

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

@app.before_request
def before_request():
    """Executed before each request"""
    pass

@app.after_request
def after_request(response):
    """Executed after each request"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == '__main__':
    import threading
    
    print("\n" + "="*60)
    print("🤖 Humanoid Robot Backend Server")
    print("="*60)
    print(f"🚀 Starting server on http://0.0.0.0:5001")
    print(f"📡 WebSocket endpoint: ws://localhost:5001/socket.io")
    print(f"📊 API endpoints available at http://localhost:5001/api/*")
    print("="*60 + "\n")
    
    # Start background telemetry broadcast thread
    telemetry_thread = threading.Thread(target=background_telemetry_broadcast, daemon=True)
    telemetry_thread.start()
    
    # Start SocketIO server
    socketio.run(app, host='0.0.0.0', port=5001, debug=False, allow_unsafe_werkzeug=True)
