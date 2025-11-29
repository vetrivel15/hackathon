from __future__ import annotations

from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration sourced from environment variables."""

    # MQTT Broker Configuration
    mqtt_host: str = Field(default="mqtt-broker", description="MQTT broker hostname")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_username: str | None = Field(default=None, description="Optional MQTT username")
    mqtt_password: str | None = Field(default=None, description="Optional MQTT password")
    mqtt_client_id: str = Field(default="s4-backend", description="Client ID for MQTT connection")

    # Robot MQTT Topics
    robot_status_topic: str = Field(default="robot/status", description="Topic for robot status updates")
    robot_pose_topic: str = Field(default="robot/pose", description="Topic for robot pose updates")
    robot_cmd_vel_topic: str = Field(default="robot/cmd_vel", description="Topic for velocity commands")
    robot_teleop_topic: str = Field(default="robot/teleop", description="Topic for teleop commands")
    robot_errors_topic: str = Field(default="robot/errors", description="Topic for robot errors")
    robot_mode_topic: str = Field(default="robot/mode", description="Topic for mode switching")
    robot_update_topic: str = Field(default="robot/update", description="Topic for update triggers")

    # Legacy topics (for backward compatibility)
    mqtt_base_topic: str = Field(default="frontend/events", description="Base topic for events coming from the UI")
    mqtt_dummy_topic: str = Field(default="simulator/telemetry", description="Topic used for dummy telemetry")
    mqtt_default_subscriptions: List[str] = Field(
        default_factory=lambda: [
            "frontend/events/#",
            "simulator/#",
            "robot/status/#",
            "robot/pose/#",
            "robot/errors/#",
        ],
        description="Topics the backend subscribes to on startup",
    )

    # Application Settings
    max_recorded_events: int = Field(default=250, description="How many events to keep in memory")
    dummy_publish_interval: float = Field(default=5.0, description="Seconds between dummy telemetry messages")
    dummy_publish_enabled: bool = Field(default=True, description="Toggle periodic dummy publishing")

    # API Settings
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000)

    # Database Settings
    database_path: str = Field(default="./data/robot_telemetry.db", description="SQLite database file path")
    database_echo: bool = Field(default=False, description="Enable SQLAlchemy query logging")

    # Robot Simulator Settings
    enable_robot_simulator: bool = Field(default=True, description="Enable built-in robot simulator on startup")
    num_simulated_robots: int = Field(default=1, description="Number of robots to simulate")
    simulator_center_lat: float = Field(default=37.7749, description="Center latitude for robot spawning")
    simulator_center_lon: float = Field(default=-122.4194, description="Center longitude for robot spawning")
    simulator_spawn_radius: float = Field(default=5.0, description="Spawn radius in kilometers")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
