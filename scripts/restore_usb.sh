#!/bin/bash
# scripts/restore_usb.sh
# Usage: ./restore_usb.sh <backup_folder_path>
# Example: ./restore_usb.sh /mnt/usb/chores_backup_20251010_120000

set -e

BACKUP_SOURCE=$1
DATA_DIR="/var/lib/chores_app"

if [ -z "$BACKUP_SOURCE" ]; then
    echo "Usage: $0 <path_to_backup_folder>"
    exit 1
fi

if [ ! -f "$BACKUP_SOURCE/chores.db" ]; then
    echo "Error: valid chores.db not found in $BACKUP_SOURCE"
    exit 1
fi

echo "WARNING: This will OVERWRITE current data in $DATA_DIR."
echo "Waiting 5 seconds... Press Ctrl+C to cancel."
sleep 5

echo "Stopping services..."
sudo systemctl stop chores-backend
sudo systemctl stop chores-kiosk

echo "Creating Safety Backup of current data..."
SAFE_BACKUP="$DATA_DIR/pre_restore_backup_$(date +%s)"
mkdir -p "$SAFE_BACKUP"
cp "$DATA_DIR/chores.db" "$SAFE_BACKUP/"
[ -f "$DATA_DIR/config.json" ] && cp "$DATA_DIR/config.json" "$SAFE_BACKUP/"

echo "Restoring from $BACKUP_SOURCE..."
cp "$BACKUP_SOURCE/chores.db" "$DATA_DIR/"
[ -f "$BACKUP_SOURCE/config.json" ] && cp "$BACKUP_SOURCE/config.json" "$DATA_DIR/"
if [ -d "$BACKUP_SOURCE/avatars" ]; then
    mkdir -p "$DATA_DIR/avatars"
    cp -r "$BACKUP_SOURCE/avatars/*" "$DATA_DIR/avatars/"
fi

# Fix permissions
chown -R pi:pi "$DATA_DIR"

echo "Restarting services..."
sudo systemctl start chores-backend
sudo systemctl start chores-kiosk

echo "Restore Complete."
