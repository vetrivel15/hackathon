#!/usr/bin/env python3
"""
S4 Robot Backend Startup Script
Starts the FastAPI backend with configurable robot simulator settings.

This replaces the need for separate run_robot_simulator.py and uvicorn commands.
All functionality is now integrated into one command.

Usage:
    python run_backend.py
    python run_backend.py --robots 3 --mqtt-host localhost --mqtt-port 1883
    python run_backend.py --no-simulator  # Start without robot simulators
"""

import argparse
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="S4 Robot Backend with Integrated Robot Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with default settings (1 robot)
  python run_backend.py

  # Start with 5 robots
  python run_backend.py --robots 5

  # Configure MQTT broker
  python run_backend.py --mqtt-host mqtt-broker --mqtt-port 1883

  # Custom GPS spawn location (New York)
  python run_backend.py --center-lat 40.7128 --center-lon -74.0060 --radius 10

  # Start without robot simulators
  python run_backend.py --no-simulator

  # Combine options
  python run_backend.py --robots 3 --center-lat 37.7749 --center-lon -122.4194
        """
    )

    # Robot Simulator Settings
    parser.add_argument(
        "--robots",
        type=int,
        default=None,
        help="Number of robots to simulate (default: from config or 1)"
    )
    parser.add_argument(
        "--no-simulator",
        action="store_true",
        help="Disable robot simulator (only run backend API/WebSocket)"
    )

    # MQTT Settings
    parser.add_argument(
        "--mqtt-host",
        default=None,
        help="MQTT broker host (default: from config or 'localhost')"
    )
    parser.add_argument(
        "--mqtt-port",
        type=int,
        default=None,
        help="MQTT broker port (default: from config or 1883)"
    )

    # GPS Spawn Settings
    parser.add_argument(
        "--center-lat",
        type=float,
        default=None,
        help="Center latitude for robot spawning (default: 37.7749 - San Francisco)"
    )
    parser.add_argument(
        "--center-lon",
        type=float,
        default=None,
        help="Center longitude for robot spawning (default: -122.4194 - San Francisco)"
    )
    parser.add_argument(
        "--radius",
        type=float,
        default=None,
        help="Spawn radius in kilometers (default: 5.0)"
    )

    # Server Settings
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Server port (default: 8001)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    parser.add_argument(
        "--log-level",
        default="info",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Log level (default: info)"
    )

    args = parser.parse_args()

    # Update config with CLI arguments
    from app.config import settings

    if args.robots is not None:
        settings.num_simulated_robots = args.robots

    if args.no_simulator:
        settings.enable_robot_simulator = False

    if args.mqtt_host is not None:
        settings.mqtt_host = args.mqtt_host

    if args.mqtt_port is not None:
        settings.mqtt_port = args.mqtt_port

    if args.center_lat is not None:
        settings.simulator_center_lat = args.center_lat

    if args.center_lon is not None:
        settings.simulator_center_lon = args.center_lon

    if args.radius is not None:
        settings.simulator_spawn_radius = args.radius

    # Print startup banner
    print("\n" + "=" * 70)
    print("S4 ROBOT BACKEND - FastAPI Server with MQTT & WebSocket")
    print("=" * 70)
    print(f"Server: http://{args.host}:{args.port}")
    print(f"API Docs: http://{args.host}:{args.port}/docs")
    print(f"WebSocket: ws://{args.host}:{args.port}/ws")
    print(f"MQTT Broker: {settings.mqtt_host}:{settings.mqtt_port}")

    if settings.enable_robot_simulator:
        print(f"\n✓ Robot Simulator: ENABLED ({settings.num_simulated_robots} robot(s))")
        print(f"  Spawn Location: ({settings.simulator_center_lat}, {settings.simulator_center_lon})")
        print(f"  Spawn Radius: {settings.simulator_spawn_radius} km")
    else:
        print("\n✗ Robot Simulator: DISABLED")

    print("=" * 70 + "\n")

    # Start uvicorn server
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level,
    )


if __name__ == "__main__":
    main()
