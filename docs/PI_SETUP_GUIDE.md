# Raspberry Pi Setup Guide

This guide provides step-by-step instructions for setting up a fresh Raspberry Pi 4 with the Chores Tracking Kiosk application.

> [!IMPORTANT]
> This guide has been tested on Raspberry Pi OS Lite (64-bit) Bookworm. Follow each step in order for a successful installation.

---

## Prerequisites

- Raspberry Pi 4 Model B (2GB+ RAM recommended)
- MicroSD card (32GB+ recommended)
- Touchscreen display
- Network connection (WiFi or Ethernet)
- Another computer to flash the SD card

---

## 1. OS Installation

1. Download and install **Raspberry Pi Imager** on your computer
2. In the Imager:
   - **OS:** Choose "Raspberry Pi OS Lite (64-bit)" (No Desktop Environment)
   - **Storage:** Select your MicroSD card
3. Click the **Settings** icon (gear) and configure:
   - **Hostname:** `chores-kiosk` (or your preference)
   - **Enable SSH:** ✅ Use password authentication
   - **Username:** `pi` (recommended, or your preference)
   - **Password:** Set a secure password
   - **WiFi:** Configure if using wireless (optional)
   - **Locale:** Set your timezone and keyboard layout
4. Click **Write** and wait for completion
5. Insert the MicroSD card into your Pi and power it on

---

## 2. Initial System Setup

SSH into your Pi from your computer:
```bash
ssh pi@chores-kiosk.local
# Or use the IP address if .local doesn't work: ssh pi@192.168.x.x
```

### Update System and Install Core Dependencies

```bash
# System updates
sudo apt update && sudo apt upgrade -y

# Core dependencies
sudo apt install -y git python3-venv python3-pip

# X11 & Window Manager (for GUI)
sudo apt install -y xserver-xorg x11-xserver-utils xinit openbox

# Qt dependencies (required for PySide6)
sudo apt install -y libgl1 libegl1 libpulse0 libasound2 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 \
    libxcb-xfixes0 libxcb-shape0 libxkbcommon-x11-0 libfontconfig1

# System fonts
sudo apt install -y fonts-roboto

# Allow non-console users to start X (required for systemd service)
sudo sed -i 's/allowed_users=console/allowed_users=anybody/g' /etc/X11/Xwrapper.config 2>/dev/null || \
    echo "allowed_users=anybody" | sudo tee /etc/X11/Xwrapper.config
```

### Configure Auto-Login

```bash
# Enable console auto-login (required for kiosk to start on boot)
sudo raspi-config nonint do_boot_behaviour B2
```

> [!NOTE]
> If the above command doesn't work, run `sudo raspi-config` manually and navigate to:
> **System Options → Boot / Auto Login → Console Autologin**
>
> **Why this works:** The deployment script configures your `.profile` to automatically start X (and the kiosk UI) when you login to the console. This method is more reliable across different Pi models (3B, 4B, etc.) than using a systemd service.

### Create Directory Structure

```bash
# Persistent data directory
sudo mkdir -p /var/lib/chores_app
sudo chown $USER:$USER /var/lib/chores_app

# App directory
mkdir -p ~/chores_app/releases

# Add user to required groups (for WiFi and USB access)
sudo usermod -aG netdev $USER 2>/dev/null || true
sudo usermod -aG plugdev $USER 2>/dev/null || true
```

---

## 3. Deploy Application

### Clone Repository

```bash
git clone https://github.com/protoshoff/Chores-Tracking-and-Accounting.git ~/chores_repo
```

### Run Deployment Script

The deployment script automates:
- Virtual environment creation
- Dependency installation  
- Database initialization and migrations
- Backend service installation and configuration
- Kiosk UI startup configuration (via `.profile` and `.xinitrc`)

```bash
chmod +x ~/chores_repo/scripts/*.sh
~/chores_repo/scripts/deploy_release.sh main
```

> [!NOTE]
> This step may take 10-15 minutes as it installs all Python packages including PySide6.

**What to expect:**
- Git clone of the repository
- Python virtual environment creation
- Package installations (lots of output)
- Database creation (you'll see CREATE TABLE statements)
- Migration application (with automatic fallback for fresh installs)
- Service installation messages
- **Success message with reboot instructions**

---

## 4. Reboot and Verify

```bash
sudo reboot
```

After reboot (typically 30-60 seconds):
- ✅ The Pi will auto-login to the console
- ✅ Your `.profile` will automatically start X
- ✅ The backend service will start automatically  
- ✅ The kiosk UI will launch via `.xinitrc`
- ✅ The touchscreen should show the Chores Kiosk interface

---

## 5. Verification

SSH back into your Pi to verify everything is running:

```bash
# Check service status
sudo systemctl status chores-backend --no-pager
sudo systemctl status chores-kiosk --no-pager

# Test backend API
curl http://localhost:8000/

# Expected: {"message":"Chores Kiosk API is running. Go to /docs for Swagger UI."}
```

Both services should show **`active (running)`** in green.

---

## 6. Troubleshooting

### Kiosk Not Displaying After Reboot

```bash
# Check if X is running
ps aux | grep startx

# Check kiosk logs
cat /tmp/kiosk.log

# Check X server logs
cat /var/log/Xorg.0.log | tail -50

# Verify .profile has X startup
cat ~/.profile | grep startx

# Test manual X start
startx
```

**Common causes:**
- Auto-login not configured: Re-run `sudo raspi-config nonint do_boot_behaviour B2`
- `.profile` missing X startup: The deployment script should have added it
- X dependencies missing: Re-run Qt dependency installation commands from Section 2

### Black Screen (X Starts but No UI)

```bash
# Check Python errors
cat /tmp/kiosk.log

# Install additional multimedia dependencies
sudo apt install -y gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-alsa pipewire
sudo systemctl restart chores-kiosk
```

### Backend Not Responding

```bash
# Check backend logs
sudo journalctl -u chores-backend -n 50

# Check if port 8000 is in use
sudo netstat -tlnp | grep 8000

# Restart backend
sudo systemctl restart chores-backend
```

### WiFi Issues

The kiosk includes a built-in WiFi configurator (System → WiFi). If it's not working:

```bash
# Enable WiFi radio
sudo nmcli radio wifi on

# List available networks
sudo nmcli device wifi list

# Connect manually
sudo nmcli device wifi connect "SSID" password "PASSWORD"
```

### Screen Rotation

If you need to rotate the display, edit `/boot/firmware/config.txt`:

```bash
sudo nano /boot/firmware/config.txt
# Add: display_rotate=1  (0=normal, 1=90°, 2=180°, 3=270°)
sudo reboot
```

---

## 7. Maintenance & Updates

### Update Application

```bash
# SSH into your Pi
cd ~/chores_repo
git pull
~/chores_repo/scripts/deploy_release.sh main
```

The deployment script automatically:
- Creates a new release
- Backs up the database
- Runs migrations
- Switches to the new version
- Restarts services

### View Logs

```bash
# Backend logs
sudo journalctl -u chores-backend -f

# Kiosk logs
cat /tmp/kiosk.log
```

### Backup Database

```bash
# Manual backup
cp /var/lib/chores_app/chores.db ~/chores_backup_$(date +%Y%m%d).db

# USB backup (if configured)
~/chores_app/current/scripts/backup_usb.sh
```

---

## 8. Next Steps

Once setup is complete:

1. **Configure Admin PIN:** Default is `0000` - change via database or admin UI
2. **Add Family Members:** Use Parent Mode to add kids to the system
3. **Create Chores:** Set up daily/weekly chores with rewards
4. **Explore Features:** Test the kiosk UI, WiFi settings, and admin portal

---

## Additional Resources

- **Architecture:** See `docs/ARCHITECTURE.md`
- **Database Schema:** See `docs/DB_SCHEMA.md`
- **API Documentation:** Access at `http://<pi-ip>:8000/docs`
- **Admin Portal:** Access at `http://<pi-ip>:8000/admin`

---

## Support

For issues or questions:
- Check `docs/SETUP_ISSUES_RESOLVED.md` for known issues and fixes
- Review the troubleshooting section above
- Check application logs for error messages

## 1. OS Installation
1.  Download **Raspberry Pi Imager**.
2.  Select **Raspberry Pi OS Lite (64-bit)** (No Desktop Environment).
3.  Click settings (gear icon):
    - Set hostname: `chores-kiosk`
    - Enable SSH only (Use password auth initially or your key).
    - Set username: `pi` (recommended) or your preferred username
    - Set password.
    - Configure WiFi (or skip if Ethernet).
4.  Write to MicroSD and boot.

## 2. System Level Config
SSH into the Pi: `ssh pi@chores-kiosk.local`

### A. Core Dependencies
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git python3-venv python3-pip libpq-dev
# X11 & Window Manager (Minimal)
sudo apt install -y xserver-xorg x11-xserver-utils xinit openbox
# Qt dependencies (Complete set for Qt 6.5+)
sudo apt install -y libgl1 libegl1 libpulse0 libasound2 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 \
    libxcb-xfixes0 libxcb-shape0 libxkbcommon-x11-0 libfontconfig1

# Allow non-console user to start X (Required for systemd service)
sudo sed -i 's/allowed_users=console/allowed_users=anybody/g' /etc/X11/Xwrapper.config || echo "allowed_users=anybody" | sudo tee /etc/X11/Xwrapper.config
```

### B. Auto-Login
1.  Run `sudo raspi-config`.
2.  System Options -> Boot / Auto Login -> **Console Autologin**.
3.  Finish and Reboot.

### C. Touchscreen Rotation (If needed)
Edit `/boot/firmware/config.txt` to add `dtoverlay=vc4-kms-v3d,rotate=xxx` if using official screen, or standard HDMI rotation.

## 3. Database Volume
We use `/var/lib/chores_app/` for the SQLite DB so it persists outside release folders.
```bash
sudo mkdir -p /var/lib/chores_app
sudo chown $USER:$USER /var/lib/chores_app
```

## 4. App Directory Structure
```bash
mkdir -p ~/chores_app/releases
```

## 5. First Deployment (Public Repo)

> [!NOTE]
> The deployment script (`deploy_release.sh`) automates most of the setup process including:
> - Creating release directory and virtual environment
> - Installing dependencies
> - Database initialization and migrations
> - Service installation and configuration
> - Creating `.xinitrc` for kiosk mode

1.  **Clone Repo**:
    On the Pi:
    ```bash
    git clone https://github.com/protoshoff/Chores-Tracking-and-Accounting.git ~/chores_repo
    ```

2.  **Run Deployment Script**:
    ```bash
    chmod +x ~/chores_repo/scripts/*.sh
    ~/chores_repo/scripts/deploy_release.sh main
    ```

3.  **Services Installation**:
    The deployment script handles service installation automatically. If you need to manually install:
    ```bash
    sudo cp ~/chores_app/current/ops/chores-backend.service /etc/systemd/system/
    sudo cp ~/chores_app/current/ops/chores-kiosk.service /etc/systemd/system/
    
    # Update service user and paths
    # 1. Update User/Group
    sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-backend.service
    sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-kiosk.service
    sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-kiosk.service
    
    # 2. Update Paths (replace /home/pi with /home/$USER)
    sudo sed -i "s|/home/pi|/home/$USER|g" /etc/systemd/system/chores-backend.service

    # 3. Create .xinitrc for Kiosk Mode
    echo '#!/bin/bash' > ~/.xinitrc
    echo "xset s off" >> ~/.xinitrc
    echo "xset -dpms" >> ~/.xinitrc
    echo "xset s noblank" >> ~/.xinitrc
    echo "xrandr > /tmp/xrandr.log" >> ~/.xinitrc
    echo "cd /home/$USER/chores_app/current" >> ~/.xinitrc
    echo "exec venv/bin/python3 -u -m kiosk.main --fullscreen > /tmp/kiosk.log 2>&1" >> ~/.xinitrc
    chmod +x ~/.xinitrc
    
    # Reload & Enable
    sudo systemctl daemon-reload
    sudo systemctl enable chores-backend
    sudo systemctl enable chores-kiosk
    ```
4.  **Reboot**:
    ```bash
    sudo reboot
    ```
The Kiosk should now start automatically on TV/Screen.


## 6. Maintenance
- **Update**: Commit/Push changes, then SSH in and run `deploy_release.sh`.
- **Logs**:
    - Backend: `journalctl -u chores-backend -f`
    - Kiosk: `cat /tmp/kiosk.log` (stdout/stderr is redirected here for robustness)

### 7. WiFi Management
The Kiosk includes a built-in WiFi configurator (System -> WiFi).
- **Persistence:** Connections created via the Kiosk use `nmcli`, which automatically saves a persistent profile with `autoconnect=yes`. The Pi will reconnect automatically after a reboot.
- **Troubleshooting:**
    - If the "Scan" button shows no networks, ensure the radio is not soft-blocked: `sudo nmcli radio wifi on`.
    - If "Hardware Missing" error occurs, ensure you are not using a Pi Zero without WiFi.
    - Check the backend logs for scan errors: `sudo journalctl -u chores-backend`.

### 8. Troubleshooting & Maintenance

#### Post-Reboot Issues
- **Kiosk doesn't start after reboot**:
  - Check service status: `sudo systemctl status chores-kiosk`
  - Check logs: `cat /tmp/kiosk.log` and `cat /var/log/Xorg.0.log`
  - Verify user group membership took effect: `groups` (should include `netdev`, `plugdev`)
  - If groups are missing, re-login or reboot again
  - Manually restart: `sudo systemctl restart chores-kiosk`

- **Black Screen**:
  - Usually means Python crashed before showing a window.
  - Check `/tmp/kiosk.log`.
  - Common culprit: Missing audio drivers (`pipewire`). If errors persist, install `gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-alsa`.

- **Window not Fullscreen**:
  - Ensure `.xinitrc` passes `--fullscreen`.
  - Ensure `openbox` is installed if you want window management, or use our "Frameless" mode in bare X11.
