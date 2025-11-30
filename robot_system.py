"""
Mobile Robot MQTT System - Clean Version
Core robot kinematics and control system
"""
import math
import json
from datetime import datetime, timedelta

class KinematicsLogger:
    """Kinematics assessment and path logging system"""
    
    def __init__(self):
        self.path_log = []
        self.velocity_log = []
        self.acceleration_log = []
        self.position_history = []
        self.current_position = {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0}
        self.target_position = {"x": 0.0, "y": 0.0, "z": 0.0, "theta": 0.0}
        self.max_velocity = 2.0  # m/s
        self.max_acceleration = 1.0  # m/s²
        
    def update_position(self, dx=0.0, dy=0.0, dtheta=0.0, duration=0.1):
        """Update robot position and log kinematics"""
        timestamp = datetime.now().isoformat() + "Z"
        
        # Calculate new position
        old_pos = self.current_position.copy()
        self.current_position["x"] += dx
        self.current_position["y"] += dy
        self.current_position["theta"] += dtheta
        
        # Calculate velocity using actual duration
        dt = max(duration, 0.01)  # Minimum 10ms to avoid division by zero
        velocity = {
            "linear": math.sqrt(dx**2 + dy**2) / dt,
            "angular": abs(dtheta) / dt
        }
        
        # Calculate acceleration (change in velocity)
        if self.velocity_log:
            last_vel = self.velocity_log[-1]["velocity"]
            acceleration = {
                "linear": (velocity["linear"] - last_vel["linear"]) / dt,
                "angular": (velocity["angular"] - last_vel["angular"]) / dt
            }
        else:
            acceleration = {"linear": 0.0, "angular": 0.0}
        
        # Log data
        path_entry = {
            "timestamp": timestamp,
            "position": self.current_position.copy(),
            "previous_position": old_pos,
            "displacement": {"dx": dx, "dy": dy, "dtheta": dtheta}
        }
        
        velocity_entry = {
            "timestamp": timestamp,
            "velocity": velocity
        }
        
        acceleration_entry = {
            "timestamp": timestamp,
            "acceleration": acceleration
        }
        
        self.path_log.append(path_entry)
        self.velocity_log.append(velocity_entry)
        self.acceleration_log.append(acceleration_entry)
        
        # Keep only last 1000 entries
        for log in [self.path_log, self.velocity_log, self.acceleration_log]:
            if len(log) > 1000:
                log[:] = log[-1000:]
        
        return {
            "current_position": self.current_position,
            "velocity": velocity,
            "acceleration": acceleration,
            "timestamp": timestamp
        }
    
    def get_kinematics_summary(self):
        """Get comprehensive kinematics summary"""
        total_distance = 0
        if self.path_log:
            for entry in self.path_log:
                disp = entry["displacement"]
                total_distance += math.sqrt(disp["dx"]**2 + disp["dy"]**2)
        
        velocities = [entry["velocity"]["linear"] for entry in self.velocity_log if entry["velocity"]["linear"] > 0]
        avg_velocity = sum(velocities) / len(velocities) if velocities else 0
        max_velocity = max(velocities) if velocities else 0
        
        accelerations = [entry["acceleration"]["linear"] for entry in self.acceleration_log]
        avg_acceleration = sum(accelerations) / len(accelerations) if accelerations else 0
        
        efficiency = min(1.0, avg_velocity / self.max_velocity) if avg_velocity > 0 else 0
        
        return {
            "current_position": self.current_position,
            "target_position": self.target_position,
            "statistics": {
                "total_distance_traveled_m": total_distance,
                "average_velocity_ms": avg_velocity,
                "max_velocity_reached_ms": max_velocity,
                "average_acceleration_ms2": avg_acceleration,
                "path_points_logged": len(self.path_log),
                "movement_efficiency": efficiency
            },
            "timestamp": datetime.now().isoformat() + "Z"
        }

class TeleoperationController:
    """Remote tele-operated driving system"""
    
    def __init__(self, kinematics_logger):
        self.kinematics = kinematics_logger
        self.drive_mode = "MANUAL"
        self.safety_enabled = True
        self.emergency_stop = False
        self.drive_commands = []
        self.last_command_time = datetime.now()
        
    def process_drive_command(self, command_data):
        """Process drive command and update kinematics"""
        timestamp = datetime.now()
        
        if self.emergency_stop:
            return {"status": "BLOCKED", "reason": "Emergency stop active"}
        
        direction = command_data.get("direction", "forward")
        speed = max(0.0, min(1.0, command_data.get("speed", 0.5)))
        duration = max(0.1, min(5.0, command_data.get("duration", 1.0)))
        
        # Calculate movement
        movement = self._calculate_movement(direction, speed, duration)
        
        # Apply safety limits
        if self.safety_enabled:
            movement = self._apply_safety_limits(movement)
        
        # Execute movement
        kinematics_result = self.kinematics.update_position(
            dx=movement["dx"],
            dy=movement["dy"], 
            dtheta=movement["dtheta"],
            duration=duration
        )
        
        # Log command
        command_log = {
            "timestamp": timestamp.isoformat() + "Z",
            "command": command_data,
            "movement": movement,
            "result_position": kinematics_result["current_position"]
        }
        self.drive_commands.append(command_log)
        
        # Keep only last 100 commands
        if len(self.drive_commands) > 100:
            self.drive_commands = self.drive_commands[-100:]
        
        self.last_command_time = timestamp
        
        return {
            "status": "SUCCESS",
            "executed_movement": movement,
            "new_position": kinematics_result["current_position"],
            "velocity": kinematics_result["velocity"]
        }
    
    def _calculate_movement(self, direction, speed, duration):
        """Calculate movement deltas based on command"""
        # Realistic robot movement parameters
        max_linear_speed = 1.5  # m/s maximum linear speed
        max_angular_speed = 1.0  # rad/s maximum angular speed
        
        # Calculate actual speeds based on input
        linear_speed = max_linear_speed * speed
        angular_speed = max_angular_speed * speed
        
        # Calculate movement based on direction
        movements = {
            "forward": {"dx": linear_speed * duration, "dy": 0, "dtheta": 0},
            "backward": {"dx": -linear_speed * duration, "dy": 0, "dtheta": 0},
            "left": {"dx": 0, "dy": linear_speed * duration, "dtheta": 0},
            "right": {"dx": 0, "dy": -linear_speed * duration, "dtheta": 0},
            "rotate_left": {"dx": 0, "dy": 0, "dtheta": angular_speed * duration},
            "rotate_right": {"dx": 0, "dy": 0, "dtheta": -angular_speed * duration}
        }
        
        return movements.get(direction, {"dx": 0, "dy": 0, "dtheta": 0})
    
    def _apply_safety_limits(self, movement):
        """Apply safety limits to movement"""
        # More reasonable safety limits for robot operation
        max_single_move = 5.0  # Maximum single movement distance (5 meters)
        max_rotation = 3.14  # Maximum single rotation (180 degrees)
        
        # Only apply safety limits if safety is enabled
        if self.safety_enabled:
            movement["dx"] = max(-max_single_move, min(max_single_move, movement["dx"]))
            movement["dy"] = max(-max_single_move, min(max_single_move, movement["dy"]))
            movement["dtheta"] = max(-max_rotation, min(max_rotation, movement["dtheta"]))
        
        return movement

class RobotHealthMonitor:
    """Health parameters logging with cycle counter, battery status"""
    
    def __init__(self):
        self.cycle_counter = 0
        self.battery_level = 100.0  # percentage
        self.voltage = 24.0  # volts
        self.temperature = 25.0  # celsius
        self.error_log = []
        self.maintenance_due = False
        self.last_maintenance = datetime.now()
        self.start_time = datetime.now()
        
    def update_cycle(self):
        """Update cycle counter"""
        self.cycle_counter += 1
        
        # Simulate battery drain
        self.battery_level = max(0, self.battery_level - 0.1)
        
        # Simulate temperature variation
        self.temperature = 25.0 + (self.cycle_counter % 10) * 0.5
        
        # Check if maintenance is due (every 1000 cycles)
        self.maintenance_due = (self.cycle_counter % 1000) == 0
    
    def get_health_status(self):
        """Get comprehensive health status"""
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        battery_status = "NORMAL"
        if self.battery_level < 10:
            battery_status = "CRITICAL"
        elif self.battery_level < 25:
            battery_status = "LOW"
        
        return {
            "timestamp": datetime.now().isoformat() + "Z",
            "cycle_counter": self.cycle_counter,
            "battery": {
                "level_percent": self.battery_level,
                "voltage": self.voltage,
                "status": battery_status
            },
            "system": {
                "temperature_celsius": round(self.temperature, 1),
                "uptime_seconds": int(uptime_seconds),
                "uptime_formatted": str(timedelta(seconds=int(uptime_seconds))),
                "maintenance_due": self.maintenance_due,
                "last_maintenance": self.last_maintenance.isoformat() + "Z"
            },
            "errors": {
                "recent_count": len(self.error_log),
                "latest": self.error_log[-1] if self.error_log else None
            }
        }