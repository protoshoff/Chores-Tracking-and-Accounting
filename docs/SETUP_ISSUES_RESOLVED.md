# Setup Issues Resolved (February 2026)

This document details critical issues discovered during a fresh Raspberry Pi setup and the fixes applied.

## Issues Discovered

### 1. Database Migration Failure ⚠️ **CRITICAL**

**Problem:**
- The initial Alembic migration (`8165403687aa_initial_migration.py`) had empty `upgrade()` and `downgrade()` functions
- The migration tried to run before any tables existed
- The second migration (`999999999999_add_due_day.py`) failed with "no such table: chores"

**Root Cause:**
- `backend/db.py`'s `create_db_and_tables()` function didn't import model classes
- When `SQLModel.metadata.create_all()` was called, the metadata was empty (no tables registered)
- Alembic migrations ran before base tables were created

**Fix Applied:**
1. Updated `backend/db.py` to import all model classes in `create_db_and_tables()`
2. Modified `deploy_release.sh` to initialize database BEFORE running migrations:
   ```bash
   # 6. Initialize Database (Create Base Tables)
   venv/bin/python3 -c "from backend.db import create_db_and_tables; create_db_and_tables()"
   
   # 7. Run Migrations (Apply Schema Changes)
   alembic upgrade head
   ```

**Files Changed:**
- `backend/db.py` - Added model imports
- `scripts/deploy_release.sh` - Reordered DB setup steps

---

### 2. Service File Path Hardcoded to `/home/pi` ⚠️ **CRITICAL**

**Problem:**
- Service files (`ops/chores-backend.service`, `ops/chores-kiosk.service`) hardcoded `User=pi` and paths to `/home/pi`
- Installation failed if using a different username (e.g., `chores-tracker`)
- WorkingDirectory pointed to non-existent path

**Fix Applied:**
- `deploy_release.sh` already had `sed` commands to replace `pi` with `$USER`
- These worked correctly once the script completed successfully

**No Code Changes Needed** - Existing fix was adequate

---

### 3. Service File Boot Target Mismatch ⚠️ **CRITICAL**

**Problem:**
- `ops/chores-kiosk.service` was configured with `WantedBy=graphical.target`
- Pi boots to console auto-login which reaches `multi-user.target`, not `graphical.target`
- Kiosk service never started on boot
- Service worked fine when manually started, but failed after reboot

**Root Cause:**
- Console auto-login doesn't reach `graphical.target`
- The kiosk starts X itself via `startx`, so it doesn't need `graphical.target`

**Fix Applied:**
- Changed `WantedBy=graphical.target` to `WantedBy=multi-user.target`
- Removed `graphical.target` from `After=` directive
- Added comment explaining why

**Files Changed:**
- `ops/chores-kiosk.service`

---

### 4. Documentation Errors

**Problems:**
- Typo: "Endvironment" instead of "Environment" (line 7)
- Incorrect path: `docs/ops/` instead of `ops/` (line 72)
- Missing clarification that `deploy_release.sh` handles most setup automatically

**Fixes Applied:**
- Fixed typo in `PI_SETUP_GUIDE.md`
- Corrected service file paths
- Added note about automated deployment script

**Files Changed:**
- `docs/PI_SETUP_GUIDE.md`

---

## Testing Results

The fixes were validated on a fresh Raspberry Pi 4B with:
- **OS:** Raspberry Pi OS Lite (64-bit) Bookworm
- **User:** `chores-tracker` (non-default username to test path fixes)
- **Hardware:** Official Raspberry Pi touchscreen

**Result:** ✅ **Successful deployment, boot, and automatic startup on first try with updated code**

---

## Summary of Code Changes

### `backend/db.py`
```diff
 def create_db_and_tables():
+    # Import models so they're registered in SQLModel.metadata
+    from backend.models import (
+        User, Chore, ChoreLog, LedgerEntry, 
+        WeeklyRollup, Streak, Settings
+    )
     SQLModel.metadata.create_all(engine)
```

### `scripts/deploy_release.sh`
```diff
-# 6. Migrate DB
+# 6. Initialize Database (Create Base Tables)
+echo "Initializing Database..."
+export CHORES_DATA_DIR="/var/lib/chores_app"
+cd "$NEW_release_DIR"
+# Create base tables using SQLModel (if DB is new, this creates everything)
+venv/bin/python3 -c "from backend.db import create_db_and_tables; create_db_and_tables()"
+
+# 7. Run Migrations (Apply Schema Changes)
 echo "Running Migrations..."
-# We need to set CHORES_DATA_DIR env if DB is there
-export CHORES_DATA_DIR="/var/lib/chores_app"
-cd "$NEW_release_DIR"
 alembic upgrade head
```

### `ops/chores-kiosk.service`
```diff
 [Unit]
 Description=Chores Kiosk UI
-After=graphical.target chores-backend.service
+After=chores-backend.service
+# Kiosk starts X directly from console login, no need for graphical.target
 
 [Install]
-WantedBy=graphical.target
+WantedBy=multi-user.target
```

### `docs/PI_SETUP_GUIDE.md`
- Complete rewrite for clarity and accuracy
- Fixed typos and incorrect paths
- Added comprehensive troubleshooting section
- Structured as step-by-step guide with verification points

---

## Recommendations

1. ✅ **Test fresh installations regularly** - These issues would have been caught with periodic clean Pi setups
2. ✅ **Use non-default usernames in testing** - Catches hardcoded paths
3. ✅ **Always test reboots** - Catches systemd target mismatches and boot issues
4. ✅ **Document assumptions** - The empty initial migration should have had comments explaining the SQLModel initialization pattern
5. 🔄 **Consider consolidating migrations** - Generate a comprehensive initial migration that includes all base tables

---

## Status

- [x] All critical bugs fixed
- [x] Code changes applied
- [x] Documentation completely rewritten
- [x] Tested on fresh Pi installation (including reboot)
- [x] Ready for commit and deployment
