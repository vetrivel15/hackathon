from __future__ import annotations

import asyncio
import json
import logging
import math
import random
import threading
from datetime import datetime
from typing import Dict, Optional, Tuple

from .mqtt_manager import mqtt_manager
from .config import settings

logger = logging.getLogger(__name__)


class GPSCoordinates:
    """GPS coordinates with latitude and longitude."""

    def __init__(self, latitude: float = 0.0, longitude: float = 0.0):
        self.latitude = latitude
        self.longitude = longitude

    def to_dict(self) -> Dict:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }

    def move(self, distance_meters: float, heading_degrees: float) -> None:
        """
        Move GPS position by distance in meters at given heading.

        Args:
            distance_meters: Distance to move in meters
            heading_degrees: Direction to move (0=North, 90=East, 180=South, 270=West)
        """
        # Earth radius in meters
        EARTH_RADIUS = 6378137.0

        # Convert to radians
        lat_rad = math.radians(self.latitude)
        lon_rad = math.radians(self.longitude)
        heading_rad = math.radians(heading_degrees)

        # Calculate new position
        # Angular distance
        angular_distance = distance_meters / EARTH_RADIUS

        new_lat = math.asin(
            math.sin(lat_rad) * math.cos(angular_distance) +
            math.cos(lat_rad) * math.sin(angular_distance) * math.cos(heading_rad)
        )

        new_lon = lon_rad + math.atan2(
            math.sin(heading_rad) * math.sin(angular_distance) * math.cos(lat_rad),
            math.cos(angular_distance) - math.sin(lat_rad) * math.sin(new_lat)
        )

        self.latitude = math.degrees(new_lat)
        self.longitude = math.degrees(new_lon)


class RobotSimulator:
    """Simulates a robot with random values, controls, and GPS tracking."""

    # Robot modes
    MODE_WALKING = "walking"
    MODE_SITTING = "sitting"
    MODE_STANDING = "standing"
    MODE_RUNNING = "running"

    # Robot statuses
    STATUS_IDLE = "idle"
    STATUS_MOVING = "moving"
    STATUS_ERROR = "error"
    STATUS_CHARGING = "charging"

    # Movement speeds (meters per second)
    SPEED_WALK = 1.2  # Moderate walking speed
    SPEED_RUN = 4.5   # Fast running speed
    SPEED_TURN = 0.8  # Faster turning (radians per second)

    def __init__(self, robot_id: str, initial_lat: float = 37.7749, initial_lon: float = -122.4194):
        """
        Initialize robot simulator.

        Args:
            robot_id: Unique robot identifier
            initial_lat: Starting latitude (default: San Francisco)
            initial_lon: Starting longitude (default: San Francisco)
        """
        self.robot_id = robot_id
        self.mode = self.MODE_STANDING
        self.status = self.STATUS_IDLE
        self.battery = random.uniform(50.0, 100.0)

        # Position tracking
        self.x = 0.0  # meters
        self.y = 0.0  # meters
        self.theta = 0.0  # radians (heading)

        # GPS tracking
        self.gps = GPSCoordinates(initial_lat, initial_lon)

        # Movement state
        self.linear_velocity = 0.0  # m/s
        self.angular_velocity = 0.0  # rad/s
        self.target_heading = 0.0  # for turning commands

        # Simulation state
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Register MQTT command handler
        mqtt_manager.register_handler(
            f"robot/teleop/{self.robot_id}",
            self._handle_command
        )
        mqtt_manager.register_handler(
            f"robot/cmd_vel/{self.robot_id}",
            self._handle_cmd_vel
        )
        mqtt_manager.register_handler(
            f"robot/mode/{self.robot_id}",
            self._handle_mode_change
        )

    def start(self) -> None:
        """Start the robot simulation."""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()
        logger.info(f"Robot {self.robot_id} simulator started")

    def stop(self) -> None:
        """Stop the robot simulation."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
        logger.info(f"Robot {self.robot_id} simulator stopped")

    def _simulation_loop(self) -> None:
        """Main simulation loop that updates robot state."""
        import time
        update_rate = 1  # Hz (1 update per second)
        dt = 1.0 / update_rate

        while self._running:
            self._update_state(dt)
            self._publish_telemetry()
            time.sleep(dt)

    def _update_state(self, dt: float) -> None:
        """Update robot state based on current velocities."""
        with self._lock:
            # Only update position if in walking or running mode
            if (self.linear_velocity != 0 or self.angular_velocity != 0) and \
               (self.mode in [self.MODE_WALKING, self.MODE_RUNNING]):
                # Update heading
                self.theta += self.angular_velocity * dt
                self.theta = self.theta % (2 * math.pi)

                # Update x, y position
                dx = self.linear_velocity * math.cos(self.theta) * dt
                dy = self.linear_velocity * math.sin(self.theta) * dt
                self.x += dx
                self.y += dy

                # Update GPS coordinates
                distance = self.linear_velocity * dt
                heading_degrees = math.degrees(self.theta)
                self.gps.move(distance, heading_degrees)

                self.status = self.STATUS_MOVING
            else:
                # In stand/sit mode, zero out velocities
                if self.mode in [self.MODE_STANDING, self.MODE_SITTING]:
                    self.linear_velocity = 0.0
                    self.angular_velocity = 0.0
                if self.status == self.STATUS_MOVING:
                    self.status = self.STATUS_IDLE

            # Battery drain based on activity
            drain_rate = 0.01  # % per second at idle
            if self.mode == self.MODE_WALKING:
                drain_rate = 0.05
            elif self.mode == self.MODE_RUNNING:
                drain_rate = 0.1
            elif self.mode == self.MODE_SITTING:
                drain_rate = 0.005

            self.battery = max(0.0, self.battery - drain_rate * dt)

            # Random battery recharge if sitting and low
            if self.mode == self.MODE_SITTING and self.battery < 20.0:
                if random.random() < 0.1:  # 10% chance per update
                    self.status = self.STATUS_CHARGING
                    self.battery = min(100.0, self.battery + 0.5 * dt)

    def _publish_telemetry(self) -> None:
        """Publish robot telemetry to MQTT."""
        with self._lock:
            timestamp = datetime.utcnow().isoformat() + "Z"
            telemetry = {
                "robot_id": self.robot_id,
                "mode": self.mode,
                "status": self.status,
                "battery": round(self.battery, 2),
                "pose": {
                    "x": round(self.x, 3),
                    "y": round(self.y, 3),
                    "theta": round(self.theta, 3)
                },
                "gps": self.gps.to_dict(),
                "velocity": {
                    "linear": round(self.linear_velocity, 3),
                    "angular": round(self.angular_velocity, 3)
                },
                "timestamp": timestamp
            }

        # Publish to multiple topics
        mqtt_manager.publish_event(f"robot/status/{self.robot_id}", telemetry)
        mqtt_manager.publish_event(f"robot/pose/{self.robot_id}", {
            "pose": telemetry["pose"],
            "gps": telemetry["gps"],
            "timestamp": timestamp
        })
        
        # Publish GPS data separately
        mqtt_manager.publish_event(f"robot/gps/{self.robot_id}", {
            "latitude": self.gps.latitude,
            "longitude": self.gps.longitude,
            "altitude": 10.0,
            "heading": math.degrees(self.theta),
            "timestamp": timestamp
        })
        
        # Publish joint data separately
        joints = self._get_joint_values_for_mode()
        mqtt_manager.publish_event(f"robot/joints/{self.robot_id}", {
            "timestamp": timestamp,
            "frame_id": "base_link",
            "joints": joints
        })

    def _handle_command(self, topic: str, payload: Dict) -> None:
        """Handle teleop commands."""
        if not isinstance(payload, dict):
            return

        cmd = payload.get("cmd", "")
        params = payload.get("params", {})

        logger.info(f"Robot {self.robot_id} received command: {cmd}")

        with self._lock:
            if cmd == "sit":
                self._execute_sit()
            elif cmd == "stand":
                self._execute_stand()
            elif cmd == "walk":
                self._execute_walk()
            elif cmd == "run":
                self._execute_run()
            elif cmd == "stop":
                self._execute_stop()
            elif cmd == "move_forward":
                self._execute_move_forward(params)
            elif cmd == "move_backward":
                self._execute_move_backward(params)
            elif cmd == "turn_left":
                self._execute_turn_left(params)
            elif cmd == "turn_right":
                self._execute_turn_right(params)
            else:
                logger.warning(f"Unknown command: {cmd}")

    def _handle_cmd_vel(self, topic: str, payload: Dict) -> None:
        """Handle velocity commands."""
        if not isinstance(payload, dict):
            return

        with self._lock:
            self.linear_velocity = float(payload.get("linear", 0.0))
            self.angular_velocity = float(payload.get("angular", 0.0))
            logger.info(f"Robot {self.robot_id} velocity updated: linear={self.linear_velocity}, angular={self.angular_velocity}")
        
        # Print endpoint values and publish immediate update
        self._print_endpoint_values()
        self._publish_telemetry()

    def _handle_mode_change(self, topic: str, payload: Dict) -> None:
        """Handle mode change commands."""
        if not isinstance(payload, dict):
            return

        mode = payload.get("mode", "")
        logger.info(f"Robot {self.robot_id} received mode change request: '{mode}'")
        
        # Handle 'stop' as a special command that stops movement but keeps current mode
        if mode == "stop":
            self._execute_stop()
            return
        
        # Normalize mode names: "run" -> "running", "walk" -> "walking", etc.
        mode_map = {
            "run": self.MODE_RUNNING,
            "walk": self.MODE_WALKING,
            "sit": self.MODE_SITTING,
            "stand": self.MODE_STANDING
        }
        normalized_mode = mode_map.get(mode, mode)
        
        # Execute the appropriate mode command
        if normalized_mode == self.MODE_SITTING:
            self._execute_sit()
        elif normalized_mode == self.MODE_STANDING:
            self._execute_stand()
        elif normalized_mode == self.MODE_WALKING:
            self._execute_walk()
        elif normalized_mode == self.MODE_RUNNING:
            self._execute_run()
        else:
            logger.warning(f"Robot {self.robot_id} received invalid mode: '{mode}' (normalized: '{normalized_mode}')")

    # Movement command implementations
    def _execute_sit(self) -> None:
        """Execute sit command."""
        self.mode = self.MODE_SITTING
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.status = self.STATUS_IDLE
        # Print and publish immediate update
        self._print_endpoint_values()
        self._publish_telemetry()

    def _execute_stand(self) -> None:
        """Execute stand command."""
        self.mode = self.MODE_STANDING
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.status = self.STATUS_IDLE
        # Print and publish immediate update
        self._print_endpoint_values()
        self._publish_telemetry()

    def _execute_walk(self) -> None:
        """Execute walk command."""
        self.mode = self.MODE_WALKING
        self.linear_velocity = self.SPEED_WALK
        self.angular_velocity = 0.0
        self.status = self.STATUS_MOVING
        # Print and publish immediate update
        self._print_endpoint_values()
        self._publish_telemetry()

    def _execute_run(self) -> None:
        """Execute run command."""
        self.mode = self.MODE_RUNNING
        self.linear_velocity = self.SPEED_RUN
        self.angular_velocity = 0.0
        self.status = self.STATUS_MOVING
        # Print and publish immediate update
        self._print_endpoint_values()
        self._publish_telemetry()

    def _execute_stop(self) -> None:
        """Execute stop command."""
        self.linear_velocity = 0.0
        self.angular_velocity = 0.0
        self.status = self.STATUS_IDLE

    def _execute_move_forward(self, params: Dict) -> None:
        """Execute move forward command."""
        if self.mode == self.MODE_SITTING:
            return

        distance = params.get("distance", 1.0)
        speed = self.SPEED_WALK if self.mode == self.MODE_WALKING else self.SPEED_RUN
        self.linear_velocity = speed
        self.angular_velocity = 0.0

    def _execute_move_backward(self, params: Dict) -> None:
        """Execute move backward command."""
        if self.mode == self.MODE_SITTING:
            return

        distance = params.get("distance", 1.0)
        speed = self.SPEED_WALK if self.mode == self.MODE_WALKING else self.SPEED_RUN
        self.linear_velocity = -speed
        self.angular_velocity = 0.0

    def _execute_turn_left(self, params: Dict) -> None:
        """Execute turn left command."""
        if self.mode == self.MODE_SITTING:
            return

        angle = params.get("angle", 90.0)  # degrees
        self.linear_velocity = 0.0
        self.angular_velocity = self.SPEED_TURN

    def _execute_turn_right(self, params: Dict) -> None:
        """Execute turn right command."""
        if self.mode == self.MODE_SITTING:
            return

        angle = params.get("angle", 90.0)  # degrees
        self.linear_velocity = 0.0
        self.angular_velocity = -self.SPEED_TURN

    def get_state(self) -> Dict:
        """Get current robot state as dictionary."""
        with self._lock:
            return {
                "robot_id": self.robot_id,
                "mode": self.mode,
                "status": self.status,
                "battery": round(self.battery, 2),
                "pose": {
                    "x": round(self.x, 3),
                    "y": round(self.y, 3),
                    "theta": round(self.theta, 3)
                },
                "gps": self.gps.to_dict(),
                "velocity": {
                    "linear": round(self.linear_velocity, 3),
                    "angular": round(self.angular_velocity, 3)
                }
            }

    def _get_joint_values_for_mode(self) -> list:
        """Get joint positions based on current mode with time-based variation."""
        import time
        time_factor = math.sin(time.time() * 2) * 0.1

        # Map internal mode names to joint template keys
        mode_map = {
            self.MODE_SITTING: "sit",
            self.MODE_STANDING: "stand",
            self.MODE_WALKING: "walk",
            self.MODE_RUNNING: "run"
        }

        mode_key = mode_map.get(self.mode, "stand")

        joints_templates = {
            "sit": [
                {"name": "neck", "dof": 3, "position": [0.0, -0.4, 0.0], "velocity": 0.0, "torque": 0.05, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.6 + time_factor * 0.05, 0.4, -0.3], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-0.6 - time_factor * 0.05, 0.4, -0.3], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "left_elbow", "dof": 3, "position": [0.1, -1.2, 0.1], "velocity": 0.0, "torque": 0.1, "status": "OK"},
                {"name": "right_elbow", "dof": 3, "position": [-0.1, -1.2, 0.1], "velocity": 0.0, "torque": 0.1, "status": "OK"},
                {"name": "left_wrist", "dof": 2, "position": [0.1, 0.05], "velocity": 0.0, "torque": 0.02, "status": "OK"},
                {"name": "right_wrist", "dof": 2, "position": [0.1, -0.05], "velocity": 0.0, "torque": 0.02, "status": "OK"},
                {"name": "left_gripper", "dof": 1, "position": [0.01], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "right_gripper", "dof": 1, "position": [0.01], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "hip", "dof": 3, "position": [0.0, 0.0, -1.4], "velocity": 0.0, "torque": 0.3, "status": "OK"},
                {"name": "left_hip", "dof": 3, "position": [0.0, -0.2, -0.5], "velocity": 0.0, "torque": 0.35, "status": "OK"},
                {"name": "right_hip", "dof": 3, "position": [0.0, 0.2, -0.5], "velocity": 0.0, "torque": 0.35, "status": "OK"},
                {"name": "left_knee", "dof": 2, "position": [1.5, 0.0], "velocity": 0.0, "torque": 0.25, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [1.5, 0.0], "velocity": 0.0, "torque": 0.25, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [-0.4, 0.0], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [-0.4, 0.0], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "left_foot", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.1, "status": "OK"},
                {"name": "right_foot", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.1, "status": "OK"}
            ],
            "stand": [
                {"name": "neck", "dof": 3, "position": [0.0, 0.0, 0.0], "velocity": 0.0, "torque": 0.08, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0], "velocity": 0.0, "torque": 0.3, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0], "velocity": 0.0, "torque": 0.3, "status": "OK"},
                {"name": "left_elbow", "dof": 3, "position": [0.0, -0.15, 0.0], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "right_elbow", "dof": 3, "position": [0.0, -0.15, 0.0], "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "left_wrist", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.02, "status": "OK"},
                {"name": "right_wrist", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.02, "status": "OK"},
                {"name": "left_gripper", "dof": 1, "position": [0.0], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "right_gripper", "dof": 1, "position": [0.0], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "hip", "dof": 3, "position": [0.0, 0.0, 0.0], "velocity": 0.0, "torque": 0.5, "status": "OK"},
                {"name": "left_hip", "dof": 3, "position": [0.0, -0.15, 0.0], "velocity": 0.0, "torque": 0.45, "status": "OK"},
                {"name": "right_hip", "dof": 3, "position": [0.0, 0.15, 0.0], "velocity": 0.0, "torque": 0.45, "status": "OK"},
                {"name": "left_knee", "dof": 2, "position": [0.05, 0.0], "velocity": 0.0, "torque": 0.4, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [0.05, 0.0], "velocity": 0.0, "torque": 0.4, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.3, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.3, "status": "OK"},
                {"name": "left_foot", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.2, "status": "OK"},
                {"name": "right_foot", "dof": 2, "position": [0.0, 0.0], "velocity": 0.0, "torque": 0.2, "status": "OK"}
            ],
            "walk": [
                {"name": "neck", "dof": 3, "position": [0.0, 0.15, 0.0], "velocity": 0.08, "torque": 0.12, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.5 + time_factor * 1.5, 0.3, -0.2], "velocity": 0.25, "torque": 0.5, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-0.5 - time_factor * 1.5, 0.3, -0.2], "velocity": 0.25, "torque": 0.5, "status": "OK"},
                {"name": "left_elbow", "dof": 3, "position": [0.1 + time_factor * 0.3, -0.6, 0.05], "velocity": 0.15, "torque": 0.25, "status": "OK"},
                {"name": "right_elbow", "dof": 3, "position": [-0.1 - time_factor * 0.3, -0.6, 0.05], "velocity": 0.15, "torque": 0.25, "status": "OK"},
                {"name": "left_wrist", "dof": 2, "position": [0.05, 0.03], "velocity": 0.08, "torque": 0.03, "status": "OK"},
                {"name": "right_wrist", "dof": 2, "position": [0.05, -0.03], "velocity": 0.08, "torque": 0.03, "status": "OK"},
                {"name": "left_gripper", "dof": 1, "position": [0.0], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "right_gripper", "dof": 1, "position": [0.0], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "hip", "dof": 3, "position": [0.0, 0.15, 0.0], "velocity": 0.1, "torque": 0.7, "status": "OK"},
                {"name": "left_hip", "dof": 3, "position": [0.3 + time_factor * 0.8, -0.15, 0.1], "velocity": 0.2, "torque": 0.6, "status": "OK"},
                {"name": "right_hip", "dof": 3, "position": [-0.3 - time_factor * 0.8, 0.15, 0.1], "velocity": 0.2, "torque": 0.6, "status": "OK"},
                {"name": "left_knee", "dof": 2, "position": [0.5 + time_factor * 0.8, 0.0], "velocity": 0.3, "torque": 0.65, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [0.2 - time_factor * 0.8, 0.0], "velocity": 0.3, "torque": 0.65, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [0.15 + time_factor * 0.2, 0.05], "velocity": 0.18, "torque": 0.45, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [-0.1 - time_factor * 0.2, -0.05], "velocity": 0.18, "torque": 0.45, "status": "OK"},
                {"name": "left_foot", "dof": 2, "position": [0.1, 0.0], "velocity": 0.15, "torque": 0.3, "status": "OK"},
                {"name": "right_foot", "dof": 2, "position": [-0.05, 0.0], "velocity": 0.15, "torque": 0.3, "status": "OK"}
            ],
            "run": [
                {"name": "neck", "dof": 3, "position": [0.0, 0.35 + time_factor * 0.1, 0.0], "velocity": 0.2, "torque": 0.22, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [1.4 + time_factor * 2.5, 0.6, -0.5], "velocity": 0.65, "torque": 1.1, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-1.4 - time_factor * 2.5, 0.6, -0.5], "velocity": 0.65, "torque": 1.1, "status": "OK"},
                {"name": "left_elbow", "dof": 3, "position": [0.3 + time_factor * 0.6, -1.4, 0.15], "velocity": 0.5, "torque": 0.6, "status": "OK"},
                {"name": "right_elbow", "dof": 3, "position": [-0.3 - time_factor * 0.6, -1.4, 0.15], "velocity": 0.5, "torque": 0.6, "status": "OK"},
                {"name": "left_wrist", "dof": 2, "position": [0.12, 0.08], "velocity": 0.2, "torque": 0.05, "status": "OK"},
                {"name": "right_wrist", "dof": 2, "position": [0.12, -0.08], "velocity": 0.2, "torque": 0.05, "status": "OK"},
                {"name": "left_gripper", "dof": 1, "position": [0.02], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "right_gripper", "dof": 1, "position": [0.02], "velocity": 0.0, "torque": 0.0, "status": "OK"},
                {"name": "hip", "dof": 3, "position": [0.0, 0.4 + time_factor * 0.15, 0.1], "velocity": 0.45, "torque": 1.5, "status": "OK"},
                {"name": "left_hip", "dof": 3, "position": [0.8 + time_factor * 1.5, -0.2, 0.3], "velocity": 0.6, "torque": 1.3, "status": "OK"},
                {"name": "right_hip", "dof": 3, "position": [-0.8 - time_factor * 1.5, 0.2, 0.3], "velocity": 0.6, "torque": 1.3, "status": "OK"},
                {"name": "left_knee", "dof": 2, "position": [1.2 + time_factor * 1.5, 0.1], "velocity": 0.75, "torque": 1.4, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [0.5 - time_factor * 1.5, -0.1], "velocity": 0.75, "torque": 1.4, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [0.5 + time_factor * 0.5, 0.12], "velocity": 0.6, "torque": 1.0, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [-0.3 - time_factor * 0.5, -0.12], "velocity": 0.6, "torque": 1.0, "status": "OK"},
                {"name": "left_foot", "dof": 2, "position": [0.25 + time_factor * 0.3, 0.08], "velocity": 0.5, "torque": 0.7, "status": "OK"},
                {"name": "right_foot", "dof": 2, "position": [-0.15 - time_factor * 0.3, -0.08], "velocity": 0.5, "torque": 0.7, "status": "OK"}
            ]
        }

        return joints_templates.get(mode_key, joints_templates["stand"])

    def _print_endpoint_values(self) -> None:
        """Print simulated values for all endpoints whenever robot controls change."""
        print("\n" + "=" * 80)
        print(f"ROBOT CONTROL CHANGE - UPDATED SIMULATED VALUES [{datetime.utcnow().isoformat()}Z]")
        print("=" * 80)

        # Status endpoint data
        print(f"\n[/robot/state/{self.robot_id}] - Robot State:")
        print(f"  Robot ID:    {self.robot_id}")
        print(f"  Mode:        {self.mode}")
        print(f"  Status:      {self.status}")
        print(f"  Battery:     {round(self.battery, 2)}%")

        # Pose endpoint data
        print(f"\n[/robot/{{robot_id}}/path] - Robot Pose:")
        print(f"  Position X:  {round(self.x, 3)} m")
        print(f"  Position Y:  {round(self.y, 3)} m")
        print(f"  Heading θ:   {round(self.theta, 3)} rad ({round(math.degrees(self.theta), 1)}°)")

        # GPS endpoint data
        print(f"\n[GPS Data] - Location:")
        print(f"  Latitude:    {self.gps.latitude:.6f}°")
        print(f"  Longitude:   {self.gps.longitude:.6f}°")

        # Velocity endpoint data (cmd_vel)
        print(f"\n[/robot/cmd_vel] - Velocity:")
        print(f"  Linear:      {round(self.linear_velocity, 3)} m/s")
        print(f"  Angular:     {round(self.angular_velocity, 3)} rad/s")

        # Joint values based on current mode
        joints = self._get_joint_values_for_mode()
        print(f"\n[/robot/joints/{self.robot_id}] - Joint States ({len(joints)} joints):")

        # Group joints by body part for better readability
        head_joints = [j for j in joints if 'neck' in j['name'].lower()]
        arm_joints = [j for j in joints if 'shoulder' in j['name'].lower() or 'elbow' in j['name'].lower() or 'wrist' in j['name'].lower() or 'gripper' in j['name'].lower()]
        leg_joints = [j for j in joints if 'hip' in j['name'].lower() or 'knee' in j['name'].lower() or 'ankle' in j['name'].lower()]

        if head_joints:
            print("  HEAD:")
            for joint in head_joints:
                pos_str = ", ".join([f"{p:.2f}" for p in joint['position']])
                print(f"    {joint['name']:20s} pos:[{pos_str}] vel:{joint['velocity']:.2f} torque:{joint['torque']:.2f}")

        if arm_joints:
            print("  ARMS:")
            for joint in arm_joints:
                pos_str = ", ".join([f"{p:.2f}" for p in joint['position']])
                print(f"    {joint['name']:20s} pos:[{pos_str}] vel:{joint['velocity']:.2f} torque:{joint['torque']:.2f}")

        if leg_joints:
            print("  LEGS:")
            for joint in leg_joints:
                pos_str = ", ".join([f"{p:.2f}" for p in joint['position']])
                print(f"    {joint['name']:20s} pos:[{pos_str}] vel:{joint['velocity']:.2f} torque:{joint['torque']:.2f}")

        # Mode-specific details
        print(f"\n[Robot Configuration]:")
        if self.mode == self.MODE_WALKING:
            print(f"  Walking speed: {self.SPEED_WALK} m/s")
            print(f"  Battery drain: 0.05%/s")
            print(f"  Moderate arm swing & leg movement")
        elif self.mode == self.MODE_RUNNING:
            print(f"  Running speed: {self.SPEED_RUN} m/s")
            print(f"  Battery drain: 0.1%/s")
            print(f"  DRAMATIC arm swing & leg stride!")
        elif self.mode == self.MODE_SITTING:
            print(f"  Sitting - relaxed posture")
            print(f"  Battery drain: 0.005%/s")
            print(f"  Minimal joint movement")
        elif self.mode == self.MODE_STANDING:
            print(f"  Standing - ready stance")
            print(f"  Battery drain: 0.01%/s")
            print(f"  Balanced & alert")

        print(f"\n  Turn speed:  {self.SPEED_TURN} rad/s")

        print("=" * 80 + "\n")
