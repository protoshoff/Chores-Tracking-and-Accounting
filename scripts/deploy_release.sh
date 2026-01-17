#!/bin/bash
# scripts/deploy_release.sh
# Usage: ./scripts/deploy_release.sh [branch] (defaults to main)
# Run as the deployment user
set -e

APP_ROOT="/home/$USER/chores_app"
RELEASES_DIR="$APP_ROOT/releases"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_release_DIR="$RELEASES_DIR/$TIMESTAMP"
REPO_URL="https://github.com/protoshoff/Chores-Tracking-and-Accounting.git"
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

# 4b. Install System Fonts (Roboto)
echo "Installing System Fonts..."
sudo apt-get update && sudo apt-get install -y fonts-roboto

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
# 8. Restart Services
# 8. Update Service Definitions (Ensure we use repo version)
echo "Updating Systemd Services..."
sudo cp "$NEW_release_DIR/ops/chores-kiosk.service" /etc/systemd/system/
sudo cp "$NEW_release_DIR/ops/chores-backend.service" /etc/systemd/system/

echo "Patching Service Files with correct User/Path..."
# 8a. Permissions: Ensure user can manage WiFi (netdev) and USB (plugdev)
echo "Ensuring user permission groups..."
sudo usermod -aG netdev $USER || echo "netdev group not found, skipping"
sudo usermod -aG plugdev $USER || echo "plugdev group not found, skipping"

# 8b. Patch Service Files (Replace 'pi' with current user)
sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-backend.service
sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-kiosk.service
sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-backend.service
sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-kiosk.service
sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-backend.service
sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-kiosk.service

sudo systemctl daemon-reload

# 8b. Update .xinitrc (Ensure it points to 'current' and logs properly)
echo "Updating .xinitrc..."
echo '#!/bin/bash' > /home/$USER/.xinitrc
echo "xset s off" >> /home/$USER/.xinitrc
echo "xset -dpms" >> /home/$USER/.xinitrc
echo "xset s noblank" >> /home/$USER/.xinitrc
echo "cd /home/$USER/chores_app/current" >> /home/$USER/.xinitrc
echo "exec venv/bin/python3 -u -m kiosk.main --fullscreen > /tmp/kiosk.log 2>&1" >> /home/$USER/.xinitrc
chmod +x /home/$USER/.xinitrc
chown $USER:$USER /home/$USER/.xinitrc

# 9. Restart Services
echo "Restarting Services..."
# Enable and start/restart
sudo systemctl enable chores-backend chores-kiosk
sudo systemctl restart chores-backend chores-kiosk

echo "Deployment Complete: $TIMESTAMP"
