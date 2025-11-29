from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional

import paho.mqtt.client as mqtt

from .config import settings

logger = logging.getLogger(__name__)


class CommandDispatcher:
    """Dispatches commands to robots via MQTT."""

    def __init__(self, mqtt_client: mqtt.Client) -> None:
        self._client = mqtt_client

    def send_cmd_vel(
        self,
        robot_id: str,
        linear: float,
        angular: float,
        qos: int = 0,
    ) -> None:
        """
        Send velocity command to robot.

        Args:
            robot_id: Target robot identifier
            linear: Linear velocity (m/s)
            angular: Angular velocity (rad/s)
            qos: MQTT QoS level
        """
        topic = f"{settings.robot_cmd_vel_topic}/{robot_id}"
        payload = {
            "cmd": "move",
            "linear": float(linear),
            "angular": float(angular),
            "timestamp": self._get_timestamp(),
        }

        self._publish(topic, payload, qos)
        logger.info(f"Sent cmd_vel to {robot_id}: linear={linear}, angular={angular}")

    def send_teleop_command(
        self,
        robot_id: str,
        command: str,
        params: Optional[Dict[str, Any]] = None,
        qos: int = 0,
    ) -> None:
        """
        Send teleop command to robot.

        Args:
            robot_id: Target robot identifier
            command: Command type (e.g., "move_forward", "stop", "turn_left")
            params: Optional command parameters
            qos: MQTT QoS level
        """
        topic = f"{settings.robot_teleop_topic}/{robot_id}"
        payload = {
            "cmd": command,
            "params": params or {},
            "timestamp": self._get_timestamp(),
        }

        self._publish(topic, payload, qos)
        logger.info(f"Sent teleop command to {robot_id}: {command}")

    def send_mode_switch(
        self,
        robot_id: str,
        mode: str,
        qos: int = 0,
    ) -> None:
        """
        Send mode switch command to robot.

        Args:
            robot_id: Target robot identifier
            mode: Target mode (e.g., "TELEOP", "AUTONOMOUS", "MANUAL")
            qos: MQTT QoS level
        """
        topic = f"{settings.robot_mode_topic}/{robot_id}"
        payload = {
            "mode": mode,
            "timestamp": self._get_timestamp(),
        }

        self._publish(topic, payload, qos)
        logger.info(f"Sent mode switch to {robot_id}: {mode}")

    def trigger_update(
        self,
        robot_id: str,
        update_type: str = "software",
        qos: int = 1,
    ) -> None:
        """
        Trigger software/firmware update on robot.

        Args:
            robot_id: Target robot identifier
            update_type: Type of update ("software", "firmware", "config")
            qos: MQTT QoS level (default 1 for reliability)
        """
        topic = f"{settings.robot_update_topic}/{robot_id}"
        payload = {
            "update_type": update_type,
            "timestamp": self._get_timestamp(),
        }

        self._publish(topic, payload, qos)
        logger.info(f"Triggered {update_type} update for {robot_id}")

    def send_emergency_stop(
        self,
        robot_id: str,
        qos: int = 2,
    ) -> None:
        """
        Send emergency stop command to robot.

        Args:
            robot_id: Target robot identifier
            qos: MQTT QoS level (default 2 for maximum reliability)
        """
        topic = f"{settings.robot_cmd_vel_topic}/{robot_id}"
        payload = {
            "cmd": "emergency_stop",
            "linear": 0.0,
            "angular": 0.0,
            "timestamp": self._get_timestamp(),
        }

        self._publish(topic, payload, qos)
        logger.warning(f"Sent EMERGENCY STOP to {robot_id}")

    def _publish(self, topic: str, payload: Dict[str, Any], qos: int) -> None:
        """Internal method to publish MQTT message."""
        try:
            message = json.dumps(payload)
            info = self._client.publish(topic, message, qos=qos, retain=False)
            info.wait_for_publish(timeout=5)
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            raise

    @staticmethod
    def _get_timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
