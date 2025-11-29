from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession

from .database import ErrorLog
from .robot_state import robot_state_cache

logger = logging.getLogger(__name__)


class LoggingService:
    """Service for logging robot errors and system events."""

    async def log_robot_error(
        self,
        robot_id: str,
        error_type: str,
        error_message: str,
        severity: str = "ERROR",
        db_session: AsyncSession | None = None,
    ) -> None:
        """
        Log robot error to database and update state cache.

        Args:
            robot_id: Robot identifier
            error_type: Type of error (e.g., "NAVIGATION", "SENSOR", "COMMUNICATION")
            error_message: Detailed error message
            severity: Error severity level ("INFO", "WARNING", "ERROR", "CRITICAL")
            db_session: Optional database session
        """
        try:
            # Add to state cache
            robot_state_cache.add_error(robot_id, f"[{error_type}] {error_message}")

            # Log to database if session provided
            if db_session:
                error_log = ErrorLog(
                    robot_id=robot_id,
                    error_type=error_type,
                    error_message=error_message,
                    severity=severity,
                    timestamp=datetime.utcnow(),
                )
                db_session.add(error_log)
                await db_session.commit()

            # Log to application logger
            log_msg = f"Robot {robot_id} - {error_type}: {error_message}"
            if severity == "CRITICAL":
                logger.critical(log_msg)
            elif severity == "ERROR":
                logger.error(log_msg)
            elif severity == "WARNING":
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

        except Exception as e:
            logger.error(f"Failed to log robot error: {e}")
            if db_session:
                await db_session.rollback()

    async def process_error_message(
        self,
        robot_id: str,
        error_data: Dict[str, Any],
        db_session: AsyncSession,
    ) -> None:
        """
        Process error message from MQTT topic.

        Expected format:
        {
            "error_type": "NAVIGATION",
            "message": "Path planning failed",
            "severity": "ERROR"
        }
        """
        error_type = error_data.get("error_type", "UNKNOWN")
        error_message = error_data.get("message", "No message provided")
        severity = error_data.get("severity", "ERROR")

        await self.log_robot_error(
            robot_id=robot_id,
            error_type=error_type,
            error_message=error_message,
            severity=severity,
            db_session=db_session,
        )

    def clear_robot_errors(self, robot_id: str) -> None:
        """Clear error history for a robot."""
        robot_state_cache.clear_errors(robot_id)
        logger.info(f"Cleared errors for robot {robot_id}")


# Global instance
logging_service = LoggingService()
