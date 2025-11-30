"""
MQTT Robot Server - Clean Version
Complete MQTT integration with live updates
"""
import json
import time
import threading
import logging
from datetime import datetime
from robot_system import TeleoperationController, KinematicsLogger, RobotHealthMonitor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MQTTRobotServer:
    """Complete MQTT Robot Server with real-time updates"""
    
    def __init__(self):
        self.running = False
        self.update_thread = None
        self.command_thread = None
        
        # Initialize robot components
        self.kinematics = KinematicsLogger()
        self.teleop = TeleoperationController(self.kinematics)
        self.health = RobotHealthMonitor()
        
        # Mock MQTT data storage (simulating MQTT broker)
        self.mqtt_data = {
            'kinematics': {},
            'health': {},
            'drive_response': {},
            'system_status': {},
            'software_updates': {},
            'system_diagnostics': {},
            'commands': []
        }
        
        # Command queue for processing
        self.command_queue = []
        self.command_lock = threading.Lock()
        
        logger.info("🤖 MQTT Robot Server initialized")
    
    def start(self):
        """Start the robot server"""
        self.running = True
        
        # Start update thread for periodic data publishing
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()
        
        # Start command processing thread
        self.command_thread = threading.Thread(target=self._command_loop, daemon=True)
        self.command_thread.start()
        
        logger.info("✅ MQTT Robot Server started")
    
    def stop(self):
        """Stop the robot server"""
        self.running = False
        if self.update_thread:
            self.update_thread.join(timeout=1)
        if self.command_thread:
            self.command_thread.join(timeout=1)
        logger.info("🛑 MQTT Robot Server stopped")
    
    def add_command(self, command):
        """Add a drive command to the queue"""
        with self.command_lock:
            command['timestamp'] = datetime.now().isoformat() + "Z"
            self.command_queue.append(command)
            logger.info(f"📥 Command queued: {command['direction']} at {command['speed']*100:.0f}%")
    
    def get_latest_data(self):
        """Get all latest robot data"""
        return {
            'kinematics': self.mqtt_data.get('kinematics', {}),
            'health': self.mqtt_data.get('health', {}),
            'drive_response': self.mqtt_data.get('drive_response', {}),
            'system_status': self.mqtt_data.get('system_status', {}),
            'software_updates': self.mqtt_data.get('software_updates', {}),
            'system_diagnostics': self.mqtt_data.get('system_diagnostics', {}),
            'timestamp': datetime.now().isoformat() + "Z"
        }
    
    def _update_loop(self):
        """Periodic update loop - simulates MQTT publishing"""
        logger.info("🔄 Starting update loop")
        
        while self.running:
            try:
                # Update kinematics data
                kinematics_summary = self.kinematics.get_kinematics_summary()
                self.mqtt_data['kinematics'] = {
                    'topic': 'mobile_robot/mobile/kinematics/data',
                    'current_position': self.kinematics.current_position,
                    'statistics': kinematics_summary['statistics'],
                    'timestamp': datetime.now().isoformat() + "Z"
                }
                
                # Update health data
                health_data = self.health.get_health_status()
                self.mqtt_data['health'] = {
                    'topic': 'mobile_robot/mobile/health/status',
                    'data': health_data,
                    'timestamp': datetime.now().isoformat() + "Z"
                }
                
                # Update system status
                self.mqtt_data['system_status'] = {
                    'topic': 'mobile_robot/mobile/system/status',
                    'status': 'RUNNING',
                    'uptime': int(time.time() - getattr(self, 'start_time', time.time())),
                    'commands_processed': len(self.mqtt_data.get('commands', [])),
                    'timestamp': datetime.now().isoformat() + "Z"
                }
                
                # Update software updates status
                self._update_software_status()
                
                # Update system diagnostics
                self._update_diagnostics()
                
                # Save to file for web interface to read
                with open('mqtt_live_data.json', 'w') as f:
                    json.dump(self.get_latest_data(), f, indent=2)
                
                time.sleep(0.5)  # Update every 500ms for smooth real-time feel
                
            except Exception as e:
                logger.error(f"❌ Error in update loop: {e}")
                time.sleep(1)
    
    def _command_loop(self):
        """Command processing loop"""
        logger.info("🎮 Starting command loop")
        
        while self.running:
            try:
                commands_to_process = []
                
                # Get all pending commands
                with self.command_lock:
                    commands_to_process = self.command_queue.copy()
                    self.command_queue.clear()
                
                # Process each command
                for command in commands_to_process:
                    result = self._process_command(command)
                    
                    # Store drive response
                    self.mqtt_data['drive_response'] = {
                        'topic': 'mobile_robot/mobile/drive/response',
                        'command': command,
                        'result': result,
                        'timestamp': datetime.now().isoformat() + "Z"
                    }
                    
                    # Log command to history
                    self.mqtt_data.setdefault('commands', []).append({
                        'command': command,
                        'result': result,
                        'timestamp': datetime.now().isoformat() + "Z"
                    })
                    
                    logger.info(f"✅ Command processed: {result['status']}")
                
                time.sleep(0.1)  # Check for new commands every 100ms
                
            except Exception as e:
                logger.error(f"❌ Error in command loop: {e}")
                time.sleep(1)
    
    def _process_command(self, command):
        """Process a single drive command"""
        try:
            # Use the real teleop controller to process the command
            result = self.teleop.process_drive_command(command)
            
            # Update health cycle
            self.health.update_cycle()
            
            logger.info(f"🎮 Executed: {command['direction']} -> Position: X={self.kinematics.current_position['x']:.3f}, Y={self.kinematics.current_position['y']:.3f}, θ={self.kinematics.current_position['theta']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Command processing error: {e}")
            return {
                'status': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat() + "Z"
            }
    
    def _update_software_status(self):
        """Update software and update information"""
        import random
        
        # Simulate software components and their versions
        components = [
            {
                'name': 'Robot Control System',
                'current_version': '2.1.4',
                'latest_version': '2.1.4',
                'description': 'Core navigation and control algorithms',
                'size_mb': 12.3,
                'status': 'up_to_date',
                'last_updated': '2025-11-28T10:30:00Z'
            },
            {
                'name': 'Security Patches',
                'current_version': '1.8.1',
                'latest_version': '1.8.2',
                'description': 'Latest security updates and patches',
                'size_mb': 5.7,
                'status': 'update_available',
                'last_updated': '2025-11-25T14:15:00Z'
            },
            {
                'name': 'AI Navigation Module',
                'current_version': '3.2.1',
                'latest_version': '3.2.1',
                'description': 'Enhanced pathfinding and obstacle avoidance',
                'size_mb': 28.5,
                'status': 'up_to_date',
                'last_updated': '2025-11-29T09:45:00Z'
            },
            {
                'name': 'MQTT Communication',
                'current_version': '1.4.6',
                'latest_version': '1.4.7',
                'description': 'Real-time communication protocol updates',
                'size_mb': 8.2,
                'status': 'update_available',
                'last_updated': '2025-11-27T16:20:00Z'
            }
        ]
        
        # Randomly simulate updates becoming available
        for component in components:
            if component['status'] == 'up_to_date' and random.random() < 0.02:  # 2% chance per update cycle
                component['status'] = 'update_available'
                # Increment patch version
                parts = component['latest_version'].split('.')
                parts[-1] = str(int(parts[-1]) + 1)
                component['latest_version'] = '.'.join(parts)
        
        self.mqtt_data['software_updates'] = {
            'topic': 'mobile_robot/mobile/software/updates',
            'components': components,
            'last_check': datetime.now().isoformat() + "Z",
            'auto_update_enabled': True,
            'timestamp': datetime.now().isoformat() + "Z"
        }
    
    def _update_diagnostics(self):
        """Update system diagnostics information"""
        import random
        
        # Simulate system metrics (removed psutil dependency)
        cpu_percent = 15 + random.random() * 30
        memory_percent = 40 + random.random() * 30
        disk_percent = 60 + random.random() * 20
        
        uptime_seconds = int(time.time() - getattr(self, 'start_time', time.time()))
        uptime_days = uptime_seconds // 86400
        uptime_hours = (uptime_seconds % 86400) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        
        diagnostics = {
            'system_health': {
                'overall_status': 'healthy',
                'cpu_usage': round(cpu_percent, 1),
                'memory_usage': round(memory_percent, 1),
                'disk_usage': round(disk_percent, 1),
                'temperature': round(35 + random.random() * 25, 1),
                'voltage': round(23.5 + random.random() * 1.0, 1),
                'current_draw': round(1.8 + random.random() * 1.2, 1),
                'error_count': random.randint(0, 2),
                'wifi_signal': -35 - random.randint(0, 25)
            },
            'uptime': {
                'seconds': uptime_seconds,
                'formatted': f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"
            },
            'network': {
                'status': 'connected',
                'ip_address': '192.168.1.100',
                'gateway': '192.168.1.1',
                'dns': ['8.8.8.8', '8.8.4.4']
            },
            'storage': {
                'total_gb': 32.0,
                'used_gb': round(32.0 * disk_percent / 100, 1),
                'available_gb': round(32.0 * (100 - disk_percent) / 100, 1),
                'last_backup': '2025-11-29T10:30:00Z'
            }
        }
        
        # Determine overall health status
        if (diagnostics['system_health']['cpu_usage'] > 80 or 
            diagnostics['system_health']['memory_usage'] > 85 or
            diagnostics['system_health']['temperature'] > 70):
            diagnostics['system_health']['overall_status'] = 'warning'
        
        if (diagnostics['system_health']['cpu_usage'] > 95 or 
            diagnostics['system_health']['memory_usage'] > 95 or
            diagnostics['system_health']['temperature'] > 80):
            diagnostics['system_health']['overall_status'] = 'critical'
        
        self.mqtt_data['system_diagnostics'] = {
            'topic': 'mobile_robot/mobile/system/diagnostics',
            'data': diagnostics,
            'timestamp': datetime.now().isoformat() + "Z"
        }

# Global server instance
robot_server = None

def start_mqtt_robot_server():
    """Start the MQTT robot server"""
    global robot_server
    
    robot_server = MQTTRobotServer()
    robot_server.start_time = time.time()
    # Ensure starting state is clean: reset kinematics and logs so robot starts at origin
    try:
        robot_server.kinematics.current_position = {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0}
        robot_server.kinematics.path_log = []
        robot_server.kinematics.velocity_log = []
        robot_server.kinematics.acceleration_log = []
        robot_server.mqtt_data = {
            'kinematics': {},
            'health': {},
            'drive_response': {},
            'system_status': {},
            'software_updates': {},
            'system_diagnostics': {},
            'commands': []
        }
        # write an initial mqtt_live_data.json so the web UI reads zeros
        try:
            with open('mqtt_live_data.json', 'w') as f:
                json.dump(robot_server.get_latest_data(), f, indent=2)
        except Exception:
            # ignore file write errors here; update loop will recreate
            pass
    except Exception as e:
        logger.error(f"❌ Error resetting initial state: {e}")

    robot_server.start()
    
    return robot_server

def stop_mqtt_robot_server():
    """Stop the MQTT robot server"""
    global robot_server
    if robot_server:
        robot_server.stop()
        robot_server = None

if __name__ == "__main__":
    print("🚀 STARTING MQTT ROBOT SERVER")
    print("=" * 40)
    
    # Start the server
    server = start_mqtt_robot_server()
    
    try:
        print("✅ MQTT Robot Server running!")
        print("📡 Publishing data to: mqtt_live_data.json")
        print("🔄 Server running... (Press Ctrl+C to stop)")
        
        # Keep running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping MQTT Robot Server...")
        stop_mqtt_robot_server()
        print("✅ Server stopped successfully")