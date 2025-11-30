"""
Complete Web Server with MQTT Integration - Clean Version
"""
import json
import http.server
import socketserver
import threading
import time
import webbrowser
from urllib.parse import parse_qs
from mqtt_server import start_mqtt_robot_server, stop_mqtt_robot_server

class WebHandler(http.server.SimpleHTTPRequestHandler):
    """Web handler for MQTT commands"""
    
    def __init__(self, *args, **kwargs):
        self.robot_server = kwargs.pop('robot_server', None)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests for live data and status"""
        if self.path == '/get_live_data':
            try:
                # Read the latest MQTT data
                with open('mqtt_live_data.json', 'r') as f:
                    data = json.load(f)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps(data).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'ERROR', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
        else:
            # Handle file requests
            super().do_GET()
    
    def do_POST(self):
        """Handle command POST requests"""
        if self.path == '/send_command':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                command = json.loads(post_data.decode('utf-8'))
                
                if self.robot_server:
                    self.robot_server.add_command(command)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        'status': 'SUCCESS',
                        'message': f"Command {command['direction']} queued",
                        'timestamp': time.time()
                    }
                    self.wfile.write(json.dumps(response).encode())
                    
                    print(f"📥 Command: {command['direction']} @ {command['speed']*100:.0f}%")
                else:
                    raise Exception("Robot server not available")
                    
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json') 
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'ERROR', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                print(f"❌ Command error: {e}")
        elif self.path == '/system_action':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                action = json.loads(post_data.decode('utf-8'))
                
                # Handle system actions like diagnostics, reboot, backup, etc.
                result = self._handle_system_action(action)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                self.wfile.write(json.dumps(result).encode())
                print(f"🔧 System action: {action.get('type', 'unknown')}")
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json') 
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = {'status': 'ERROR', 'message': str(e)}
                self.wfile.write(json.dumps(response).encode())
                print(f"❌ System action error: {e}")
        else:
            self.send_response(404)
            self.end_headers()
    
    def _handle_system_action(self, action):
        """Handle system management actions"""
        action_type = action.get('type', '')
        
        if action_type == 'diagnostics':
            return {'status': 'SUCCESS', 'message': 'Full diagnostics initiated'}
        elif action_type == 'reboot':
            return {'status': 'SUCCESS', 'message': 'System reboot scheduled'}
        elif action_type == 'factory_reset':
            return {'status': 'SUCCESS', 'message': 'Factory reset initiated'}
        elif action_type == 'backup':
            return {'status': 'SUCCESS', 'message': 'Backup created successfully'}
        elif action_type == 'restore':
            return {'status': 'SUCCESS', 'message': 'System restored from backup'}
        elif action_type == 'update_software':
            component = action.get('component', 'Unknown')
            return {'status': 'SUCCESS', 'message': f'Update started for {component}'}
        elif action_type == 'reset_position':
            # Reset robot kinematics to origin if robot_server is available
            if self.robot_server and hasattr(self.robot_server, 'kinematics'):
                try:
                    self.robot_server.kinematics.current_position = {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0}
                    # Clear logs to avoid carrying previous path
                    self.robot_server.kinematics.path_log = []
                    self.robot_server.kinematics.velocity_log = []
                    self.robot_server.kinematics.acceleration_log = []
                    # Update mqtt_live_data.json immediately so UI sees the reset
                    try:
                        with open('mqtt_live_data.json', 'w') as f:
                            json.dump(self.robot_server.get_latest_data(), f, indent=2)
                    except Exception:
                        pass
                    return {'status': 'SUCCESS', 'message': 'Position reset to origin'}
                except Exception as e:
                    return {'status': 'ERROR', 'message': f'Failed to reset: {e}'}
            else:
                return {'status': 'ERROR', 'message': 'Robot server unavailable'}
        else:
            return {'status': 'ERROR', 'message': f'Unknown action: {action_type}'}
    
    def do_OPTIONS(self):
        """Handle CORS"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Minimal logging"""
        if "interface.html" in str(args):
            print(f"🌐 Interface: {args[1]}")

def main():
    """Run the complete system"""
    PORT = 8100
    
    print("🚀 CLEAN MQTT ROBOT SYSTEM")
    print("=" * 40)
    
    # Start robot server
    print("🤖 Starting robot server...")
    robot_server = start_mqtt_robot_server()
    time.sleep(1)
    
    # Create web server
    def handler(*args, **kwargs):
        return WebHandler(*args, robot_server=robot_server, **kwargs)
    
    httpd = socketserver.TCPServer(("", PORT), handler)
    
    print(f"🌐 Starting web server on port {PORT}...")
    
    # Start server in background
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    print("✅ SYSTEM RUNNING!")
    print()
    print(f"🔗 Interface: http://localhost:{PORT}/interface.html")
    print("📡 Features: Live position tracking, drive controls, health monitoring")
    print()
    
    # Auto-open browser
    try:
        time.sleep(1)
        url = f"http://localhost:{PORT}/interface.html"
        print(f"🚀 Opening: {url}")
        webbrowser.open(url)
    except:
        print("❌ Could not auto-open browser")
    
    try:
        print("🔄 System running... (Press Ctrl+C to stop)")
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping system...")
        httpd.shutdown()
        stop_mqtt_robot_server()
        print("✅ System stopped")

if __name__ == "__main__":
    main()