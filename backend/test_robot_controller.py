#!/usr/bin/env python3
"""
Test Console Application for Robot Control
Allows manual control of simulated robots via MQTT commands.
"""

import json
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt


class RobotController:
    """Console application for controlling robots via MQTT."""

    def __init__(self, mqtt_host: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = mqtt.Client(client_id="robot-controller-console", clean_session=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.connected = False

        # Robot state tracking
        self.current_mode = "stand"
        self.current_gps = {"latitude": 37.7749, "longitude": -122.4194, "altitude": 10.0}
        self.current_heading = 0.0  # degrees, 0 = North

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print(f"[✓] Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            self.connected = True
        else:
            print(f"[✗] Connection failed with code {rc}")
            self.connected = False

    def _on_message(self, client, userdata, msg):
        """Callback for received messages."""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"\n[RESPONSE] Topic: {msg.topic}")
            print(f"           Payload: {json.dumps(payload, indent=2)}")
        except Exception as e:
            print(f"\n[RESPONSE] Topic: {msg.topic}")
            print(f"           Payload: {msg.payload.decode()}")

    def connect(self):
        """Connect to MQTT broker."""
        print(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}...")
        try:
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection
            return self.connected
        except Exception as e:
            print(f"[✗] Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()
        print("[✓] Disconnected from MQTT broker")

    def get_joints_for_mode(self, mode: str) -> dict:
        """Get joint positions based on current mode."""
        joints_templates = {
            "sit": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_id": "base_link",
                "joints": [
                    {"name": "neck", "dof": 3, "position": [0.0, -0.3, 0.0],
                     "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.05, "status": "OK"},
                    {"name": "left_shoulder", "dof": 3, "position": [0.5, 0.3, -0.2],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "right_shoulder", "dof": 3, "position": [-0.5, 0.3, -0.2],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "left_elbow", "dof": 3, "position": [0.0, -0.8, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.1, "status": "OK"},
                    {"name": "right_elbow", "dof": 3, "position": [0.0, -0.8, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.1, "status": "OK"},
                    {"name": "left_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "right_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "left_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "right_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "hip", "dof": 3, "position": [0.0, 0.0, -1.2],
                     "position_limits": {"min": [-1.5, -1.5, -0.7], "max": [1.5, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "left_knee", "dof": 2, "position": [1.4, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.25, "status": "OK"},
                    {"name": "right_knee", "dof": 2, "position": [1.4, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.25, "status": "OK"},
                    {"name": "left_ankle", "dof": 2, "position": [-0.3, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "right_ankle", "dof": 2, "position": [-0.3, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"}
                ]
            },
            "stand": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_id": "base_link",
                "joints": [
                    {"name": "neck", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.08, "status": "OK"},
                    {"name": "left_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "right_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "left_elbow", "dof": 3, "position": [0.0, -0.1, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "right_elbow", "dof": 3, "position": [0.0, -0.1, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "left_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "right_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "left_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "right_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "hip", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5, -0.7], "max": [1.5, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.5, "status": "OK"},
                    {"name": "left_knee", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.4, "status": "OK"},
                    {"name": "right_knee", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.4, "status": "OK"},
                    {"name": "left_ankle", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "right_ankle", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"}
                ]
            },
            "walk": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_id": "base_link",
                "joints": [
                    {"name": "neck", "dof": 3, "position": [0.0, 0.1, 0.0],
                     "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                     "velocity": 0.05, "torque": 0.1, "status": "OK"},
                    {"name": "left_shoulder", "dof": 3, "position": [0.3, 0.2, -0.1],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.1, "torque": 0.4, "status": "OK"},
                    {"name": "right_shoulder", "dof": 3, "position": [-0.3, 0.2, -0.1],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.1, "torque": 0.4, "status": "OK"},
                    {"name": "left_elbow", "dof": 3, "position": [0.05, -0.4, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.08, "torque": 0.2, "status": "OK"},
                    {"name": "right_elbow", "dof": 3, "position": [-0.05, -0.4, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.08, "torque": 0.2, "status": "OK"},
                    {"name": "left_wrist", "dof": 2, "position": [0.02, 0.02],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.03, "torque": 0.02, "status": "OK"},
                    {"name": "right_wrist", "dof": 2, "position": [0.02, -0.02],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.03, "torque": 0.02, "status": "OK"},
                    {"name": "left_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "right_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "hip", "dof": 3, "position": [0.0, 0.1, 0.0],
                     "position_limits": {"min": [-1.5, -1.5, -0.7], "max": [1.5, 1.0, 0.7]},
                     "velocity": 0.05, "torque": 0.6, "status": "OK"},
                    {"name": "left_knee", "dof": 2, "position": [0.3, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.15, "torque": 0.5, "status": "OK"},
                    {"name": "right_knee", "dof": 2, "position": [0.1, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.15, "torque": 0.5, "status": "OK"},
                    {"name": "left_ankle", "dof": 2, "position": [0.1, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.1, "torque": 0.35, "status": "OK"},
                    {"name": "right_ankle", "dof": 2, "position": [-0.05, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.1, "torque": 0.35, "status": "OK"}
                ]
            },
            "run": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_id": "base_link",
                "joints": [
                    {"name": "neck", "dof": 3, "position": [0.0, 0.2, 0.0],
                     "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                     "velocity": 0.1, "torque": 0.15, "status": "OK"},
                    {"name": "left_shoulder", "dof": 3, "position": [0.8, 0.4, -0.3],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.3, "torque": 0.7, "status": "OK"},
                    {"name": "right_shoulder", "dof": 3, "position": [-0.8, 0.4, -0.3],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.3, "torque": 0.7, "status": "OK"},
                    {"name": "left_elbow", "dof": 3, "position": [0.1, -0.8, 0.05],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.2, "torque": 0.35, "status": "OK"},
                    {"name": "right_elbow", "dof": 3, "position": [-0.1, -0.8, 0.05],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.2, "torque": 0.35, "status": "OK"},
                    {"name": "left_wrist", "dof": 2, "position": [0.05, 0.05],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.08, "torque": 0.03, "status": "OK"},
                    {"name": "right_wrist", "dof": 2, "position": [0.05, -0.05],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.08, "torque": 0.03, "status": "OK"},
                    {"name": "left_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "right_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "hip", "dof": 3, "position": [0.0, 0.3, 0.0],
                     "position_limits": {"min": [-1.5, -1.5, -0.7], "max": [1.5, 1.0, 0.7]},
                     "velocity": 0.2, "torque": 1.0, "status": "OK"},
                    {"name": "left_knee", "dof": 2, "position": [0.8, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.4, "torque": 0.9, "status": "OK"},
                    {"name": "right_knee", "dof": 2, "position": [0.3, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.4, "torque": 0.9, "status": "OK"},
                    {"name": "left_ankle", "dof": 2, "position": [0.3, 0.05],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.3, "torque": 0.6, "status": "OK"},
                    {"name": "right_ankle", "dof": 2, "position": [-0.15, -0.05],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.3, "torque": 0.6, "status": "OK"}
                ]
            },
            "stop": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "frame_id": "base_link",
                "joints": [
                    {"name": "neck", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.08, "status": "OK"},
                    {"name": "left_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "right_shoulder", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "left_elbow", "dof": 3, "position": [0.0, -0.1, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "right_elbow", "dof": 3, "position": [0.0, -0.1, 0.0],
                     "position_limits": {"min": [-2.0, -2.5, -1.0], "max": [2.0, 0.5, 1.0]},
                     "velocity": 0.0, "torque": 0.15, "status": "OK"},
                    {"name": "left_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "right_wrist", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5], "max": [1.5, 1.5]},
                     "velocity": 0.0, "torque": 0.02, "status": "OK"},
                    {"name": "left_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "right_gripper", "dof": 1, "position": [0.0],
                     "position_limits": {"min": [0.0], "max": [0.04]},
                     "velocity": 0.0, "torque": 0.0, "status": "OK"},
                    {"name": "hip", "dof": 3, "position": [0.0, 0.0, 0.0],
                     "position_limits": {"min": [-1.5, -1.5, -0.7], "max": [1.5, 1.0, 0.7]},
                     "velocity": 0.0, "torque": 0.5, "status": "OK"},
                    {"name": "left_knee", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.4, "status": "OK"},
                    {"name": "right_knee", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                     "velocity": 0.0, "torque": 0.4, "status": "OK"},
                    {"name": "left_ankle", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"},
                    {"name": "right_ankle", "dof": 2, "position": [0.0, 0.0],
                     "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                     "velocity": 0.0, "torque": 0.3, "status": "OK"}
                ]
            }
        }
        return joints_templates.get(mode, joints_templates["stand"])

    def update_gps_position(self, direction: str, distance: float = 0.0001):
        """Update GPS coordinates based on movement direction."""
        import math

        if direction == "forward":
            # Move in current heading direction
            lat_change = distance * math.cos(math.radians(self.current_heading))
            lon_change = distance * math.sin(math.radians(self.current_heading))
            self.current_gps["latitude"] += lat_change
            self.current_gps["longitude"] += lon_change

        elif direction == "backward":
            # Move opposite to current heading
            lat_change = distance * math.cos(math.radians(self.current_heading))
            lon_change = distance * math.sin(math.radians(self.current_heading))
            self.current_gps["latitude"] -= lat_change
            self.current_gps["longitude"] -= lon_change

        elif direction == "left":
            # Turn left (counter-clockwise)
            self.current_heading = (self.current_heading - 90) % 360

        elif direction == "right":
            # Turn right (clockwise)
            self.current_heading = (self.current_heading + 90) % 360

    def send_mode_switch(self, robot_id: str, mode: str):
        """Send mode switch command and update joints/GPS."""
        self.current_mode = mode

        # Send mode change
        topic = f"robot/mode/{robot_id}"
        payload = {
            "mode": mode,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        result = self.client.publish(topic, json.dumps(payload), qos=0)
        result.wait_for_publish(timeout=5)
        print(f"[✓] Switched robot '{robot_id}' to mode '{mode}'")

        # Send corresponding joint positions
        joints_data = self.get_joints_for_mode(mode)
        self.send_joints_data(robot_id, joints_data)

    def send_joints_data(self, robot_id: str, joints_data: dict):
        """Send joint information for the robot."""
        topic = f"robot/joints/{robot_id}"
        payload = joints_data
        if "timestamp" not in payload:
            payload["timestamp"] = datetime.utcnow().isoformat() + "Z"

        result = self.client.publish(topic, json.dumps(payload), qos=0)
        result.wait_for_publish(timeout=5)
        print(f"[✓] Sent joints data for robot '{robot_id}' ({len(payload.get('joints', []))} joints)")

    def send_gps_data(self, robot_id: str):
        """Send current GPS coordinates for the robot."""
        topic = f"robot/gps/{robot_id}"
        payload = {
            "latitude": self.current_gps["latitude"],
            "longitude": self.current_gps["longitude"],
            "altitude": self.current_gps["altitude"],
            "heading": self.current_heading,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        result = self.client.publish(topic, json.dumps(payload), qos=0)
        result.wait_for_publish(timeout=5)
        print(f"[✓] GPS: Lat={self.current_gps['latitude']:.6f}, Lon={self.current_gps['longitude']:.6f}, Heading={self.current_heading:.1f}°")

    def send_movement_command(self, robot_id: str, direction: str, distance: float = 1.0):
        """Send movement command and update GPS/joints accordingly."""
        # Update GPS based on movement
        if direction in ["forward", "backward"]:
            self.update_gps_position(direction, distance * 0.00001)  # Scale for GPS
        elif direction in ["left", "right"]:
            self.update_gps_position(direction)

        # Send teleop command
        topic = f"robot/teleop/{robot_id}"
        payload = {
            "cmd": f"move_{direction}",
            "params": {"distance": distance} if direction in ["forward", "backward"] else {"angle": 90},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        result = self.client.publish(topic, json.dumps(payload), qos=0)
        result.wait_for_publish(timeout=5)
        print(f"[✓] Sent movement command: {direction}")

        # Send updated GPS
        self.send_gps_data(robot_id)

        # Send joints for current mode (movement affects joint positions slightly)
        joints_data = self.get_joints_for_mode(self.current_mode)
        self.send_joints_data(robot_id, joints_data)

    def print_menu(self):
        """Print the control menu."""
        print("\n" + "=" * 60)
        print("ROBOT CONTROLLER - Main Menu")
        print("=" * 60)
        print(f"\nCurrent Mode: {self.current_mode.upper()}")
        print(f"Current GPS: Lat={self.current_gps['latitude']:.6f}, Lon={self.current_gps['longitude']:.6f}")
        print(f"Current Heading: {self.current_heading:.1f}°")
        print("\nMode Commands:")
        print("  1. Sit Mode")
        print("  2. Stand Mode")
        print("  3. Walk Mode")
        print("  4. Run Mode")
        print("  5. Stop Mode")
        print("\nMovement Commands:")
        print("  6. Move Forward")
        print("  7. Move Backward")
        print("  8. Turn Left")
        print("  9. Turn Right")
        print("\nOther:")
        print("  10. Change Robot ID")
        print("  0. Exit")
        print("=" * 60)

    def run(self):
        """Run the interactive console."""
        if not self.connect():
            return

        current_robot_id = "robot_01"
        print(f"\nCurrent Robot ID: {current_robot_id}")

        # Send initial state
        self.send_mode_switch(current_robot_id, self.current_mode)
        self.send_gps_data(current_robot_id)

        try:
            while True:
                self.print_menu()
                choice = input(f"\nEnter command (Robot: {current_robot_id}): ").strip()

                if choice == "0":
                    print("Exiting...")
                    break

                elif choice == "1":
                    self.send_mode_switch(current_robot_id, "sit")
                    self.send_gps_data(current_robot_id)

                elif choice == "2":
                    self.send_mode_switch(current_robot_id, "stand")
                    self.send_gps_data(current_robot_id)

                elif choice == "3":
                    self.send_mode_switch(current_robot_id, "walk")
                    self.send_gps_data(current_robot_id)

                elif choice == "4":
                    self.send_mode_switch(current_robot_id, "run")
                    self.send_gps_data(current_robot_id)

                elif choice == "5":
                    self.send_mode_switch(current_robot_id, "stop")
                    self.send_gps_data(current_robot_id)

                elif choice == "6":
                    distance = input("  Enter distance (meters, default=1.0): ").strip()
                    distance = float(distance) if distance else 1.0
                    self.send_movement_command(current_robot_id, "forward", distance)

                elif choice == "7":
                    distance = input("  Enter distance (meters, default=1.0): ").strip()
                    distance = float(distance) if distance else 1.0
                    self.send_movement_command(current_robot_id, "backward", distance)

                elif choice == "8":
                    self.send_movement_command(current_robot_id, "left")

                elif choice == "9":
                    self.send_movement_command(current_robot_id, "right")

                elif choice == "10":
                    new_id = input("  Enter new robot ID: ").strip()
                    if new_id:
                        current_robot_id = new_id
                        print(f"[✓] Changed to robot '{current_robot_id}'")
                        # Send current state to new robot
                        self.send_mode_switch(current_robot_id, self.current_mode)
                        self.send_gps_data(current_robot_id)

                else:
                    print("[✗] Invalid choice")

                time.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        finally:
            self.disconnect()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Robot Controller Console")
    parser.add_argument("--host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    args = parser.parse_args()

    print("=" * 60)
    print("ROBOT CONTROLLER - Test Console Application")
    print("=" * 60)
    print(f"MQTT Broker: {args.host}:{args.port}")
    print("=" * 60)

    controller = RobotController(mqtt_host=args.host, mqtt_port=args.port)
    controller.run()


if __name__ == "__main__":
    main()
