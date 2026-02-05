from sqlmodel import SQLModel, create_engine, Session
import os

# Ensure the data directory exists
DATA_DIR = os.getenv("CHORES_DATA_DIR", "/var/lib/chores_app")
# For dev, fallback to current dir if /var/lib not writable or configured
if not os.access(DATA_DIR, os.W_OK):
    DATA_DIR = "."

DB_NAME = "chores.db"
DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, DB_NAME)}"

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, echo=True, connect_args=connect_args)

def create_db_and_tables():
    # Import models so they're registered in SQLModel.metadata
    from backend.models import (
        User, Chore, ChoreLog, LedgerEntry, 
        WeeklyRollup, Streak, Settings
    )
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
