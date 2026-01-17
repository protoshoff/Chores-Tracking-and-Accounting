#!/bin/bash
# scripts/diagnose_kiosk.sh
# Diagnostic script to find missing dependencies for Qt6 Kiosk

echo "=== Chores Kiosk Diagnostic Tool ==="
echo "Date: $(date)"
echo "User: $USER"

# 1. Locate the Virtual Environment and Python
APP_DIR="/home/$USER/chores_app/current"
if [ ! -d "$APP_DIR" ]; then
    echo "ERROR: App directory not found at $APP_DIR"
    exit 1
fi

PYTHON_BIN="$APP_DIR/venv/bin/python3"
if [ ! -f "$PYTHON_BIN" ]; then
    echo "ERROR: Python binary not found at $PYTHON_BIN"
    exit 1
fi

# 2. Find the PySide6 Platform Plugin
echo "Locating libqxcb.so..."
PLUGIN_PATH=$($PYTHON_BIN -c "import os, PySide6; print(os.path.join(os.path.dirname(PySide6.__file__), 'Qt', 'plugins', 'platforms', 'libqxcb.so'))")

if [ ! -f "$PLUGIN_PATH" ]; then
    echo "ERROR: Could not find libqxcb.so at $PLUGIN_PATH"
    echo "Trying simpler search..."
    PLUGIN_PATH=$(find "$APP_DIR/venv" -name "libqxcb.so" | head -n 1)
fi

if [ -f "$PLUGIN_PATH" ]; then
    echo "Found plugin at: $PLUGIN_PATH"
    echo ""
    echo "=== MISSING DEPENDENCIES ==="
    # Run ldd and only show what's missing
    ldd "$PLUGIN_PATH" | grep "not found"
    
    if [ $? -ne 0 ]; then
        echo "No missing dependencies reported by ldd!"
    fi
    echo "============================"
else
    echo "CRITICAL: libqxcb.so not found!"
fi

echo ""
echo "=== INSTALLED XCB PACKAGES ==="
dpkg -l | grep xcb | awk '{print $2}'
