from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from pydantic import BaseModel
from ..db import get_session
from ..models import User, Chore, Frequency, ChoreLog, ChoreStatus
from datetime import datetime

router = APIRouter(prefix="/api/management", tags=["Management"])

# --- Models ---
class KidCreate(BaseModel):
    name: str
    allowance: float = 0.0
    avatar_path: str = "/static/default_avatar.png"

class KidUpdate(BaseModel):
    name: Optional[str] = None
    allowance: Optional[float] = None
    avatar_path: Optional[str] = None
    is_active: Optional[bool] = None

class ChoreCreate(BaseModel):
    kid_id: int
    name: str
    description: Optional[str] = None
    reward: float = 1.0
    frequency: Frequency
    due_day: Optional[int] = None # 0-6

class ChoreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reward: Optional[float] = None
    frequency: Optional[Frequency] = None
    due_day: Optional[int] = None
    archived: Optional[bool] = None

# --- Kid Endpoints ---

@router.post("/kids", response_model=User)
def create_kid(kid: KidCreate, session: Session = Depends(get_session)):
    db_kid = User(
        name=kid.name,
        allowance=kid.allowance,
        avatar_path=kid.avatar_path,
        balance=0.0,
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

@router.get("/chores", response_model=List[Chore])
def list_chores(archived: bool = False, session: Session = Depends(get_session)):
    stmt = select(Chore)
    if not archived:
        stmt = stmt.where(Chore.archived == False)
    return session.exec(stmt).all()

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
        reward=chore.reward,
        frequency=chore.frequency,
        due_day=chore.due_day,
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
    db_chore.archived = True
    session.add(db_chore)
    session.commit()
    return {"status": "archived", "id": chore_id}

# --- Approvals Endpoints ---

@router.get("/approvals")
def list_pending_approvals(session: Session = Depends(get_session)):
    # Join with User and Chore to get names
    stmt = select(ChoreLog, User, Chore).where(
        ChoreLog.status == ChoreStatus.PENDING,
        ChoreLog.kid_id == User.id,
        ChoreLog.chore_id == Chore.id
    ).order_by(ChoreLog.completed_at)
    
    results = session.exec(stmt).all()
    
    # Format output
    output = []
    for log, kid, chore in results:
        output.append({
            "id": log.id,
            "kid_name": kid.name,
            "chore_name": chore.name,
            "date": log.date.isoformat(),
            "completed_at": log.completed_at,
            "reward": chore.reward
        })
    return output

@router.post("/approvals/{log_id}/{action}")
def process_approval(log_id: int, action: str, session: Session = Depends(get_session)):
    log = session.get(ChoreLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    if action == "approve":
        log.status = ChoreStatus.APPROVED
        log.reviewed_at = datetime.utcnow()
        # Explicitly credit the balance immediately as per user expectation for quick feedback
        kid = session.get(User, log.kid_id)
        chore = session.get(Chore, log.chore_id)
        if kid and chore:
             kid.balance += chore.reward
             session.add(kid)
        
    elif action == "reject":
        log.status = ChoreStatus.REJECTED
        log.reviewed_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    session.add(log)
    session.commit()
    return {"status": "success", "action": action}

# --- Approvals Endpoints ---

@router.get("/approvals")
def list_pending_approvals(session: Session = Depends(get_session)):
    # Join with User and Chore to get names
    stmt = select(ChoreLog, User, Chore).where(
        ChoreLog.status == ChoreStatus.PENDING,
        ChoreLog.kid_id == User.id,
        ChoreLog.chore_id == Chore.id
    ).order_by(ChoreLog.completed_at)
    
    results = session.exec(stmt).all()
    
    # Format output
    output = []
    for log, kid, chore in results:
        output.append({
            "id": log.id,
            "kid_name": kid.name,
            "chore_name": chore.name,
            "date": log.date.isoformat(),
            "completed_at": log.completed_at,
            "reward": chore.reward
        })
    return output

@router.post("/approvals/{log_id}/{action}")
def process_approval(log_id: int, action: str, session: Session = Depends(get_session)):
    log = session.get(ChoreLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
        
    if action == "approve":
        log.status = ChoreStatus.APPROVED
        log.reviewed_at = datetime.utcnow()
        
        # Credit the kid immediately? Usually handled by weekly rollup, 
        # but if we want instant gratification or balance updates:
        # For now, just mark approved. Payout calculation handles the rest.
        
    elif action == "reject":
        log.status = ChoreStatus.REJECTED
        log.reviewed_at = datetime.utcnow()
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
        
    session.add(log)
    session.commit()
    return {"status": "success", "action": action}
