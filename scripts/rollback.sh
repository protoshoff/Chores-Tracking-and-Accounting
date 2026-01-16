#!/bin/bash
# scripts/rollback.sh
# Run as user 'pi'

APP_ROOT="/home/pi/chores_app"
RELEASES_DIR="$APP_ROOT/releases"

# Find 2nd most recent directory
PREV_RELEASE=$(ls -dt "$RELEASES_DIR"/*/ | sed -n '2p' | sed 's/\/$//')

if [ -z "$PREV_RELEASE" ]; then
    echo "No previous release found to rollback to."
    exit 1
fi

echo "Rolling back to: $PREV_RELEASE"

# Switch Symlink
ln -sfn "$PREV_RELEASE" "$APP_ROOT/current"

# Restart
echo "Restarting Services..."
sudo systemctl restart chores-backend
sudo systemctl restart chores-kiosk

echo "Rollback Complete."
# Note: Database migrations are NOT rolled back automatically. 
# That requires manual alembic downgrade if schema changed.
