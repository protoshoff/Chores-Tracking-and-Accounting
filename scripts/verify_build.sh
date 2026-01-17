#!/bin/bash
set -e

echo "🔍 Starting Build Verification..."

# 1. Syntax Check (Python)
echo "Checking Python Syntax..."
find . -name "*.py" -not -path "./venv/*" -exec python3 -m py_compile {} +
echo "✅ Syntax OK"

# 2. Import Smoke Test
echo "Running Import Smoke Test..."
# Attempt to import main modules to catch circular deps or missing vars
export PYTHONPATH=$PYTHONPATH:.
python3 -c "from kiosk.app import KioskApp; print('Kiosk App Importable')"
python3 -c "from backend.main import app; print('Backend App Importable')"
echo "✅ Imports OK"

echo "🎉 Build Verification Passed!"
