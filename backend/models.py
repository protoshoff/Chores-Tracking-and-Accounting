from typing import Optional, List
from datetime import datetime, time, date as dt_date # Alias to avoid collision
from sqlmodel import Field, SQLModel, Relationship
from enum import Enum

# --- Enums ---
class Frequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"

class ChoreStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INCOMPLETE = "INCOMPLETE"

class TransactionType(str, Enum):
    ALLOWANCE = "ALLOWANCE"
    BONUS = "BONUS"
    SPEND = "SPEND"
    PAYOUT = "PAYOUT"
    ADJUSTMENT = "ADJUSTMENT"

class PayoutMode(str, Enum):
    PRORATED = "PRORATED"
    ALL_OR_NOTHING = "ALL_OR_NOTHING"

# --- Tables ---

class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    pin_hash: Optional[str] = None
    avatar_path: str = Field(default="/static/default_avatar.png")
    allowance_cents: int = Field(default=0)
    balance_cents: int = Field(default=0)
    is_active: bool = Field(default=True)
    
    chores: List["Chore"] = Relationship(back_populates="kid")
    chore_logs: List["ChoreLog"] = Relationship(back_populates="kid")
    ledger_entries: List["LedgerEntry"] = Relationship(back_populates="kid")

class Chore(SQLModel, table=True):
    __tablename__ = "chores"
    id: Optional[int] = Field(default=None, primary_key=True)
    kid_id: int = Field(foreign_key="users.id", index=True)
    name: str
    description: Optional[str] = None
    icon_name: str = Field(default="star") # Default icon
    weight: int = Field(default=1)
    frequency: Frequency
    due_time: Optional[time] = Field(default=None)
    archived: bool = Field(default=False)
    
    kid: User = Relationship(back_populates="chores")
    logs: List["ChoreLog"] = Relationship(back_populates="chore")

class ChoreLog(SQLModel, table=True):
    __tablename__ = "chore_log"
    id: Optional[int] = Field(default=None, primary_key=True)
    chore_id: int = Field(foreign_key="chores.id")
    kid_id: int = Field(foreign_key="users.id", index=True)
    week_id: str = Field(index=True) # "YYYY-W##"
    date: dt_date = Field(index=True)
    status: ChoreStatus = Field(default=ChoreStatus.INCOMPLETE, index=True)
    completed_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    chore: Chore = Relationship(back_populates="logs")
    kid: User = Relationship(back_populates="chore_logs")

class LedgerEntry(SQLModel, table=True):
    __tablename__ = "ledger_entries"
    id: Optional[int] = Field(default=None, primary_key=True)
    kid_id: int = Field(foreign_key="users.id", index=True)
    transaction_type: TransactionType
    amount_cents: int
    description: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    week_id: Optional[str] = None
    
    kid: User = Relationship(back_populates="ledger_entries")

class WeeklyRollup(SQLModel, table=True):
    __tablename__ = "weekly_rollups"
    id: Optional[int] = Field(default=None, primary_key=True)
    kid_id: int = Field(foreign_key="users.id")
    week_id: str
    total_weight_possible: int
    total_weight_completed: int
    payout_cents: int
    finalized_at: datetime = Field(default_factory=datetime.utcnow)

class Streak(SQLModel, table=True):
    __tablename__ = "streaks"
    kid_id: int = Field(foreign_key="users.id", primary_key=True)
    current_streak_days: int = Field(default=0)
    last_completed_date: Optional[dt_date] = None
    max_streak_days: int = Field(default=0)

class Settings(SQLModel, table=True):
    __tablename__ = "settings"
    key: str = Field(primary_key=True)
    value: str # JSON encoded
