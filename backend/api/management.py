from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from pydantic import BaseModel
from ..db import get_session
from ..models import User, Chore, Frequency

router = APIRouter(prefix="/api/management", tags=["Management"])

# --- Models ---
class KidCreate(BaseModel):
    name: str
    allowance_cents: int = 0
    avatar_path: str = "/static/default_avatar.png"

class KidUpdate(BaseModel):
    name: Optional[str] = None
    allowance_cents: Optional[int] = None
    avatar_path: Optional[str] = None
    is_active: Optional[bool] = None

class ChoreCreate(BaseModel):
    kid_id: int
    name: str
    description: Optional[str] = None
    weight: int = 1
    frequency: Frequency

class ChoreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    weight: Optional[int] = None
    frequency: Optional[Frequency] = None
    archived: Optional[bool] = None

# --- Kid Endpoints ---

@router.post("/kids", response_model=User)
def create_kid(kid: KidCreate, session: Session = Depends(get_session)):
    db_kid = User(
        name=kid.name,
        allowance_cents=kid.allowance_cents,
        avatar_path=kid.avatar_path,
        balance_cents=0,
        is_active=True
    )
    session.add(db_kid)
    session.commit()
    session.refresh(db_kid)
    return db_kid

@router.put("/kids/{kid_id}", response_model=User)
def update_kid(kid_id: int, kid: KidUpdate, session: Session = Depends(get_session)):
    db_kid = session.get(User, kid_id)
    if not db_kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    
    data = kid.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_kid, key, value)
        
    session.add(db_kid)
    session.commit()
    session.refresh(db_kid)
    return db_kid

# --- Chore Endpoints ---

@router.post("/chores", response_model=Chore)
def create_chore(chore: ChoreCreate, session: Session = Depends(get_session)):
    # Verify kid exists
    kid = session.get(User, chore.kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
        
    db_chore = Chore(
        kid_id=chore.kid_id,
        name=chore.name,
        description=chore.description,
        weight=chore.weight,
        frequency=chore.frequency,
        archived=False
    )
    session.add(db_chore)
    session.commit()
    session.refresh(db_chore)
    return db_chore

@router.put("/chores/{chore_id}", response_model=Chore)
def update_chore(chore_id: int, chore: ChoreUpdate, session: Session = Depends(get_session)):
    db_chore = session.get(Chore, chore_id)
    if not db_chore:
        raise HTTPException(status_code=404, detail="Chore not found")
        
    data = chore.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(db_chore, key, value)
        
    session.add(db_chore)
    session.commit()
    session.refresh(db_chore)
    return db_chore

@router.delete("/chores/{chore_id}")
def delete_chore(chore_id: int, session: Session = Depends(get_session)):
    # Soft delete (archive) mainly, but let's see if we want hard delete.
    # Spec says archive. So we reuse update or specific endpoint.
    # Let's make DELETE actually archive it for safety.
    
    db_chore = session.get(Chore, chore_id)
    if not db_chore:
        raise HTTPException(status_code=404, detail="Chore not found")
        
    db_chore.archived = True
    session.add(db_chore)
    session.commit()
    return {"status": "archived", "id": chore_id}
