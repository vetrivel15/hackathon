#!/bin/bash

# Script to fix MQTT port conflict
# Run this with: sudo ./fix_mqtt_port_conflict.sh

echo "Stopping system mosquitto service..."
systemctl stop mosquitto

echo "Disabling system mosquitto service from auto-start..."
systemctl disable mosquitto

echo "Verifying port 1883 is free..."
if lsof -i :1883 > /dev/null 2>&1; then
    echo "⚠️  Port 1883 is still in use. Killing the process..."
    fuser -k 1883/tcp
else
    echo "✓ Port 1883 is now free"
fi

echo ""
echo "✓ Done! You can now run ./start_application.sh"
