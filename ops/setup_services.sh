#!/bin/bash
# ops/setup_services.sh
# Run this on the Raspberry Pi as sudo

SOURCE_DIR="/home/pi/chores_app/current/ops"
SYSTEMD_DIR="/etc/systemd/system"

echo "Installing Chores Services..."

# Link Backend
if [ -f "$SOURCE_DIR/chores-backend.service" ]; then
    cp "$SOURCE_DIR/chores-backend.service" "$SYSTEMD_DIR/"
    echo "  - Copied chores-backend.service"
else
    echo "  X Error: chores-backend.service not found in $SOURCE_DIR"
fi

# Link Kiosk
if [ -f "$SOURCE_DIR/chores-kiosk.service" ]; then
    cp "$SOURCE_DIR/chores-kiosk.service" "$SYSTEMD_DIR/"
    echo "  - Copied chores-kiosk.service"
else
    echo "  X Error: chores-kiosk.service not found in $SOURCE_DIR"
fi

# Reload
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling services..."
systemctl enable chores-backend.service
systemctl enable chores-kiosk.service

echo "Done. Services are enabled. Start them with:"
echo "  sudo systemctl start chores-backend chores-kiosk"
