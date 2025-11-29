#!/bin/bash

# Fix database permissions script

echo "================================================================"
echo "  Database Permissions Fix"
echo "================================================================"
echo ""

# Check if database exists
if [ ! -f "./data/robot_telemetry.db" ]; then
    echo "✓ No existing database found - app will create it with correct permissions"
    exit 0
fi

# Check current ownership
CURRENT_OWNER=$(stat -c '%U' ./data/robot_telemetry.db)
CURRENT_USER=$(whoami)

if [ "$CURRENT_OWNER" != "$CURRENT_USER" ]; then
    echo "⚠️  Database is owned by '$CURRENT_OWNER' but you are '$CURRENT_USER'"
    echo ""
    echo "Option 1: Fix ownership (requires sudo password)"
    echo "  sudo chown $CURRENT_USER:$CURRENT_USER ./data/robot_telemetry.db"
    echo "  sudo chmod 664 ./data/robot_telemetry.db"
    echo ""
    echo "Option 2: Start fresh (no sudo needed)"
    echo "  rm ./data/robot_telemetry.db"
    echo ""
    read -p "Choose option (1/2) or press Enter to cancel: " choice

    if [ "$choice" == "1" ]; then
        echo "Fixing ownership..."
        sudo chown $CURRENT_USER:$CURRENT_USER ./data/robot_telemetry.db
        sudo chmod 664 ./data/robot_telemetry.db
        echo "✓ Ownership fixed!"
        ls -la ./data/robot_telemetry.db
    elif [ "$choice" == "2" ]; then
        echo "Deleting old database..."
        rm ./data/robot_telemetry.db
        echo "✓ Database deleted - app will create a new one on next startup"
    else
        echo "Cancelled"
        exit 1
    fi
else
    echo "✓ Database ownership is correct"
    chmod 664 ./data/robot_telemetry.db 2>/dev/null
    echo "✓ Permissions updated"
    ls -la ./data/robot_telemetry.db
fi

echo ""
echo "================================================================"
echo "  Done! You can now restart the application:"
echo "  ./start_application.sh"
echo "================================================================"
