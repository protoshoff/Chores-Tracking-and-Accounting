# Kiosk Startup Method: .profile vs systemd service

## Decision: Use .profile Method

**Date:** 2026-02-15  
**Tested on:** Raspberry Pi 3B, Raspberry Pi 4B

## Problem with systemd Service Approach

The original deployment used a systemd service (`chores-kiosk.service`) to start X:

```ini
[Service]
ExecStart=/usr/bin/startx
```

**Issue:** `startx` requires access to the console TTY, which systemd services don't reliably have. This causes:
- **Error:** "Couldn't get a file descriptor referring to the console"
- **Error:** "Server terminated with error (1)"
- Behavior varies between Pi models (worked on Pi 4B, failed on Pi 3B)

## Solution: .profile Auto-start

Instead, configure X to start from the user's login shell:

**`~/.profile`:**
```bash
# Auto-start X and kiosk on tty1 (console login)
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
    exec startx
fi
```

**`~/.xinitrc`:**
```bash
#!/bin/bash
xset s off
xset -dpms
xset s noblank
cd ~/chores_app/current
exec venv/bin/python3 -u -m kiosk.main --fullscreen > /tmp/kiosk.log 2>&1
```

## Why This Works

1. **Console auto-login** → User logs in to tty1
2. **`.profile` executes** → Checks if on console and X not running
3. **Starts X** → `startx` has proper TTY access
4. **`.xinitrc` runs** → Launches kiosk UI

## Benefits

✅ **Reliable across Pi models** - Works on Pi 3B, 4B, etc.  
✅ **Standard approach** - This is how most kiosk systems work  
✅ **Clean process hierarchy** - X runs under user session, not systemd  
✅ **Easy debugging** - Standard X logs and process tree  
✅ **No TTY permission issues** - User owns the console session

## Implementation in Deployment Script

The `deploy_release.sh` now:
1. Creates `.xinitrc` with kiosk startup
2. Adds X auto-start logic to `.profile`
3. Installs **only** the backend service (not kiosk service)
4. Relies on console auto-login + `.profile` for kiosk

## Legacy Files

- `ops/chores-kiosk.service` - **NOT USED** (kept for reference only)
- Backend still uses systemd: `chores-backend.service`

## Testing Checklist

When deploying on a new Pi model:
- [ ] Console auto-login configured
- [ ] `.profile` has X startup logic
- [ ] `.xinitrc` exists and is executable
- [ ] Reboot test - kiosk appears automatically
- [ ] Backend service running independently

## References

- [ArchWiki: Xinit](https://wiki.archlinux.org/title/Xinit)
- [Raspberry Pi Kiosk Mode](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/)
