from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Chore, ChoreLog, ChoreStatus
from ..services.chores import ChoreService

router = APIRouter(prefix="/api/kids", tags=["Kids"])

@router.get("/", response_model=List[User])
def list_kids(session: Session = Depends(get_session)):
    kids = session.exec(select(User).where(User.is_active == True)).all()
    return kids

@router.get("/{kid_id}", response_model=User)
def get_kid(kid_id: int, session: Session = Depends(get_session)):
    kid = session.get(User, kid_id)
    if not kid:
        raise HTTPException(status_code=404, detail="Kid not found")
    return kid

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
    
    # 3. Merge
    result = []
    for chore in chores:
        log = log_map.get(chore.id)
        status = log.status if log else ChoreStatus.INCOMPLETE
        result.append({
            "id": chore.id,
            "name": chore.name,
            "weight": chore.weight,
            "status": status,
            "description": chore.description,
            "frequency": chore.frequency,
            "icon": "default" # TODO: Add icon field to model
        })
        
    return result
