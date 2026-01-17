# Chores Tracking Kiosk (v1.0)

A Gamified Chores & Allowance Tracking System for Raspberry Pi.
Designed with a "Sci-Fi / Space Ops" aesthetic.

## Features (v1.0)
- **Kid Dashboard**: View assigned quests (chores), mark them as complete, and see weekly earnings.
- **Parent Mode**: Secure PIN access to approve/reject chores and manage the system.
- **Quest Management**: Create/Edit daily or weekly chores with XP weights.
- **Crew Management**: Add/Edit kids and set allowance rates.
- **Financial Tracking**: Automatic weekly payouts (Sundays), ledger history, and customizable allowance logic.
- **Streak Tracking**: daily streak calculation to gamify consistency.
- **Immersive UI**: Full-screen kiosk mode, sound effects, animations, and on-screen "HoloKeyboard" for touch input.
- **System Protection**: Auto-screensaver (2 min idle) and burn-in protection.
- **Operations**: USB Backup/Restore scripts and "Release Folder" deployment strategy.

## Installation (Development)

1. **Clone & Setup**:
   ```bash
   git clone <repo_url>
   cd Chores-Tracking-and-Accounting
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   ```bash
   # Auto-created on first run at /var/lib/chores_app/chores.db (or local backend/chores.db if dev)
   # To force init:
   python -c "from backend.db import create_db_and_tables; create_db_and_tables()"
   ```

3. **Run Backend** (Terminal 1):
   ```bash
   uvicorn backend.main:app --reload
   ```

4. **Run Kiosk** (Terminal 2):
   ```bash
   python kiosk/main.py
   ```

## Deployment (Raspberry Pi)
See [docs/OPS_DEPLOYMENT.md](docs/OPS_DEPLOYMENT.md) for full details on:
- Setting up the Pi (Auto-login, X11).
- Systemd services (`chores-backend`, `chores-kiosk`).
- Update scripts (`deploy_release.sh`).
- USB Backup/Restore procedures.

## Admin Config
- **Default PIN**: `0000` (Change in database or via future UI update).
- **Admin Portal**: Accessible at `http://<pi-ip>:8000/admin`.

## Project Structure
- `backend/`: FastAPI application, database models, and logic.
- `kiosk/`: PySide6 (Qt) application for the touchscreen interface.
- `docs/`: Architecture, Database Schema, and deployment guides.
- `scripts/`: Operational scripts for backup, restore, and deployment.

**Status**: v1.0 RELEASED
