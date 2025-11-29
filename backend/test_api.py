#!/usr/bin/env python3
"""
Test script for S4 Robot Backend API

Run this after starting the backend with: docker compose up
"""

import json
import time
import requests
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, success: bool, data: Any = None) -> None:
    """Print test result."""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status} - {test_name}")
    if data:
        print(f"  Response: {json.dumps(data, indent=2)}")


def test_health_check() -> bool:
    """Test health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        success = response.status_code == 200
        print_result("Health Check", success, response.json())
        return success
    except Exception as e:
        print_result("Health Check", False, {"error": str(e)})
        return False


def test_send_command() -> bool:
    """Test sending velocity command."""
    try:
        payload = {
            "robot_id": "TEST-01",
            "linear": 0.5,
            "angular": 0.0
        }
        response = requests.post(f"{BASE_URL}/robot/cmd_vel", json=payload)
        success = response.status_code == 200
        print_result("Send Velocity Command", success, response.json())
        return success
    except Exception as e:
        print_result("Send Velocity Command", False, {"error": str(e)})
        return False


def test_teleop_command() -> bool:
    """Test sending teleop command."""
    try:
        payload = {
            "robot_id": "TEST-01",
            "command": "move_forward",
            "params": {"speed": 0.5}
        }
        response = requests.post(f"{BASE_URL}/robot/teleop", json=payload)
        success = response.status_code == 200
        print_result("Send Teleop Command", success, response.json())
        return success
    except Exception as e:
        print_result("Send Teleop Command", False, {"error": str(e)})
        return False


def test_mode_switch() -> bool:
    """Test mode switching."""
    try:
        payload = {
            "robot_id": "TEST-01",
            "mode": "AUTONOMOUS"
        }
        response = requests.post(f"{BASE_URL}/robot/mode", json=payload)
        success = response.status_code == 200
        print_result("Mode Switch", success, response.json())
        return success
    except Exception as e:
        print_result("Mode Switch", False, {"error": str(e)})
        return False


def test_mqtt_publish() -> bool:
    """Test publishing to MQTT."""
    try:
        payload = {
            "topic": "test/topic",
            "payload": {"message": "Hello from test"},
            "qos": 0
        }
        response = requests.post(f"{BASE_URL}/mqtt/publish", json=payload)
        success = response.status_code == 200
        print_result("MQTT Publish", success, response.json())
        return success
    except Exception as e:
        print_result("MQTT Publish", False, {"error": str(e)})
        return False


def test_get_events() -> bool:
    """Test getting recent MQTT events."""
    try:
        response = requests.get(f"{BASE_URL}/mqtt/events?limit=10")
        success = response.status_code == 200
        data = response.json()
        print_result(
            f"Get MQTT Events ({data.get('count', 0)} events)",
            success,
            {"count": data.get("count")}
        )
        return success
    except Exception as e:
        print_result("Get MQTT Events", False, {"error": str(e)})
        return False


def test_robot_state() -> bool:
    """Test getting robot state (may return 404 if no telemetry received)."""
    try:
        response = requests.get(f"{BASE_URL}/robot/state/TEST-01")
        # 404 is expected if no telemetry has been published yet
        success = response.status_code in [200, 404]

        if response.status_code == 200:
            print_result("Get Robot State", success, response.json())
        else:
            print_result(
                "Get Robot State",
                success,
                {"note": "Robot not found (expected - no telemetry published yet)"}
            )
        return success
    except Exception as e:
        print_result("Get Robot State", False, {"error": str(e)})
        return False


def test_all_states() -> bool:
    """Test getting all robot states."""
    try:
        response = requests.get(f"{BASE_URL}/robot/states")
        success = response.status_code == 200
        data = response.json()
        print_result(
            f"Get All Robot States ({len(data)} robots)",
            success,
            {"robot_count": len(data)}
        )
        return success
    except Exception as e:
        print_result("Get All Robot States", False, {"error": str(e)})
        return False


def test_dummy_publish() -> bool:
    """Test publishing dummy telemetry."""
    try:
        payload = {
            "device_ids": ["TEST-DEVICE"],
            "count": 2
        }
        response = requests.post(f"{BASE_URL}/mqtt/dummy", json=payload)
        success = response.status_code == 200
        print_result("Publish Dummy Telemetry", success, response.json())
        return success
    except Exception as e:
        print_result("Publish Dummy Telemetry", False, {"error": str(e)})
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  S4 Robot Backend - API Test Suite")
    print("=" * 60)
    print(f"\nTesting API at: {BASE_URL}")
    print("Make sure the backend is running: docker compose up")

    # Wait a moment for user to read
    time.sleep(2)

    results = []

    # Run tests
    print_section("1. Basic Health Check")
    results.append(("Health Check", test_health_check()))

    print_section("2. Robot Commands")
    results.append(("Velocity Command", test_send_command()))
    results.append(("Teleop Command", test_teleop_command()))
    results.append(("Mode Switch", test_mode_switch()))

    print_section("3. MQTT Operations")
    results.append(("MQTT Publish", test_mqtt_publish()))
    results.append(("Dummy Publish", test_dummy_publish()))
    time.sleep(1)  # Wait for events to be processed
    results.append(("Get Events", test_get_events()))

    print_section("4. Robot State")
    results.append(("Get Robot State", test_robot_state()))
    results.append(("Get All States", test_all_states()))

    # Summary
    print_section("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    print(f"\nPassed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed! Backend is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        print("\nFailed tests:")
        for test_name, success in results:
            if not success:
                print(f"  - {test_name}")

    print("\n" + "=" * 60)
    print("\nNext steps:")
    print("  1. Open http://localhost:8000/docs for interactive API docs")
    print("  2. Connect your robot to MQTT broker at localhost:1883")
    print("  3. Monitor MQTT: mosquitto_sub -h localhost -t 'robot/#' -v")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
