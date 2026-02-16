import os
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, text
from ..db import get_session, engine, create_db_and_tables
from ..models import User, Settings

router = APIRouter(prefix="/api/debug", tags=["Debug"])


class ResetRequest(BaseModel):
    pin: str


@router.post("/reset")
def reset_database(payload: ResetRequest, session: Session = Depends(get_session)):
    # Require PIN verification to prevent accidental/malicious resets
    from ..services.pin import verify_pin
    setting = session.get(Settings, "parent_pin")
    stored_pin = setting.value if setting else "1234"
    if not verify_pin(payload.pin, stored_pin):
        raise HTTPException(status_code=403, detail="PIN required to reset database")
    """
    WARNING: Drops all tables and recreates them. Adds a dummy user.
    """
    # This is rough but effective for dev.
    # In production, this should be disabled or protected.
    
    # Close session to allow drop
    session.close()
    
    # Drop all
    from sqlmodel import SQLModel
    SQLModel.metadata.drop_all(engine)
    
    # Recreate
    create_db_and_tables()
    
    # Seed
    with Session(engine) as session:
        alice = User(name="Grayson", balance=12.50, allowance=5.00, avatar_path="/static/avatars/grayson.png")
        bob = User(name="Owen", balance=0.0, allowance=5.00, avatar_path="/static/avatars/owen.png")
        session.add(alice)
        session.add(bob)
        session.commit()
    
        # Add Chores
        from ..models import Chore, Frequency
        c1 = Chore(kid_id=alice.id, name="Walk Dog", frequency=Frequency.DAILY, reward=1.0)
        c2 = Chore(kid_id=alice.id, name="Wash Dishes", frequency=Frequency.DAILY, reward=1.0)
        c3 = Chore(kid_id=bob.id, name="Clean Room", frequency=Frequency.WEEKLY, reward=3.0)
        session.add(c1)
        session.add(c2)
        session.add(c3)
        session.commit()
    
    return {"status": "Database reset and seeded"}
