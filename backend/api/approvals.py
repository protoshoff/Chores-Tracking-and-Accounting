from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from datetime import datetime, timezone
from ..db import get_session
from ..models import ChoreLog, ChoreStatus

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

from pydantic import BaseModel

class PendingChore(BaseModel):
    id: int
    kid_id: int
    kid_name: str
    chore_id: int
    chore_name: str
    date: str
    status: str
    completed_at: datetime | None
    reward: float = 0.0

@router.get("/pending", response_model=List[PendingChore])
def get_pending_approvals(session: Session = Depends(get_session)):
    stmt = select(ChoreLog).where(ChoreLog.status == ChoreStatus.PENDING)
    logs = session.exec(stmt).all()
    
    # Enrich with names (using eager loading via relationship access or manual join)
    # Since specific join syntax is tricky in simple sqlmodel, we'll access relationship props 
    # which triggers lazy load (fine for low volume)
    
    result = []
    for log in logs:
        # Ensure relationships are loaded
        # In SQLModel async they need explicit join, but sync (default) does lazy load if session open
        
        # Note: If relationship is not loaded, we might need: session.refresh(log, ["kid", "chore"])
        
        result.append(PendingChore(
            id=log.id,
            kid_id=log.kid_id,
            kid_name=log.kid.name if log.kid else "Unknown",
            chore_id=log.chore_id,
            chore_name=log.chore.name if log.chore else "Unknown",
            date=log.date.isoformat(),
            status=log.status,
            completed_at=log.completed_at,
            reward=log.chore.reward if log.chore else 0.0
        ))
    return result

class ReviewAction(str):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

from ..services.stats import StreakService

@router.post("/{log_id}/review")
def review_chore(
    log_id: int, 
    action: dict = Body(...), # {"action": "APPROVE"}
    session: Session = Depends(get_session)
):
    log = session.get(ChoreLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    act = action.get("action")
    if act == "APPROVE":
        log.status = ChoreStatus.APPROVED
    elif act == "REJECT":
        log.status = ChoreStatus.REJECTED
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    log.reviewed_at = datetime.now(timezone.utc)
    session.add(log)
    session.commit()
    session.refresh(log)
    
    # Update Streak if approved
    if log.status == ChoreStatus.APPROVED:
        StreakService(session).update_streak(log.kid_id)
        
    return log
