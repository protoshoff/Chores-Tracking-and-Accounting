# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Quest2Earn Deployment

- **Repo:** `https://github.com/protoshoff/Chores-Tracking-and-Accounting.git` (branch: main)
- **Kiosk "Check for Updates" is fully self-contained** — no SSH needed
  - Backend endpoint `POST /api/system/update` does: `git pull ~/chores_repo` → runs `deploy_release.sh` → clones fresh from GitHub → reboots
  - `deploy_release.sh` lives in `~/chores_repo/scripts/` but auto-updates before running
- **Three Pi prototypes:** Pi 4B (primary), Pi 3B (fresh), Pi 4B w/ higher-res LCD (1.3x scaling)
- **DB:** SQLite at `/var/lib/chores_app/chores.db`
- **Startup migrations** run automatically via `create_db_and_tables()` in `backend/db.py`
