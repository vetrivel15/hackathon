#!/usr/bin/env python3
"""
Test Console Application for MQTT Listening and Logging
Continuously listens to MQTT topics and logs all robot telemetry and events.
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class MQTTListener:
    """Console application for listening to and logging MQTT messages."""

    def __init__(self, mqtt_host: str = "localhost", mqtt_port: int = 1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.client = mqtt.Client(client_id="mqtt-listener-console", clean_session=True)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.connected = False

        # Message logging
        self.message_count = 0
        self.messages_by_topic: Dict[str, int] = {}
        self.last_messages: Dict[str, Dict] = {}

        # Subscribed topics
        self.subscriptions: List[str] = [
             "robot/status/#",
            "robot/pose/#",
            "robot/teleop/#",
             "robot/cmd_vel/#",
            "robot/mode/#",
             "robot/errors/#",
            "robot/joints/#",
            "robot/gps/#",
             "simulator/#",
            "frontend/events/#"
        ]

        # Display settings
        self.verbose = True
        self.show_timestamps = True
        self.pretty_print = True

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            print(f"\n{'=' * 70}")
            print(f"[✓] Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            print(f"{'=' * 70}")
            self.connected = True

            # Subscribe to all topics
            for topic in self.subscriptions:
                client.subscribe(topic, qos=0)
                print(f"[SUB] Subscribing to: {topic}")

            print(f"{'=' * 70}")
            print("[LISTENING] Waiting for messages... (Press Ctrl+C to exit)\n")
        else:
            print(f"[✗] Connection failed with code {rc}")
            self.connected = False

    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback when subscription is confirmed."""
        pass

    def _on_message(self, client, userdata, msg):
        """Callback for received messages."""
        self.message_count += 1

        # Track messages per topic
        topic_base = msg.topic.split('/')[0] + '/' + msg.topic.split('/')[1] if '/' in msg.topic else msg.topic
        self.messages_by_topic[topic_base] = self.messages_by_topic.get(topic_base, 0) + 1

        # Parse payload
        try:
            payload = json.loads(msg.payload.decode())
            is_json = True
        except:
            payload = msg.payload.decode()
            is_json = False

        # Store last message for this topic
        self.last_messages[msg.topic] = {
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "qos": msg.qos
        }

        # Display message
        self._display_message(msg.topic, payload, is_json, msg.qos)

    def _display_message(self, topic: str, payload, is_json: bool, qos: int):
        """Display a received message."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Color coding based on topic type
        if "status" in topic:
            color_prefix = "\033[92m"  # Green
            msg_type = "STATUS"
        elif "joints" in topic:
            color_prefix = "\033[95m"  # Magenta
            msg_type = "JOINTS"
        elif "gps" in topic.lower():
            color_prefix = "\033[94m"  # Blue
            msg_type = "GPS"
        elif "pose" in topic:
            color_prefix = "\033[94m"  # Blue
            msg_type = "POSE"
        elif "teleop" in topic or "cmd_vel" in topic:
            color_prefix = "\033[93m"  # Yellow
            msg_type = "COMMAND"
        elif "mode" in topic:
            color_prefix = "\033[95m"  # Magenta
            msg_type = "MODE"
        elif "error" in topic:
            color_prefix = "\033[91m"  # Red
            msg_type = "ERROR"
        else:
            color_prefix = "\033[96m"  # Cyan
            msg_type = "OTHER"

        reset_color = "\033[0m"

        # Print header
        print(f"{color_prefix}{'─' * 70}")
        print(f"[{msg_type}] Message #{self.message_count} @ {timestamp}")
        print(f"Topic: {topic} (QoS: {qos})")

        # Print payload
        if is_json and self.pretty_print:
            # Pretty print JSON
            if isinstance(payload, dict):
                # Extract key fields for quick view
                if "robot_id" in payload:
                    print(f"Robot: {payload['robot_id']}")
                if "mode" in payload:
                    print(f"Mode: {payload['mode']}")
                if "status" in payload:
                    print(f"Status: {payload['status']}")
                if "battery" in payload:
                    print(f"Battery: {payload['battery']}%")

                # GPS coordinates display
                if "latitude" in payload and "longitude" in payload:
                    print(f"GPS: Lat={payload['latitude']:.6f}, Lon={payload['longitude']:.6f}")
                    if "altitude" in payload:
                        print(f"     Alt={payload['altitude']:.2f}m")
                if "gps" in payload:
                    gps = payload['gps']
                    print(f"GPS: {gps.get('latitude', 'N/A'):.6f}, {gps.get('longitude', 'N/A'):.6f}")

                # Joints display
                if "joints" in payload:
                    joints = payload['joints']
                    if isinstance(joints, list):
                        print(f"Joints: {len(joints)} joints")
                        # Show summary of first few joints
                        for i, joint in enumerate(joints[:3]):
                            if isinstance(joint, dict):
                                name = joint.get('name', 'unknown')
                                status = joint.get('status', 'N/A')
                                print(f"  [{i+1}] {name}: {status}")
                        if len(joints) > 3:
                            print(f"  ... and {len(joints) - 3} more joints")

                if "pose" in payload:
                    pose = payload['pose']
                    print(f"Pose: x={pose.get('x', 0):.2f}m, y={pose.get('y', 0):.2f}m, θ={pose.get('theta', 0):.2f}rad")
                if "velocity" in payload:
                    vel = payload['velocity']
                    print(f"Velocity: linear={vel.get('linear', 0):.2f}m/s, angular={vel.get('angular', 0):.2f}rad/s")

                if self.verbose:
                    print(f"\nFull Payload:")
                    print(json.dumps(payload, indent=2))
            else:
                print(f"Payload: {json.dumps(payload, indent=2)}")
        else:
            print(f"Payload: {payload}")

        print(f"{'─' * 70}{reset_color}\n")

    def print_statistics(self):
        """Print message statistics."""
        print("\n" + "=" * 70)
        print("MESSAGE STATISTICS")
        print("=" * 70)
        print(f"Total Messages Received: {self.message_count}")
        print(f"\nMessages by Topic:")
        for topic, count in sorted(self.messages_by_topic.items()):
            print(f"  {topic}: {count}")
        print("=" * 70 + "\n")

    def connect(self):
        """Connect to MQTT broker."""
        print(f"\nConnecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}...")
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
        print("\n[✓] Disconnected from MQTT broker")

    def run(self):
        """Run the listener."""
        if not self.connect():
            return

        try:
            # Keep running until interrupted
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.print_statistics()
        finally:
            self.disconnect()


class InteractiveMQTTListener(MQTTListener):
    """Interactive version with commands."""

    def run(self):
        """Run the interactive listener."""
        if not self.connect():
            return

        print("\nInteractive Commands:")
        print("  'stats' - Show message statistics")
        print("  'verbose' - Toggle verbose mode")
        print("  'clear' - Clear screen")
        print("  'quit' - Exit")
        print()

        try:
            import threading
            import select

            def listen_for_input():
                while True:
                    if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        line = sys.stdin.readline().strip()
                        if line:
                            self._handle_command(line)

            # Start input listener in background
            input_thread = threading.Thread(target=listen_for_input, daemon=True)
            input_thread.start()

            # Keep main thread running
            while True:
                time.sleep(1)

        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
            self.print_statistics()
        except:
            # Fallback to simple mode if select not available
            print("[INFO] Interactive mode not available on this platform")
            super().run()
        finally:
            self.disconnect()

    def _handle_command(self, command: str):
        """Handle interactive commands."""
        if command == "stats":
            self.print_statistics()
        elif command == "verbose":
            self.verbose = not self.verbose
            print(f"\n[INFO] Verbose mode: {'ON' if self.verbose else 'OFF'}\n")
        elif command == "clear":
            print("\033[2J\033[H")  # Clear screen
        elif command == "quit":
            raise KeyboardInterrupt()


def main():
    """Main entry point."""
    import argparse

    # Get default values from environment
    default_host = os.getenv("MQTT_HOST", "localhost")
    default_port = int(os.getenv("MQTT_PORT", "1884"))

    parser = argparse.ArgumentParser(description="MQTT Listener and Logger Console")
    parser.add_argument("--host", default=default_host, help=f"MQTT broker host (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"MQTT broker port (default: {default_port})")
    parser.add_argument("--simple", action="store_true", help="Use simple mode (no interactive commands)")
    parser.add_argument("--no-verbose", action="store_true", help="Disable verbose output")
    args = parser.parse_args()

    print("=" * 70)
    print("MQTT LISTENER - Test Console Application")
    print("=" * 70)
    print(f"MQTT Broker: {args.host}:{args.port}")
    print("=" * 70)

    if args.simple:
        listener = MQTTListener(mqtt_host=args.host, mqtt_port=args.port)
    else:
        listener = InteractiveMQTTListener(mqtt_host=args.host, mqtt_port=args.port)

    if args.no_verbose:
        listener.verbose = False

    listener.run()


if __name__ == "__main__":
    main()
