#!/usr/bin/env python3
"""
Run Robot Simulator
Starts one or more robot simulators with random initial values.
"""

import argparse
import logging
import random
import sys
import time

# Add app to path
sys.path.insert(0, '.')

from app.mqtt_manager import mqtt_manager
from app.robot_simulator import RobotSimulator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def generate_random_gps(center_lat=37.7749, center_lon=-122.4194, radius_km=5.0):
    """
    Generate random GPS coordinates within a radius of a center point.

    Args:
        center_lat: Center latitude (default: San Francisco)
        center_lon: Center longitude (default: San Francisco)
        radius_km: Radius in kilometers

    Returns:
        Tuple of (latitude, longitude)
    """
    import math

    # Random distance and angle
    distance = random.uniform(0, radius_km)
    angle = random.uniform(0, 2 * math.pi)

    # Convert km to degrees (approximate)
    lat_change = (distance / 111.32) * math.cos(angle)
    lon_change = (distance / (111.32 * math.cos(math.radians(center_lat)))) * math.sin(angle)

    return center_lat + lat_change, center_lon + lon_change


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Robot Simulator Runner")
    parser.add_argument(
        "--robots",
        type=int,
        default=1,
        help="Number of robots to simulate (default: 1)"
    )
    parser.add_argument(
        "--mqtt-host",
        default="localhost",
        help="MQTT broker host (default: localhost)"
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )
    parser.add_argument(
        "--center-lat",
        type=float,
        default=37.7749,
        help="Center latitude for robot spawning (default: 37.7749 - San Francisco)"
    )
    parser.add_argument(
        "--center-lon",
        type=float,
        default=-122.4194,
        help="Center longitude for robot spawning (default: -122.4194 - San Francisco)"
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=5.0,
        help="Spawn radius in kilometers (default: 5.0)"
    )

    args = parser.parse_args()

    print("=" * 70)
    print("ROBOT SIMULATOR")
    print("=" * 70)
    print(f"Number of robots: {args.robots}")
    print(f"MQTT Broker: {args.mqtt_host}:{args.mqtt_port}")
    print(f"Spawn location: {args.center_lat}, {args.center_lon}")
    print(f"Spawn radius: {args.radius} km")
    print("=" * 70)

    # Update MQTT settings
    from app.config import settings
    settings.mqtt_host = args.mqtt_host
    settings.mqtt_port = args.mqtt_port

    # Start MQTT manager
    try:
        logger.info("Starting MQTT manager...")
        mqtt_manager.start()
        logger.info("MQTT manager started successfully")
    except Exception as e:
        logger.error(f"Failed to start MQTT manager: {e}")
        return 1

    # Create and start robot simulators
    robots = []
    try:
        for i in range(args.robots):
            robot_id = f"robot_{i+1:02d}"

            # Generate random GPS coordinates
            lat, lon = generate_random_gps(
                args.center_lat,
                args.center_lon,
                args.radius
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

            # Random initial heading
            import math
            robot.theta = random.uniform(0, 2 * math.pi)

            robot.start()
            robots.append(robot)

            logger.info(
                f"Started robot '{robot_id}' at GPS ({lat:.6f}, {lon:.6f}), "
                f"mode={robot.mode}, battery={robot.battery:.1f}%"
            )

        print("\n" + "=" * 70)
        print(f"[✓] All {args.robots} robot(s) started successfully!")
        print("=" * 70)
        print("\nRobots are now publishing telemetry to MQTT topics:")
        print("  - robot/status/<robot_id>")
        print("  - robot/pose/<robot_id>")
        print("\nTo control robots, use the test controller:")
        print("  python test_robot_controller.py")
        print("\nTo monitor MQTT messages, use the listener:")
        print("  python test_mqtt_listener.py")
        print("\nPress Ctrl+C to stop all robots")
        print("=" * 70 + "\n")

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutting down robots...")
        for robot in robots:
            robot.stop()
        mqtt_manager.stop()
        print("[✓] All robots stopped")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        for robot in robots:
            robot.stop()
        mqtt_manager.stop()
        return 1


if __name__ == "__main__":
    sys.exit(main())
