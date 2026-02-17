from sqlmodel import SQLModel, create_engine, Session, select
import os

# Ensure the data directory exists
DATA_DIR = os.getenv("CHORES_DATA_DIR", "/var/lib/chores_app")
# For dev, fallback to current dir if /var/lib not writable or configured
if not os.access(DATA_DIR, os.W_OK):
    DATA_DIR = "."

DB_NAME = "chores.db"
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, DB_NAME)}"

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)

def create_db_and_tables():
    # Import models so they're registered in SQLModel.metadata
    from backend.models import (
        User, Chore, ChoreLog, LedgerEntry, 
        WeeklyRollup, Streak, Settings,
        RotationGroup, RotationMember, RotationLog
    )
    SQLModel.metadata.create_all(engine)
    seed_default_settings()
    fix_week_id_format()

def fix_week_id_format():
    """One-time migration: convert old %Y-W%W week_ids to ISO %G-W%V format."""
    from backend.models import ChoreLog
    with Session(engine) as session:
        # Find logs with potentially old-format week_ids and recalculate
        logs = session.exec(select(ChoreLog).where(ChoreLog.date != None)).all()
        fixed = 0
        for log in logs:
            if log.date is None:
                continue
            correct_week_id = log.date.strftime("%G-W%V")
            if log.week_id != correct_week_id:
                log.week_id = correct_week_id
                session.add(log)
                fixed += 1
        if fixed > 0:
            session.commit()
            print(f"Fixed {fixed} ChoreLog week_id values to ISO format")


def seed_default_settings():
    """Initialize default settings if they don't exist"""
    from backend.models import Settings
    
    defaults = {
        "payout_day": "6",      # Sunday (0=Mon, 6=Sun)
        "payout_hour": "0",     # Midnight
        "payout_minute": "5",   # 00:05
    }
    
    # Auto-detect timezone from system
    try:
        with open('/etc/timezone', 'r') as f:
            defaults["timezone"] = f.read().strip()
    except Exception:
        defaults["timezone"] = "America/Phoenix"  # Safe fallback
    
    with Session(engine) as session:
        for key, value in defaults.items():
            existing = session.get(Settings, key)
            if not existing:
                session.add(Settings(key=key, value=value))
        session.commit()

def get_session():
    with Session(engine) as session:
        yield session
