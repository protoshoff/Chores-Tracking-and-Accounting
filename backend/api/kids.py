from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Chore, ChoreLog, ChoreStatus
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/kids", tags=["Kids"])

from pydantic import BaseModel

class KidWithSummary(BaseModel):
    id: int
    name: str
    balance: float
    allowance: float
    avatar_path: str
    chores_summary: dict

@router.get("/", response_model=List[KidWithSummary])
def list_kids(session: Session = Depends(get_session)):
    kids = session.exec(select(User).where(User.is_active == True)).all()
    service = ChoreService(session)
    
    result = []
    for k in kids:
        summary = service.calculate_weekly_progress(k.id)
        result.append(KidWithSummary(
            id=k.id, 
            name=k.name, 
            balance=k.balance,
            allowance=k.allowance,
            avatar_path=k.avatar_path,
            chores_summary=summary
        ))
        
    return result

@router.get("/{kid_id}", response_model=KidWithSummary)
def get_kid(kid_id: int, session: Session = Depends(get_session)):
    kid = session.get(User, kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
        
    service = ChoreService(session)
    summary = service.calculate_weekly_progress(kid.id)
    return KidWithSummary(
        id=kid.id,
        name=kid.name,
        balance=kid.balance,
        allowance=kid.allowance,
        avatar_path=kid.avatar_path,
        chores_summary=summary
    )

@router.get("/{kid_id}/rotation-chores")
def get_kid_rotation_chores(kid_id: int, session: Session = Depends(get_session)):
    """Get rotation chores assigned to this kid for today."""
    from ..services.rotation import RotationService
    svc = RotationService(session)
    return svc.get_todays_rotation_chores(kid_id)

@router.get("/{kid_id}/chores")
def get_kid_chores(
    kid_id: int, 
    date_str: Optional[str] = Query(None, alias="date"), 
    session: Session = Depends(get_session)
):
    target_date = date.today()
    # Basic date parsing
    if date_str:
        from datetime import date as dt_date
        target_date = dt_date.fromisoformat(date_str)
    
    # 1. Get Assigned Chores
    stmt = select(Chore).where(Chore.kid_id == kid_id, Chore.archived == False)
    chores = session.exec(stmt).all()
    
    # 2. Get Logs for today
    service = ChoreService(session)
    logs = service.get_today_logs(kid_id, target_date)
    log_map = {log.chore_id: log for log in logs}
    
    # 3. Merge — only include chores that are due today
    result = []
    weekday = target_date.weekday()  # 0=Monday, 6=Sunday
    
    for chore in chores:
        # Skip weekly chores that aren't due today
        if chore.frequency == "WEEKLY":
            if chore.due_day is not None and chore.due_day != weekday:
                continue
        
        # Skip weekdays-only chores on weekends (Saturday=5, Sunday=6)
        if chore.weekdays_only and weekday >= 5:
            continue
        
        log = log_map.get(chore.id)
        status = log.status if log else ChoreStatus.INCOMPLETE
        result.append({
            "id": chore.id,
            "name": chore.name,
            "reward": chore.reward,
            "status": status,
            "description": chore.description,
            "frequency": chore.frequency,
            "due_day": chore.due_day,
            "weekdays_only": chore.weekdays_only,
            "icon": "default"
        })
        
    return result
