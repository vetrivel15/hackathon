#!/bin/bash

echo "================================================================================"
echo "  SWITCHING TO CORRECT BACKEND"
echo "================================================================================"
echo ""

# Find and kill any uvicorn processes on port 8001
echo "[1/3] Stopping old backend on port 8001..."
OLD_PID=$(lsof -ti :8001 2>/dev/null)

if [ -n "$OLD_PID" ]; then
    echo "Found process on port 8001 (PID: $OLD_PID)"
    echo "Stopping..."
    kill $OLD_PID 2>/dev/null
    sleep 2

    # Force kill if still running
    if lsof -ti :8001 > /dev/null 2>&1; then
        echo "Force stopping..."
        kill -9 $(lsof -ti :8001) 2>/dev/null
        sleep 1
    fi
    echo "✓ Old backend stopped"
else
    echo "✓ No process found on port 8001"
fi

echo ""
echo "[2/3] Checking directory..."
CURRENT_DIR=$(pwd)
EXPECTED_DIR="/home/sruthi/Documents/workspace/hackathon/backend"

if [ "$CURRENT_DIR" != "$EXPECTED_DIR" ]; then
    echo "⚠️  Wrong directory!"
    echo "   Current:  $CURRENT_DIR"
    echo "   Expected: $EXPECTED_DIR"
    echo ""
    echo "Changing to correct directory..."
    cd "$EXPECTED_DIR" || exit 1
fi

echo "✓ In correct directory: $(pwd)"

echo ""
echo "[3/3] Starting backend with integrated robot simulator..."
echo ""
echo "================================================================================"
echo "  Backend will start now with:"
echo "  - FastAPI on port 8001"
echo "  - Robot simulator integrated"
echo "  - Battery and health tracking"
echo "  - All mode changes (sit, stand, walk, run)"
echo "================================================================================"
echo ""

# Start the application using the start script
./start_application.sh
