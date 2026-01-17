# Ops & Deployment Specification

**Version:** 1.0
**Status:** DRAFT

## 1. System Overview

The Chores Kiosk runs on a Raspberry Pi 4. It consists of a FastAPI backend and a PySide6 (Qt) Kiosk UI. The system is designed for high availability, safe unattended updates, and power-loss resilience.

**Key constraints:**
- App boots directly into Kiosk UI (no desktop).
- No microSD removal required for updates.
- Database is backed up automatically.
- Atomic updates via symlinks.

## 2. Directory Structure

We use a "Capistrano-style" release structure to ensure atomic deployments.

```text
/opt/chores_app/
├── current -> releases/v1.0.0    # Symlink to the currently active version
├── releases/
│   ├── v1.0.0/                   # Immutable version folder
│   │   ├── backend/
│   │   │   ├── main.py
│   │   │   └── data/ -> /var/lib/chores_app/data/  (Symlink to persistent data)
│   │   ├── kiosk/
│   │   └── requirements.txt
│   └── v1.0.1/
├── venv/                         # Shared Virtual Environment
├── scripts/                      # Deployment & Maintenance Scripts
│   ├── deploy_release.sh
│   ├── rollback.sh
│   ├── backup_usb.sh
│   └── restore_usb.sh
└── env                           # Environment variables file

/var/lib/chores_app/              # Persistent Data Storage
├── chores.db
├── chores.db.bak                 # Last known good backup
├── config.json
└── avatars/
```

## 3. OS Configuration

**Base OS:** Raspberry Pi OS Lite (64-bit)

### 3.1. Auto-Login & Splash
Enable console auto-login to the `pi` user.
```bash
sudo raspi-config nonint do_boot_behaviour B2  # Console Autologin
```
*Note: We do NOT load a full Desktop Environment (GNOME/LXDE).*

### 3.2. Disable Screen Blanking
To prevent the screen from turning off (Kiosk mode):

**1. Kernel Command Line** (`/boot/cmdline.txt`)
Add `consoleblank=0` to the end of the line.

**2. X Server Config**
Create `~/.xinitrc`:
```bash
#!/bin/bash
xset s off      # Don't activate system screensaver (We handle it in-app globally)
xset -dpms      # Disable DPMS (Energy Star) features
xset s noblank  # Don't blank the video device
exec python3 /opt/chores_app/current/kiosk/main.py
```

### 3.3. Input Methods
We use a custom **HoloKeyboard** component built into the Kiosk app.
- No external virtual keyboard package (like `matchbox-keyboard`) is required.
- Text fields in "Manage Crew" and "Manage Quests" automatically trigger the on-screen keyboard.

### 3.4. Screen Protection
The application has a built-in screensaver to prevent burn-in.
- **Timeout**: 2 minutes of idle time.
- **Behavior**: Drifting "SYSTEM STANDBY" text on black background.
- **Wake**: Tap anywhere to wake. Security feature: Waking **always** returns to the Home Screen to prevent unauthorized access if the Admin panel was left open.

## 4. Systemd Services

We use two services: one for the backend API and one for the GUI Kiosk.

### 4.1. Backend Service (`/etc/systemd/system/chores-backend.service`)
The backend must start before the Kiosk.

```ini
[Unit]
Description=Chores App Backend API
After=network.target

[Service]
User=pi
Group=pi
WorkingDirectory=/opt/chores_app/current/backend
EnvironmentFile=/opt/chores_app/env
# Run uvicorn on all interfaces so local network devices can connect
ExecStart=/opt/chores_app/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 4.2. Kiosk Service (`/etc/systemd/system/chores-kiosk.service`)
This services launches X server and the Qt app.

```ini
[Unit]
Description=Chores App Kiosk UI
After=chores-backend.service
Wants=chores-backend.service

[Service]
User=pi
Group=pi
Environment=DISPLAY=:0
# startx launches X server which runs .xinitrc (defined above)
ExecStart=/usr/bin/startx -- -nocursor
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 5. Deployment & Update Mechanism

### 5.1. Update Strategy
Updates are delivered as a compressed archive (zip/tar) containing the new code.
**Trigger:** Parent uploads a `.zip` via the Admin Web UI, or runs a script.

### 5.2. `deploy_release.sh`
This script handles the safe update process.

```bash
#!/bin/bash
set -e

RELEASE_ARCHIVE=$1
VERSION_TAG=$2
RELEASE_DIR="/opt/chores_app/releases/$VERSION_TAG"
CURRENT_LINK="/opt/chores_app/current"
DB_PATH="/var/lib/chores_app/chores.db"

# 1. Validation
if [ -z "$RELEASE_ARCHIVE" ] || [ -z "$VERSION_TAG" ]; then
    echo "Usage: $0 <path_to_zip> <version_tag>"
    exit 1
fi

if [ -d "$RELEASE_DIR" ]; then
    echo "Version $VERSION_TAG already exists. Aborting."
    exit 1
fi

echo "Starting deployment of $VERSION_TAG..."

# 2. Extract Code
mkdir -p "$RELEASE_DIR"
unzip -q "$RELEASE_ARCHIVE" -d "$RELEASE_DIR"

# 3. Update Dependencies (if changed)
source /opt/chores_app/venv/bin/activate
pip install -r "$RELEASE_DIR/requirements.txt" --quiet

# 4. Backup Database (Pre-migration safety)
cp "$DB_PATH" "${DB_PATH}.pre_deploy_backup"

# 5. Run Migrations (Dry run or actual)
# Assuming backend has a migration script
python "$RELEASE_DIR/backend/manage.py" migrate

# 6. Healthcheck / Smoke Test
# Spin up the NEW backend on a temporary port to verify it starts
echo "Verifying build..."
# (Implementation dependent: could run pytest or check --help)

# 7. Atomic Switch
ln -sfn "$RELEASE_DIR" "$CURRENT_LINK"

# 8. Restart Services
sudo systemctl restart chores-backend
sudo systemctl restart chores-kiosk

echo "Deployment of $VERSION_TAG successful."
```

## 6. Rollback Procedure

### 6.1. `rollback.sh`
If an update fails or is buggy, we can instantly revert to the previous version.

```bash
#!/bin/bash
set -e

# Find the previous release directory
CURRENT_REAL_PATH=$(readlink -f /opt/chores_app/current)
PREVIOUS_VERSION=$(ls -dt /opt/chores_app/releases/*/ | grep -v "$CURRENT_REAL_PATH" | head -n 1)

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "No previous version found to rollback to."
    exit 1
fi

echo "Rolling back to $PREVIOUS_VERSION..."

# 1. Flip Symlink
ln -sfn "$PREVIOUS_VERSION" /opt/chores_app/current

# 2. Restore Database (Optional/Conditional)
# Ideally, migrations are backward compatible. If not:
# cp /var/lib/chores_app/chores.db.pre_deploy_backup /var/lib/chores_app/chores.db

# 3. Restart Services
sudo systemctl restart chores-backend
sudo systemctl restart chores-kiosk

echo "Rollback complete."
```

## 7. Backup & Restore (USB)

To survive SD card failure, we support USB backups.

### 7.1. Backup Flow
1. Parent inserts USB drive labeled `CHORES_BACKUP`.
2. `udev` rule triggers `backup_usb.sh`.
3. Script mounts drive, dumps DB and config, syncs to USB.
4. Script unmounts and plays a sound/blinks LED (via backend command).

**`backup_usb.sh` snippet:**
```bash
#!/bin/bash
MOUNT_POINT="/mnt/usb_backup"
BACKUP_DIR="$MOUNT_POINT/chores_backup_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"
# Stop backend to ensure DB integrity (or use sqlite3 .backup)
systemctl stop chores-backend

cp /var/lib/chores_app/chores.db "$BACKUP_DIR/"
cp /var/lib/chores_app/config.json "$BACKUP_DIR/"
cp -r /var/lib/chores_app/avatars "$BACKUP_DIR/"

systemctl start chores-backend
```

### 7.2. Restore Flow
1. Flash new SD card.
2. Place special file `restore.flag` on USB stick with backup data.
3. Insert USB on boot.
4. Launch script checks for `restore.flag`, restores data to `/var/lib/chores_app`, and deletes flag.
