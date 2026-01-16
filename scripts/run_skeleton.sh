#!/bin/bash
# scripts/run_skeleton.sh

# Function to kill child processes on exit
cleanup() {
    echo "Stopping processes..."
    kill $(jobs -p)
}
trap cleanup EXIT

source venv/bin/activate

echo "Starting Backend..."
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
echo "Waiting for backend..."
sleep 3

echo "Starting Kiosk..."
python -m kiosk.main

# If kiosk closes, script ends and cleanup triggers
