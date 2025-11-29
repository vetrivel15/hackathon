from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class RobotPose:
    """Robot position and orientation."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


@dataclass
class RobotState:
    """Complete robot state snapshot."""
    robot_id: str
    mode: str = "UNKNOWN"
    status: str = "UNKNOWN"
    battery: float = 0.0
    pose: RobotPose = field(default_factory=RobotPose)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    errors: list[str] = field(default_factory=list)

    def update_from_telemetry(self, data: Dict) -> None:
        """Update state from telemetry message."""
        if "mode" in data:
            self.mode = data["mode"]
        if "status" in data:
            self.status = data["status"]
        if "battery" in data:
            self.battery = float(data["battery"])
        if "pose" in data:
            pose_data = data["pose"]
            self.pose.x = float(pose_data.get("x", 0.0))
            self.pose.y = float(pose_data.get("y", 0.0))
            self.pose.theta = float(pose_data.get("theta", 0.0))
        self.last_updated = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "robot_id": self.robot_id,
            "mode": self.mode,
            "status": self.status,
            "battery": self.battery,
            "pose": {
                "x": self.pose.x,
                "y": self.pose.y,
                "theta": self.pose.theta,
            },
            "last_updated": self.last_updated.isoformat() + "Z",
            "errors": self.errors,
        }


class RobotStateCache:
    """Thread-safe cache for robot states."""

    def __init__(self) -> None:
        self._states: Dict[str, RobotState] = {}
        self._lock = threading.Lock()

    def get_state(self, robot_id: str) -> Optional[RobotState]:
        """Get cached state for a robot."""
        with self._lock:
            return self._states.get(robot_id)

    def update_state(self, robot_id: str, telemetry: Dict) -> RobotState:
        """Update or create robot state from telemetry data."""
        with self._lock:
            if robot_id not in self._states:
                self._states[robot_id] = RobotState(robot_id=robot_id)

            state = self._states[robot_id]
            state.update_from_telemetry(telemetry)
            return state

    def add_error(self, robot_id: str, error: str) -> None:
        """Add an error to robot's error list."""
        with self._lock:
            if robot_id not in self._states:
                self._states[robot_id] = RobotState(robot_id=robot_id)

            # Keep only last 10 errors
            if len(self._states[robot_id].errors) >= 10:
                self._states[robot_id].errors.pop(0)

            self._states[robot_id].errors.append(error)

    def get_all_states(self) -> Dict[str, Dict]:
        """Get all robot states as dictionaries."""
        with self._lock:
            return {
                robot_id: state.to_dict()
                for robot_id, state in self._states.items()
            }

    def clear_errors(self, robot_id: str) -> None:
        """Clear error list for a robot."""
        with self._lock:
            if robot_id in self._states:
                self._states[robot_id].errors.clear()


# Global instance
robot_state_cache = RobotStateCache()
