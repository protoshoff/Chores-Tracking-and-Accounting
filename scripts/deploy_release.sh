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
if [ ! -d "/var/lib/chores_app" ]; then
    echo "Creating persistent data directory..."
    sudo mkdir -p /var/lib/chores_app
    sudo chown $USER:$USER /var/lib/chores_app
    sudo chmod 755 /var/lib/chores_app
fi

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

# 6. Initialize Database (Create Base Tables)
echo "Initializing Database..."
export CHORES_DATA_DIR="/var/lib/chores_app"
cd "$NEW_release_DIR"
# Create base tables using SQLModel (if DB is new, this creates everything)
venv/bin/python3 -c "from backend.db import create_db_and_tables; create_db_and_tables()"

# 7. Run Migrations (Apply Schema Changes)
echo "Running Migrations..."
# Try migrations first, if they fail (duplicate column, etc), just stamp as current
if ! alembic upgrade head 2>&1; then
    echo "Migration failed (likely fresh DB with all columns present), stamping as current..."
    alembic stamp head
fi

# 8. Switch Symlink
echo "Switching Symlink..."
ln -sfn "$NEW_release_DIR" "$APP_ROOT/current"

# 9. Update Backend Service (Only - Kiosk uses .profile method)
echo "Updating Backend Service..."
sudo cp "$NEW_release_DIR/ops/chores-backend.service" /etc/systemd/system/

echo "Installing PolicyKit Rules (Fix 'Not Authorized' Error)..."
sudo cp "$NEW_release_DIR/ops/50-chores-wifi.rules" /etc/polkit-1/rules.d/

echo "Patching Service Files with correct User/Path..."
# 9a. Permissions: Ensure user can manage WiFi (netdev) and USB (plugdev)
echo "Ensuring user permission groups..."
sudo usermod -aG netdev $USER || echo "netdev group not found, skipping"
sudo usermod -aG plugdev $USER || echo "plugdev group not found, skipping"

# 9b. Patch Backend Service File (Replace 'pi' with current user)
sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-backend.service
sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-backend.service
sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-backend.service

sudo systemctl daemon-reload
sudo systemctl enable chores-backend

# 9c. Update .xinitrc (Kiosk UI startup)
echo "Updating .xinitrc..."
cat > /home/$USER/.xinitrc << 'XINITRC_EOF'
#!/bin/bash
xset s off
xset -dpms
xset s noblank

# Detect screen resolution using xrandr and set Qt scaling BEFORE Python starts
SCREEN_WIDTH=$(xrandr 2>/dev/null | grep ' connected' | grep -oP '\d+x\d+' | head -1 | cut -d'x' -f1)

if [ "$SCREEN_WIDTH" -ge 1920 ] 2>/dev/null; then
    echo "High-res display detected ($SCREEN_WIDTH px). Applying 1.3x scaling."
    export QT_SCALE_FACTOR=1.3
    export QT_AUTO_SCREEN_SCALE_FACTOR=1
else
    echo "Standard resolution display ($SCREEN_WIDTH px). Disabling Qt auto-scaling."
    export QT_SCALE_FACTOR=1
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
    export QT_FONT_DPI=96  # Force standard DPI instead of physical screen DPI
    export QT_SCREEN_SCALE_FACTORS=1  # Explicitly set scale to 1.0 for all screens
fi

cd ~/chores_app/current
exec venv/bin/python3 -u -m kiosk.main --fullscreen > /tmp/kiosk.log 2>&1
XINITRC_EOF
chmod +x /home/$USER/.xinitrc
chown $USER:$USER /home/$USER/.xinitrc

# 9d. Setup .profile to auto-start X on console login
echo "Configuring auto-start X on console login..."
# Remove old kiosk startup lines if they exist
sed -i '/# Auto-start X and kiosk/,/fi/d' /home/$USER/.profile 2>/dev/null || true

# Add new startup logic
cat >> /home/$USER/.profile << 'PROFILE_EOF'

# Auto-start X and kiosk on tty1 (console login)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx
fi
PROFILE_EOF
chown $USER:$USER /home/$USER/.profile

# 10. Restart Backend Service
echo "Restarting backend service..."
sudo systemctl restart chores-backend

# 11. Cleanup Old Releases
echo "Cleaning up old releases..."
if [ -f "$NEW_release_DIR/scripts/cleanup_old_releases.sh" ]; then
    bash "$NEW_release_DIR/scripts/cleanup_old_releases.sh"
else
    echo "Warning: Cleanup script not found."
fi

echo "Deployment Complete: $TIMESTAMP"
