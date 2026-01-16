#!/bin/bash
set -e

# Directory where this script resides
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Setting up development environment in $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    echo "No requirements.txt found!"
    exit 1
fi

echo "Setup complete! Activate with: source venv/bin/activate"
