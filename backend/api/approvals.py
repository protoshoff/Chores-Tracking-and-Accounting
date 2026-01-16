from typing import List, Literal
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from datetime import datetime
from ..db import get_session
from ..models import ChoreLog, ChoreStatus

router = APIRouter(prefix="/api/approvals", tags=["Approvals"])

@router.get("/pending", response_model=List[ChoreLog])
def get_pending_approvals(session: Session = Depends(get_session)):
    stmt = select(ChoreLog).where(ChoreLog.status == ChoreStatus.PENDING)
    return session.exec(stmt).all()

class ReviewAction(str):
    APPROVE = "APPROVE"
    REJECT = "REJECT"

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
    
    log.reviewed_at = datetime.utcnow()
    session.add(log)
    session.commit()
    session.refresh(log)
    return log
