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
        # Position and heading
        self.latitude = 37.7749
        self.longitude = -122.4194
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
        'robot_name': 'HUM-01',
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
        
        # Update robot position based on velocity
        if robot.linear_velocity != 0 or robot.angular_velocity != 0:
            update_robot_position()
        
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
        update_robot_position()
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
    dt = 0.1  # 100ms time step
    speed_factor = 0.00001  # Scale factor for lat/lon movement
    
    if robot.linear_velocity != 0:
        # Move in the direction of heading
        angle_rad = math.radians(robot.heading)
        robot.latitude += robot.linear_velocity * math.cos(angle_rad) * speed_factor
        robot.longitude += robot.linear_velocity * math.sin(angle_rad) * speed_factor
    
    if robot.angular_velocity != 0:
        # Rotate heading
        robot.heading += robot.angular_velocity * 10
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
    """Simulate telemetry changes"""
    # Battery depletion
    if robot.mode == "TELEOP":
        robot.battery -= random.uniform(0.1, 0.3)
    else:
        robot.battery -= random.uniform(0.01, 0.05)
    
    robot.battery = max(0, min(100, robot.battery))
    
    # Temperature fluctuation
    robot.temperature += random.uniform(-0.5, 0.5)
    robot.temperature = max(30, min(80, robot.temperature))
    
    # CPU and memory variations
    robot.cpu_usage = max(10, min(90, robot.cpu_usage + random.uniform(-5, 5)))
    robot.memory_usage = max(20, min(95, robot.memory_usage + random.uniform(-3, 3)))
    
    # System status based on conditions
    if robot.battery < 20:
        robot.system_status = "WARNING"
    elif robot.temperature > 70:
        robot.system_status = "WARNING"
    elif robot.battery < 10:
        robot.system_status = "ERROR"
    else:
        robot.system_status = "OK"
    
    # Random signal fluctuation
    robot.signal_strength = max(0, min(5, robot.signal_strength + random.randint(-1, 1)))
    
    # FPS counter
    robot.fps_count = 30 + random.randint(-2, 2)

def broadcast_telemetry():
    """Broadcast robot state to all connected clients"""
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
    
    # Send mode update
    socketio.emit('mode_update', {
        'mode': robot.mode
    })

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
    robot.latitude = 37.7749
    robot.longitude = -122.4194
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
