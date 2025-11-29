#!/usr/bin/env python3
"""
Continuous MQTT Publisher for Robot Telemetry
Publishes robot status, pose, joints, GPS, and other data continuously.
"""

import json
import sys
import time
import math
import threading
from datetime import datetime

import paho.mqtt.client as mqtt


class ContinuousRobotPublisher:
    """Continuously publishes robot telemetry data to MQTT topics."""

    def __init__(self, mqtt_host: str = "localhost", mqtt_port: int = 1883, robot_id: str = "robot_01"):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.robot_id = robot_id
        self.client = mqtt.Client(client_id=f"continuous-publisher-{robot_id}", clean_session=True)
        self.client.on_connect = self._on_connect
        self.connected = False
        self.running = False

        # Robot state
        self.current_mode = "stand"
        self.current_gps = {"latitude": 37.7749, "longitude": -122.4194, "altitude": 10.0}
        self.current_heading = 0.0
        self.battery = 100.0
        self.position = {"x": 0.0, "y": 0.0, "z": 0.0}
        self.theta = 0.0
        self.velocity = {"linear": 0.0, "angular": 0.0}
        self.status = "OPERATIONAL"

        # Publishing intervals (seconds)
        self.publish_intervals = {
            "status": 2.0,
            "pose": 0.5,
            "joints": 1.0,
            "gps": 1.0,
        }

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print(f"[✓] Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            self.connected = True
        else:
            print(f"[✗] Connection failed with code {rc}")
            self.connected = False

    def connect(self):
        """Connect to MQTT broker."""
        print(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}...")
        try:
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()
            time.sleep(1)
            return self.connected
        except Exception as e:
            print(f"[✗] Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker."""
        self.running = False
        time.sleep(1)
        self.client.loop_stop()
        self.client.disconnect()
        print("[✓] Disconnected from MQTT broker")

    def get_joints_for_mode(self, mode: str) -> dict:
        """Get joint positions based on current mode."""
        # Add some variation based on time for realistic movement
        time_factor = math.sin(time.time() * 2) * 0.1

        joints_templates = {
            "sit": [
                {"name": "neck", "dof": 3, "position": [0.0, -0.3, 0.0],
                 "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                 "velocity": 0.0, "torque": 0.05, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.5 + time_factor, 0.3, -0.2],
                 "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                 "velocity": 0.0, "torque": 0.15, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-0.5 - time_factor, 0.3, -0.2],
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
            ],
            "stand": [
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
            ],
            "walk": [
                {"name": "neck", "dof": 3, "position": [0.0, 0.1, 0.0],
                 "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                 "velocity": 0.05, "torque": 0.1, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.3 + time_factor, 0.2, -0.1],
                 "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                 "velocity": 0.1, "torque": 0.4, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-0.3 - time_factor, 0.2, -0.1],
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
                {"name": "left_knee", "dof": 2, "position": [0.3 + time_factor * 0.5, 0.0],
                 "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                 "velocity": 0.15, "torque": 0.5, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [0.1 - time_factor * 0.5, 0.0],
                 "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                 "velocity": 0.15, "torque": 0.5, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [0.1, 0.0],
                 "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                 "velocity": 0.1, "torque": 0.35, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [-0.05, 0.0],
                 "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                 "velocity": 0.1, "torque": 0.35, "status": "OK"}
            ],
            "run": [
                {"name": "neck", "dof": 3, "position": [0.0, 0.2, 0.0],
                 "position_limits": {"min": [-1.57, -1.0, -0.7], "max": [1.57, 1.0, 0.7]},
                 "velocity": 0.1, "torque": 0.15, "status": "OK"},
                {"name": "left_shoulder", "dof": 3, "position": [0.8 + time_factor, 0.4, -0.3],
                 "position_limits": {"min": [-2.0, -2.0, -1.5], "max": [2.0, 1.5, 1.5]},
                 "velocity": 0.3, "torque": 0.7, "status": "OK"},
                {"name": "right_shoulder", "dof": 3, "position": [-0.8 - time_factor, 0.4, -0.3],
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
                {"name": "left_knee", "dof": 2, "position": [0.8 + time_factor, 0.0],
                 "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                 "velocity": 0.4, "torque": 0.9, "status": "OK"},
                {"name": "right_knee", "dof": 2, "position": [0.3 - time_factor, 0.0],
                 "position_limits": {"min": [-0.2, -0.2], "max": [1.57, 0.9]},
                 "velocity": 0.4, "torque": 0.9, "status": "OK"},
                {"name": "left_ankle", "dof": 2, "position": [0.3, 0.05],
                 "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                 "velocity": 0.3, "torque": 0.6, "status": "OK"},
                {"name": "right_ankle", "dof": 2, "position": [-0.15, -0.05],
                 "position_limits": {"min": [-0.7, -0.4], "max": [0.7, 0.4]},
                 "velocity": 0.3, "torque": 0.6, "status": "OK"}
            ],
            "stop": [
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

        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "frame_id": "base_link",
            "joints": joints_templates.get(mode, joints_templates["stand"])
        }

    def publish_status(self):
        """Publish robot status."""
        topic = f"robot/status/{self.robot_id}"
        payload = {
            "robot_id": self.robot_id,
            "status": self.status,
            "mode": self.current_mode,
            "battery": self.battery,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.publish(topic, json.dumps(payload), qos=0)
        print(f"[PUB] Status: mode={self.current_mode}, battery={self.battery:.1f}%")

    def publish_pose(self):
        """Publish robot pose."""
        topic = f"robot/pose/{self.robot_id}"
        payload = {
            "robot_id": self.robot_id,
            "pose": {
                "x": self.position["x"],
                "y": self.position["y"],
                "z": self.position["z"],
                "theta": self.theta
            },
            "velocity": self.velocity,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.publish(topic, json.dumps(payload), qos=0)
        print(f"[PUB] Pose: x={self.position['x']:.2f}, y={self.position['y']:.2f}, θ={self.theta:.2f}rad")

    def publish_joints(self):
        """Publish robot joint data."""
        topic = f"robot/joints/{self.robot_id}"
        payload = self.get_joints_for_mode(self.current_mode)
        self.client.publish(topic, json.dumps(payload), qos=0)
        print(f"[PUB] Joints: {len(payload['joints'])} joints in {self.current_mode} mode")

    def publish_gps(self):
        """Publish GPS coordinates."""
        topic = f"robot/gps/{self.robot_id}"
        payload = {
            "latitude": self.current_gps["latitude"],
            "longitude": self.current_gps["longitude"],
            "altitude": self.current_gps["altitude"],
            "heading": self.current_heading,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.publish(topic, json.dumps(payload), qos=0)
        print(f"[PUB] GPS: Lat={self.current_gps['latitude']:.6f}, Lon={self.current_gps['longitude']:.6f}")

    def publish_mode(self):
        """Publish mode change."""
        topic = f"robot/mode/{self.robot_id}"
        payload = {
            "mode": self.current_mode,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.client.publish(topic, json.dumps(payload), qos=0)
        print(f"[PUB] Mode: {self.current_mode}")

    def update_simulation(self):
        """Update simulation state (battery drain, movement, etc.)."""
        # Slowly drain battery
        self.battery = max(0, self.battery - 0.01)

        # Update position based on mode
        if self.current_mode == "walk":
            self.position["x"] += 0.01 * math.cos(self.theta)
            self.position["y"] += 0.01 * math.sin(self.theta)
            self.velocity["linear"] = 0.5
            self.current_gps["latitude"] += 0.000001
        elif self.current_mode == "run":
            self.position["x"] += 0.05 * math.cos(self.theta)
            self.position["y"] += 0.05 * math.sin(self.theta)
            self.velocity["linear"] = 1.5
            self.current_gps["latitude"] += 0.000005
        else:
            self.velocity["linear"] = 0.0
            self.velocity["angular"] = 0.0

    def publisher_thread(self, topic_type: str, interval: float):
        """Thread for publishing specific topic."""
        last_publish = 0
        while self.running:
            current_time = time.time()
            if current_time - last_publish >= interval:
                if topic_type == "status":
                    self.publish_status()
                elif topic_type == "pose":
                    self.publish_pose()
                elif topic_type == "joints":
                    self.publish_joints()
                elif topic_type == "gps":
                    self.publish_gps()
                last_publish = current_time
            time.sleep(0.1)

    def run(self):
        """Start continuous publishing."""
        if not self.connect():
            return

        self.running = True

        print("\n" + "=" * 60)
        print("CONTINUOUS PUBLISHER STARTED")
        print("=" * 60)
        print(f"Robot ID: {self.robot_id}")
        print(f"Publishing to topics:")
        print(f"  - robot/status/{self.robot_id} (every {self.publish_intervals['status']}s)")
        print(f"  - robot/pose/{self.robot_id} (every {self.publish_intervals['pose']}s)")
        print(f"  - robot/joints/{self.robot_id} (every {self.publish_intervals['joints']}s)")
        print(f"  - robot/gps/{self.robot_id} (every {self.publish_intervals['gps']}s)")
        print("\nPress Ctrl+C to stop")
        print("=" * 60 + "\n")

        # Publish initial mode
        self.publish_mode()

        # Start publisher threads
        threads = []
        for topic_type, interval in self.publish_intervals.items():
            thread = threading.Thread(target=self.publisher_thread, args=(topic_type, interval), daemon=True)
            thread.start()
            threads.append(thread)

        try:
            # Main loop for simulation updates
            while self.running:
                self.update_simulation()
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\nStopping publisher...")
        finally:
            self.disconnect()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Continuous Robot Telemetry Publisher")
    parser.add_argument("--host", default="localhost", help="MQTT broker host (default: localhost)")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port (default: 1883)")
    parser.add_argument("--robot-id", default="robot_01", help="Robot ID (default: robot_01)")
    parser.add_argument("--mode", default="stand", choices=["sit", "stand", "walk", "run", "stop"],
                        help="Initial mode (default: stand)")
    args = parser.parse_args()

    publisher = ContinuousRobotPublisher(mqtt_host=args.host, mqtt_port=args.port, robot_id=args.robot_id)
    publisher.current_mode = args.mode
    publisher.run()


if __name__ == "__main__":
    main()
