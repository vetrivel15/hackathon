#!/bin/bash

# Humanoid Robot Backend - Run Script

echo "🤖 Humanoid Robot Backend"
echo "=========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "✨ Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Run the application
echo "🚀 Starting backend server..."
echo ""
python app.py
