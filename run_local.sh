#!/bin/bash

# Start the Russian AI Assistant system

echo "Starting Russian AI Assistant..."

# Activate virtual environment
source venv/bin/activate

# Start GoMLX connector in background
echo "Starting GoMLX Connector..."
cd ai_engine
./gomlx_connector &
GOMLX_PID=$!
cd ..

# Wait for GoMLX to start
sleep 3

# Start Telegram bot
echo "Starting Telegram Bot..."
python bot/main.py

# Cleanup
kill $GOMLX_PID
