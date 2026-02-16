from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, timezone
from ..db import get_session
from ..models import ChoreLog, ChoreStatus, User, Chore

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
    # Join upfront to avoid N+1 lazy loads
    stmt = (
        select(ChoreLog, User, Chore)
        .join(User, ChoreLog.kid_id == User.id)
        .join(Chore, ChoreLog.chore_id == Chore.id)
        .where(ChoreLog.status == ChoreStatus.PENDING)
        .order_by(ChoreLog.completed_at)
    )
    results = session.exec(stmt).all()

    return [
        PendingChore(
            id=log.id,
            kid_id=log.kid_id,
            kid_name=kid.name,
            chore_id=log.chore_id,
            chore_name=chore.name,
            date=log.date.isoformat(),
            status=log.status,
            completed_at=log.completed_at,
            reward=chore.reward,
        )
        for log, kid, chore in results
    ]

class ReviewRequest(BaseModel):
    action: str  # "APPROVE" or "REJECT"

from ..services.stats import StreakService

@router.post("/{log_id}/review")
def review_chore(
    log_id: int, 
    action: ReviewRequest,
    session: Session = Depends(get_session)
):
    log = session.get(ChoreLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    
    act = action.action
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
