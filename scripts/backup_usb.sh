#!/bin/bash
# scripts/backup_usb.sh
# Triggered by udev rule or manual run
# Usage: ./backup_usb.sh [mount_point]

set -e

MOUNT_POINT=${1:-"/mnt/usb_backup"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$MOUNT_POINT/chores_backup_$TIMESTAMP"
DATA_DIR="/var/lib/chores_app"

# Check if mount point exists/is mounted
if ! mountpoint -q "$MOUNT_POINT"; then
    echo "Error: $MOUNT_POINT is not a mountpoint."
    # Optional: Try to auto-mount if device arg provided? 
    # For now assume udev mounts it or it's already mounted.
    exit 1
fi

echo "Starting Backup to $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

# Stop backend to ensure DB consistency (WAL mode might allow live backup, but stopping is safer for v0.1)
echo "Stopping services..."
sudo systemctl stop chores-backend
sudo systemctl stop chores-kiosk

# Copy Data
echo "Copying data..."
cp "$DATA_DIR/chores.db" "$BACKUP_DIR/"
if [ -f "$DATA_DIR/config.json" ]; then
    cp "$DATA_DIR/config.json" "$BACKUP_DIR/"
fi
if [ -d "$DATA_DIR/avatars" ]; then
    cp -r "$DATA_DIR/avatars" "$BACKUP_DIR/"
fi

# Metadata
echo "{"version": "v0.1", "timestamp": "$TIMESTAMP"}" > "$BACKUP_DIR/backup_info.json"

# Restart Services
echo "Restarting services..."
sudo systemctl start chores-backend
sudo systemctl start chores-kiosk

echo "Backup Complete."
# TODO: Play success sound via a specialized small script or CLI tool?
# e.g. aplay /opt/chores_app/current/kiosk/assets/sounds/success.wav
