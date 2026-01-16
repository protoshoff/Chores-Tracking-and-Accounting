from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text
from ..db import get_session, engine, create_db_and_tables
from ..models import User

router = APIRouter(prefix="/api/debug", tags=["Debug"])

@router.post("/reset")
def reset_database(session: Session = Depends(get_session)):
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
        alice = User(name="Alice", balance_cents=1250, allowance_cents=500, avatar_path="/static/avatars/alice.png")
        bob = User(name="Bob", balance_cents=0, allowance_cents=500, avatar_path="/static/avatars/bob.png")
        session.add(alice)
        session.add(bob)
        session.commit()
    
        # Add Chores
        from ..models import Chore, Frequency
        c1 = Chore(kid_id=alice.id, name="Walk Dog", frequency=Frequency.DAILY, weight=1)
        c2 = Chore(kid_id=alice.id, name="Wash Dishes", frequency=Frequency.DAILY, weight=1)
        c3 = Chore(kid_id=bob.id, name="Clean Room", frequency=Frequency.WEEKLY, weight=3)
        session.add(c1)
        session.add(c2)
        session.add(c3)
        session.commit()
    
    return {"status": "Database reset and seeded"}
