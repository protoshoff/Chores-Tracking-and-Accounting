#!/bin/bash
# scripts/deploy_release.sh
# Usage: ./scripts/deploy_release.sh [branch] (defaults to main)
# Run as user 'pi'

set -e

APP_ROOT="/home/pi/chores_app"
RELEASES_DIR="$APP_ROOT/releases"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_release_DIR="$RELEASES_DIR/$TIMESTAMP"
REPO_URL="git@github.com:youruser/chores-kiosk.git" # TODO: Update with actual URL or use local path
# For now, we assume this script is running from the repo checkout location or the repo is separate.
# Let's assume user is running this from their dev machine via ssh or on the pi from a 'repo' dir.
# OPTION B (Self-contained): We clone from remote.

BRANCH=${1:-main}

echo "Deploying branch $BRANCH to $NEW_release_DIR..."

# 1. Ensure directories
mkdir -p "$RELEASES_DIR"

# 2. Clone/Copy Code
git clone -b "$BRANCH" "$REPO_URL" "$NEW_release_DIR"
# Alternatively if running locally on Pi from updated repo: cp -r . "$NEW_release_DIR"

# 3. Setup Venv (Share cache if possible, but for robustness create fresh or copy)
echo "Setting up venv..."
python3 -m venv "$NEW_release_DIR/venv"
source "$NEW_release_DIR/venv/bin/activate"

# 4. Install Deps
echo "Installing dependencies..."
pip install -r "$NEW_release_DIR/requirements.txt"

# 5. Backup DB (Safety)
DB_PATH="/var/lib/chores_app/chores.db"
if [ -f "$DB_PATH" ]; then
    echo "Backing up DB..."
    cp "$DB_PATH" "$DB_PATH.bak.$TIMESTAMP"
fi

# 6. Migrate DB
echo "Running Migrations..."
# We need to set CHORES_DATA_DIR env if DB is there
export CHORES_DATA_DIR="/var/lib/chores_app"
cd "$NEW_release_DIR"
alembic upgrade head

# 7. Switch Symlink
echo "Switching Symlink..."
ln -sfn "$NEW_release_DIR" "$APP_ROOT/current"

# 8. Restart Services
echo "Restarting Services..."
sudo systemctl restart chores-backend
sudo systemctl restart chores-kiosk

echo "Deployment Complete: $TIMESTAMP"
