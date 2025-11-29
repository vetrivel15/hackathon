#!/bin/bash

# S4 Robot Backend - Application Starter
# This script starts EVERYTHING: MQTT broker + Backend + Robot Simulator

echo "================================================================================"
echo "  S4 ROBOT BACKEND - STARTING COMPLETE APPLICATION"
echo "================================================================================"
echo ""

# Function to check if docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "✗ Docker is not running"
        echo "Please start Docker Desktop or Docker daemon first"
        exit 1
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Stopping MQTT broker..."
    docker stop s4-mqtt-broker 2>/dev/null
    docker rm s4-mqtt-broker 2>/dev/null
    exit 0
}

# Set up cleanup trap
trap cleanup EXIT INT TERM

echo "[1/3] Checking Docker..."
check_docker
echo "✓ Docker is running"

# Clean up any corrupted environment variables
unset MQTT_DEFAULT_SUBSCRIPTIONS

echo ""
echo "[1.5/3] Checking for existing application processes..."
# Find and kill existing uvicorn processes using the configured port
PORT=$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)
EXISTING_PID=$(lsof -ti :$PORT 2>/dev/null)

if [ -n "$EXISTING_PID" ]; then
    echo "Found existing process on port $PORT (PID: $EXISTING_PID)"
    echo "Stopping existing application..."
    kill $EXISTING_PID 2>/dev/null
    sleep 2

    # Force kill if still running
    if lsof -ti :$PORT > /dev/null 2>&1; then
        echo "Force stopping..."
        kill -9 $(lsof -ti :$PORT) 2>/dev/null
        sleep 1
    fi
    echo "✓ Existing application stopped"
else
    echo "✓ No existing application found on port $PORT"
fi

echo ""
echo "[2/3] Starting MQTT broker..."
# Stop existing broker if running
docker stop s4-mqtt-broker 2>/dev/null
docker rm s4-mqtt-broker 2>/dev/null

# Start MQTT broker with config volume mount
CONTAINER_ID=$(docker run -d \
  --name s4-mqtt-broker \
  -p 1884:1883 \
  -p 9001:9001 \
  -v "$(pwd)/mosquitto/config:/mosquitto/config:ro" \
  eclipse-mosquitto:2.0 2>&1)

if [ $? -eq 0 ]; then
    echo "✓ MQTT broker container started (ID: ${CONTAINER_ID:0:12})"

    # Wait for MQTT broker to be fully ready
    echo "Waiting for MQTT broker to be ready..."
    MAX_WAIT=20
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        if nc -z localhost 1884 2>/dev/null; then
            echo "✓ MQTT broker is ready on localhost:1884"
            sleep 3  # Extra 3 seconds for full stability
            break
        fi
        sleep 1
        WAITED=$((WAITED + 1))
    done

    if [ $WAITED -eq $MAX_WAIT ]; then
        echo "✗ MQTT broker failed to start within ${MAX_WAIT} seconds"
        exit 1
    fi
else
    echo "✗ Failed to start MQTT broker container"
    echo "Error: $CONTAINER_ID"
    echo ""
    echo "Troubleshooting:"
    echo "  - Check if port 1884 is available: lsof -i :1884"
    echo "  - Check Docker logs: docker logs s4-mqtt-broker"
    echo "  - Verify mosquitto config exists: ls -la mosquitto/config/"
    exit 1
fi

echo ""
echo "[3/3] Starting FastAPI application with integrated robot simulator..."

# Check virtual environment
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating it now..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

PORT=$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)
echo ""
echo "================================================================================"
echo "  🚀 APPLICATION READY"
echo "================================================================================"
echo "  Backend API:     http://localhost:$PORT"
echo "  API Docs:        http://localhost:$PORT/docs"
echo "  WebSocket:       ws://localhost:$PORT/ws"
echo "  MQTT Broker:     localhost:1884"
echo ""
echo "  Robot Simulator: ENABLED ($(grep NUM_SIMULATED_ROBOTS .env 2>/dev/null | cut -d= -f2 || echo 1) robot(s))"
echo ""
echo "================================================================================"
echo "  💡 TEST COMMANDS (open new terminal)"
echo "================================================================================"
echo "  python test_robot_controller.py    # Send robot commands"
echo "  python test_mqtt_listener.py       # Monitor MQTT messages"
echo ""
echo "  Press Ctrl+C to stop everything (MQTT broker + Application)"
echo "================================================================================"
echo ""

# Start the application (read port from .env)
PORT=$(grep API_PORT .env 2>/dev/null | cut -d= -f2 || echo 8000)
uvicorn app.main:app --host 0.0.0.0 --port $PORT --reload
