#!/usr/bin/env python3
"""
Simple MQTT Robot Demo Server
A clean, working version with all features
"""

import json
import time
import random
from datetime import datetime, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs
import threading
import os
import sys

class MQTTRobotServer:
    def __init__(self):
        print("🚀 INITIALIZING SIMPLE MQTT ROBOT SERVER")
        self.running = True
        self.start_time = datetime.now()
        
        # Robot state
        self.robot_data = {
            "kinematics": {
                "current_position": {
                    "x": 0.0,
                    "y": 0.0,
                    "theta": 0.0
                },
                "velocity": {"vx": 0.0, "vy": 0.0, "omega": 0.0},
                "timestamp": datetime.now().isoformat()
            },
            "health": {
                "data": {
                    "battery": {
                        "level_percent": 100.0,
                        "voltage": 24.0,
                        "current": 0.0,
                        "temperature": 25.0
                    },
                    "motors": {
                        "left": {"temperature": 30.0, "current": 0.0, "status": "OK"},
                        "right": {"temperature": 30.0, "current": 0.0, "status": "OK"}
                    }
                }
            },
            "software_updates": [
                {
                    "name": "Robot Control System",
                    "current_version": "2.1.4",
                    "latest_version": "2.1.4",
                    "status": "up_to_date",
                    "size_mb": 12.3,
                    "description": "Core navigation and control algorithms"
                },
                {
                    "name": "Security Patches",
                    "current_version": "1.8.1",
                    "latest_version": "1.8.2",
                    "status": "update_available",
                    "size_mb": 5.7,
                    "description": "Latest security updates and patches"
                },
                {
                    "name": "AI Navigation Module",
                    "current_version": "3.2.1",
                    "latest_version": "3.2.1",
                    "status": "up_to_date",
                    "size_mb": 28.5,
                    "description": "Enhanced pathfinding and obstacle avoidance"
                },
                {
                    "name": "MQTT Communication",
                    "current_version": "1.4.6",
                    "latest_version": "1.4.7",
                    "status": "update_available",
                    "size_mb": 8.2,
                    "description": "Real-time communication protocol updates"
                }
            ],
            "system_diagnostics": {
                "cpu_usage": 15.2,
                "memory_usage": 45.8,
                "temperature": 42.3,
                "uptime_hours": 0.0,
                "disk_usage": 67.4,
                "network_status": "connected"
            }
        }
        
    def update_data(self):
        """Update robot data with random changes"""
        # Update position slightly
        self.robot_data["kinematics"]["current_position"]["x"] += random.uniform(-0.01, 0.01)
        self.robot_data["kinematics"]["current_position"]["y"] += random.uniform(-0.01, 0.01)
        self.robot_data["kinematics"]["current_position"]["theta"] += random.uniform(-1, 1)
        
        # Update battery (slow decrease)
        current_battery = self.robot_data["health"]["data"]["battery"]["level_percent"]
        if current_battery > 0:
            self.robot_data["health"]["data"]["battery"]["level_percent"] = max(0, current_battery - 0.01)
        
        # Update system diagnostics
        diag = self.robot_data["system_diagnostics"]
        diag["cpu_usage"] = max(0, min(100, diag["cpu_usage"] + random.uniform(-2, 2)))
        diag["memory_usage"] = max(0, min(100, diag["memory_usage"] + random.uniform(-1, 1)))
        diag["temperature"] = max(20, min(80, diag["temperature"] + random.uniform(-1, 1)))
        
        # Update uptime
        uptime = (datetime.now() - self.start_time).total_seconds() / 3600
        diag["uptime_hours"] = uptime
        
        # Update timestamp
        self.robot_data["kinematics"]["timestamp"] = datetime.now().isoformat()
        
    def save_data(self):
        """Save current data to JSON file"""
        try:
            with open("mqtt_live_data.json", "w") as f:
                json.dump(self.robot_data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {e}")
    
    def simulate_movement(self, direction):
        """Simulate robot movement"""
        movement_map = {
            "forward": (0.1, 0.0, 0.0),
            "backward": (-0.1, 0.0, 0.0),
            "left": (0.0, 0.1, 5.0),
            "right": (0.0, -0.1, -5.0)
        }
        
        if direction in movement_map:
            dx, dy, dtheta = movement_map[direction]
            pos = self.robot_data["kinematics"]["current_position"]
            pos["x"] += dx
            pos["y"] += dy
            pos["theta"] += dtheta
            print(f"🤖 Robot moved {direction}: x={pos['x']:.2f}, y={pos['y']:.2f}, θ={pos['theta']:.1f}°")
            self.save_data()
            return True
        return False

class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, robot_server=None, **kwargs):
        self.robot_server = robot_server
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == '/':
            self.path = '/simple_interface.html'
        elif self.path == '/get_live_data':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(self.robot_server.robot_data).encode())
            return
        
        super().do_GET()
    
    def do_POST(self):
        if self.path == '/send_command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                command = json.loads(post_data.decode())
                direction = command.get('direction', '')
                
                if self.robot_server.simulate_movement(direction):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success", "command": direction}).encode())
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "message": "Invalid command"}).encode())
                    
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": "Invalid JSON"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    robot_server = MQTTRobotServer()
    
    # Data update loop
    def update_loop():
        while robot_server.running:
            robot_server.update_data()
            robot_server.save_data()
            time.sleep(1)  # Update every second
    
    # Start background thread for data updates
    update_thread = threading.Thread(target=update_loop)
    update_thread.daemon = True
    update_thread.start()
    
    # Create HTTP server
    def handler(*args, **kwargs):
        CustomHTTPRequestHandler(*args, robot_server=robot_server, **kwargs)
    
    httpd = HTTPServer(('localhost', 8100), handler)
    
    print("✅ MQTT Robot Server Running!")
    print("🌐 Web Interface: http://localhost:8100")
    print("📡 Data Updates: Every 1 second")
    print("🎮 Robot Control: Ready")
    print("🔧 System Status: Active")
    print("\n🚀 Server is ready! Open http://localhost:8100 in your browser")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        robot_server.running = False

if __name__ == "__main__":
    run_server()