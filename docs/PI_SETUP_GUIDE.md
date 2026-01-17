# Raspberry Pi Setup Guide

This guide details the steps to configure a fresh Raspberry Pi 4 for the Chores Kiosk.

## 1. OS Installation
1.  Download **Raspberry Pi Imager**.
2.  Select **Raspberry Pi OS Lite (64-bit)** (No Desktop Endvironment).
3.  Click settings (gear icon):
    - Set hostname: `chores-kiosk`
    - Enable SSH only (Use password auth initially or your key).
    - Set username: `pi`
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
# Qt dependencies
sudo apt install -y libgl1 libegl1
# If explicit platform plugin required later: libxcb-cursor0
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

3.  **Install Services**:
    ```bash
    sudo cp /opt/chores_app/current/docs/ops/chores-backend.service /etc/systemd/system/
    sudo cp /opt/chores_app/current/docs/ops/chores-kiosk.service /etc/systemd/system/
    
    # Update service user if not 'pi'
    sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-backend.service
    sudo sed -i "s/User=pi/User=$USER/g" /etc/systemd/system/chores-kiosk.service
    sudo sed -i "s/Group=pi/Group=$USER/g" /etc/systemd/system/chores-kiosk.service
    
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
    - Kiosk: `journalctl -u chores-kiosk -f`
