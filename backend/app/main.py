from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .mqtt_manager import mqtt_manager
from .command_dispatcher import CommandDispatcher
from .telemetry_processor import telemetry_processor
from .logging_service import logging_service
from .robot_state import robot_state_cache
from .websocket_server import ws_manager
from .database import get_db, init_db, close_db, RobotPathLog, BatteryHistory, ErrorLog, TelemetryLog
from .robot_simulator import RobotSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Pydantic models for API requests
class PublishRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    qos: int = Field(default=0, ge=0, le=2)


class SubscribeRequest(BaseModel):
    topic: str = Field(..., min_length=1)
    qos: int = Field(default=0, ge=0, le=2)


class DummyPublishRequest(BaseModel):
    device_ids: List[str] = Field(default_factory=lambda: ["device-A"])
    count: int = Field(default=1, ge=1, le=50)


class CommandVelocityRequest(BaseModel):
    robot_id: str = Field(..., min_length=1)
    linear: float = Field(..., ge=-5.0, le=5.0)
    angular: float = Field(..., ge=-5.0, le=5.0)


class TeleopCommandRequest(BaseModel):
    robot_id: str = Field(..., min_length=1)
    command: str = Field(..., min_length=1)
    params: Optional[Dict[str, Any]] = None


class ModeSwitchRequest(BaseModel):
    robot_id: str = Field(..., min_length=1)
    mode: str = Field(..., min_length=1)


class UpdateTriggerRequest(BaseModel):
    robot_id: str = Field(..., min_length=1)
    update_type: str = Field(default="software")


# Initialize FastAPI app
app = FastAPI(
    title="S4 Robot Backend",
    version="1.0.0",
    description="Python backend with MQTT for robot teleoperation and telemetry"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global command dispatcher instance
command_dispatcher: Optional[CommandDispatcher] = None

# Global robot simulators
robot_simulators: List[RobotSimulator] = []


# MQTT Message Handlers
async def handle_robot_status(topic: str, payload: Any) -> None:
    """Handle robot status messages."""
    try:
        if not isinstance(payload, dict):
            return

        # Extract robot_id from topic (e.g., robot/status/HUM-01)
        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        # Process telemetry
        async for db in get_db():
            await telemetry_processor.process_telemetry(robot_id, payload, db)
            break

        # Broadcast to WebSocket clients (standard format)
        await ws_manager.broadcast_telemetry(robot_id, payload)

        # Also broadcast as health_telemetry for Operations Dashboard
        health_telemetry = {
            "type": "health_telemetry",
            "robot_id": robot_id,
            "battery": {
                "level": payload.get("battery", 0),
                "health": payload.get("health", 100)
            },
            "thermal": {
                "cpu_temp": payload.get("temperature", 0),
                "motor_temp": payload.get("temperature", 0)
            },
            "resources": {
                "cpu_usage": 30,  # Can be enhanced later
                "memory_usage": 45,
                "disk_usage": 32
            },
            "performance": {
                "fps": 30,
                "signal_strength": 5,
                "latency_ms": 45
            },
            "health_score": payload.get("health", 100),
            "health_status": "HEALTHY" if payload.get("health", 100) > 70 else "WARNING" if payload.get("health", 100) > 40 else "CRITICAL"
        }
        await ws_manager.broadcast(health_telemetry)

        # Broadcast control_state for position updates
        control_state = {
            "type": "control_state",
            "robot_id": robot_id,
            "mode": payload.get("mode", "STANDBY").upper(),
            "position": {
                "x": payload.get("pose", {}).get("x", 0),
                "y": payload.get("pose", {}).get("y", 0),
                "heading": payload.get("pose", {}).get("theta", 0) * 57.2958  # radians to degrees
            }
        }
        await ws_manager.broadcast(control_state)

        # Broadcast pose_update for map visualization with GPS coordinates
        gps_data = payload.get("gps", {})
        if gps_data.get("latitude") and gps_data.get("longitude"):
            pose_update = {
                "type": "pose_update",
                "robot_id": robot_id,
                "lat": gps_data.get("latitude", 0),
                "lon": gps_data.get("longitude", 0),
                "heading": payload.get("pose", {}).get("theta", 0) * 57.2958  # radians to degrees
            }
            await ws_manager.broadcast(pose_update)

    except Exception as e:
        logger.error(f"Error handling robot status: {e}")


async def handle_robot_pose(topic: str, payload: Any) -> None:
    """Handle robot pose messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        async for db in get_db():
            await telemetry_processor.process_pose(robot_id, payload, db)
            break

        await ws_manager.broadcast_pose(robot_id, payload)

    except Exception as e:
        logger.error(f"Error handling robot pose: {e}")


async def handle_robot_errors(topic: str, payload: Any) -> None:
    """Handle robot error messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        async for db in get_db():
            await logging_service.process_error_message(robot_id, payload, db)
            break

        await ws_manager.broadcast_error(robot_id, payload)

    except Exception as e:
        logger.error(f"Error handling robot errors: {e}")


async def handle_robot_joints(topic: str, payload: Any) -> None:
    """Handle robot joints messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        # Broadcast to WebSocket clients
        await ws_manager.broadcast_joints(robot_id, payload)

    except Exception as e:
        logger.error(f"Error handling robot joints: {e}")


async def handle_robot_gps(topic: str, payload: Any) -> None:
    """Handle robot GPS messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        # Broadcast to WebSocket clients (standard format)
        await ws_manager.broadcast_gps(robot_id, payload)

        # Also send pose_update for map visualization
        pose_update = {
            "type": "pose_update",
            "robot_id": robot_id,
            "lat": payload.get("latitude", 0),
            "lon": payload.get("longitude", 0),
            "heading": 0  # Will be updated from pose data
        }
        await ws_manager.broadcast(pose_update)

    except Exception as e:
        logger.error(f"Error handling robot GPS: {e}")


async def handle_robot_battery(topic: str, payload: Any) -> None:
    """Handle robot battery messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        # Broadcast to WebSocket clients
        await ws_manager.broadcast({"type": "battery", "robot_id": robot_id, "data": payload})

    except Exception as e:
        logger.error(f"Error handling robot battery: {e}")


async def handle_robot_health(topic: str, payload: Any) -> None:
    """Handle robot health messages."""
    try:
        if not isinstance(payload, dict):
            return

        parts = topic.split("/")
        robot_id = parts[-1] if len(parts) > 2 else payload.get("robot_id", "unknown")

        # Broadcast to WebSocket clients
        await ws_manager.broadcast({"type": "health", "robot_id": robot_id, "data": payload})

    except Exception as e:
        logger.error(f"Error handling robot health: {e}")


def _cancel_dummy_task() -> None:
    task = getattr(app.state, "dummy_task", None)
    if task and not task.done():
        task.cancel()


async def _dummy_publisher_loop() -> None:
    try:
        while True:
            mqtt_manager.publish_dummy_payload()
            await asyncio.sleep(settings.dummy_publish_interval)
    except asyncio.CancelledError:
        pass


def generate_random_gps(center_lat: float, center_lon: float, radius_km: float):
    """Generate random GPS coordinates within a radius of a center point."""
    import math
    import random

    distance = random.uniform(0, radius_km)
    angle = random.uniform(0, 2 * math.pi)

    lat_change = (distance / 111.32) * math.cos(angle)
    lon_change = (distance / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(angle)

    return center_lat + lat_change, center_lon + lon_change


@app.on_event("startup")
async def on_startup() -> None:
    global command_dispatcher, robot_simulators
    import random
    import math

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Set asyncio loop for MQTT manager
    loop = asyncio.get_running_loop()
    mqtt_manager.set_asyncio_loop(loop)

    # Register MQTT message handlers
    mqtt_manager.register_handler("robot/status/*", handle_robot_status)
    mqtt_manager.register_handler("robot/pose/*", handle_robot_pose)
    mqtt_manager.register_handler("robot/errors/*", handle_robot_errors)
    mqtt_manager.register_handler("robot/joints/*", handle_robot_joints)
    mqtt_manager.register_handler("robot/gps/*", handle_robot_gps)
    mqtt_manager.register_handler("robot/battery/*", handle_robot_battery)
    mqtt_manager.register_handler("robot/health/*", handle_robot_health)

    # Start MQTT connection
    mqtt_manager.start()
    logger.info("MQTT client started")

    # Initialize command dispatcher
    command_dispatcher = CommandDispatcher(mqtt_manager._client)
    logger.info("Command dispatcher initialized")

    # Start robot simulators if enabled
    if settings.enable_robot_simulator:
        print("\n" + "=" * 70)
        print("ROBOT SIMULATOR")
        print("=" * 70)
        print(f"Number of robots: {settings.num_simulated_robots}")
        print(f"MQTT Broker: {settings.mqtt_host}:{settings.mqtt_port}")
        print(f"Spawn location: {settings.simulator_center_lat}, {settings.simulator_center_lon}")
        print(f"Spawn radius: {settings.simulator_spawn_radius} km")
        print("=" * 70 + "\n")

        logger.info(f"Starting {settings.num_simulated_robots} robot simulator(s)...")

        for i in range(settings.num_simulated_robots):
            robot_id = f"robot_{i+1:02d}"

            # Generate random GPS coordinates
            lat, lon = generate_random_gps(
                settings.simulator_center_lat,
                settings.simulator_center_lon,
                settings.simulator_spawn_radius
            )

            # Create robot with random initial state
            robot = RobotSimulator(robot_id=robot_id, initial_lat=lat, initial_lon=lon)

            # Randomize initial state
            modes = [
                RobotSimulator.MODE_STANDING,
                RobotSimulator.MODE_SITTING,
                RobotSimulator.MODE_WALKING
            ]
            robot.mode = random.choice(modes)
            robot.battery = random.uniform(30.0, 100.0)
            robot.health = random.uniform(80.0, 100.0)  # Random initial health
            robot.theta = random.uniform(0, 2 * math.pi)

            robot.start()
            robot_simulators.append(robot)

            logger.info(
                f"Started robot '{robot_id}' at GPS ({lat:.6f}, {lon:.6f}), "
                f"mode={robot.mode}, battery={robot.battery:.1f}%, health={robot.health:.1f}%"
            )

        print("\n" + "=" * 70)
        print(f"[✓] All {settings.num_simulated_robots} robot(s) started successfully!")
        print("=" * 70)
        print("\nRobots are now publishing telemetry to MQTT topics:")
        print("  - robot/status/<robot_id>   - Full telemetry")
        print("  - robot/battery/<robot_id>  - Battery info")
        print("  - robot/health/<robot_id>   - Health metrics")
        print("  - robot/pose/<robot_id>     - Position & GPS")
        print("  - robot/joints/<robot_id>   - Joint states")
        print("  - robot/gps/<robot_id>      - GPS coordinates")
        print("\nWebSocket endpoint available at: ws://localhost:8001/ws")
        print("API documentation at: http://localhost:8001/docs")
        print("\nTo control robots via REST API:")
        print("  POST /robot/mode - Switch mode (sitting, standing, walking, running)")
        print("  POST /robot/cmd_vel - Send velocity commands")
        print("  POST /robot/teleop - Send teleop commands")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 70 + "\n")

        logger.info(f"[✓] All {settings.num_simulated_robots} robot simulator(s) started successfully!")
        logger.info("Robots are now publishing telemetry to MQTT topics")

    # Start dummy publisher if enabled
    if settings.dummy_publish_enabled:
        app.state.dummy_task = asyncio.create_task(_dummy_publisher_loop())
        logger.info("Dummy publisher started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global robot_simulators

    _cancel_dummy_task()

    # Stop robot simulators
    if robot_simulators:
        logger.info(f"Stopping {len(robot_simulators)} robot simulator(s)...")
        for robot in robot_simulators:
            robot.stop()
        robot_simulators.clear()
        logger.info("All robot simulators stopped")

    mqtt_manager.stop()
    await close_db()
    logger.info("Application shutdown complete")


# Health check
@app.get("/health")
def health() -> Dict[str, Any]:
    mqtt_status = mqtt_manager.get_connection_status()

    return {
        "status": "ok" if mqtt_status["connected"] else "degraded",
        "websocket_connections": ws_manager.get_connection_count(),
        "mqtt": mqtt_status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


@app.get("/health/mqtt")
def mqtt_health() -> Dict[str, Any]:
    """Detailed MQTT connection health check."""
    status = mqtt_manager.get_connection_status()

    return {
        "status": "healthy" if status["connected"] else "unhealthy",
        "details": status,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive JSON messages from frontend
            try:
                data = await websocket.receive_json()

                # Route commands to appropriate MQTT topics
                if data.get('type') == 'cmd_vel':
                    # Joystick control - velocity commands
                    robot_id = data.get('robot_id', 'robot_01')
                    mqtt_manager.publish_event(
                        f"robot/cmd_vel/{robot_id}",
                        {
                            "linear": data.get('linear', 0.0),
                            "angular": data.get('angular', 0.0)
                        }
                    )
                    logger.info(f"CMD_VEL: robot={robot_id}, linear={data.get('linear')}, angular={data.get('angular')}")

                elif data.get('type') == 'teleop':
                    # Teleop commands (sit, stand, walk, etc.)
                    robot_id = data.get('robot_id', 'robot_01')
                    mqtt_manager.publish_event(
                        f"robot/teleop/{robot_id}",
                        {
                            "cmd": data.get('command', ''),
                            "params": data.get('params', {})
                        }
                    )
                    logger.info(f"TELEOP: robot={robot_id}, cmd={data.get('command')}")

                elif data.get('type') == 'mode':
                    # Mode switching (sitting, standing, walking, running)
                    robot_id = data.get('robot_id', 'robot_01')
                    mqtt_manager.publish_event(
                        f"robot/mode/{robot_id}",
                        {
                            "mode": data.get('mode', 'standing')
                        }
                    )
                    logger.info(f"MODE: robot={robot_id}, mode={data.get('mode')}")

            except json.JSONDecodeError:
                # Handle non-JSON messages
                text_data = await websocket.receive_text()
                logger.warning(f"Received non-JSON message: {text_data[:100]}")

    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)


# Robot state endpoints
@app.get("/robot/state/{robot_id}")
def get_robot_state(robot_id: str) -> Dict[str, Any]:
    """Get current state of a specific robot."""
    state = robot_state_cache.get_state(robot_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Robot {robot_id} not found")
    return state.to_dict()


@app.get("/robot/states")
def get_all_robot_states() -> Dict[str, Any]:
    """Get current state of all robots."""
    return robot_state_cache.get_all_states()


# Command endpoints
@app.post("/robot/cmd_vel")
def send_cmd_vel(body: CommandVelocityRequest) -> Dict[str, str]:
    """Send velocity command to robot."""
    if not command_dispatcher:
        raise HTTPException(status_code=503, detail="Command dispatcher not initialized")

    try:
        command_dispatcher.send_cmd_vel(body.robot_id, body.linear, body.angular)
        return {"status": "sent", "robot_id": body.robot_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/robot/teleop")
def send_teleop_command(body: TeleopCommandRequest) -> Dict[str, str]:
    """Send teleop command to robot."""
    if not command_dispatcher:
        raise HTTPException(status_code=503, detail="Command dispatcher not initialized")

    try:
        command_dispatcher.send_teleop_command(body.robot_id, body.command, body.params)
        return {"status": "sent", "robot_id": body.robot_id, "command": body.command}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/robot/mode")
def switch_mode(body: ModeSwitchRequest) -> Dict[str, str]:
    """Switch robot operating mode."""
    if not command_dispatcher:
        raise HTTPException(status_code=503, detail="Command dispatcher not initialized")

    try:
        command_dispatcher.send_mode_switch(body.robot_id, body.mode)
        return {"status": "sent", "robot_id": body.robot_id, "mode": body.mode}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/robot/update")
def trigger_update(body: UpdateTriggerRequest) -> Dict[str, str]:
    """Trigger robot update."""
    if not command_dispatcher:
        raise HTTPException(status_code=503, detail="Command dispatcher not initialized")

    try:
        command_dispatcher.trigger_update(body.robot_id, body.update_type)
        return {"status": "sent", "robot_id": body.robot_id, "update_type": body.update_type}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/robot/emergency_stop")
def emergency_stop(robot_id: str) -> Dict[str, str]:
    """Send emergency stop to robot."""
    if not command_dispatcher:
        raise HTTPException(status_code=503, detail="Command dispatcher not initialized")

    try:
        command_dispatcher.send_emergency_stop(robot_id)
        return {"status": "emergency_stop_sent", "robot_id": robot_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Telemetry history endpoints
@app.get("/robot/{robot_id}/path")
async def get_robot_path(
    robot_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get robot path history."""
    from sqlalchemy import select, desc

    stmt = select(RobotPathLog).where(
        RobotPathLog.robot_id == robot_id
    ).order_by(desc(RobotPathLog.timestamp)).limit(limit)

    result = await db.execute(stmt)
    paths = result.scalars().all()

    return {
        "robot_id": robot_id,
        "count": len(paths),
        "paths": [
            {
                "x": p.x,
                "y": p.y,
                "theta": p.theta,
                "timestamp": p.timestamp.isoformat() + "Z"
            }
            for p in reversed(paths)  # Return in chronological order
        ]
    }


@app.get("/robot/{robot_id}/battery")
async def get_battery_history(
    robot_id: str,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get robot battery history."""
    from sqlalchemy import select, desc

    stmt = select(BatteryHistory).where(
        BatteryHistory.robot_id == robot_id
    ).order_by(desc(BatteryHistory.timestamp)).limit(limit)

    result = await db.execute(stmt)
    battery_logs = result.scalars().all()

    return {
        "robot_id": robot_id,
        "count": len(battery_logs),
        "history": [
            {
                "battery_level": b.battery_level,
                "timestamp": b.timestamp.isoformat() + "Z"
            }
            for b in reversed(battery_logs)
        ]
    }


@app.get("/robot/{robot_id}/errors")
async def get_robot_errors(
    robot_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Get robot error logs."""
    from sqlalchemy import select, desc

    stmt = select(ErrorLog).where(
        ErrorLog.robot_id == robot_id
    ).order_by(desc(ErrorLog.timestamp)).limit(limit)

    result = await db.execute(stmt)
    error_logs = result.scalars().all()

    return {
        "robot_id": robot_id,
        "count": len(error_logs),
        "errors": [
            {
                "error_type": e.error_type,
                "message": e.error_message,
                "severity": e.severity,
                "timestamp": e.timestamp.isoformat() + "Z"
            }
            for e in error_logs
        ]
    }


# Legacy MQTT endpoints (for backward compatibility)
@app.post("/mqtt/publish")
def publish_event(body: PublishRequest) -> Dict[str, str]:
    try:
        mqtt_manager.publish_event(body.topic, body.payload, qos=body.qos)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "published", "topic": body.topic}


@app.post("/mqtt/subscribe")
def subscribe_topic(body: SubscribeRequest) -> Dict[str, str]:
    mqtt_manager.subscribe(body.topic, qos=body.qos)
    return {"status": "subscribed", "topic": body.topic}


@app.get("/mqtt/events")
def recent_events(limit: int = 25) -> Dict[str, Any]:
    events = mqtt_manager.get_recent_events(limit)
    return {"items": events, "count": len(events)}


@app.post("/mqtt/dummy")
def publish_dummy(body: DummyPublishRequest) -> Dict[str, Any]:
    published: List[Dict[str, Any]] = []
    for _ in range(body.count):
        for device_id in body.device_ids:
            published.append(mqtt_manager.publish_dummy_payload(device_id))
    return {"published": published, "count": len(published)}
