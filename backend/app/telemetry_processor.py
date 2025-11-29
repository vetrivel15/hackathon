from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from .database import RobotPathLog, BatteryHistory, TelemetryLog
from .robot_state import robot_state_cache

logger = logging.getLogger(__name__)


class TelemetryProcessor:
    """Processes incoming robot telemetry and stores to database."""

    def __init__(self):
        self._last_db_write = {}  # Track last database write time per robot
        self._min_write_interval = 5.0  # Minimum seconds between database writes

    async def process_telemetry(
        self,
        robot_id: str,
        telemetry_data: Dict[str, Any],
        db_session: AsyncSession,
    ) -> None:
        """
        Process telemetry message from robot.

        Expected format:
        {
            "robot_id": "HUM-01",
            "mode": "TELEOP",
            "battery": 76,
            "pose": {"x": 2.1, "y": 1.3, "theta": 95},
            "status": "OK"
        }
        """
        try:
            # Always update in-memory cache
            robot_state_cache.update_state(robot_id, telemetry_data)

            # Throttle database writes to reduce lock contention
            import time
            current_time = time.time()
            last_write = self._last_db_write.get(robot_id, 0)
            
            if current_time - last_write < self._min_write_interval:
                # Skip database write, only update cache
                return
            
            self._last_db_write[robot_id] = current_time

            # Store complete telemetry snapshot
            telemetry_log = TelemetryLog(
                robot_id=robot_id,
                mode=telemetry_data.get("mode"),
                status=telemetry_data.get("status"),
                battery_level=telemetry_data.get("battery"),
                x=telemetry_data.get("pose", {}).get("x") if telemetry_data.get("pose") else None,
                y=telemetry_data.get("pose", {}).get("y") if telemetry_data.get("pose") else None,
                theta=telemetry_data.get("pose", {}).get("theta") if telemetry_data.get("pose") else None,
                raw_data=json.dumps(telemetry_data),
                timestamp=datetime.utcnow(),
            )
            db_session.add(telemetry_log)

            # Store path log if pose data exists
            if "pose" in telemetry_data and telemetry_data["pose"]:
                pose = telemetry_data["pose"]
                if all(k in pose for k in ["x", "y", "theta"]):
                    path_log = RobotPathLog(
                        robot_id=robot_id,
                        x=float(pose["x"]),
                        y=float(pose["y"]),
                        theta=float(pose["theta"]),
                        timestamp=datetime.utcnow(),
                    )
                    db_session.add(path_log)

            # Store battery history if battery data exists
            if "battery" in telemetry_data:
                battery_history = BatteryHistory(
                    robot_id=robot_id,
                    battery_level=float(telemetry_data["battery"]),
                    timestamp=datetime.utcnow(),
                )
                db_session.add(battery_history)

            await db_session.commit()
            logger.debug(f"Processed telemetry for robot {robot_id}")

        except Exception as e:
            logger.error(f"Error processing telemetry for {robot_id}: {e}")
            await db_session.rollback()
            raise

    async def process_pose(
        self,
        robot_id: str,
        pose_data: Dict[str, float],
        db_session: AsyncSession,
    ) -> None:
        """
        Process pose update from robot.

        Expected format:
        {
            "pose": {"x": 2.1, "y": 1.3, "theta": 95},
            "gps": {"latitude": 37.7, "longitude": -122.4}
        }
        """
        try:
            # Extract pose from nested structure if present
            pose = pose_data.get("pose", pose_data)
            
            if not all(k in pose for k in ["x", "y", "theta"]):
                # Don't warn, just skip - pose data comes in different formats
                return

            # Update cache
            state = robot_state_cache.get_state(robot_id)
            if state:
                state.pose.x = float(pose["x"])
                state.pose.y = float(pose["y"])
                state.pose.theta = float(pose["theta"])
                state.last_updated = datetime.utcnow()

            # Store to database (throttled like telemetry)
            import time
            current_time = time.time()
            last_write = self._last_db_write.get(f"{robot_id}_pose", 0)
            
            if current_time - last_write < self._min_write_interval:
                return
                
            self._last_db_write[f"{robot_id}_pose"] = current_time
            
            path_log = RobotPathLog(
                robot_id=robot_id,
                x=float(pose["x"]),
                y=float(pose["y"]),
                theta=float(pose["theta"]),
                timestamp=datetime.utcnow(),
            )
            db_session.add(path_log)
            await db_session.commit()

        except Exception as e:
            logger.error(f"Error processing pose for {robot_id}: {e}")
            await db_session.rollback()


# Global instance
telemetry_processor = TelemetryProcessor()
