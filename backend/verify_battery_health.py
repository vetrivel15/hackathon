#!/usr/bin/env python3
"""
Quick verification script to check if battery and health data is flowing correctly.
Run this after starting the backend to verify MQTT -> WebSocket -> Frontend connection.
"""

import asyncio
import json
import sys
import time
from datetime import datetime

import paho.mqtt.client as mqtt


class BatteryHealthVerifier:
    def __init__(self, mqtt_host="localhost", mqtt_port=1883):
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.received_messages = {
            "battery": [],
            "health": [],
            "status": []
        }
        self.client = mqtt.Client(client_id="battery-health-verifier", clean_session=True)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"✅ Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            print("\nSubscribing to topics...")
            client.subscribe("robot/battery/#")
            client.subscribe("robot/health/#")
            client.subscribe("robot/status/#")
            print("✅ Subscribed to robot/battery/#")
            print("✅ Subscribed to robot/health/#")
            print("✅ Subscribed to robot/status/#")
            print("\n" + "="*70)
            print("LISTENING FOR MESSAGES (will stop after 30 seconds)")
            print("="*70 + "\n")
        else:
            print(f"❌ Connection failed with code {rc}")
            sys.exit(1)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

            if "battery" in msg.topic:
                self.received_messages["battery"].append(payload)
                battery_level = payload.get("battery", "N/A")
                charging = " (CHARGING)" if payload.get("charging") else ""
                print(f"[{timestamp}] 🔋 BATTERY: {battery_level}%{charging} - {msg.topic}")

            elif "health" in msg.topic:
                self.received_messages["health"].append(payload)
                health = payload.get("health", "N/A")
                temp = payload.get("temperature", "N/A")
                print(f"[{timestamp}] ❤️  HEALTH: {health}% | Temp: {temp}°C - {msg.topic}")

            elif "status" in msg.topic:
                self.received_messages["status"].append(payload)
                battery = payload.get("battery", "N/A")
                health = payload.get("health", "N/A")
                temp = payload.get("temperature", "N/A")
                mode = payload.get("mode", "N/A")
                print(f"[{timestamp}] 📊 STATUS: Battery={battery}%, Health={health}%, Temp={temp}°C, Mode={mode}")

        except json.JSONDecodeError:
            print(f"⚠️  Received non-JSON message on {msg.topic}")
        except Exception as e:
            print(f"❌ Error processing message: {e}")

    def run_verification(self, duration=30):
        """Run verification for specified duration in seconds."""
        print("\n" + "="*70)
        print("BATTERY & HEALTH DATA VERIFICATION")
        print("="*70)
        print(f"Connecting to MQTT broker at {self.mqtt_host}:{self.mqtt_port}...\n")

        try:
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()

            # Run for specified duration
            time.sleep(duration)

            # Stop and report
            self.client.loop_stop()
            self.client.disconnect()

            # Print summary
            print("\n" + "="*70)
            print("VERIFICATION SUMMARY")
            print("="*70)

            battery_count = len(self.received_messages["battery"])
            health_count = len(self.received_messages["health"])
            status_count = len(self.received_messages["status"])

            print(f"\n📊 Messages Received in {duration} seconds:")
            print(f"   Battery messages: {battery_count}")
            print(f"   Health messages:  {health_count}")
            print(f"   Status messages:  {status_count}")

            if battery_count > 0 and health_count > 0:
                print("\n✅ SUCCESS: Battery and health data is flowing correctly!")

                # Show last values
                if self.received_messages["battery"]:
                    last_battery = self.received_messages["battery"][-1]
                    print(f"\n   Last Battery: {last_battery.get('battery')}%")

                if self.received_messages["health"]:
                    last_health = self.received_messages["health"][-1]
                    print(f"   Last Health: {last_health.get('health')}%")
                    print(f"   Last Temperature: {last_health.get('temperature')}°C")

                print("\n✅ MQTT Backend is properly configured")
                print("✅ Battery and health topics are publishing")
                print("\n💡 Next Step: Check if WebSocket is forwarding to frontend")
                print("   1. Start backend: uvicorn app.main:app --port 8001")
                print("   2. Check backend logs for 'WebSocket connected'")
                print("   3. Open frontend and check browser console")
                return 0
            else:
                print("\n❌ FAILURE: No battery or health messages received!")
                print("\nPossible issues:")
                print("   1. Robot simulator not running")
                print("   2. MQTT broker not running (mosquitto)")
                print("   3. Wrong MQTT host/port")
                print("   4. Check backend logs for errors")
                return 1

        except ConnectionRefusedError:
            print(f"\n❌ ERROR: Could not connect to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
            print("\nMake sure:")
            print("   1. Mosquitto broker is running: sudo systemctl start mosquitto")
            print("   2. MQTT_HOST and MQTT_PORT in .env are correct")
            return 1
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            self.client.loop_stop()
            self.client.disconnect()
            return 1
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            return 1


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Verify battery and health data flow")
    parser.add_argument("--host", default="localhost", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
    parser.add_argument("--duration", type=int, default=30, help="Test duration in seconds")

    args = parser.parse_args()

    verifier = BatteryHealthVerifier(mqtt_host=args.host, mqtt_port=args.port)
    return verifier.run_verification(duration=args.duration)


if __name__ == "__main__":
    sys.exit(main())
