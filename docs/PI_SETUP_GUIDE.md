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
    sudo cp ~/chores_app/current/docs/ops/chores-backend.service /etc/systemd/system/
    sudo cp ~/chores_app/current/docs/ops/chores-kiosk.service /etc/systemd/system/
    
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
- **Black Screen**:
  - Usually means Python crashed before showing a window.
  - Check `/tmp/kiosk.log`.
  - Common culprit: Missing audio drivers (`pipewire`). If errors persist, install `gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-alsa`.

- **Window not Fullscreen**:
  - Ensure `.xinitrc` passes `--fullscreen`.
  - Ensure `openbox` is installed if you want window management, or use our "Frameless" mode in bare X11.
