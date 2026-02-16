#!/bin/bash
# scripts/deploy_release.sh
# Usage: ./scripts/deploy_release.sh [branch] (defaults to main)
# Run as the deployment user
#
# NOTE: Do NOT use 'set -e' — individual failures are handled gracefully
# so the deploy always reaches the reboot step.

APP_ROOT="/home/$USER/chores_app"
RELEASES_DIR="$APP_ROOT/releases"
TIMESTAMP=$(date +%Y%m%d%H%M%S)
NEW_RELEASE_DIR="$RELEASES_DIR/$TIMESTAMP"
REPO_URL="https://github.com/protoshoff/Chores-Tracking-and-Accounting.git"
LOG_FILE="$APP_ROOT/deploy.log"
BRANCH=${1:-main}

# Redirect all output to log file AND stdout
exec > >(tee -a "$LOG_FILE") 2>&1

echo ""
echo "=========================================="
echo "DEPLOY STARTED: $(date)"
echo "Branch: $BRANCH"
echo "Target: $NEW_RELEASE_DIR"
echo "=========================================="

# Track if any step failed (but continue anyway)
DEPLOY_OK=true

# 1. Ensure directories
mkdir -p "$RELEASES_DIR"
if [ ! -d "/var/lib/chores_app" ]; then
    echo "[1/10] Creating persistent data directory..."
    sudo mkdir -p /var/lib/chores_app
    sudo chown $USER:$USER /var/lib/chores_app
    sudo chmod 755 /var/lib/chores_app
fi

# 2. Clone code
echo "[2/10] Cloning from GitHub..."
if ! git clone -b "$BRANCH" --depth 1 "$REPO_URL" "$NEW_RELEASE_DIR"; then
    echo "FATAL: Git clone failed. Aborting."
    echo "DEPLOY FAILED: $(date)" 
    # Still reboot to recover the kiosk from the update screen
    nohup sudo shutdown -r now "Deploy failed - rebooting to recover" &>/dev/null &
    exit 1
fi

# 3. Setup venv
echo "[3/10] Setting up venv..."
python3 -m venv "$NEW_RELEASE_DIR/venv"
source "$NEW_RELEASE_DIR/venv/bin/activate"

# 4. Install deps
echo "[4/10] Installing dependencies..."
if ! pip install -r "$NEW_RELEASE_DIR/requirements.txt"; then
    echo "WARNING: pip install failed — continuing with partial deps"
    DEPLOY_OK=false
fi

# 4b. Fonts (skip if already installed)
if ! fc-list | grep -qi roboto; then
    echo "[4b/10] Installing Roboto fonts..."
    sudo apt-get update -qq && sudo apt-get install -y -qq fonts-roboto || echo "WARNING: Font install failed"
else
    echo "[4b/10] Roboto fonts already installed, skipping."
fi

# 5. Backup DB
DB_PATH="/var/lib/chores_app/chores.db"
if [ -f "$DB_PATH" ]; then
    echo "[5/10] Backing up DB..."
    cp "$DB_PATH" "$DB_PATH.bak.$TIMESTAMP"
    # Clean old backups (keep last 10)
    ls -t "$DB_PATH".bak.* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null
fi

# 6. Initialize Database
echo "[6/10] Initializing database..."
export CHORES_DATA_DIR="/var/lib/chores_app"
cd "$NEW_RELEASE_DIR"
if ! venv/bin/python3 -c "from backend.db import create_db_and_tables; create_db_and_tables()" 2>&1; then
    echo "WARNING: DB init failed — tables may already exist (OK for upgrades)"
    DEPLOY_OK=false
fi

# 7. Run Migrations (non-fatal — may fail if already applied or no migration history)
echo "[7/10] Running migrations..."
if ! venv/bin/python3 -m alembic upgrade head 2>&1; then
    echo "WARNING: Alembic migration failed — this is often OK (tables created by SQLModel)"
    # Try stamping current state so future migrations work
    venv/bin/python3 -m alembic stamp head 2>&1 || true
fi

# 8. Switch Symlink
echo "[8/10] Switching symlink..."
ln -sfn "$NEW_RELEASE_DIR" "$APP_ROOT/current"

# 9. Update services
echo "[9/10] Updating systemd services..."
sudo cp "$NEW_RELEASE_DIR/ops/chores-kiosk.service" /etc/systemd/system/ 2>/dev/null || true
sudo cp "$NEW_RELEASE_DIR/ops/chores-backend.service" /etc/systemd/system/ 2>/dev/null || true
sudo cp "$NEW_RELEASE_DIR/ops/50-chores-wifi.rules" /etc/polkit-1/rules.d/ 2>/dev/null || true

# Patch user/paths
sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-backend.service 2>/dev/null || true
sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-kiosk.service 2>/dev/null || true
sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-backend.service 2>/dev/null || true
sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-kiosk.service 2>/dev/null || true
sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-backend.service 2>/dev/null || true
sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-kiosk.service 2>/dev/null || true

sudo usermod -aG netdev $USER 2>/dev/null || true
sudo usermod -aG plugdev $USER 2>/dev/null || true
sudo systemctl daemon-reload

# Update .xinitrc
cat > /home/$USER/.xinitrc << 'XINITRC_EOF'
#!/bin/bash
xset s off
xset -dpms
xset s noblank
sleep 1

PRIMARY_OUTPUT=$(xrandr | grep " connected primary" | cut -d' ' -f1)
AVAILABLE_MODES=$(xrandr | grep -A 20 "^$PRIMARY_OUTPUT" | grep -oP '\d{3,4}x\d{3,4}' | sort -u)

if echo "$AVAILABLE_MODES" | grep -q "1920x1200"; then
    xrandr --output $PRIMARY_OUTPUT --mode 1920x1200 || xrandr --output $PRIMARY_OUTPUT --auto
    export QT_SCALE_FACTOR=1.3
    export QT_AUTO_SCREEN_SCALE_FACTOR=1
elif echo "$AVAILABLE_MODES" | grep -q "1600x900"; then
    xrandr --output $PRIMARY_OUTPUT --mode 1600x900 || xrandr --output $PRIMARY_OUTPUT --auto
    export QT_SCALE_FACTOR=1
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
else
    xrandr --output $PRIMARY_OUTPUT --auto
    export QT_SCALE_FACTOR=1
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
fi

cd ~/chores_app/current
exec venv/bin/python3 -u -m kiosk.main --fullscreen > /tmp/kiosk.log 2>&1
XINITRC_EOF
chmod +x /home/$USER/.xinitrc
chown $USER:$USER /home/$USER/.xinitrc

# 10. Cleanup old releases (keep last 5)
echo "[10/10] Cleaning up old releases..."
ls -dt "$RELEASES_DIR"/*/ 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true

if [ "$DEPLOY_OK" = true ]; then
    echo "=========================================="
    echo "DEPLOY SUCCESSFUL: $(date)"
    echo "=========================================="
else
    echo "=========================================="
    echo "DEPLOY COMPLETED WITH WARNINGS: $(date)"
    echo "=========================================="
fi

# 11. Reboot (ALWAYS runs — even if steps above failed)
echo "Rebooting..."
sudo systemctl enable chores-backend chores-kiosk 2>/dev/null || true
nohup sudo shutdown -r now "Chores app updated - rebooting..." &>/dev/null &
